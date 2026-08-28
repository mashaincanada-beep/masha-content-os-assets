#!/usr/bin/env python3
"""Rasteriza emoji a PNG para poder pegarlos dentro de los subtitulos.

Pillow no sabe dibujar las fuentes de emoji modernas (Noto Color Emoji viene en
formato COLR/SVG), asi que los emoji se cachean como PNG en fuentes/emoji/ y el
renderizador de subtitulos solo pega imagenes.

    python3 emoji_cache.py "⚠️" "🇨🇦" "👀"        # cachea esos emoji
    python3 emoji_cache.py --de-guion guion.json  # cachea los del guion

Necesita fonttools, uharfbuzz y cairosvg (pip install fonttools uharfbuzz cairosvg).
Si en tu maquina hay una fuente de emoji que Pillow si sabe dibujar (en macOS la
hay: Apple Color Emoji), subtitulos.py la usa sola y este paso sobra.
"""

import argparse
import io
import json
import os
import re
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUENTES = os.path.join(RAIZ, "fuentes")
CACHE = os.path.join(FUENTES, "emoji")
FUENTE_EMOJI = os.path.join(FUENTES, "NotoColorEmoji.ttf")

LADO = 256  # los PNG se cachean a este tamano y luego se escalan hacia abajo


def nombre_cache(cluster):
    return "-".join("%x" % ord(c) for c in cluster) + ".png"


def ruta_cache(cluster):
    return os.path.join(CACHE, nombre_cache(cluster))


def _fuente(cache={}):
    """Abre la fuente una sola vez: son 25 MB y parsearla no es gratis."""
    if "hb" in cache:
        return cache["hb"], cache["tt"]
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont

    if not os.path.exists(FUENTE_EMOJI):
        raise SystemExit("falta %s: corre fuentes/descargar.sh" % FUENTE_EMOJI)
    cache["hb"] = hb.Font(hb.Face(hb.Blob.from_file_path(FUENTE_EMOJI)))
    cache["tt"] = TTFont(FUENTE_EMOJI, lazy=True)
    return cache["hb"], cache["tt"]


def _troceado(doc, cache={}):
    """Separa un documento SVG de la fuente en cabecera, defs y el resto.

    Noto mete 2737 emoji dentro de un unico documento de 14 MB. Rasterizarlo
    entero cuelga el proceso, asi que hay que recortar el grupo del glifo que
    interesa y llevarse solo los <defs> (que no se dibujan si nadie los usa).
    """
    clave = id(doc)
    if clave not in cache:
        ini = doc.index("<defs>")
        fin = doc.index("</defs>") + len("</defs>")
        cache[clave] = (doc[:ini], doc[ini:fin])
    return cache[clave]


def _svg_del_glifo(doc, gid):
    cabecera, defs = _troceado(doc)
    marca = '<g id="glyph%d">' % gid
    ini = doc.find(marca)
    if ini < 0:
        return None
    siguiente = doc.find('<g id="glyph', ini + len(marca))
    fin = siguiente if siguiente > 0 else doc.rindex("</svg>")
    # Caja generosa: los dibujos de Noto se salen del cuadratin por los cuatro
    # lados. Luego se recorta al contenido real.
    caja = 'viewBox="-256 -1280 1536 1536" width="%d" height="%d" ' % (LADO, LADO)
    return (cabecera.replace("<svg ", "<svg " + caja, 1)
            + defs + doc[ini:fin] + "</svg>")


def rasterizar(cluster):
    """Saca el dibujo del emoji de la tabla SVG de la fuente y lo pasa a PNG."""
    import cairosvg
    import uharfbuzz as hb

    fuente, tt = _fuente()
    buf = hb.Buffer()
    buf.add_str(cluster)
    buf.guess_segment_properties()
    hb.shape(fuente, buf)
    glifos = [i.codepoint for i in buf.glyph_infos]

    if "SVG " not in tt:
        raise SystemExit("la fuente de emoji no trae tabla SVG")
    docs = tt["SVG "].docList

    piezas = []
    for gid in glifos:
        doc = next((d for d, a, b in docs if a <= gid <= b), None)
        if doc is None:
            continue
        svg = _svg_del_glifo(doc, gid)
        if not svg:
            continue
        png = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                               output_width=LADO, output_height=LADO)
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        caja = img.getbbox()
        if caja:
            piezas.append(img.crop(caja))

    if not piezas:
        return None
    if len(piezas) == 1:
        return piezas[0]
    # Una secuencia que la fuente no resuelve en un solo dibujo: se ponen los
    # dibujos uno detras de otro, que es lo que hace el sistema.
    alto = max(p.height for p in piezas)
    hueco = int(alto * 0.06)
    ancho = sum(p.width for p in piezas) + hueco * (len(piezas) - 1)
    junto = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    x = 0
    for p in piezas:
        junto.alpha_composite(p, (x, (alto - p.height) // 2))
        x += p.width + hueco
    return junto


def asegurar(cluster, verboso=True):
    """Devuelve la ruta del PNG del emoji, generandolo si hace falta."""
    ruta = ruta_cache(cluster)
    if os.path.exists(ruta):
        return ruta
    try:
        img = rasterizar(cluster)
    except ImportError as exc:
        if verboso:
            print("  aviso: no puedo rasterizar %s (%s)" % (cluster, exc))
        return None
    if img is None:
        if verboso:
            print("  aviso: la fuente no tiene dibujo para %s" % cluster)
        return None
    os.makedirs(CACHE, exist_ok=True)
    img.save(ruta)
    if verboso:
        print("  %s -> %s (%dx%d)" % (cluster, nombre_cache(cluster), *img.size))
    return ruta


def emoji_de_guion(ruta):
    from subtitulos import agrupar_emoji, es_emoji

    with open(ruta, encoding="utf-8") as fh:
        guion = json.load(fh)
    vistos = []
    for grupo in guion["grupos"]:
        for clave in ("l1", "l2"):
            texto = (grupo.get(clave) or {}).get("texto", "")
            for cl in agrupar_emoji(texto):
                if es_emoji(cl[0]) and cl not in vistos:
                    vistos.append(cl)
    return vistos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("emoji", nargs="*")
    ap.add_argument("--de-guion")
    args = ap.parse_args()

    sys.path.insert(0, AQUI)
    objetivos = list(args.emoji)
    if args.de_guion:
        objetivos += emoji_de_guion(args.de_guion)
    if not objetivos:
        print(__doc__)
        return 1
    for cluster in objetivos:
        asegurar(cluster)
    return 0


if __name__ == "__main__":
    sys.exit(main())
