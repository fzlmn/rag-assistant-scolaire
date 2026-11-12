# backend/app/llm.py
# =============================================================================
# RÔLE : envoyer les messages (prompt + question) au modèle de langage et renvoyer sa réponse.
#   - generer()  → texte de la réponse ; lève ErreurLLM si le modèle ne répond pas (→ 502 dans l'API)
# Deux fournisseurs possibles, choisis dans .env : Groq (API gratuite en ligne) ou Ollama (modèle local).
# SÉANCE 3 — Fatima Zahra.
# Exigence du sujet (3) : LLM par API ou modèle local, clés dans un fichier .env, jamais dans le dépôt.
# =============================================================================

import httpx                    # → client HTTP pour appeler l'API du modèle

from app.config import GROQ_API_KEY, LLM_DELAI, LLM_FOURNISSEUR, LLM_MODELE, OLLAMA_URL  # → réglages lus dans .env

URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"     # → adresse de l'API de Groq (format OpenAI)


class ErreurLLM(Exception):
    pass
    # → erreur « maison » : le modèle ne répond pas (clé absente, réseau, quota…) ; l'API la transforme en 502


def generer(messages):
    """Envoie la liste de messages au modèle et renvoie le texte de sa réponse."""
    try:
        if LLM_FOURNISSEUR == "ollama":                                  # → modèle local avec Ollama
            reponse = httpx.post(
                f"{OLLAMA_URL}/api/chat",                                # → route de conversation d'Ollama
                json={"model": LLM_MODELE, "messages": messages, "stream": False,
                    "options": {"temperature": 0}},                    # → stream=False : réponse en un bloc ; température 0
                timeout=LLM_DELAI,                                       # → abandonne après LLM_DELAI secondes
            )
            reponse.raise_for_status()                                   # → lève une erreur si le code HTTP n'est pas 2xx
            return reponse.json()["message"]["content"]                  # → texte de la réponse d'Ollama

        if not GROQ_API_KEY:                                             # → pas de clé dans .env
            raise ErreurLLM("Clé GROQ_API_KEY absente du fichier .env")
        reponse = httpx.post(
            URL_GROQ,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},         # → la clé est envoyée dans l'en-tête, jamais affichée
            json={"model": LLM_MODELE, "messages": messages, "temperature": 0},
            # → temperature 0 : le modèle choisit toujours le mot le plus probable → réponses reproductibles
            timeout=LLM_DELAI,
        )
        reponse.raise_for_status()                                       # → 401 (mauvaise clé), 429 (quota)… → erreur
        return reponse.json()["choices"][0]["message"]["content"]        # → texte de la réponse de Groq
    except ErreurLLM:                                                    # → notre propre erreur : on la laisse passer
        raise
    except (httpx.HTTPError, KeyError, ValueError) as e:                 # → réseau, délai dépassé, réponse inattendue
        raise ErreurLLM(f"Le modèle de langage ne répond pas : {e}")     # → transformée en ErreurLLM (→ 502)