"""MIC Study Childhood Stories - character rig.

A character is drawn once as an SVG group with every expression variant
inside it; each frame the film renderer only switches variants on/off and
updates a few transforms and arm paths.  Origin (0,0) is the point between
the feet; y grows downward (so the head is at negative y).

Hands are simple mitten shapes on purpose: no fingers, so no malformed hands.
"""
import math

SKIN = {  # base, shade, blush
    "fair":  ("#F9DCC8", "#EDBFA5", "#F4978E"),
    "light": ("#F3CBAE", "#E2AE8D", "#EE8E85"),
    "olive": ("#DDAA80", "#C58D63", "#DE7F6E"),
    "tan":   ("#C98E62", "#AD744C", "#C9675A"),
    "brown": ("#A26A45", "#875536", "#B35A4B"),
    "deep":  ("#6E4430", "#583424", "#9A4A3E"),
}
INK = "#2B2230"


def _shade(hex_color, f):
    """Darken (f<1) or lighten (f>1) a hex colour."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if f < 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    return "#%02X%02X%02X" % (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


# ------------------------------------------------------------------ geometry
def geometry(spec):
    kind = spec.get("kind", "child")
    age = spec.get("age", 8)
    if kind == "adult":
        H = spec.get("height", 800 if spec.get("sex") == "m" else 760)
        headR = H * 0.108
        legL = H * 0.42
        torsoH = H * 0.31
        W = headR * 2.25
    else:
        H = spec.get("height", 400 + (min(max(age, 5), 15) - 5) * 26)
        t = (min(max(age, 5), 15) - 5) / 10.0      # 0 young .. 1 teen
        headR = H * (0.175 - 0.045 * t)
        legL = H * (0.30 + 0.07 * t)
        torsoH = H * (0.27 + 0.02 * t)
        W = headR * (1.45 + 0.45 * t)
    if spec.get("build") == "broad":
        W *= 1.12
    hipY = -legL
    shoulderY = hipY - torsoH
    headCY = shoulderY - headR * 0.92
    g = dict(H=H, headR=headR, legL=legL, torsoH=torsoH, W=W, hipW=W * 0.92,
             hipY=hipY, shoulderY=shoulderY, headCY=headCY,
             armW=max(H * 0.042, 13), legW=max(H * 0.07, 20),
             ua=torsoH * 0.55, fa=torsoH * 0.52)
    g["handR"] = g["armW"] * 0.68
    g["shoulderX"] = W / 2 - g["armW"] * 0.35
    g["shoulderYa"] = shoulderY + g["armW"] * 0.55
    return g


# arm poses: (upper-arm angle, forearm angle) in degrees; 0 = hanging down,
# +90 = straight out to the side, 180 = straight up, negative = across body.
ARM_POSES = {
    "down": (7, 3), "relaxed": (12, 6), "hold": (-6, -122), "hold_low": (-4, -62),
    "raise": (170, 176), "wave": (138, 162), "hip": (48, -92), "point": (84, 92),
    "reach": (58, 72), "chin": (-12, -158), "cross": (-12, -96), "shrug": (38, 112),
    "cheer": (152, 170), "chest": (-4, -142), "face": (-18, -170), "write": (-18, -104),
    "give": (28, 70), "hug": (70, -40), "tablet": (-10, -115),
    "counter": (32, 62), "rest": (6, -40), "thumbs": (40, 150), "open": (26, 40), "pocket": (4, -20),
}


def arm_geom(g, side, upper, fore, sleeve="short"):
    """Return (skin path d, sleeve path d, hand centre) for one arm.
    side = -1 for the character's left-of-screen arm, +1 for right."""
    sx, sy = side * g["shoulderX"], g["shoulderYa"]
    a1, a2 = math.radians(upper), math.radians(fore)
    ex, ey = sx + side * math.sin(a1) * g["ua"], sy + math.cos(a1) * g["ua"]
    hx, hy = ex + side * math.sin(a2) * g["fa"], ey + math.cos(a2) * g["fa"]
    skin = f"M{sx:.1f},{sy:.1f} L{ex:.1f},{ey:.1f} L{hx:.1f},{hy:.1f}"
    if sleeve == "long":
        wx, wy = ex + (hx - ex) * 0.86, ey + (hy - ey) * 0.86
        sl = f"M{sx:.1f},{sy:.1f} L{ex:.1f},{ey:.1f} L{wx:.1f},{wy:.1f}"
    elif sleeve == "none":
        sl = f"M{sx:.1f},{sy:.1f} L{sx:.1f},{sy:.1f}"
    else:
        mx, my = sx + (ex - sx) * 0.58, sy + (ey - sy) * 0.58
        sl = f"M{sx:.1f},{sy:.1f} L{mx:.1f},{my:.1f}"
    return skin, sl, (hx, hy)


