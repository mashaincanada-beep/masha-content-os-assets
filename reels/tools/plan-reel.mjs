#!/usr/bin/env node
// Imprime el espacio permitido para el Reel de hoy.
//
//   node reels/tools/plan-reel.mjs                      # plan del dia
//   node reels/tools/plan-reel.mjs --date=2026-09-01    # plan de otra fecha
//   node reels/tools/plan-reel.mjs --category=salarios  # forzar categoria
//   node reels/tools/plan-reel.mjs --json               # solo JSON
//
// Forzar una categoria es legitimo cuando la noticia del dia manda, pero si esa
// categoria sigue en enfriamiento el comando lo dice en voz alta y sale con
// codigo 1: la decision se toma a sabiendas, no por descuido.

import { planFor, loadConfig, loadLedger, today } from './ledger.mjs';

const args = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const [k, v] = a.replace(/^--/, '').split('=');
    return [k, v ?? true];
  })
);

const date = args.date === true || !args.date ? today() : args.date;
const cfg = loadConfig();
const ledger = loadLedger();
const plan = planFor(date, ledger, cfg);

let forcedWarning = null;
if (args.category && args.category !== true) {
  const all = cfg.topics.categories.map((c) => {
    const ranked = [plan.category, ...plan.categoryAlternatives].find((x) => x.id === c.id);
    return ranked ?? c;
  });
  const wanted = all.find((c) => c.id === args.category);
  if (!wanted) {
    console.error(`Categoria desconocida: ${args.category}`);
    console.error(`Validas: ${cfg.topics.categories.map((c) => c.id).join(', ')}`);
    process.exit(2);
  }
  const eligible = [plan.category, ...plan.categoryAlternatives].some((c) => c.id === wanted.id);
  plan.category = { ...wanted, forced: true };
  plan.accent = wanted.defaultAccent;
  const pool = [plan.template, ...plan.templateAlternatives];
  plan.template = pool.find((t) => (t.bestFor || []).includes(wanted.id)) ?? plan.template;
  plan.templateAlternatives = pool.filter((t) => t.id !== plan.template.id);
  if (!eligible) forcedWarning = `La categoria "${wanted.id}" sigue en enfriamiento (${cfg.topics.cooldownDays.category} dias).`;
}

if (args.json) {
  console.log(JSON.stringify(plan, null, 2));
  process.exit(forcedWarning ? 1 : 0);
}

const L = cfg.brand.limits;
const list = (xs) => (xs.length ? xs.join(', ') : '(ninguno)');

console.log(`
PLAN DEL REEL — ${plan.date}
${'='.repeat(56)}

CATEGORIA   ${plan.category.name}  [${plan.category.id}]${plan.category.forced ? '  (forzada)' : ''}
            ${plan.category.brief}
            Alternativas: ${list(plan.categoryAlternatives.map((c) => c.id))}

PLANTILLA   ${plan.template.name}  [${plan.template.id}]
            ${plan.template.layout}
            Direccion para Canva: ${plan.template.canvaDirective}
            Alternativas: ${list(plan.templateAlternatives.map((t) => t.id))}

HOOK        Familia: ${plan.hookFamily.name}  [${plan.hookFamily.id}]
            Cuando: ${plan.hookFamily.when}
            Patrones:
${plan.hookFamily.patterns.map((p) => `              - ${p}`).join('\n')}
            Alternativas: ${list(plan.hookFamilyAlternatives.map((f) => f.id))}

ACENTO      ${plan.accent}  ${cfg.brand.colors[plan.accent]}

CTA         Permitidos hoy (en orden de prioridad):
${plan.ctas.map((c) => `              [${c.id}] ${c.text}\n                  usar cuando: ${c.useWhen}`).join('\n')}

PROMOCION   Cupo restante: ${plan.promoSlotsLeft} de ${cfg.topics.promoQuota.maxPromoReels} cada ${cfg.topics.promoQuota.windowDays} dias
${plan.offers.length
  ? plan.offers.map((o) => `              [${o.id}] ${o.name}\n                  encaja con: ${o.attachTo.join(', ')}`).join('\n')
  : '              Sin ofertas disponibles hoy: el Reel va sin promocion.'}

LIMITES     hook <= ${L.hookMaxChars} car. | pantalla <= ${L.bodyMaxChars} car. | ${L.bodyScreensMin}-${L.bodyScreensMax} pantallas
            CTA <= ${L.ctaMaxChars} car. | ${L.hashtagsMin}-${L.hashtagsMax} hashtags
            duracion ${cfg.brand.timing.targetSecondsMin}-${cfg.brand.timing.targetSecondsMax}s | lienzo ${cfg.brand.canvas.width}x${cfg.brand.canvas.height}

PROHIBIDO REPETIR
            Hooks de los ultimos 60 dias: ${plan.bannedHooks.length}
${plan.bannedHooks.slice(0, 10).map((h) => `              - "${h}"`).join('\n') || '              (ninguno todavia)'}
            Temas de los ultimos ${cfg.topics.keywordOverlap.lookbackDays} dias:
${plan.recentTopics.map((t) => `              - ${t.date} [${t.category}] ${t.title ?? ''}`).join('\n') || '              (ninguno todavia)'}
`);

if (forcedWarning) {
  console.error(`AVISO: ${forcedWarning}`);
  process.exit(1);
}
