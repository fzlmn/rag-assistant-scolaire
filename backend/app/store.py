# backend/app/store.py
# =============================================================================
# RÔLE : stockage partagé ChromaDB — une collection par stratégie.
#   - nom_collection()          → eih_structural / eih_fixed_500_100
#   - ajouter_chunks()          → ajoute seulement les fragments absents (idempotence)
#   - definir_collection_active / collection_active() → collection utilisée par health, search, /api/documents
#   - rechercher()              → top-k par recherche HYBRIDE (sens + mots-clés), score = 1 - distance,
#                                 filtre par doc_type
# =============================================================================

import json                                             # → fichier qui mémorise la collection active
import math                                             # → logarithme du calcul BM25
import re                                               # → découpage du texte en mots
import unicodedata                                      # → suppression des accents
from collections import Counter                         # → fréquence des mots

import chromadb                                         # → base vectorielle persistante

from app.config import DOSSIER_BASE                     # → dossier de la base sur disque
from app.embeddings import generer_embeddings_chunks, encoder_requete


class BaseIndisponible(Exception):
    """La base est absente, vide ou illisible (→ HTTP 503)."""


_client = None                                          # → client Chroma, créé une seule fois


def obtenir_client():
    global _client
    if _client is None:
        DOSSIER_BASE.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(DOSSIER_BASE))
    return _client


def nom_collection(strategie: str, taille: int = 500, chevauchement: int = 100) -> str:
    """Une collection par stratégie : les fragments ne se mélangent jamais."""
    if strategie == "structural":
        return "eih_structural"
    return f"eih_fixed_{taille}_{chevauchement}"        # → par défaut : eih_fixed_500_100


def _fichier_actif():
    return DOSSIER_BASE / "collection_active.json"


def definir_collection_active(nom: str) -> None:
    """Mémorise la dernière collection ingérée (survit au redémarrage)."""
    DOSSIER_BASE.mkdir(parents=True, exist_ok=True)
    _fichier_actif().write_text(json.dumps({"collection": nom}), encoding="utf-8")


def collection_active():
    """Renvoie la collection active, ou lève BaseIndisponible si rien n'est indexé."""
    fichier = _fichier_actif()
    if not fichier.exists():
        raise BaseIndisponible("Aucune ingestion n'a encore été faite.")

    try:
        nom = json.loads(fichier.read_text(encoding="utf-8"))["collection"]
        collection = obtenir_client().get_collection(nom)
        nombre = collection.count()
    except Exception as erreur:
        raise BaseIndisponible(f"Base illisible : {erreur}") from erreur

    if nombre == 0:
        raise BaseIndisponible("La base est vide.")
    return collection


def ajouter_chunks(nom: str, chunks: list[dict]) -> tuple[int, int]:
    """
    Ajoute uniquement les fragments absents de la collection.
    Retourne (added, skipped). Les embeddings ne sont calculés que pour les nouveaux.
    """
    collection = obtenir_client().get_or_create_collection(
        name=nom, metadata={"hnsw:space": "cosine"}
    )

    ids = [str(c["chunk_id"]) for c in chunks]

    existants = set()
    for i in range(0, len(ids), 500):                   # → par lots, pour rester sous les limites SQLite
        existants.update(collection.get(ids=ids[i:i + 500], include=[])["ids"])

    nouveaux = [c for c in chunks if str(c["chunk_id"]) not in existants]

    if nouveaux:
        embeddings = generer_embeddings_chunks(nouveaux)   # → seulement les nouveaux
        collection.add(
            ids=[str(c["chunk_id"]) for c in nouveaux],
            embeddings=embeddings,
            documents=[c["text"] for c in nouveaux],
            metadatas=[
                {k: v for k, v in c.items()
                 if k not in ("chunk_id", "text") and isinstance(v, (str, int, float, bool))}
                for c in nouveaux
            ],
        )

    return len(nouveaux), len(chunks) - len(nouveaux)


def construire_filtre(doc_type: str | None = None, reference: str | None = None) -> dict | None:
    """Filtre Chroma sur les métadonnées : type de document et/ou référence exacte (None = pas de filtre)."""
    conditions = []
    if doc_type:
        conditions.append({"doc_type": doc_type})        # → filtre par type de document
    if reference:
        conditions.append({"reference": reference})      # → filtre par référence (ex. EIH-DE-NS-2026-14)
    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}   # → Chroma exige $and pour 2 conditions


