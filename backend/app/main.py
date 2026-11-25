# backend/app/main.py
# =============================================================================
# RÔLE : API FastAPI — /api/health, /api/ingest, /api/search, /api/documents
# Validation Pydantic → 422 (question vide, overlap >= chunk_size)
# =============================================================================

from typing import Annotated, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # → autorise le frontend à appeler l'API
from fastapi.responses import FileResponse           # → renvoie un fichier (le PDF d'un document)
from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.ingestion import ingerer
from app.llm import ErreurLLM                       # → le LLM ne répond pas (→ 502)
from app.rag import repondre                        # → chaîne complète de /api/ask
from app.store import BaseIndisponible, collection_active, rechercher
from app.config import DOSSIER_CORPUS, DOSSIER_SORTIE  # → data/corpus/ (les PDF) et data/processed/

import json                                         # → lecture de documents.json
import time                                         # → chronomètre pour latency_ms


app = FastAPI(
    title="RAG Assistant Scolaire",
    description="API de recherche documentaire pour les étudiants.",
    version="1.0.0",
)
app.add_middleware(                                           # → CORS (séance 4)
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Question : espaces retirés AVANT min_length → "   " devient "" → rejetée (422)
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Filters(BaseModel):
    type: Optional[str] = None                      # → type de document (ex. "faq")


class SearchRequest(BaseModel):
    question: Question
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Filters = Field(default_factory=Filters)


class AskRequest(SearchRequest):
    """Même forme que /api/search : question non vide, top_k (1 à 20), filters.type."""


class Source(BaseModel):
    id: int                                         # → numéro cité dans la réponse : [1], [2]…
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
    found: bool                                     # → False = refus (hors corpus)
    sources: list[Source]
    invalid_citations: list[int]
    latency_ms: int


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
    debut = time.perf_counter()                      # → départ du chronomètre
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
        "results": [                                          # → nom attendu par le frontend et par run_eval.py
            {**r["metadata"], "chunk_id": r["chunk_id"], "text": r["text"], "score": r["score"]}
            for r in resultats                                # → métadonnées « à plat » : file, reference, doc_type, page…
        ],
        "latency_ms": int((time.perf_counter() - debut) * 1000),  # → temps de la recherche en millisecondes
    }

@app.get("/api/documents")                                    # → route GET /api/documents
def documents():
    try:
        collection = collection_active()                      # → collection utilisée par la recherche
    except BaseIndisponible as erreur:
        raise HTTPException(status_code=503, detail=str(erreur))   # → 503 si aucune ingestion
    docs = json.loads((DOSSIER_SORTIE / "documents.json").read_text(encoding="utf-8"))
    # → métadonnées des 7 documents (écrites par /api/ingest)
    fichiers = [m["file"] for m in collection.get(include=["metadatas"])["metadatas"]]
    # → le nom de fichier de chaque fragment présent dans la base
    return [{**d, "nb_fragments": fichiers.count(d["file"])} for d in docs]
    # → chaque document avec son nombre de fragments, compté dans la base active


@app.get("/api/documents/{fichier}/pdf")                     # → le PDF d'un document (aperçu ou téléchargement)
def document_pdf(fichier: str, download: bool = False):
    pdf_du_corpus = {p.name for p in DOSSIER_CORPUS.glob("*.pdf")}  # → seuls les PDF du corpus sont servis
    if fichier not in pdf_du_corpus:                          # → nom inconnu (ou tentative « ../ ») → 404
        raise HTTPException(status_code=404, detail=f"Document introuvable : {fichier}")
    return FileResponse(
        DOSSIER_CORPUS / fichier,
        media_type="application/pdf",
        filename=fichier,
        content_disposition_type="attachment" if download else "inline",
        # → inline : le navigateur l'affiche (aperçu) ; attachment : il le télécharge (?download=true)
    )


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        return repondre(request.question, top_k=request.top_k, doc_type=request.filters.type)
    except BaseIndisponible as erreur:
        raise HTTPException(status_code=503, detail=str(erreur))     # → base absente ou vide
    except ErreurLLM as erreur:
        raise HTTPException(status_code=502, detail=str(erreur))     # → le LLM ne répond pas
    except Exception as erreur:
        raise HTTPException(status_code=500, detail=str(erreur))