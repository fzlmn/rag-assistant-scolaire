"""
Génération des embeddings pour les fragments documentaires.
Utilise le modèle multilingual-e5-small.
"""

from typing import Sequence

from sentence_transformers import SentenceTransformer

from app.config import NOM_MODELE


# Chargement différé : le modèle ne se charge que lorsqu'on en a besoin.
_modele = None


def obtenir_modele() -> SentenceTransformer:
    """Charge le modèle une seule fois et le réutilise ensuite."""
    global _modele

    if _modele is None:
        print(f"Chargement du modèle : {NOM_MODELE}")
        _modele = SentenceTransformer(NOM_MODELE)

    return _modele


def encoder_passages(
    textes: Sequence[str],
    batch_size: int = 32
) -> list[list[float]]:
    """
    Transforme une liste de textes en vecteurs.

    E5 attend le préfixe 'passage:' pour les documents.
    """

    if not textes:
        return []

    textes_prepares = []

    for texte in textes:
        if not isinstance(texte, str) or not texte.strip():
            raise ValueError("Chaque fragment doit contenir un texte non vide.")

        textes_prepares.append(f"passage: {texte.strip()}")

    modele = obtenir_modele()

    embeddings = modele.encode(
        textes_prepares,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings.tolist()


def encoder_requete(question: str) -> list[float]:
    """
    Transforme une question en vecteur pour la recherche.

    E5 attend le préfixe 'query:' pour les questions.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    modele = obtenir_modele()

    embedding = modele.encode(
        [f"query: {question.strip()}"],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embedding[0].tolist()


def generer_embeddings_chunks(
    chunks: list[dict],
    batch_size: int = 32
) -> list[list[float]]:
    """
    Génère un embedding pour chaque fragment.

    L'ordre des vecteurs correspond exactement à l'ordre des chunks.
    """

    textes = [chunk["text"] for chunk in chunks]

    return encoder_passages(textes, batch_size=batch_size)
