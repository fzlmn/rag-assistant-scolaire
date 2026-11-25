// frontend/src/app/pages/documents/documents.ts
// =============================================================================
// RÔLE : écran Documents : liste issue de GET /api/documents ; un clic sur un document ouvre
// l'aperçu du PDF (GET /api/documents/{fichier}/pdf), avec téléchargement et ouverture dans un onglet.
// SÉANCE 4 — Fatima Zahra. Exigence du sujet (6) : écran Documents.
// =============================================================================

import { DatePipe } from '@angular/common';                  // → date affichée au format JJ/MM/AAAA
import { Component, ElementRef, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';    // → autorise l'adresse du PDF dans l'<iframe>

import { DocumentInfo } from '../../core/models';            // → forme d'un document
import { RagApiService } from '../../core/rag-api.service';  // → appels à l'API

@Component({
  selector: 'app-documents',
  imports: [DatePipe],
  templateUrl: './documents.html',
  styleUrl: './documents.css',
})
export class Documents implements OnInit {
  private api = inject(RagApiService);
  private sanitizer = inject(DomSanitizer);

  documents = signal<DocumentInfo[]>([]);                    // → documents reçus
  enCours = signal(true);                                    // → chargement en cours
  erreur = signal<string | null>(null);                      // → message d'erreur éventuel
  ouvert = signal<DocumentInfo | null>(null);                // → document affiché dans l'aperçu (null = fermé)
  totalFragments = computed(() => this.documents().reduce((total, d) => total + d.nb_fragments, 0)); // → somme des fragments

  private fenetre = viewChild.required<ElementRef<HTMLDialogElement>>('fenetre'); // → la fenêtre <dialog> de l'aperçu

  apercu = computed(() => {
    // → Angular bloque par défaut une adresse calculée dans <iframe [src]> ; on l'autorise ici,
    //   car elle est construite par notre service à partir de environment.apiUrl
    const d = this.ouvert();
    return d ? this.sanitizer.bypassSecurityTrustResourceUrl(this.api.urlPdf(d.file)) : null;
  });

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

  lien(d: DocumentInfo, telecharger = false): string {
    return this.api.urlPdf(d.file, telecharger);             // → adresse du PDF (aperçu ou téléchargement)
  }

  ouvrir(d: DocumentInfo): void {
    this.ouvert.set(d);
    this.fenetre().nativeElement.showModal();                // → fenêtre au premier plan ; Échap la ferme
  }

  fermer(): void {
    this.fenetre().nativeElement.close();                    // → déclenche (close), qui vide « ouvert »
  }

  clicFenetre(e: MouseEvent): void {
    if (e.target === this.fenetre().nativeElement) this.fermer(); // → clic sur le fond grisé, hors du contenu
  }
}
