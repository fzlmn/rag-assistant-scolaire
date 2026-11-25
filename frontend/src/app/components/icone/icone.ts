// frontend/src/app/components/icone/icone.ts
// =============================================================================
// RÔLE : icônes de navigation (SVG aux coins et traits arrondis), partagées par la barre du haut
// et le menu latéral : <app-icone nom="documents" />. La taille suit celle du texte (1.25em).
// =============================================================================

import { Component, input } from '@angular/core';

export type NomIcone = 'accueil' | 'conversation' | 'documents' | 'recherche';

@Component({
  selector: 'app-icone',
  template: `
    @switch (nom()) {
      @case ('accueil') {
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M3.5 10.5l7.8-6.4a1.1 1.1 0 0 1 1.4 0l7.8 6.4" />
          <path d="M5.5 9v10a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V9" />
          <path d="M10 21v-4.5a2 2 0 0 1 4 0V21" />
        </svg>
      }
      @case ('conversation') {
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 4h12a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3h-6l-4.6 3.4a.6.6 0 0 1-.9-.5V17H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3z" />
          <path d="M8 10.5h.01M12 10.5h.01M16 10.5h.01" stroke-width="2.4" />
        </svg>
      }
      @case ('documents') {
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M14 3H8a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h8a3 3 0 0 0 3-3V8z" />
          <path d="M14 3v3a2 2 0 0 0 2 2h3" />
          <path d="M9 13h6M9 17h4" />
        </svg>
      }
      @case ('recherche') {
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="6.5" />
          <path d="M20 20l-4.2-4.2" />
        </svg>
      }
    }`,
  styles: [`
    :host { display: inline-flex; flex: none; }
    svg {
      width: 1.25em; height: 1.25em; fill: none; stroke: currentColor;
      stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round;   /* → bouts et angles arrondis */
    }
  `],
})
export class Icone {
  nom = input.required<NomIcone>();                          // → quelle icône afficher
}
