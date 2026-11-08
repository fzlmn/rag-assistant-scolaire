# backend/app/extraction.py
# =============================================================================
# RÔLE : lire les PDF du corpus.
#   - extraire_pages()    → texte nettoyé de chaque page (sans en-tête ni pied de page),
#                           titres marqués ## / ###, tableaux convertis en phrases
#   - lire_metadonnees()  → référence, type, date, version, statut, document modifié
# SÉANCE 1 — Personne 1.
# Exigences du sujet (4.1) : numéro de page, métadonnées, suppression des en-têtes/pieds,
# lien en-tête/cellule des tableaux.
# =============================================================================

import re                       # → expressions régulières (recherche de motifs dans le texte)
from pathlib import Path        # → pour récupérer le nom du fichier PDF

import pdfplumber               # → bibliothèque qui lit les PDF : mots, positions, polices, tableaux

MARGE_HAUT = 50   # l'en-tête est vers y = 22
# → on retire les 50 premiers points de chaque page (l'en-tête « École d'Ingénieurs Hélianthe… »)
MARGE_BAS = 50    # le pied de page est vers y = 808 (page de 842)
# → on retire les 50 derniers points (le pied « Document fictif… page N »)

MOIS = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}
# → table de correspondance nom du mois → numéro, pour convertir les dates françaises


def nettoyer(texte):
    """Remplace les retours à la ligne et espaces multiples par un seul espace."""
    return re.sub(r"\s+", " ", (texte or "")).strip()
    # → (texte or "") : si texte vaut None (cellule vide), on prend une chaîne vide
    # → \s+ : tout groupe d'espaces / tabulations / retours à la ligne → un seul espace
    # → .strip() : enlève les espaces au début et à la fin


def date_fr_vers_iso(texte):
    """« 1er septembre 2026 » → « 2026-09-01 »."""
    m = re.search(r"(\d{1,2})(?:er)?\s+([a-zéû]+)\s+(\d{4})", texte.lower())
    # → cherche : 1 ou 2 chiffres (le jour), « er » facultatif (1er), un mot (le mois), 4 chiffres (l'année)
    # → .lower() met tout en minuscules pour retrouver le mois dans MOIS
    if not m or m.group(2) not in MOIS:                       # → pas de date reconnue
        return ""                                             # → on renvoie une chaîne vide
    jour, mois, annee = int(m.group(1)), MOIS[m.group(2)], int(m.group(3))
    # → group(1) = jour, group(2) = nom du mois converti en numéro, group(3) = année
    return f"{annee:04d}-{mois:02d}-{jour:02d}"
    # → format ISO AAAA-MM-JJ ; :02d ajoute un zéro devant (9 → 09) ; ce format se compare facilement


def ligne_vers_phrase(entetes, ligne):
    """Une ligne de tableau → « En-tête 1 : valeur — En-tête 2 : valeur ... »."""
    morceaux = []                                             # → les « En-tête : valeur » de la ligne
    for entete, valeur in zip(entetes, ligne):                # → parcourt colonne par colonne (en-tête, cellule)
        valeur = nettoyer(valeur)                             # → nettoie la cellule (retours à la ligne, espaces)
        if valeur:                                            # → ignore les cellules vides
            morceaux.append(f"{nettoyer(entete)} : {valeur}") # → ex. « Date ou période : Vendredi 12 février 2027 »
    return " — ".join(morceaux)
    # → assemble les morceaux avec « — » : chaque phrase garde le lien en-tête / cellule (exigence 4.1)


def est_tableau_metadonnees(tableau):
    return len(tableau[0]) == 2 and nettoyer(tableau[0][0]) == "Organisme émetteur"
    # → vrai si c'est le tableau de la page 1 : 2 colonnes et première case « Organisme émetteur »


def lire_metadonnees(chemin_pdf):
    """Lit le tableau clé/valeur de la page 1 et les métadonnées internes du PDF."""
    with pdfplumber.open(chemin_pdf) as pdf:                  # → ouvre le PDF (refermé automatiquement à la fin)
        infos_pdf = pdf.metadata                              # → métadonnées internes du fichier (Title, Author…)
        nb_pages = len(pdf.pages)                             # → nombre de pages
        tableau = next(t for t in pdf.pages[0].extract_tables() if est_tableau_metadonnees(t))
        # → parmi les tableaux de la page 1, prend le premier qui est le tableau de métadonnées
    champs = {nettoyer(cle): nettoyer(valeur) for cle, valeur in tableau}
    # → transforme les lignes [clé, valeur] en dictionnaire : {"Référence": "EIH-DE-REG-2026", ...}
    statut = champs.get("Statut", "")                         # → texte du statut (vide s'il manque)
    # Un document qui se déclare modificatif cite les références qu'il modifie (ex. EIH-SRE-GUIDE-2026)
    modifie = re.findall(r"EIH-[A-Z0-9-]+?-\d{4}", statut) if "modifie" in statut.lower() else []
    # → si le statut contient « modifie », on récupère toutes les références EIH-…-AAAA qu'il cite
    # → sinon liste vide ; aucune règle écrite pour un fichier précis (exigence du sujet)
    return {                                                  # → dictionnaire des métadonnées du document
        "file": Path(chemin_pdf).name,                        # → nom du fichier, ex. 07_Note_de_service_2026-14.pdf
        "title": infos_pdf.get("Title", ""),                  # → titre lu dans le PDF
        "reference": champs.get("Référence", ""),             # → ex. EIH-DE-NS-2026-14
        "doc_type": champs.get("Type de document", ""),       # → ex. Note de service (texte modificatif)
        "date": date_fr_vers_iso(champs.get("Date de publication", "")),  # → ex. 2026-10-05
        "version": champs.get("Version", ""),                 # → ex. 1.0
        "status": statut,                                     # → texte complet du statut
        "pages": nb_pages,                                    # → nombre de pages
        "modifies": modifie,                                  # → références modifiées, ex. ["EIH-SRE-GUIDE-2026"]
    }


