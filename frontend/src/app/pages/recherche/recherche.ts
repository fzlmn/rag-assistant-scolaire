
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
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

  loading = false;
  error = '';
  response: ReponseRecherche | null = null;

  rechercher(): void {
    const question = this.question.trim();

    if (!question || this.loading) {
      return;
    }

    this.loading = true;
    this.error = '';
    this.response = null;

    this.api
      .rechercher(question, this.topK, this.type.trim() || null)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (resultat) => {
          this.response = resultat;
        },
        error: (err: HttpErrorResponse) => {
          const detail = err.error?.detail;

          this.error =
            typeof detail === 'string'
              ? detail
              : 'Impossible de contacter le serveur. Vérifiez que le backend est démarré.';
        },
      });
  }

  reinitialiser(): void {
    this.question = '';
    this.type = '';
    this.topK = 5;
    this.response = null;
    this.error = '';
  }
}
