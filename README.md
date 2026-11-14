# Assistant scolaire RAG

Assistant scolaire RAG : répond aux questions des étudiants à partir des documents officiels d'une école, avec citations des sources et refus hors corpus.

Projet du module **Applications Avancées de l'IA** (3ACINFO, 2026-2027) — application RAG (Retrieval-Augmented Generation) avec un backend FastAPI et un frontend Angular.

---

## Objectif

L'application répond aux questions des étudiants de l'École d'Ingénieurs Hélianthe (EIH, école fictive) **uniquement** à partir de ses 7 documents officiels :

- elle cite ses sources sous la forme [1], [2] ;
- elle répond « Je ne trouve pas cette information dans les documents de l'École. » quand la réponse n'est pas dans le corpus ;
- quand deux documents se contredisent, elle retient le plus récent s'il se déclare modificatif, et le signale.

---

## Architecture

```
Ingestion (une fois) :
  PDF → extraction (texte, tableaux, métadonnées) → découpage → embeddings → base vectorielle Chroma

Question (à chaque requête) :
  Interface Angular → API FastAPI → recherche top-k → seuil de score → prompt → LLM → vérification des citations → réponse citée
```

---

## Technologies

| Composant | Choix |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic |
| Extraction PDF | pdfplumber |
| Embeddings | `intfloat/multilingual-e5-small` (sentence-transformers) |
| Base vectorielle | Chroma (persistante sur disque) |
| LLM | Groq (clé dans `.env`) ou Ollama (modèle local), au choix dans `.env` |
| Frontend | Angular (composants standalone, TypeScript) |
| Tests | pytest |

---

## Structure du dépôt

```
rag-assistant-scolaire/
├── backend/
│   ├── app/
│   │   ├── config.py          chemins et paramètres (.env, seuil de refus)
│   │   ├── extraction.py      PDF → texte par page + métadonnées
│   │   ├── chunking.py        découpage à taille fixe et structurel
│   │   ├── ingestion.py       extraction + découpage + export JSON
│   │   ├── embeddings.py      texte → vecteurs
│   │   ├── store.py           base Chroma : indexation et recherche
│   │   ├── prompt.py          prompt système et mise en forme du contexte
│   │   ├── llm.py             client LLM (Groq ou Ollama)
│   │   ├── citations.py       vérification des citations [n]
│   │   ├── rag.py             chaîne question → recherche → seuil → LLM → citations
│   │   └── main.py            API FastAPI
│   ├── tests/                 tests pytest
│   └── requirements.txt
├── frontend/                  application Angular (séance 4)
├── data/
│   ├── corpus/                les 7 PDF fournis
│   ├── processed/             fragments et métadonnées en JSON
│   └── vectorstore/           base Chroma (non versionnée)
├── eval/                      jeu de test et script d'évaluation (séance 5)
├── docs/                      rapport, journal d'utilisation de l'IA
├── .env.example               modèle du fichier .env
└── README.md
```

---

## Installation

Prérequis : Python 3.11 ou plus récent, Git.

```powershell
git clone https://github.com/fzlmn/rag-assistant-scolaire.git
cd rag-assistant-scolaire\backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sous Linux / macOS : `python3 -m venv .venv` puis `source .venv/bin/activate`.

Au premier lancement, le modèle d'embeddings (≈ 470 Mo) est téléchargé automatiquement.

---

## Variables d'environnement

Copier le modèle à la racine du dépôt, puis le remplir. Le fichier `.env` est ignoré par Git : aucune clé n'est jamais commitée.

```bash
cp .env.example .env
```

| Variable | Rôle | Exemple |
|---|---|---|
| `LLM_PROVIDER` | `groq` (API en ligne) ou `ollama` (modèle local) | `groq` |
| `GROQ_API_KEY` | clé Groq (si `groq`) | `gsk_...` |
| `LLM_MODEL` | modèle appelé | `openai/gpt-oss-120b` ou `llama3.2` |
| `OLLAMA_URL` | adresse d'Ollama (si `ollama`) | `http://localhost:11434` |
| `LLM_TIMEOUT` | délai maximal d'attente du LLM, en secondes | `30` (prévoir `120` pour un modèle local) |
| `SCORE_THRESHOLD` | seuil de refus : si le meilleur score de la recherche est inférieur, l'API refuse sans appeler le LLM | `0.80` (à calibrer) |
| `EMBEDDING_MODEL` | modèle d'embeddings (facultatif) | `intfloat/multilingual-e5-small` |

