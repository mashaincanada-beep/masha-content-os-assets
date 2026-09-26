"""MIC Study Childhood Stories - scene kit.

Helpers that return SVG snippets for sets (backgrounds) and props.  World
coordinates: the default camera shows x 0..1080, y 0..1920.  Sets are drawn
a little larger (about -220..1300 x -240..2160) so the camera can pan/zoom.

Every function returns a string; compose them freely and add hand-written
SVG for anything a story needs that is not here.  Keep the storybook look:
flat shapes, soft gradients, gentle shadows, warm palette, no photos, no
realistic people.
"""
import math, random

X0, X1, Y0, Y1 = -240, 1320, -260, 2180   # drawable extent for sets
_uid = [0]


def uid(prefix="u"):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if f < 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    return "#%02X%02X%02X" % (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def grad(c1, c2, vertical=True):
    i = uid("g")
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    return i, (f'<defs><linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
               f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>')


def radial(c1, c2, o1=1, o2=0):
    i = uid("r")
    return i, (f'<defs><radialGradient id="{i}"><stop offset="0" stop-color="{c1}" stop-opacity="{o1}"/>'
               f'<stop offset="1" stop-color="{c2}" stop-opacity="{o2}"/></radialGradient></defs>')


def blur(sd):
    i = uid("f")
    return i, f'<defs><filter id="{i}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{sd}"/></filter></defs>'


def text(x, y, s, size=40, color="#2B2230", font="Nunito", weight=800, anchor="middle", rot=0, italic=False, opacity=1):
    st = "font-style:italic;" if italic else ""
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-weight="{weight}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" style="{st}" opacity="{opacity}"{tr}>{s}</text>')


# ================================================================ interiors
def wall(color="#F7E3C8", color2=None, floor_y=1300, pattern=None, pcolor=None):
    color2 = color2 or shade(color, 0.93)
    gi, gd = grad(shade(color, 1.05), color2)
    out = gd + f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{floor_y - Y0}" fill="url(#{gi})"/>'
    pc = pcolor or shade(color, 0.94)
    if pattern == "stripes":
        out += "".join(f'<rect x="{x}" y="{Y0}" width="34" height="{floor_y - Y0}" fill="{pc}" opacity=".55"/>' for x in range(X0, X1, 110))
    elif pattern == "dots":
        out += "".join(f'<circle cx="{x + (55 if (y // 110) % 2 else 0)}" cy="{y}" r="7" fill="{pc}" opacity=".6"/>'
                       for x in range(X0, X1, 110) for y in range(Y0 + 40, floor_y - 60, 110))
    elif pattern == "wainscot":
        out += (f'<rect x="{X0}" y="{floor_y - 420}" width="{X1 - X0}" height="420" fill="{pc}"/>'
                f'<rect x="{X0}" y="{floor_y - 430}" width="{X1 - X0}" height="18" fill="{shade(pc, 0.9)}"/>'
                + "".join(f'<rect x="{x}" y="{floor_y - 380}" width="150" height="320" rx="8" fill="none" stroke="{shade(pc, 0.9)}" stroke-width="6"/>' for x in range(X0 + 30, X1, 200)))
    out += f'<rect x="{X0}" y="{floor_y - 26}" width="{X1 - X0}" height="30" fill="{shade(color2, 0.82)}"/>'
    return out


def floor(y=1300, color="#C99A6B", kind="wood"):
    gi, gd = grad(shade(color, 0.92), shade(color, 1.06))
    out = gd + f'<rect x="{X0}" y="{y}" width="{X1 - X0}" height="{Y1 - y}" fill="url(#{gi})"/>'
    if kind == "wood":
        for i, yy in enumerate(range(y + 40, Y1, 70)):
            out += f'<rect x="{X0}" y="{yy}" width="{X1 - X0}" height="4" fill="{shade(color, 0.85)}" opacity=".5"/>'
            off = (i * 173) % 400
            out += "".join(f'<rect x="{x}" y="{yy - 66}" width="4" height="66" fill="{shade(color, 0.85)}" opacity=".35"/>' for x in range(X0 + off, X1, 400))
    elif kind == "tile":
        for yy in range(y, Y1, 110):
            out += f'<rect x="{X0}" y="{yy}" width="{X1 - X0}" height="4" fill="{shade(color, 0.86)}" opacity=".6"/>'
        for x in range(X0, X1, 110):
            out += f'<rect x="{x}" y="{y}" width="4" height="{Y1 - y}" fill="{shade(color, 0.86)}" opacity=".6"/>'
    elif kind == "carpet":
        out += "".join(f'<circle cx="{random.Random(k).randint(X0, X1)}" cy="{random.Random(k + 999).randint(y, Y1)}" r="3" fill="{shade(color, 0.9)}"/>' for k in range(160))
    return out


def window(x, y, w=300, h=380, sky="day", curtain="#F2A5B8", frame="#FFFFFF", beam=True):
    skies = {"day": ("#9FD3F7", "#DFF2FF"), "golden": ("#FFC98B", "#FFE9C4"), "dusk": ("#8B7BD1", "#F7B0A5"),
             "night": ("#1F2A55", "#3E4C85"), "morning": ("#BDE3F7", "#FFF1D6")}
    c1, c2 = skies.get(sky, skies["day"])
    gi, gd = grad(c1, c2)
    out = gd
    if beam and sky in ("day", "golden", "morning"):
        out += (f'<path d="M{x},{y + h} L{x + w},{y + h} L{x + w + 260},{y + h + 900} L{x + 120},{y + h + 900}Z" '
                f'fill="#FFF7DA" opacity=".18"/>')
    out += f'<rect x="{x - 18}" y="{y - 18}" width="{w + 36}" height="{h + 36}" rx="10" fill="{shade(frame, 0.92)}"/>'
    out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{gi})"/>'
    if sky in ("day", "morning", "golden"):
        out += f'<ellipse cx="{x + w * 0.3}" cy="{y + h * 0.3}" rx="{w * 0.2}" ry="{h * 0.06}" fill="#fff" opacity=".8"/>'
        out += f'<path d="M{x},{y + h * 0.82} Q{x + w * 0.35},{y + h * 0.66} {x + w * 0.7},{y + h * 0.78} T{x + w},{y + h * 0.72} L{x + w},{y + h} L{x},{y + h}Z" fill="#7CC47A" opacity=".85"/>'
    if sky == "night":
        out += f'<circle cx="{x + w * 0.7}" cy="{y + h * 0.3}" r="{w * 0.1}" fill="#FFF3C4"/>'
        out += "".join(f'<circle cx="{x + w * a}" cy="{y + h * b}" r="3" fill="#fff" opacity=".8"/>' for a, b in ((.2, .2), (.4, .45), (.15, .6), (.85, .55), (.55, .15)))
    out += f'<rect x="{x + w / 2 - 7}" y="{y}" width="14" height="{h}" fill="{frame}"/><rect x="{x}" y="{y + h / 2 - 7}" width="{w}" height="14" fill="{frame}"/>'
    out += f'<rect x="{x - 40}" y="{y + h + 14}" width="{w + 80}" height="22" rx="6" fill="{shade(frame, 0.88)}"/>'
    if curtain:
        for s in (0, 1):
            cx = x - 60 if s == 0 else x + w - 20
            out += (f'<path d="M{cx},{y - 50} L{cx + 80},{y - 50} Q{cx + (70 if s == 0 else 10)},{y + h * 0.6} {cx + (95 if s == 0 else -15)},{y + h + 40} '
                    f'L{cx + (10 if s == 0 else 55)},{y + h + 40} Q{cx - 5},{y + h * 0.5} {cx},{y - 50}Z" fill="{curtain}"/>')
        out += f'<rect x="{x - 90}" y="{y - 64}" width="{w + 180}" height="16" rx="8" fill="{shade(curtain, 0.7)}"/>'
    return out


def door(x, y, w=220, h=520, color="#B9855C"):
    return (f'<rect x="{x - 14}" y="{y - 14}" width="{w + 28}" height="{h + 14}" rx="6" fill="{shade(color, 0.8)}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{color}"/>'
            f'<rect x="{x + 28}" y="{y + 30}" width="{w - 56}" height="{h * 0.36}" rx="8" fill="none" stroke="{shade(color, 0.85)}" stroke-width="6"/>'
            f'<rect x="{x + 28}" y="{y + h * 0.48}" width="{w - 56}" height="{h * 0.42}" rx="8" fill="none" stroke="{shade(color, 0.85)}" stroke-width="6"/>'
            f'<circle cx="{x + w - 34}" cy="{y + h * 0.5}" r="11" fill="#F2C14E"/>')


def picture(x, y, w=160, h=130, art="#8FC1E8", frame="#8A5A44", kind="landscape"):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{frame}"/><rect x="{x + 12}" y="{y + 12}" width="{w - 24}" height="{h - 24}" fill="{art}"/>'
    if kind == "landscape":
        out += f'<path d="M{x + 12},{y + h - 12} L{x + w * 0.4},{y + h * 0.45} L{x + w * 0.6},{y + h * 0.7} L{x + w * 0.75},{y + h * 0.5} L{x + w - 12},{y + h - 12}Z" fill="#5FB36A"/><circle cx="{x + w * 0.72}" cy="{y + h * 0.3}" r="{h * 0.1}" fill="#FFD166"/>'
    elif kind == "drawing":  # child's crayon drawing
        out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFDF7" transform="rotate(-3 {x} {y})"/>'
        out += f'<g transform="rotate(-3 {x} {y})"><circle cx="{x + w * 0.25}" cy="{y + h * 0.3}" r="{h * 0.12}" fill="none" stroke="#FFB020" stroke-width="5"/><path d="M{x + w * 0.2},{y + h * 0.85} L{x + w * 0.45},{y + h * 0.45} L{x + w * 0.7},{y + h * 0.85}Z" fill="none" stroke="#FE007A" stroke-width="5"/><rect x="{x + w * 0.55}" y="{y + h * 0.55}" width="{w * 0.3}" height="{h * 0.3}" fill="none" stroke="#1C8FFF" stroke-width="5"/></g>'
    return out


def clock(x, y, r=60, face="#FFFFFF", rim="#E4513C", h=3, m=0):
    ha, ma = math.radians((h % 12 + m / 60) * 30), math.radians(m * 6)
    return (f'<circle cx="{x}" cy="{y}" r="{r + 10}" fill="{rim}"/><circle cx="{x}" cy="{y}" r="{r}" fill="{face}"/>'
            + "".join(f'<circle cx="{x + math.sin(math.radians(a)) * r * 0.8:.1f}" cy="{y - math.cos(math.radians(a)) * r * 0.8:.1f}" r="4" fill="#2B2230"/>' for a in range(0, 360, 30))
            + f'<line x1="{x}" y1="{y}" x2="{x + math.sin(ha) * r * 0.5:.1f}" y2="{y - math.cos(ha) * r * 0.5:.1f}" stroke="#2B2230" stroke-width="7" stroke-linecap="round"/>'
            f'<line x1="{x}" y1="{y}" x2="{x + math.sin(ma) * r * 0.75:.1f}" y2="{y - math.cos(ma) * r * 0.75:.1f}" stroke="#2B2230" stroke-width="4" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="6" fill="#2B2230"/>')


def shelf(x, y, w=360, rows=3, row_h=130, wood="#A8744F", seed=1):
    rnd = random.Random(seed)
    cols = ["#E4513C", "#1C8FFF", "#5FE223", "#FFB020", "#FE007A", "#7C5CBF", "#2BB3A3", "#F4A259", "#FFFFFF"]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{rows * row_h + 20}" rx="6" fill="{shade(wood, 0.75)}"/>'
    for r in range(rows):
        by = y + (r + 1) * row_h
        bx = x + 16
        while bx < x + w - 40:
            bw = rnd.randint(18, 34)
            bh = rnd.randint(int(row_h * 0.55), int(row_h * 0.85))
            if rnd.random() < 0.12:
                out += f'<rect x="{bx}" y="{by - bh * 0.7}" width="{bh * 0.7}" height="{bh * 0.7}" rx="4" fill="{rnd.choice(cols)}" opacity=".9"/>'
                bx += bh * 0.7 + 6
                continue
            c = rnd.choice(cols)
            out += f'<rect x="{bx}" y="{by - bh}" width="{bw}" height="{bh}" rx="3" fill="{c}"/><rect x="{bx + 3}" y="{by - bh * 0.7}" width="{bw - 6}" height="5" fill="#fff" opacity=".45"/>'
            bx += bw + 3
        out += f'<rect x="{x}" y="{by}" width="{w}" height="18" fill="{wood}"/>'
    return out


def plant(x, y, s=1.0, pot="#E98A6B", leaf="#4FA36B"):
    out = ""
    for a in (-50, -25, 0, 25, 50, -65, 65):
        rad = math.radians(a)
        lx, ly = x + math.sin(rad) * 110 * s, y - 60 * s - math.cos(rad) * 130 * s
        out += f'<path d="M{x},{y - 50 * s} Q{(x + lx) / 2 - 30 * s * math.cos(rad)},{(y + ly) / 2} {lx:.1f},{ly:.1f} Q{(x + lx) / 2 + 30 * s * math.cos(rad)},{(y + ly) / 2 + 20 * s} {x},{y - 50 * s}Z" fill="{leaf if a % 50 else shade(leaf, 1.15)}"/>'
    out += f'<path d="M{x - 60 * s},{y - 70 * s} L{x + 60 * s},{y - 70 * s} L{x + 45 * s},{y} L{x - 45 * s},{y}Z" fill="{pot}"/><rect x="{x - 66 * s}" y="{y - 82 * s}" width="{132 * s}" height="{20 * s}" rx="6" fill="{shade(pot, 0.88)}"/>'
    return out


def lamp(x, y, s=1.0, shade_col="#FFE0A3", on=True):
    out = ""
    if on:
        ri, rd = radial("#FFE9B0", "#FFE9B0", 0.55, 0)
        out += rd + f'<circle cx="{x}" cy="{y - 330 * s}" r="{260 * s}" fill="url(#{ri})"/>'
    out += (f'<rect x="{x - 6 * s}" y="{y - 320 * s}" width="{12 * s}" height="{300 * s}" fill="#6B5B4B"/>'
            f'<ellipse cx="{x}" cy="{y - 10 * s}" rx="{70 * s}" ry="{18 * s}" fill="#6B5B4B"/>'
            f'<path d="M{x - 90 * s},{y - 300 * s} L{x + 90 * s},{y - 300 * s} L{x + 60 * s},{y - 420 * s} L{x - 60 * s},{y - 420 * s}Z" fill="{shade_col}"/>')
    return out


def rug(cx, cy, rx=420, ry=90, color="#E98A6B", stripe="#FFF3E6"):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx * 0.8}" ry="{ry * 0.7}" fill="none" stroke="{stripe}" stroke-width="8" opacity=".7"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx * 0.55}" ry="{ry * 0.45}" fill="none" stroke="{stripe}" stroke-width="6" opacity=".5"/>')


def table(x, y, w=620, top="#C98B5A", h=34, legs=True, leg_h=330, cloth=None):
    """Table whose top surface front edge is at y (x = left edge).  Put it in
    the NEAR layer (or after actors) when characters stand behind it."""
    out = ""
    if legs:
        for lx in (x + 30, x + w - 60):
            out += f'<rect x="{lx}" y="{y + h - 4}" width="30" height="{leg_h}" rx="6" fill="{shade(top, 0.75)}"/>'
    out += f'<rect x="{x}" y="{y - 26}" width="{w}" height="30" rx="8" fill="{shade(top, 1.08)}"/>'
    out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{top}"/>'
    if cloth:
        out += f'<path d="M{x - 10},{y - 22} L{x + w + 10},{y - 22} L{x + w + 20},{y + 120} Q{x + w / 2},{y + 140} {x - 20},{y + 120}Z" fill="{cloth}"/>'
        out += "".join(f'<rect x="{xx}" y="{y - 22}" width="26" height="140" fill="#fff" opacity=".35"/>' for xx in range(int(x), int(x + w), 70))
    return out


def chair(x, y, color="#E4513C", s=1.0, back=True):
    """Simple chair seen from the front; seat at y."""
    out = ""
    if back:
        out += f'<rect x="{x - 90 * s}" y="{y - 250 * s}" width="{180 * s}" height="{230 * s}" rx="{22 * s}" fill="{shade(color, 0.85)}"/>'
    out += (f'<rect x="{x - 100 * s}" y="{y - 20 * s}" width="{200 * s}" height="{36 * s}" rx="{10 * s}" fill="{color}"/>'
            f'<rect x="{x - 90 * s}" y="{y + 16 * s}" width="{18 * s}" height="{190 * s}" fill="{shade(color, 0.7)}"/>'
            f'<rect x="{x + 72 * s}" y="{y + 16 * s}" width="{18 * s}" height="{190 * s}" fill="{shade(color, 0.7)}"/>')
    return out


def counter(x, y, w=900, top="#EDE6DA", cab="#7FB7A4", h=360):
    """Kitchen counter whose top is at y."""
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{cab}"/>'
    n = max(2, int(w // 220))
    cw = w / n
    for i in range(n):
        out += f'<rect x="{x + i * cw + 14}" y="{y + 40}" width="{cw - 28}" height="{h - 60}" rx="8" fill="{shade(cab, 1.08)}"/>'
        out += f'<rect x="{x + i * cw + cw / 2 - 30}" y="{y + 70}" width="60" height="10" rx="5" fill="{shade(cab, 0.7)}"/>'
    out += f'<rect x="{x - 12}" y="{y - 20}" width="{w + 24}" height="34" rx="6" fill="{top}"/>'
    return out


def upper_cabinets(x, y, w=900, h=260, cab="#9FCBBE"):
    n = max(2, int(w // 220))
    cw = w / n
    out = ""
    for i in range(n):
        out += f'<rect x="{x + i * cw + 6}" y="{y}" width="{cw - 12}" height="{h}" rx="8" fill="{cab}"/>'
        out += f'<rect x="{x + i * cw + cw / 2 - 5}" y="{y + h - 60}" width="10" height="40" rx="5" fill="{shade(cab, 0.7)}"/>'
    return out


def fridge(x, y, w=260, h=720, color="#F4F7FA"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{color}"/>'
            f'<rect x="{x}" y="{y + h * 0.36}" width="{w}" height="8" fill="{shade(color, 0.85)}"/>'
            f'<rect x="{x + w - 40}" y="{y + 60}" width="12" height="120" rx="6" fill="{shade(color, 0.7)}"/>'
            f'<rect x="{x + w - 40}" y="{y + h * 0.42}" width="12" height="160" rx="6" fill="{shade(color, 0.7)}"/>'
            f'<rect x="{x + 36}" y="{y + 90}" width="90" height="70" fill="#FFF3C4" transform="rotate(-6 {x + 80} {y + 120})"/>'
            f'<circle cx="{x + 80}" cy="{y + 92}" r="8" fill="#FE007A"/>')


def stove(x, y, w=300, color="#E7E2DA"):
    return (f'<rect x="{x}" y="{y - 16}" width="{w}" height="16" fill="#3B3B45"/>'
            + "".join(f'<ellipse cx="{x + w * a}" cy="{y - 18}" rx="{w * 0.16}" ry="10" fill="#2B2B33"/>' for a in (0.28, 0.72)))


def pot(x, y, s=1.0, color="#E4513C", steam=True):
    out = (f'<rect x="{x - 90 * s}" y="{y - 110 * s}" width="{180 * s}" height="{110 * s}" rx="{18 * s}" fill="{color}"/>'
           f'<rect x="{x - 100 * s}" y="{y - 124 * s}" width="{200 * s}" height="{22 * s}" rx="{10 * s}" fill="{shade(color, 0.8)}"/>'
           f'<rect x="{x - 130 * s}" y="{y - 90 * s}" width="{40 * s}" height="{14 * s}" rx="{7 * s}" fill="{shade(color, 0.7)}"/>')
    if steam:
        out += "".join(f'<path class="steam" d="M{x + d * s},{y - 140 * s} q{-20 * s},{-40 * s} 0,{-80 * s} t0,{-80 * s}" stroke="#FFFFFF" stroke-width="{10 * s}" fill="none" stroke-linecap="round" opacity=".5"/>' for d in (-40, 10, 55))
    return out


def bed(x, y, w=620, blanket="#8FB8F0", frame="#B9855C", pillow="#FFFFFF"):
    """Bed seen from the side-front; mattress top at y."""
    return (f'<rect x="{x - 20}" y="{y - 280}" width="46" height="480" rx="14" fill="{frame}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="150" rx="16" fill="{shade(frame, 0.9)}"/>'
            f'<rect x="{x}" y="{y - 40}" width="{w}" height="80" rx="30" fill="#F7F3EA"/>'
            f'<ellipse cx="{x + 130}" cy="{y - 55}" rx="110" ry="45" fill="{pillow}"/>'
            f'<path d="M{x + 220},{y - 60} Q{x + w / 2},{y - 110} {x + w},{y - 60} L{x + w + 20},{y + 110} L{x + 200},{y + 110}Z" fill="{blanket}"/>'
            + "".join(f'<circle cx="{x + 260 + i * 80}" cy="{y + 20 + (i % 2) * 35}" r="10" fill="#fff" opacity=".6"/>' for i in range(int((w - 260) // 80))))


def chalkboard(x, y, w=720, h=380, lines=(), color="#2F5D50", chalk="#F5F5F0", size=46):
    out = (f'<rect x="{x - 20}" y="{y - 20}" width="{w + 40}" height="{h + 40}" rx="10" fill="#A8744F"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'
           f'<rect x="{x + 30}" y="{y + h + 10}" width="{w - 60}" height="16" rx="6" fill="#8A5A3C"/>')
    for i, ln in enumerate(lines):
        out += text(x + 50, y + 80 + i * (size * 1.35), ln, size, chalk, "Nunito", 700, "start", opacity=.9)
    return out


def bulletin(x, y, w=300, h=240, seed=3):
    rnd = random.Random(seed)
    cols = ["#FFF3C4", "#FFD6E7", "#D6F0FF", "#DFF7D6", "#FFFFFF"]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#C99A6B"/><rect x="{x + 10}" y="{y + 10}" width="{w - 20}" height="{h - 20}" fill="#D9B081"/>'
    for i in range(6):
        px, py = x + 20 + (i % 3) * (w - 40) / 3, y + 20 + (i // 3) * (h - 40) / 2
        out += f'<rect x="{px}" y="{py}" width="{(w - 60) / 3}" height="{(h - 60) / 2}" fill="{rnd.choice(cols)}" transform="rotate({rnd.randint(-6, 6)} {px} {py})"/>'
        out += f'<circle cx="{px + (w - 60) / 6}" cy="{py + 6}" r="5" fill="{rnd.choice(["#E4513C", "#1C8FFF", "#5FE223"])}"/>'
    return out


def school_desk(x, y, top="#E9C891", metal="#6E7B8B", s=1.0):
    """Student desk seen from the front; top at y. Put in NEAR layer."""
    return (f'<rect x="{x - 150 * s}" y="{y}" width="{300 * s}" height="{26 * s}" rx="{6 * s}" fill="{top}"/>'
            f'<rect x="{x - 150 * s}" y="{y + 24 * s}" width="{300 * s}" height="{60 * s}" rx="{4 * s}" fill="{shade(top, 0.82)}"/>'
            f'<rect x="{x - 130 * s}" y="{y + 84 * s}" width="{14 * s}" height="{170 * s}" fill="{metal}"/>'
            f'<rect x="{x + 116 * s}" y="{y + 84 * s}" width="{14 * s}" height="{170 * s}" fill="{metal}"/>')


def banner(x, y, w, letters="ABCDEFG", colors=("#1C8FFF", "#5FE223", "#FE007A", "#FFB020")):
    n = len(letters)
    out = f'<path d="M{x},{y} Q{x + w / 2},{y + 60} {x + w},{y}" stroke="#8A5A44" stroke-width="4" fill="none"/>'
    for i, ch in enumerate(letters):
        t = (i + 0.5) / n
        px = x + w * t
        py = y + 60 * 4 * t * (1 - t) * 0.5 + 6
        out += f'<path d="M{px - 34},{py} L{px + 34},{py} L{px},{py + 80}Z" fill="{colors[i % len(colors)]}"/>'
        out += text(px, py + 40, ch, 34, "#FFFFFF", "Nunito", 900)
    return out


# ================================================================ exteriors
def sky(kind="day", horizon=1100):
    k = {"day": ("#8CCBF5", "#E6F5FF"), "golden": ("#F9B872", "#FFE8C2"), "dusk": ("#6C5BB8", "#F5A99A"),
         "night": ("#141B3D", "#34427A"), "morning": ("#A8D8F2", "#FFF0D2"), "overcast": ("#AFC0CF", "#E4EAF0")}
    c1, c2 = k.get(kind, k["day"])
    gi, gd = grad(c1, c2)
    out = gd + f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{horizon - Y0 + 40}" fill="url(#{gi})"/>'
    if kind in ("day", "golden", "morning"):
        ri, rd = radial("#FFF6D0", "#FFF6D0", 0.9, 0)
        out += rd + f'<circle cx="860" cy="220" r="260" fill="url(#{ri})"/><circle cx="860" cy="220" r="80" fill="#FFF3B8"/>'
    if kind == "night":
        out += f'<circle cx="820" cy="260" r="70" fill="#FFF3C4"/><circle cx="845" cy="245" r="62" fill="#1B2350"/>'
        out += "".join(f'<circle cx="{random.Random(i).randint(X0, X1)}" cy="{random.Random(i + 50).randint(Y0, horizon - 200)}" r="{random.Random(i + 9).choice([2, 3, 4])}" fill="#fff" opacity=".8"/>' for i in range(70))
    return out


def cloud(x, y, s=1.0, color="#FFFFFF", opacity=0.95):
    return (f'<g opacity="{opacity}"><ellipse cx="{x}" cy="{y}" rx="{120 * s}" ry="{50 * s}" fill="{color}"/>'
            f'<circle cx="{x - 50 * s}" cy="{y - 30 * s}" r="{55 * s}" fill="{color}"/><circle cx="{x + 30 * s}" cy="{y - 45 * s}" r="{70 * s}" fill="{color}"/></g>')


def hills(y=1100, color="#8CCB7E", color2=None, seed=2):
    color2 = color2 or shade(color, 0.88)
    return (f'<path d="M{X0},{y} Q{X0 + 300},{y - 200} {X0 + 700},{y - 60} T{X1},{y - 120} L{X1},{Y1} L{X0},{Y1}Z" fill="{shade(color, 1.1)}" opacity=".85"/>'
            f'<path d="M{X0},{y + 80} Q{X0 + 500},{y - 90} {X0 + 1000},{y + 40} T{X1},{y} L{X1},{Y1} L{X0},{Y1}Z" fill="{color}"/>')


def ground(y=1300, color="#7CC46A", kind="grass"):
    gi, gd = grad(shade(color, 1.05), shade(color, 0.9))
    out = gd + f'<rect x="{X0}" y="{y}" width="{X1 - X0}" height="{Y1 - y}" fill="url(#{gi})"/>'
    if kind == "grass":
        rnd = random.Random(7)
        for _ in range(140):
            gx, gy = rnd.randint(X0, X1), rnd.randint(y + 20, Y1)
            out += f'<path d="M{gx},{gy} l-6,-18 M{gx},{gy} l0,-22 M{gx},{gy} l7,-17" stroke="{shade(color, 0.8)}" stroke-width="3" stroke-linecap="round"/>'
    elif kind == "sidewalk":
        out = f'<rect x="{X0}" y="{y}" width="{X1 - X0}" height="{Y1 - y}" fill="#D8D2C8"/>' + "".join(
            f'<rect x="{x}" y="{y}" width="5" height="{Y1 - y}" fill="#C4BDB2"/>' for x in range(X0, X1, 260))
    return out


def tree(x, y, s=1.0, leaf="#5FAE5B", trunk="#8A5A3C", kind="round"):
    out = f'<path d="M{x - 26 * s},{y} L{x - 18 * s},{y - 300 * s} L{x + 18 * s},{y - 300 * s} L{x + 26 * s},{y}Z" fill="{trunk}"/>'
    if kind == "round":
        for dx, dy, r in ((0, -420, 170), (-120, -330, 120), (120, -330, 125), (-60, -520, 110), (80, -500, 120)):
            out += f'<circle cx="{x + dx * s}" cy="{y + dy * s}" r="{r * s}" fill="{leaf if dy < -400 else shade(leaf, 0.9)}"/>'
    else:  # pine
        for i in range(3):
            out += f'<path d="M{x - (170 - i * 40) * s},{y - (220 + i * 150) * s} L{x},{y - (470 + i * 150) * s} L{x + (170 - i * 40) * s},{y - (220 + i * 150) * s}Z" fill="{shade(leaf, 0.9 + i * 0.05)}"/>'
    return out


def bush(x, y, s=1.0, color="#5FAE5B", flowers=None):
    out = "".join(f'<circle cx="{x + dx * s}" cy="{y - dy * s}" r="{r * s}" fill="{shade(color, f)}"/>'
                  for dx, dy, r, f in ((-70, 50, 70, 0.9), (60, 50, 75, 0.92), (0, 90, 90, 1.0)))
    if flowers:
        out += "".join(f'<circle cx="{x + dx * s}" cy="{y - dy * s}" r="{10 * s}" fill="{flowers}"/>' for dx, dy in ((-60, 90), (-10, 150), (50, 110), (80, 60), (-90, 40)))
    return out


def fence(y=1250, color="#FFFFFF"):
    out = f'<rect x="{X0}" y="{y - 150}" width="{X1 - X0}" height="18" fill="{shade(color, 0.9)}"/><rect x="{X0}" y="{y - 70}" width="{X1 - X0}" height="18" fill="{shade(color, 0.9)}"/>'
    out += "".join(f'<path d="M{x},{y} L{x},{y - 200} L{x + 22},{y - 225} L{x + 44},{y - 200} L{x + 44},{y}Z" fill="{color}"/>' for x in range(X0, X1, 80))
    return out


def house(x, y, s=1.0, wall_c="#F6D6A8", roof="#D9644A", door_c="#1C8FFF"):
    return (f'<rect x="{x - 200 * s}" y="{y - 300 * s}" width="{400 * s}" height="{300 * s}" fill="{wall_c}"/>'
            f'<path d="M{x - 240 * s},{y - 290 * s} L{x},{y - 480 * s} L{x + 240 * s},{y - 290 * s}Z" fill="{roof}"/>'
            f'<rect x="{x - 40 * s}" y="{y - 150 * s}" width="{80 * s}" height="{150 * s}" rx="{6 * s}" fill="{door_c}"/>'
            f'<rect x="{x - 160 * s}" y="{y - 230 * s}" width="{90 * s}" height="{80 * s}" fill="#BFE3F7"/><rect x="{x + 70 * s}" y="{y - 230 * s}" width="{90 * s}" height="{80 * s}" fill="#BFE3F7"/>')


def goal(x, y, w=520, h=260):
    out = f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" fill="none" stroke="#FFFFFF" stroke-width="16"/>'
    out += "".join(f'<line x1="{x + i}" y1="{y - h}" x2="{x + i}" y2="{y}" stroke="#FFFFFF" stroke-width="2" opacity=".6"/>' for i in range(20, w, 30))
    out += "".join(f'<line x1="{x}" y1="{y - h + j}" x2="{x + w}" y2="{y - h + j}" stroke="#FFFFFF" stroke-width="2" opacity=".6"/>' for j in range(20, h, 30))
    return out


def scoreboard(x, y, w=420, h=220, left="HOME", right="GUEST", ls="0", rs="0"):
    return (f'<rect x="{x - 12}" y="{y - 12}" width="{w + 24}" height="{h + 24}" rx="14" fill="#3A3F4B"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#1E222B"/>'
            + text(x + w * 0.25, y + 50, left, 32, "#FFD166", "Nunito", 900) + text(x + w * 0.75, y + 50, right, 32, "#FFD166", "Nunito", 900)
            + f'<g id="score-l">{text(x + w * 0.25, y + 170, ls, 100, "#FFFFFF", "Nunito", 900)}</g>'
            + f'<g id="score-r">{text(x + w * 0.75, y + 170, rs, 100, "#FFFFFF", "Nunito", 900)}</g>')


def stage(floor_y=1350, curtain="#B83B5E", boards="#C99A6B"):
    out = f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{floor_y - Y0}" fill="#2A2238"/>'
    ri, rd = radial("#FFF1C8", "#FFF1C8", 0.55, 0)
    out += rd + f'<ellipse cx="540" cy="{floor_y - 60}" rx="520" ry="700" fill="url(#{ri})"/>'
    out += floor(floor_y, boards, "wood")
    for s in (0, 1):
        x = X0 if s == 0 else X1 - 380
        out += f'<path d="M{x},{Y0} L{x + 380},{Y0} Q{x + (330 if s == 0 else 50)},{floor_y * 0.6} {x + (360 if s == 0 else 20)},{floor_y + 40} L{x + (0 if s == 0 else 380)},{floor_y + 40}Z" fill="{curtain}"/>'
        out += "".join(f'<path d="M{x + k},{Y0} Q{x + k + 20},{floor_y * 0.5} {x + k - 10},{floor_y + 40}" stroke="{shade(curtain, 0.8)}" stroke-width="10" fill="none"/>' for k in range(40, 380, 70))
    out += f'<path d="M{X0},{Y0} L{X1},{Y0} L{X1},{Y0 + 260} Q540,{Y0 + 380} {X0},{Y0 + 260}Z" fill="{shade(curtain, 0.9)}"/>'
    return out


def audience(y=1900, n=9, seed=4):
    """Row of audience heads (silhouettes) for the NEAR layer."""
    rnd = random.Random(seed)
    out = ""
    for i in range(n):
        x = X0 + 60 + i * (X1 - X0 - 120) / (n - 1)
        r = rnd.randint(70, 95)
        c = rnd.choice(["#1E1A26", "#241E2E", "#2A2433"])
        out += f'<circle cx="{x}" cy="{y - r * 1.9}" r="{r}" fill="{c}"/><rect x="{x - r * 1.3}" y="{y - r}" width="{r * 2.6}" height="{r * 2}" rx="{r}" fill="{c}"/>'
    return out


def market_shelf(x, y, w=700, rows=3, row_h=170, seed=5):
    rnd = random.Random(seed)
    cols = ["#E4513C", "#FFB020", "#5FE223", "#1C8FFF", "#FE007A", "#F4A259", "#2BB3A3", "#FFFFFF"]
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{rows * row_h + 30}" fill="#E8E2D8"/>'
    for r in range(rows):
        by = y + (r + 1) * row_h
        bx = x + 20
        while bx < x + w - 90:
            kind = rnd.random()
            c = rnd.choice(cols)
            if kind < 0.4:
                out += f'<rect x="{bx}" y="{by - 110}" width="70" height="110" rx="8" fill="{c}"/><rect x="{bx + 10}" y="{by - 80}" width="50" height="34" rx="4" fill="#fff" opacity=".8"/>'
                bx += 80
            elif kind < 0.7:
                out += f'<rect x="{bx}" y="{by - 80}" width="54" height="80" rx="22" fill="{c}"/><rect x="{bx + 12}" y="{by - 100}" width="30" height="24" rx="6" fill="{shade(c, 0.8)}"/>'
                bx += 64
            else:
                out += "".join(f'<circle cx="{bx + 22 + i * 30}" cy="{by - 22 - (i % 2) * 26}" r="22" fill="{c}"/>' for i in range(3))
                bx += 110
        out += f'<rect x="{x}" y="{by}" width="{w}" height="22" fill="#BFB6A8"/>'
        out += f'<rect x="{x + 40}" y="{by + 2}" width="70" height="30" fill="#FFF3C4"/>' + text(x + 75, by + 26, "$" + str(rnd.randint(1, 9)) + "." + rnd.choice(["49", "99", "25", "75"]), 20, "#2B2230", "Nunito", 900)
    return out


def lemonade_stand(x, y, w=560, sign="LEMONADE", price="50¢", stripe="#FFD23F"):
    """Stand whose counter top is at y (x = centre). Put in NEAR layer."""
    l = x - w / 2
    out = (f'<rect x="{l}" y="{y}" width="{w}" height="360" fill="#F5E6C8"/>'
           + "".join(f'<rect x="{l + i}" y="{y}" width="40" height="360" fill="{stripe}" opacity=".85"/>' for i in range(0, int(w), 80))
           + f'<rect x="{l - 20}" y="{y - 24}" width="{w + 40}" height="36" rx="8" fill="#C98B5A"/>'
           f'<rect x="{l + 20}" y="{y + 80}" width="{w - 40}" height="120" rx="10" fill="#FFFFFF"/>'
           + text(x, y + 160, sign, 64, "#E4513C", "Fraunces", 900)
           + f'<rect x="{l + w - 170}" y="{y + 230}" width="140" height="80" rx="8" fill="#FFF3C4" transform="rotate(-5 {l + w - 100} {y + 270})"/>'
           + text(l + w - 100, y + 285, price, 42, "#2B2230", "Nunito", 900, rot=-5))
    return out


# ================================================================ lights & fx
def light_rays(x, y, w=500, h=1400, angle=18, color="#FFF6D6", opacity=0.22):
    return (f'<g transform="rotate({angle} {x} {y})" opacity="{opacity}">'
            + "".join(f'<path d="M{x + i},{y} L{x + i + 60},{y} L{x + i + 140},{y + h} L{x + i - 20},{y + h}Z" fill="{color}"/>' for i in range(0, w, 150)) + "</g>")


def bokeh(n=10, seed=1, colors=("#FFE9B0", "#FFD6E7", "#D6F0FF"), y0=1500, y1=2150, r0=40, r1=110, opacity=0.5):
    """Soft out-of-focus circles for the NEAR layer (foreground depth)."""
    fi, fd = blur(18)
    rnd = random.Random(seed)
    out = fd + f'<g filter="url(#{fi})" opacity="{opacity}">'
    for _ in range(n):
        out += f'<circle cx="{rnd.randint(X0, X1)}" cy="{rnd.randint(y0, y1)}" r="{rnd.randint(r0, r1)}" fill="{rnd.choice(colors)}"/>'
    return out + "</g>"


def fg_blur(svg, sd=10):
    """Wrap foreground elements in a soft blur (depth of field)."""
    fi, fd = blur(sd)
    return fd + f'<g filter="url(#{fi})">{svg}</g>'


def string_lights(y=200, color_seed=2):
    rnd = random.Random(color_seed)
    out = f'<path d="M{X0},{y} Q{X0 + 400},{y + 90} {540},{y + 20} T{X1},{y + 40}" stroke="#4A3F35" stroke-width="3" fill="none"/>'
    for i in range(22):
        t = i / 21
        x = X0 + (X1 - X0) * t
        yy = y + 40 + 35 * math.sin(t * math.pi * 2.2)
        c = rnd.choice(["#FFE08A", "#FFB3C7", "#A8E6FF", "#C2F2A0"])
        ri, rd = radial(c, c, 0.7, 0)
        out += rd + f'<circle cx="{x:.0f}" cy="{yy + 18:.0f}" r="34" fill="url(#{ri})"/><circle cx="{x:.0f}" cy="{yy + 18:.0f}" r="10" fill="{c}"/>'
    return out


# ================================================================ props
# Props are drawn centred on (0,0) and roughly 60-200 px in size; place them
# with {"svg": ..., "x":.., "y":..} or attach them to a hand.
def p_book(color="#1C8FFF", open_=False, w=150, title=None):
    if open_:
        return (f'<path d="M{-w},{-w * 0.55} Q{-w / 2},{-w * 0.68} 0,{-w * 0.52} Q{w / 2},{-w * 0.68} {w},{-w * 0.55} L{w},{w * 0.25} Q{w / 2},{w * 0.12} 0,{w * 0.28} Q{-w / 2},{w * 0.12} {-w},{w * 0.25}Z" fill="{color}"/>'
                f'<path d="M{-w * 0.93},{-w * 0.5} Q{-w / 2},{-w * 0.6} {-4},{-w * 0.46} L{-4},{w * 0.2} Q{-w / 2},{w * 0.07} {-w * 0.93},{w * 0.18}Z" fill="#FFFDF5"/>'
                f'<path d="M{w * 0.93},{-w * 0.5} Q{w / 2},{-w * 0.6} {4},{-w * 0.46} L{4},{w * 0.2} Q{w / 2},{w * 0.07} {w * 0.93},{w * 0.18}Z" fill="#FFFDF5"/>'
                + "".join(f'<rect x="{-w * 0.8}" y="{-w * 0.36 + i * w * 0.1}" width="{w * 0.65}" height="{w * 0.025}" rx="2" fill="#B8B0A4"/><rect x="{w * 0.15}" y="{-w * 0.36 + i * w * 0.1}" width="{w * 0.65}" height="{w * 0.025}" rx="2" fill="#B8B0A4"/>' for i in range(5)))
    out = (f'<rect x="{-w * 0.5}" y="{-w * 0.65}" width="{w}" height="{w * 1.3}" rx="8" fill="{color}"/>'
           f'<rect x="{-w * 0.5}" y="{-w * 0.65}" width="{w * 0.12}" height="{w * 1.3}" rx="4" fill="{shade(color, 0.8)}"/>'
           f'<rect x="{-w * 0.25}" y="{-w * 0.4}" width="{w * 0.6}" height="{w * 0.3}" rx="6" fill="#FFFFFF" opacity=".85"/>')
    if title:
        out += text(w * 0.05, -w * 0.2, title, w * 0.13, "#2B2230", "Nunito", 900)
    return out


def p_worksheet(w=170, color="#1C8FFF", kind="math"):
    """A MIC Study-style printable practice page (generic, no product text)."""
    h = w * 1.3
    out = (f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="4" fill="#FFFFFF" stroke="#E0DAD0" stroke-width="2"/>'
           f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h * 0.12}" fill="{color}"/>'
           f'<circle cx="{w * 0.33}" cy="{-h * 0.44}" r="{w * 0.05}" fill="#FFFFFF"/>')
    for i in range(5):
        yy = -h * 0.28 + i * h * 0.15
        if kind == "math":
            out += f'<rect x="{-w * 0.38}" y="{yy}" width="{w * 0.3}" height="{w * 0.05}" rx="2" fill="#9A93A6"/><rect x="{w * 0.05}" y="{yy - w * 0.02}" width="{w * 0.25}" height="{w * 0.09}" rx="3" fill="none" stroke="#C8C1D3" stroke-width="2"/>'
        else:
            out += f'<rect x="{-w * 0.38}" y="{yy}" width="{w * 0.76}" height="{w * 0.035}" rx="2" fill="#9A93A6"/><rect x="{-w * 0.38}" y="{yy + w * 0.06}" width="{w * 0.5}" height="{w * 0.035}" rx="2" fill="#C8C1D3"/>'
    out += f'<path d="M{w * 0.22},{h * 0.38} l{w * 0.05},{w * 0.05} l{w * 0.1},{-w * 0.1}" stroke="#5FE223" stroke-width="{w * 0.03}" fill="none" stroke-linecap="round"/>'
    return out


def p_pencil(l=150, color="#FFC83D"):
    return (f'<g transform="rotate(-35)"><rect x="{-l / 2}" y="-9" width="{l * 0.8}" height="18" fill="{color}"/>'
            f'<rect x="{-l / 2 - 16}" y="-9" width="16" height="18" rx="4" fill="#F28CA4"/><rect x="{-l / 2}" y="-9" width="10" height="18" fill="#C9C9C9"/>'
            f'<path d="M{l * 0.3},-9 L{l * 0.5},0 L{l * 0.3},9Z" fill="#F2D2A9"/><path d="M{l * 0.44},-3 L{l * 0.5},0 L{l * 0.44},3Z" fill="#2B2230"/></g>')


def p_cup(color="#FFE066", fill="#FFF3A6", w=60):
    return (f'<path d="M{-w / 2},{-w * 0.8} L{w / 2},{-w * 0.8} L{w * 0.4},{w * 0.5} L{-w * 0.4},{w * 0.5}Z" fill="{color}" opacity=".95"/>'
            f'<rect x="{-w * 0.46}" y="{-w * 0.7}" width="{w * 0.92}" height="{w * 0.18}" fill="{fill}"/>'
            f'<rect x="{-w * 0.3}" y="{-w * 0.55}" width="{w * 0.1}" height="{w * 0.9}" fill="#fff" opacity=".4"/>')


def p_pitcher(w=110, liquid="#FFF06A"):
    return (f'<path d="M{-w / 2},{-w} L{w / 2},{-w} L{w * 0.45},{w * 0.5} Q0,{w * 0.62} {-w * 0.45},{w * 0.5}Z" fill="#E8F6FF" opacity=".9"/>'
            f'<path d="M{-w * 0.46},{-w * 0.45} L{w * 0.46},{-w * 0.45} L{w * 0.42},{w * 0.48} Q0,{w * 0.58} {-w * 0.42},{w * 0.48}Z" fill="{liquid}"/>'
            f'<path d="M{w / 2},{-w * 0.8} Q{w * 0.95},{-w * 0.6} {w * 0.45},{w * 0.1}" stroke="#CFE4F2" stroke-width="{w * 0.1}" fill="none"/>'
            + "".join(f'<circle cx="{dx}" cy="{dy}" r="{w * 0.1}" fill="#FFE14D" stroke="#F2C230" stroke-width="3"/>' for dx, dy in ((-w * 0.2, -w * 0.25), (w * 0.15, -w * 0.05))))


def p_lemon(r=34):
    return f'<ellipse rx="{r * 1.25}" ry="{r}" fill="#FFE14D"/><ellipse cx="{-r * 0.35}" cy="{-r * 0.35}" rx="{r * 0.35}" ry="{r * 0.18}" fill="#fff" opacity=".6"/><circle cx="{r * 1.25}" r="{r * 0.18}" fill="#E6C12E"/>'


def p_coins(n=4, r=22):
    return "".join(f'<ellipse cx="{i * r * 0.9 - n * r * 0.4}" cy="{-i * 6}" rx="{r}" ry="{r * 0.55}" fill="#F2C230" stroke="#C99A1E" stroke-width="3"/>' for i in range(n))


def p_jar(w=90, label="$", coins=True):
    out = f'<rect x="{-w / 2}" y="{-w * 1.1}" width="{w}" height="{w * 1.2}" rx="{w * 0.2}" fill="#DFF3FF" opacity=".8"/>'
    if coins:
        out += "".join(f'<ellipse cx="{dx}" cy="{w * 0.0 - k * 10}" rx="{w * 0.18}" ry="{w * 0.08}" fill="#F2C230"/>' for k, dx in enumerate((-w * 0.2, w * 0.12, -w * 0.05, w * 0.2)))
    out += f'<rect x="{-w * 0.55}" y="{-w * 1.22}" width="{w * 1.1}" height="{w * 0.2}" rx="6" fill="#C98B5A"/><rect x="{-w * 0.3}" y="{-w * 0.75}" width="{w * 0.6}" height="{w * 0.35}" rx="4" fill="#FFFFFF"/>'
    out += text(0, -w * 0.47, label, w * 0.28, "#2B2230", "Nunito", 900)
    return out


def p_measuring_cup(w=90, label="1/2", color="#FE5C9D"):
    return (f'<path d="M{-w / 2},{-w * 0.6} L{w / 2},{-w * 0.6} L{w * 0.4},{w * 0.4} L{-w * 0.4},{w * 0.4}Z" fill="{color}"/>'
            f'<rect x="{w * 0.45}" y="{-w * 0.5}" width="{w * 0.7}" height="{w * 0.18}" rx="{w * 0.09}" fill="{color}"/>'
            + text(0, w * 0.05, label, w * 0.32, "#FFFFFF", "Nunito", 900))


def p_bowl(w=180, color="#8FC1E8", content="#F5E1B5"):
    return (f'<ellipse cx="0" cy="{-w * 0.25}" rx="{w / 2}" ry="{w * 0.12}" fill="{content}"/>'
            f'<path d="M{-w / 2},{-w * 0.25} Q0,{w * 0.45} {w / 2},{-w * 0.25}Z" fill="{color}"/>'
            f'<path d="M{-w * 0.3},{-w * 0.1} Q0,{w * 0.2} {w * 0.3},{-w * 0.1}" stroke="#fff" stroke-width="5" fill="none" opacity=".4"/>')


def p_cookie_tray(w=320):
    out = f'<rect x="{-w / 2}" y="{-w * 0.2}" width="{w}" height="{w * 0.4}" rx="10" fill="#B9C2CC"/><rect x="{-w / 2 + 10}" y="{-w * 0.2 + 10}" width="{w - 20}" height="{w * 0.4 - 20}" rx="6" fill="#CDD5DE"/>'
    for i in range(6):
        cx, cy = -w * 0.33 + (i % 3) * w * 0.33, -w * 0.07 + (i // 3) * w * 0.16
        out += f'<ellipse cx="{cx}" cy="{cy}" rx="{w * 0.1}" ry="{w * 0.065}" fill="#D9A15E"/>' + "".join(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="5" fill="#5A3A26"/>' for dx, dy in ((-10, -4), (8, 3), (0, -9)))
    return out


def p_ball(r=60, kind="soccer"):
    if kind == "soccer":
        return (f'<circle r="{r}" fill="#FFFFFF" stroke="#2B2230" stroke-width="4"/>'
                f'<path d="M0,{-r * 0.3} L{r * 0.28},{-r * 0.08} L{r * 0.18},{r * 0.25} L{-r * 0.18},{r * 0.25} L{-r * 0.28},{-r * 0.08}Z" fill="#2B2230"/>')
    return f'<circle r="{r}" fill="#F2803A"/><path d="M{-r},0 L{r},0 M0,{-r} L0,{r}" stroke="#2B2230" stroke-width="4"/>'


def p_card(w=160, color="#FFD6E7", title="YOU'RE INVITED!", lines=2):
    h = w * 0.7
    out = (f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="8" fill="{color}"/>'
           f'<rect x="{-w / 2 + 8}" y="{-h / 2 + 8}" width="{w - 16}" height="{h - 16}" rx="6" fill="none" stroke="#FFFFFF" stroke-width="3"/>'
           + text(0, -h * 0.18, title, w * 0.085, "#E4513C", "Nunito", 900))
    out += "".join(f'<rect x="{-w * 0.32}" y="{-h * 0.02 + i * h * 0.16}" width="{w * 0.64}" height="{w * 0.03}" rx="2" fill="#9A7A88"/>' for i in range(lines))
    return out


def p_clipboard(w=150, color="#C98B5A"):
    h = w * 1.35
    return (f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="10" fill="{color}"/>'
            f'<rect x="{-w * 0.42}" y="{-h * 0.42}" width="{w * 0.84}" height="{h * 0.86}" fill="#FFFFFF"/>'
            f'<rect x="{-w * 0.2}" y="{-h / 2 - 10}" width="{w * 0.4}" height="28" rx="8" fill="#9AA3AE"/>'
            + "".join(f'<rect x="{-w * 0.32}" y="{-h * 0.28 + i * h * 0.12}" width="{w * 0.64}" height="{w * 0.035}" rx="2" fill="#B8B0A4"/>' for i in range(6)))


def p_map(w=200):
    h = w * 0.7
    return (f'<path d="M{-w / 2},{-h / 2} L{-w / 6},{-h / 2 + 10} L{w / 6},{-h / 2} L{w / 2},{-h / 2 + 10} L{w / 2},{h / 2} L{w / 6},{h / 2 - 10} L{-w / 6},{h / 2} L{-w / 2},{h / 2 - 10}Z" fill="#FFF1C9" stroke="#D9B97A" stroke-width="3"/>'
            f'<path d="M{-w * 0.35},{h * 0.25} Q{-w * 0.1},{-h * 0.1} {w * 0.1},{h * 0.05} T{w * 0.33},{-h * 0.25}" stroke="#E4513C" stroke-width="5" stroke-dasharray="10 8" fill="none"/>'
            f'<path d="M{w * 0.3},{-h * 0.3} l14,14 m0,-14 l-14,14" stroke="#E4513C" stroke-width="6"/>')


def p_backpack(w=150, color="#FE5C9D"):
    return (f'<rect x="{-w / 2}" y="{-w * 0.65}" width="{w}" height="{w * 1.25}" rx="{w * 0.3}" fill="{color}"/>'
            f'<rect x="{-w * 0.35}" y="{w * 0.05}" width="{w * 0.7}" height="{w * 0.4}" rx="{w * 0.12}" fill="{shade(color, 0.85)}"/>'
            f'<path d="M{-w * 0.25},{-w * 0.65} Q0,{-w * 0.95} {w * 0.25},{-w * 0.65}" stroke="{shade(color, 0.7)}" stroke-width="10" fill="none"/>')


def p_speech(txt="?", w=110, color="#FFFFFF"):
    """Small thought/speech bubble with a symbol (use sparingly)."""
    return (f'<ellipse rx="{w / 2}" ry="{w * 0.38}" fill="{color}" stroke="#2B2230" stroke-width="3"/>'
            f'<circle cx="{-w * 0.35}" cy="{w * 0.48}" r="{w * 0.08}" fill="{color}" stroke="#2B2230" stroke-width="3"/>'
            + text(0, w * 0.16, txt, w * 0.45, "#2B2230", "Nunito", 900))


def p_sign(w=320, h=140, txt="", color="#FFFFFF", ink="#2B2230", post=True, size=48):
    out = ""
    if post:
        out += f'<rect x="-10" y="{h / 2}" width="20" height="{h * 1.6}" fill="#8A5A3C"/>'
    out += f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="12" fill="{color}" stroke="{shade(color, 0.8)}" stroke-width="5"/>'
    out += text(0, size * 0.35, txt, size, ink, "Nunito", 900)
    return out
