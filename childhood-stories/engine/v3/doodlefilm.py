"""MIC Study v3 'handmade doodle' film renderer (Childhood Stories).

Same art language as the daily Stories/Carousels (kit2.py, style reference
"Mom-daughter dates", approved v3 layout), brought to life as a short film:
  * hand-drawn "boil": the ink wobble is re-drawn every 3 frames (on threes),
    geometry stays stable so it reads as one drawing, not flicker
  * camera: push-ins, pans and cuts via a world->screen transform, with
    subtle parallax between background / midground / foreground layers
  * acting: blinks, eye direction, brows, a smile that grows slowly, talking
    mouths, walking, sitting, pointing, floating pencil hearts
Everything (characters, room, props, decorations) is drawn with the kit's
colored-pencil hatching and wobbly ink, on warm cream paper with grain.
"""
import base64, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit2 as K

W, H = 1080, 1920
INK = K.INK
ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PAPER = '#FFF8EC'


def spoly(p, color, **k):
    """kit2.poly() on an opaque paper-coloured base, so shapes hide what is behind them
    (pencil hatching alone is see-through)."""
    return f'<path d="{K.pts2d(p)}Z" fill="{PAPER}"/>' + K.poly(p, color, **k)


def seed(n):
    """Stable geometry per element: every element re-seeds the kit's RNG."""
    K.R.seed(n)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def seg(t, t0, t1):
    return ease((t - t0) / max(1e-6, t1 - t0))


