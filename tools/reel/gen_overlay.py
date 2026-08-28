"""Capa de animacion del reel (1080x1920 RGBA cruda a stdout).

Contiene: degradados de legibilidad, sombra de la tarjeta de video, logo con
entrada animada, frases, y la transformacion de la M azul del logo en una
mariposa que vuela y sale del encuadre.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from butterfly import draw_butterfly

SP = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 31.41
NFRAMES = int(round(DUR * FPS))

CARD = (38, 356, 1004, 1004)         # x, y, w, h
CARD_R = 40
ACCENT = (111, 196, 255)
WHITE = (255, 255, 255)

F_MONT = os.path.join(SP, "fonts", "Montserrat.ttf")
F_PLAY = os.path.join(SP, "fonts", "PlayfairDisplay.ttf")
LOGO_SRC = "/root/.claude/uploads/0faedaae-9eb7-500a-80b4-d14074bbaf5f/c3032025-image.png"


# ---------------------------------------------------------------- utilidades
def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 3 * x ** 2 - 2 * x ** 3


def ramp(t, t0, t1, ease=ease_out):
    """0 antes de t0, 1 despues de t1, suavizado en medio."""
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    return ease((t - t0) / (t1 - t0))


def blit(dst, src, x, y):
    """alpha_composite con recorte contra los bordes del lienzo."""
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, W - x), min(src.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    piece = src if (sx0, sy0, sx1, sy1) == (0, 0, src.width, src.height) \
        else src.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(piece, (x + sx0, y + sy0))


def with_alpha(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    out.putalpha(out.split()[3].point(lambda v: int(v * a)))
    return out


def font(path, size, name=None):
    f = ImageFont.truetype(path, size)
    if name:
        try:
            f.set_variation_by_name(name)
        except Exception:
            pass
    return f


def text_img(text, fnt, color, maxw=944, shadow=True):
    """Renderiza una linea con sombra suave, recortada a su caja."""
    pad = 54
    tmp = Image.new("RGBA", (10, 10))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((pad - bb[0], pad - bb[1]), text, font=fnt, fill=color + (255,))
    if shadow:
        a = img.split()[3]
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.72)))
        sh = Image.merge("RGBA", (Image.new("L", img.size, 4),) * 3 + (sh.split()[3],))
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 7))
        out.alpha_composite(img)
        img = out
    return img


def fit_font(text, path, size, name, maxw=944):
    """Reduce el cuerpo hasta que la linea entre en el ancho util."""
    while size > 30:
        f = font(path, size, name)
        bb = ImageDraw.Draw(Image.new("RGBA", (10, 10))).textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= maxw:
            return f, bb[2] - bb[0]
        size -= 2
    return font(path, size, name), maxw


# ---------------------------------------------------------------- capa fija
def build_static():
    """Degradados de legibilidad arriba/abajo + sombra bajo la tarjeta."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = np.zeros((H, W, 4), np.float32)
    y = np.arange(H)[:, None]

    top = np.clip((356 - y) / 356.0, 0, 1) ** 1.5 * 0.44
    bot = np.clip((y - 1360) / (H - 1360.0), 0, 1) ** 1.2 * 0.50
    a = np.clip(top + bot, 0, 1)
    g[..., 3] = (a * 255)
    g[..., 0], g[..., 1], g[..., 2] = 4, 8, 16
    base = Image.fromarray(g.astype(np.uint8), "RGBA")

    # sombra proyectada de la tarjeta (solo por fuera de la tarjeta)
    x0, y0, cw, ch = CARD
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 10, x0 + cw, y0 + ch + 16],
                                         CARD_R, fill=190)
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).rounded_rectangle([x0, y0, x0 + cw, y0 + ch], CARD_R, fill=0)
    sh = Image.fromarray((np.array(sh) * (np.array(hole) / 255.0)).astype(np.uint8))
    shadow = Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (sh,))
    base.alpha_composite(shadow)

    # filo claro en el borde superior de la tarjeta
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rounded_rectangle([x0, y0, x0 + cw, y0 + ch], CARD_R,
                                           outline=(255, 255, 255, 46), width=2)
    base.alpha_composite(edge)
    return base


