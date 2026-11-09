# backend/app/main.py
# =============================================================================
# RÔLE : API FastAPI — /api/health, /api/ingest, /api/search
# Validation Pydantic → 422 (question vide, overlap >= chunk_size)
# =============================================================================

from typing import Annotated, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.ingestion import ingerer
from app.store import BaseIndisponible, collection_active, rechercher


app = FastAPI(
    title="RAG Assistant Scolaire",
    description="API de recherche documentaire pour les étudiants.",
    version="1.0.0",
)

# Question : espaces retirés AVANT min_length → "   " devient "" → rejetée (422)
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Filters(BaseModel):
    type: Optional[str] = None                      # → type de document (ex. "faq")


class SearchRequest(BaseModel):
    question: Question
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Filters = Field(default_factory=Filters)


class IngestRequest(BaseModel):
    strategy: Literal["structural", "fixed"] = "fixed"
    chunk_size: int = Field(default=500, ge=1)
    overlap: int = Field(default=100, ge=0)

    @model_validator(mode="after")
    def verifier_overlap(self):
        if self.overlap >= self.chunk_size:         # → ValueError ici = HTTP 422
            raise ValueError("overlap doit être strictement inférieur à chunk_size.")
        return self


@app.get("/api/health")
def health():
    try:
        nombre = collection_active().count()
    except BaseIndisponible as erreur:
        raise HTTPException(status_code=503, detail=str(erreur))
    return {"status": "ok", "fragments": nombre}


@app.post("/api/ingest")
def ingest(request: IngestRequest):
    try:
        return ingerer(
            strategie=request.strategy,
            taille=request.chunk_size,
            chevauchement=request.overlap,
        )
    except Exception as erreur:
        raise HTTPException(status_code=500, detail=str(erreur))


@app.post("/api/search")
def search(request: SearchRequest):
    try:
        resultats = rechercher(
            request.question,
            top_k=request.top_k,
            doc_type=request.filters.type,
        )
    except BaseIndisponible as erreur:
        raise HTTPException(status_code=503, detail=str(erreur))
    except Exception as erreur:
        raise HTTPException(status_code=500, detail=str(erreur))

    return {
        "question": request.question,
        "nombre_resultats": len(resultats),
        "resultats": resultats,
    }