Exemple pour un modèle local avec Ollama :

```
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_TIMEOUT=120
```

Le fichier `.env` est lu au démarrage : relancer l'API après l'avoir modifié.

---

## Utilisation

Toutes les commandes se lancent depuis `backend/`, avec l'environnement virtuel activé.

**Générer les fragments en JSON** (sans base vectorielle) :

```powershell
python -m app.ingestion
```

**Lancer l'API :**

```powershell
uvicorn app.main:app --reload
```

Documentation interactive : http://localhost:8000/docs

**Lancer les tests :**

```powershell
python -m pytest -v
```

---

## API

Toutes les routes sont préfixées par `/api`.

| Méthode | Route | Rôle | Erreurs |
|---|---|---|---|
| GET | `/api/health` | État du service et nombre de fragments indexés | 503 si la base est indisponible |
| POST | `/api/ingest` | (Ré)indexation : `strategy`, `chunk_size`, `overlap` | 422 si paramètres invalides |
| GET | `/api/documents` | Documents indexés, métadonnées, nombre de fragments | 503 si la base est indisponible |
| POST | `/api/search` | Recherche seule, sans LLM : fragments et scores | 422 si question vide |
| POST | `/api/ask` | Recherche + génération avec citations, refus hors corpus et seuil | 422 ; 502 si le LLM ne répond pas ; 503 si la base est indisponible |

Exemple `/api/search` :

```json
POST /api/search
{ "question": "Quelle est la durée minimale d'un PFE ?", "top_k": 5, "filters": { "type": null } }
```

Exemple `/api/ask` :

```json
POST /api/ask
{ "question": "Quelle est la durée minimale d'un PFE qui commence en février 2027 ?", "top_k": 5, "filters": { "type": null } }
```

Réponse :

```json
{
  "answer": "… [1] …",
  "found": true,
  "sources": [
    { "id": 1, "chunk_id": "…", "file": "…", "reference": "…", "date": "…", "page": 1, "section": "…", "excerpt": "…", "score": 0.0 }
  ],
  "invalid_citations": [],
  "latency_ms": 0
}
```

Hors corpus : `found` vaut `false`, `answer` contient la phrase de refus et `sources` est vide. Le numéro `id` de chaque source est celui que le modèle cite dans la réponse ([1], [2]…).

---

## Corpus

| # | Document | Référence | Type | Publié le |
|---|---|---|---|---|
| 01 | Règlement des études 2026-2027 | EIH-DE-REG-2026 | Règlement officiel | 10/07/2026 |
| 02 | Guide des stages et du PFE | EIH-SRE-GUIDE-2026 | Guide pratique | 15/06/2026 |
| 03 | Charte de mobilité internationale | EIH-BRI-CHARTE-2026 | Charte et procédure | 20/04/2026 |
| 04 | Calendrier académique 2026-2027 | EIH-DE-CAL-2026 | Calendrier officiel | 10/07/2026 |
| 05 | Guide de la vie étudiante | EIH-BVE-GUIDE-2026 | Guide d'information | 01/09/2026 |
| 06 | FAQ Scolarité | EIH-SCOL-FAQ-2026 | FAQ | 21/09/2026 |
| 07 | Note de service n° 2026-14 | EIH-DE-NS-2026-14 | Note de service (texte modificatif) | 05/10/2026 |

