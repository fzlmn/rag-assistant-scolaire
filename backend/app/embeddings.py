"""
Génération des embeddings pour les fragments documentaires.
Utilise le modèle multilingual-e5-small.
"""

from typing import Sequence

from sentence_transformers import SentenceTransformer

from app.config import NOM_MODELE


_modele = None   # → chargement différé : le modèle ne se charge qu'au premier besoin


def obtenir_modele() -> SentenceTransformer:
    global _modele
    if _modele is None:
        print(f"Chargement du modèle : {NOM_MODELE}")
        _modele = SentenceTransformer(NOM_MODELE)
    return _modele


def encoder_passages(textes: Sequence[str], batch_size: int = 32) -> list[list[float]]:
    """E5 attend le préfixe 'passage:' pour les documents."""
    if not textes:
        return []

    textes_prepares = []
    for texte in textes:
        if not isinstance(texte, str) or not texte.strip():
            raise ValueError("Chaque fragment doit contenir un texte non vide.")
        textes_prepares.append(f"passage: {texte.strip()}")

    embeddings = obtenir_modele().encode(
        textes_prepares,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=len(textes_prepares) > 50,
    )
    return embeddings.tolist()


def encoder_requete(question: str) -> list[float]:
    """E5 attend le préfixe 'query:' pour les questions."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    embedding = obtenir_modele().encode(
        [f"query: {question.strip()}"],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embedding[0].tolist()


def generer_embeddings_chunks(chunks: list[dict], batch_size: int = 32) -> list[list[float]]:
    """Un embedding par fragment, dans le même ordre que les chunks."""
    return encoder_passages([c["text"] for c in chunks], batch_size=batch_size)