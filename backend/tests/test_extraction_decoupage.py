# backend/tests/test_extraction_decoupage.py
# =============================================================================
# RÔLE : tests de l'extraction et du découpage structurel — Personne 1.
# Lancer depuis backend/ : python -m pytest -v
# =============================================================================

from app.chunking import decouper_structurel                         # → découpage structurel
from app.config import DOSSIER_CORPUS                                # → dossier des PDF
from app.extraction import extraire_pages, lire_metadonnees          # → extraction

FAQ = DOSSIER_CORPUS / "06_FAQ_Scolarite.pdf"                 # → PDF utilisé par plusieurs tests
CALENDRIER = DOSSIER_CORPUS / "04_Calendrier_academique_2026-2027.pdf"


def test_structurel_garde_question_et_reponse_ensemble():
    fragments = decouper_structurel(extraire_pages(FAQ), lire_metadonnees(FAQ))
    # → découpage structurel de la FAQ
    q8 = [f for f in fragments if "Q8." in (f["section"] or "")]
    # → fragments dont la section est la question Q8
    assert len(q8) == 1 and "12 février 2027" in q8[0]["text"]
    # → un seul fragment, qui contient aussi la réponse (la date du 12 février 2027)


def test_ligne_de_tableau_devient_phrase():
    texte = "\n".join(p["text"] for p in extraire_pages(CALENDRIER))  # → tout le texte du Calendrier
    assert "Date ou période : Vendredi 12 février 2027 — Événement : Date limite d'inscription" in texte
    # → la ligne du tableau est devenue une phrase qui garde ses en-têtes (exemple du sujet)


def test_pas_d_entete_ni_de_pied_de_page():
    for chemin in DOSSIER_CORPUS.glob("*.pdf"):               # → pour chaque PDF du corpus
        for page in extraire_pages(chemin):                   # → et chaque page
            assert "usage pédagogique uniquement" not in page["text"]
            # → le pied de page « Document fictif – usage pédagogique uniquement » a bien été retiré


def test_note_de_service_declare_ce_quelle_modifie():
    meta = lire_metadonnees(DOSSIER_CORPUS / "07_Note_de_service_2026-14.pdf")  # → métadonnées de la Note 07
    assert meta["modifies"] == ["EIH-SRE-GUIDE-2026"] and meta["date"] == "2026-10-05"
    # → elle déclare modifier le Guide des stages, et sa date est bien convertie en ISO
