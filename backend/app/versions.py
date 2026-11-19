# backend/app/versions.py
# =============================================================================
# RÔLE : gestion des versions documentaires (sujet, 4.4 : « en cas de règles différentes entre deux
#        documents, retenir le plus récent »).
#   Quand la recherche ramène un fragment d'un document, on ajoute aussi des fragments des documents
#   qui le MODIFIENT (ex. la note de service qui change une règle du guide), sinon le LLM ne voit
#   que l'ancienne règle.
#   - modificateurs_manquants() → références des documents modificatifs absents des résultats
#   - completer_avec_versions() → ajoute leurs fragments les plus proches de la question
# Aucune règle écrite pour ce corpus : tout vient de la métadonnée « modifies » de documents.json,
# lue dans le statut de chaque document (voir extraction.lire_metadonnees).
# SÉANCE 3 — Aya.
# =============================================================================

import json                                             # → lecture de documents.json

from app.config import DOSSIER_SORTIE                   # → dossier data/processed/
from app.store import rechercher                        # → recherche, avec filtre par référence

FRAGMENTS_PAR_MODIFICATIF = 2                           # → combien de fragments ajouter par document modificatif


def charger_documents():
    """Lit data/processed/documents.json (écrit par /api/ingest). Liste vide s'il n'existe pas encore."""
    chemin = DOSSIER_SORTIE / "documents.json"
    if not chemin.exists():
        return []
    return json.loads(chemin.read_text(encoding="utf-8"))


def modificateurs_manquants(references_trouvees, documents):
    """Références des documents qui modifient un document trouvé et ne sont pas déjà dans les résultats.
    Répété jusqu'à stabilité : une note qui en modifie une autre est suivie aussi."""
    connues = set(references_trouvees)                  # → références déjà présentes (puis complétées)
    ajoutees = []                                       # → modificatifs à aller chercher, dans l'ordre
    changement = True
    while changement:                                   # → on s'arrête quand un tour n'ajoute plus rien
        changement = False
        for doc in documents:
            reference = doc.get("reference", "")
            modifies = set(doc.get("modifies") or [])   # → références que ce document déclare modifier
            if reference and reference not in connues and modifies & connues:
                ajoutees.append(reference)
                connues.add(reference)
                changement = True
    return ajoutees


def completer_avec_versions(question, fragments):
    """Ajoute, à la fin de la liste, des fragments des documents modificatifs absents des résultats.
    Les fragments déjà là gardent leur numéro [1], [2]… : les nouveaux prennent les numéros suivants."""
    references = {f.get("metadata", {}).get("reference", "") for f in fragments}
    references.discard("")                              # → ignore les fragments sans référence
    deja_la = {f["chunk_id"] for f in fragments}        # → évite d'ajouter deux fois le même fragment
    resultat = list(fragments)

    for reference in modificateurs_manquants(references, charger_documents()):
        for f in rechercher(question, top_k=FRAGMENTS_PAR_MODIFICATIF, reference=reference):
            if f["chunk_id"] not in deja_la:            # → l'ajout ignore volontairement le filtre « type » de l'utilisateur :
                resultat.append(f)                      #   une règle modifiée doit toujours être accompagnée de sa modification
                deja_la.add(f["chunk_id"])
    return resultat