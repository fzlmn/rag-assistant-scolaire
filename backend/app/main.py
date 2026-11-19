
# backend/app/main.py
# =============================================================================
# RÔLE : API FastAPI — /api/health, /api/ingest, /api/search,
#        /api/documents, /api/ask
# Validation Pydantic → 422 (question vide, overlap >= chunk_size)
# =============================================================================

import json

from typing import Annotated, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.ingestion import ingerer
from app.llm import ErreurLLM
from app.rag import repondre
from app.store import BaseIndisponible, collection_active, rechercher
from app.config import DOSSIER_SORTIE


# =============================================================================
# CRÉATION DE L'APPLICATION FASTAPI
# =============================================================================

app = FastAPI(
    title="RAG Assistant Scolaire",
    description="API de recherche documentaire pour les étudiants.",
    version="1.0.0",
)


# =============================================================================
# CONFIGURATION CORS
# Autorise le frontend Angular (localhost:4200) à communiquer avec FastAPI.
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# VALIDATION DES DONNÉES
# =============================================================================

# Les espaces sont retirés avant min_length.
# Une question contenant uniquement des espaces est donc rejetée (422).

Question = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1)
]


class Filters(BaseModel):
    type: Optional[str] = None


class SearchRequest(BaseModel):
    question: Question
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Filters = Field(default_factory=Filters)


class AskRequest(SearchRequest):
    """Même structure que SearchRequest."""


class Source(BaseModel):
    id: int
    chunk_id: str
    file: str
    reference: str
    date: str
    page: Optional[int] = None
    section: Optional[str] = None
    excerpt: str
    score: float


class AskResponse(BaseModel):
    answer: str
    found: bool
    sources: list[Source]
    invalid_citations: list[int]
    latency_ms: int


class IngestRequest(BaseModel):
    strategy: Literal["structural", "fixed"] = "fixed"
    chunk_size: int = Field(default=500, ge=1)
    overlap: int = Field(default=100, ge=0)

    @model_validator(mode="after")
    def verifier_overlap(self):
        if self.overlap >= self.chunk_size:
            raise ValueError(
                "overlap doit être strictement inférieur à chunk_size."
            )
        return self


# =============================================================================
# ROUTE GET /api/health
# Vérifie que la base vectorielle est disponible.
# =============================================================================

@app.get("/api/health")
def health():
    try:
        nombre = collection_active().count()

    except BaseIndisponible as erreur:
        raise HTTPException(
            status_code=503,
            detail=str(erreur)
        )

    return {
        "status": "ok",
        "fragments": nombre
    }


# =============================================================================
# ROUTE POST /api/ingest
# Lance l'ingestion et le découpage des documents.
# =============================================================================

@app.post("/api/ingest")
def ingest(request: IngestRequest):
    try:
        return ingerer(
            strategie=request.strategy,
            taille=request.chunk_size,
            chevauchement=request.overlap,
        )

    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=str(erreur)
        )


# =============================================================================
# ROUTE POST /api/search
# Recherche les fragments pertinents dans la base vectorielle.
# =============================================================================

@app.post("/api/search")
def search(request: SearchRequest):
    try:
        resultats = rechercher(
            request.question,
            top_k=request.top_k,
            doc_type=request.filters.type,
        )

    except BaseIndisponible as erreur:
        raise HTTPException(
            status_code=503,
            detail=str(erreur)
        )

    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=str(erreur)
        )

    return {
        "question": request.question,
        "nombre_resultats": len(resultats),
        "resultats": resultats,
    }


# =============================================================================
# ROUTE GET /api/documents
# Retourne les documents et leur nombre de fragments.
# =============================================================================

@app.get("/api/documents")
def documents():
    try:
        collection = collection_active()

    except BaseIndisponible as erreur:
        raise HTTPException(
            status_code=503,
            detail=str(erreur)
        )

    docs = json.loads(
        (DOSSIER_SORTIE / "documents.json").read_text(
            encoding="utf-8"
        )
    )

    # Récupération des métadonnées des fragments présents dans la base.
    fichiers = [
        m["file"]
        for m in collection.get(
            include=["metadatas"]
        )["metadatas"]
    ]

    # Ajout du nombre de fragments pour chaque document.
    return [
        {
            **d,
            "nb_fragments": fichiers.count(d["file"])
        }
        for d in docs
    ]


# =============================================================================
# ROUTE POST /api/ask
# Exécute toute la chaîne RAG :
# Question → Recherche → Contexte → LLM → Réponse avec sources.
# =============================================================================

@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return repondre(
            request.question,
            top_k=request.top_k,
            doc_type=request.filters.type
        )

    except BaseIndisponible as erreur:
        raise HTTPException(
            status_code=503,
            detail=str(erreur)
        )

    except ErreurLLM as erreur:
        raise HTTPException(
            status_code=502,
            detail=str(erreur)
        )

    except Exception as erreur:
        raise HTTPException(
            status_code=500,
            detail=str(erreur)
        )
