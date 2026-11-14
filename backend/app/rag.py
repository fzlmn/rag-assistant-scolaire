# backend/app/rag.py
# =============================================================================
# RÔLE : la chaîne complète d'une question — recherche → seuil → prompt → LLM → vérification des citations.
#   - repondre() → dictionnaire au format de la réponse de /api/ask
# SÉANCE 3 — Aya.
# Exigences du sujet (4.4) : seuil de score (refus sans appeler le LLM), vérification des citations.
# =============================================================================

import time                                             # → mesure de la latence

from app.citations import citations_invalides          # → numéros cités qui ne correspondent à aucun fragment
from app.config import SEUIL_SCORE                      # → seuil de refus (réglable dans .env)
from app.llm import generer                             # → appel au modèle de langage (lève ErreurLLM)
from app.prompt import MESSAGE_REFUS, construire_messages  # → phrase de refus + messages system/user
from app.store import rechercher                        # → top-k fragments avec leur score

LONGUEUR_EXTRAIT = 300                                  # → nombre de caractères gardés dans « excerpt »


def _normaliser(texte):
    """Uniformise l'apostrophe (’ → ') et les espaces pour comparer deux phrases."""
    return texte.replace("’", "'").strip()


def _construire_sources(fragments):
    """Transforme les fragments en sources numérotées : le numéro 'id' est celui que le modèle cite [1], [2]…"""
    sources = []
    for numero, f in enumerate(fragments, start=1):     # → même numérotation que dans le prompt
        m = f.get("metadata", {})                       # → référence, date, page… sont rangées sous « metadata »
        sources.append({
            "id": numero,
            "chunk_id": f["chunk_id"],
            "file": m.get("file", ""),
            "reference": m.get("reference", ""),
            "date": m.get("date", ""),
            "page": m.get("page"),
            "section": m.get("section") or None,
            "excerpt": f["text"][:LONGUEUR_EXTRAIT],    # → début du fragment seulement
            "score": f["score"],
        })
    return sources


def _reponse(answer, found, sources, invalides, debut):
    """Assemble le dictionnaire de réponse, avec la latence depuis 'debut'."""
    return {
        "answer": answer,
        "found": found,
        "sources": sources,
        "invalid_citations": invalides,
        "latency_ms": int((time.perf_counter() - debut) * 1000),
    }


def repondre(question, top_k=5, doc_type=None):
    """Recherche, applique le seuil, interroge le LLM et vérifie les citations."""
    debut = time.perf_counter()
    fragments = rechercher(question, top_k=top_k, doc_type=doc_type)   # → peut lever BaseIndisponible (→ 503)

    meilleur = max((f["score"] for f in fragments), default=None)      # → meilleur score (None si aucun résultat)
    if meilleur is None or meilleur < SEUIL_SCORE:
        return _reponse(MESSAGE_REFUS, False, [], [], debut)           # → refus direct : le LLM n'est PAS appelé

    texte = generer(construire_messages(question, fragments)).strip()  # → peut lever ErreurLLM (→ 502)

    if _normaliser(MESSAGE_REFUS) in _normaliser(texte):               # → le modèle a lui-même refusé
        return _reponse(MESSAGE_REFUS, False, [], [], debut)

    invalides = citations_invalides(texte, len(fragments))             # → ex. le modèle cite [7] avec 5 fragments
    return _reponse(texte, True, _construire_sources(fragments), invalides, debut)