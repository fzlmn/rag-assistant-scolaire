# backend/app/prompt.py
# =============================================================================
# RÔLE : écrire le prompt envoyé au modèle.
#   - MESSAGE_REFUS        → phrase exacte imposée par le sujet quand l'information n'est pas dans le corpus
#   - PROMPT_SYSTEME       → règles que le modèle doit suivre
#   - formater_contexte()  → fragments numérotés [1], [2]… avec leurs métadonnées (référence, date, statut…)
#   - construire_messages() → messages « system » + « user » envoyés au modèle
# SÉANCE 3 — Fatima Zahra.
# Exigences du sujet (4.4) : répondre uniquement à partir des fragments, citer [1], [2],
# phrase de refus exacte, retenir le plus récent en cas de divergence et le signaler.
# =============================================================================

MESSAGE_REFUS = "Je ne trouve pas cette information dans les documents de l'École."
# → phrase imposée par le sujet, utilisée telle quelle dans le prompt, dans l'API et dans les tests

PROMPT_SYSTEME = f"""Tu es l'assistant scolaire de l'École d'Ingénieurs Hélianthe (EIH).
Tu réponds aux questions des étudiants en suivant strictement ces règles :
1. Réponds uniquement à partir des fragments fournis. N'utilise aucune connaissance extérieure et n'invente rien.
2. Après chaque affirmation, cite le ou les fragments utilisés sous la forme [1], [2]. N'utilise que les numéros des fragments fournis.
3. Si les fragments ne contiennent pas l'information demandée, réponds exactement par cette phrase, sans guillemets et sans rien ajouter : {MESSAGE_REFUS}
4. Si deux fragments donnent des règles différentes sur le même point, retiens celle du document le plus récent lorsque son statut indique qu'il modifie l'autre, et signale la divergence en citant les deux fragments.
5. Réponds en français, de façon courte et précise."""
# → règle 1 : pas d'invention ; règle 2 : citations ; règle 3 : refus exact ; règle 4 : versions ; règle 5 : forme


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


def construire_messages(question, fragments):
    """Messages au format « chat » : les règles (system), puis les fragments et la question (user)."""
    return [
        {"role": "system", "content": PROMPT_SYSTEME},          # → les règles à respecter
        {"role": "user", "content": f"Fragments :\n\n{formater_contexte(fragments)}\n\nQuestion : {question}"},
        # → le contexte numéroté, puis la question de l'étudiant
    ]