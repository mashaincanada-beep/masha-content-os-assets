#!/usr/bin/env python3
"""Dibuja los subtitulos del estilo de reels como PNG con transparencia.

Un PNG por grupo de subtitulo (no por fotograma): el estilo cambia de golpe,
sin animacion de entrada, asi que cada grupo es una imagen fija que montar.py
superpone durante su intervalo.

    python3 subtitulos.py guion.json out/subs

Escribe out/subs/cap_000.png ... y out/subs/grupos.json con los tiempos.
"""

import json
import os
import re
import shutil
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUENTES = os.path.join(RAIZ, "fuentes")

# Rangos que se dibujan con la fuente de emoji en vez de con la tipografia de texto.
RANGOS_EMOJI = [
    (0x1F000, 0x1FAFF),
    (0x2190, 0x2BFF),
    (0x2600, 0x27BF),
    (0xFE00, 0xFE0F),
    (0x1F1E6, 0x1F1FF),
    (0x200D, 0x200D),
    (0x20E3, 0x20E3),
]

# Cuerpo al que se piden las fuentes de emoji de mapa de bits del sistema: solo
# traen un tamano de dibujo y pedir otro devuelve un hueco vacio.
CUERPO_EMOJI_NATIVO = 109


def es_emoji(car):
    cp = ord(car)
    return any(a <= cp <= b for a, b in RANGOS_EMOJI)


def agrupar_emoji(texto):
    """Parte el texto en unidades dibujables: un emoji completo cuenta como una.

    Junta lo que va suelto en codigos distintos pero se ve como un solo dibujo:
    banderas (dos indicadores regionales), secuencias con ZWJ, tonos de piel y
    el selector de presentacion FE0F.
    """
    unidades, i = [], 0
    while i < len(texto):
        car = texto[i]
        if not es_emoji(car):
            unidades.append(car)
            i += 1
            continue
        cluster, i = car, i + 1
        if 0x1F1E6 <= ord(car) <= 0x1F1FF and i < len(texto) \
                and 0x1F1E6 <= ord(texto[i]) <= 0x1F1FF:
            cluster += texto[i]
            i += 1
        while i < len(texto):
            cp = ord(texto[i])
            if cp in (0xFE0F, 0x20E3) or 0x1F3FB <= cp <= 0x1F3FF:
                cluster += texto[i]
                i += 1
            elif cp == 0x200D and i + 1 < len(texto):
                cluster += texto[i:i + 2]
                i += 2
            else:
                break
        unidades.append(cluster)
    return unidades


def cargar_preset(ruta=None, paleta=None):
    ruta = ruta or os.path.join(RAIZ, "preset.json")
    with open(ruta, encoding="utf-8") as fh:
        preset = json.load(fh)
    elegida = paleta or preset.get("paleta", "mic")
    if elegida not in preset["paletas"]:
        raise SystemExit("paleta desconocida: %s (hay %s)"
                         % (elegida, ", ".join(preset["paletas"])))
    preset["colores"] = preset["paletas"][elegida]
    preset["paleta"] = elegida
    return preset


def fuente(nombre, cuerpo):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), cuerpo)


def trocear(texto):
    """Parte el texto en tramos (clase, contenido).

    clase es 'redonda', 'cursiva' o 'emoji'. La cursiva se marca con *asteriscos*.
    """
    tramos = []
    for parte in re.split(r"(\*[^*]+\*)", texto):
        if not parte:
            continue
        cursiva = parte.startswith("*") and parte.endswith("*") and len(parte) > 2
        cuerpo = parte[1:-1] if cursiva else parte
        clase_texto = "cursiva" if cursiva else "redonda"
        actual, buffer = None, ""
        for car in cuerpo:
            clase = "emoji" if es_emoji(car) else clase_texto
            if clase != actual and buffer:
                tramos.append((actual, buffer))
                buffer = ""
            actual, buffer = clase, buffer + car
        if buffer:
            tramos.append((actual, buffer))
    return [(c, t) for c, t in tramos if t.strip() or c != "emoji"]


class Registro:
    """Una de las dos familias del sistema: apoyo (linea 1) o golpe (linea 2)."""

    def __init__(self, spec, escala=1.0):
        self.cuerpo = int(round(spec["tamano"] * escala))
        self.tracking = spec.get("tracking", 0) * escala
        self.mayusculas = spec.get("mayusculas", False)
        self.redonda = fuente(spec["fuente"], self.cuerpo)
        self.cursiva = fuente(spec.get("cursiva", spec["fuente"]), self.cuerpo)

    def tipo(self, clase):
        return self.cursiva if clase == "cursiva" else self.redonda

    @property
    def alto_mayuscula(self):
        caja = self.redonda.getbbox("H")
        return caja[3] - caja[1]