# ---------- Recherche hybride : sens (embeddings) + mots-clés (BM25) ----------
# La recherche par le sens seule comprend mal les sigles et les mots isolés (« sdia », « CSR », « césure ») :
# pour « infos sur sdia », le seul fragment qui définit SDIA n'arrivait qu'en 11e position.
# On classe donc aussi les fragments par mots-clés (BM25), puis on fusionne les deux classements.

MOTS_VIDES = {                                          # → mots trop courants pour aider à trouver un fragment (sans accents)
    "le", "la", "les", "un", "une", "de", "des", "du", "et", "en", "au", "aux", "pour", "par", "sur", "dans",
    "avec", "est", "sont", "etre", "que", "qui", "quoi", "quel", "quels", "quelle", "quelles", "ce", "cet",
    "cette", "ces", "se", "mon", "ma", "mes", "me", "moi", "ton", "ta", "tes", "son", "sa", "ses", "leur",
    "leurs", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "on", "ne", "pas", "plus", "ou",
    "comment", "combien", "quand", "pourquoi", "faut", "peut", "peux", "dois", "doit", "fait", "faire",
    "info", "infos", "information", "informations", "parle", "dire", "svp", "stp", "merci", "bonjour",
}
K1, B = 1.5, 0.75                                       # → réglages classiques de BM25
K_FUSION = 60                                           # → constante de la fusion des rangs (Reciprocal Rank Fusion)
POIDS_MOTS = 0.5                                        # → poids du classement par mots-clés face à celui par le sens


def mots_cles(texte: str) -> list[str]:
    """« Quelles sont les filières ? » → ["filiere"] : minuscules, sans accents, sans mots vides, sans « s » final."""
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")      # → é → e, è → e…
    mots = re.findall(r"[a-z0-9]+", texte)
    return [m[:-1] if len(m) > 3 and m[-1] in "sx" else m                     # → filières = filière, stages = stage
            for m in mots if len(m) > 1 and m not in MOTS_VIDES]


def scores_bm25(mots_question: list[str], textes: list[list[str]]) -> list[float]:
    """Score BM25 de chaque texte : un mot rare de la question (ex. « sdia ») compte beaucoup, un mot courant peu."""
    if not textes:
        return []
    longueur_moyenne = sum(len(t) for t in textes) / len(textes) or 1
    nb_textes_avec = Counter(m for t in textes for m in set(t))               # → dans combien de textes chaque mot apparaît
    scores = []
    for mots in textes:
        frequence = Counter(mots)
        score = 0.0
        for m in set(mots_question):
            if m in frequence:
                idf = math.log(1 + (len(textes) - nb_textes_avec[m] + 0.5) / (nb_textes_avec[m] + 0.5))
                score += idf * frequence[m] * (K1 + 1) / (
                    frequence[m] + K1 * (1 - B + B * len(mots) / longueur_moyenne))
        scores.append(score)
    return scores


def rechercher(question: str, top_k: int = 5, doc_type: str | None = None,
               reference: str | None = None) -> list[dict]:
    """Top-k fragments par recherche hybride. Filtres facultatifs : type, référence.
    Le « score » renvoyé reste la similarité cosinus (1 - distance) : c'est lui que compare le seuil de refus."""
    collection = collection_active()
    embedding = encoder_requete(question)

    options = {
        "query_embeddings": [embedding],
        "n_results": collection.count(),               # → toute la base (environ 100 fragments) : chacun reçoit son score
        "include": ["documents", "metadatas", "distances"],
    }
    filtre = construire_filtre(doc_type, reference)
    if filtre:
        options["where"] = filtre                       # → filtre par type et/ou référence

    resultats = collection.query(**options)

    candidats = [                                       # → triés du plus proche au plus éloigné par le sens
        {
            "chunk_id": resultats["ids"][0][i],
            "text": resultats["documents"][0][i],
            "metadata": resultats["metadatas"][0][i],
            "score": round(1 - resultats["distances"][0][i], 4),
        }
        for i in range(len(resultats["ids"][0]))
    ]

    bm25 = scores_bm25(mots_cles(question), [mots_cles(c["text"]) for c in candidats])
    rang_mots = {i: r for r, i in enumerate(sorted((i for i, s in enumerate(bm25) if s > 0),
                                                   key=lambda i: -bm25[i]), start=1)}
    # → rang de chaque fragment qui contient au moins un mot-clé de la question (1 = le meilleur)

    def fusion(i):
        score = 1 / (K_FUSION + i + 1)                  # → rang par le sens
        if i in rang_mots:
            score += POIDS_MOTS / (K_FUSION + rang_mots[i])  # → + rang par mots-clés
        return score

    ordre = sorted(range(len(candidats)), key=fusion, reverse=True)
    return [candidats[i] for i in ordre[:top_k]]