# ------------------------------------------------------------------ face
def face(cx, cy, r, skin='#FFF1E6', look=(0, 0), smile=0.3, blink=False, talk=0.0, brow=0.0, sid=1):
    """kit2.head() drawn with acting controls.
    look: eye direction (-1..1, -1..1); smile 0 (flat) .. 1 (wide); talk 0..1 mouth open;
    brow: +1 = worried (inner ends raised), -1 = cheerful."""
    seed(sid)
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PAPER}"/>'
    s += K.pencil(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>', skin, (cx - r, cy - r, cx + r, cy + r), gap=7, tint=.6)
    s += K.ink(f'M{cx + r} {cy} A{r} {r} 0 1 1 {cx + r - 0.5} {cy - 3}', 4.5)
    e = r * 0.33
    lx, ly = look[0] * r * 0.09, look[1] * r * 0.08
    for sx in (-1, 1):
        ex = cx + sx * e + lx
        ey = cy - r * 0.06 + ly
        if blink:
            s += K.ink(f'M{ex - r * 0.1:.1f} {ey:.1f} q{r * 0.1:.1f} {r * 0.06:.1f} {r * 0.2:.1f} 0', 3.2)
        else:
            s += (f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{r * 0.085 + 1.5:.1f}" ry="{r * 0.115 + 2:.1f}" fill="{INK}"/>'
                  f'<circle cx="{ex + r * 0.03:.1f}" cy="{ey - r * 0.05:.1f}" r="{r * 0.035 + 0.8:.1f}" fill="#fff"/>')
        bx = cx + sx * e
        by = cy - r * 0.3
        outer_y = by + brow * r * 0.03
        inner_y = by - brow * r * 0.06      # worried: inner ends lift
        ly_, ry_ = (outer_y, inner_y) if sx < 0 else (inner_y, outer_y)
        s += K.ink(f'M{bx - r * 0.11:.1f} {ly_:.1f} Q{bx:.1f} {min(ly_, ry_) - r * 0.03:.1f} {bx + r * 0.11:.1f} {ry_:.1f}', 2.6)
    s += (f'<circle cx="{cx - e - r * 0.1}" cy="{cy + r * 0.3}" r="{r * 0.24}" fill="url(#blush)"/>'
          f'<circle cx="{cx + e + r * 0.1}" cy="{cy + r * 0.3}" r="{r * 0.24}" fill="url(#blush)"/>')
    my = cy + r * 0.3
    if talk > 0.05:
        s += (f'<ellipse cx="{cx}" cy="{my + r * 0.02:.1f}" rx="{r * 0.1:.1f}" ry="{r * (0.03 + 0.07 * talk):.1f}" '
              f'fill="#D84343" stroke="{INK}" stroke-width="2.5" filter="url(#ink)"/>')
    else:
        d = r * (0.03 + 0.42 * smile)
        w = r * (0.24 + 0.1 * smile)
        s += K.ink(f'M{cx - w:.1f} {my - d * 0.3:.1f} Q{cx} {my + d:.1f} {cx + w:.1f} {my - d * 0.3:.1f}', 5, '#E53935')
    return s


def ponytail(cx, cy, r, color, side, sid):
    """Scribbled pigtail bunch on one side of the head."""
    seed(sid)
    x0 = cx + side * r * 0.85
    y0 = cy - r * 0.35
    d = ''
    for _ in range(26):
        d += (f'M{x0:.0f} {y0:.0f} Q{x0 + side * K.R.uniform(30, 55):.0f} {y0 + K.R.uniform(10, 40):.0f} '
              f'{x0 + side * K.R.uniform(25, 60):.0f} {y0 + K.R.uniform(60, 115):.0f}')
    return f'<path d="{d}" stroke="{color}" stroke-width="3.2" fill="none" stroke-linecap="round" opacity=".95"/>'


def bow(x, y, s, color, sid):
    seed(sid)
    return (spoly([(x, y), (x - s, y - s * 0.6), (x - s, y + s * 0.6)], color, gap=4) +
            spoly([(x, y), (x + s, y - s * 0.6), (x + s, y + s * 0.6)], color, gap=4) +
            f'<circle cx="{x}" cy="{y}" r="{s * 0.28:.0f}" fill="{color}" stroke="{INK}" stroke-width="3" filter="url(#ink)"/>')


def hand(x, y, skin='#FFF1E6', r=13, point=None):
    s = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{skin}" stroke="{INK}" stroke-width="3.5" filter="url(#ink)"/>'
    if point:
        s += K.stick([(x, y), (x + point[0], y + point[1])], 5)
    return s


# ------------------------------------------------------------------ characters
def child_ava(st):
    """Ava (7): blonde scribbled pigtails with blue bows, lilac dress with a heart print.
    st: x, y (head centre), look, smile, blink, talk, brow, tilt, hand (x,y), hand2 (x,y)."""
    x, y, r = st['x'], st['y'], 100
    tilt = st.get('tilt', 0)
    out = f'<g transform="rotate({tilt:.2f} {x} {y + r})">'
    # torso (dress top) - hidden below the table edge by draw order
    seed(101)
    torso = [(x - 72, y + r + 10), (x + 72, y + r + 10), (x + 105, y + r + 250), (x - 105, y + r + 250)]
    out += spoly(torso, '#B58DF0', angle=-35, gap=5)
    out += K.ink(f'M{x - 40} {y + r + 14} Q{x} {y + r + 44} {x + 40} {y + r + 14}', 3.5)          # collar
    for i, (hx, hy) in enumerate([(-45, 70), (30, 60), (-10, 130), (55, 150), (-60, 180)]):
        seed(120 + i)
        out += K.heart(x + hx, y + r + hy, 9, '#E91E63')
    # hair behind
    out += ponytail(x, y, r, '#D8A65A', -1, 131) + ponytail(x, y, r, '#C8913F', 1, 132)
    out += face(x, y, r, look=st.get('look', (0, 0)), smile=st.get('smile', .3), blink=st.get('blink', False),
                talk=st.get('talk', 0), brow=st.get('brow', 0), sid=140)
    seed(150)
    out += K.hair(x, y, r, '#D8A65A', 'messy', n=55)
    seed(151)
    out += K.hair(x, y, r * 0.96, '#B98534', 'messy', n=22)                                         # two-tone
    out += bow(x - r * 0.92, y - r * 0.4, 20, '#1C8FFF', 160) + bow(x + r * 0.92, y - r * 0.4, 20, '#1C8FFF', 161)
    out += '</g>'
    return out


def child_arms(st):
    """Arms drawn after the table so hands rest on it."""
    x, y, r = st['x'], st['y'], 100
    sh_l, sh_r = (x - 70, y + r + 45), (x + 70, y + r + 45)
    hl, hr = st.get('hand2', (x - 60, 1238)), st['hand']
    el = (lerp(sh_l[0], hl[0], .45) - 25, lerp(sh_l[1], hl[1], .6))
    er = (lerp(sh_r[0], hr[0], .45) + 20, lerp(sh_r[1], hr[1], .6))
    s = K.stick([sh_l, el, hl], 5) + K.stick([sh_r, er, hr], 5)
    # sleeves
    seed(170)
    s += spoly([(sh_l[0] - 20, sh_l[1] - 10), (sh_l[0] + 18, sh_l[1] - 14), (el[0] + 12, el[1] - 4), (el[0] - 16, el[1] + 4)], '#B58DF0', gap=5)
    seed(171)
    s += spoly([(sh_r[0] - 18, sh_r[1] - 14), (sh_r[0] + 20, sh_r[1] - 10), (er[0] + 16, er[1] + 4), (er[0] - 12, er[1] - 4)], '#B58DF0', gap=5)
    s += hand(*hl) + hand(*hr, point=st.get('point', (14, -6)))
    return s


def mom_elena(st):
    """Elena (mom): long dark scribbled hair, coral knit cardigan over a cream top, navy trousers.
    st: x, y (head centre), look, smile, blink, talk, brow, walk (phase or None), seated (0..1)."""
    x, y, r = st['x'], st['y'], 82
    out = ''
    seated = st.get('seated', 0)
    hip_y = y + r + 330
    # legs (standing / walking); when seated the table hides them
    if seated < 0.95:
        ph = st.get('walk')
        sw = 0 if ph is None else math.sin(ph) * 38
        foot_y = 1640
        kl = (x - 30 + sw * 0.4, lerp(hip_y, foot_y, .5))
        kr = (x + 30 - sw * 0.4, lerp(hip_y, foot_y, .5))
        fl = (x - 34 + sw, foot_y)
        fr = (x + 34 - sw, foot_y)
        seed(201)
        out += spoly([(x - 60, hip_y - 20), (x + 60, hip_y - 20), (kr[0] + 26, kr[1]), (fr[0] + 22, fr[1] - 30),
                       (fr[0] - 8, fr[1] - 30), (x, hip_y + 40), (fl[0] + 8, fl[1] - 30), (fl[0] - 22, fl[1] - 30), (kl[0] - 26, kl[1])],
                      '#3E4A66', angle=80, gap=5)
        seed(202)
        out += K.sneaker2(fl[0] - 40, fl[1], 80, '#E0E0E0', flip=False) + K.sneaker2(fr[0] + 40, fr[1], 80, '#E0E0E0', flip=True)
    # long hair falls behind the shoulders (drawn before the torso)
    seed(220)
    back = ''.join(f'M{x + K.R.uniform(-70, 70):.0f} {y - r * 0.6:.0f} Q{x + K.R.uniform(-110, 110):.0f} {y + r * 0.8:.0f} '
                   f'{x + K.R.uniform(-95, 95):.0f} {y + r * 2.1:.0f}' for _ in range(60))
    out += f'<path d="{back}" stroke="#3A2418" stroke-width="3.3" fill="none" stroke-linecap="round" opacity=".95"/>'
    # torso: cream top + open coral cardigan with knit rows and buttons
    seed(210)
    out += spoly([(x - 45, y + r + 8), (x + 45, y + r + 8), (x + 52, hip_y), (x - 52, hip_y)], '#FFF3E6', gap=6)
    seed(211)
    out += spoly([(x - 62, y + r + 4), (x - 20, y + r + 4), (x - 26, hip_y + 12), (x - 82, hip_y + 12)], '#E98A6B', cross=True, gap=5)
    seed(212)
    out += spoly([(x + 20, y + r + 4), (x + 62, y + r + 4), (x + 82, hip_y + 12), (x + 26, hip_y + 12)], '#E98A6B', cross=True, gap=5)
    for i in range(4):
        by = y + r + 60 + i * 60
        out += f'<circle cx="{x - 24}" cy="{by}" r="6" fill="#FFF3E6" stroke="{INK}" stroke-width="2.5" filter="url(#ink)"/>'
    out += K.ink(f'M{x - 82} {hip_y - 4} L{x - 26} {hip_y - 4} M{x + 26} {hip_y - 4} L{x + 82} {hip_y - 4}', 3)   # ribbed hem
    out += face(x, y, r, skin='#F6D9C3', look=st.get('look', (0, 0)), smile=st.get('smile', .35), blink=st.get('blink', False),
                talk=st.get('talk', 0), brow=st.get('brow', 0), sid=230)
    seed(240)
    out += K.hair(x, y, r, '#3A2418', 'long', n=70, length=1.1)
    seed(241)
    out += K.hair(x, y, r * 0.95, '#5A3A28', 'messy', n=18)
    return out


def mom_arms(st):
    x, y, r = st['x'], st['y'], 82
    shl, shr = (x - 62, y + r + 40), (x + 62, y + r + 40)
    hl = st.get('hand2', (x - 70, y + r + 250))
    hr = st.get('hand', (x + 70, y + r + 250))
    el = (lerp(shl[0], hl[0], .5) - 30, lerp(shl[1], hl[1], .55))
    er = (lerp(shr[0], hr[0], .5) + 30, lerp(shr[1], hr[1], .55))
    s = K.stick([shl, el, hl], 5) + K.stick([shr, er, hr], 5)
    seed(250)
    s += spoly([(shl[0] - 22, shl[1] - 14), (shl[0] + 16, shl[1] - 16), (el[0] + 14, el[1]), (el[0] - 16, el[1] + 6)], '#E98A6B', cross=True, gap=5)
    seed(251)
    s += spoly([(shr[0] - 16, shr[1] - 16), (shr[0] + 22, shr[1] - 14), (er[0] + 16, er[1] + 6), (er[0] - 14, er[1])], '#E98A6B', cross=True, gap=5)
    s += hand(*hl, skin='#F6D9C3') + hand(*hr, skin='#F6D9C3', point=st.get('point'))
    return s


# ------------------------------------------------------------------ set: family kitchen at dusk
def set_back(t):
    """Background layer: wall, window with moon and stars, framed child drawing, lamp, counter with pot."""
    s = K.paper(W, H, '#FFF8EC')
    seed(1)
    s += K.pencil(f'<rect x="0" y="0" width="{W}" height="1640"/>', '#FFE9CF', (0, 0, W, 1640), angle=-12, gap=18, tint=.08)
    seed(2)
    s += K.pencil(f'<rect x="0" y="1640" width="{W}" height="{H - 1640}"/>', '#D7B98E', (0, 1640, W, H), angle=-4, gap=9, tint=.25)
    s += K.ink('M0 1642 Q540 1632 1080 1644', 3.5)
    # window
    seed(3)
    s += K.pencil('<rect x="110" y="330" width="330" height="400"/>', '#5C6BC0', (110, 330, 440, 730), angle=-30, gap=6, tint=.25)
    s += K.ink('M110 330 L440 332 L438 730 L112 728 Z M275 331 L276 729 M111 530 L439 531', 5)
    s += (f'<path d="M190 430 a42 42 0 1 0 50 52 a34 34 0 1 1 -50 -52z" fill="#FFF59D" stroke="{INK}" stroke-width="3.5" filter="url(#ink)"/>')
    for i, (sx, sy, sr) in enumerate([(360, 400, 16), (330, 620, 12), (170, 640, 11), (400, 690, 9)]):
        seed(10 + i)
        s += K.star(sx, sy, sr)
    for i, cx0 in enumerate((70, 440)):
        seed(20 + i)
        s += spoly([(cx0, 300), (cx0 + 70, 300), (cx0 + 50, 760), (cx0 + 5, 770)], '#F48FB1', angle=85, gap=6)
    s += K.ink('M60 300 L520 298', 5)
    # framed child drawing (sun + house) on the wall
    seed(30)
    s += spoly([(610, 420), (780, 416), (784, 560), (606, 564)], '#FFFFFF', gap=9)
    seed(31)
    s += spoly([(650, 520), (700, 482), (745, 520), (745, 552), (650, 552)], '#EF9A9A', gap=5, w=3)
    s += f'<circle cx="752" cy="456" r="16" fill="#FFD54F" stroke="{INK}" stroke-width="2.5" filter="url(#ink)"/>'
    # pendant lamp + warm glow
    s += K.ink('M540 0 L540 200', 3.5)
    seed(40)
    s += spoly([(485, 200), (595, 200), (640, 285), (440, 285)], '#FFCA28', angle=-20, gap=5)
    s += '<ellipse cx="540" cy="1150" rx="520" ry="420" fill="url(#glow)"/>'
    # counter with pot (right)
    seed(50)
    s += spoly([(900, 1170), (1080, 1170), (1080, 1640), (905, 1640)], '#A5D6A7', angle=-60, gap=6)
    s += K.ink('M890 1170 L1080 1168', 6)
    seed(51)
    s += spoly([(930, 1100), (1030, 1100), (1022, 1168), (938, 1168)], '#90A4AE', gap=5)
    s += K.ink('M915 1110 L930 1110 M1030 1110 L1046 1110', 4)
    # steam curls (animated)
    for i in range(3):
        ph = t * 0.9 + i * 1.3
        yy = 1080 - (ph % 3) * 45
        op = max(0.0, 0.7 - (ph % 3) * 0.23)
        s += (f'<path d="M{950 + i * 30} {yy:.0f} q-14 -18 0 -36 q14 -18 0 -36" stroke="#B0BEC5" stroke-width="4" fill="none" '
              f'stroke-linecap="round" opacity="{op:.2f}" filter="url(#ink)"/>')
    return s


def chairs():
    s = ''
    for i, cx0 in enumerate((430, 700)):
        seed(60 + i)
        s += spoly([(cx0 - 85, 980), (cx0 + 85, 980), (cx0 + 80, 1250), (cx0 - 80, 1250)], '#BCAAA4', angle=88, gap=7)
        s += K.ink(f'M{cx0 - 85} 1030 L{cx0 + 85} 1030 M{cx0 - 83} 1090 L{cx0 + 83} 1090', 3)
        s += K.stick([(cx0 - 78, 1330), (cx0 - 82, 1640)], 6) + K.stick([(cx0 + 78, 1330), (cx0 + 82, 1640)], 6)
    return s


def table_and_book(t, word_glow=0.0):
    seed(70)
    s = spoly([(120, 1250), (960, 1246), (975, 1285), (108, 1290)], '#C8A27A', angle=-8, gap=6)
    seed(71)
    s += spoly([(135, 1290), (950, 1286), (945, 1335), (140, 1338)], '#B08968', angle=-8, gap=6)            # apron
    s += K.stick([(160, 1335), (165, 1640)], 7) + K.stick([(925, 1332), (920, 1640)], 7)
    # a mug and a pencil on the table
    seed(72)
    s += spoly([(745, 1180), (800, 1180), (796, 1248), (749, 1248)], '#81D4FA', gap=5)
    s += K.ink('M800 1195 q24 4 20 24 q-4 18 -22 16', 4)
    s += K.heart(772, 1215, 8, '#E91E63', fill=False)
    seed(73)
    s += spoly([(250, 1240), (345, 1222), (348, 1230), (253, 1248)], '#FFD54F', gap=4, w=3)
    s += spoly([(345, 1222), (362, 1224), (348, 1230)], '#FFCCBC', gap=3, w=3)
    # open book (reading)
    seed(74)
    s += spoly([(340, 1250), (468, 1236), (470, 1175), (352, 1182)], '#FFFDF8', gap=10)
    seed(75)
    s += spoly([(470, 1236), (610, 1250), (598, 1182), (470, 1175)], '#FFFDF8', gap=10)
    for i in range(4):
        yy = 1192 + i * 11
        s += K.ink(f'M{364 + i * 2} {yy + 2} L{455} {yy - 2}', 2, '#9E9E9E')
        if i != 2:
            s += K.ink(f'M{484} {yy - 1} L{588 - i * 2} {yy + 3}', 2, '#9E9E9E')
    if word_glow > 0:
        s += f'<ellipse cx="526" cy="1213" rx="40" ry="11" fill="#FFE082" opacity="{0.75 * word_glow:.2f}"/>'
    s += ('<text x="498" y="1219" font-family="Architects Daughter" font-size="17" fill="#1f1b24" '
          'transform="rotate(3 498 1219)">through</text>')
    return s


def foreground():
    seed(80)
    s = spoly([(20, 1760), (150, 1760), (135, 1920), (35, 1920)], '#FFAB91', angle=-30, gap=5)
    for i in range(9):
        seed(81 + i)
        s += K.leaf(85 + K.R.uniform(-40, 40), 1690 + K.R.uniform(-60, 50), K.R.uniform(22, 30), K.R.uniform(-150, -20))
    return s


def floating_hearts(t, t0):
    s = ''
    for i in range(3):
        k = t - t0 - i * 0.55
        if k <= 0:
            continue
        yy = 1170 - k * 70
        xx = 520 + i * 40 + math.sin(k * 2 + i) * 14
        op = max(0.0, min(1.0, k * 2)) * max(0.0, 1 - k / 3.2)
        seed(300 + i)
        s += f'<g opacity="{op:.2f}">' + K.heart(xx, yy, 14 + i * 3, ['#E91E63', '#F06292', '#EC407A'][i]) + '</g>'
    return s


# ------------------------------------------------------------------ frame + camera
def camera_group(inner, cx, cy, s, depth=1.0):
    """World -> screen. depth < 1 moves/zooms less (background), > 1 more (foreground)."""
    sd = 1 + (s - 1) * depth
    cxd = 540 + (cx - 540) * depth
    cyd = 960 + (cy - 960) * depth
    return f'<g transform="translate(540 960) scale({sd:.4f}) translate({-cxd:.2f} {-cyd:.2f})">{inner}</g>'


def glow_def():
    return ('<radialGradient id="glow"><stop offset="0" stop-color="#FFE082" stop-opacity=".30"/>'
            '<stop offset="1" stop-color="#FFE082" stop-opacity="0"/></radialGradient>')


def svg_frame(layers, boil):
    d = K.defs(4 + boil).replace('</defs>', K.paper_filter() + glow_def() + '</defs>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{d}{layers}</svg>'


def font_face_css():
    F = os.path.join(ENGINE, 'fonts')
    def b(p):
        return base64.b64encode(open(os.path.join(F, p), 'rb').read()).decode()
    return (f"@font-face{{font-family:'Architects Daughter';src:url(data:font/woff2;base64,{b('architects-daughter-latin-400-normal.woff2')}) format('woff2')}}"
            f"@font-face{{font-family:'Nunito';font-weight:800;src:url(data:font/woff2;base64,{b('nunito-latin-800-normal.woff2')}) format('woff2')}}")


PAGE = '''<!doctype html><html><head><meta charset="utf-8"><style>{fonts}
html,body{{margin:0;padding:0;background:#FFF8EC}}#stage{{position:relative;width:1080px;height:1920px;overflow:hidden}}
#fade{{position:absolute;inset:0;background:#FFF8EC;opacity:0}}
#sub{{position:absolute;left:0;right:0;top:1500px;display:flex;justify-content:center;opacity:0}}
#sub span{{max-width:860px;text-align:center;font-family:'Nunito',sans-serif;font-weight:800;font-size:50px;line-height:1.25;
color:#1f1b24;background:rgba(255,248,236,.92);border:3px solid #1f1b24;border-radius:30px 26px 32px 24px;padding:14px 30px}}
</style></head><body><div id="stage"><div id="art"></div><div id="fade"></div><div id="sub"><span id="subt"></span></div></div></body></html>'''
