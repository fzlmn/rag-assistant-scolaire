# backend/app/rag.py
# =============================================================================
# RÔLE : la chaîne complète d'une question —
#   recherche → seuil → reformulation → recherche → prompt → LLM → vérification des citations.
#   - reformuler() → la question réécrite par le LLM (fautes, langage SMS, question de suivi)
#   - repondre()   → dictionnaire au format de la réponse de /api/ask (avec gestion des versions, voir versions.py)
# SÉANCE 3 — Aya. Reformulation et historique de conversation : Fatima Zahra.
# Exigences du sujet (4.4) : seuil de score (refus sans appeler le LLM), vérification des citations.
# =============================================================================

import re                                               # → nettoyage de la question reformulée
import time                                             # → mesure de la latence

from app.citations import citations_invalides          # → numéros cités qui ne correspondent à aucun fragment
from app.config import SEUIL_SCORE                      # → seuil de refus (réglable dans .env)
from app.llm import ErreurLLM, generer                  # → appel au modèle de langage (lève ErreurLLM)
from app.prompt import (MESSAGE_REFUS, construire_messages,  # → phrase de refus + messages system/user
                        construire_messages_reformulation)   # → messages pour réécrire la question
from app.store import rechercher                        # → top-k fragments avec leur score
from app.versions import completer_avec_versions        # → ajoute les documents qui modifient ceux trouvés

LONGUEUR_EXTRAIT = 300                                  # → nombre de caractères gardés dans « excerpt »
MAX_ECHANGES = 3                                        # → échanges précédents gardés pour comprendre une question de suivi


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


def _reponse(answer, found, sources, invalides, debut, question_comprise=None):
    """Assemble le dictionnaire de réponse, avec la latence depuis 'debut'."""
    return {
        "answer": answer,
        "found": found,
        "sources": sources,
        "invalid_citations": invalides,
        "latency_ms": int((time.perf_counter() - debut) * 1000),
        "question_comprise": question_comprise,         # → question reformulée (affichée sous la réponse)
    }


def _sous_le_seuil(fragments):
    """Vrai si aucun fragment n'atteint le seuil de score : la question est sans rapport avec le corpus."""
    meilleur = max((f["score"] for f in fragments), default=None)      # → meilleur score (None si aucun résultat)
    return meilleur is None or meilleur < SEUIL_SCORE


def reformuler(question, historique=None):
    """Le LLM réécrit la question (fautes, langage SMS, « et pour X ? »…) pour mieux chercher.
    S'il échoue ou répond n'importe quoi, on garde la question d'origine : la reformulation n'est qu'une aide."""
    try:
        texte = generer(construire_messages_reformulation(question, historique)).strip()
    except ErreurLLM:
        return question                                                # → LLM injoignable : on cherche avec la question telle quelle
    texte = texte.splitlines()[0].strip() if texte else ""             # → une seule ligne
    texte = re.sub(r"^(question\s*(réécrite|reformulée)?\s*:\s*)", "", texte, flags=re.IGNORECASE)
    texte = texte.strip(" \"'«»“”")                                    # → sans guillemets autour
    if not texte or len(texte) > 400 or _normaliser(MESSAGE_REFUS) in _normaliser(texte):
        return question
    return texte


def repondre(question, top_k=5, doc_type=None, historique=None):
    """Recherche, applique le seuil, reformule la question, interroge le LLM et vérifie les citations.
    historique = échanges précédents [{"question": …, "answer": …}] pour comprendre une question de suivi."""
    debut = time.perf_counter()
    historique = (historique or [])[-MAX_ECHANGES:]                    # → les derniers échanges seulement

    if not historique:
        # → question isolée : le seuil s'applique AVANT tout appel au LLM (exigence du sujet)
        fragments = rechercher(question, top_k=top_k, doc_type=doc_type)   # → peut lever BaseIndisponible (→ 503)
        if _sous_le_seuil(fragments):
            return _reponse(MESSAGE_REFUS, False, [], [], debut)       # → refus direct : le LLM n'est PAS appelé
    # → avec un historique, « et la max ? » ne veut rien dire seul : on reformule d'abord, puis on applique le seuil

    question_comprise = reformuler(question, historique)               # → 1er appel au LLM : réécrire la question
    if historique or question_comprise != question:
        fragments = rechercher(question_comprise, top_k=top_k, doc_type=doc_type)  # → recherche avec la question claire
        if _sous_le_seuil(fragments):
            return _reponse(MESSAGE_REFUS, False, [], [], debut, question_comprise)

    fragments = completer_avec_versions(question_comprise, fragments)  # → ajoute la note qui modifie un document trouvé

    texte = generer(construire_messages(question, fragments, question_comprise)).strip()  # → 2e appel (→ 502 si échec)

    if _normaliser(MESSAGE_REFUS) in _normaliser(texte):               # → le modèle a lui-même refusé
        return _reponse(MESSAGE_REFUS, False, [], [], debut, question_comprise)

    invalides = citations_invalides(texte, len(fragments))             # → ex. le modèle cite [7] avec 5 fragments
    return _reponse(texte, True, _construire_sources(fragments), invalides, debut, question_comprise)