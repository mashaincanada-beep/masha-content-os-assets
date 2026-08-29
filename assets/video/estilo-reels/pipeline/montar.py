#!/usr/bin/env python3
"""Monta un reel con el estilo: encuadre 9:16, subtitulos quemados y voz normalizada.

    python3 montar.py --video crudo.mp4 --guion guion.json --salida reel.mp4

El clip de entrada ya deberia venir sin pausas (ver quitar_pausas.py), porque los
tiempos del guion se leen contra el clip que se le pasa aqui.

Opciones utiles:
    --paleta viral      usa la paleta del reel de referencia en vez de la de marca
    --maquillaje        retoque leve de piel y luz (ver "maquillaje" en preset.json)
    --tapar 1380,540    tapa una banda del clip original (subtitulos ya quemados,
                        marcas de agua) con un desenfoque degradado: y0,alto en
                        pixeles del lienzo final
    --centro-subs 0.74  sube o baja el bloque de subtitulos (0 arriba, 1 abajo)
    --sin-sfx           monta sin los efectos de burbuja y tecleo
    --sin-audio-norm    deja el audio tal cual (para revisar antes de publicar)
    --solo-comando      imprime el ffmpeg y no ejecuta nada
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx  # noqa: E402
from subtitulos import cargar_preset, dibujar_grupo  # noqa: E402


def ffmpeg():
    for cand in (os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if cand and os.path.exists(cand):
            return cand
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    raise SystemExit("no encuentro ffmpeg: instala imageio-ffmpeg o exporta FFMPEG=/ruta/ffmpeg")


def cadena_maquillaje(preset, entrada, salida):
    """Retoque leve: piel suavizada, algo de brillo y la luz menos amarilla.

    El desenfoque bilateral respeta los bordes, asi que ojos, gafas y pelo se
    quedan nitidos mientras la piel se empareja. El fondo tambien se suaviza,
    pero como ya viene desenfocado no se nota.
    """
    m = preset["maquillaje"]
    b = m["bilateral"]
    bal = m["balance"]
    return (
        "[{ent}]format=gbrp,split[mq_a][mq_b];"
        "[mq_b]bilateral=sigmaS={ss}:sigmaR={sr},format=gbrp[mq_sm];"
        "[mq_a][mq_sm]blend=all_mode=normal:all_opacity={op},format=gbrp[mq_s];"
        "[mq_s]split[mq_c][mq_d];"
        "[mq_d]gblur=sigma={gr},format=gbrp[mq_g];"
        "[mq_c][mq_g]blend=all_mode=screen:all_opacity={gl},format=gbrp[mq_gl];"
        "[mq_gl]colorbalance=rm={rm}:bm={bm}:rh={rh}:bh={bh},"
        "eq=brightness={br}:contrast={co}:saturation={sa},"
        "unsharp=5:5:{ni},format=rgba[{sal}]"
    ).format(ent=entrada, sal=salida, ss=b["sigmaS"], sr=b["sigmaR"],
             op=m["suavizado"], gr=m["glow_radio"], gl=m["glow"],
             rm=bal["rm"], bm=bal["bm"], rh=bal["rh"], bh=bal["bh"],
             br=m["brillo"], co=m["contraste"], sa=m["saturacion"],
             ni=m["nitidez"])


def mascara_banda(preset, ancho, alto, pega_arriba, pega_abajo, destino):
    """PNG en escala de grises con los bordes de la banda degradados."""
    from PIL import Image

    d = preset["tapar"]["difuminado"]
    img = Image.new("L", (ancho, alto), 255)
    pix = img.load()
    for y in range(alto):
        v = 255
        if not pega_arriba and y < d:
            v = min(v, int(255 * y / d))
        if not pega_abajo and y > alto - d:
            v = min(v, int(255 * (alto - y) / d))
        if v != 255:
            for x in range(ancho):
                pix[x, y] = v
    img.save(destino)
    return destino


def cadena_tapar(preset, entrada, salida, indice_mascara, y0, alto, ancho, alto_lienzo):
    """Tapa una banda del clip con una copia desenfocada y oscurecida de si misma."""
    t = preset["tapar"]
    return (
        "[{ent}]format=gbrp,split[tp_a][tp_b];"
        "[tp_b]crop={w}:{h}:0:{y0},gblur=sigma={dz},eq=brightness={osc},format=gbrp[tp_c];"
        "[{im}:v]format=gray,scale={w}:{h}[tp_m];"
        "[tp_c][tp_m]alphamerge[tp_d];"
        "[tp_a][tp_d]overlay=0:{y0}:format=auto,format=rgba[{sal}]"
    ).format(ent=entrada, sal=salida, im=indice_mascara, w=ancho, h=alto,
             y0=y0, dz=t["desenfoque"], osc=t["oscurecer"])


def construir_filtros(grupos, preset, indice_primer_sub, maquillaje=False,
                      tapar=None, indice_mascara=None):
    W = preset["lienzo"]["ancho"]
    H = preset["lienzo"]["alto"]
    fps = preset["lienzo"]["fps"]
    partes = [
        # Encuadre: rellena 9:16 recortando el sobrante, nunca deforma.
        "[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,"
        "setsar=1,format=rgba[base]" % (W, H, W, H, fps)
    ]
    anterior = "base"
    if maquillaje:
        partes.append(cadena_maquillaje(preset, anterior, "mq"))
        anterior = "mq"
    if tapar:
        y0, alto = tapar
        partes.append(cadena_tapar(preset, anterior, "tp", indice_mascara,
                                   y0, alto, W, H))
        anterior = "tp"
    for i, g in enumerate(grupos):
        etiqueta = "v%d" % i
        partes.append(
            "[%d:v]scale=%d:%d,format=rgba,setsar=1[s%d]"
            % (indice_primer_sub + i, W, H, i)
        )
        # Cada PNG entra como un solo fotograma: repeatlast lo mantiene vivo
        # hasta el final para que enable pueda encenderlo cuando toque.
        partes.append(
            "[%s][s%d]overlay=0:0:format=auto:eof_action=repeat:repeatlast=1:"
            "shortest=0:enable='between(t,%.3f,%.3f)'[%s]"
            % (anterior, i, g["in"], g["out"], etiqueta)
        )
        anterior = etiqueta
    partes.append(
        "[%s]format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:"
        "color_trc=bt709:range=tv[v]" % anterior
    )
    return ";".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--guion", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--preset")
    ap.add_argument("--paleta")
    ap.add_argument("--maquillaje", action="store_true")
    ap.add_argument("--tapar", help="y0,alto en pixeles del lienzo final")
    ap.add_argument("--centro-subs", type=float,
                    help="centro vertical del bloque de subtitulos (0-1)")
    ap.add_argument("--crf", type=int,
                    help="calidad de video: cuanto mas alto, mas comprimido")
    ap.add_argument("--sin-sfx", action="store_true")
    ap.add_argument("--sin-audio-norm", action="store_true")
    ap.add_argument("--solo-comando", action="store_true")
    ap.add_argument("--conservar-subs", help="carpeta donde dejar los PNG de subtitulos")
    args = ap.parse_args()

    with open(args.guion, encoding="utf-8") as fh:
        guion = json.load(fh)
    preset = cargar_preset(args.preset, args.paleta or guion.get("paleta"))
    if "lienzo" in guion:
        preset["lienzo"].update(guion["lienzo"])
    centro = args.centro_subs if args.centro_subs is not None else guion.get("centro_subs")
    if centro is not None:
        preset["bloque"]["centro_y_rel"] = centro
    grupos = guion["grupos"]

    destino = args.conservar_subs or tempfile.mkdtemp(prefix="subs_")
    os.makedirs(destino, exist_ok=True)
    pngs = []
    for i, grupo in enumerate(grupos):
        ruta = os.path.join(destino, "cap_%03d.png" % i)
        dibujar_grupo(grupo, preset).save(ruta)
        pngs.append(ruta)

    # Entradas: 0 = video, luego la mascara de tapado (si la hay), luego la pista
    # de efectos (si la hay) y por ultimo los PNG de subtitulos.
    extras, indice_mascara, indice_sfx = [], None, None
    tapar = None
    if args.tapar:
        y0, alto = (int(v) for v in args.tapar.replace(":", ",").split(","))
        tapar = (y0, alto)
        pega_arriba = y0 <= 0
        pega_abajo = y0 + alto >= preset["lienzo"]["alto"]
        indice_mascara = 1 + len(extras)
        extras.append(mascara_banda(preset, preset["lienzo"]["ancho"], alto,
                                    pega_arriba, pega_abajo,
                                    os.path.join(destino, "banda.png")))

    eventos = [] if args.sin_sfx else sfx.eventos_de_guion(guion)
    if eventos:
        fin = max(float(g["out"]) for g in grupos) + 1.0
        indice_sfx = 1 + len(extras)
        extras.append(sfx.escribir_wav(
            sfx.construir_pista(eventos, fin, preset.get("sfx")),
            os.path.join(destino, "sfx.wav")))

    a = preset["audio"]
    voz = ("anull" if args.sin_audio_norm else
           "loudnorm=I=%s:TP=%s:LRA=%s" % (a["lufs"], a["true_peak"], a["lra"]))
    if indice_sfx is None:
        filtro_audio = ["-af", voz]
    else:
        # normalize=0 para que amix no baje la voz al meter los efectos.
        filtro_audio = ["-filter_complex",
                        "[0:a]%s[voz];[%d:a]aresample=48000[efx];"
                        "[voz][efx]amix=inputs=2:duration=first:normalize=0,"
                        "alimiter=limit=0.97[a]" % (voz, indice_sfx)]
    e = preset["export"]
    if args.crf is not None:
        e["crf"] = args.crf

    cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", args.video]
    for p in extras + pngs:
        cmd += ["-i", p]
    filtros = construir_filtros(grupos, preset, 1 + len(extras),
                                maquillaje=args.maquillaje, tapar=tapar,
                                indice_mascara=indice_mascara)
    if indice_sfx is None:
        cmd += ["-filter_complex", filtros, "-map", "[v]", "-map", "0:a?"]
        cmd += filtro_audio
    else:
        cmd += ["-filter_complex", filtros + ";" + filtro_audio[1],
                "-map", "[v]", "-map", "[a]"]
    cmd += [
        "-c:v", "libx264", "-crf", str(e["crf"]), "-preset", e["preset"],
        "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv",
        "-c:a", "aac", "-b:a", "%dk" % e["aac_kbps"], "-ar", "48000",
        "-movflags", "+faststart", "-shortest", args.salida,
    ]

    if args.solo_comando:
        # Los PNG se dejan donde estan, si no el comando impreso no serviria.
        print(" ".join("'%s'" % c if " " in c or ";" in c else c for c in cmd))
        print("\n# subtitulos en %s" % destino)
        return 0

    print("montando %d grupos de subtitulo sobre %s%s%s%s"
          % (len(grupos), args.video,
             " | maquillaje" if args.maquillaje else "",
             " | banda tapada" if tapar else "",
             " | %d efectos" % len(eventos) if eventos else ""))
    subprocess.run(cmd, check=True)
    print("listo: %s (%.1f MB)" % (args.salida, os.path.getsize(args.salida) / 1e6))
    if not args.conservar_subs:
        shutil.rmtree(destino, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