# ------------------------------------------------------------------ face parts
def _eyes(p, g, c):
    R, cy = g["headR"], g["headCY"]
    ex, ey = R * 0.37, cy + R * 0.06
    rx, ry = R * 0.135, R * 0.19
    lash = c.get("lashes", False)
    out = []
    def both(fn):
        return "".join(fn(sgn * ex, sgn) for sgn in (-1, 1))
    def open_eye(x, s, k=1.0, yo=0):
        extra = ""
        if lash:
            extra = (f'<path d="M{x + s*rx*0.6:.1f},{ey - ry*0.75:.1f} l{s*rx*0.55:.1f},{-ry*0.3:.1f}" '
                     f'stroke="{INK}" stroke-width="{R*0.035:.1f}" stroke-linecap="round"/>')
        return (f'<ellipse cx="{x:.1f}" cy="{ey+yo:.1f}" rx="{rx*k:.1f}" ry="{ry*k:.1f}" fill="{INK}"/>'
                f'<circle cx="{x + rx*0.35*k:.1f}" cy="{ey + yo - ry*0.38*k:.1f}" r="{rx*0.38*k:.1f}" fill="#fff"/>'
                f'<circle cx="{x - rx*0.3*k:.1f}" cy="{ey + yo + ry*0.35*k:.1f}" r="{rx*0.16*k:.1f}" fill="#fff" opacity=".7"/>'
                + extra)
    sw = R * 0.055
    out.append(f'<g id="{p}eye-open">{both(lambda x, s: open_eye(x, s))}</g>')
    out.append(f'<g id="{p}eye-wide" style="display:none">{both(lambda x, s: open_eye(x, s, 1.22, -R*0.02))}</g>')
    half = lambda x, s: (open_eye(x, s, 0.95, R * 0.03) +
                         f'<path d="M{x - rx*1.25:.1f},{ey - ry*0.05:.1f} Q{x:.1f},{ey - ry*0.35:.1f} {x + rx*1.25:.1f},{ey - ry*0.05:.1f} L{x + rx*1.3:.1f},{ey - ry*1.3:.1f} L{x - rx*1.3:.1f},{ey - ry*1.3:.1f}Z" fill="{c["skin"]}"/>'
                         f'<path d="M{x - rx*1.15:.1f},{ey - ry*0.05:.1f} Q{x:.1f},{ey - ry*0.32:.1f} {x + rx*1.15:.1f},{ey - ry*0.05:.1f}" stroke="{INK}" stroke-width="{sw*0.8:.1f}" fill="none" stroke-linecap="round"/>')
    out.append(f'<g id="{p}eye-half" style="display:none">{both(half)}</g>')
    down = lambda x, s: (open_eye(x, s, 0.9, R * 0.06) +
                         f'<path d="M{x - rx*1.3:.1f},{ey + ry*0.15:.1f} Q{x:.1f},{ey - ry*0.2:.1f} {x + rx*1.3:.1f},{ey + ry*0.15:.1f} L{x + rx*1.4:.1f},{ey - ry*1.4:.1f} L{x - rx*1.4:.1f},{ey - ry*1.4:.1f}Z" fill="{c["skin"]}"/>'
                         f'<path d="M{x - rx*1.15:.1f},{ey + ry*0.12:.1f} Q{x:.1f},{ey - ry*0.18:.1f} {x + rx*1.15:.1f},{ey + ry*0.12:.1f}" stroke="{INK}" stroke-width="{sw*0.8:.1f}" fill="none" stroke-linecap="round"/>')
    out.append(f'<g id="{p}eye-down" style="display:none">{both(down)}</g>')
    closed = lambda x, s: f'<path d="M{x - rx*1.1:.1f},{ey:.1f} Q{x:.1f},{ey + ry*0.7:.1f} {x + rx*1.1:.1f},{ey:.1f}" stroke="{INK}" stroke-width="{sw:.1f}" fill="none" stroke-linecap="round"/>'
    out.append(f'<g id="{p}eye-closed" style="display:none">{both(closed)}</g>')
    happy = lambda x, s: f'<path d="M{x - rx*1.15:.1f},{ey + ry*0.25:.1f} Q{x:.1f},{ey - ry*0.85:.1f} {x + rx*1.15:.1f},{ey + ry*0.25:.1f}" stroke="{INK}" stroke-width="{sw*1.1:.1f}" fill="none" stroke-linecap="round"/>'
    out.append(f'<g id="{p}eye-happy" style="display:none">{both(happy)}</g>')
    return "".join(out)


BROWS = {  # (outer dy, inner dy, arch) in units of headR; negative = up
    "neutral": (0.0, 0.0, -0.05), "raised": (-0.09, -0.11, -0.07), "worried": (0.03, -0.12, 0.0),
    "sad": (0.06, -0.14, 0.02), "angry": (-0.04, 0.08, 0.0), "focused": (-0.01, 0.05, -0.02),
    "soft": (0.01, -0.03, -0.05),
}


def _brows(p, g, c):
    R, cy = g["headR"], g["headCY"]
    by = cy + R * 0.06 - R * 0.36
    col = _shade(c["hair_color"], 0.85) if c.get("hair_style") not in ("bald",) else _shade(c["skin"], 0.6)
    out = []
    for name, (o, i, a) in BROWS.items():
        seg = ""
        for s in (-1, 1):
            ox, ix = s * R * 0.52, s * R * 0.2
            oy, iy = by + o * R, by + i * R
            mx, my = (ox + ix) / 2, (oy + iy) / 2 + a * R
            seg += (f'<path d="M{ox:.1f},{oy:.1f} Q{mx:.1f},{my:.1f} {ix:.1f},{iy:.1f}" stroke="{col}" '
                    f'stroke-width="{R*0.075:.1f}" fill="none" stroke-linecap="round"/>')
        disp = "" if name == "neutral" else ' style="display:none"'
        out.append(f'<g id="{p}brow-{name}"{disp}>{seg}</g>')
    # thinking: one brow raised
    seg = ""
    for s, (o, i, a) in ((-1, BROWS["raised"]), (1, BROWS["focused"])):
        ox, ix = s * R * 0.52, s * R * 0.2
        oy, iy = by + o * R - (R * 0.05 if s < 0 else 0), by + i * R
        mx, my = (ox + ix) / 2, (oy + iy) / 2 + a * R
        seg += (f'<path d="M{ox:.1f},{oy:.1f} Q{mx:.1f},{my:.1f} {ix:.1f},{iy:.1f}" stroke="{col}" '
                f'stroke-width="{R*0.075:.1f}" fill="none" stroke-linecap="round"/>')
    out.append(f'<g id="{p}brow-thinking" style="display:none">{seg}</g>')
    return "".join(out)


MOUTHS = ["smile", "smile_small", "grin", "neutral", "flat", "frown", "wavy", "o",
          "open_s", "open_b", "smile_open_s", "smile_open_b", "purse", "bite"]


