"""Mariposa azul vectorial con aleteo, en los azules de la marca (#2088F8)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# azules de marca
C_EDGE  = (10, 40, 110)      # borde profundo
C_OUT   = (24, 92, 214)      # zona externa
C_MID   = (32, 136, 248)     # #2088F8 marca
C_IN    = (120, 210, 255)    # brillo interno
C_BODY  = (12, 32, 78)


def _catmull(pts, samples=26):
    """Spline cerrada Catmull-Rom que suaviza el contorno del ala."""
    p = np.asarray(pts, float)
    n = len(p)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = p[(i - 1) % n], p[i], p[(i + 1) % n], p[(i + 2) % n]
        t = np.linspace(0, 1, samples, endpoint=False)[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t
                          + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.concatenate(out)


# contornos normalizados del ala derecha (x hacia fuera, y hacia abajo, cuerpo en x=0)
FOREWING = [(0.04, -0.08), (0.15, -0.48), (0.40, -0.82), (0.71, -0.89),
            (0.97, -0.66), (1.01, -0.38), (0.71, -0.15), (0.36, -0.03)]
HINDWING = [(0.05, 0.05), (0.33, 0.12), (0.61, 0.29), (0.64, 0.55),
            (0.44, 0.72), (0.22, 0.65), (0.07, 0.33)]


def _wing_layer(size, poly, flap, sx, sy, cx, cy):
    """Rasteriza un ala con degradado radial y borde oscuro."""
    pts = _catmull(poly)
    pts = pts * np.array([sx * flap, sy]) + np.array([cx, cy])
    layer = Image.new("L", size, 0)
    ImageDraw.Draw(layer).polygon([tuple(q) for q in pts], fill=255)
    return layer, pts


def draw_butterfly(size=560, flap=1.0, glow=True):
    """flap: 1.0 alas abiertas de frente, ~0.15 alas casi de perfil."""
    S = size
    ss = 2                              # supersampling
    W = H = S * ss
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = W / 2, H / 2 + S * 0.03 * ss
    sx = sy = S * 0.44 * ss

    # degradado reutilizable (radial desde el cuerpo hacia la punta del ala)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - cx) / (sx * max(flap, 0.05))) ** 2 + ((yy - cy) / sy) ** 2)
    d = np.clip(d, 0, 1.25) / 1.25
    grad = np.zeros((H, W, 3), np.float32)
    stops = [(0.00, C_IN), (0.32, C_MID), (0.66, C_OUT), (1.00, C_EDGE)]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]; t1, c1 = stops[i + 1]
        m = (d >= t0) & (d <= t1)
        u = ((d - t0) / (t1 - t0))[m][:, None]
        grad[m] = np.array(c0, np.float32) * (1 - u) + np.array(c1, np.float32) * u

    body_alpha = Image.new("L", (W, H), 0)
    for side in (1, -1):
        for poly in (FOREWING, HINDWING):
            lay, pts = _wing_layer((W, H), poly, flap, sx * side, sy, cx, cy)
            body_alpha = Image.fromarray(
                np.maximum(np.array(body_alpha), np.array(lay)))

    alpha = np.array(body_alpha).astype(np.float32)
    # borde oscuro: la diferencia entre la máscara y su versión erosionada
    inner = np.array(body_alpha.filter(ImageFilter.MinFilter(13)).filter(
        ImageFilter.GaussianBlur(3 * ss))).astype(np.float32)
    edge = np.clip((alpha - inner) / 255.0, 0, 1)[:, :, None] ** 0.7
    rgb = grad * (1 - edge) + np.array(C_EDGE, np.float32) * edge

    out = np.dstack([rgb, alpha]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")

    dr = ImageDraw.Draw(img)
    # venas suaves
    for side in (1, -1):
        for k in range(4):
            ang = -1.15 + k * 0.30
            x1 = cx + side * sx * 0.10 * flap
            y1 = cy - sy * 0.05
            x2 = cx + side * sx * 0.92 * flap * math_cos(ang)
            y2 = cy + sy * 0.86 * math_sin(ang)
            dr.line([(x1, y1), (x2, y2)], fill=(10, 45, 120, 60), width=int(2.2 * ss))
    # lunares blancos en el borde del ala anterior
    for side in (1, -1):
        for (rx, ry, rr) in [(0.84, -0.58, 0.042), (0.92, -0.42, 0.035), (0.66, -0.75, 0.038)]:
            x = cx + side * sx * rx * flap
            y = cy + sy * ry
            r = S * rr * ss * max(flap, 0.25)
            dr.ellipse([x - r * max(flap, .3), y - r, x + r * max(flap, .3), y + r],
                       fill=(235, 248, 255, 205))

    # cuerpo
    bw = S * 0.030 * ss
    bh = S * 0.30 * ss
    dr.ellipse([cx - bw, cy - bh * 0.78, cx + bw, cy + bh], fill=C_BODY + (255,))
    dr.ellipse([cx - bw * 1.35, cy - bh * 0.95, cx + bw * 1.35, cy - bh * 0.55],
               fill=C_BODY + (255,))   # tórax
    dr.ellipse([cx - bw * 1.15, cy - bh * 1.20, cx + bw * 1.15, cy - bh * 0.88],
               fill=(18, 46, 100, 255))  # cabeza
    # antenas
    for side in (1, -1):
        pts = [(cx + side * bw * 0.5, cy - bh * 1.12),
               (cx + side * S * 0.085 * ss, cy - bh * 1.55),
               (cx + side * S * 0.150 * ss, cy - bh * 1.82)]
        dr.line(pts, fill=(16, 42, 96, 235), width=max(2, int(2.4 * ss)), joint="curve")
        ex, ey = pts[-1]
        rr = S * 0.014 * ss
        dr.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=(16, 42, 96, 235))

    img = img.resize((S, S), Image.LANCZOS)

    if glow:
        g = img.split()[3].filter(ImageFilter.GaussianBlur(S * 0.055))
        ga = np.array(g).astype(np.float32) * 0.55
        halo = np.dstack([
            np.full((S, S), 90, np.float32),
            np.full((S, S), 190, np.float32),
            np.full((S, S), 255, np.float32),
            ga]).astype(np.uint8)
        base = Image.fromarray(halo, "RGBA")
        base.alpha_composite(img)
        img = base
    return img


from math import cos as math_cos, sin as math_sin  # noqa: E402

if __name__ == "__main__":
    import sys
    strip = Image.new("RGBA", (560 * 5, 560), (18, 22, 30, 255))
    for i, f in enumerate([1.0, 0.75, 0.45, 0.2, 0.62]):
        strip.alpha_composite(draw_butterfly(560, f), (560 * i, 0))
    strip.convert("RGB").save(sys.argv[1], quality=92)
