#!/usr/bin/env python3
"""Prepara las fotos que van dentro de VID-002 a partir de los originales.

Cada hueco necesita un recorte distinto, asi que el recorte se hace aqui y no a
ojo: la tarjeta del reel solo escala y centra, y si le entra la foto entera
recorta por donde no toca.

    python3 preparar_fotos.py

Lee de originales/ y escribe gafas.png, valor_gafas.png y seguro_salud.png.
"""

import os
import sys

from PIL import Image, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(AQUI, "originales")
LADO = 900
CREMA = (242, 234, 218)


def recorte(nombre, x0, y0, x1, y1):
    im = Image.open(os.path.join(ORIG, nombre)).convert("RGB")
    W, H = im.size
    return im.crop((int(W * x0), int(H * y0), int(W * x1), int(H * y1)))


def sobre_crema(img, margen=0.055, alto_util=1.0):
    """Mete la imagen entera dentro de un cuadrado crema, sin recortar nada.

    Para documentos apaisados: si se dejara recortar por la tarjeta se perderia
    justo lo que se quiere ensenar. alto_util deja libre la franja de abajo, que
    es donde la tarjeta pone el pie de foto.
    """
    lienzo = Image.new("RGB", (LADO, LADO), CREMA)
    util = int(LADO * alto_util)
    hueco_w = int(LADO * (1 - 2 * margen))
    hueco_h = int(util * (1 - 2 * margen))
    copia = img.copy()
    copia.thumbnail((hueco_w, hueco_h), Image.LANCZOS)
    lienzo.paste(copia, ((LADO - copia.width) // 2, (util - copia.height) // 2))
    return lienzo


def difuminar(img, x0, y0, x1, y1, radio=14):
    """Tapa una zona con desenfoque. Los datos personales no se publican."""
    W, H = img.size
    caja = (int(W * x0), int(H * y0), int(W * x1), int(H * y1))
    img.paste(img.crop(caja).filter(ImageFilter.GaussianBlur(radio)), caja)
    return img


def main():
    if not os.path.isdir(ORIG):
        raise SystemExit("falta la carpeta %s con los originales" % ORIG)

    # 1. La hija con las gafas nuevas. Recorte a cara y hombros.
    recorte("hija_gafas.jpg", 0.06, 0.42, 0.52, 0.66).save(
        os.path.join(AQUI, "gafas.png"))

    # 2. Factura de ejemplo: solo el bloque de cobertura y el sello del 100 %.
    #    Fuera quedan RFC, folio fiscal, nombres y direcciones, que ni son
    #    reales ni pintan nada en pantalla.
    sobre_crema(recorte("factura_ejemplo.png", 0.50, 0.60, 0.98, 0.94),
                alto_util=0.80).save(os.path.join(AQUI, "valor_gafas.png"))

    # 3. Tarjeta de ejemplo: entera sobre fondo crema, con los datos del
    #    titular difuminados.
    tarjeta = Image.open(os.path.join(ORIG, "tarjeta_ejemplo.png")).convert("RGB")
    tarjeta = difuminar(tarjeta, 0.52, 0.355, 0.80, 0.53)
    sobre_crema(tarjeta, alto_util=0.80).save(
        os.path.join(AQUI, "seguro_salud.png"))

    for n in ("gafas.png", "valor_gafas.png", "seguro_salud.png"):
        im = Image.open(os.path.join(AQUI, n))
        print("  %-18s %s" % (n, im.size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