def _mouths(p, g, c):
    R, cy = g["headR"], g["headCY"]
    mx, my = 0.0, cy + R * 0.5
    w = R * 0.30
    sw = R * 0.06
    lip = INK
    tongue = "#E0707A"
    st = f'stroke="{lip}" stroke-width="{sw:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    d = {
        "smile": f'<path d="M{-w:.1f},{my - R*0.03:.1f} Q0,{my + R*0.2:.1f} {w:.1f},{my - R*0.03:.1f}" {st}/>',
        "smile_small": f'<path d="M{-w*0.62:.1f},{my:.1f} Q0,{my + R*0.11:.1f} {w*0.62:.1f},{my:.1f}" {st}/>',
        "neutral": f'<path d="M{-w*0.55:.1f},{my + R*0.02:.1f} Q0,{my + R*0.06:.1f} {w*0.55:.1f},{my + R*0.02:.1f}" {st}/>',
        "flat": f'<path d="M{-w*0.5:.1f},{my + R*0.04:.1f} L{w*0.5:.1f},{my + R*0.04:.1f}" {st}/>',
        "frown": f'<path d="M{-w*0.6:.1f},{my + R*0.1:.1f} Q0,{my - R*0.06:.1f} {w*0.6:.1f},{my + R*0.1:.1f}" {st}/>',
        "wavy": f'<path d="M{-w*0.6:.1f},{my + R*0.05:.1f} q{w*0.3:.1f},{-R*0.07:.1f} {w*0.6:.1f},0 t{w*0.6:.1f},0" {st}/>',
        "purse": f'<path d="M{w*0.05:.1f},{my + R*0.03:.1f} q{w*0.25:.1f},{-R*0.04:.1f} {w*0.45:.1f},{R*0.02:.1f}" {st}/>',
        "bite": f'<path d="M{-w*0.45:.1f},{my + R*0.03:.1f} L{w*0.45:.1f},{my + R*0.03:.1f}" {st}/><path d="M{-w*0.2:.1f},{my + R*0.03:.1f} l{w*0.12:.1f},{R*0.06:.1f} l{w*0.12:.1f},{-R*0.06:.1f}" fill="#fff" stroke="{lip}" stroke-width="{sw*0.5:.1f}"/>',
        "o": f'<ellipse cx="0" cy="{my + R*0.06:.1f}" rx="{w*0.32:.1f}" ry="{R*0.13:.1f}" fill="#5A2630" stroke="{lip}" stroke-width="{sw*0.6:.1f}"/>',
        "open_s": f'<ellipse cx="0" cy="{my + R*0.05:.1f}" rx="{w*0.45:.1f}" ry="{R*0.075:.1f}" fill="#5A2630" stroke="{lip}" stroke-width="{sw*0.6:.1f}"/>',
        "open_b": f'<ellipse cx="0" cy="{my + R*0.07:.1f}" rx="{w*0.55:.1f}" ry="{R*0.14:.1f}" fill="#5A2630" stroke="{lip}" stroke-width="{sw*0.6:.1f}"/><ellipse cx="0" cy="{my + R*0.15:.1f}" rx="{w*0.3:.1f}" ry="{R*0.05:.1f}" fill="{tongue}"/>',
    }
    for name, h in (("grin", 0.24), ("smile_open_s", 0.14), ("smile_open_b", 0.22)):
        ww = w * (1.0 if name != "smile_open_s" else 0.8)
        d[name] = (f'<path d="M{-ww:.1f},{my - R*0.03:.1f} Q0,{my + R*h*1.9:.1f} {ww:.1f},{my - R*0.03:.1f} Z" fill="#5A2630" stroke="{lip}" stroke-width="{sw*0.7:.1f}" stroke-linejoin="round"/>'
                   f'<path d="M{-ww*0.8:.1f},{my - R*0.01:.1f} Q0,{my + R*0.04:.1f} {ww*0.8:.1f},{my - R*0.01:.1f}" stroke="#fff" stroke-width="{R*0.05:.1f}" fill="none" stroke-linecap="round"/>'
                   f'<ellipse cx="0" cy="{my + R*h*0.75:.1f}" rx="{ww*0.4:.1f}" ry="{R*h*0.25:.1f}" fill="{tongue}"/>')
    out = []
    for name in MOUTHS:
        disp = "" if name == "smile_small" else ' style="display:none"'
        out.append(f'<g id="{p}mouth-{name}"{disp}>{d[name]}</g>')
    return "".join(out)


