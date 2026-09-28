"""MIC Study v3 doodle characters, generated from engine/cast.json so every recurring
character keeps the same identity (skin, hair style and colour, clothing palette, age)
in every film.  Same art language as kit2.py / the daily Stories.

draw_body(key, spec, st) -> svg drawn BEFORE the set's midground (table, counter...)
draw_arms(key, spec, st) -> svg drawn AFTER it, so hands can rest on tables and point at things

st (per-frame state, world coords):
  x          body centre x
  floor      y of the feet line (standing)                         default 1640
  pose       'stand' | 'sit' | 'walk'
  y          head centre (optional; derived from pose/age if absent)
  look       (dx, dy) eye direction -1..1
  smile      0..1, brow -1..1 (+ worried), talk 0..1 (mouth open), blink bool, tilt degrees
  hand, hand2   (x, y) right / left hand targets (optional)
  point      (dx, dy) finger from the right hand (optional)
  phase      walk cycle phase (radians)
  scale      overall size multiplier (default 1)
"""
import math
import doodlefilm as D
from doodlefilm import K, spoly, seed, face, lerp

SKIN = {"fair": "#FFF1E6", "light": "#FCE3D0", "olive": "#EFCFAE", "tan": "#E3B98F", "brown": "#C68E62", "deep": "#8D5A3B"}


def _h(key):
    return sum(ord(c) * (i + 1) for i, c in enumerate(key)) % 9000


def dims(spec):
    """(head radius, head-to-feet height) by age - big heads, childlike proportions."""
    if spec.get("kind") == "child":
        a = spec.get("age", 9)
        r = 100 if a <= 8 else 92 if a <= 11 else 86
        hgt = 430 + (a - 6) * 32
    else:
        r = 82
        hgt = 880 * min(1.0, spec.get("height", 800) / 800)          # grandparents are a little shorter
    return r, hgt


def head_y(spec, st):
    if "y" in st:
        return st["y"]
    r, hgt = dims(spec)
    floor = st.get("floor", 1640)
    if st.get("pose") == "sit":
        return floor - hgt * 0.72
    return floor - hgt


