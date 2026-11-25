# backend/app/prompt.py
# =============================================================================
# RÔLE : écrire le prompt envoyé au modèle.
#   - MESSAGE_REFUS        → phrase exacte imposée par le sujet quand l'information n'est pas dans le corpus
#   - PROMPT_SYSTEME       → règles que le modèle doit suivre
#   - formater_contexte()  → fragments numérotés [1], [2]… avec leurs métadonnées (référence, date, statut…)
#   - construire_messages() → messages « system » + « user » envoyés au modèle
#   - PROMPT_REFORMULATION / construire_messages_reformulation() → réécrire la question de l'étudiant
#     (fautes, langage SMS, question de suivi) avant la recherche
# SÉANCE 3 — Fatima Zahra. Questions libres et reformulation : Fatima Zahra.
# Exigences du sujet (4.4) : répondre uniquement à partir des fragments, citer [1], [2],
# phrase de refus exacte, retenir le plus récent en cas de divergence et le signaler.
# =============================================================================

import re                       # → retirer les citations [n] de l'historique

MESSAGE_REFUS = "Je ne trouve pas cette information dans les documents de l'École."
# → phrase imposée par le sujet, utilisée telle quelle dans le prompt, dans l'API et dans les tests

PROMPT_SYSTEME = f"""Tu es l'assistant scolaire de l'École d'Ingénieurs Hélianthe (EIH).
Tu réponds aux questions des étudiants en suivant strictement ces règles :
1. Réponds uniquement à partir des fragments fournis. N'utilise aucune connaissance extérieure et n'invente rien.
2. Après chaque affirmation, cite le ou les fragments utilisés sous la forme [1], [2], avec des crochets droits. N'utilise que les numéros des fragments fournis.
3. Si les fragments ne contiennent pas l'information demandée, réponds exactement par cette phrase, sans guillemets et sans rien ajouter : {MESSAGE_REFUS}
4. Si deux fragments donnent des règles différentes sur le même point, ou si un fragment indique qu'une règle a été modifiée (par exemple « au lieu de », « est portée de … à … »), donne d'abord la règle en vigueur, celle du document le plus récent lorsque son statut indique qu'il modifie l'autre, puis termine toujours par une phrase qui donne l'ancienne valeur et le document qui la fixait, sur le modèle : « Cette règle remplace l'ancienne valeur (X) fixée par le document Y [n]. »
5. Réponds en français, de façon courte et précise.
6. Les questions peuvent être familières, mal orthographiées, abrégées ou écrites dans une autre langue : comprends l'intention de l'étudiant. Si la question est vague (par exemple « infos sur X » ou « parle-moi de X »), résume ce que les fragments disent de X.
7. Écris en texte simple, sans mise en forme Markdown (ni **, ni #, ni tableau). Pour une liste, commence chaque ligne par « - »."""
# → règle 1 : pas d'invention ; règle 2 : citations ; règle 3 : refus exact ; règle 4 : versions ; règle 5 : forme ;
#   règle 6 : questions libres ; règle 7 : pas de Markdown (le chat l'afficherait tel quel)


def formater_contexte(fragments):
    """Numérote les fragments à partir de 1 et affiche leurs métadonnées avant leur texte."""
    blocs = []                                                   # → un bloc de texte par fragment
    for numero, f in enumerate(fragments, start=1):              # → numéro = celui que le modèle citera : [1], [2]…
        m = {**f.get("metadata", {}), **f}
        # → la recherche (store.rechercher) range référence, date, page… sous « metadata » : on les remonte
        #   au premier niveau ; un fragment déjà « à plat » (comme dans les tests) reste inchangé
        entete = (f"[{numero}] {m.get('reference', '')} — {m.get('doc_type', '')} — publié le {m.get('date', '')} — "
                f"statut : {m.get('status', '')} — page {m.get('page', '')} — section : {m.get('section') or '—'}")
        # → .get() : un champ absent (ex. section vide, non stockée dans Chroma) n'empêche pas de construire le prompt
        # → la date et le statut permettent au modèle de savoir quel document est le plus récent et lequel modifie l'autre
        blocs.append(entete + "\n" + m["text"])                 # → en-tête puis texte du fragment
            # → en-tête puis texte du fragment
    return "\n\n".join(blocs)                                    # → blocs séparés par une ligne vide


def construire_messages(question, fragments, question_reformulee=None):
    """Messages au format « chat » : les règles (system), puis les fragments et la question (user).
    Si la question a été reformulée, le modèle reçoit les deux : la question telle qu'écrite et ce qu'elle veut dire."""
    question_texte = f"Question : {question}"
    if question_reformulee and question_reformulee.strip() != question.strip():
        question_texte += f"\nQuestion reformulée (pour comprendre l'intention de l'étudiant) : {question_reformulee}"
    return [
        {"role": "system", "content": PROMPT_SYSTEME},          # → les règles à respecter
        {"role": "user", "content": f"Fragments :\n\n{formater_contexte(fragments)}\n\n{question_texte}"},
        # → le contexte numéroté, puis la question de l'étudiant
    ]


# ---------- Reformulation de la question, avant la recherche ----------

PROMPT_REFORMULATION = """Tu prépares la recherche documentaire de l'assistant scolaire de l'École d'Ingénieurs Hélianthe (EIH).
On te donne la dernière question d'un étudiant et, parfois, les échanges précédents de la conversation.
Réécris la dernière question en une seule question complète, claire et autonome, en français correct :
- corrige les fautes, les abréviations et le langage SMS (« c koi » → « qu'est-ce que », « pr » → « pour ») ;
- si la question fait référence aux échanges précédents (« et pour… », « et la max ? », « il », « ça »), remplace ces références par ce dont il s'agit ;
- garde les sigles tels quels (PFE, ECTS, SDIA, CSR…) ; si les échanges précédents donnent leur signification, ajoute-la entre parenthèses ;
- si la question est écrite dans une autre langue, traduis-la en français ;
- n'ajoute aucune information qui n'est ni dans la question ni dans les échanges, et ne réponds pas à la question ;
- si la question est déjà claire, recopie-la telle quelle.
Réponds uniquement par la question réécrite, sans guillemets ni commentaire."""
# → la reformulation sert seulement à mieux CHERCHER : la réponse vient toujours des fragments

LONGUEUR_HISTORIQUE = 400                                        # → caractères gardés de chaque réponse précédente


def construire_messages_reformulation(question, historique=None):
    """Messages pour réécrire la question. historique = [{"question": …, "answer": …}, …], du plus ancien au plus récent."""
    lignes = []
    for echange in historique or []:
        reponse = re.sub(r"\s*\[\d+(?:\s*,\s*\d+)*\]", "", echange.get("answer", ""))  # → sans les citations [n]
        lignes.append(f"Étudiant : {echange.get('question', '')}\nAssistant : {reponse[:LONGUEUR_HISTORIQUE]}")
    contexte = "Échanges précédents :\n" + "\n\n".join(lignes) + "\n\n" if lignes else ""
    return [
        {"role": "system", "content": PROMPT_REFORMULATION},
        {"role": "user", "content": f"{contexte}Dernière question : {question}"},
    ]