# ------------------------------------------------------------------ hair
def _hair(g, c):
    """Return (back_svg, front_svg)."""
    R, cy = g["headR"], g["headCY"]
    col = c["hair_color"]
    dk = _shade(col, 0.8)
    hi = _shade(col, 1.25)
    st = c.get("hair_style", "short")
    back, front = "", ""
    cap_top = cy - R * 1.2
    def cap(top=cap_top, fringe="side", side_drop=0.18):
        l, r = -R * 1.06, R * 1.06
        sy = cy + R * side_drop
        ctrl = sy + (top - sy) / 0.75          # cubic peak reaches `top`
        base = f"M{l:.1f},{sy:.1f} C{-R*1.12:.1f},{ctrl:.1f} {R*1.12:.1f},{ctrl:.1f} {r:.1f},{sy:.1f} "
        if fringe == "side":
            base += (f"L{R*0.96:.1f},{cy - R*0.12:.1f} Q{R*0.55:.1f},{cy - R*0.62:.1f} {-R*0.05:.1f},{cy - R*0.42:.1f} "
                     f"Q{-R*0.55:.1f},{cy - R*0.3:.1f} {-R*0.96:.1f},{cy - R*0.06:.1f} Z")
        elif fringe == "straight":
            base += f"L{R*0.98:.1f},{cy - R*0.3:.1f} Q0,{cy - R*0.42:.1f} {-R*0.98:.1f},{cy - R*0.3:.1f} Z"
        elif fringe == "part":
            base += (f"L{R*0.97:.1f},{cy - R*0.1:.1f} Q{R*0.55:.1f},{cy - R*0.62:.1f} {R*0.08:.1f},{cy - R*0.8:.1f} "
                     f"Q{-R*0.55:.1f},{cy - R*0.62:.1f} {-R*0.97:.1f},{cy - R*0.1:.1f} Z")
        elif fringe == "high":
            base += f"L{R*0.9:.1f},{cy - R*0.45:.1f} Q0,{cy - R*0.78:.1f} {-R*0.9:.1f},{cy - R*0.45:.1f} Z"
        elif fringe == "back":
            base += f"L{R*0.95:.1f},{cy - R*0.35:.1f} Q0,{cy - R*0.9:.1f} {-R*0.95:.1f},{cy - R*0.35:.1f} Z"
        return (f'<path d="{base}" fill="{col}"/>'
                f'<path d="M{-R*0.55:.1f},{top + R*0.24:.1f} Q{-R*0.1:.1f},{top + R*0.1:.1f} {R*0.35:.1f},{top + R*0.2:.1f}" '
                f'stroke="{hi}" stroke-width="{R*0.07:.1f}" fill="none" stroke-linecap="round" opacity=".55"/>')
    if st == "short":
        front = cap()
    elif st == "buzz":
        front = cap(top=cy - R * 1.1, fringe="high", side_drop=0.0)
    elif st == "spiky":
        pts = " ".join(f"L{x:.1f},{y:.1f}" for x, y in [
            (-R*0.9, cy - R*0.75), (-R*0.75, cy - R*1.35), (-R*0.45, cy - R*1.05), (-R*0.25, cy - R*1.45),
            (0, cy - R*1.1), (R*0.3, cy - R*1.48), (R*0.45, cy - R*1.08), (R*0.78, cy - R*1.32), (R*0.92, cy - R*0.8)])
        front = (f'<path d="M{-R*1.05:.1f},{cy + R*0.1:.1f} {pts} L{R*1.05:.1f},{cy + R*0.1:.1f} '
                 f'L{R*0.95:.1f},{cy - R*0.25:.1f} Q0,{cy - R*0.55:.1f} {-R*0.95:.1f},{cy - R*0.25:.1f} Z" fill="{col}"/>')
    elif st == "curly":
        back = f'<circle cx="0" cy="{cy - R*0.25:.1f}" r="{R*1.18:.1f}" fill="{dk}"/>'
        blobs = ""
        for i in range(11):
            a = math.radians(-175 + i * 17)
            bx, by = math.cos(a) * R * 1.0, cy - R * 0.1 + math.sin(a) * R * 1.02
            blobs += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{R*0.3:.1f}" fill="{col}"/>'
        for bx in (-0.5, -0.15, 0.2, 0.52):
            blobs += f'<circle cx="{bx*R:.1f}" cy="{cy - R*0.55:.1f}" r="{R*0.27:.1f}" fill="{col}"/>'
        front = blobs
    elif st == "afro":
        back = (f'<circle cx="0" cy="{cy - R*0.35:.1f}" r="{R*1.5:.1f}" fill="{col}"/>'
                f'<circle cx="{-R*0.5:.1f}" cy="{cy - R*1.0:.1f}" r="{R*0.5:.1f}" fill="{hi}" opacity=".25"/>')
        front = f'<path d="M{-R*1.0:.1f},{cy - R*0.2:.1f} Q0,{cy - R*0.85:.1f} {R*1.0:.1f},{cy - R*0.2:.1f} L{R*1.1:.1f},{cy - R*1.0:.1f} L{-R*1.1:.1f},{cy - R*1.0:.1f}Z" fill="{col}"/>'
    elif st == "ponytail":
        back = (f'<path d="M{R*0.6:.1f},{cy - R*0.9:.1f} Q{R*1.9:.1f},{cy - R*0.6:.1f} {R*1.45:.1f},{cy + R*0.9:.1f} '
                f'Q{R*1.25:.1f},{cy + R*0.3:.1f} {R*0.9:.1f},{cy - R*0.3:.1f} Z" fill="{col}"/>')
        front = cap(fringe="part") + f'<circle cx="{R*0.98:.1f}" cy="{cy - R*0.72:.1f}" r="{R*0.13:.1f}" fill="{c.get("accent", "#FE007A")}"/>'
    elif st == "pigtails":
        back = "".join(f'<circle cx="{s*R*1.18:.1f}" cy="{cy - R*0.05:.1f}" r="{R*0.42:.1f}" fill="{col}"/>'
                       f'<circle cx="{s*R*1.18:.1f}" cy="{cy + R*0.4:.1f}" r="{R*0.32:.1f}" fill="{col}"/>' for s in (-1, 1))
        front = cap(fringe="straight") + "".join(
            f'<circle cx="{s*R*0.98:.1f}" cy="{cy - R*0.35:.1f}" r="{R*0.1:.1f}" fill="{c.get("accent", "#FE007A")}"/>' for s in (-1, 1))
    elif st == "bob":
        back = f'<path d="M{-R*1.17:.1f},{cy + R*0.75:.1f} L{-R*1.17:.1f},{cy - R*0.4:.1f} Q0,{cy - R*1.75:.1f} {R*1.17:.1f},{cy - R*0.4:.1f} L{R*1.17:.1f},{cy + R*0.75:.1f} Q0,{cy + R*0.95:.1f} {-R*1.17:.1f},{cy + R*0.75:.1f}Z" fill="{col}"/>'
        front = cap(fringe="straight", side_drop=0.55)
    elif st == "long":
        back = f'<path d="M{-R*1.2:.1f},{cy + R*1.9:.1f} L{-R*1.22:.1f},{cy - R*0.3:.1f} Q0,{cy - R*1.8:.1f} {R*1.22:.1f},{cy - R*0.3:.1f} L{R*1.2:.1f},{cy + R*1.9:.1f} Q0,{cy + R*2.1:.1f} {-R*1.2:.1f},{cy + R*1.9:.1f}Z" fill="{col}"/>'
        front = cap(fringe="part", side_drop=0.6)
    elif st == "bun":
        back = f'<circle cx="0" cy="{cy - R*1.25:.1f}" r="{R*0.42:.1f}" fill="{col}"/>'
        front = cap(fringe="back", side_drop=0.1)
    elif st == "braids":
        for s in (-1, 1):
            back += "".join(f'<ellipse cx="{s*R*1.02:.1f}" cy="{cy + R*(0.3 + i*0.34):.1f}" rx="{R*0.2:.1f}" ry="{R*0.22:.1f}" fill="{col}" stroke="{dk}" stroke-width="{R*0.03:.1f}"/>' for i in range(5))
        front = cap(fringe="part", side_drop=0.3)
    elif st == "adult_m":
        front = cap(top=cy - R * 1.12, fringe="side", side_drop=0.05)
    elif st == "long_adult":
        back = f'<path d="M{-R*1.15:.1f},{cy + R*1.7:.1f} L{-R*1.18:.1f},{cy - R*0.3:.1f} Q0,{cy - R*1.75:.1f} {R*1.18:.1f},{cy - R*0.3:.1f} L{R*1.15:.1f},{cy + R*1.7:.1f} Q0,{cy + R*1.35:.1f} {-R*1.15:.1f},{cy + R*1.7:.1f}Z" fill="{col}"/>'
        front = cap(fringe="side", side_drop=0.5)
    elif st == "bald":
        front = "".join(f'<path d="M{s*R*1.02:.1f},{cy + R*0.15:.1f} Q{s*R*1.12:.1f},{cy - R*0.35:.1f} {s*R*0.8:.1f},{cy - R*0.6:.1f}" stroke="{col}" stroke-width="{R*0.2:.1f}" fill="none" stroke-linecap="round"/>' for s in (-1, 1))
    elif st == "hijab":
        hc = c.get("hijab_color", "#7C5CBF")
        back = (f'<path d="M{-R*1.35:.1f},{cy + R*1.9:.1f} Q{-R*1.5:.1f},{cy - R*1.5:.1f} 0,{cy - R*1.42:.1f} '
                f'Q{R*1.5:.1f},{cy - R*1.5:.1f} {R*1.35:.1f},{cy + R*1.9:.1f} Z" fill="{hc}"/>')
        front = (f'<path d="M{-R*1.12:.1f},{cy + R*0.4:.1f} Q{-R*1.2:.1f},{cy - R*1.32:.1f} 0,{cy - R*1.3:.1f} '
                 f'Q{R*1.2:.1f},{cy - R*1.32:.1f} {R*1.12:.1f},{cy + R*0.4:.1f} L{R*0.95:.1f},{cy + R*0.1:.1f} '
                 f'Q{R*0.9:.1f},{cy - R*0.95:.1f} 0,{cy - R*0.95:.1f} Q{-R*0.9:.1f},{cy - R*0.95:.1f} {-R*0.95:.1f},{cy + R*0.1:.1f}Z" fill="{_shade(hc, 0.9)}"/>'
                 f'<path d="M{-R*1.05:.1f},{cy + R*0.65:.1f} Q0,{cy + R*1.45:.1f} {R*1.05:.1f},{cy + R*0.65:.1f} L{R*1.25:.1f},{cy + R*1.3:.1f} Q0,{cy + R*1.9:.1f} {-R*1.25:.1f},{cy + R*1.3:.1f}Z" fill="{hc}"/>')
    return back, front


