import sys, os
from playwright.sync_api import sync_playwright
times = [float(x) for x in sys.argv[1].split(',')] if sys.argv[1]!='ALL' else None
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--force-color-profile=srgb','--font-render-hinting=none'])
    pg = b.new_page(viewport={'width':1080,'height':1920}, device_scale_factor=1)
    pg.goto('file://'+os.path.abspath('overlay.html'))
    pg.wait_for_timeout(700)
    if times is None:
        N = int(round(30.0*30))
        for i in range(N):
            pg.evaluate('t=>window.__seek(t)', i/30*1000)
            pg.screenshot(path=f'{outdir}/f_{i:05d}.png', omit_background=True)
            if i%90==0: print(i, flush=True)
    else:
        for t in times:
            pg.evaluate('t=>window.__seek(t)', t*1000)
            pg.screenshot(path=f'{outdir}/t_{t:06.2f}.png', omit_background=True)
    b.close()
print('done')