def _hair(key, spec, x, y, r, layer):
    """layer 'back' (behind body) or 'front' (over the head)."""
    hs = spec.get("hair", {})
    style, col = hs.get("style", "short"), hs.get("color", "#3A2418")
    acc = hs.get("accent", "#1C8FFF")
    b = _h(key)
    s = ""
    dark = "#000000"
    if layer == "back":
        if style in ("long_adult", "long", "braids", "hijab"):
            if style == "hijab":
                hc = spec.get("hijab_color", "#6E6BD8")
                s += spoly([(x - r * 1.18, y - r * 0.2), (x - r * 0.9, y - r * 1.15), (x + r * 0.9, y - r * 1.15),
                            (x + r * 1.18, y - r * 0.2), (x + r * 1.25, y + r * 1.6), (x - r * 1.25, y + r * 1.6)], hc, gap=5)
            else:
                seed(b + 1)
                back = "".join(f"M{x + K.R.uniform(-r * .85, r * .85):.0f} {y - r * .6:.0f} Q{x + K.R.uniform(-r * 1.3, r * 1.3):.0f} {y + r * .8:.0f} "
                               f"{x + K.R.uniform(-r * 1.15, r * 1.15):.0f} {y + r * (2.1 if style != 'braids' else .9):.0f}" for _ in range(55))
                s += f'<path d="{back}" stroke="{col}" stroke-width="3.3" fill="none" stroke-linecap="round" opacity=".95"/>'
            if style == "braids":
                for side in (-1, 1):
                    bx = x + side * r * 0.95
                    d = "".join(f"M{bx - 12:.0f} {y + r * .3 + i * 26:.0f} l24 12 M{bx + 12:.0f} {y + r * .3 + i * 26:.0f} l-24 12" for i in range(7))
                    s += f'<path d="{d}" stroke="{col}" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#ink)"/>'
        if style in ("ponytail",):
            s += D.ponytail(x, y, r, col, 1, b + 2)
        if style in ("pigtails",):
            s += D.ponytail(x, y, r, col, -1, b + 3) + D.ponytail(x, y, r, col, 1, b + 4)
        if style == "afro":
            seed(b + 5)
            d = "".join(f"M{x + (r * 1.25) * math.cos(a):.0f} {y - r * .15 + (r * 1.2) * math.sin(a):.0f} "
                        f"q{K.R.uniform(-14, 14):.0f} {K.R.uniform(-14, 14):.0f} {K.R.uniform(-16, 16):.0f} {K.R.uniform(-16, 16):.0f}"
                        for a in [K.R.uniform(0, 2 * math.pi) for _ in range(260)])
            s += f'<path d="{d}" stroke="{col}" stroke-width="4" fill="none" stroke-linecap="round"/>'
        return s
    # front layer
    if style == "hijab":
        hc = spec.get("hijab_color", "#6E6BD8")
        s += K.ink(f"M{x - r * 1.05} {y + r * .2} Q{x - r * 1.05} {y - r * 1.2} {x} {y - r * 1.12} Q{x + r * 1.05} {y - r * 1.2} {x + r * 1.05} {y + r * .2}", 5)
        seed(b + 6)
        s += K.pencil(f'<path d="M{x - r * 1.1} {y + r * .25} Q{x - r * 1.1} {y - r * 1.25} {x} {y - r * 1.18} Q{x + r * 1.1} {y - r * 1.25} {x + r * 1.1} {y + r * .25} '
                      f'L{x + r * .92} {y + r * .1} Q{x + r * .9} {y - r * .95} {x} {y - r * .95} Q{x - r * .9} {y - r * .95} {x - r * .92} {y + r * .1}Z"/>',
                      hc, (x - r * 1.2, y - r * 1.3, x + r * 1.2, y + r * .3), gap=5, tint=.5)
        return s
    if style == "bald":
        seed(b + 7)
        for side in (-1, 1):
            d = "".join(f"M{x + side * r * .95:.0f} {y - r * .1 + i * 6:.0f} q{side * 10} -4 {side * 16} 2" for i in range(6))
            s += f'<path d="{d}" stroke="{col}" stroke-width="3" fill="none"/>'
        return s
    if style == "buzz":
        seed(b + 8)
        dots = "".join(f'<circle cx="{x + r * .85 * math.cos(a):.0f}" cy="{y - r * .15 + r * .8 * math.sin(a):.0f}" r="2.2" fill="{col}"/>'
                       for a in [K.R.uniform(math.pi * 1.08, math.pi * 1.92) for _ in range(90)])
        return dots + K.ink(f"M{x - r * .95} {y - r * .25} Q{x} {y - r * 1.25} {x + r * .95} {y - r * .25}", 4, col)
    if style == "afro":
        return ""
    if style == "curly":
        seed(b + 9)
        d = "".join(f"M{x + r * K.R.uniform(-.95, .95):.0f} {y - r * K.R.uniform(.55, 1.15):.0f} a9 9 0 1 1 1 0" for _ in range(60))
        return f'<path d="{d}" stroke="{col}" stroke-width="3.4" fill="none"/>'
    seed(b + 10)
    if style in ("long_adult", "long", "braids"):
        s += K.hair(x, y, r, col, "long", n=60, length=1.05)
    elif style == "bun":
        s += K.hair(x, y, r, col, "bun", n=45)
    elif style == "spiky":
        s += K.hair(x, y, r * 1.05, col, "messy", n=80)
    else:
        s += K.hair(x, y, r, col, "messy", n=50 if style != "adult_m" else 40)
    seed(b + 11)
    s += K.hair(x, y, r * .95, _shade(col), "messy", n=16)                     # two-tone
    if style in ("ponytail", "pigtails"):
        s += D.bow(x + r * .92, y - r * .4, 18, acc, b + 12)
        if style == "pigtails":
            s += D.bow(x - r * .92, y - r * .4, 18, acc, b + 13)
    return s


def _shade(hexcol, k=0.78):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


