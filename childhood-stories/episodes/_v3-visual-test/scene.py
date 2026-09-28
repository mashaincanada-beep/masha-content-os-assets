#!/usr/bin/env python3
"""MIC Study v3 visual test - 18 s, one child, one parent, one room, one emotional beat.

Ava (7) is reading at the kitchen table in the evening and gets stuck on a word.
Mom leaves the stove, sits beside her, and they try the first sound together.
The word comes out; a small smile, a few pencil hearts.

usage: python3 scene.py [--stills] [--out DIR]
Visual test only: dialogue is shown as subtitles (no voices yet - the child
voice provider is still being approved), with music and room ambience.
"""
import argparse, math, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, '..', '..', 'engine')
sys.path.insert(0, os.path.join(ENGINE, 'v3'))
sys.path.insert(0, ENGINE)
import doodlefilm as D
from doodlefilm import lerp, seg

FPS, DUR = 30, 18.0
SUBS = [(6.2, 8.0, "I... don't know this word."),
        (11.3, 13.2, "Let's try the first sound. Together."),
        (14.3, 16.3, "Th... thr... through!")]
BLINKS_CHILD = [3.2, 9.1, 13.25, 16.9]
BLINKS_MOM = [2.4, 7.2, 12.0, 15.2]


def blinking(t, times):
    return any(0 <= t - b < 0.13 for b in times)


def talking(t, t0, t1):
    if not (t0 <= t <= t1):
        return 0.0
    return 0.5 + 0.5 * math.sin((t - t0) * 17) if int((t - t0) * 7) % 5 != 4 else 0.0


def camera(t):
    """Four shots: wide push-in, insert on the book, medium (mom comes to sit), close two-shot."""
    if t < 5.0:
        k = seg(t, 0, 5.0)
        return lerp(540, 520, k), lerp(1000, 1030, k), lerp(1.0, 1.12, k)
    if t < 8.0:
        k = seg(t, 5.0, 8.0)
        return lerp(470, 490, k), 1110, lerp(2.2, 2.34, k)
    if t < 13.0:
        k = seg(t, 8.0, 13.0)
        return lerp(575, 590, k), lerp(1000, 1010, k), lerp(1.42, 1.5, k)
    k = seg(t, 13.0, 18.0)
    return 565, lerp(985, 995, k), lerp(1.86, 2.02, k)


def child_state(t):
    st = {'x': 430, 'y': 930, 'blink': blinking(t, BLINKS_CHILD)}
    # finger along the line, stops under the word, trembles, later traces the word
    if t < 5.0:
        fx = lerp(390, 470, seg(t, 0.5, 4.8))
    elif t < 6.1:
        fx = lerp(470, 505, seg(t, 5.0, 6.0))
    elif t < 14.3:
        fx = 505 + math.sin(t * 22) * (1.5 if t < 8 else 0.6)
    else:
        fx = lerp(505, 548, seg(t, 14.3, 16.1))
    st['hand'] = (fx - 12, 1242)
    st['point'] = (10, -15)
    st['hand2'] = (360, 1244)
    st['talk'] = talking(t, 14.3, 16.1)
    if t < 8.0:
        st.update(look=(0.2, 1.0), smile=0.18, brow=0.2, tilt=-2)
    elif t < 13.0:
        # stuck: head lower, worried brows; glances at mom once she sits
        glance = seg(t, 11.0, 11.6)
        st.update(look=(lerp(0.1, 0.9, glance), lerp(1.0, 0.1, glance)), smile=0.06, brow=0.8, tilt=lerp(-2, -5, seg(t, 8.0, 9.5)))
    else:
        up = seg(t, 13.3, 13.9)
        st.update(look=(lerp(0.9, 0.2, seg(t, 14.2, 14.5)), lerp(0.0, 0.9, seg(t, 14.2, 14.5)) if t < 16.2 else lerp(0.9, -0.1, seg(t, 16.2, 16.7))),
                  smile=0.08 + 0.5 * seg(t, 16.2, 17.2), brow=lerp(0.6, -0.2, seg(t, 15.8, 16.6)), tilt=lerp(-4, 2, up))
    return st


