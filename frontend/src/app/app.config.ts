// frontend/src/app/app.config.ts
// =============================================================================
// RÔLE : configuration de l'application (routes, client HTTP, intercepteur d'erreurs).
// SÉANCE 4 — Aya.
// =============================================================================

import { provideHttpClient, withInterceptors } from '@angular/common/http'; // → active HttpClient
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';             // → active la navigation entre les écrans

import { routes } from './app.routes';                       // → liste des écrans
import { erreurInterceptor } from './core/erreur.interceptor'; // → messages d'erreur clairs

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),                    // → (généré par Angular) remonte les erreurs non gérées
    provideRouter(routes),                                   // → routes de l'application
    provideHttpClient(withInterceptors([erreurInterceptor])), // → HttpClient + notre intercepteur
  ],
};
