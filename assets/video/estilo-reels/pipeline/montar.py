#!/usr/bin/env python3
"""Monta un reel con el estilo: encuadre 9:16, subtitulos quemados y voz normalizada.

    python3 montar.py --video crudo.mp4 --guion guion.json --salida reel.mp4

El clip de entrada ya deberia venir sin pausas (ver quitar_pausas.py), porque los
tiempos del guion se leen contra el clip que se le pasa aqui.

Opciones utiles:
    --paleta viral      usa la paleta del reel de referencia en vez de la de marca
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


def construir_filtros(n_subs, grupos, preset):
    W = preset["lienzo"]["ancho"]
    H = preset["lienzo"]["alto"]
    fps = preset["lienzo"]["fps"]
    partes = [
        # Encuadre: rellena 9:16 recortando el sobrante, nunca deforma.
        "[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,"
        "setsar=1,format=rgba[base]" % (W, H, W, H, fps)
    ]
    anterior = "base"
    for i, g in enumerate(grupos):
        etiqueta = "v%d" % i
        partes.append(
            "[%d:v]scale=%d:%d,format=rgba,setsar=1[s%d]" % (i + 1, W, H, i)
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
    ap.add_argument("--sin-audio-norm", action="store_true")
    ap.add_argument("--solo-comando", action="store_true")
    ap.add_argument("--conservar-subs", help="carpeta donde dejar los PNG de subtitulos")
    args = ap.parse_args()

    with open(args.guion, encoding="utf-8") as fh:
        guion = json.load(fh)
    preset = cargar_preset(args.preset, args.paleta or guion.get("paleta"))
    if "lienzo" in guion:
        preset["lienzo"].update(guion["lienzo"])
    grupos = guion["grupos"]

    destino = args.conservar_subs or tempfile.mkdtemp(prefix="subs_")
    os.makedirs(destino, exist_ok=True)
    pngs = []
    for i, grupo in enumerate(grupos):
        ruta = os.path.join(destino, "cap_%03d.png" % i)
        dibujar_grupo(grupo, preset).save(ruta)
        pngs.append(ruta)

    a = preset["audio"]
    filtro_audio = (
        "anull" if args.sin_audio_norm else
        "loudnorm=I=%s:TP=%s:LRA=%s" % (a["lufs"], a["true_peak"], a["lra"])
    )
    e = preset["export"]

    cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", args.video]
    for p in pngs:
        cmd += ["-i", p]
    cmd += [
        "-filter_complex", construir_filtros(len(pngs), grupos, preset),
        "-map", "[v]", "-map", "0:a?",
        "-af", filtro_audio,
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

    print("montando %d grupos de subtitulo sobre %s" % (len(grupos), args.video))
    subprocess.run(cmd, check=True)
    print("listo: %s (%.1f MB)" % (args.salida, os.path.getsize(args.salida) / 1e6))
    if not args.conservar_subs:
        shutil.rmtree(destino, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
