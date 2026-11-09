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
  Interface Angular → API FastAPI → recherche top-k → prompt → LLM → réponse avec citations
```

---

## Technologies

| Composant | Choix |
|---|---|
| Backend | Python 3.11+, FastAPI, Pydantic |
| Extraction PDF | pdfplumber |
| Embeddings | `intfloat/multilingual-e5-small` (sentence-transformers) |
| Base vectorielle | Chroma (persistante sur disque) |
| LLM | Groq (clé dans `.env`), Ollama en secours |
| Frontend | Angular (composants standalone, TypeScript) |
| Tests | pytest |

---

## Structure du dépôt

```
rag-assistant-scolaire/
├── backend/
│   ├── app/
│   │   ├── config.py          chemins et paramètres
│   │   ├── extraction.py      PDF → texte par page + métadonnées
│   │   ├── chunking.py        découpage à taille fixe et structurel
│   │   ├── ingestion.py       extraction + découpage + export JSON
│   │   ├── embeddings.py      texte → vecteurs
│   │   ├── store.py           base Chroma : indexation et recherche
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
| POST | `/api/ask` | Recherche + génération avec citations *(séance 3)* | 422, 502 si le LLM ne répond pas |

Exemple :

```json
POST /api/search
{ "question": "Quelle est la durée minimale d'un PFE ?", "top_k": 5, "filters": { "type": null } }
```

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
| 1 | Extraction et découpage : fragments et métadonnées en JSON | Personne 1 (extraction, structurel) + Personne 2 (taille fixe) | En cours |
| 2 | Indexation et recherche : `/api/ingest` et `/api/search` testés dans `/docs` | Personne 2 (embeddings, Chroma, API) + Personne 1 (`/api/documents`) | En cours |
| 3 | Génération : `/api/ask` avec citations, refus et seuil | | À faire |
| 4 | Frontend : conversation, sources, gestion des erreurs | | À faire |
| 5 | Évaluation : jeu de test, script, comparaison de configurations | | À faire |

### Journal

- **Semaine du 2 novembre 2026** — Mise en place du dépôt et du README.

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

- Une branche par séance ou par tâche (`feat/seances-1-2`, `feat/generation`…), fusionnée dans `main` par une pull request relue par l'autre membre.
- Messages de commit : `feat: …`, `fix: …`, `test: …`, `docs: …`.
- Aucune clé d'API dans le dépôt : elles vont dans un fichier `.env` (ignoré par Git).

## Équipe

