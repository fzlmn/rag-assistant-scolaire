"""
Gestion de la base vectorielle ChromaDB.
Stockage et recherche des fragments documentaires.
"""

import chromadb

from app.config import DOSSIER_BASE
from app.embeddings import generer_embeddings_chunks, encoder_requete


NOM_COLLECTION = "chunks_scolaires"

_client = None
_collection = None


def obtenir_collection():
    """Ouvre ou crée la collection ChromaDB."""

    global _client, _collection

    if _collection is None:
        DOSSIER_BASE.mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(
            path=str(DOSSIER_BASE)
        )

        _collection = _client.get_or_create_collection(
            name=NOM_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

    return _collection


def indexer_chunks(chunks: list[dict]) -> int:
    """Génère les embeddings et enregistre les chunks dans ChromaDB."""

    if not chunks:
        return 0

    for chunk in chunks:
        if not chunk.get("chunk_id") or not chunk.get("text"):
            raise ValueError(
                "Chaque chunk doit avoir un chunk_id et un text."
            )

    embeddings = generer_embeddings_chunks(chunks)

    ids = [str(chunk["chunk_id"]) for chunk in chunks]
    textes = [chunk["text"] for chunk in chunks]

    metadonnees = []

    for chunk in chunks:
        metadata = {
            key: value
            for key, value in chunk.items()
            if key not in ("chunk_id", "text")
            and isinstance(value, (str, int, float, bool))
        }
        metadonnees.append(metadata)

    collection = obtenir_collection()

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=textes,
        metadatas=metadonnees
    )

    return collection.count()


def rechercher_chunks(question: str, top_k: int = 5) -> list[dict]:
    """Recherche les chunks les plus proches d'une question."""

    if not question or not question.strip():
        raise ValueError("La question ne peut pas être vide.")

    if top_k < 1:
        raise ValueError("top_k doit être supérieur ou égal à 1.")

    collection = obtenir_collection()

    if collection.count() == 0:
        return []

    embedding_question = encoder_requete(question)

    resultats = collection.query(
        query_embeddings=[embedding_question],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks_trouves = []

    for i in range(len(resultats["ids"][0])):
        chunks_trouves.append({
            "chunk_id": resultats["ids"][0][i],
            "text": resultats["documents"][0][i],
            "metadata": resultats["metadatas"][0][i],
            "distance": resultats["distances"][0][i]
        })

    return chunks_trouves
