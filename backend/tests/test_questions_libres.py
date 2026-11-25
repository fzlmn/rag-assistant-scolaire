# backend/tests/test_questions_libres.py
# =============================================================================
# RÔLE : tests des questions libres — recherche par mots-clés (BM25), reformulation de la question
# et historique de conversation. Fatima Zahra.
# Lancer depuis backend/ : python -m pytest -v
# Aucun appel réel au LLM ni à la base : rechercher() et generer() sont remplacés (monkeypatch).
# =============================================================================

from fastapi.testclient import TestClient

from app import rag
from app.llm import ErreurLLM
from app.main import app
from app.store import mots_cles, scores_bm25

client = TestClient(app)

FRAGMENT = {
    "chunk_id": "art2",
    "text": "À partir de la 2A, trois filières : IGL, SDIA — Science des Données et IA, CSR — Cybersécurité et Réseaux.",
    "metadata": {"file": "01_Reglement.pdf", "reference": "EIH-DE-REG-2026", "date": "2026-07-10",
                 "page": 1, "section": "Article 2", "doc_type": "Règlement officiel", "status": "En vigueur"},
    "score": 0.85,
}


def test_mots_cles_sans_accents_ni_mots_vides():
    assert mots_cles("Quelles sont les filières ? Infos sur SDIA") == ["filiere", "sdia"]


def test_bm25_favorise_le_fragment_qui_contient_le_sigle():
    textes = [mots_cles("Durée du PFE et délai du rapport"),
              mots_cles("Les filières IGL, SDIA et CSR"),
              mots_cles("Horaires de la bibliothèque")]
    scores = scores_bm25(mots_cles("infos sur sdia"), textes)
    assert scores[1] > 0 and scores[0] == scores[2] == 0      # → seul le fragment qui contient « SDIA » est retenu


def test_question_de_suivi_reformulee_avec_l_historique(monkeypatch):
    questions_cherchees, appels = [], []
    monkeypatch.setattr(rag, "rechercher", lambda q, top_k=5, doc_type=None: questions_cherchees.append(q) or [FRAGMENT])
    monkeypatch.setattr(rag, "completer_avec_versions", lambda question, fragments: fragments)
    reponses = iter(["Qu'est-ce que la filière CSR ?", "La CSR est la filière Cybersécurité et Réseaux [1]."])
    monkeypatch.setattr(rag, "generer", lambda messages: appels.append(messages) or next(reponses))

    historique = [{"question": "Quelles sont les filières ?", "answer": "IGL, SDIA et CSR [1]."}]
    resultat = rag.repondre("et la CSR c'est quoi ?", historique=historique)

    assert "Quelles sont les filières ?" in appels[0][1]["content"]     # → la reformulation voit l'historique
    assert "[1]" not in appels[0][1]["content"]                         # → sans les citations de l'ancienne réponse
    assert questions_cherchees == ["Qu'est-ce que la filière CSR ?"]    # → on cherche avec la question claire
    assert resultat["found"] is True and resultat["question_comprise"] == "Qu'est-ce que la filière CSR ?"


def test_api_ask_accepte_l_historique(monkeypatch):
    appels = []
    monkeypatch.setattr(rag, "rechercher", lambda q, top_k=5, doc_type=None: [FRAGMENT])
    monkeypatch.setattr(rag, "completer_avec_versions", lambda question, fragments: fragments)
    reponses = iter(["Quelle est la durée maximale du PFE ?", "24 semaines [1]."])
    monkeypatch.setattr(rag, "generer", lambda messages: appels.append(messages) or next(reponses))

    corps = client.post("/api/ask", json={
        "question": "et la max ?",
        "history": [{"question": "Durée minimale du PFE ?", "answer": "18 semaines [1]."}],
    }).json()
    assert "Durée minimale du PFE ?" in appels[0][1]["content"]        # → l'historique arrive jusqu'à la reformulation
    assert corps["question_comprise"] == "Quelle est la durée maximale du PFE ?"
    assert client.post("/api/ask", json={"question": "x", "history": "pas une liste"}).status_code == 422


def test_reformulation_en_panne_garde_la_question(monkeypatch):
    questions_cherchees = []
    monkeypatch.setattr(rag, "rechercher", lambda q, top_k=5, doc_type=None: questions_cherchees.append(q) or [FRAGMENT])
    monkeypatch.setattr(rag, "completer_avec_versions", lambda question, fragments: fragments)
    appels = []
    def llm(messages):
        appels.append(messages)
        if len(appels) == 1:
            raise ErreurLLM("pas de réponse")                           # → la reformulation échoue…
        return "Trois filières : IGL, SDIA et CSR [1]."                 # → …mais la réponse arrive
    monkeypatch.setattr(rag, "generer", llm)

    resultat = rag.repondre("filieres ?")
    assert questions_cherchees == ["filieres ?"]                        # → recherche faite avec la question d'origine
    assert resultat["found"] is True and resultat["question_comprise"] == "filieres ?"
