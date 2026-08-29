#!/usr/bin/env node
// Registra un Reel ya producido en el historial.
//
//   node reels/tools/record-reel.mjs reels/RE-2026-08-29/reel.json
//   node reels/tools/record-reel.mjs reels/RE-2026-08-29/reel.json --force
//
// Valida antes de escribir: un Reel que no pasa verify-reel.mjs no entra al
// historial, porque el historial es lo que protege a los Reels siguientes de
// repetirse. --force existe solo para reparar el historial a mano cuando algo
// se publico fuera del flujo.

import { readFileSync } from 'node:fs';
import { validateReel, loadLedger, saveLedger, toLedgerEntry } from './ledger.mjs';

const args = process.argv.slice(2);
const path = args.find((a) => !a.startsWith('--'));
const force = args.includes('--force');

if (!path) {
  console.error('Uso: node reels/tools/record-reel.mjs <ruta/al/reel.json> [--force]');
  process.exit(2);
}

const reel = JSON.parse(readFileSync(path, 'utf8'));
const problems = validateReel(reel);

if (problems.length && !force) {
  console.error(`No se registra: ${problems.length} problema(s).`);
  for (const p of problems) console.error(`  - ${p}`);
  console.error('Corrige el Reel, o usa --force si sabes exactamente por que lo saltas.');
  process.exit(1);
}
if (problems.length) {
  console.error(`AVISO: se registra con --force pese a ${problems.length} problema(s):`);
  for (const p of problems) console.error(`  - ${p}`);
}

const ledger = loadLedger();
ledger.history = ledger.history.filter((e) => e.id !== reel.id);
ledger.history.push(toLedgerEntry(reel));
ledger.history.sort((a, b) => a.date.localeCompare(b.date));
saveLedger(ledger);

console.log(`Registrado ${reel.id} (${reel.date}). El historial tiene ${ledger.history.length} Reel(s).`);
