// frontend/src/app/components/sources/sources.ts
// =============================================================================
// RÔLE : panneau des sources d'une réponse : document, section, page, date, score, extrait.
// La source citée sur laquelle on a cliqué est mise en évidence et affichée.
// SÉANCE 4 — Fatima Zahra. Exigence du sujet : panneau des sources.
// =============================================================================

import { Component, effect, input } from '@angular/core';   // → input() : données reçues du parent ; effect() : réaction

import { Source } from '../../core/models';                  // → forme d'une source

@Component({
  selector: 'app-sources',                                   // → s'utilise avec <app-sources>
  templateUrl: './sources.html',
  styleUrl: './sources.css',
})
export class Sources {
  sources = input<Source[]>([]);                             // → sources de la réponse sélectionnée
  selection = input<number | null>(null);                    // → numéro de la source cliquée ([2] → 2)

  constructor() {
    effect(() => {                                           // → se relance quand la sélection change
      const id = this.selection();
      if (id !== null) {
        setTimeout(() =>                                     // → attend que l'affichage soit à jour…
          document.getElementById(`source-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }),
        );                                                   // → …puis fait défiler jusqu'à la source
      }
    });
  }
}