La Note de service 2026-14 modifie le Guide des stages : durée minimale du PFE (16 → 18 semaines) et délai de dépôt du rapport (10 → 14 jours).

---

## Avancement

*Mis à jour chaque semaine par la personne qui a terminé sa partie.*

| Séance | Jalon | Responsable | État |
|---|---|---|---|
| 1 | Extraction et découpage : fragments et métadonnées en JSON | Fatima Zahra (extraction, structurel) + Aya (taille fixe) | Terminé |
| 2 | Indexation et recherche : `/api/ingest` et `/api/search` testés dans `/docs` | Aya (embeddings, Chroma, API) + Fatima Zahra (`/api/documents`) | Terminé |
| 3 | Génération : `/api/ask` avec citations, refus et seuil | Fatima Zahra (prompt, client LLM, citations) + Aya (`/api/ask`, seuil) | Terminé (test commun avec le vrai LLM à finaliser) |
| 4 | Frontend : conversation, sources, gestion des erreurs | | À faire |
| 5 | Évaluation : jeu de test, script, comparaison de configurations | | À faire |

### Journal

- **Semaine du 2 novembre 2026** — Mise en place du dépôt et du README.
- **Semaine du 9 novembre 2026** — Séances 1 et 2 terminées : extraction (texte, tableaux, métadonnées) et découpage structurel (Fatima Zahra), découpage à taille fixe, embeddings e5, base Chroma, routes health/ingest/search (Aya), route documents (Fatima Zahra). 104 / 93 fragments, 7 tests.
- **Semaine du 9 novembre 2026 (suite)** — Séance 3 : prompt, client LLM et vérification des citations (Fatima Zahra) ; route `/api/ask`, seuil de refus configurable et tests avec LLM simulé (Aya). 17 tests.

---

## Livrables

- [ ] Dépôt Git partagé avec l'enseignant, commits réguliers
- [ ] README : installation, variables d'environnement, lancement, choix techniques
- [ ] Au moins 5 tests pytest, dont un sur le découpage et un sur le refus hors corpus
- [ ] Rapport de 6 pages maximum (architecture, choix, résultats, limites)
- [ ] Annexe : déclaration d'utilisation des outils d'IA générative
- [ ] Soutenance de 15 minutes avec démonstration en direct

---

## Organisation

- Une branche par séance ou par tâche (`feat/seances-1-2`, `feat/ask`…), fusionnée dans `main` par une pull request relue par l'autre membre.
- Messages de commit : `feat: …`, `fix: …`, `test: …`, `docs: …`.
- Aucune clé d'API dans le dépôt : elles vont dans un fichier `.env` (ignoré par Git).

## Équipe

