// frontend/src/app/app.routes.ts
// =============================================================================
// RÔLE : associer chaque adresse à un écran.
// SÉANCE 4 — Aya.
// =============================================================================

import { Routes } from '@angular/router';

import { Accueil } from './pages/accueil/accueil';           // → page d'accueil de l'université
import { Chat } from './pages/chat/chat';                    // → écran Conversation (Fatima Zahra)
import { Documents } from './pages/documents/documents';     // → écran Documents (Fatima Zahra)
import { Recherche } from './pages/recherche/recherche';     // → écran Recherche (Aya)

export const routes: Routes = [
  { path: '', component: Accueil },                          // → page d'accueil
  { path: 'conversation', component: Chat },                 // → /conversation : l'assistant
  { path: 'documents', component: Documents },               // → /documents
  { path: 'recherche', component: Recherche },               // → /recherche (débogage)
  { path: '**', redirectTo: '' },                            // → toute autre adresse → accueil
];
