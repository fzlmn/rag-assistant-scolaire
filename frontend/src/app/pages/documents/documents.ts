// frontend/src/app/pages/documents/documents.ts
// =============================================================================
// RÔLE : écran Documents : liste issue de GET /api/documents.
// SÉANCE 4 — Fatima Zahra. Exigence du sujet (6) : écran Documents.
// =============================================================================

import { Component, OnInit, inject, signal } from '@angular/core';

import { DocumentInfo } from '../../core/models';            // → forme d'un document
import { RagApiService } from '../../core/rag-api.service';  // → appels à l'API

@Component({
  selector: 'app-documents',
  templateUrl: './documents.html',
  styleUrl: './documents.css',
})
export class Documents implements OnInit {
  private api = inject(RagApiService);

  documents = signal<DocumentInfo[]>([]);                    // → documents reçus
  enCours = signal(true);                                    // → chargement en cours
  erreur = signal<string | null>(null);                      // → message d'erreur éventuel

  ngOnInit(): void {
    this.api.documents().subscribe({                         // → appel de GET /api/documents
      next: (docs) => {
        this.documents.set(docs);
        this.enCours.set(false);
      },
      error: (e: Error) => {                                 // → ex. 503 si l'ingestion n'a pas été faite
        this.erreur.set(e.message);
        this.enCours.set(false);
      },
    });
  }
}