- Ait Lamine Fatima Zahra — [@fzlmn](https://github.com/fzlmn)
- Anam Aya — [@ayaaas](https://github.com/ayaaas)

## Utilisation de l'IA générative

Les outils d'IA générative utilisés pendant le projet sont déclarés au fil de l'eau dans `docs/journal-ia.md` (outil, partie concernée, vérification effectuée). Ce journal sert à l'annexe du rapport.


## Travail réalisé — Aya

Cette partie du projet concerne le découpage en taille fixe, la génération des embeddings, l'indexation vectorielle avec ChromaDB (une collection par stratégie), les endpoints API d'ingestion, de recherche et d'état du service, puis la route de génération `/api/ask` avec son seuil de refus.

### 1. Fonctionnalités développées

#### 1.1. Découpage en taille fixe

Fonction `decouper_taille_fixe()` dans `backend/app/chunking.py`.

- Taille par défaut : **500 caractères**.
- Chevauchement : **100 caractères**.
- Conservation des métadonnées des fragments.
- Deux stratégies disponibles dans le module d'ingestion :
  - `structural` : découpage selon la structure du document.
  - `fixed` : découpage selon une taille fixe.

#### 1.2. Génération des embeddings

Module `backend/app/embeddings.py`.

Le modèle utilisé est `intfloat/multilingual-e5-small`. Il transforme les textes en vecteurs de dimension 384.

- `encoder_passages()` : embeddings des fragments documentaires (préfixe `passage:`).
- `encoder_requete()` : embedding d'une question (préfixe `query:`).
- `generer_embeddings_chunks()` : un embedding par fragment, dans le même ordre.

Les embeddings ne sont calculés que pour les fragments nouveaux (voir 1.3).

#### 1.3. Stockage et recherche vectorielle

Module `backend/app/store.py`, basé sur **ChromaDB** en mode persistant (`data/vectorstore/`).

**Une collection par stratégie**, afin que les fragments ne se mélangent jamais et que les deux stratégies restent comparables :

| Stratégie | Collection |
|---|---|
| `structural` | `eih_structural` |
| `fixed` (500 / 100) | `eih_fixed_500_100` |

Pour une autre taille ou un autre chevauchement, la collection prend le nom `eih_fixed_<taille>_<chevauchement>`.

Fonctionnalités :
- **Ingestion idempotente** : `ajouter_chunks()` n'ajoute que les fragments absents et retourne `added` et `skipped`. Relancer la même ingestion retourne `added: 0`, sans recalcul d'embeddings.
- **Collection active** : `collection_active()` retourne la dernière collection ingérée. Elle lève `BaseIndisponible` si aucune ingestion n'a eu lieu ou si la base est vide.
- **Recherche** : `rechercher()` retourne les k fragments les plus proches avec `score = 1 - distance`, et accepte un filtre par type de document (`where={"doc_type": ...}`).

#### 1.4. API FastAPI

Module `backend/app/main.py`.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Nombre de fragments indexés ; **503** si la base est vide ou indisponible |
| POST | `/api/ingest` | Extrait, découpe et indexe ; retourne `added` et `skipped` ; écrit `documents.json` |
| POST | `/api/search` | Recherche sans LLM : fragments et scores, avec filtre `filters.type` |
| POST | `/api/ask` | Recherche, seuil, génération et vérification des citations (voir 9) |

Validations (erreur **422**) :
- question vide ou composée uniquement d'espaces (`StringConstraints(strip_whitespace=True, min_length=1)`) ;
- `overlap >= chunk_size` (`model_validator`).

L'ingestion écrit `data/processed/documents.json` (métadonnées de chaque document et nombre de fragments), utilisé par l'endpoint `/api/documents`, qui appartient à une autre tâche du projet.

---

### 2. Installation et préparation

Depuis la racine du projet :

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
cp .env.example .env     # puis remplir .env (voir « Variables d'environnement »)
```

### 3. Exécution des tests

Depuis le dossier `backend/` :

```bash
python -m pytest -v
```

Résultat obtenu :

```text
tests/test_ask.py::test_refus_hors_corpus_sans_appeler_le_llm PASSED
tests/test_ask.py::test_reponse_avec_sources PASSED
tests/test_ask.py::test_citation_invalide_signalee PASSED
tests/test_ask.py::test_refus_du_llm_donne_found_false PASSED
tests/test_ask.py::test_llm_en_panne_renvoie_502 PASSED
tests/test_ask.py::test_question_vide_renvoie_422 PASSED
tests/test_extraction_decoupage.py::test_structurel_garde_question_et_reponse_ensemble PASSED
tests/test_extraction_decoupage.py::test_ligne_de_tableau_devient_phrase PASSED
tests/test_extraction_decoupage.py::test_pas_d_entete_ni_de_pied_de_page PASSED
tests/test_extraction_decoupage.py::test_note_de_service_declare_ce_quelle_modifie PASSED
tests/test_generation.py::test_extraire_citations_simples_et_groupees PASSED
tests/test_generation.py::test_citation_invalide_detectee PASSED
tests/test_generation.py::test_prompt_contient_regles_et_contexte_numerote PASSED
tests/test_generation.py::test_llm_sans_cle_leve_erreur PASSED
tests/test_recherche.py::test_taille_fixe_max_500_caracteres PASSED
tests/test_recherche.py::test_question_vide_renvoie_422 PASSED
tests/test_recherche.py::test_ingestion_idempotente PASSED

=========================== 17 passed ===========================
```

| Fichier | Test | Vérifie |
|---|---|---|
| `test_extraction_decoupage.py` | structurel | Une question de la FAQ et sa réponse restent ensemble |
| | tableau | Les lignes de tableau gardent leurs en-têtes |
| | en-têtes / pieds de page | Ils sont supprimés |
| | note de service | Les métadonnées de la note modificative sont correctes |
| `test_recherche.py` | taille fixe | Chaque fragment contient au maximum 500 caractères |
| | question vide | `POST /api/search` avec `"   "` retourne 422 |
| | idempotence | Deux ingestions identiques : le 2e appel retourne `added: 0` |
| `test_generation.py` | citations | Extraction des `[n]` et détection d'un numéro sans fragment |
| | prompt | La phrase de refus, les fragments numérotés, la référence et la date sont présents |
| | LLM sans clé | `ErreurLLM` levée (→ 502) |
| `test_ask.py` | refus hors corpus | Score sous le seuil : refus et **le LLM n'est pas appelé** |
| | réponse avec sources | `found: true`, sources numérotées, aucune citation invalide |
| | citation invalide | Un numéro cité sans fragment est signalé dans `invalid_citations` |
| | refus du modèle | Le modèle répond par la phrase de refus : `found: false` |
| | LLM en panne | `/api/ask` retourne 502 |
| | question vide | `/api/ask` retourne 422 |

Les tests de `/api/ask` remplacent la recherche et le LLM par des versions simulées : ils n'ont besoin ni de clé, ni d'internet, ni de base vectorielle.

### 4. Lancer l'API

Depuis `backend/` :

```bash
python -m uvicorn app.main:app --reload --port 8001
```

- API : `http://127.0.0.1:8001`
- Swagger : `http://127.0.0.1:8001/docs`

Si le port est déjà utilisé par une instance précédente, arrêter celle-ci (`ss -ltnp | grep 8001`) ou choisir un autre port.

### 5. Tester les endpoints

#### 5.1. État de l'API

```bash
curl -i http://127.0.0.1:8001/api/health
```

Avant toute ingestion (base vide) : **503**. Après ingestion :

```json
{
  "status": "ok",
  "fragments": 104
}
```

#### 5.2. Ingestion

```bash
curl -X POST http://127.0.0.1:8001/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "fixed",
    "chunk_size": 500,
    "overlap": 100
  }'
```

Premier appel :

```json
{
  "strategy": "fixed",
  "collection": "eih_fixed_500_100",
  "documents": 7,
  "fragments": 104,
  "added": 104,
  "skipped": 0
}
```

Deuxième appel identique (idempotence) :

```json
{
  "strategy": "fixed",
  "collection": "eih_fixed_500_100",
  "documents": 7,
  "fragments": 104,
  "added": 0,
  "skipped": 104
}
```

L'ingestion effectue :

1. l'extraction du contenu des PDF ;
2. le découpage selon la stratégie choisie ;
3. l'écriture de `documents.json` ;
4. le calcul des embeddings des seuls fragments absents de la collection ;
5. l'indexation dans la collection de la stratégie, qui devient la collection active.

Stratégie structurelle :

```json
{
  "strategy": "structural"
}
```

Paramètres invalides (`overlap >= chunk_size`) : réponse **422**.

#### 5.3. Recherche sémantique

```bash
curl -X POST http://127.0.0.1:8001/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment valider mon diplôme d ingénieur ?",
    "top_k": 5,
    "filters": {"type": null}
  }'
```

La réponse contient :

- la question envoyée ;
- le nombre de résultats ;
- les fragments retrouvés, avec leurs métadonnées ;
- un `score` pour chaque fragment.

**Filtre par type de document** : renseigner `filters.type` avec la valeur du champ `doc_type` (visible dans `metadata.doc_type` et dans `documents.json`). Seuls les fragments de ce type sont retournés.

**Interprétation :** `score = 1 - distance` (similarité cosinus). Plus le score est élevé, plus le fragment est proche de la question. Il ne représente pas directement un pourcentage de pertinence ; il sert à fixer le seuil de refus de `/api/ask`.

**Erreurs :**

| Cas | Code |
|---|---|
| Question vide ou espaces seuls | 422 |
| Aucune ingestion ou base vide | 503 |

#### 5.4. Question avec réponse citée

```bash
curl -X POST http://127.0.0.1:8001/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la durée minimale d un PFE qui commence en février 2027 ?",
    "top_k": 5,
    "filters": {"type": null}
  }'
```

Question hors corpus (refus attendu, sans appel au LLM) :

```bash
curl -X POST http://127.0.0.1:8001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel est le prix d un repas au restaurant de l École ?"}'
```

---

### 6. Résultats obtenus

| Élément | Résultat |
|---|---|
| Documents traités | 7 |
| Fragments en taille fixe | 104 |
| Modèle d'embeddings | multilingual-e5-small |
| Dimension des vecteurs | 384 |
| Base vectorielle | ChromaDB, une collection par stratégie |
| Idempotence | 2e ingestion : `added: 0` |
| Tests | 17/17 réussis |
| API | Health, Ingest, Search, Ask |
| Seuil de refus | 0.xx (calibré sur une question du corpus et une question hors corpus) |

### 7. Fichiers concernés

```text
backend/
├── app/
│   ├── chunking.py
│   ├── ingestion.py
│   ├── embeddings.py
│   ├── store.py
│   ├── rag.py
│   ├── config.py        (ajout de SEUIL_SCORE)
│   └── main.py
└── tests/
    ├── test_extraction_decoupage.py
    ├── test_recherche.py
    └── test_ask.py

data/
├── processed/
│   ├── chunks_fixed.json
│   └── documents.json
└── vectorstore/
```

### 8. Prochaine étape

La prochaine étape est l'interface Angular (séance 4), puis l'évaluation du système avec le jeu de questions et le recalibrage du seuil (séance 5).

### 9. Génération : `/api/ask` et seuil de refus

Module `backend/app/rag.py`, fonction `repondre()`. Elle s'appuie sur le prompt, le client LLM et la vérification des citations écrits par Fatima Zahra (`prompt.py`, `llm.py`, `citations.py`).

1. `rechercher()` récupère les k fragments les plus proches (avec filtre éventuel par type).
2. **Seuil** : si le meilleur score est inférieur à `SCORE_THRESHOLD`, l'API renvoie la phrase de refus avec `found: false`, **sans appeler le LLM**.
3. Le prompt présente chaque fragment avec sa référence, sa date et son statut. Le modèle peut ainsi retenir le document le plus récent qui se déclare modificatif et signaler la divergence, sans règle écrite en dur pour ce corpus.
4. Si le modèle répond lui-même par la phrase de refus, `found` vaut `false` et `sources` est vide.
5. `citations_invalides()` remplit `invalid_citations` : les numéros cités qui ne correspondent à aucun fragment fourni.
6. Les sources sont numérotées dans le même ordre que dans le prompt : `[1]` dans la réponse correspond à la source d'`id` 1. Chaque source contient `chunk_id`, `file`, `reference`, `date`, `page`, `section`, `excerpt` (300 caractères au plus) et `score`.

Erreurs :

| Cas | Code |
|---|---|
| Question vide, `top_k` hors de 1 à 20 | 422 |
| LLM injoignable, clé absente, délai dépassé | 502 |
| Aucune ingestion ou base vide | 503 |

Calibrage du seuil : le meilleur score d'une question du corpus était de **0.xx**, celui d'une question hors corpus de **0.xx** ; le seuil retenu est **0.xx**. Il sera recalibré avec le jeu de test lors de l'évaluation (séance 5).