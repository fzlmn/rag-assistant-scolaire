import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';

import { RagApiService } from '../../core/rag-api.service';
import { ReponseRecherche } from '../../core/models';

@Component({
  selector: 'app-recherche',
  imports: [CommonModule, FormsModule],
  templateUrl: './recherche.html',
  styleUrl: './recherche.css',
})
export class Recherche {
  private api = inject(RagApiService);

  question = '';
  topK = 5;
  type = '';

  loading = signal(false);                                   // → signals : Angular 21 (sans zone.js) met l'écran
  error = signal('');                                        //   à jour quand ils changent, même après une réponse HTTP
  response = signal<ReponseRecherche | null>(null);

  rechercher(): void {
    const question = this.question.trim();

    if (!question || this.loading()) {
      return;
    }

    this.loading.set(true);
    this.error.set('');
    this.response.set(null);

    this.api
      .rechercher(question, this.topK, this.type.trim() || null)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (resultat) => {
          this.response.set(resultat);
        },
        error: (e: Error) => {
          this.error.set(e.message);                         // → message clair préparé par l'intercepteur
        },
      });
  }

  reinitialiser(): void {
    this.question = '';
    this.type = '';
    this.topK = 5;
    this.response.set(null);
    this.error.set('');
  }
}
