// Render con time-warp: re-sincroniza el video original de 60 s al ritmo
// de la locucion grabada (71.4 s), mapeando anclas orig<-final.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
const fs = require('fs');

// [tiempo_original, tiempo_final]
const A = [
  [0.00, 0.00], [1.00, 1.60], [1.90, 4.60], [3.60, 8.90],
  [4.15, 9.60], [6.05, 12.30], [6.85, 13.40], [7.75, 14.40], [9.00, 16.20],
  [10.15, 16.90], [14.00, 19.40],
  [18.50, 23.30], [20.48, 25.10], [21.50, 26.20],
  [23.00, 27.70], [30.30, 34.60], [31.85, 35.70], [33.60, 37.30],
  [34.55, 37.90], [38.20, 40.20], [41.35, 41.60], [42.05, 42.30],
  [43.15, 43.40], [44.35, 44.60], [44.75, 44.90], [46.60, 46.30],
  [47.95, 47.65], [49.15, 48.85], [50.20, 49.90], [52.20, 54.20],
  [56.20, 60.90], [56.90, 62.00], [57.50, 64.50], [58.30, 67.60],
  [59.00, 69.00], [60.00, 71.40],
];
function warp(tf) {                       // final -> original
  if (tf <= A[0][1]) return A[0][0];
  for (let i = 1; i < A.length; i++) {
    if (tf <= A[i][1]) {
      const [o0, f0] = A[i - 1], [o1, f1] = A[i];
      return o0 + (o1 - o0) * (tf - f0) / (f1 - f0);
    }
  }
  return A[A.length - 1][0];
}

// subtitulos en tiempo FINAL, calzados con la locucion
const CAPS_VO = [
  [9.40, 15.70, 'Regístrate <em>gratis</em> en<br>talent.mashaincanada.com'],
  [16.70, 18.95, 'Creas tu perfil <em>una sola vez</em>…'],
  [19.05, 21.60, 'Tu experiencia, tus roles<br>objetivo y tu CV'],
  [22.80, 25.45, 'Entras a la sección <u>Jobs</u>…'],
  [25.55, 28.65, '…y ya tienes ofertas reales<br>en Canadá para <em>tu</em> perfil'],
  [29.10, 32.65, 'En inglés, con % de match,<br>salario y ubicación'],
  [34.35, 36.25, 'Abres la que te interesa…'],
  [36.45, 38.15, 'Ves la oferta completa…'],
  [38.25, 40.90, 'Y <em>aplicas ahí mismo</em>,<br>con tu perfil MIC'],
  [45.95, 53.70, 'Con el <u>Paquete de Optimización</u><br>desbloqueas todos los recursos'],
  [54.30, 60.70, 'Y muy pronto: ofertas de<br>empleadores <em>partner de MIC</em>'],
];

(async () => {
  const outDir = process.argv[2];
  const mode = process.argv[3] || 'full';
  const FPS = 30, DUR = 71.4;
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--force-device-scale-factor=1', '--hide-scrollbars',
           '--font-render-hinting=none', '--disable-lcd-text', '--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  await page.evaluate(() => window.__measure());
  // sobreescribe subtitulos con la version en tiempo final
  await page.evaluate((caps) => {
    window.__capsVO = caps;
    window.__capVO = (t) => {
      const lin = (x, a, b) => Math.min(1, Math.max(0, (x - a) / (b - a || 1e-6)));
      let op = 0, html = '';
      for (const [a, b, h] of window.__capsVO) {
        if (t >= a - 0.3 && t <= b + 0.3) {
          const o = lin(t, a, a + 0.28) * (1 - lin(t, b - 0.28, b));
          if (o > op) { op = o; html = h; }
        }
      }
      const c = document.querySelector('#cap'), ct = document.querySelector('#capT');
      c.style.opacity = op;
      if (html && ct.dataset.h !== html) { ct.innerHTML = html; ct.dataset.h = html; }
      ct.style.transform = `translateY(${9 - 9 * op}px)`;
    };
  }, CAPS_VO);

  const times = mode === 'preview'
    ? [1.0, 3.0, 7.5, 10.5, 13.5, 15.5, 18.0, 20.5, 24.3, 26.8, 30.5, 35.5, 38.5, 41.0,
       43.9, 45.5, 48.3, 52.0, 57.0, 62.5, 66.0, 70.5]
    : Array.from({ length: Math.round(DUR * FPS) }, (_, i) => i / FPS);

  let n = 0;
  for (const tf of times) {
    await page.evaluate(([to, t2]) => { window.__seek(to); window.__capVO(t2); }, [warp(tf), tf]);
    const name = mode === 'preview'
      ? `p_${String(tf.toFixed(1)).padStart(5, '0')}.png`
      : `f_${String(n).padStart(5, '0')}.jpg`;
    await page.screenshot({ path: path.join(outDir, name),
      type: mode === 'preview' ? 'png' : 'jpeg',
      quality: mode === 'preview' ? undefined : 92 });
    n++;
    if (mode === 'full' && n % 300 === 0) console.log('frame', n, '/', times.length);
  }
  await browser.close();
  console.log('done', n);
})();