FUENTES_EMOJI_SISTEMA = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",          # macOS
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",    # Linux con Noto CBDT
    "C:/Windows/Fonts/seguiemj.ttf",                        # Windows
]


def fuente_emoji_sistema(cache={}):
    """Una fuente de emoji que Pillow si sepa dibujar, si es que hay alguna."""
    if "f" in cache:
        return cache["f"]
    cache["f"] = None
    for ruta in FUENTES_EMOJI_SISTEMA:
        if not os.path.exists(ruta):
            continue
        try:
            tipo = ImageFont.truetype(ruta, CUERPO_EMOJI_NATIVO)
            prueba = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            ImageDraw.Draw(prueba).text((0, 0), "\U0001F600", font=tipo,
                                        embedded_color=True)
            if prueba.getbbox():
                cache["f"] = tipo
                break
        except Exception:
            continue
    return cache["f"]


def imagen_emoji(cluster, alto, cache={}):
    """Devuelve el emoji rasterizado a la altura pedida (RGBA), o None.

    Primero mira el PNG cacheado en fuentes/emoji/, luego una fuente de color del
    sistema y, como ultimo recurso, intenta generar el PNG desde la tabla SVG de
    Noto Color Emoji. Si no sale nada, el subtitulo se dibuja sin el emoji.
    """
    clave = (cluster, alto)
    if clave in cache:
        return cache[clave]

    base = None
    ruta = os.path.join(FUENTES, "emoji",
                        "-".join("%x" % ord(c) for c in cluster) + ".png")
    if os.path.exists(ruta):
        base = Image.open(ruta).convert("RGBA")
    else:
        tipo = fuente_emoji_sistema()
        if tipo is not None:
            lienzo = Image.new("RGBA", (CUERPO_EMOJI_NATIVO * 3,) * 2, (0, 0, 0, 0))
            try:
                ImageDraw.Draw(lienzo).text((0, 0), cluster, font=tipo,
                                            embedded_color=True)
                caja = lienzo.getbbox()
                base = lienzo.crop(caja) if caja else None
            except Exception:
                base = None
        if base is None:
            try:
                sys.path.insert(0, AQUI)
                import emoji_cache

                generado = emoji_cache.asegurar(cluster, verboso=False)
                if generado:
                    base = Image.open(generado).convert("RGBA")
            except Exception:
                base = None

    if base is None:
        if cluster not in _avisados:
            _avisados.add(cluster)
            print("  aviso: no hay dibujo para el emoji %s, va sin el" % cluster)
        cache[clave] = None
        return None

    escala = alto / base.height
    salida = base.resize(
        (max(1, int(base.width * escala)), max(1, alto)), Image.LANCZOS
    )
    cache[clave] = salida
    return salida


_avisados = set()


def medir_linea(texto, reg, alto_emoji):
    """Ancho total en px y lista de tramos ya medidos."""
    medidos, ancho = [], 0.0
    lienzo = Image.new("RGBA", (8, 8))
    dib = ImageDraw.Draw(lienzo)
    for clase, contenido in trocear(texto):
        if clase == "emoji":
            w = 0
            for cluster in agrupar_emoji(contenido):
                img = imagen_emoji(cluster, alto_emoji)
                if img:
                    w += img.width + int(alto_emoji * 0.14)
            medidos.append((clase, contenido, w))
            ancho += w
        else:
            visible = contenido.upper() if reg.mayusculas else contenido
            w = dib.textlength(visible, font=reg.tipo(clase))
            w += reg.tracking * len(visible)
            medidos.append((clase, visible, w))
            ancho += w
    return ancho, medidos


def dibujar_tramos(dib, lienzo, medidos, reg, x, baseline, relleno, contorno, grosor,
                   alto_emoji, solo_contorno=False):
    for clase, contenido, w in medidos:
        if clase == "emoji":
            for cluster in agrupar_emoji(contenido):
                img = imagen_emoji(cluster, alto_emoji)
                if not img:
                    continue
                y = int(baseline - img.height * 0.86)
                if solo_contorno:
                    silueta = Image.new("RGBA", img.size, contorno)
                    silueta.putalpha(img.getchannel("A"))
                    lienzo.alpha_composite(silueta, (int(x), y))
                else:
                    lienzo.alpha_composite(img, (int(x), y))
                x += img.width + int(alto_emoji * 0.14)
            continue
        tipo = reg.tipo(clase)
        if reg.tracking:
            for car in contenido:
                if solo_contorno:
                    dib.text((x, baseline), car, font=tipo, fill=contorno,
                             anchor="ls", stroke_width=grosor, stroke_fill=contorno)
                else:
                    dib.text((x, baseline), car, font=tipo, fill=relleno, anchor="ls")
                x += dib.textlength(car, font=tipo) + reg.tracking
        else:
            if solo_contorno:
                dib.text((x, baseline), contenido, font=tipo, fill=contorno,
                         anchor="ls", stroke_width=grosor, stroke_fill=contorno)
            else:
                dib.text((x, baseline), contenido, font=tipo, fill=relleno, anchor="ls")
            x += w
    return x