# ---------------------------------------------------------------- logo
def build_logo():
    im = Image.open(LOGO_SRC).convert("RGBA")
    im = im.crop(im.getbbox())
    a = np.array(im)
    al = a[..., 3] > 100
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    blue = al & (b > 150) & (b - r > 60) & (b - g > 30)
    lab, n = ndimage.label(blue)
    sizes = ndimage.sum(blue, lab, range(1, n + 1))
    mmask = lab == (int(np.argmax(sizes)) + 1)

    m_arr = a.copy(); m_arr[..., 3] = np.where(mmask, a[..., 3], 0)
    rest = a.copy(); rest[..., 3] = np.where(mmask, 0, a[..., 3])

    LW = 300
    LH = int(round(im.height * LW / im.width))
    full = im.resize((LW, LH), Image.LANCZOS)
    m_im = Image.fromarray(m_arr, "RGBA").resize((LW, LH), Image.LANCZOS)
    rest_im = Image.fromarray(rest, "RGBA").resize((LW, LH), Image.LANCZOS)

    ys, xs = np.where(np.array(m_im)[..., 3] > 60)
    m_center = (float(xs.mean()), float(ys.mean()))
    m_box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return full, m_im, rest_im, m_center, m_box


def radial_glow(size, color=(150, 215, 255)):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2.0
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    a = np.clip(1 - d, 0, 1) ** 2.4 * 255
    arr = np.dstack([np.full((size, size), color[0], np.float32),
                     np.full((size, size), color[1], np.float32),
                     np.full((size, size), color[2], np.float32), a])
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- guion
LINES = [
    # (texto, fuente, variante, cuerpo, color, t_entrada, t_salida)
    ("Dejé mi tierra,",       F_MONT, "SemiBold", 72, WHITE,  2.6, 10.9),
    ("no mis raíces.",        F_MONT, "Bold",     82, ACCENT, 3.3, 11.1),
    ("Aquí aprendí",          F_MONT, "SemiBold", 72, WHITE, 12.3, 21.1),
    ("a florecer de nuevo.",  F_MONT, "Bold",     82, ACCENT, 13.0, 21.3),
    ("Canadá,",               F_PLAY, "Bold",     76, WHITE, 26.6, 99.0),
    ("mi segundo hogar.",     F_PLAY, "Bold",     76, ACCENT, 27.2, 99.0),
]
BLOCK_OF = [0, 0, 1, 1, 2, 2]
BLOCK_Y = [1468, 1468, 1478]                      # y del primer renglon por bloque
IN_DUR, OUT_DUR = 1.05, 0.85

# hitos de la transformacion
T_LOGO_IN   = 1.00
T_SPLIT     = 22.80    # empieza a desvanecerse el resto del logo
T_MORPH     = 24.00    # la M empieza a convertirse
T_BORN      = 25.40    # mariposa formada
T_EXIT      = 31.15    # fuera del encuadre


