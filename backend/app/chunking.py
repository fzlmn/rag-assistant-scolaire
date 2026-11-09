# backend/app/chunking.py
# =============================================================================
# RÔLE : découper le texte des pages en fragments (« chunks »), avec leurs métadonnées.
#   - decouper_structurel()   → stratégie (b) : un titre + son contenu — Personne 1
#   - decouper_taille_fixe()  → stratégie (a) : ajoutée ensuite par la Personne 2 (étape 3)
#   - creer_id()              → identifiant calculé, base de l'idempotence
# SÉANCE 1. Exigences du sujet (4.2) : deux stratégies configurables,
# chaque fragment porte identifiant, fichier, référence, type, date, page, section.
# =============================================================================

import hashlib                  # → calcul d'empreintes (hash SHA-1) pour les identifiants
import re                       # → expressions régulières pour repérer les titres ## / ###


def creer_id(meta, strategie, parametres, numero, texte):
    """Identifiant déterministe : mêmes entrées → même id → pas de doublon à la ré-indexation."""
    brut = f"{meta['file']}|{strategie}|{parametres}|{numero}|{texte}"
    # → chaîne qui décrit le fragment de façon unique : fichier, stratégie, paramètres, numéro, texte
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()[:16]
    # → empreinte SHA-1 de cette chaîne, gardée sur 16 caractères ; toujours la même pour le même fragment


def creer_fragment(meta, strategie, parametres, numero, texte, page, section):
    return {                                                  # → un fragment = un dictionnaire
        "chunk_id": creer_id(meta, strategie, parametres, numero, texte),  # → identifiant unique et stable
        "text": texte,                                        # → le texte du fragment
        "file": meta["file"],                                 # → fichier PDF d'origine
        "reference": meta["reference"],                       # → référence du document (ex. EIH-DE-REG-2026)
        "doc_type": meta["doc_type"],                         # → type (sert au filtre de la recherche)
        "date": meta["date"],                                 # → date de publication ISO
        "version": meta["version"],                           # → version du document
        "status": meta["status"],                             # → statut (en vigueur, modificatif…)
        "page": page,                                         # → page où commence le fragment
        "section": section,                                   # → titre de la section (ou None)
        "strategy": strategie,                                # → "fixed" ou "structural"
    }


def sans_marques_titre(texte):
    return re.sub(r"^#+ ", "", texte, flags=re.MULTILINE)
    # → enlève les marques « ## » / « ### » en début de ligne (utile pour le découpage fixe)


# ---------- Stratégie (b) : structurelle (titres, articles, questions) ----------

def decouper_structurel(pages, meta, taille_max=1200):
    unites = []      # une unité = un titre + son contenu
    titre_parent, titre_courant = None, None                  # → titre ## en cours et titre ### en cours
    lignes, page_debut = [], None                             # → lignes de l'unité en cours, page où elle commence

    def fermer_unite():                                       # → enregistre l'unité en cours
        if lignes:                                            # → seulement si elle contient du texte
            section = " > ".join(t for t in (titre_parent, titre_courant) if t) or None
            # → chemin de section, ex. « Titre V — Validation > Article 14 — Session de rattrapage »
            unites.append({"section": section, "page": page_debut, "lignes": list(lignes)})
            # → list(lignes) fait une copie, car « lignes » sera vidée ensuite

    for page in pages:                                        # → parcourt toutes les pages du document
        for ligne in page["text"].split("\n"):                # → et chaque ligne de la page
            if ligne.startswith("## ") or ligne.startswith("### "):  # → la ligne est un titre
                fermer_unite()                                # → on termine l'unité précédente
                lignes.clear()                                # → et on en commence une nouvelle
                if ligne.startswith("## "):                   # → grand titre de section
                    titre_parent, titre_courant = ligne[3:], None  # → nouveau parent, plus de sous-titre
                else:                                         # → sous-titre (article, question…)
                    titre_courant = ligne[4:]                 # → le parent reste le même
                page_debut = page["page"]                     # → page du titre
            else:                                             # → ligne de texte normal
                if not lignes:                                # → première ligne de contenu de l'unité…
                    page_debut = page["page"]                 # → …la page de l'unité est celle de son contenu
                lignes.append(ligne)                          # → la ligne rejoint l'unité en cours
    fermer_unite()                                            # → enregistre la dernière unité du document
    # → comme titre_parent n'est pas remis à zéro entre les pages, une section commencée
    #   en bas d'une page continue sur la suivante (cas du Calendrier, section 3)

    fragments = []                                            # → résultat : liste des fragments
    for unite in unites:                                      # → transforme chaque unité en fragment(s)
        entete = f"[{unite['section']}]\n" if unite["section"] else ""
        # → la section est écrite en tête du fragment : la recherche « voit » de quoi il parle
        bloc = ""                                             # → texte du fragment en cours de construction
        for ligne in unite["lignes"]:                  # une unité trop longue est redécoupée par lignes
            if bloc and len(bloc) + len(ligne) > taille_max:  # → ajouter cette ligne dépasserait 1 200 caractères
                fragments.append(creer_fragment(meta, "structural", taille_max, len(fragments),
                                                entete + bloc.strip(), unite["page"], unite["section"]))
                # → on ferme le fragment en cours (sans couper de ligne)
                bloc = ""                                     # → et on en commence un nouveau
            bloc += ligne + "\n"                              # → ajoute la ligne au fragment en cours
        if bloc.strip():                                      # → reste du texte à la fin de l'unité
            fragments.append(creer_fragment(meta, "structural", taille_max, len(fragments),
                                            entete + bloc.strip(), unite["page"], unite["section"]))
            # → dernier fragment de l'unité
    return fragments                                          # → tous les fragments du document
# ---------- Stratégie (a) : taille fixe avec chevauchement ----------

def decouper_taille_fixe(pages, meta, taille=500, chevauchement=100):
    fragments = []
    parametres = f"{taille}-{chevauchement}"
    section = None

    for page in pages:
        texte_original = page["text"]

        # Récupérer les titres avant de supprimer les marques ##
        titres = re.findall(
            r"^#{2,3} (.+)$",
            texte_original,
            flags=re.MULTILINE
        )

        texte = sans_marques_titre(texte_original).replace("\n", " ")

        debut = 0

        while debut < len(texte):
            fin = min(debut + taille, len(texte))

            # Éviter de couper un mot en deux
            if fin < len(texte):
                espace = texte.rfind(" ", debut, fin)
                if espace > debut:
                    fin = espace

            morceau = texte[debut:fin].strip()

            if morceau:
                # Conserver le dernier titre rencontré
                texte_avant = texte_original[:len(texte_original)]

                for titre in titres:
                    if titre in texte[:fin]:
                        section = titre

                fragments.append(
                    creer_fragment(
                        meta,
                        "fixed",
                        parametres,
                        len(fragments),
                        morceau,
                        page["page"],
                        section
                    )
                )

            if fin >= len(texte):
                break

            debut = max(fin - chevauchement, debut + 1)

            # Reprendre au début d'un mot
            espace = texte.find(" ", debut)
            if espace != -1 and espace < fin:
                debut = espace + 1

    return fragments