- Ait Lamine Fatima Zahra — [@fzlmn](https://github.com/fzlmn)
- Anam Aya — [@ayaaas](https://github.com/ayaaas)

## Utilisation de l'IA générative

Les outils d'IA générative utilisés pendant le projet sont déclarés au fil de l'eau dans `docs/journal-ia.md` (outil, partie concernée, vérification effectuée). Ce journal sert à l'annexe du rapport.


## Travail réalisé — Aya

Cette partie du projet concerne le découpage en taille fixe, la génération des embeddings, l'indexation vectorielle avec ChromaDB et la mise en place des endpoints API pour l'ingestion et la recherche documentaire.

### 1. Fonctionnalités développées

#### 1.1. Découpage en taille fixe

Ajout de la fonction `decouper_taille_fixe()` dans `backend/app/chunking.py`.

- Taille par défaut : **500 caractères**.
- Chevauchement : **100 caractères**.
- Conservation des métadonnées des fragments.
- Possibilité de choisir entre deux stratégies :
  - `structural` : découpage selon la structure du document.
  - `fixed` : découpage selon une taille fixe.

Les deux stratégies sont disponibles dans le module d'ingestion.

#### 1.2. Génération des embeddings

Création de `backend/app/embeddings.py`.

Le modèle utilisé est :

`intfloat/multilingual-e5-small`

Ce modèle transforme les textes en vecteurs numériques de dimension 384.

Deux fonctions principales sont disponibles :

- `encoder_passages()` : génère les embeddings des fragments documentaires.
- `encoder_requete()` : génère l'embedding d'une question utilisateur.

Les préfixes `passage:` et `query:` sont utilisés conformément au fonctionnement du modèle E5.

#### 1.3. Indexation et recherche vectorielle

Création de `backend/app/vectorstore.py`.

La base vectorielle utilisée est **ChromaDB**, en mode persistant.

Fonctionnalités :
- Indexation des fragments et de leurs embeddings.
- Conservation des identifiants et métadonnées.
- Recherche sémantique à partir d'une question.
- Retour des fragments les plus proches avec leur distance.

Les données sont stockées dans :

`data/vectorstore/`

#### 1.4. API FastAPI

Création de `backend/app/main.py` avec trois endpoints.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Vérifie le fonctionnement de l'API |
| POST | `/api/ingest` | Extrait, découpe et indexe les documents |
| POST | `/api/search` | Recherche les fragments pertinents |

**Remarque :** l'endpoint `/api/documents` n'est pas inclus dans cette partie, car il appartient à une autre tâche du projet.

---

### 2. Installation et préparation

Depuis la racine du projet :

```bash
source backend/.venv/bin/activate
cd backend
```

Si l'environnement virtuel n'existe pas encore :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Exécution des tests

Depuis le dossier `backend/` :

```bash
python -m pytest -v
```

Résultat obtenu :

```text
tests/test_extraction_decoupage.py::test_structurel_garde_question_et_reponse_ensemble PASSED
tests/test_extraction_decoupage.py::test_ligne_de_tableau_devient_phrase PASSED
tests/test_extraction_decoupage.py::test_pas_d_entete_ni_de_pied_de_page PASSED
tests/test_extraction_decoupage.py::test_note_de_service_declare_ce_quelle_modifie PASSED

=========================== 4 passed ===========================
```

Les quatre tests existants passent après l'ajout du découpage en taille fixe.

### 4. Lancer l'API

Toujours depuis `backend/` :

```bash
python -m uvicorn app.main:app --reload --port 8001
```

L'API est accessible à :

`http://127.0.0.1:8001`

La documentation interactive Swagger est disponible à :

`http://127.0.0.1:8001/docs`

Si le port 8001 est déjà utilisé par une instance précédente, réutiliser celle-ci au lieu de lancer une deuxième instance.

### 5. Tester les endpoints

#### 5.1. Vérifier l'état de l'API

```bash
curl http://127.0.0.1:8001/api/health
```

Résultat attendu :

```json
{
  "status": "ok",
  "message": "RAG Assistant Scolaire fonctionne."
}
```

#### 5.2. Lancer l'ingestion

```bash
curl -X POST http://127.0.0.1:8001/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "strategie": "fixed",
    "taille": 500,
    "chevauchement": 100
  }'
```

Résultat obtenu lors du test :

```json
{
  "message": "Ingestion terminée avec succès.",
  "strategie": "fixed",
  "nombre_documents": 7,
  "nombre_fragments": 104,
  "nombre_chunks_indexes": 104
}
```

L'ingestion effectue les opérations suivantes :

1. Extraction du contenu des PDF.
2. Découpage en fragments de taille fixe.
3. Génération des embeddings.
4. Indexation des fragments dans ChromaDB.

Il est également possible de choisir la stratégie structurelle :

```json
{
  "strategie": "structural"
}
```

#### 5.3. Tester la recherche sémantique

```bash
curl -X POST http://127.0.0.1:8001/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment valider mon diplôme d ingénieur ?",
    "top_k": 5
  }'
```

La réponse contient :

- La question envoyée.
- Le nombre de résultats.
- Les fragments retrouvés.
- Les métadonnées associées.
- La distance calculée par ChromaDB.

**Interprétation :** une distance plus faible indique généralement une meilleure proximité vectorielle. Elle ne représente pas directement un pourcentage de pertinence.

---

### 6. Résultats obtenus

| Élément | Résultat |
|---|---|
| Documents traités | 7 |
| Fragments en taille fixe | 104 |
| Modèle d'embeddings | multilingual-e5-small |
| Dimension des vecteurs | 384 |
| Base vectorielle | ChromaDB |
| Tests existants | 4/4 réussis |
| API | Health, Ingest, Search |

### 7. Fichiers concernés

```text
backend/
├── app/
│   ├── chunking.py
│   ├── ingestion.py
│   ├── embeddings.py
│   ├── vectorstore.py
│   └── main.py
└── tests/
    └── test_extraction_decoupage.py

data/
├── processed/
│   └── chunks_fixed.json
└── vectorstore/
```

### 8. Prochaine étape

La prochaine étape consiste à intégrer la génération de réponses avec un LLM, la gestion des versions documentaires, le filtrage des résultats selon un seuil de pertinence et l'endpoint `/api/ask`.

Cette étape sera réalisée en coordination avec le développement du client LLM et du système de citations.