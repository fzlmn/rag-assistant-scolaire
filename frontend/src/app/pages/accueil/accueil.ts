// frontend/src/app/pages/accueil/accueil.ts — page d'accueil de l'EIH (contenu statique, sans appel à l'API)
// Chiffres et filières tirés des documents du corpus : l'accueil ne doit jamais contredire l'assistant.
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Logo } from '../../components/logo/logo';

@Component({ selector: 'app-accueil', imports: [RouterLink, Logo], templateUrl: './accueil.html', styleUrl: './accueil.css' })
export class Accueil {
  chiffres = [
    { valeur: '3', label: "filières d'ingénieur" },               // → Règlement, art. 2
    { valeur: '180', label: 'crédits ECTS en 3 ans' },            // → Règlement, art. 3
    { valeur: '18', label: 'clubs étudiants' },                   // → Guide de la vie étudiante, 4.1
    { valeur: '16', label: "places d'études à l'étranger" },      // → Charte de mobilité, 3
  ];
  formations = [                                                   // → les trois filières (Règlement, art. 2)
    { titre: 'IGL', texte: 'Informatique et Génie Logiciel' },
    { titre: 'SDIA', texte: 'Science des Données et Intelligence Artificielle' },
    { titre: 'CSR', texte: 'Cybersécurité et Réseaux' },
  ];
}
