# backend/tests/test_versions.py
# =============================================================================
# RÔLE : tests de la gestion des versions (versions.py) et du filtre par référence (store.py) — Aya.
# Lancer depuis backend/ : python -m pytest -v
# Aucune base ni documents.json réels : tout est simulé (monkeypatch).
# =============================================================================

from app import rag, versions
from app.prompt import formater_contexte
from app.store import construire_filtre

DOCUMENTS = [
    {"reference": "EIH-SRE-GUIDE-2026", "modifies": []},
    {"reference": "EIH-DE-REG-2026", "modifies": []},
    {"reference": "EIH-DE-NS-2026-14", "modifies": ["EIH-SRE-GUIDE-2026"]},      # → la note modifie le guide
]


def fragment(chunk_id, reference, score=0.9):
    return {"chunk_id": chunk_id, "text": f"texte {chunk_id}", "score": score,
            "metadata": {"reference": reference, "date": "2026-01-01", "status": "En vigueur"}}


def test_note_modificative_detectee_sans_regle_en_dur():
    assert versions.modificateurs_manquants({"EIH-SRE-GUIDE-2026"}, DOCUMENTS) == ["EIH-DE-NS-2026-14"]
    assert versions.modificateurs_manquants({"EIH-DE-REG-2026"}, DOCUMENTS) == []      # → rien ne modifie le règlement
    assert versions.modificateurs_manquants({"EIH-SRE-GUIDE-2026", "EIH-DE-NS-2026-14"}, DOCUMENTS) == []   # → déjà là


def test_la_note_est_ajoutee_apres_les_fragments_trouves(monkeypatch):
    monkeypatch.setattr(versions, "charger_documents", lambda: DOCUMENTS)
    appels = []
    def fausse_recherche(question, top_k=5, doc_type=None, reference=None):
        appels.append(reference)
        return [fragment("note-1", reference), fragment("note-2", reference)]
    monkeypatch.setattr(versions, "rechercher", fausse_recherche)

    trouves = [fragment("guide-1", "EIH-SRE-GUIDE-2026")]
    resultat = versions.completer_avec_versions("durée du PFE ?", trouves)

    assert [f["chunk_id"] for f in resultat] == ["guide-1", "note-1", "note-2"]   # → le guide garde le numéro [1]
    assert appels == ["EIH-DE-NS-2026-14"]
    assert "[3]" in formater_contexte(resultat)                                     # → la note est présentée au LLM


def test_pas_d_ajout_si_aucun_document_modifie(monkeypatch):
    monkeypatch.setattr(versions, "charger_documents", lambda: DOCUMENTS)
    monkeypatch.setattr(versions, "rechercher", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ne doit pas être appelé")))
    trouves = [fragment("reg-1", "EIH-DE-REG-2026")]
    assert versions.completer_avec_versions("question", trouves) == trouves


def test_pas_de_doublon_si_le_fragment_est_deja_present(monkeypatch):
    monkeypatch.setattr(versions, "charger_documents", lambda: DOCUMENTS)
    monkeypatch.setattr(versions, "rechercher", lambda q, top_k=5, doc_type=None, reference=None: [fragment("guide-1", reference)])
    trouves = [fragment("guide-1", "EIH-SRE-GUIDE-2026")]
    assert len(versions.completer_avec_versions("question", trouves)) == 1


def test_ask_donne_la_note_au_llm(monkeypatch):
    """Bout en bout : /api/ask envoie au LLM le fragment du guide ET celui de la note."""
    monkeypatch.setattr(versions, "charger_documents", lambda: DOCUMENTS)
    monkeypatch.setattr(versions, "rechercher", lambda q, top_k=5, doc_type=None, reference=None: [fragment("note-1", reference)])
    monkeypatch.setattr(rag, "rechercher", lambda q, top_k=5, doc_type=None: [fragment("guide-1", "EIH-SRE-GUIDE-2026")])
    messages_recus = []
    monkeypatch.setattr(rag, "generer", lambda messages: messages_recus.append(messages) or "18 semaines [2].")

    resultat = rag.repondre("durée du PFE ?")

    assert "EIH-DE-NS-2026-14" in messages_recus[-1][1]["content"]       # → la note est dans le prompt de réponse
    # → [-1] : le dernier appel au LLM est la réponse ; le premier est la reformulation de la question
    assert [s["id"] for s in resultat["sources"]] == [1, 2]              # → et dans les sources numérotées
    assert resultat["invalid_citations"] == []


def test_filtre_chroma_par_type_et_reference():
    assert construire_filtre() is None
    assert construire_filtre(doc_type="Guide pratique") == {"doc_type": "Guide pratique"}
    assert construire_filtre(reference="EIH-DE-NS-2026-14") == {"reference": "EIH-DE-NS-2026-14"}
    assert construire_filtre("Guide pratique", "EIH-DE-NS-2026-14") == {
        "$and": [{"doc_type": "Guide pratique"}, {"reference": "EIH-DE-NS-2026-14"}]}