def mom_state(t):
    st = {'blink': blinking(t, BLINKS_MOM), 'talk': talking(t, 11.3, 13.1)}
    if t < 8.4:
        # at the stove, stirring; glances towards her daughter at 4 s
        ang = t * 3.2
        st.update(x=820, y=770, seated=0, walk=None, smile=0.3,
                  look=(0.7, 0.8) if not (3.8 < t < 6.5) else (-1.0, 0.3),
                  hand=(965 + math.cos(ang) * 16, 1128 + math.sin(ang) * 6), hand2=(760, 1190), point=(0, -40))
    elif t < 10.2:
        k = seg(t, 8.4, 10.2)
        st.update(x=lerp(820, 700, k), y=770 + abs(math.sin(t * 6)) * 6, seated=0, walk=t * 6, smile=0.3,
                  look=(-1.0, 0.4), hand=(lerp(890, 800, k), 1120), hand2=(lerp(750, 630, k), 1150))
    else:
        k = seg(t, 10.2, 11.0)
        reach = seg(t, 11.1, 11.8)
        nod = math.sin(seg(t, 16.3, 17.0) * math.pi) * 8
        st.update(x=700, y=lerp(770, 880, k) + nod, seated=k, walk=None,
                  smile=0.32 + 0.3 * seg(t, 16.2, 17.0), look=(-1.0, lerp(0.4, 0.9, reach)) if t < 16.2 else (-1.0, 0.2),
                  hand=(lerp(780, 610, reach), lerp(1200, 1228, reach)), hand2=(lerp(640, 620, reach), 1245),
                  point=(-18, -4) if reach > 0.5 else None)
    return st


def frame_svg(t, fi):
    boil = (fi // 3) % 4                                  # drawings change "on threes"
    cx, cy, s = camera(t)
    word_glow = seg(t, 14.4, 15.4) if t < 17 else 1.0
    bg = D.set_back(t)
    mid = D.chairs() + D.mom_elena(mom_state(t)) + D.child_ava(child_state(t))
    top = (D.table_and_book(t, word_glow) + D.child_arms(child_state(t)) + D.mom_arms(mom_state(t)) +
           (D.floating_hearts(t, 16.3) if t > 16.3 else ''))
    layers = (D.camera_group(bg, cx, cy, s, 0.9) + D.camera_group(mid + top, cx, cy, s, 1.0) +
              D.camera_group(D.foreground(), cx, cy, s, 1.12))
    return D.svg_frame(layers, boil)


def sub_at(t):
    for a, b, txt in SUBS:
        if a <= t <= b:
            return txt, min(1, (t - a) / 0.15, (b - t) / 0.15)
    return '', 0


def render(out, stills=False):
    from playwright.sync_api import sync_playwright
    fdir = os.path.join(out, 'frames')
    os.makedirs(fdir, exist_ok=True)
    times = [0.5, 4.5, 6.8, 9.3, 11.9, 14.8, 17.0] if stills else [i / FPS for i in range(int(DUR * FPS))]
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.set_content(D.PAGE.format(fonts=D.font_face_css()))
        pg.evaluate('document.fonts.ready')
        for n, t in enumerate(times):
            fi = int(round(t * FPS))
            txt, op = sub_at(t)
            fade = max(seg(t, 17.35, 18.0), 1 - seg(t, 0.0, 0.5))
            pg.evaluate('([svg, txt, op, fade]) => {document.getElementById("art").innerHTML = svg;'
                        'document.getElementById("subt").textContent = txt; document.getElementById("sub").style.opacity = op;'
                        'document.getElementById("fade").style.opacity = fade;}', [frame_svg(t, fi), txt, op, fade])
            name = f'still_{t:05.2f}.png' if stills else f'f_{n:04d}.jpg'
            pg.screenshot(path=os.path.join(fdir if not stills else out, name), type='png' if stills else 'jpeg',
                          **({} if stills else {'quality': 93}))
            if n % 60 == 0:
                print(f'frame {n}/{len(times)}  {time.time() - t0:.0f}s', flush=True)
        b.close()


def audio(out):
    from cs import audio as A
    import numpy as np
    total = DUR
    score = A.Score('F', 72, 23)
    music = score.render([(0, 8.0, 'uncertain'), (8.0, 13.2, 'reflective'), (13.2, total, 'hopeful')], total)
    sfx = []
    for name, t, g in [('page', 0.7, 0.5), ('pencil', 2.0, 0.3), ('footsteps', 8.5, 0.55), ('chair', 10.3, 0.5)]:
        try:
            sfx.append((t, A.sfx(name, seed=int(t * 10)), g, 0.1))
        except Exception as e:  # pragma: no cover
            print('sfx skipped', name, e)
    wav = os.path.join(out, 'mix.wav')
    A.mix(total, [], sfx, [(0, total, 'kitchen')], music, wav)
    return wav


def mux(out, wav):
    mp4 = os.path.join(out, 'v3-visual-test.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(out, 'frames', 'f_%04d.jpg'),
                    '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-shortest', mp4], check=True)
    return mp4


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stills', action='store_true')
    ap.add_argument('--out', default=os.path.join(HERE, 'out'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    render(a.out, a.stills)
    if not a.stills:
        print(mux(a.out, audio(a.out)))
