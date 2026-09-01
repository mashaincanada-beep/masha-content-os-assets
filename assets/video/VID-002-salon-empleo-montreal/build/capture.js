// Usage: node capture.js <html> <outdir> [--times 1.2,3.4,...] [--range start end] [--fps 30]
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const args = process.argv.slice(2);
const html = path.resolve(args[0]); const outdir = path.resolve(args[1]);
let times = null, range = null, fps = 30, names = null;
for (let i = 2; i < args.length; i++) {
  if (args[i] === '--times') { times = args[++i].split(',').map(Number); }
  if (args[i] === '--range') { range = [Number(args[++i]), Number(args[++i])]; }
  if (args[i] === '--fps') { fps = Number(args[++i]); }
}
fs.mkdirSync(outdir, { recursive: true });
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await p.goto('file://' + html);
  await p.evaluate(() => document.fonts.ready);
  // preload all cutaway images so screenshots never catch a half-loaded img
  await p.evaluate(async () => {
    const srcs = (window.CUTS || []).map(c => c[2]);
    await Promise.all(srcs.map(s => new Promise(res => { const im = new Image(); im.onload = res; im.onerror = res; im.src = s; })));
  });
  const total = await p.evaluate(() => window.TOTAL);
  let list;
  if (times) list = times.map(t => ({ t, name: `qa_${t.toFixed(2).replace('.', '_')}.png` }));
  else {
    const f0 = range ? Math.round(range[0] * fps) : 0; const f1 = range ? Math.round(range[1] * fps) : Math.round(total * fps);
    list = []; for (let f = f0; f < f1; f++) list.push({ t: f / fps, name: `o_${String(f).padStart(5, '0')}.png` });
  }
  const t0 = Date.now();
  for (let i = 0; i < list.length; i++) {
    const { t, name } = list[i];
    await p.evaluate(tt => { window.render(tt); }, t);
    // make sure a just-swapped img is decoded
    await p.evaluate(() => { const im = document.getElementById('shot'); return im && im.src && !im.complete ? im.decode().catch(() => {}) : null; });
    await p.screenshot({ path: path.join(outdir, name), type: 'png', omitBackground: true });
    if (i % 200 === 0) console.log(`frame ${i}/${list.length} t=${t.toFixed(2)} elapsed ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  console.log(`done ${list.length} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
