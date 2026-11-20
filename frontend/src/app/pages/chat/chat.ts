// frontend/src/app/pages/chat/chat.ts
// =============================================================================
// RÔLE : écran Conversation : saisie, historique de la session, citations [1], [2] cliquables,
// réglages top_k et type, indicateur de chargement, style distinct pour les refus.
// SÉANCE 4 — Fatima Zahra. Exigences du sujet (6) : écran Conversation et exigences d'interface.
// =============================================================================

import { Component, OnInit, inject, signal } from '@angular/core'; // → signal() : valeur qui met l'écran à jour
import { FormsModule } from '@angular/forms';                // → [(ngModel)] pour lier les champs du formulaire

import { Sources } from '../../components/sources/sources';  // → panneau des sources
import { ReponseQuestion, Source } from '../../core/models';  // → formes des données
import { RagApiService } from '../../core/rag-api.service';   // → appels à l'API

interface Morceau {                                          // → un morceau de la réponse affichée
  texte?: string;                                            // → texte normal…
  citations?: number[];                                      // → …ou une citation [1] / [2, 3]
}

interface Echange {                                          // → une question et ce qu'on a reçu
  question: string;
  reponse?: ReponseQuestion;                                 // → réponse de l'API (si réussie)
  morceaux?: Morceau[];                                      // → réponse découpée pour rendre les citations cliquables
  erreur?: string;                                           // → message d'erreur (si échec)
}

export function decouper(texte: string): Morceau[] {
  // → « A [1] B [2, 3] » → [{texte:"A "}, {citations:[1]}, {texte:" B "}, {citations:[2,3]}]
  const morceaux: Morceau[] = [];
  const motif = /\[(\d+(?:\s*,\s*\d+)*)\]/g;                 // → même motif que citations.py côté backend
  let debut = 0;                                             // → position après la dernière citation
  for (const m of texte.matchAll(motif)) {                   // → chaque citation trouvée
    if (m.index! > debut) morceaux.push({ texte: texte.slice(debut, m.index) }); // → texte avant la citation
    morceaux.push({ citations: m[1].split(',').map((n) => Number(n.trim())) });   // → numéros cités
    debut = m.index! + m[0].length;                          // → on continue après la citation
  }
  if (debut < texte.length) morceaux.push({ texte: texte.slice(debut) }); // → texte restant
  return morceaux;
}

@Component({
  selector: 'app-chat',
  imports: [FormsModule, Sources],                           // → formulaire + panneau des sources
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat implements OnInit {
  private api = inject(RagApiService);                       // → service d'appel à l'API

  question = '';                                             // → texte saisi
  topK = 5;                                                  // → nombre de fragments (réglable)
  type: string | null = null;                                // → filtre par type (null = tous)
  types = signal<string[]>([]);                              // → types disponibles, lus dans /api/documents
  echanges = signal<Echange[]>([]);                          // → historique de la session
  enCours = signal(false);                                   // → vrai pendant un appel : chargement + bouton désactivé
  sourcesAffichees = signal<Source[]>([]);                   // → sources montrées dans le panneau
  selection = signal<number | null>(null);                   // → numéro de la source cliquée

  ngOnInit(): void {
    this.api.documents().subscribe({                         // → au démarrage, récupère les documents…
      next: (docs) => this.types.set([...new Set(docs.map((d) => d.doc_type))]), // → …pour lister les types sans doublon
      error: () => this.types.set([]),                       // → si la base n'est pas prête, pas de filtre proposé
    });
  }

  envoyer(): void {
    const question = this.question.trim();                   // → enlève les espaces autour
    if (!question || this.enCours()) return;                 // → rien à envoyer, ou un appel déjà en cours
    this.enCours.set(true);                                  // → affiche le chargement, désactive le bouton
    this.question = '';                                      // → vide le champ de saisie
    const index = this.echanges().length;                    // → position de ce nouvel échange
    this.echanges.update((liste) => [...liste, { question }]); // → ajoute la question à l'historique
    this.api.poser(question, this.topK, this.type).subscribe({
      next: (reponse) => {                                   // → réponse reçue
        this.modifier(index, { reponse, morceaux: decouper(reponse.answer) });
        this.sourcesAffichees.set(reponse.sources);          // → le panneau montre les sources de la dernière réponse
        this.selection.set(null);
        this.enCours.set(false);
      },
      error: (e: Error) => {                                 // → erreur (message préparé par l'intercepteur)
        this.modifier(index, { erreur: e.message });
        this.enCours.set(false);
      },
    });
  }

  choisirSource(index: number, id: number): void {
    // → clic sur une citation : affiche les sources de cette réponse et met la source [id] en évidence
    this.sourcesAffichees.set(this.echanges()[index].reponse?.sources ?? []);
    this.selection.set(id);
  }

  private modifier(index: number, valeurs: Partial<Echange>): void {
    this.echanges.update((liste) => liste.map((e, i) => (i === index ? { ...e, ...valeurs } : e)));
    // → crée une nouvelle liste où seul l'échange « index » est complété (le signal prévient l'écran)
  }
}