# ------------------------------------------------------------------ body
def build_svg(key, spec):
    """Full static SVG group for one character (all variants inside)."""
    g = geometry(spec)
    p = f"a_{key}_"
    skin, skin_sh, blush = SKIN[spec.get("skin", "light")]
    c = {"skin": skin, "skin_sh": skin_sh, "hair_color": spec.get("hair", {}).get("color", "#3B2A20"),
         "hair_style": spec.get("hair", {}).get("style", "short"), "accent": spec.get("hair", {}).get("accent", "#FE007A"),
         "lashes": spec.get("lashes", spec.get("sex") == "f"), "hijab_color": spec.get("hijab_color", "#7C5CBF")}
    if c["hair_style"] == "hijab":
        c["hair_color"] = "#3B2A20"
    top = spec.get("top", {})
    tcol = top.get("color", "#5AA9F5")
    tsh = _shade(tcol, 0.84)
    tstyle = top.get("style", "tee")
    bottom = spec.get("bottom", {})
    bcol = bottom.get("color", "#3D4A6B")
    bstyle = bottom.get("style", "pants")
    shoes = spec.get("shoes", "#3A3A48")
    R, cy = g["headR"], g["headCY"]
    W, hipW, sY, hY = g["W"], g["hipW"], g["shoulderY"], g["hipY"]
    legW = g["legW"]
    parts = []
    # shadow
    parts.append(f'<ellipse id="{p}shadow" cx="0" cy="4" rx="{W*0.85:.1f}" ry="{W*0.16:.1f}" fill="#000" opacity=".16"/>')
    hair_back, hair_front = _hair(g, c)
    parts.append(f'<g id="{p}hairback">{hair_back}</g>')
    # legs (standing)
    legs = ""
    for s in (-1, 1):
        lx = s * hipW * 0.25
        leg_col = bcol if bstyle == "pants" else skin
        legs += f'<g id="{p}leg{"L" if s < 0 else "R"}">'
        legs += f'<rect x="{lx - legW/2:.1f}" y="{hY - 4:.1f}" width="{legW:.1f}" height="{-hY - legW*0.3:.1f}" rx="{legW*0.45:.1f}" fill="{leg_col}"/>'
        if bstyle == "shorts":
            legs += f'<rect x="{lx - legW*0.62:.1f}" y="{hY - 4:.1f}" width="{legW*1.24:.1f}" height="{-hY*0.42:.1f}" rx="{legW*0.3:.1f}" fill="{bcol}"/>'
        if bstyle in ("skirt", "dress") and spec.get("socks"):
            legs += f'<rect x="{lx - legW*0.52:.1f}" y="{-legW*1.5:.1f}" width="{legW*1.04:.1f}" height="{legW*1.2:.1f}" rx="{legW*0.3:.1f}" fill="{spec["socks"]}"/>'
        legs += (f'<ellipse cx="{lx + s*legW*0.12:.1f}" cy="{-legW*0.28:.1f}" rx="{legW*0.78:.1f}" ry="{legW*0.42:.1f}" fill="{shoes}"/>'
                 f'<ellipse cx="{lx + s*legW*0.02:.1f}" cy="{-legW*0.42:.1f}" rx="{legW*0.4:.1f}" ry="{legW*0.12:.1f}" fill="#fff" opacity=".25"/>')
        legs += "</g>"
    parts.append(f'<g id="{p}legs">{legs}</g>')
    # legs (sitting, knees toward camera)
    sit = ""
    kneeY = hY + g["legL"] * 0.1
    for s in (-1, 1):
        lx = s * hipW * 0.26
        leg_col = bcol if bstyle == "pants" else skin
        sit += (f'<rect x="{lx - legW*0.55:.1f}" y="{hY - 4:.1f}" width="{legW*1.1:.1f}" height="{g["legL"]*0.62:.1f}" rx="{legW*0.5:.1f}" fill="{leg_col}"/>'
                f'<ellipse cx="{lx:.1f}" cy="{hY + g["legL"]*0.6:.1f}" rx="{legW*0.72:.1f}" ry="{legW*0.4:.1f}" fill="{shoes}"/>')
    parts.append(f'<g id="{p}legsit" style="display:none">{sit}</g>')
    # skirt / dress lower
    if bstyle in ("skirt", "dress"):
        scol = tcol if bstyle == "dress" else bcol
        parts.append(f'<path d="M{-hipW*0.5:.1f},{hY - g["torsoH"]*0.12:.1f} L{hipW*0.5:.1f},{hY - g["torsoH"]*0.12:.1f} '
                     f'L{hipW*0.78:.1f},{hY + g["legL"]*0.42:.1f} Q0,{hY + g["legL"]*0.5:.1f} {-hipW*0.78:.1f},{hY + g["legL"]*0.42:.1f}Z" fill="{scol}"/>'
                     f'<path d="M{hipW*0.1:.1f},{hY - g["torsoH"]*0.1:.1f} L{hipW*0.78:.1f},{hY + g["legL"]*0.42:.1f} Q{hipW*0.4:.1f},{hY + g["legL"]*0.48:.1f} {hipW*0.3:.1f},{hY + g["legL"]*0.47:.1f}Z" fill="#000" opacity=".08"/>')
    # torso
    tb = hY + (g["legL"] * 0.08 if tstyle != "tuck" else 0)
    rr = W * 0.22
    torso_d = (f"M{-W/2:.1f},{sY + rr:.1f} Q{-W/2:.1f},{sY:.1f} {-W/2 + rr:.1f},{sY:.1f} L{W/2 - rr:.1f},{sY:.1f} "
               f"Q{W/2:.1f},{sY:.1f} {W/2:.1f},{sY + rr:.1f} L{hipW/2:.1f},{tb:.1f} Q0,{tb + W*0.06:.1f} {-hipW/2:.1f},{tb:.1f} Z")
    parts.append(f'<clipPath id="{p}tclip"><path d="{torso_d}"/></clipPath>')
    torso = f'<path d="{torso_d}" fill="{tcol}"/>'
    if top.get("stripes"):
        sc = top.get("accent", "#FFFFFF")
        torso += f'<g clip-path="url(#{p}tclip)">' + "".join(
            f'<rect x="{-W:.1f}" y="{sY + i*W*0.16:.1f}" width="{2*W:.1f}" height="{W*0.07:.1f}" fill="{sc}" opacity=".85"/>' for i in range(1, 9)) + "</g>"
    if tstyle == "cardigan":
        torso += (f'<path d="M{-W*0.14:.1f},{sY:.1f} L{W*0.14:.1f},{sY:.1f} L{W*0.1:.1f},{tb:.1f} L{-W*0.1:.1f},{tb:.1f}Z" fill="{top.get("accent", "#FFFFFF")}"/>'
                  + "".join(f'<circle cx="{-W*0.17:.1f}" cy="{sY + (tb - sY)*k:.1f}" r="{W*0.025:.1f}" fill="{tsh}"/>' for k in (0.3, 0.55, 0.8)))
    if tstyle == "hoodie":
        torso += (f'<path d="M{-W*0.3:.1f},{tb - (tb - sY)*0.35:.1f} L{W*0.3:.1f},{tb - (tb - sY)*0.35:.1f} L{W*0.36:.1f},{tb - 6:.1f} L{-W*0.36:.1f},{tb - 6:.1f}Z" fill="{tsh}"/>'
                  f'<path d="M{-W*0.07:.1f},{sY + 6:.1f} l0,{(tb - sY)*0.25:.1f} M{W*0.07:.1f},{sY + 6:.1f} l0,{(tb - sY)*0.22:.1f}" stroke="#fff" stroke-width="{W*0.025:.1f}" stroke-linecap="round"/>')
    if tstyle == "shirt":
        torso += (f'<path d="M{-W*0.2:.1f},{sY - 2:.1f} L0,{sY + W*0.2:.1f} L{-W*0.02:.1f},{sY - 2:.1f}Z M{W*0.2:.1f},{sY - 2:.1f} L0,{sY + W*0.2:.1f} L{W*0.02:.1f},{sY - 2:.1f}Z" fill="{top.get("accent", "#FFFFFF")}"/>'
                  + "".join(f'<circle cx="0" cy="{sY + (tb - sY)*k:.1f}" r="{W*0.02:.1f}" fill="{tsh}"/>' for k in (0.4, 0.62, 0.84)))
    if top.get("logo"):
        torso += f'<circle cx="{-W*0.18:.1f}" cy="{sY + (tb - sY)*0.35:.1f}" r="{W*0.07:.1f}" fill="{top.get("accent", "#FFFFFF")}" opacity=".9"/>'
    torso += f'<g clip-path="url(#{p}tclip)"><rect x="{W*0.18:.1f}" y="{sY - 10:.1f}" width="{W:.1f}" height="{tb - sY + 40:.1f}" fill="#000" opacity=".08"/></g>'
    if tstyle in ("tee", "dress", "tuck", "stripes"):
        torso += f'<path d="M{-W*0.17:.1f},{sY + 1:.1f} Q0,{sY + W*0.16:.1f} {W*0.17:.1f},{sY + 1:.1f}" fill="{skin}"/>'
    if bstyle in ("pants", "shorts") and tstyle != "hoodie":
        torso += f'<rect x="{-hipW/2 + 2:.1f}" y="{tb - W*0.06:.1f}" width="{hipW - 4:.1f}" height="{W*0.08:.1f}" fill="{bcol}" opacity=".0"/>'
    parts.append(f'<g id="{p}torso">{torso}</g>')
    # head
    head = []
    neckw = R * 0.42
    head.append(f'<rect x="{-neckw/2:.1f}" y="{sY - R*0.45:.1f}" width="{neckw:.1f}" height="{R*0.55:.1f}" fill="{skin_sh}"/>')
    ear_y = cy + R * 0.08
    head.append(f'<circle id="{p}earL" cx="{-R*0.97:.1f}" cy="{ear_y:.1f}" r="{R*0.19:.1f}" fill="{skin}"/>'
                f'<circle id="{p}earR" cx="{R*0.97:.1f}" cy="{ear_y:.1f}" r="{R*0.19:.1f}" fill="{skin}"/>')
    ry = R * (1.0 if spec.get("kind", "child") != "adult" else 1.08)
    rx = R * (1.0 if spec.get("kind", "child") != "adult" else 0.93)
    head.append(f'<ellipse cx="0" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{skin}"/>')
    head.append(f'<path d="M{R*0.35:.1f},{cy + ry*0.9:.1f} Q{rx*1.0:.1f},{cy + ry*0.6:.1f} {rx*0.98:.1f},{cy - R*0.1:.1f} Q{rx*0.9:.1f},{cy + ry*0.95:.1f} {R*0.35:.1f},{cy + ry*0.9:.1f}Z" fill="{skin_sh}" opacity=".55"/>')
    feats = []
    feats.append(f'<g id="{p}blush" opacity=".45">' + "".join(
        f'<ellipse cx="{s*R*0.58:.1f}" cy="{cy + R*0.36:.1f}" rx="{R*0.16:.1f}" ry="{R*0.1:.1f}" fill="{blush}"/>' for s in (-1, 1)) + '</g>')
    feats.append(f'<g id="{p}eyes">{_eyes(p, g, c)}</g>')
    feats.append(f'<g id="{p}brows">{_brows(p, g, c)}</g>')
    feats.append(f'<path d="M{-R*0.03:.1f},{cy + R*0.2:.1f} q{R*0.09:.1f},{R*0.1:.1f} {R*0.0:.1f},{R*0.16:.1f}" stroke="{skin_sh}" stroke-width="{R*0.07:.1f}" fill="none" stroke-linecap="round"/>')
    if spec.get("beard"):
        bc = spec.get("beard_color", c["hair_color"])
        feats.append(f'<path d="M{-rx*0.98:.1f},{cy + R*0.1:.1f} Q{-rx*0.95:.1f},{cy + ry*1.12:.1f} 0,{cy + ry*1.12:.1f} Q{rx*0.95:.1f},{cy + ry*1.12:.1f} {rx*0.98:.1f},{cy + R*0.1:.1f} '
                     f'Q{rx*0.75:.1f},{cy + R*0.75:.1f} {R*0.3:.1f},{cy + R*0.35:.1f} Q0,{cy + R*0.28:.1f} {-R*0.3:.1f},{cy + R*0.35:.1f} Q{-rx*0.75:.1f},{cy + R*0.75:.1f} {-rx*0.98:.1f},{cy + R*0.1:.1f}Z" fill="{bc}"/>')
    feats.append(f'<g id="{p}mouth">{_mouths(p, g, c)}</g>')
    if spec.get("glasses"):
        gc = spec.get("glasses_color", "#2B2230")
        ex, ey = R * 0.37, cy + R * 0.06
        feats.append("".join(f'<rect x="{s*ex - R*0.27:.1f}" y="{ey - R*0.24:.1f}" width="{R*0.54:.1f}" height="{R*0.46:.1f}" rx="{R*0.14:.1f}" fill="#fff" fill-opacity=".12" stroke="{gc}" stroke-width="{R*0.055:.1f}"/>' for s in (-1, 1))
                     + f'<path d="M{-ex + R*0.27:.1f},{ey - R*0.04:.1f} Q0,{ey - R*0.12:.1f} {ex - R*0.27:.1f},{ey - R*0.04:.1f}" stroke="{gc}" stroke-width="{R*0.05:.1f}" fill="none"/>')
    head.append(f'<g id="{p}feat">{"".join(feats)}</g>')
    head.append(f'<g id="{p}hairfront">{hair_front}</g>')
    parts.append(f'<g id="{p}head">{"".join(head)}</g>')
    # arms (dynamic paths), drawn last so hands can come in front of the face
    sleeve = "long" if tstyle in ("hoodie", "cardigan", "sweater", "shirt", "long") else ("none" if tstyle == "tank" else "short")
    for s, nm in ((-1, "L"), (1, "R")):
        sk, sl, (hx, hy) = arm_geom(g, s, *ARM_POSES["down"], sleeve=sleeve)
        parts.append(f'<g id="{p}arm{nm}">'
                     f'<path id="{p}arm{nm}s" d="{sk}" stroke="{skin}" stroke-width="{g["armW"]:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                     f'<path id="{p}arm{nm}c" d="{sl}" stroke="{tcol}" stroke-width="{g["armW"]*1.18:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                     f'<circle id="{p}hand{nm}" cx="{hx:.1f}" cy="{hy:.1f}" r="{g["handR"]:.1f}" fill="{skin}"/>'
                     f'</g>')
    body = "".join(parts)
    return (f'<g id="{p}root" data-actor="{key}"><g id="{p}lean"><g id="{p}bob">{body}</g></g></g>'), g, sleeve


