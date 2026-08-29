// Estado y reglas de rotacion del Reel diario.
//
// Todo lo que impide que el sistema se repita vive aqui, y es deterministico a
// proposito: la variedad no se deja al criterio del modelo que escribe el Reel
// ese dia, porque un modelo sin memoria no sabe que publico hace cuatro dias.
// El ledger si lo sabe, y las funciones de este archivo son las unicas que
// deciden que categoria, plantilla, familia de hook, CTA y oferta estan
// permitidas hoy.

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
export const ROOT = join(HERE, '..');
const LEDGER_PATH = join(ROOT, 'state', 'ledger.json');

const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));

export function loadConfig() {
  return {
    brand: readJson(join(ROOT, 'brandkit.json')),
    topics: readJson(join(ROOT, 'playbook', 'topics.json')),
    hooks: readJson(join(ROOT, 'playbook', 'hooks.json')),
    templates: readJson(join(ROOT, 'playbook', 'templates.json')),
    ctas: readJson(join(ROOT, 'playbook', 'ctas.json')),
    offers: readJson(join(ROOT, 'playbook', 'offers.json')),
  };
}

export function loadLedger() {
  if (!existsSync(LEDGER_PATH)) return { version: 1, history: [] };
  return readJson(LEDGER_PATH);
}

export function saveLedger(ledger) {
  writeFileSync(LEDGER_PATH, JSON.stringify(ledger, null, 2) + '\n');
}

export const today = () => new Date().toISOString().slice(0, 10);

/** Dias enteros entre dos fechas YYYY-MM-DD. */
export function daysBetween(from, to) {
  return Math.round((Date.parse(to) - Date.parse(from)) / 86400000);
}

/** Entradas de los ultimos `days` dias, de la mas reciente a la mas antigua. */
export function recent(ledger, refDate, days) {
  return ledger.history
    .filter((e) => daysBetween(e.date, refDate) < days && daysBetween(e.date, refDate) >= 0)
    .sort((a, b) => b.date.localeCompare(a.date));
}

/** Dias transcurridos desde el ultimo uso de un valor, o null si nunca se uso. */
function daysSinceUse(ledger, refDate, field, value) {
  const hits = ledger.history
    .filter((e) => e[field] === value)
    .map((e) => daysBetween(e.date, refDate))
    .filter((d) => d >= 0);
  return hits.length ? Math.min(...hits) : null;
}

// --- Palabras clave -------------------------------------------------------

const STOP = new Set(
  ('de la el en y a los las un una para con por que se del al es su lo como mas o si ya no te tu ' +
   'canada canadiense canadienses trabajo empleo').split(' ')
);

/** Normaliza a minusculas sin acentos y descarta vacio semantico. */
export function normalizeKeywords(list) {
  return [...new Set(
    list
      .flatMap((k) => String(k).toLowerCase().split(/[^a-z0-9à-ÿ]+/i))
      .map((w) => w.normalize('NFD').replace(/[̀-ͯ]/g, ''))
      .filter((w) => w.length > 2 && !STOP.has(w))
  )];
}

export function jaccard(a, b) {
  const A = new Set(a);
  const B = new Set(b);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const x of A) if (B.has(x)) inter++;
  return inter / (A.size + B.size - inter);
}

/**
 * Solape maximo del tema propuesto contra los Reels recientes.
 * Devuelve `{ score, against }` con el peor caso encontrado.
 */
export function overlapAgainstRecent(ledger, refDate, keywords, cfg) {
  const { lookbackDays } = cfg.topics.keywordOverlap;
  const kw = normalizeKeywords(keywords);
  let worst = { score: 0, against: null };
  for (const e of recent(ledger, refDate, lookbackDays)) {
    const score = jaccard(kw, normalizeKeywords(e.keywords || []));
    if (score > worst.score) worst = { score, against: e.id };
  }
  return worst;
}

// --- Desempate estable ----------------------------------------------------

/**
 * Ruido deterministico por (fecha, valor). Rompe empates sin volver el orden
 * alfabetico: dos categorias con la misma antiguedad no ganan siempre la
 * misma.
 */
