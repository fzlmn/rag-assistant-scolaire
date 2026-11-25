// frontend/src/app/app.ts — composant racine : barre du haut, menu latéral (hamburger) et écran courant
import { Component, HostListener, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';       // → transforme les événements du routeur en signal
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router'; // → liens et zone d'affichage
import { filter, map } from 'rxjs';

import { Icone } from './components/icone/icone';
import { Logo } from './components/logo/logo';

@Component({
  selector: 'app-root',                                      // → balise <app-root> de index.html
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Logo, Icone], // → composant standalone : il déclare ce qu'il utilise
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private router = inject(Router);
  menu = signal(false);                                      // → menu latéral ouvert ou fermé
  pleineLargeur = toSignal(                                  // → vrai sur l'écran Conversation : il prend toute la largeur
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),             // → à chaque changement d'écran…
      map(() => this.router.url.startsWith('/conversation')),  // → …est-ce la conversation ?
    ),
    { initialValue: false },
  );

  basculer(): void { this.menu.update((v) => !v); }
  fermer(): void { this.menu.set(false); }

  @HostListener('document:keydown.escape')                   // → la touche Échap ferme le menu
  echap(): void { this.fermer(); }
}
