// frontend/src/app/components/logo/logo.ts — logo EIH (SVG) : carré violet, « E » blanc, point orange
import { Component, input } from '@angular/core';

@Component({
  selector: 'app-logo',
  template: `
    <svg [attr.width]="taille()" [attr.height]="taille()" viewBox="0 0 48 48" role="img" aria-label="Logo EIH">
      <rect width="48" height="48" rx="14" fill="#3d1e8f" />
      <rect x="13" y="12" width="22" height="4" rx="2" fill="#fff" />
      <rect x="13" y="22" width="13" height="4" rx="2" fill="#fff" />
      <rect x="13" y="32" width="22" height="4" rx="2" fill="#fff" />
      <circle cx="33" cy="24" r="3.6" fill="#ffa15c" />
    </svg>`,
  styles: ['svg { display: block; }'],
})
export class Logo {
  taille = input(36);                                       // → taille en pixels
}
