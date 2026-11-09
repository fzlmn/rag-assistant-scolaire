# backend/app/ingestion.py
# =============================================================================
# RÔLE : enchaîner extraction + découpage + indexation.
#   - construire_fragments() → extraction + découpage (structural ou fixed)
#   - exporter_json()        → écrit dans data/processed/
#   - ingerer()              → utilisé par /api/ingest : écrit documents.json, indexe, renvoie added/skipped
#   - python -m app.ingestion → produit les JSON de la séance 1
# =============================================================================

import json

from app.chunking import decouper_structurel, decouper_taille_fixe
from app.config import DOSSIER_CORPUS, DOSSIER_SORTIE
from app.extraction import extraire_pages, lire_metadonnees


def construire_fragments(strategie="structural", taille=500, chevauchement=100):
    documents, fragments = [], []

    if strategie not in ("structural", "fixed"):
        raise ValueError("strategy doit être 'structural' ou 'fixed'.")

    for chemin in sorted(DOSSIER_CORPUS.glob("*.pdf")):
        meta = lire_metadonnees(chemin)
        pages = extraire_pages(chemin)

        if strategie == "structural":
            nouveaux = decouper_structurel(pages, meta)
        else:
            nouveaux = decouper_taille_fixe(pages, meta, taille, chevauchement)

        fragments.extend(nouveaux)
        documents.append(meta)

    return documents, fragments


def exporter_json(nom_fichier, donnees):
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    (DOSSIER_SORTIE / nom_fichier).write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ingerer(strategie="structural", taille=500, chevauchement=100) -> dict:
    """Ingestion complète et idempotente. Utilisée par POST /api/ingest."""
    from app.store import ajouter_chunks, definir_collection_active, nom_collection

    documents, fragments = construire_fragments(strategie, taille, chevauchement)

    # documents.json : métadonnées + nombre de fragments (utilisé par /api/documents)
    par_fichier = {}
    for f in fragments:
        par_fichier[f["file"]] = par_fichier.get(f["file"], 0) + 1
    exporter_json(
        "documents.json",
        [{**d, "nb_fragments": par_fichier.get(d["file"], 0)} for d in documents],
    )

    nom = nom_collection(strategie, taille, chevauchement)
    added, skipped = ajouter_chunks(nom, fragments)
    definir_collection_active(nom)

    return {
        "strategy": strategie,
        "collection": nom,
        "documents": len(documents),
        "fragments": len(fragments),
        "added": added,
        "skipped": skipped,
    }


if __name__ == "__main__":
    documents, fragments_structural = construire_fragments("structural")
    exporter_json("chunks_structural.json", fragments_structural)
    exporter_json("documents.json", documents)
    print(f"structural : {len(documents)} documents, {len(fragments_structural)} fragments")

    _, fragments_fixed = construire_fragments("fixed", taille=500, chevauchement=100)
    exporter_json("chunks_fixed.json", fragments_fixed)
    print(f"fixed : {len(fragments_fixed)} fragments")