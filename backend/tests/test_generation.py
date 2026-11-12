# backend/tests/test_generation.py
# =============================================================================
# RÔLE : tests du prompt, des citations et du client LLM — Fatima Zahra (séance 3).
# Lancer depuis backend/ : python -m pytest -v
# Aucun appel réel au LLM : ces tests n'ont pas besoin de clé ni d'internet.
# =============================================================================

import pytest                   # → pytest.raises vérifie qu'une erreur est bien levée

from app import llm                                          # → client LLM (on modifie ses réglages pour le test)
from app.citations import citations_invalides, extraire_citations  # → vérification des citations
from app.prompt import MESSAGE_REFUS, PROMPT_SYSTEME, construire_messages  # → prompt

FRAGMENT = {"chunk_id": "abc", "text": "La durée minimale du PFE est de 18 semaines.", "file": "07.pdf",
            "reference": "EIH-DE-NS-2026-14", "doc_type": "Note de service (texte modificatif)",
            "date": "2026-10-05", "version": "1.0", "status": "En vigueur ; modifie partiellement EIH-SRE-GUIDE-2026",
            "page": 1, "section": "Article 1 — Durée du PFE", "strategy": "structural", "score": 0.9}
# → un faux fragment, construit à la main, pour tester sans base de données


def test_extraire_citations_simples_et_groupees():
    assert extraire_citations("Réponse [1]. Autre point [2, 3]. Rappel [1].") == [1, 2, 3]
    # → [1], [2, 3] et un doublon [1] → trois numéros, sans doublon, dans l'ordre


def test_citation_invalide_detectee():
    assert citations_invalides("Voir [1] et [7].", nb_fragments=5) == [7]
    # → 5 fragments fournis : [7] ne correspond à aucun fragment


def test_prompt_contient_regles_et_contexte_numerote():
    messages = construire_messages("Durée du PFE ?", [FRAGMENT])     # → messages envoyés au modèle
    assert MESSAGE_REFUS in PROMPT_SYSTEME                            # → la phrase de refus exacte est dans les règles
    assert messages[0]["role"] == "system" and messages[1]["role"] == "user"
    assert "[1] EIH-DE-NS-2026-14" in messages[1]["content"]          # → fragment numéroté avec sa référence
    assert "publié le 2026-10-05" in messages[1]["content"]           # → la date est donnée au modèle (versions)


def test_llm_sans_cle_leve_erreur(monkeypatch):
    monkeypatch.setattr(llm, "LLM_FOURNISSEUR", "groq")               # → force le fournisseur Groq…
    monkeypatch.setattr(llm, "GROQ_API_KEY", "")                      # → …sans clé
    with pytest.raises(llm.ErreurLLM):                                # → generer doit lever ErreurLLM (→ 502)
        llm.generer([{"role": "user", "content": "test"}])