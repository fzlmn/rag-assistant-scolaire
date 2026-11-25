// frontend/src/app/app.ts — composant racine : barre du haut, menu latéral (hamburger) et écran courant
import { Component, HostListener, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router'; // → liens et zone d'affichage

import { Icone } from './components/icone/icone';
import { Logo } from './components/logo/logo';

@Component({
  selector: 'app-root',                                      // → balise <app-root> de index.html
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Logo, Icone], // → composant standalone : il déclare ce qu'il utilise
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  menu = signal(false);                                      // → menu latéral ouvert ou fermé

  basculer(): void { this.menu.update((v) => !v); }
  fermer(): void { this.menu.set(false); }

  @HostListener('document:keydown.escape')                   // → la touche Échap ferme le menu
  echap(): void { this.fermer(); }
}