def voice_for(spec):
    v = spec.get("voice", {})
    return v.get("id", "af_heart"), v.get("speed", 1.0), v.get("pitch", 1.0)


# ------------------------------------------------------------------ per-frame state
def _arm_angles(v):
    if isinstance(v, str):
        return ARM_POSES[v]
    return tuple(v)


def frame_state(key, g, sleeve, P):
    """Turn high-level actor parameters into the small dict the page applies.
    P keys: x y s lean bob tilt turn eye brow mouth blush look(armL/armR as
    pose name or (upper,fore)) legs('stand'|'sit') walk(phase or None) flip."""
    s = P.get("s", 1.0)
    flip = -1 if P.get("flip") else 1
    st = {"k": key}
    sit_drop = g["legL"] * 0.5 * s if P.get("legs") == "sit" else 0
    st["tf"] = f'translate({P["x"]:.1f},{P["y"] + sit_drop:.1f}) scale({s * flip:.4f},{s:.4f})'
    st["lean"] = f'rotate({P.get("lean", 0):.2f})'
    st["bob"] = f'translate(0,{P.get("bob", 0):.2f})'
    st["legs"] = P.get("legs", "stand")
    w = P.get("walk")
    if w is not None:
        a = math.sin(w) * 16
        st["legL"] = f'rotate({a:.1f},{-g["hipW"]*0.25:.1f},{g["hipY"]:.1f})'
        st["legR"] = f'rotate({-a:.1f},{g["hipW"]*0.25:.1f},{g["hipY"]:.1f})'
    else:
        st["legL"] = st["legR"] = ""
    st["head"] = f'rotate({P.get("tilt", 0):.2f},0,{g["shoulderY"]:.1f})'
    turn = P.get("turn", 0.0)
    lx, ly = P.get("look", (0, 0))
    R = g["headR"]
    st["feat"] = f'translate({turn * R * 0.2:.2f},0)'
    st["eyes"] = f'translate({lx * R * 0.07:.2f},{ly * R * 0.05:.2f})'
    st["hair"] = f'translate({turn * R * 0.06:.2f},0)'
    st["earL"] = 0 if turn < -0.55 else 1
    st["earR"] = 0 if turn > 0.55 else 1
    st["eye"] = P.get("eye", "open")
    st["brow"] = P.get("brow", "neutral")
    st["mouth"] = P.get("mouth", "smile_small")
    st["blush"] = round(P.get("blush", 0.45), 3)
    for side, nm in ((-1, "L"), (1, "R")):
        up, fo = _arm_angles(P.get("arm" + nm, "down"))
        sk, sl, (hx, hy) = arm_geom(g, side, up, fo, sleeve)
        st["arm" + nm] = [sk, sl, round(hx, 1), round(hy, 1)]
    st["op"] = round(P.get("opacity", 1.0), 3)
    return st


