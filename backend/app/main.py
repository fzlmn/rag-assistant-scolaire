
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.ingestion import construire_fragments
from app.vectorstore import indexer_chunks, rechercher_chunks


app = FastAPI(
    title="RAG Assistant Scolaire",
    description="API de recherche documentaire pour les étudiants.",
    version="1.0.0"
)


class SearchRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class IngestRequest(BaseModel):
    strategie: Literal["structural", "fixed"] = "fixed"
    taille: int = Field(default=500, ge=1)
    chevauchement: int = Field(default=100, ge=0)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "RAG Assistant Scolaire fonctionne."
    }


@app.post("/api/ingest")
def ingest(request: IngestRequest):
    try:
        if request.chevauchement >= request.taille:
            raise ValueError(
                "Le chevauchement doit être inférieur à la taille."
            )

        documents, fragments = construire_fragments(
            strategie=request.strategie,
            taille=request.taille,
            chevauchement=request.chevauchement
        )

        nombre_indexe = indexer_chunks(fragments)

        return {
            "message": "Ingestion terminée avec succès.",
            "strategie": request.strategie,
            "nombre_documents": len(documents),
            "nombre_fragments": len(fragments),
            "nombre_chunks_indexes": nombre_indexe
        }

    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    except Exception as erreur:
        raise HTTPException(status_code=500, detail=str(erreur))


@app.post("/api/search")
def search(request: SearchRequest):
    try:
        resultats = rechercher_chunks(
            request.question,
            top_k=request.top_k
        )

        return {
            "question": request.question,
            "nombre_resultats": len(resultats),
            "resultats": resultats
        }

    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur))
    except Exception as erreur:
        raise HTTPException(status_code=500, detail=str(erreur))
