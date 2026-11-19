// frontend/src/app/app.ts
// =============================================================================
// RÔLE : composant racine : barre de navigation + emplacement où s'affiche l'écran choisi.
// SÉANCE 4 — Aya.
// =============================================================================

import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router'; // → liens et zone d'affichage

@Component({
  selector: 'app-root',                                      // → balise <app-root> de index.html
  imports: [RouterOutlet, RouterLink, RouterLinkActive],     // → composant standalone : il déclare ce qu'il utilise
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {}
