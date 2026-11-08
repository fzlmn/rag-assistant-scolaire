# backend/app/config.py
# =============================================================================
# RÔLE : regrouper au même endroit les chemins des dossiers et le nom du modèle.
# SÉANCE 1 — Personne 1.
# Tous les autres fichiers importent ces constantes au lieu d'écrire les chemins eux-mêmes.
# =============================================================================

import os                       # → accès aux variables d'environnement (os.getenv)
from pathlib import Path        # → manipulation des chemins de fichiers, compatible Windows et Linux

RACINE = Path(__file__).resolve().parents[2]          # dossier rag-assistant-scolaire/
# → __file__ = ce fichier (backend/app/config.py)
# → .resolve() = chemin absolu ; .parents[0] = app/, [1] = backend/, [2] = racine du dépôt
# → ainsi les chemins marchent quel que soit le dossier depuis lequel on lance le code

DOSSIER_CORPUS = RACINE / "data" / "corpus"           # → les 7 PDF fournis
DOSSIER_SORTIE = RACINE / "data" / "processed"        # → les JSON générés (livrable séance 1)
DOSSIER_BASE = RACINE / "data" / "vectorstore"        # → la base Chroma (séance 2), non versionnée

NOM_MODELE = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
# → nom du modèle d'embeddings ; on peut le changer sans toucher au code
#   en définissant la variable d'environnement EMBEDDING_MODEL (sinon : e5-small multilingue)
