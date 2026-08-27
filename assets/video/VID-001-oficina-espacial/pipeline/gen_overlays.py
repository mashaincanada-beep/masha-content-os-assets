# -*- coding: utf-8 -*-
"""Genera las capas de VFX (HUD con alfa + capa de brillo aditivo) para el montaje espacial."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30
DUR = 9.17
NF = int(DUR * FPS)          # 275 fotogramas
GW, GH = W // 2, H // 2      # la capa de brillo se dibuja a media resolucion

BASE = os.path.dirname(os.path.abspath(__file__))
FD = "/usr/share/fonts/truetype/dejavu/"
def font(name, size): return ImageFont.truetype(FD + name, size)
MONO   = lambda s: font("DejaVuSansMono.ttf", s)
MONOB  = lambda s: font("DejaVuSansMono-Bold.ttf", s)
SANSB  = lambda s: font("DejaVuSans-Bold.ttf", s)

CY   = (110, 235, 255)
CYD  = (58, 148, 180)
AM   = (255, 176, 70)
WH   = (232, 249, 255)
RD   = (255, 96, 96)

M    = 54                    # margen lateral
rnd  = random.Random(7)

# ---------------------------------------------------------------- utilidades
def a(c, alpha):
    """Color RGB -> RGBA con alfa 0..1."""
    return (c[0], c[1], c[2], max(0, min(255, int(alpha * 255))))

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def track(d, xy, text, f, fill, sp=0):
    """Texto con espaciado entre caracteres."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + sp
    return x

def dashed_circle(d, cx, cy, r, phase, fill, seg=14, gap=10, wd=3):
    per = seg + gap
    n = max(1, int(2 * math.pi * r / per))
    for i in range(n):
        a0 = 2 * math.pi * i / n + phase
        a1 = a0 + (seg / per) * (2 * math.pi / n)
        d.arc([cx - r, cy - r, cx + r, cy + r],
              math.degrees(a0), math.degrees(a1), fill=fill, width=wd)

def bracket(d, x, y, sx, sy, L, wd, fill):
    d.line([x, y, x + sx * L, y], fill=fill, width=wd)
    d.line([x, y, x, y + sy * L], fill=fill, width=wd)

def soft_dot(g, x, y, r, c, inten):
    """Punto suave en la capa de brillo (media resolucion)."""
    if r < 1: r = 1
    box = [x - r, y - r, x + r, y + r]
    g.ellipse(box, fill=(int(c[0] * inten), int(c[1] * inten), int(c[2] * inten)))

# ---------------------------------------------------------------- elementos persistentes
# Particulas en gravedad cero: 3 capas de profundidad
PART = []
for layer, (n, rr, sp, br) in enumerate([(70, 1.6, 6.0, .35), (55, 2.6, 11.0, .55), (30, 4.0, 18.0, .85)]):
    for _ in range(n):
        PART.append(dict(x=rnd.uniform(0, GW), y=rnd.uniform(0, GH), r=rr * rnd.uniform(.6, 1.4),
                         sp=sp * rnd.uniform(.7, 1.3), ph=rnd.uniform(0, 6.28),
                         br=br * rnd.uniform(.6, 1.2), wob=rnd.uniform(6, 20)))

# Campo de estrellas del ventanal
STARS = [dict(x=rnd.uniform(0, 1), y=rnd.uniform(0, 1), r=rnd.choice([1, 1, 1, 2, 2, 3]),
              b=rnd.uniform(.35, 1.0), tw=rnd.uniform(0, 6.28), sp=rnd.uniform(.006, .03))
         for _ in range(240)]

# ---------------------------------------------------------------- ventanal al espacio
VP_X0, VP_Y0, VP_X1, VP_Y1 = 250, 500, 980, 1140
VP_IN, VP_OUT = 3.30, 8.15

