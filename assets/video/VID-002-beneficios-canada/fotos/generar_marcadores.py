#!/usr/bin/env python3
"""Genera las imagenes provisionales de las inserciones de VID-002.

Son marcadores, no fotos: desde este entorno no hay acceso a ningun banco de
imagenes, asi que cada hueco lleva una tarjeta de marca con el icono del tema.
Sirven para ver el ritmo y oir las burbujas en el sitio correcto. Cuando lleguen
las fotos de verdad basta con reemplazar el archivo: el guion apunta al nombre.

    python3 generar_marcadores.py
"""

import os
import sys

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.join(AQUI, "..", "..", "estilo-reels", "pipeline")
sys.path.insert(0, os.path.abspath(PIPELINE))

from subtitulos import imagen_emoji  # noqa: E402

LADO = 900
CREMA = (242, 234, 218)
PAPEL = (250, 250, 242)

MARCADORES = [
    ("canada.png", "🇨🇦"),
    ("seguro_salud.png", "🩺"),
    ("oftalmologo.png", "👁️"),
    ("gafas.png", "👓"),
    ("valor_gafas.png", "🧾"),
    ("massage.png", "💆"),
    ("beneficios.png", "📋"),
]


def marcador(emoji):
    img = Image.new("RGB", (LADO, LADO), CREMA)
    d = ImageDraw.Draw(img)
    margen = 70
    d.rounded_rectangle([margen, margen, LADO - margen, LADO - margen],
                        48, fill=PAPEL)
    icono = imagen_emoji(emoji, 380)
    if icono:
        img.paste(icono, ((LADO - icono.width) // 2,
                          (LADO - icono.height) // 2 - 20), icono)
    return img


def main():
    for nombre, emoji in MARCADORES:
        ruta = os.path.join(AQUI, nombre)
        marcador(emoji).save(ruta)
        print("  %s  %s" % (emoji, nombre))
    print("%d marcadores en %s" % (len(MARCADORES), AQUI))
    return 0


if __name__ == "__main__":
    sys.exit(main())
