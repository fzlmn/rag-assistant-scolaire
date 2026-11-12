# Journal d'utilisation des outils d'IA générative

| Date | Membre | Outil | Partie concernée | Vérification effectuée |
|---|---|---|---|---|
| 2026-11-08 | Fatima Zahra | Claude (Anthropic) | Plan de travail par séance, répartition des tâches, première version commentée du code (séances 1 à 5), première version des 20 questions d'évaluation | Plan et répartition relus et validés par les deux membres ; le code est vérifié à chaque étape (lignes suivantes) |
| 2026-11-10 | Aya | Claude (Anthropic) | Découpage à taille fixe (étape 3) ; embeddings, base Chroma, routes /api/health, /api/ingest et /api/search (étape 4) | Code relu et compris ligne par ligne ; ingestion lancée deux fois sans doublons ; routes testées dans /docs (filtre par type, 422 sur question vide) ; tests pytest passés |
| 2026-11-12 | Fatima Zahra | Claude (Anthropic) | Extraction et découpage structurel (étape 2), route /api/documents (étape 5), relecture de la PR d'Aya, mise à jour du README | Code relu ligne par ligne ; 4 tests pytest ; fragments contrôlés dans chunks_structural.json (Q8, Calendrier, Note 07) ; /api/documents testé dans /docs ; branche d'Aya exécutée (7 tests, 11 appels de la démo) avant fusion |
