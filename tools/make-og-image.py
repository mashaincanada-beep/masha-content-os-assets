"""Genera la imagen Open Graph (1200x630) del Paquete de Optimizacion.

Identidad Masha in Canada: paleta y logo tomados de los assets reales del
repositorio masha-content-os-assets (CID-009).
"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
FONTS = os.environ.get("POPPINS_DIR", "fonts")
OUT = os.path.join(ASSETS, "og", "paquete-de-optimizacion-og.jpg")

W, H = 1200, 630
SS = 2  # supersampling

BG = (234, 246, 253)
MINT = (178, 230, 230)
CREAM = (238, 241, 213)
PEACH = (238, 209, 188)
NAVY = (8, 36, 58)
BLUE = (14, 165, 233)
SLATE = (62, 95, 115)
RED = (216, 26, 54)

font = lambda w, s: ImageFont.truetype(f"{FONTS}/Poppins-{w}.ttf", s * SS)


def extract_logo():
    """Recorta el logo MIC real del creativo y le quita el fondo por saturacion."""
    src = Image.open(f"{ASSETS}/CID-009/optimization_package.jpeg").convert("RGB")
    crop = src.crop((300, 445, 790, 755))
    out = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    sp, op = crop.load(), out.load()
    for y in range(crop.size[1]):
        for x in range(crop.size[0]):
            r, g, b = sp[x, y]
            mx, mn = max(r, g, b), min(r, g, b)
            sat = 0 if mx == 0 else (mx - mn) / mx
            a = int(max(0.0, min(1.0, (sat - 0.22) / 0.20)) * 255)
            if a:
                op[x, y] = (r, g, b, a)
    return out.crop(out.getbbox())


def circle(layer, cx, cy, r, color, alpha=255):
    d = ImageDraw.Draw(layer, "RGBA")
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (alpha,))


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        probe = (cur + " " + word).strip()
        if draw.textlength(probe, font=fnt) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


img = Image.new("RGB", (W * SS, H * SS), BG)
draw = ImageDraw.Draw(img)

# Formas decorativas de la identidad (mismas del sistema de contenidos)
circle(img, 40 * SS, 30 * SS, 210 * SS, MINT, 150)
circle(img, 1195 * SS, 120 * SS, 165 * SS, CREAM, 200)
circle(img, 1140 * SS, 620 * SS, 190 * SS, PEACH, 165)

M = 72 * SS  # margen izquierdo
TEXT_W = 720 * SS

# Pill: PAQUETE DE OPTIMIZACION
pill_font = font("700", 19)
label = "PAQUETE DE OPTIMIZACIÓN"
pad_x, pad_y = 26 * SS, 13 * SS
tw = draw.textlength(label, font=pill_font)
ph = 46 * SS
draw.rounded_rectangle((M, 62 * SS, M + tw + pad_x * 2, 62 * SS + ph),
                       radius=ph // 2, fill=BLUE)
draw.text((M + pad_x, 62 * SS + ph / 2), label, font=pill_font,
          fill=(255, 255, 255), anchor="lm")

# Titular
head_font = font("800", 52)
head = "Tu camino a una oferta laboral en Canadá empieza aquí"
y = 142 * SS
for line in wrap(draw, head, head_font, TEXT_W):
    draw.text((M, y), line, font=head_font, fill=NAVY)
    y += 64 * SS

# Bajada
sub_font = font("400", 25)
sub = "Currículum, LinkedIn y estrategia de aplicación optimizados para el mercado canadiense."
y += 24 * SS
for line in wrap(draw, sub, sub_font, TEXT_W):
    draw.text((M, y), line, font=sub_font, fill=SLATE)
    y += 36 * SS

# Dominio
url_font = font("700", 22)
draw.text((M, 548 * SS), "www.mashaincanada.com", font=url_font, fill=RED)

# Logo MIC real, abajo a la derecha
logo = extract_logo()
lw = 250 * SS
logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
img.paste(logo, (W * SS - lw - 72 * SS, 470 * SS - logo.height // 2), logo)

img = img.resize((W, H), Image.LANCZOS)
img.save(OUT, quality=90, optimize=True, progressive=True, subsampling=0)
print("OK", img.size)