def dibujar_grupo(grupo, preset):
    """Compone un grupo de subtitulo completo sobre un lienzo transparente."""
    W = preset["lienzo"]["ancho"]
    H = preset["lienzo"]["alto"]
    ancho_max = W * preset["bloque"]["ancho_max_rel"]
    colores = preset["colores"]
    contorno = preset["contorno"]["color"]
    grosor = preset["contorno"]["grosor"]

    # El registro sale de la ranura del guion (l1 = apoyo, l2 = golpe), no del
    # orden: un grupo que solo trae l2 sigue yendo en la condensada.
    lineas = [(clave, grupo[clave]) for clave in ("l1", "l2")
              if grupo.get(clave) and grupo[clave].get("texto")]
    if not lineas:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def spec_de(clave, linea):
        nombre = linea.get("estilo") or ("apoyo" if clave == "l1" else "golpe")
        return preset["tipografia"][nombre]

    # Una sola escala para todo el grupo: si algo no cabe, encoge el bloque entero.
    escala = 1.0
    for _ in range(24):
        regs, medidas, cabe = [], [], True
        for clave, linea in lineas:
            reg = Registro(spec_de(clave, linea), escala)
            alto_emoji = int(reg.alto_mayuscula * preset["emoji"]["alto_rel"])
            ancho, medidos = medir_linea(linea["texto"], reg, alto_emoji)
            regs.append((reg, alto_emoji))
            medidas.append((ancho, medidos))
            if ancho > ancho_max:
                cabe = False
        if cabe:
            break
        escala *= 0.96

    interlineado = preset["bloque"]["interlineado_px"] * escala
    centro_y = H * preset["bloque"]["centro_y_rel"]

    if len(lineas) == 2:
        alto_may_1 = regs[0][0].alto_mayuscula
        base1 = centro_y - (interlineado - alto_may_1) / 2.0
        baselines = [base1, base1 + interlineado]
    else:
        baselines = [centro_y + regs[0][0].alto_mayuscula / 2.0]

    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    capa_contorno = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dib_contorno = ImageDraw.Draw(capa_contorno)

    # Paso 1: todo el bloque en negro con contorno, para que ningun tramo pise
    # el relleno del vecino.
    for (reg, alto_emoji), (ancho, medidos), baseline in zip(regs, medidas, baselines):
        x = (W - ancho) / 2.0
        dibujar_tramos(dib_contorno, capa_contorno, medidos, reg, x, baseline,
                       None, contorno, grosor, alto_emoji, solo_contorno=True)

    # Sombra: la misma silueta, desenfocada y desplazada.
    s = preset["sombra"]
    sombra = capa_contorno.filter(ImageFilter.GaussianBlur(s["desenfoque"]))
    alfa = sombra.getchannel("A").point(lambda v: int(v * s["opacidad"]))
    sombra.putalpha(alfa)
    lienzo.alpha_composite(sombra, (int(s["dx"]), int(s["dy"])))
    lienzo.alpha_composite(capa_contorno)

    # Paso 2: los rellenos de color encima.
    dib = ImageDraw.Draw(lienzo)
    for i, ((reg, alto_emoji), (ancho, medidos), baseline) in enumerate(
        zip(regs, medidas, baselines)
    ):
        color = colores[lineas[i][1].get("color", "blanco")]
        x = (W - ancho) / 2.0
        dibujar_tramos(dib, lienzo, medidos, reg, x, baseline,
                       color, contorno, grosor, alto_emoji)
    return lienzo


def escalar_bloque(img, preset, k):
    """Escala la imagen alrededor del centro del bloque de subtitulos.

    El bloque tiene que crecer desde su propio centro, no desde el del cuadro,
    o el rebote de entrada se ve desplazado.
    """
    if abs(k - 1.0) < 1e-6:
        return img
    W, H = img.size
    cx, cy = W / 2.0, H * preset["bloque"]["centro_y_rel"]
    escalada = img.resize((max(1, int(W * k)), max(1, int(H * k))), Image.LANCZOS)
    lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # paste admite coordenadas negativas y recorta lo que se sale.
    lienzo.paste(escalada, (int(round(cx - cx * k)), int(round(cy - cy * k))), escalada)
    return lienzo


