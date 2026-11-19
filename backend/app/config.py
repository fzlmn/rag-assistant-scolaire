# backend/app/config.py
# =============================================================================
# RÔLE : regrouper au même endroit les chemins des dossiers et tous les réglages du projet.
# SÉANCE 1 — Fatima Zahra (chemins, modèle d'embeddings).
# SÉANCE 3 — Fatima Zahra (lecture du fichier .env, réglages du LLM) ; Aya (seuil de refus).
# Les valeurs secrètes (clé d'API) sont lues dans le fichier .env, jamais écrites dans le code.
# =============================================================================

import os                       # → accès aux variables d'environnement (os.getenv)
from pathlib import Path        # → manipulation des chemins de fichiers, compatible Windows et Linux

from dotenv import load_dotenv  # → lit le fichier .env et le charge dans les variables d'environnement

RACINE = Path(__file__).resolve().parents[2]          # dossier rag-assistant-scolaire/
# → __file__ = ce fichier (backend/app/config.py)
# → .resolve() = chemin absolu ; .parents[0] = app/, [1] = backend/, [2] = racine du dépôt
# → ainsi les chemins marchent quel que soit le dossier depuis lequel on lance le code

load_dotenv(RACINE / ".env")
# → charge rag-assistant-scolaire/.env s'il existe (clé d'API, choix du LLM…) ; ce fichier n'est jamais commité

DOSSIER_CORPUS = RACINE / "data" / "corpus"           # → les 7 PDF fournis
DOSSIER_SORTIE = RACINE / "data" / "processed"        # → les JSON générés (livrable séance 1)
DOSSIER_BASE = RACINE / "data" / "vectorstore"        # → la base Chroma (séance 2), non versionnée

NOM_MODELE = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
# → nom du modèle d'embeddings ; on peut le changer sans toucher au code
#   en définissant la variable d'environnement EMBEDDING_MODEL (sinon : e5-small multilingue)

# ---------- LLM (séance 3) ----------
LLM_FOURNISSEUR = os.getenv("LLM_PROVIDER", "groq")              # → "groq" (API en ligne) ou "ollama" (modèle local)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")                     # → clé Groq, lue dans .env (vide si absente)
LLM_MODELE = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")       # → nom du modèle à appeler (Llama 3.3 retiré de Groq)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")   # → adresse d'Ollama s'il est utilisé
LLM_DELAI = float(os.getenv("LLM_TIMEOUT", "30"))                # → secondes d'attente maximum avant d'abandonner
SEUIL_SCORE = float(os.getenv("SCORE_THRESHOLD", "0.80"))