def main(out):
    static = build_static()
    logo_full, logo_m, logo_rest, m_center, m_box = build_logo()
    LX, LY = W - 54 - logo_full.width, 128          # esquina superior derecha
    MCX, MCY = LX + m_center[0], LY + m_center[1]   # centro de la M en el lienzo

    # frases pre-renderizadas
    rendered = []
    for txt, fp, var, size, col, tin, tout in LINES:
        f, _ = fit_font(txt, fp, size, var)
        rendered.append(text_img(txt, f, col))

    # posiciones: cada bloque centrado horizontalmente, apilado
    positions = []
    for i, img in enumerate(rendered):
        blk = BLOCK_OF[i]
        first = BLOCK_OF.index(blk)
        y = BLOCK_Y[blk] + (0 if i == first else 96)
        positions.append(((W - img.width) // 2, y - 54))   # -54 compensa el padding

    # aleteo pre-renderizado
    NPH = 24
    BFSIZE = 460
    flaps = []
    for k in range(NPH):
        ph = k / NPH
        fl = 0.16 + 0.84 * (0.5 + 0.5 * math.cos(2 * math.pi * ph)) ** 0.75
        flaps.append(draw_butterfly(BFSIZE, fl))

    glow = radial_glow(700)

    # trayectoria de vuelo (Catmull-Rom sobre puntos guia)
    WPTS = np.array([[MCX, MCY], [MCX - 70, MCY + 70], [520, 520], [330, 830],
                     [400, 1130], [670, 1300], [900, 1080], [980, 760],
                     [930, 460], [880, 190], [840, -180], [820, -700],
                     [810, -1250]], float)
    # ritmo del vuelo: (segundo, posicion sobre la curva)
    KEY_T = np.array([25.40, 26.60, 27.80, 28.80, 29.60, 30.20, 30.70, 31.15])
    KEY_S = np.array([0.50,  2.20,  4.00,  5.80,  7.20,  8.50,  9.50, 11.50])
    S_MAX = len(WPTS) - 1.5

    def path_at(sv):
        """Punto sobre la curva Catmull-Rom en la abscisa sv."""
        p = WPTS
        sv = float(np.clip(sv, 0.5, S_MAX))
        i = int(np.clip(math.floor(sv), 1, len(p) - 3))
        t = np.clip(sv - i, 0, 1)
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        return 0.5 * ((2 * p1) + (-p0 + p2) * t
                      + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)

    # particulas del destello
    rng = np.random.default_rng(7)
    NP = 54
    p_ang = rng.uniform(0, 2 * math.pi, NP)
    p_spd = rng.uniform(70, 340, NP)
    p_life = rng.uniform(0.55, 1.35, NP)
    p_size = rng.uniform(3.5, 11.0, NP)
    p_delay = rng.uniform(0.0, 0.45, NP)

    trail = []
    preview = os.environ.get("PREVIEW_TIMES")
    if preview:
        times = [float(x) for x in preview.split(",")]
        frame_ids = [int(round(x * FPS)) for x in times]
        fo = None
    else:
        frame_ids = list(range(NFRAMES))
        fo = open(out, "wb", buffering=1024 * 1024) if out != "-" else sys.stdout.buffer

    for fi in frame_ids:
        t = fi / FPS
        fr = static.copy()

        # ---------------- frases
        for i, img in enumerate(rendered):
            _, _, _, _, _, tin, tout = LINES[i]
            if t < tin - 0.02:
                continue
            ain = ramp(t, tin, tin + IN_DUR)
            aout = 1.0 - ramp(t, tout, tout + OUT_DUR, ease_in_out)
            a = ain * aout
            if a <= 0.004:
                continue
            dy = (1 - ain) * 46 - (1 - aout) * 26
            x, y = positions[i]
            blit(fr, with_alpha(img, a), x, y + dy)

        # ---------------- logo / M / mariposa
        if t >= T_LOGO_IN - 0.05:
            lin = ramp(t, T_LOGO_IN, T_LOGO_IN + 1.10)
            # ligero rebote en la entrada
            sc = 0.74 + 0.26 * lin + 0.05 * math.sin(math.pi * lin) * (1 - lin)
            dy = (1 - lin) * -22

            rest_a = lin * (1.0 - ramp(t, T_SPLIT, T_SPLIT + 1.05, ease_in_out))
            m_a = lin * (1.0 - ramp(t, T_MORPH + 0.15, T_MORPH + 1.15, ease_in_out))
            # la M crece y se eleva justo antes de transformarse
            grow = ramp(t, T_SPLIT, T_MORPH + 0.6, ease_in_out)
            m_sc = sc * (1 + 0.30 * grow)
            m_dy = dy - 26 * grow

            def put(layer, alpha, scale, off_y, about=None):
                if alpha <= 0.004:
                    return
                nw = max(2, int(round(layer.width * scale)))
                nh = max(2, int(round(layer.height * scale)))
                im = layer.resize((nw, nh), Image.LANCZOS)
                if about is None:
                    cxp, cyp = LX + layer.width / 2, LY + layer.height / 2
                    blit(fr, with_alpha(im, alpha), cxp - nw / 2, cyp - nh / 2 + off_y)
                else:
                    # escala respecto al centro de la M para que no se desplace
                    ax, ay = about
                    ox = LX + ax - (ax * scale)
                    oy = LY + ay - (ay * scale)
                    blit(fr, with_alpha(im, alpha), ox, oy + off_y)

            put(logo_rest, rest_a, sc, dy, about=m_center)
            put(logo_m, m_a, m_sc, m_dy, about=m_center)

            # resplandor de la metamorfosis
            gl = 0.0
            if t > T_SPLIT:
                gl = ramp(t, T_MORPH - 0.5, T_MORPH + 0.45) * \
                     (1 - ramp(t, T_MORPH + 0.55, T_BORN + 0.35, ease_in_out))
            if gl > 0.004:
                gs = int(320 + 380 * gl)
                g2 = glow.resize((gs, gs), Image.BILINEAR)
                blit(fr, with_alpha(g2, 0.85 * gl), MCX - gs / 2, MCY - 26 - gs / 2)

        # ---------------- particulas
        if T_MORPH - 0.1 <= t <= T_MORPH + 2.2:
            pl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dp = ImageDraw.Draw(pl)
            any_p = False
            for k in range(NP):
                age = t - (T_MORPH + p_delay[k])
                if age < 0 or age > p_life[k]:
                    continue
                any_p = True
                u = age / p_life[k]
                d = p_spd[k] * age * (1.6 - 0.6 * u)
                px = MCX + math.cos(p_ang[k]) * d
                py = MCY - 26 + math.sin(p_ang[k]) * d * 0.85 + 42 * u * u
                rr = p_size[k] * (1 - 0.45 * u)
                aa = int(235 * (1 - u) ** 1.5)
                dp.ellipse([px - rr, py - rr, px + rr, py + rr],
                           fill=(190, 232, 255, aa))
            if any_p:
                pl = pl.filter(ImageFilter.GaussianBlur(1.6))
                fr.alpha_composite(pl)

        # ---------------- mariposa
        if t >= T_MORPH + 0.35:
            born = ramp(t, T_MORPH + 0.35, T_BORN, ease_in_out)
            u = np.clip((t - T_BORN) / (T_EXIT - T_BORN), 0, 1)
            sv = float(np.interp(t, KEY_T, KEY_S))
            pos = path_at(sv)
            nxt = path_at(sv + 0.10)
            vx, vy = nxt[0] - pos[0], nxt[1] - pos[1]

            # aleteo (mas rapido cuanto mas rapido vuela)
            beat = 3.6 if t > T_BORN else 2.4
            ph = ((t - T_MORPH) * beat) % 1.0
            bimg = flaps[int(ph * NPH) % NPH]

            # tamano: nace pequena, crece al acercarse a camara
            base_px = 190 + 26 * float(u)
            near = ramp(t, T_EXIT - 1.7, T_EXIT, ease_in_out) ** 1.7
            px_size = (base_px * (0.55 + 0.45 * born)) * (1 + 1.7 * near)
            s = px_size / BFSIZE
            bw = max(4, int(BFSIZE * s))
            b2 = bimg.resize((bw, bw), Image.LANCZOS)

            sp = math.hypot(vx, vy) + 1e-6
            bank = 19.0 * (vx / sp)          # se ladea hacia su direccion
            ang = -bank + 6.0 * math.sin(2 * math.pi * (t - T_BORN) * 0.95)
            b2 = b2.rotate(-ang, resample=Image.BICUBIC, expand=True)

            # ondulacion del vuelo
            wob_x = 26 * math.sin(2 * math.pi * (t - T_BORN) * 0.62 + 1.1) * (1 - near)
            wob_y = 20 * math.sin(2 * math.pi * (t - T_BORN) * 0.83) * (1 - near)
            bx, by = pos[0] + wob_x, pos[1] + wob_y

            # estela de destellos
            if t > T_BORN and fi % 2 == 0:
                trail.append((bx, by, t))
            trail = [q for q in trail if t - q[2] < 0.85]
            if trail:
                tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                dt = ImageDraw.Draw(tl)
                for (tx, ty, tt0) in trail:
                    k = 1 - (t - tt0) / 0.85
                    rr = 7 * k
                    dt.ellipse([tx - rr, ty - rr, tx + rr, ty + rr],
                               fill=(160, 220, 255, int(120 * k ** 2)))
                fr.alpha_composite(tl.filter(ImageFilter.GaussianBlur(3)))

            a_bf = born
            if a_bf > 0.004:
                blit(fr, with_alpha(b2, a_bf), bx - b2.width / 2, by - b2.height / 2)

        if fo is None:
            fr.save(os.path.join(SP, "build", "ov_%06.2f.png" % t))
            print("preview t=%.2f" % t, file=sys.stderr)
            continue
        fo.write(fr.tobytes())
        if fi % 60 == 0:
            print("frame %d/%d  t=%.1fs" % (fi, NFRAMES, t), file=sys.stderr)

    if fo is not None and fo is not sys.stdout.buffer:
        fo.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "-")