def _torso(key, spec, x, y, r, hip):
    top = spec.get("top", {})
    style, col, acc = top.get("style", "tee"), top.get("color", "#FFB84D"), top.get("accent", "#FFFFFF")
    b = _h(key) + 100
    wtop, wbot = (70 if spec.get("kind") == "child" else 62), (92 if spec.get("kind") == "child" else 80)
    if spec.get("build") == "broad":
        wtop, wbot = wtop + 14, wbot + 14
    y0 = y + r + 6
    bottom = spec.get("bottom", {})
    s = ""
    if style == "dress" or bottom.get("style") == "dress":
        seed(b)
        s += spoly([(x - wtop, y0), (x + wtop, y0), (x + wbot + 45, hip + 90), (x - wbot - 45, hip + 90)], col, angle=-35)
        for i, (hx, hy) in enumerate([(-35, 70), (30, 60), (-10, 130), (45, 160), (-50, 190)]):
            seed(b + 20 + i)
            s += K.heart(x + hx, y0 + hy, 9, "#E91E63")
        return s
    cross = style in ("sweater", "cardigan")
    seed(b)
    if style == "cardigan":
        s += spoly([(x - 45, y0 + 2), (x + 45, y0 + 2), (x + 52, hip), (x - 52, hip)], acc, gap=6)
        seed(b + 1)
        s += spoly([(x - wtop, y0), (x - 20, y0), (x - 26, hip + 12), (x - wbot, hip + 12)], col, cross=True)
        seed(b + 2)
        s += spoly([(x + 20, y0), (x + wtop, y0), (x + wbot, hip + 12), (x + 26, hip + 12)], col, cross=True)
        for i in range(4):
            s += f'<circle cx="{x - 24}" cy="{y0 + 55 + i * (hip - y0 - 60) / 4:.0f}" r="6" fill="{acc}" stroke="{D.INK}" stroke-width="2.5" filter="url(#ink)"/>'
    else:
        s += spoly([(x - wtop, y0), (x + wtop, y0), (x + wbot, hip + 10), (x - wbot, hip + 10)], col, angle=-35 if not cross else -40, cross=cross)
    if style in ("sweater", "cardigan", "hoodie"):
        s += K.ink(f"M{x - wbot + 4} {hip - 2} L{x + wbot - 4} {hip - 2}", 3)                          # ribbed hem
    if style == "hoodie":
        s += K.ink(f"M{x - 38} {y0 + 4} Q{x} {y0 + 40} {x + 38} {y0 + 4}", 4)
        s += K.ink(f"M{x - 12} {y0 + 22} l-4 50 M{x + 12} {y0 + 22} l4 50", 2.5)
        s += K.ink(f"M{x - 45} {hip - 70} L{x + 45} {hip - 70} L{x + 38} {hip - 20} L{x - 38} {hip - 20} Z", 3)
    elif style == "shirt":
        s += K.ink(f"M{x - 30} {y0 + 2} L{x} {y0 + 28} L{x + 30} {y0 + 2} M{x} {y0 + 28} L{x} {hip}", 3)
        for i in range(3):
            s += f'<circle cx="{x + 6}" cy="{y0 + 60 + i * 55}" r="4.5" fill="#FFFFFF" stroke="{D.INK}" stroke-width="2"/>'
    elif style in ("tee", "long"):
        s += K.ink(f"M{x - 34} {y0 + 2} Q{x} {y0 + 30} {x + 34} {y0 + 2}", 3.5)
    if top.get("stripes"):
        for i in range(4):
            yy = y0 + 45 + i * (hip - y0 - 40) / 4
            s += K.ink(f"M{x - wtop - 6 - i * 5:.0f} {yy:.0f} L{x + wtop + 6 + i * 5:.0f} {yy:.0f}", 7, acc)
    if top.get("logo"):
        seed(b + 30)
        s += K.star(x, y0 + 80, 18, "#FFD54F")
    if spec.get("glasses") is not None:
        pass
    return s


def _legs(key, spec, x, hip, floor, st):
    bottom = spec.get("bottom", {})
    col = bottom.get("color", "#3E4A66")
    shoes = spec.get("shoes", "#E0E0E0")
    kind = bottom.get("style", "pants")
    ph = st.get("phase")
    sw = 0 if ph is None or st.get("pose") != "walk" else math.sin(ph) * 36
    fl, fr = (x - 30 + sw, floor), (x + 30 - sw, floor)
    s = ""
    if kind in ("dress", "skirt"):
        if kind == "skirt":
            seed(_h(key) + 200)
            s += spoly([(x - 70, hip - 10), (x + 70, hip - 10), (x + 105, hip + 150), (x - 105, hip + 150)], col, angle=-30)
        top_y = hip + (150 if kind == "skirt" else 90)
        s += K.stick([(x - 26, top_y), fl], 5) + K.stick([(x + 26, top_y), fr], 5)
        if spec.get("socks"):
            s += K.ink(f"M{fl[0] - 8} {floor - 40} l14 0 M{fr[0] - 6} {floor - 40} l14 0", 5, spec["socks"])
    else:
        knee_y = lerp(hip, floor, .5)
        seed(_h(key) + 201)
        if kind == "shorts":
            s += spoly([(x - 62, hip - 14), (x + 62, hip - 14), (x + 66, knee_y - 30), (x + 6, knee_y - 30), (x, hip + 30),
                        (x - 6, knee_y - 30), (x - 66, knee_y - 30)], col, angle=80)
            s += K.stick([(x - 34, knee_y - 30), fl], 5) + K.stick([(x + 34, knee_y - 30), fr], 5)
        else:
            s += spoly([(x - 60, hip - 16), (x + 60, hip - 16), (fr[0] + 26, floor - 28), (fr[0] - 10, floor - 28), (x, hip + 40),
                        (fl[0] + 10, floor - 28), (fl[0] - 26, floor - 28)], col, angle=80)
            s += K.ink(f"M{x - 34} {knee_y:.0f} q6 6 12 0 M{x + 22} {knee_y:.0f} q6 6 12 0", 2.2)          # knee creases
    seed(_h(key) + 202)
    w = 64 if spec.get("kind") == "child" else 80
    s += K.sneaker2(fl[0] - w * .55, floor, w, shoes if shoes != "#FFFFFF" else "#ECEFF1") + K.sneaker2(fr[0] + w * .55, floor, w, shoes if shoes != "#FFFFFF" else "#ECEFF1", flip=True)
    return s


