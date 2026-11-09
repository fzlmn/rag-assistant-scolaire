# backend/app/store.py
# =============================================================================
# RÔLE : stockage partagé ChromaDB — une collection par stratégie.
#   - nom_collection()          → eih_structural / eih_fixed_500_100
#   - ajouter_chunks()          → ajoute seulement les fragments absents (idempotence)
#   - definir_collection_active / collection_active() → collection utilisée par health, search, /api/documents
#   - rechercher()              → top-k avec score = 1 - distance, filtre par doc_type
# =============================================================================

import json                                             # → fichier qui mémorise la collection active

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


def rechercher(question: str, top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    """Top-k fragments les plus proches ; score = 1 - distance (cosinus)."""
    collection = collection_active()
    embedding = encoder_requete(question)

    options = {
        "query_embeddings": [embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if doc_type:
        options["where"] = {"doc_type": doc_type}       # → filtre par type de document

    resultats = collection.query(**options)

    return [
        {
            "chunk_id": resultats["ids"][0][i],
            "text": resultats["documents"][0][i],
            "metadata": resultats["metadatas"][0][i],
            "score": round(1 - resultats["distances"][0][i], 4),
        }
        for i in range(len(resultats["ids"][0]))
    ]