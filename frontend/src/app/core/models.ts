// frontend/src/app/core/models.ts
// =============================================================================
// RÔLE : interfaces TypeScript = la forme exacte des réponses de l'API (backend/app/main.py).
// SÉANCE 4 — Aya. Exigence du sujet : interfaces TypeScript.
// =============================================================================

export interface Source {          // → un fragment cité dans une réponse de /api/ask
  id: number;                      // → numéro utilisé dans la réponse : [1], [2]…
  chunk_id: string;                // → identifiant du fragment
  file: string;                    // → fichier PDF
  reference: string;               // → référence du document
  date: string;                    // → date de publication (AAAA-MM-JJ)
  page: number;                    // → page
  section: string | null;          // → section (ou null)
  excerpt: string;                 // → extrait du texte
  score: number;                   // → score de similarité
}

export interface ReponseQuestion { // → réponse de POST /api/ask
  answer: string;                  // → texte de la réponse (ou phrase de refus)
  found: boolean;                  // → false = refus hors corpus
  sources: Source[];               // → fragments fournis au modèle
  invalid_citations: number[];     // → numéros cités qui ne correspondent à aucun fragment
  latency_ms: number;              // → temps de réponse
  question_comprise?: string | null; // → la question telle que l'assistant l'a comprise (reformulée)
}

export interface EchangePrecedent { // → un échange déjà affiché, renvoyé à /api/ask (champ « history »)
  question: string;                // →   pour comprendre une question de suivi : « et la max ? »
  answer: string;
}

export interface Fragment {        // → un résultat de POST /api/search
  chunk_id: string;
  text: string;                    // → texte complet du fragment
  file: string;
  reference: string;
  doc_type: string;                // → type de document
  date: string;
  page: number;
  section: string | null;
  score: number;
}

export interface ReponseRecherche { // → réponse de POST /api/search
  question: string;
  results: Fragment[];
  latency_ms: number;
}

export interface DocumentInfo {    // → un élément de GET /api/documents
  file: string;
  title: string;
  reference: string;
  doc_type: string;
  date: string;
  version: string;
  status: string;
  pages: number;
  modifies: string[];              // → références des documents qu'il modifie
  nb_fragments: number;            // → nombre de fragments indexés (nom renvoyé par /api/documents)
}
