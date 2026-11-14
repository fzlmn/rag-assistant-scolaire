# backend/tests/test_ask.py
# =============================================================================
# RÔLE : tests de /api/ask — Aya (séance 3).
# Lancer depuis backend/ : python -m pytest -v
# Aucun appel réel au LLM ni à la base : rechercher() et generer() sont remplacés (monkeypatch).
# =============================================================================

from fastapi.testclient import TestClient

from app import rag
from app.llm import ErreurLLM
from app.main import app
from app.prompt import MESSAGE_REFUS

client = TestClient(app)

FRAGMENT = {
    "chunk_id": "abc",
    "text": "La durée minimale du PFE est de 18 semaines.",
    "metadata": {"file": "07_Note.pdf", "reference": "EIH-DE-NS-2026-14", "date": "2026-10-05",
                "page": 1, "section": "Article 1", "doc_type": "Note de service", "status": "En vigueur"},
    "score": 0.9,
}   # → un faux résultat de recherche, construit à la main


def _simuler(monkeypatch, score=0.9, reponse="18 semaines [1]."):
    """Remplace la recherche et le LLM ; renvoie la liste des appels faits au LLM."""
    appels = []
    monkeypatch.setattr(rag, "rechercher", lambda q, top_k=5, doc_type=None: [{**FRAGMENT, "score": score}])
    def faux_llm(messages):
        appels.append(messages)
        return reponse
    monkeypatch.setattr(rag, "generer", faux_llm)
    return appels


def test_refus_hors_corpus_sans_appeler_le_llm(monkeypatch):
    appels = _simuler(monkeypatch, score=0.1)                 # → score bien sous le seuil
    r = client.post("/api/ask", json={"question": "Prix d'un repas ?"})
    assert r.status_code == 200
    corps = r.json()
    assert corps["found"] is False and corps["answer"] == MESSAGE_REFUS
    assert corps["sources"] == []
    assert appels == []                                       # → le LLM n'a PAS été appelé


def test_reponse_avec_sources(monkeypatch):
    _simuler(monkeypatch)
    corps = client.post("/api/ask", json={"question": "Durée du PFE ?"}).json()
    assert corps["found"] is True and "[1]" in corps["answer"]
    assert corps["sources"][0]["id"] == 1 and corps["sources"][0]["reference"] == "EIH-DE-NS-2026-14"
    assert corps["invalid_citations"] == []


def test_citation_invalide_signalee(monkeypatch):
    _simuler(monkeypatch, reponse="18 semaines [1] et aussi [4].")   # → [4] n'existe pas (1 seul fragment)
    corps = client.post("/api/ask", json={"question": "Durée du PFE ?"}).json()
    assert corps["invalid_citations"] == [4]


def test_refus_du_llm_donne_found_false(monkeypatch):
    _simuler(monkeypatch, reponse=MESSAGE_REFUS)              # → le modèle refuse lui-même
    corps = client.post("/api/ask", json={"question": "Durée du PFE ?"}).json()
    assert corps["found"] is False and corps["sources"] == []


def test_llm_en_panne_renvoie_502(monkeypatch):
    _simuler(monkeypatch)
    def en_panne(messages):
        raise ErreurLLM("pas de réponse")
    monkeypatch.setattr(rag, "generer", en_panne)
    assert client.post("/api/ask", json={"question": "Durée du PFE ?"}).status_code == 502


def test_question_vide_renvoie_422():
    assert client.post("/api/ask", json={"question": "   "}).status_code == 422