// frontend/src/app/app.routes.ts
// =============================================================================
// RÔLE : associer chaque adresse à un écran.
// SÉANCE 4 — Aya.
// =============================================================================

import { Routes } from '@angular/router';

import { Chat } from './pages/chat/chat';                    // → écran Conversation (Fatima Zahra)
import { Documents } from './pages/documents/documents';     // → écran Documents (Fatima Zahra)
import { Recherche } from './pages/recherche/recherche';     // → écran Recherche (Aya)

export const routes: Routes = [
  { path: '', component: Chat },                             // → page d'accueil : la conversation
  { path: 'documents', component: Documents },               // → /documents
  { path: 'recherche', component: Recherche },               // → /recherche (débogage)
  { path: '**', redirectTo: '' },                            // → toute autre adresse → accueil
];