def draw_body(key, spec, st):
    base = key.split("#")[0]
    sc = st.get("scale", 1.0)
    x = st["x"]
    r, hgt = dims(spec)
    y = head_y(spec, st)
    floor = st.get("floor", 1640)
    hip = y + r + (hgt - r) * ((0.52 if spec.get("kind") == "child" else 0.5) if st.get("pose") != "sit" else (0.4 if spec.get("kind") == "child" else 0.36))
    out = f'<g transform="translate({x} {y}) scale({sc}) translate({-x} {-y}) rotate({st.get("tilt", 0):.2f} {x} {y + r})">'
    out += _hair(base, spec, x, y, r, "back")
    if st.get("pose") != "sit":
        out += _legs(base, spec, x, hip, floor, st)
    out += _torso(base, spec, x, y, r, hip)
    out += face(x, y, r, skin=SKIN.get(spec.get("skin"), "#FFF1E6"), look=st.get("look", (0, 0)), smile=st.get("smile", .3),
                blink=st.get("blink", False), talk=st.get("talk", 0), brow=st.get("brow", 0), sid=_h(base) + 300)
    if spec.get("beard"):
        seed(_h(base) + 310)
        d = "".join(f'<circle cx="{x + r * K.R.uniform(-.55, .55):.0f}" cy="{y + r * K.R.uniform(.45, .85):.0f}" r="1.8" fill="{spec["hair"]["color"]}"/>' for _ in range(70))
        out += d
    if spec.get("glasses"):
        e = r * .33
        out += (f'<circle cx="{x - e}" cy="{y - r * .06}" r="{r * .2:.0f}" fill="none" stroke="{D.INK}" stroke-width="3.5" filter="url(#ink)"/>'
                f'<circle cx="{x + e}" cy="{y - r * .06}" r="{r * .2:.0f}" fill="none" stroke="{D.INK}" stroke-width="3.5" filter="url(#ink)"/>'
                + K.ink(f"M{x - e + r * .2} {y - r * .08} L{x + e - r * .2} {y - r * .08}", 3))
    out += _hair(base, spec, x, y, r, "front")
    out += "</g>"
    return out


def draw_arms(key, spec, st):
    base = key.split("#")[0]
    sc = st.get("scale", 1.0)
    x = st["x"]
    r, hgt = dims(spec)
    y = head_y(spec, st)
    hip = y + r + (hgt - r) * ((0.52 if spec.get("kind") == "child" else 0.5) if st.get("pose") != "sit" else (0.4 if spec.get("kind") == "child" else 0.36))
    sw = 0 if st.get("phase") is None or st.get("pose") != "walk" else math.sin(st["phase"]) * 30
    shl, shr = (x - (66 if spec.get("kind") == "child" else 60), y + r + 42), (x + (66 if spec.get("kind") == "child" else 60), y + r + 42)
    hl = tuple(st.get("hand2") or (x - 70 - sw * .3, hip + 20 - abs(sw) * .2))
    hr = tuple(st.get("hand") or (x + 70 + sw * .3, hip + 20 - abs(sw) * .2))
    el = (lerp(shl[0], hl[0], .5) - 26, lerp(shl[1], hl[1], .55))
    er = (lerp(shr[0], hr[0], .5) + 26, lerp(shr[1], hr[1], .55))
    top = spec.get("top", {})
    col = top.get("color", "#FFB84D")
    long_sleeve = top.get("style") in ("cardigan", "sweater", "hoodie", "shirt", "long")
    skin = SKIN.get(spec.get("skin"), "#FFF1E6")
    s = f'<g transform="translate({x} {y}) scale({sc}) translate({-x} {-y})">'
    s += K.stick([shl, el, hl], 5) + K.stick([shr, er, hr], 5)
    seed(_h(base) + 400)
    end_l = el if long_sleeve else (lerp(shl[0], el[0], .55), lerp(shl[1], el[1], .55))
    end_r = er if long_sleeve else (lerp(shr[0], er[0], .55), lerp(shr[1], er[1], .55))
    s += spoly([(shl[0] - 20, shl[1] - 12), (shl[0] + 16, shl[1] - 16), (end_l[0] + 14, end_l[1]), (end_l[0] - 16, end_l[1] + 6)], col,
               cross=top.get("style") in ("cardigan", "sweater"))
    seed(_h(base) + 401)
    s += spoly([(shr[0] - 16, shr[1] - 16), (shr[0] + 20, shr[1] - 12), (end_r[0] + 16, end_r[1] + 6), (end_r[0] - 14, end_r[1])], col,
               cross=top.get("style") in ("cardigan", "sweater"))
    s += D.hand(*hl, skin=skin) + D.hand(*hr, skin=skin, point=st.get("point"))
    s += "</g>"
    return s
