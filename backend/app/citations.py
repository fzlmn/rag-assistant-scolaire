# backend/app/citations.py
# =============================================================================
# RÔLE : vérifier les citations de la réponse du modèle.
#   - extraire_citations()   → numéros cités dans la réponse : [1], [2], et aussi [1, 3]
#   - citations_invalides()  → numéros cités qui ne correspondent à aucun fragment fourni
# SÉANCE 3 — Fatima Zahra.
# Exigence du sujet (4.4) : chaque numéro cité doit correspondre à un fragment fourni.
# =============================================================================

import re                       # → expressions régulières pour repérer les [n] dans le texte


def extraire_citations(texte):
    """« … [1] … [2, 3] … [1] » → [1, 2, 3] (sans doublon, dans l'ordre d'apparition)."""
    numeros = []                                                 # → résultat
    for groupe in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", texte):
        # → trouve le contenu de chaque crochet qui ne contient que des nombres séparés par des virgules : "1", "2, 3"
        for morceau in groupe.split(","):                        # → "2, 3" → ["2", " 3"]
            n = int(morceau)                                     # → texte → nombre (int ignore les espaces)
            if n not in numeros:                                 # → évite les doublons
                numeros.append(n)
    return numeros


def citations_invalides(texte, nb_fragments):
    """Numéros cités qui ne sont pas entre 1 et le nombre de fragments fournis."""
    return [n for n in extraire_citations(texte) if not 1 <= n <= nb_fragments]
    # → ex. 5 fragments fournis et le modèle cite [7] → [7]