def niveau_titre(mots):
    """2 = grand titre de section, 3 = sous-titre (article, question, 2.1...), 0 = texte normal."""
    tout_gras = all("Bold" in m["fontname"] for m in mots)    # → vrai si tous les mots de la ligne sont en gras
    taille = max(m["size"] for m in mots)                     # → plus grande taille de police de la ligne
    if tout_gras and taille >= 13:                            # → gras et ≥ 13 pt (13,5 dans le corpus)
        return 2                                              # → titre de section (« Titre IV », « 2. … »)
    if tout_gras and taille >= 11:                            # → gras et ≥ 11 pt (11,2 dans le corpus)
        return 3                                              # → sous-titre (« Article 8 », « Q4. », « 2.1 »)
    return 0                                                  # → texte normal (9,6 pt)


def extraire_pages(chemin_pdf):
    """Renvoie une liste [{file, page, text}] : texte nettoyé, titres marqués ## / ###, tableaux en phrases."""
    pages = []                                                # → résultat : un dictionnaire par page
    with pdfplumber.open(chemin_pdf) as pdf:                  # → ouvre le PDF
        for numero, page in enumerate(pdf.pages, start=1):    # → parcourt les pages ; numéro à partir de 1
            zone = page.crop((0, MARGE_HAUT, page.width, page.height - MARGE_BAS))
            # → garde seulement la zone entre l'en-tête et le pied de page (x0, haut, x1, bas)
            tableaux = zone.find_tables()                     # → détecte les tableaux de cette zone
            blocs = []  # (position verticale, texte) → remis dans l'ordre de lecture à la fin

            # 1) Les tableaux : une phrase par ligne
            for t in tableaux:                                # → pour chaque tableau trouvé
                lignes = t.extract()                          # → contenu du tableau : liste de lignes de cellules
                if est_tableau_metadonnees(lignes):           # → le tableau de métadonnées de la page 1…
                    continue                                  # → …est ignoré (il sert à lire_metadonnees)
                entetes = lignes[0]                           # → la première ligne contient les en-têtes de colonnes
                for ligne in lignes[1:]:                      # → les lignes suivantes sont les données
                    phrase = ligne_vers_phrase(entetes, ligne)  # → ligne → phrase « En-tête : valeur — … »
                    if phrase:                                # → ignore les lignes entièrement vides
                        blocs.append((t.bbox[1], phrase))     # → t.bbox[1] = haut du tableau, pour le remettre à sa place

            # 2) Le texte hors tableaux (sinon il serait lu deux fois)
            def hors_tableau(obj):                            # → vrai si un caractère est en dehors de tous les tableaux
                x = (obj["x0"] + obj["x1"]) / 2               # → centre horizontal du caractère
                y = (obj["top"] + obj["bottom"]) / 2          # → centre vertical du caractère
                return not any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in (t.bbox for t in tableaux))
                # → bbox = (x0, haut, x1, bas) de chaque tableau ; on garde le caractère s'il n'est dans aucun

            mots = zone.filter(hors_tableau).extract_words(extra_attrs=["fontname", "size"])
            # → mots hors tableaux, avec leur police (fontname) et leur taille (size) pour repérer les titres
            lignes = {}                                       # → position verticale → mots de cette ligne
            for m in mots:                                   # regrouper les mots par ligne
                lignes.setdefault(round(m["top"]), []).append(m)
                # → les mots qui ont le même « top » (arrondi) sont sur la même ligne
            for top in sorted(lignes):                        # → parcourt les lignes de haut en bas
                ligne = sorted(lignes[top], key=lambda m: m["x0"])  # → mots de la ligne, de gauche à droite
                if max(m["size"] for m in ligne) >= 18:      # titre du document : déjà dans les métadonnées
                    continue                                  # → on l'ignore (19 pt dans le corpus)
                texte = " ".join(m["text"] for m in ligne)    # → reconstitue le texte de la ligne
                niveau = niveau_titre(ligne)                  # → 2, 3 ou 0 selon la police
                blocs.append((top, ("#" * niveau + " " + texte) if niveau else texte))
                # → un titre devient « ## Titre » ou « ### Titre » ; le texte normal reste tel quel

            # 3) Remettre dans l'ordre de la page et nettoyer
            blocs.sort(key=lambda b: b[0])                    # → trie tableaux et texte par position verticale
            texte_page = "\n".join(b[1] for b in blocs)       # → une ligne par bloc
            texte_page = re.sub(r"\(cid:127\)\s*", "- ", texte_page)   # puces mal décodées
            # → pdfplumber lit la puce « • » comme « (cid:127) » : on la remplace par « - »
            texte_page = re.sub(r" +([.,])", r"\1", texte_page)          # « 18 semaines . » → « 18 semaines. »
            # → supprime l'espace parasite avant un point ou une virgule (mots en gras lus séparément)
            pages.append({"file": Path(chemin_pdf).name, "page": numero, "text": texte_page})
            # → ajoute la page au résultat, avec son numéro (exigence 4.1)
    return pages                                              # → liste des pages du document
