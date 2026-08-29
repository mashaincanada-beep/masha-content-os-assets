#!/usr/bin/env node
// Valida un reel.json contra el brandkit y el historial, sin escribir nada.
//
//   node reels/tools/verify-reel.mjs reels/RE-2026-08-29/reel.json
//
// Sale con 0 si el Reel es publicable y con 1 listando cada problema. Esta es
// la puerta que impide publicar un Reel que repite tema, se pasa de texto o
// afirma una cifra sin fuente.

import { readFileSync } from 'node:fs';
import { validateReel } from './ledger.mjs';

const path = process.argv[2];
if (!path) {
  console.error('Uso: node reels/tools/verify-reel.mjs <ruta/al/reel.json>');
  process.exit(2);
}

const reel = JSON.parse(readFileSync(path, 'utf8'));
const problems = validateReel(reel);

if (!problems.length) {
  console.log(`OK  ${reel.id} — ${reel.screens.length} pantallas, ${reel.durationSeconds}s, acento ${reel.accent}, CTA ${reel.cta.id}${reel.offer ? `, oferta ${reel.offer}` : ''}`);
  process.exit(0);
}

console.error(`${problems.length} problema(s) en ${path}:`);
for (const p of problems) console.error(`  - ${p}`);
process.exit(1);
