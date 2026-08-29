// Pruebas de las reglas de rotacion.
//
//   node --test reels/tools/
//
// Lo que se prueba no es que el codigo corra, sino que las reglas muerdan: que
// un tema repetido, un hook reciclado o una tercera promocion en la misma
// semana no puedan pasar.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { planFor, validateReel, loadConfig, toLedgerEntry, jaccard, normalizeKeywords } from './ledger.mjs';

const cfg = loadConfig();

const base = {
  id: 'RE-2026-09-10',
  date: '2026-09-10',
  category: 'entrevistas',
  template: 'T5-linea',
  hookFamily: 'contraste',
  accent: 'azul',
  evergreen: true,
  title: 'Prueba',
  hook: 'Un hook que no se ha usado nunca.',
  screens: [
    { kicker: 'Uno', text: 'Primer mensaje corto.' },
    { kicker: 'Dos', text: 'Segundo mensaje corto.' },
    { kicker: 'Tres', text: 'Tercer mensaje corto.' },
  ],
  cta: { id: 'guardar', text: 'Guardalo para tu busqueda de empleo.' },
  offer: null,
  keywords: ['entrevista', 'star', 'competencias'],
  caption: { firstLine: 'Una primera linea inedita.', body: 'Cuerpo.', hashtags: ['#a', '#b', '#c', '#d', '#e', '#f'] },
  durationSeconds: 22,
  sources: [],
};

const ledgerWith = (entries) => ({ version: 1, history: entries });
const entry = (over) => toLedgerEntry({ ...base, ...over });

test('un Reel bien formado pasa con historial vacio', () => {
  assert.deepEqual(validateReel(base, { ledger: ledgerWith([]), cfg }), []);
});

test('la categoria no puede repetirse dentro del enfriamiento', () => {
  const ledger = ledgerWith([entry({ id: 'RE-2026-09-07', date: '2026-09-07', hook: 'otro', caption: { ...base.caption, firstLine: 'otra' } })]);
  const problems = validateReel(base, { ledger, cfg });
  assert.ok(problems.some((p) => p.includes('la categoria "entrevistas"')), problems.join(' | '));
});

test('un hook ya publicado se rechaza aunque el tema sea distinto', () => {
  const ledger = ledgerWith([
    entry({ id: 'RE-2026-08-01', date: '2026-08-01', category: 'linkedin', keywords: ['linkedin'], caption: { ...base.caption, firstLine: 'distinta' } }),
  ]);
  const problems = validateReel(base, { ledger, cfg });
  assert.ok(problems.some((p) => p.includes('el hook ya se publico')), problems.join(' | '));
});

test('un tema que solapa demasiado con las ultimas 3 semanas se rechaza', () => {
  const ledger = ledgerWith([
    entry({
      id: 'RE-2026-09-02', date: '2026-09-02', category: 'linkedin', hook: 'otro hook',
      keywords: ['entrevista', 'star', 'competencias'],
      caption: { ...base.caption, firstLine: 'otra linea' },
    }),
  ]);
  const problems = validateReel(base, { ledger, cfg });
  assert.ok(problems.some((p) => p.includes('solapa')), problems.join(' | '));
});

test('el cupo promocional corta la tercera oferta de la semana', () => {
  const promo = (id, date, offer, category) => entry({
    id, date, offer, category, hook: `hook ${id}`, keywords: [category],
    caption: { ...base.caption, firstLine: `linea ${id}` },
  });
  const ledger = ledgerWith([
    promo('RE-2026-09-08', '2026-09-08', 'optimizacion', 'linkedin'),
    promo('RE-2026-09-09', '2026-09-09', 'talent-network', 'networking'),
  ]);
  const problems = validateReel({ ...base, offer: 'study-pathway' }, { ledger, cfg });
  assert.ok(problems.some((p) => p.includes('cupo promocional')), problems.join(' | '));
  assert.equal(planFor('2026-09-10', ledger, cfg).promoSlotsLeft, 0);
});

test('un Reel noticioso exige fuente con enlace', () => {
  const problems = validateReel({ ...base, evergreen: false }, { ledger: ledgerWith([]), cfg });
  assert.ok(problems.some((p) => p.includes('fuente')), problems.join(' | '));
  assert.deepEqual(
    validateReel({ ...base, evergreen: false, sources: [{ title: 'LFS', url: 'https://www150.statcan.gc.ca/' }] }, { ledger: ledgerWith([]), cfg }),
    []
  );
});

test('los limites de texto del brandkit se aplican', () => {
  const problems = validateReel(
    { ...base, hook: 'x'.repeat(80), screens: [...base.screens, { text: 'y'.repeat(200) }] },
    { ledger: ledgerWith([]), cfg }
  );
  assert.ok(problems.some((p) => p.includes('hook de 80 caracteres')), problems.join(' | '));
  assert.ok(problems.some((p) => p.includes('pantalla 4')), problems.join(' | '));
});

test('el plan no ofrece nada que este en enfriamiento', () => {
  const ledger = ledgerWith([
    entry({ id: 'RE-2026-09-09', date: '2026-09-09', category: 'linkedin', template: 'T3-tarjetas', hookFamily: 'error-comun', hook: 'h1', caption: { ...base.caption, firstLine: 'l1' } }),
  ]);
  const plan = planFor('2026-09-10', ledger, cfg);
  const offered = [plan.category, ...plan.categoryAlternatives].map((c) => c.id);
  assert.ok(!offered.includes('linkedin'));
  assert.notEqual(plan.template.id, 'T3-tarjetas');
  assert.notEqual(plan.hookFamily.id, 'error-comun');
});

test('las palabras vacias no inflan el parecido entre temas', () => {
  const a = normalizeKeywords(['el mercado laboral en Canada']);
  const b = normalizeKeywords(['la entrevista de trabajo en Canada']);
  assert.ok(jaccard(a, b) < 0.4, `solape inesperado: ${jaccard(a, b)}`);
});

test('validar un Reel ya registrado no lo acusa de repetirse a si mismo', () => {
  const ledger = ledgerWith([entry({})]);
  assert.deepEqual(validateReel(base, { ledger, cfg }), []);
});

test('otro Reel distinto en la misma fecha si se rechaza', () => {
  const ledger = ledgerWith([entry({})]);
  const otro = { ...base, id: 'RE-2026-09-10-b', hook: 'hook nuevo', keywords: ['networking'], category: 'networking', caption: { ...base.caption, firstLine: 'otra linea' } };
  const problems = validateReel(otro, { ledger, cfg });
  assert.ok(problems.some((p) => p.includes('ya hay otro Reel registrado para 2026-09-10')), problems.join(' | '));
});