def _activo_y_fase(elementos, n, fps, escalas, por_fase):
    """Que elemento esta en pantalla en el fotograma n, y en que fase del rebote."""
    t = n / float(fps)
    indice = next((i for i, e in enumerate(elementos)
                   if float(e["in"]) <= t < float(e["out"])), None)
    if indice is None:
        return None, None
    desde = n - int(round(float(elementos[indice]["in"]) * fps))
    return indice, min(max(0, desde) // por_fase, len(escalas))


def escribir_secuencia(guion, preset, destino, animacion=True, base_fotos=None):
    """Escribe la secuencia completa de PNG con transparencia, uno por fotograma.

    Lleva los subtitulos y las fotos insertadas en la misma capa: asi ffmpeg
    recibe una sola entrada en vez de un overlay por elemento, y es lo que
    permite animar las entradas. Los fotogramas que repiten imagen se enlazan en
    duro en vez de volver a escribirse.
    """
    sys.path.insert(0, AQUI)
    import insertos as mod_insertos

    fps = preset["lienzo"]["fps"]
    W, H = preset["lienzo"]["ancho"], preset["lienzo"]["alto"]
    grupos = guion["grupos"]
    fotos = guion.get("insertos", [])
    base_fotos = base_fotos or os.path.dirname(os.path.abspath(destino))

    esc_sub = preset["animacion"]["escalas"] if animacion else []
    fase_sub = max(1, int(preset["animacion"]["fotogramas"]))
    esc_ins = preset["inserto"]["escalas"] if animacion else []
    fase_ins = max(1, int(preset["inserto"]["fotogramas"]))

    os.makedirs(destino, exist_ok=True)
    fin = max([float(g["out"]) for g in grupos]
              + [float(f["out"]) for f in fotos])
    total = int(round(fin * fps)) + 1
    capas_sub, capas_ins, hechos = {}, {}, {}

    def capa_subtitulo(clave):
        if clave not in capas_sub:
            indice, fase = clave
            img = dibujar_grupo(grupos[indice], preset)
            if fase < len(esc_sub):
                img = escalar_bloque(img, preset, esc_sub[fase])
            capas_sub[clave] = img
        return capas_sub[clave]

    def capa_inserto(clave):
        if clave not in capas_ins:
            indice, fase = clave
            foto = fotos[indice]
            ruta = foto["imagen"]
            if not os.path.isabs(ruta):
                ruta = os.path.join(base_fotos, ruta)
            img = mod_insertos.tarjeta(ruta, preset, foto.get("pie"))
            if fase < len(esc_ins):
                img = mod_insertos.escalar_tarjeta(img, preset, esc_ins[fase])
            capas_ins[clave] = img
        return capas_ins[clave]

    def imagen_de(clave):
        if clave in hechos:
            return hechos[clave]
        cs, ci = clave
        nombre = "src_%s_%s.png" % ("x" if cs is None else "%03d-%d" % cs,
                                    "x" if ci is None else "%03d-%d" % ci)
        ruta = os.path.join(destino, nombre)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if ci is not None:
            img.alpha_composite(capa_inserto(ci))
        if cs is not None:
            img.alpha_composite(capa_subtitulo(cs))
        img.save(ruta)
        hechos[clave] = ruta
        return ruta

    for n in range(total):
        i_sub, f_sub = _activo_y_fase(grupos, n, fps, esc_sub, fase_sub)
        i_ins, f_ins = _activo_y_fase(fotos, n, fps, esc_ins, fase_ins)
        clave = ((i_sub, f_sub) if i_sub is not None else None,
                 (i_ins, f_ins) if i_ins is not None else None)
        marco = os.path.join(destino, "sub_%05d.png" % n)
        if os.path.exists(marco):
            os.remove(marco)
        try:
            os.link(imagen_de(clave), marco)
        except OSError:
            shutil.copyfile(imagen_de(clave), marco)
    return total


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    guion_path, destino = sys.argv[1], sys.argv[2]
    preset = cargar_preset(sys.argv[3] if len(sys.argv) > 3 else None)
    with open(guion_path, encoding="utf-8") as fh:
        guion = json.load(fh)
    if "lienzo" in guion:
        preset["lienzo"].update(guion["lienzo"])

    os.makedirs(destino, exist_ok=True)
    grupos = []
    for i, grupo in enumerate(guion["grupos"]):
        img = dibujar_grupo(grupo, preset)
        nombre = "cap_%03d.png" % i
        img.save(os.path.join(destino, nombre))
        grupos.append({"png": nombre, "in": grupo["in"], "out": grupo["out"]})
        etiqueta = " / ".join(
            filter(None, [(grupo.get(k) or {}).get("texto") for k in ("l1", "l2")])
        )
        print("%s  %5.2f-%5.2fs  %s" % (nombre, grupo["in"], grupo["out"], etiqueta))
    with open(os.path.join(destino, "grupos.json"), "w", encoding="utf-8") as fh:
        json.dump(grupos, fh, ensure_ascii=False, indent=2)
    print("\n%d grupos en %s" % (len(grupos), destino))
    return 0


if __name__ == "__main__":
    sys.exit(main())
