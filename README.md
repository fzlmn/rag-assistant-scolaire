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