function tiebreak(date, value) {
  let h = 2166136261;
  for (const ch of `${date}:${value}`) {
    h ^= ch.charCodeAt(0);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}

/**
 * Ordena candidatos por "hace mas tiempo que no se usa" y filtra los que
 * siguen en enfriamiento. Nunca usado gana a cualquier usado.
 */
function rank(ledger, date, field, items, cooldown) {
  return items
    .map((item) => {
      const since = daysSinceUse(ledger, date, field, item.id);
      return { ...item, daysSinceUse: since, eligible: since === null || since >= cooldown };
    })
    .sort((a, b) => {
      const A = a.daysSinceUse === null ? Infinity : a.daysSinceUse;
      const B = b.daysSinceUse === null ? Infinity : b.daysSinceUse;
      if (A !== B) return B - A;
      return tiebreak(date, a.id) - tiebreak(date, b.id);
    });
}

// --- El plan del dia ------------------------------------------------------

/**
 * Calcula que puede publicarse hoy. No escribe el Reel: acota el espacio en el
 * que el Reel puede escribirse, que es justo lo que un modelo sin memoria no
 * puede acotar solo.
 */
export function planFor(date, ledger = loadLedger(), cfg = loadConfig()) {
  const cd = cfg.topics.cooldownDays;

  const categories = rank(ledger, date, 'category', cfg.topics.categories, cd.category);
  const templates = rank(ledger, date, 'template', cfg.templates.templates, cd.template);
  const hookFamilies = rank(ledger, date, 'hookFamily', cfg.hooks.families, cd.hookFamily);

  const ctas = cfg.ctas.options
    .map((c) => {
      const since = daysSinceUse(ledger, date, 'cta', c.id);
      return { ...c, daysSinceUse: since, eligible: since === null || since >= c.cooldownDays };
    })
    .sort((a, b) => a.priority - b.priority);

  // Cupo promocional: cuantos Reels con oferta caben todavia en la ventana.
  const { windowDays, maxPromoReels } = cfg.topics.promoQuota;
  const promoUsed = recent(ledger, date, windowDays).filter((e) => e.offer).length;
  const promoSlotsLeft = Math.max(0, maxPromoReels - promoUsed);

  const offers = cfg.offers.offers.map((o) => {
    const since = daysSinceUse(ledger, date, 'offer', o.id);
    return {
      ...o,
      daysSinceUse: since,
      eligible: promoSlotsLeft > 0 && (since === null || since >= cd.offer),
    };
  });

  const eligibleCats = categories.filter((c) => c.eligible);
  const chosenCategory = eligibleCats[0] ?? categories[0];

  // Una plantilla que la categoria recomienda vale mas que la simple antiguedad.
  const eligibleTpl = templates.filter((t) => t.eligible);
  const preferred = eligibleTpl.filter((t) => (t.bestFor || []).includes(chosenCategory.id));
  const chosenTemplate = preferred[0] ?? eligibleTpl[0] ?? templates[0];

  const last60 = recent(ledger, date, 60);

  return {
    date,
    category: chosenCategory,
    categoryAlternatives: eligibleCats.slice(1, 4),
    template: chosenTemplate,
    templateAlternatives: eligibleTpl.filter((t) => t.id !== chosenTemplate.id).slice(0, 2),
    hookFamily: hookFamilies.find((f) => f.eligible) ?? hookFamilies[0],
    hookFamilyAlternatives: hookFamilies.filter((f) => f.eligible).slice(1, 3),
    ctas: ctas.filter((c) => c.eligible),
    accent: chosenCategory.defaultAccent,
    promoSlotsLeft,
    offers: offers.filter((o) => o.eligible),
    bannedHooks: last60.map((e) => e.hook).filter(Boolean),
    bannedCaptionOpeners: recent(ledger, date, 30).map((e) => e.captionFirstLine).filter(Boolean),
    recentTopics: recent(ledger, date, cfg.topics.keywordOverlap.lookbackDays)
      .map((e) => ({ id: e.id, date: e.date, category: e.category, title: e.title })),
  };
}

// --- Validacion -----------------------------------------------------------

/**
 * Comprueba un Reel contra el brandkit y contra el historial. Devuelve la lista
 * de problemas; vacia significa publicable.
 */
export function validateReel(reel, { date = reel.date, ledger = loadLedger(), cfg = loadConfig() } = {}) {
  // El propio Reel no cuenta como antecedente de si mismo. Sin esto, validar un
  // Reel ya registrado lo acusaria de repetir su propio hook, su propio tema y
  // su propia categoria, y volver a pasar la puerta despues de registrarlo
  // seria imposible.
  const others = { ...ledger, history: ledger.history.filter((e) => e.id !== reel.id) };
  const L = cfg.brand.limits;
  const problems = [];
  const fail = (m) => problems.push(m);

  for (const f of ['id', 'date', 'category', 'template', 'hookFamily', 'accent', 'hook', 'screens', 'cta', 'keywords', 'caption']) {
    if (reel[f] === undefined || reel[f] === null) fail(`falta el campo obligatorio "${f}"`);
  }
  if (problems.length) return problems;

  if (!cfg.topics.categories.some((c) => c.id === reel.category)) fail(`categoria desconocida: ${reel.category}`);
  if (!cfg.templates.templates.some((t) => t.id === reel.template)) fail(`plantilla desconocida: ${reel.template}`);
  if (!cfg.hooks.families.some((f) => f.id === reel.hookFamily)) fail(`familia de hook desconocida: ${reel.hookFamily}`);
  if (!cfg.brand.colors[reel.accent]) fail(`color de acento desconocido: ${reel.accent}`);

  if (reel.hook.length > L.hookMaxChars) fail(`hook de ${reel.hook.length} caracteres (maximo ${L.hookMaxChars})`);
  if (reel.screens.length < L.bodyScreensMin || reel.screens.length > L.bodyScreensMax) {
    fail(`${reel.screens.length} pantallas de cuerpo (se permiten ${L.bodyScreensMin}-${L.bodyScreensMax})`);
  }
  reel.screens.forEach((s, i) => {
    if (!s.text) fail(`pantalla ${i + 1} sin texto`);
    else if (s.text.length > L.bodyMaxChars) fail(`pantalla ${i + 1}: ${s.text.length} caracteres (maximo ${L.bodyMaxChars})`);
    if (s.kicker && s.kicker.length > L.kickerMaxChars) fail(`pantalla ${i + 1}: kicker de ${s.kicker.length} caracteres (maximo ${L.kickerMaxChars})`);
  });

  if (!reel.cta?.id || !reel.cta?.text) fail('el CTA necesita id y texto');
  else {
    if (!cfg.ctas.options.some((c) => c.id === reel.cta.id)) fail(`CTA desconocido: ${reel.cta.id}`);
    if (reel.cta.text.length > L.ctaMaxChars) fail(`CTA de ${reel.cta.text.length} caracteres (maximo ${L.ctaMaxChars})`);
  }

  if (reel.offer && !cfg.offers.offers.some((o) => o.id === reel.offer)) fail(`oferta desconocida: ${reel.offer}`);

  const tags = reel.caption?.hashtags ?? [];
  if (!reel.caption?.firstLine) fail('el caption necesita una primera linea');
  if (!reel.caption?.body) fail('el caption necesita cuerpo');
  if (tags.length < L.hashtagsMin || tags.length > L.hashtagsMax) {
    fail(`${tags.length} hashtags (se permiten ${L.hashtagsMin}-${L.hashtagsMax})`);
  }
  if (tags.some((t) => !t.startsWith('#'))) fail('todos los hashtags empiezan por #');

  const dur = reel.durationSeconds;
  if (typeof dur !== 'number' || dur < cfg.brand.timing.targetSecondsMin || dur > cfg.brand.timing.targetSecondsMax) {
    fail(`duracion ${dur}s fuera del rango ${cfg.brand.timing.targetSecondsMin}-${cfg.brand.timing.targetSecondsMax}s`);
  }

  if (!reel.evergreen && !(reel.sources?.length)) {
    fail('un Reel noticioso necesita al menos una fuente con enlace');
  }
  for (const s of reel.sources ?? []) {
    if (!s.url || !/^https?:\/\//.test(s.url)) fail(`fuente sin URL valida: ${s.title ?? '(sin titulo)'}`);
  }

  // Contra el historial, excluyendo al propio Reel.
  const plan = planFor(date, others, cfg);
  if (plan.bannedHooks.includes(reel.hook)) fail(`el hook ya se publico en los ultimos 60 dias: "${reel.hook}"`);
  if (plan.bannedCaptionOpeners.includes(reel.caption.firstLine)) fail('la primera linea del caption ya se uso en los ultimos 30 dias');
  if (others.history.some((e) => e.date === reel.date)) fail(`ya hay otro Reel registrado para ${reel.date}`);

  const cd = cfg.topics.cooldownDays;
  const check = (field, value, days, label) => {
    const since = daysSinceUse(others, date, field, value);
    if (since !== null && since < days) fail(`${label} "${value}" se uso hace ${since} dia(s); el enfriamiento es de ${days}`);
  };
  check('category', reel.category, cd.category, 'la categoria');
  check('template', reel.template, cd.template, 'la plantilla');
  check('hookFamily', reel.hookFamily, cd.hookFamily, 'la familia de hook');
  const ctaDef = cfg.ctas.options.find((c) => c.id === reel.cta.id);
  if (ctaDef) check('cta', reel.cta.id, ctaDef.cooldownDays, 'el CTA');
  if (reel.offer) {
    check('offer', reel.offer, cd.offer, 'la oferta');
    if (plan.promoSlotsLeft <= 0) {
      fail(`se agoto el cupo promocional (${cfg.topics.promoQuota.maxPromoReels} cada ${cfg.topics.promoQuota.windowDays} dias)`);
    }
  }

  const overlap = overlapAgainstRecent(others, date, reel.keywords, cfg);
  if (overlap.score > cfg.topics.keywordOverlap.maxJaccard) {
    fail(`el tema solapa ${(overlap.score * 100).toFixed(0)}% con ${overlap.against}; el maximo es ${cfg.topics.keywordOverlap.maxJaccard * 100}%`);
  }

  return problems;
}

/** Reduce un Reel a lo que el historial necesita recordar. */
export function toLedgerEntry(reel) {
  return {
    id: reel.id,
    date: reel.date,
    category: reel.category,
    template: reel.template,
    hookFamily: reel.hookFamily,
    accent: reel.accent,
    cta: reel.cta.id,
    offer: reel.offer ?? null,
    evergreen: Boolean(reel.evergreen),
    title: reel.title ?? null,
    hook: reel.hook,
    captionFirstLine: reel.caption.firstLine,
    keywords: reel.keywords,
    canvaDesignId: reel.canva?.designId ?? null,
    published: reel.published ?? false,
  };
}
