// frontend/src/app/core/rag-api.service.ts
// =============================================================================
// RÔLE : seul endroit qui appelle l'API. Les écrans utilisent ce service, jamais HttpClient directement.
// SÉANCE 4 — Aya. Exigences du sujet : service RagApiService avec HttpClient ;
// URL de l'API fournie par une variable d'environnement ; aucune clé de LLM côté navigateur.
// =============================================================================

import { HttpClient } from '@angular/common/http';           // → client HTTP d'Angular
import { Injectable, inject } from '@angular/core';          // → déclaration du service et injection
import { Observable } from 'rxjs';                           // → type des réponses asynchrones

import { environment } from '../../environments/environment'; // → contient apiUrl
import { DocumentInfo, EchangePrecedent, ReponseQuestion, ReponseRecherche } from './models'; // → formes des données

@Injectable({ providedIn: 'root' })                          // → un seul service pour toute l'application
export class RagApiService {
  private http = inject(HttpClient);                         // → récupère le client HTTP
  private url = environment.apiUrl;                          // → ex. http://localhost:8000/api

  poser(question: string, topK: number, type: string | null,
        historique: EchangePrecedent[] = []): Observable<ReponseQuestion> {
    return this.http.post<ReponseQuestion>(`${this.url}/ask`, {
      question, top_k: topK, filters: { type },              // → même corps que celui attendu par FastAPI
      history: historique,                                   // → derniers échanges, pour les questions de suivi
    });
  }

  rechercher(question: string, topK: number, type: string | null): Observable<ReponseRecherche> {
    return this.http.post<ReponseRecherche>(`${this.url}/search`, {
      question, top_k: topK, filters: { type },
    });
  }

  documents(): Observable<DocumentInfo[]> {
    return this.http.get<DocumentInfo[]>(`${this.url}/documents`); // → liste des documents indexés
  }

  urlPdf(fichier: string, telecharger = false): string {
    // → adresse du PDF (GET /api/documents/{fichier}/pdf) : affiché par le navigateur, ou téléchargé
    return `${this.url}/documents/${encodeURIComponent(fichier)}/pdf${telecharger ? '?download=true' : ''}`;
  }
}
