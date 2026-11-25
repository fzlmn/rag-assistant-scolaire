// frontend/src/app/core/questions-exemples.ts
// =============================================================================
// RÔLE : questions prêtes à cliquer, affichées au-dessus de la barre de saisie (écran Conversation).
// Une par cas à montrer en démo ; pour en ajouter, il suffit d'ajouter une ligne.
// Fatima Zahra.
// =============================================================================

export const QUESTIONS_EXEMPLES: string[] = [
  "Combien de places de semestre d'études à l'étranger sont ouvertes au total ?", // → simple : 03 Charte (tableau sur 2 pages)
  "Comment créer un club et obtenir une subvention de l'École ?",                  // → synthèse : 05 Guide vie étudiante + 04 Calendrier
  "Quelle est la durée minimale d'un PFE en 2027 ?",                               // → version : 07 Note de service remplace 02 (18 et non 16 semaines)
  "Quel est le prix d'un repas au restaurant de l'École ?",                        // → hors corpus : restaurant décrit, sans prix → refus
];