def viewport(hud, glow_s, t):
    """Ventana holografica que muestra la orbita terrestre."""
    if t < VP_IN or t > VP_OUT + .45:
        return
    op = ease((t - VP_IN) / .40)
    if t > VP_OUT:
        op *= 1 - ease((t - VP_OUT) / .45)
    if op <= .01:
        return
    w, h = VP_X1 - VP_X0, VP_Y1 - VP_Y0
    cy_ = (VP_Y0 + VP_Y1) / 2
    hh = max(2, int(h * ease(min(1, (t - VP_IN) / .40))))   # apertura vertical tipo obturador
    y0, y1 = int(cy_ - hh / 2), int(cy_ + hh / 2)

    # --- contenido: estrellas + planeta ---
    inner = Image.new("RGB", (w, h), (3, 6, 16))
    di = ImageDraw.Draw(inner)
    drift = (t - VP_IN) * 14
    for s in STARS:
        sx = (s["x"] * w - drift * s["sp"] * 34) % w
        sy = s["y"] * h + math.sin(t * .3 + s["tw"]) * 2
        tw = .65 + .35 * math.sin(t * 2.2 + s["tw"])
        v = int(255 * s["b"] * tw)
        di.ellipse([sx - s["r"], sy - s["r"], sx + s["r"], sy + s["r"]], fill=(v, v, min(255, int(v * 1.08))))
    # limbo del planeta (abajo a la derecha) con atmosfera
    pcx, pcy, pr = w * 0.78 + math.sin(t * .25) * 6, h * 1.28, h * 0.86
    for i in range(16, 0, -1):                       # halo atmosferico
        rr = pr + i * 7
        di.ellipse([pcx - rr, pcy - rr, pcx + rr, pcy + rr],
                   outline=(int(24 + i * 2), int(70 + i * 5), int(120 + i * 7)), width=7)
    di.ellipse([pcx - pr, pcy - pr, pcx + pr, pcy + pr], fill=(14, 46, 86))
    for i in range(9):                               # bandas de nubes / terminador
        f = i / 9
        rr = pr * (1 - f * .42)
        c = int(20 + 34 * (1 - f)), int(62 + 58 * (1 - f)), int(100 + 62 * (1 - f))
        di.arc([pcx - rr, pcy - rr, pcx + rr, pcy + rr], 200 + f * 22, 340 - f * 22,
               fill=c, width=max(2, int(9 - f * 6)))
    di.arc([pcx - pr, pcy - pr, pcx + pr, pcy + pr], 186, 354, fill=(150, 210, 255), width=3)
    inner = inner.filter(ImageFilter.GaussianBlur(1.6))
    # lineas de barrido del holograma
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dov = ImageDraw.Draw(ov)
    for yy in range(int((t * 60) % 5), h, 5):
        dov.line([0, yy, w, yy], fill=(0, 0, 0, 46))
    inner = Image.alpha_composite(inner.convert("RGBA"), ov)

    flick = 1.0 if rnd.random() > .04 else .78
    panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    panel.paste(inner, (0, 0))
    panel.putalpha(panel.getchannel("A").point(lambda v: int(v * .93 * op * flick)))
    crop = panel.crop((0, int((h - hh) / 2), w, int((h + hh) / 2)))
    hud.alpha_composite(crop, (VP_X0, y0))

    # --- bisel y rotulos ---
    d = ImageDraw.Draw(hud)
    col = a(CY, .95 * op)
    d.rectangle([VP_X0, y0, VP_X1, y1], outline=col, width=3)
    for (bx, by, sx, sy) in [(VP_X0 - 8, y0 - 8, 1, 1), (VP_X1 + 8, y0 - 8, -1, 1),
                             (VP_X0 - 8, y1 + 8, 1, -1), (VP_X1 + 8, y1 + 8, -1, -1)]:
        bracket(d, bx, by, sx, sy, 34, 4, a(AM, .9 * op))
    if hh > h * .8:
        d.rectangle([VP_X0, y0 - 42, VP_X0 + 470, y0 - 6], fill=a((6, 20, 30), .82 * op))
        track(d, (VP_X0 + 12, y0 - 36), "VENTANAL EXTERIOR", MONOB(21), a(CY, .98 * op), 1.4)
        tx = f"ORBITA BAJA  ALT {412 + math.sin(t * .8) * 3:.1f} km"
        d.text((VP_X1 - MONO(19).getlength(tx) - 6, y1 + 12), tx, font=MONO(19), fill=a(CYD, .95 * op))
    # destello de apertura
    if t - VP_IN < .40:
        f = 1 - (t - VP_IN) / .40
        soft_dot_line = ImageDraw.Draw(glow_s)
        soft_dot_line.rectangle([VP_X0 // 2, int(cy_ / 2 - 3), VP_X1 // 2, int(cy_ / 2 + 3)],
                                fill=(int(200 * f), int(250 * f), int(255 * f)))
    # brillo del bisel
    dg = ImageDraw.Draw(glow_s)
    dg.rectangle([VP_X0 // 2, y0 // 2, VP_X1 // 2, y1 // 2], outline=(int(40 * op), int(110 * op), int(130 * op)), width=2)

# ---------------------------------------------------------------- HUD principal
def draw_hud(t, hud, glow_s):
    d  = ImageDraw.Draw(hud)
    dg = ImageDraw.Draw(glow_s)
    boot = ease((t - 0.55) / 0.55)          # los elementos entran tras el arranque
    end  = ease((t - 8.30) / 0.35)          # y salen en la tarjeta final
    op   = boot * (1 - end)

    if op > .01:
        # ---- barra superior ----
        track(d, (M, 74), "AURORA-7", SANSB(30), a(WH, .96 * op), 3)
        track(d, (M, 116), "ESTACION ORBITAL  ·  CUBIERTA 3  ·  MODULO OFICINA", MONO(17), a(CYD, .95 * op), .6)
        tc = f"T+00:{t:05.2f}"
        f22 = MONOB(22)
        d.text((W - M - d.textlength(tc, font=f22), 78), tc, font=f22, fill=a(CY, .95 * op))
        if (t * 1.6) % 1 < .55:
            d.ellipse([W - M - 92, 116, W - M - 78, 130], fill=a(RD, .95 * op))
        d.text((W - M - 68, 112), "REC", font=MONOB(18), fill=a(RD, .9 * op))
        d.line([M, 158, W - M, 158], fill=a(CY, .45 * op), width=2)
        hx = M + ((t * .38) % 1) * (W - 2 * M)      # destello que recorre la regla
        dg.line([int(hx / 2) - 40, 79, int(hx / 2) + 40, 79], fill=(int(60 * op), int(150 * op), int(170 * op)), width=2)

        # ---- corchetes de encuadre ----
        br = 4 * math.sin(t * 1.7)
        x0, y0, x1, y1 = M + br, 208 + br, W - M - br, H - 268 - br
        for (bx, by, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
            bracket(d, bx, by, sx, sy, 52, 3, a(CY, .8 * op))

        # ---- telemetria izquierda ----
        rows = [("O2",   f"{97.8 + math.sin(t*1.1)*0.6:.1f} %",  .97),
                ("GRAV", f"{0.81 + math.sin(t*0.7)*0.03:.2f} G", .78),
                ("TEMP", f"{21.4 + math.sin(t*0.9)*0.3:.1f} C",  .62),
                ("PRES", f"{101.1 + math.sin(t*1.4)*0.4:.1f} kPa", .88)]
        yy = 268
        for i, (lb, vl, fill) in enumerate(rows):
            ro = ease((t - .75 - i * .09) / .3) * op
            if ro <= .01:
                yy += 84; continue
            d.text((M, yy), lb, font=MONO(17), fill=a(CYD, .95 * ro))
            d.text((M, yy + 22), vl, font=MONOB(23), fill=a(WH, .95 * ro))
            bw = 176
            d.rectangle([M, yy + 54, M + bw, yy + 60], outline=a(CYD, .6 * ro), width=1)
            fw = int(bw * (fill + math.sin(t * 2 + i) * .015))
            d.rectangle([M, yy + 54, M + fw, yy + 60], fill=a(CY, .85 * ro))
            dg.rectangle([M // 2, (yy + 54) // 2, (M + fw) // 2, (yy + 60) // 2],
                         fill=(int(30 * ro), int(80 * ro), int(95 * ro)))
            yy += 84

        # ---- regla vertical derecha ----
        rx = W - M - 6
        off = (t * 46) % 26
        for i in range(-1, 26):
            ty = 268 + i * 26 + off
            if not (250 < ty < H - 300): continue
            lng = 26 if i % 5 == 0 else 12
            d.line([rx, ty, rx - lng, ty], fill=a(CY, (.75 if i % 5 == 0 else .4) * op), width=2)
        d.text((rx - 150, 240), "EJE Z", font=MONO(16), fill=a(CYD, .9 * op))

        # ---- barrido inferior ----
        by = H - 214
        pts = [(M + i, by + math.sin(i * .045 + t * 5.5) * 13 * (0.35 + 0.65 * abs(math.sin(i * .006 + t))) )
               for i in range(0, W - 2 * M, 4)]
        d.line(pts, fill=a(CY, .85 * op), width=2)
        dg.line([(int(p[0] / 2), int(p[1] / 2)) for p in pts], fill=(int(45 * op), int(120 * op), int(140 * op)), width=2)
        cap = "ESCANEO DE ENTORNO > OFICINA ORBITAL ESTABLE"
        n = int(max(0, (t - 1.0)) * 26)
        track(d, (M, by + 44), cap[:n], MONO(19), a(WH, .92 * op), 1.2)
        if n < len(cap) and (t * 6) % 1 < .5:
            d.rectangle([M + n * 12.5, by + 44, M + n * 12.5 + 9, by + 64], fill=a(CY, .9 * op))
        for i in range(14):                       # estado de modulos
            lit = (i * 7 + int(t * 3)) % 5 != 0
            c = a(CY, .85 * op) if lit else a(CYD, .32 * op)
            d.rectangle([M + i * 26, by + 84, M + i * 26 + 17, by + 92], fill=c)
        d.text((W - M - 160, by + 82), "SYS NOMINAL", font=MONO(16), fill=a(AM, .9 * op))

        # ---- reticula central / fijado de objetivo ----
        if 1.30 < t < 2.62:
            ro = ease((t - 1.30) / .28) * (1 - ease((t - 2.34) / .28))
            cx, cy_ = W // 2, 900
            dashed_circle(d, cx, cy_, 158, t * 1.1, a(CY, .85 * ro))
            dashed_circle(d, cx, cy_, 118, -t * 1.6, a(CYD, .7 * ro), 8, 14, 2)
            d.line([cx - 30, cy_, cx + 30, cy_], fill=a(CY, .8 * ro), width=2)
            d.line([cx, cy_ - 30, cx, cy_ + 30], fill=a(CY, .8 * ro), width=2)
            tx = "ANALIZANDO ENTORNO"
            f21 = MONOB(21)
            track(d, (cx - f21.getlength(tx) / 2 - 12, cy_ + 186), tx, f21, a(WH, .95 * ro), 1.6)
        if 2.44 < t < 3.34:
            ro = ease((t - 2.44) / .22) * (1 - ease((t - 3.10) / .24))
            k = ease((t - 2.44) / .45)
            bw2 = int(300 - 110 * k)
            cx, cy_ = W // 2, 900
            for (sx, sy) in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                bracket(d, cx + sx * bw2 // 2, cy_ + sy * bw2 // 2, -sx, -sy, 36, 4, a(AM, .95 * ro))
            tx = "OBJETO: ESTACION DE TRABAJO — VERIFICADO"
            f19 = MONO(19)
            d.text((cx - f19.getlength(tx) / 2, cy_ + bw2 // 2 + 26), tx, font=f19, fill=a(AM, .95 * ro))

        # ---- dron flotante ----
        for k, (amp, sp, sz, ph) in enumerate([(210, .55, 26, 0), (130, .82, 16, 2.1)]):
            dx = W * .5 + math.sin(t * sp + ph) * amp * 1.4
            dy = 1340 + math.cos(t * sp * .8 + ph) * amp * .35 + k * 120
            pts = [(dx + sz * math.cos(a_ + t * .9), dy + sz * math.sin(a_ + t * .9))
                   for a_ in [i * math.pi / 3 for i in range(6)]]
            d.polygon(pts, outline=a(CY, .8 * op), width=2)
            d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=a(WH, .95 * op))
            soft_dot(dg, dx / 2, dy / 2, 5, (120, 240, 255), .9 * op)

    # ---------------- arranque de sistemas ----------------
    if t < 1.25:
        f = 1 - ease(t / 1.15)
        d.rectangle([0, 0, W, H], fill=a((2, 8, 14), .88 * f))
        cx, cy_ = W // 2, H // 2
        tx = "INICIANDO SISTEMAS"
        fb = MONOB(30)
        track(d, (cx - (fb.getlength(tx) + 22 * 3.2) / 2, cy_ - 64), tx, fb, a(CY, .98 * f), 3.2)
        pw, p = 520, min(1, t / .95)
        d.rectangle([cx - pw // 2, cy_ + 4, cx + pw // 2, cy_ + 20], outline=a(CY, .8 * f), width=2)
        d.rectangle([cx - pw // 2, cy_ + 4, cx - pw // 2 + int(pw * p), cy_ + 20], fill=a(CY, .85 * f))
        pc = f"{int(p*100):3d}%"
        d.text((cx + pw // 2 + 16, cy_ + 0), pc, font=MONOB(22), fill=a(WH, .9 * f))
        for i in range(4):                                  # bandas de interferencia
            if rnd.random() < .5:
                by2 = rnd.uniform(0, H); hgt = rnd.uniform(4, 26)
                d.rectangle([0, by2, W, by2 + hgt], fill=a(CY, .1 * f))

    # ---------------- tarjeta final ----------------
    if t > 8.25:
        f = ease((t - 8.25) / .45)
        d.rectangle([0, 0, W, H], fill=a((2, 8, 14), .55 * f))
        cx, cy_ = W // 2, H // 2 - 40
        f64 = SANSB(64)
        track(d, (cx - (f64.getlength("AURORA-7") + 8 * 7) / 2, cy_ - 48), "AURORA-7", f64, a(WH, .98 * f), 8)
        d.line([cx - 190, cy_ + 44, cx + 190, cy_ + 44], fill=a(CY, .8 * f), width=2)
        f20 = MONO(20)
        tx = "OFICINA ORBITAL"
        track(d, (cx - (f20.getlength(tx) + 6 * 6) / 2, cy_ + 64), tx, f20, a(CY, .95 * f), 6)
        dg.line([cx // 2 - 95, (cy_ + 44) // 2, cx // 2 + 95, (cy_ + 44) // 2],
                fill=(int(50 * f), int(130 * f), int(150 * f)), width=2)

# ---------------------------------------------------------------- capa de brillo
def draw_glow(t, glow_s):
    dg = ImageDraw.Draw(glow_s)
    # motas en gravedad cero
    for p in PART:
        x = (p["x"] + t * p["sp"] * .35) % GW
        y = (p["y"] - t * p["sp"]) % GH + math.sin(t * .6 + p["ph"]) * 0
        x = (x + math.sin(t * .5 + p["ph"]) * p["wob"]) % GW
        b = p["br"] * (.6 + .4 * math.sin(t * 1.8 + p["ph"]))
        soft_dot(dg, x, y, p["r"], (150, 225, 255), b)
    # barrido de escaneo descendente
    sy = ((t * .40 + .15) % 1.0) * GH
    for i in range(-9, 10):
        f = (1 - abs(i) / 9.0) ** 2.2
        dg.line([0, sy + i * 3, GW, sy + i * 3], fill=(int(26 * f), int(78 * f), int(96 * f)), width=3)
    dg.line([0, sy, GW, sy], fill=(90, 205, 235), width=2)
    for gx in range(0, GW, 54):                       # rejilla revelada por el barrido
        dg.line([gx, sy - 26, gx, sy + 26], fill=(12, 40, 52), width=1)
    # fuga de luz superior (como una lampara de cubierta)
    for i in range(9, 0, -1):
        r = 40 + i * 26
        f = (1 - i / 9.0) * (.55 + .45 * math.sin(t * .9))
        dg.ellipse([GW * .22 - r, -40 - r, GW * .22 + r, -40 + r],
                   fill=(int(10 * f), int(34 * f), int(46 * f)))

# ---------------------------------------------------------------- bucle principal
for i in range(NF):
    t = i / FPS
    rnd.seed(1000 + i)
    hud    = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_s = Image.new("RGB",  (GW, GH), (0, 0, 0))
    draw_glow(t, glow_s)
    viewport(hud, glow_s, t)
    draw_hud(t, hud, glow_s)
    # el HUD tambien aporta luz: version desenfocada de su alfa hacia la capa aditiva
    ha = hud.resize((GW, GH), Image.BILINEAR)
    hg = Image.merge("RGB", [c.point(lambda v: int(v * .55)) for c in ha.convert("RGB").split()])
    hg = Image.composite(hg, Image.new("RGB", (GW, GH), (0, 0, 0)), ha.getchannel("A"))
    glow_s = Image.blend(glow_s, hg, 0.0) if False else Image.eval(
        Image.merge("RGB", [Image.blend(a_, b_, .5) for a_, b_ in zip(glow_s.split(), hg.split())]),
        lambda v: min(255, int(v * 2)))
    glow = glow_s.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    hud.save(f"{BASE}/hud/h_{i:04d}.png")
    glow.save(f"{BASE}/glow/g_{i:04d}.png")
    if i % 40 == 0:
        print("frame", i, "/", NF, flush=True)

# lineas de barrido estaticas para el pase final
sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ds = ImageDraw.Draw(sl)
for y in range(0, H, 4):
    ds.line([0, y, W, y], fill=(0, 0, 0, 26))
sl.save(f"{BASE}/scanlines.png")
print("OK", NF, "fotogramas")
