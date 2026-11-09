# backend/app/ingestion.py
# =============================================================================
# RÔLE : enchaîner extraction + découpage pour tout le corpus, et exporter le résultat en JSON.
#   - construire_fragments()  → sera utilisé par la route /api/ingest (séance 2)
#   - exporter_json()         → écrit dans data/processed/
#   - lancé directement (python -m app.ingestion) → produit le livrable de la séance 1
# SÉANCE 1 — Personne 1. La Personne 2 ajoutera la stratégie « fixed » à l'étape 3.
# =============================================================================

import json                     # → écriture des fichiers JSON

from app.chunking import decouper_structurel, decouper_taille_fixe                         # → découpage structurel et fixe
from app.config import DOSSIER_CORPUS, DOSSIER_SORTIE                # → où lire les PDF, où écrire le JSON
from app.extraction import extraire_pages, lire_metadonnees          # → lecture des PDF

"""
def construire_fragments(strategie="structural", taille=500, chevauchement=100):
    documents, fragments = [], []                             # → métadonnées des documents, fragments
    for chemin in sorted(DOSSIER_CORPUS.glob("*.pdf")):       # → chaque PDF du corpus, dans l'ordre 01 → 07
        meta = lire_metadonnees(chemin)                       # → métadonnées du document
        pages = extraire_pages(chemin)                        # → texte nettoyé de chaque page
        fragments += decouper_structurel(pages, meta)         # → découpage structurel
        documents.append(meta)                                # → garde les métadonnées du document
    return documents, fragments    
"""                               # → (7 documents, liste de tous les fragments)

def construire_fragments(strategie="structural", taille=500, chevauchement=100):
    documents, fragments = [], []

    if strategie not in ("structural", "fixed"):
        raise ValueError("Strategie doit être 'structural' ou 'fixed'.")

    for chemin in sorted(DOSSIER_CORPUS.glob("*.pdf")):
        meta = lire_metadonnees(chemin)
        pages = extraire_pages(chemin)

        if strategie == "structural":
            nouveaux_fragments = decouper_structurel(pages, meta)

        else:
            nouveaux_fragments = decouper_taille_fixe(
                pages,
                meta,
                taille,
                chevauchement
            )

        fragments.extend(nouveaux_fragments)
        documents.append(meta)

    return documents, fragments
def exporter_json(nom_fichier, donnees):
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)         # → crée data/processed/ s'il n'existe pas
    (DOSSIER_SORTIE / nom_fichier).write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    # → ensure_ascii=False garde les accents lisibles ; indent=2 rend le fichier lisible


"""
if __name__ == "__main__":                                    # → seulement si on lance ce fichier directement
    documents, fragments = construire_fragments("structural")
    exporter_json("chunks_structural.json", fragments)        # → fragments structurels
    exporter_json("documents.json", documents)                # → métadonnées des 7 documents
    print(f"structural : {len(documents)} documents, {len(fragments)} fragments")
    # → affiche : structural : 7 documents, 93 fragments
"""
if __name__ == "__main__":

    # Découpage structurel
    documents, fragments_structural = construire_fragments("structural")

    exporter_json("chunks_structural.json", fragments_structural)
    exporter_json("documents.json", documents)

    print(
        f"structural : {len(documents)} documents, "
        f"{len(fragments_structural)} fragments"
    )

    # Découpage à taille fixe
    _, fragments_fixed = construire_fragments(
        "fixed",
        taille=500,
        chevauchement=100
    )

    exporter_json("chunks_fixed.json", fragments_fixed)

    print(f"fixed : {len(fragments_fixed)} fragments")