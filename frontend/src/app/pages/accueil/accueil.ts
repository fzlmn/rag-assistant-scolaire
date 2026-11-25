// frontend/src/app/pages/accueil/accueil.ts — page d'accueil de l'EIH (contenu statique, sans appel à l'API)
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Logo } from '../../components/logo/logo';

@Component({ selector: 'app-accueil', imports: [RouterLink, Logo], templateUrl: './accueil.html', styleUrl: './accueil.css' })
export class Accueil {
  chiffres = [
    { valeur: '4 200', label: 'étudiants' }, { valeur: '18', label: 'laboratoires' },
    { valeur: '92 %', label: 'insérés à 6 mois' }, { valeur: '45', label: 'universités partenaires' },
  ];
  formations = [
    { titre: 'Ingénierie numérique', texte: 'Informatique, données et systèmes : du code à la mise en production.' },
    { titre: 'Humanités et sociétés', texte: 'Lettres, philosophie et sciences sociales pour penser les enjeux contemporains.' },
    { titre: 'Design et innovation', texte: 'Concevoir des produits et des services utiles, accessibles et durables.' },
    { titre: 'Management et entrepreneuriat', texte: 'Piloter des projets, créer sa startup, accompagné par l\'incubateur du campus.' },
  ];
}
