# backend/tests/test_recherche.py
# Lancer depuis backend/ : python -m pytest -v

from fastapi.testclient import TestClient

from app.chunking import decouper_taille_fixe
from app.config import DOSSIER_CORPUS
from app.extraction import extraire_pages, lire_metadonnees
from app.main import app

FAQ = DOSSIER_CORPUS / "06_FAQ_Scolarite.pdf"
client = TestClient(app)


def test_taille_fixe_max_500_caracteres():
    fragments = decouper_taille_fixe(extraire_pages(FAQ), lire_metadonnees(FAQ), 500, 100)
    assert fragments                                          # → il y a bien des fragments
    assert all(len(f["text"]) <= 500 for f in fragments)      # → aucun ne dépasse 500


def test_question_vide_renvoie_422():
    reponse = client.post("/api/search", json={"question": "   "})
    assert reponse.status_code == 422                         # → espaces seuls rejetés


def test_ingestion_idempotente():
    corps = {"strategy": "fixed", "chunk_size": 500, "overlap": 100}
    client.post("/api/ingest", json=corps)                    # → 1er appel (ajoute ou ignore)
    deuxieme = client.post("/api/ingest", json=corps).json()  # → 2e appel
    assert deuxieme["added"] == 0                             # → rien de nouveau
    assert deuxieme["skipped"] > 0