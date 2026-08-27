// Deterministic frame renderer: seeks the timeline and screenshots each frame.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const args = process.argv.slice(2);
  const outDir = args[0];
  const mode   = args[1] || 'full';           // 'full' | 'preview'
  const FPS = 30, DUR = 60.0;
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--force-device-scale-factor=1', '--hide-scrollbars', '--font-render-hinting=none',
           '--disable-lcd-text', '--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'scene.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
  await page.evaluate(() => window.__measure());

  const times = mode === 'preview'
    ? [0.9, 2.2, 5.0, 7.6, 8.6, 10.5, 13.0, 15.2, 17.5, 19.6, 21.0, 22.4, 25.0, 29.5, 32.0,
       34.5, 37.5, 41.0, 42.5, 45.5, 48.5, 51.0, 53.5, 57.5, 59.4]
    : Array.from({ length: Math.round(DUR * FPS) }, (_, i) => i / FPS);

  let n = 0;
  for (const t of times) {
    await page.evaluate(tt => window.__seek(tt), t);
    const name = mode === 'preview'
      ? `p_${String(t.toFixed(1)).padStart(5, '0')}.png`
      : `f_${String(n).padStart(5, '0')}.jpg`;
    await page.screenshot({
      path: path.join(outDir, name),
      type: mode === 'preview' ? 'png' : 'jpeg',
      quality: mode === 'preview' ? undefined : 92
    });
    n++;
    if (mode === 'full' && n % 150 === 0) console.log('frame', n, '/', times.length);
  }
  await browser.close();
  console.log('done', n);
})();