def hand_world(g, P, hand):
    """World position of a hand (for attaching props)."""
    side = -1 if hand == "L" else 1
    up, fo = _arm_angles(P.get("arm" + hand, "down"))
    _, _, (hx, hy) = arm_geom(g, side, up, fo)
    s = P.get("s", 1.0)
    flip = -1 if P.get("flip") else 1
    sit_drop = g["legL"] * 0.5 * s if P.get("legs") == "sit" else 0
    lean = math.radians(P.get("lean", 0))
    hy += P.get("bob", 0)
    rx, ry = hx * math.cos(lean) - hy * math.sin(lean), hx * math.sin(lean) + hy * math.cos(lean)
    return P["x"] + rx * s * flip, P["y"] + sit_drop + ry * s


APPLY_JS = r"""
window.__st = {};
function $(id){ return document.getElementById(id); }
function sw(p, grp, name, prev){
  if (prev === name) return;
  if (prev) { const o = $(p+grp+'-'+prev); if (o) o.style.display='none'; }
  const n = $(p+grp+'-'+name); if (n) n.style.display='';
}
function applyActor(st){
  const p = 'a_'+st.k+'_'; const old = window.__st[st.k] || {};
  $(p+'root').setAttribute('transform', st.tf);
  $(p+'root').setAttribute('opacity', st.op);
  $(p+'lean').setAttribute('transform', st.lean);
  $(p+'bob').setAttribute('transform', st.bob);
  if (old.legs !== st.legs){ $(p+'legs').style.display = st.legs==='sit'?'none':''; $(p+'legsit').style.display = st.legs==='sit'?'':'none';
    $(p+'shadow').style.display = st.legs==='sit'?'none':''; }
  $(p+'legL').setAttribute('transform', st.legL); $(p+'legR').setAttribute('transform', st.legR);
  $(p+'head').setAttribute('transform', st.head);
  $(p+'feat').setAttribute('transform', st.feat);
  $(p+'eyes').setAttribute('transform', st.eyes);
  $(p+'hairfront').setAttribute('transform', st.hair);
  $(p+'earL').style.display = st.earL? '':'none'; $(p+'earR').style.display = st.earR? '':'none';
  if (old.eye !== st.eye){ sw(p,'eye',st.eye, old.eye || 'open'); }
  if (old.brow !== st.brow){ sw(p,'brow',st.brow, old.brow || 'neutral'); }
  if (old.mouth !== st.mouth){ sw(p,'mouth',st.mouth, old.mouth || 'smile_small'); }
  $(p+'blush').setAttribute('opacity', st.blush);
  for (const s of ['L','R']){
    const a = st['arm'+s];
    $(p+'arm'+s+'s').setAttribute('d', a[0]); $(p+'arm'+s+'c').setAttribute('d', a[1]);
    const h = $(p+'hand'+s); h.setAttribute('cx', a[2]); h.setAttribute('cy', a[3]);
  }
  window.__st[st.k] = st;
}
"""
