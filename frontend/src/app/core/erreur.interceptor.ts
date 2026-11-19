// frontend/src/app/core/erreur.interceptor.ts
// =============================================================================
// RÔLE : transformer chaque erreur HTTP en message clair, au même endroit pour toute l'application.
// SÉANCE 4 — Aya. Exigence du sujet : erreurs 422, 502 et 503 avec un message clair.
// =============================================================================

import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http'; // → types des intercepteurs
import { catchError, throwError } from 'rxjs';                              // → intercepter puis relancer l'erreur

export function messageErreur(statut: number): string {
  switch (statut) {                                          // → choisit le message selon le code HTTP
    case 0:
      return "Impossible de joindre l'API. Vérifiez que le backend est lancé (uvicorn).";
    case 422:
      return 'Requête invalide : la question est vide ou un paramètre est incorrect.';
    case 502:
      return 'Le modèle de langage ne répond pas pour le moment. Réessayez dans quelques instants.';
    case 503:
      return "La base de documents n'est pas prête : lancez d'abord l'ingestion (POST /api/ingest).";
    default:
      return `Erreur inattendue (code ${statut}).`;
  }
}

export const erreurInterceptor: HttpInterceptorFn = (requete, suivant) =>
  suivant(requete).pipe(                                     // → laisse passer la requête…
    catchError((erreur: HttpErrorResponse) =>                // → …et si elle échoue :
      throwError(() => new Error(messageErreur(erreur.status))), // → relance une erreur avec un message clair
    ),
  );
