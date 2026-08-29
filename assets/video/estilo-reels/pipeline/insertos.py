#!/usr/bin/env python3
"""Dibuja las fotos que entran dentro del reel como tarjeta con esquinas redondas.

La foto no ocupa el cuadro entero: entra como una tarjeta a la derecha, donde el
encuadre de estos reels deja fondo libre y no tapa la cara. Lleva marco claro,
sombra y, si el guion se lo pone, un pie de foto.

Se usa como modulo desde subtitulos.py; suelto sirve para previsualizar una:

    python3 insertos.py foto.jpg vista.png --pie "Gafas nuevas"
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def _cubrir(img, ancho, alto):
    """Escala y recorta la foto para llenar la tarjeta sin deformarla."""
    escala = max(ancho / img.width, alto / img.height)
    nuevo = img.resize((max(1, int(img.width * escala)),
                        max(1, int(img.height * escala))), Image.LANCZOS)
    x = (nuevo.width - ancho) // 2
    y = (nuevo.height - alto) // 2
    return nuevo.crop((x, y, x + ancho, y + alto))


def _mascara_redonda(ancho, alto, radio):
    m = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ancho - 1, alto - 1], radio, fill=255)
    return m


def tarjeta(ruta_imagen, preset, pie=None):
    """Compone la tarjeta completa (foto + marco + pie) sobre el lienzo del reel."""
    cfg = preset["inserto"]
    W, H = preset["lienzo"]["ancho"], preset["lienzo"]["alto"]
    ancho = int(round(W * cfg["ancho_rel"]))
    alto = int(round(H * cfg["alto_rel"]))
    x0 = int(round(W * cfg["x_rel"]))
    y0 = int(round(H * cfg["y_rel"]))
    borde = cfg["borde"]
    radio = cfg["radio"]

    foto = Image.open(ruta_imagen).convert("RGB")
    interior = _cubrir(foto, ancho - 2 * borde, alto - 2 * borde)

    tarjeta_img = Image.new("RGBA", (ancho, alto), cfg["color_borde"])
    tarjeta_img.paste(interior, (borde, borde))
    tarjeta_img.putalpha(_mascara_redonda(ancho, alto, radio))
    interior_mask = _mascara_redonda(ancho - 2 * borde, alto - 2 * borde,
                                     max(1, radio - borde // 2))
    recorte = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    recorte.paste(interior, (borde, borde), interior_mask)
    base = Image.new("RGBA", (ancho, alto), cfg["color_borde"])
    base.putalpha(_mascara_redonda(ancho, alto, radio))
    base.alpha_composite(recorte)

    if pie:
        base = _pie_de_foto(base, pie, preset, radio)

    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = cfg["sombra"]
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    negro = Image.new("RGBA", base.size, (0, 0, 0, 255))
    negro.putalpha(base.getchannel("A"))
    sombra.alpha_composite(negro, (x0 + int(s["dx"]), y0 + int(s["dy"])))
    sombra = sombra.filter(ImageFilter.GaussianBlur(s["desenfoque"]))
    sombra.putalpha(sombra.getchannel("A").point(
        lambda v: int(v * s["opacidad"])))
    lienzo.alpha_composite(sombra)
    lienzo.alpha_composite(base, (x0, y0))
    return lienzo


def _pie_de_foto(base, texto, preset, radio):
    """Franja de color al pie de la tarjeta con una o dos palabras."""
    sys.path.insert(0, AQUI)
    from subtitulos import Registro, dibujar_tramos, medir_linea

    cfg = preset["inserto"]
    ancho, alto = base.size
    spec = dict(preset["tipografia"]["golpe"])
    spec["tamano"] = cfg["pie_tamano"]
    reg = Registro(spec)
    alto_franja = int(cfg["pie_tamano"] * 1.7)

    franja = Image.new("RGBA", (ancho, alto_franja),
                       preset["colores"][cfg["pie_fondo"]])
    dib = ImageDraw.Draw(franja)
    anchura, medidos = medir_linea(texto, reg, reg.alto_mayuscula)
    if anchura > ancho * 0.88:
        reg = Registro(spec, ancho * 0.88 / anchura)
        anchura, medidos = medir_linea(texto, reg, reg.alto_mayuscula)
    baseline = alto_franja / 2.0 + reg.alto_mayuscula / 2.0
    dibujar_tramos(dib, franja, medidos, reg, (ancho - anchura) / 2.0, baseline,
                   preset["colores"][cfg["pie_texto"]], "#000000", 0,
                   reg.alto_mayuscula)

    # La franja tiene que respetar las esquinas redondas de abajo.
    recorte = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    recorte.paste(franja, (0, alto - alto_franja))
    recorte.putalpha(Image.composite(
        recorte.getchannel("A"),
        Image.new("L", (ancho, alto), 0),
        _mascara_redonda(ancho, alto, radio)))
    base.alpha_composite(recorte)
    return base


def escalar_tarjeta(img, preset, k):
    """Escala la tarjeta alrededor de su propio centro, para el rebote de entrada."""
    if abs(k - 1.0) < 1e-6:
        return img
    cfg = preset["inserto"]
    W, H = img.size
    cx = W * (cfg["x_rel"] + cfg["ancho_rel"] / 2.0)
    cy = H * (cfg["y_rel"] + cfg["alto_rel"] / 2.0)
    escalada = img.resize((max(1, int(W * k)), max(1, int(H * k))), Image.LANCZOS)
    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lienzo.paste(escalada, (int(round(cx - cx * k)), int(round(cy - cy * k))),
                 escalada)
    return lienzo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imagen")
    ap.add_argument("salida")
    ap.add_argument("--pie")
    ap.add_argument("--preset")
    args = ap.parse_args()
    sys.path.insert(0, AQUI)
    from subtitulos import cargar_preset

    preset = cargar_preset(args.preset)
    tarjeta(args.imagen, preset, args.pie).save(args.salida)
    print("listo:", args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
