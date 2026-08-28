#!/usr/bin/env python3
"""Quita el aire muerto de una toma y deja el corte seco caracteristico del estilo.

Busca los silencios con silencedetect, se queda con los tramos hablados y los pega
sin transicion. En el reel de referencia solo quedan 0,38 s de silencio en 18,9 s:
esa es la vara.

    python3 quitar_pausas.py crudo.mp4 cortado.mp4

Imprime tambien la equivalencia de tiempos (minuto de la toma cruda -> minuto del
clip cortado) para que sea facil escribir el guion de subtitulos despues.
"""

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar import ffmpeg  # noqa: E402
from subtitulos import cargar_preset  # noqa: E402


def duracion(ruta, flujo="a"):
    """Duracion de un flujo concreto, decodificandolo entero.

    Va por flujo a proposito: los tiempos de silencedetect salen del audio, asi
    que la duracion con la que se hacen las cuentas tiene que salir del audio
    tambien.
    """
    salida = subprocess.run(
        [ffmpeg(), "-hide_banner", "-i", ruta, "-map", "0:%s" % flujo,
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    ultimo = re.findall(r"time=(\d+):(\d+):([\d.]+)", salida)
    if not ultimo:
        raise SystemExit("no pude medir la duracion de %s" % ruta)
    h, m, s = ultimo[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def silencios(ruta, umbral_db, pausa_min):
    salida = subprocess.run(
        [ffmpeg(), "-hide_banner", "-i", ruta,
         "-af", "silencedetect=n=%ddB:d=%.3f" % (umbral_db, pausa_min),
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    inicios = [float(x) for x in re.findall(r"silence_start: ([\d.-]+)", salida)]
    finales = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", salida)]
    if len(finales) < len(inicios):  # silencio abierto hasta el final
        finales.append(duracion(ruta))
    return list(zip(inicios, finales))


def tramos_hablados(pausas, total, colchon):
    tramos, cursor = [], 0.0
    for ini, fin in pausas:
        ini = max(cursor, ini + colchon)
        if ini > cursor + 0.04:
            tramos.append((cursor, ini))
        cursor = max(cursor, fin - colchon)
    if total - cursor > 0.04:
        tramos.append((cursor, total))
    return tramos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--preset")
    ap.add_argument("--umbral-db", type=int)
    ap.add_argument("--pausa-min", type=float)
    ap.add_argument("--colchon", type=float)
    ap.add_argument("--mapa", help="guarda la equivalencia de tiempos en un JSON")
    args = ap.parse_args()

    preset = cargar_preset(args.preset)
    c = preset["cortes"]
    umbral = args.umbral_db if args.umbral_db is not None else c["umbral_db"]
    pausa_min = args.pausa_min if args.pausa_min is not None else c["pausa_min_s"]
    colchon = args.colchon if args.colchon is not None else c["colchon_s"]

    total = duracion(args.entrada, "a")
    total_v = duracion(args.entrada, "v")
    if abs(total - total_v) > max(0.5, 0.02 * total):
        print("aviso: el audio dura %.2f s y el video %.2f s. El archivo trae los "
              "tiempos descuadrados (pasa con algunas grabaciones de pantalla); "
              "reenvasalo antes de cortarlo:\n"
              "  ffmpeg -i %s -c:v libx264 -crf 18 -c:a aac -vsync cfr limpio.mp4"
              % (total, total_v, args.entrada))
    pausas = silencios(args.entrada, umbral, pausa_min)
    tramos = tramos_hablados(pausas, total, colchon)
    if not tramos:
        raise SystemExit("no encontre nada por encima de %d dB: revisa el umbral" % umbral)

    conservado = sum(b - a for a, b in tramos)
    print("toma cruda: %.2f s   tramos: %d   cortado: %.2f s   fuera: %.2f s"
          % (total, len(tramos), conservado, total - conservado))

    expr = "+".join("between(t,%.3f,%.3f)" % (a, b) for a, b in tramos)
    fps = preset["lienzo"]["fps"]
    # El fps final hay que declararlo: despues de un select la cadena queda con
    # cadencia variable y ffmpeg cae a 25 fps por defecto, tirando fotogramas y
    # desincronizando la imagen del audio.
    filtro = (
        "[0:v]select='%s',setpts=N/%d/TB,fps=%d[v];"
        "[0:a]aselect='%s',asetpts=N/SR/TB[a]" % (expr, fps, fps, expr)
    )
    e = preset["export"]
    subprocess.run(
        [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", args.entrada,
         "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", str(e["crf"]), "-preset", e["preset"],
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "%dk" % e["aac_kbps"],
         args.salida],
        check=True,
    )

    mapa, acumulado = [], 0.0
    print("\n  toma cruda        clip cortado")
    for a, b in tramos:
        mapa.append({"crudo_in": round(a, 3), "crudo_out": round(b, 3),
                     "cortado_in": round(acumulado, 3),
                     "cortado_out": round(acumulado + b - a, 3)})
        print("  %6.2f - %6.2f -> %6.2f - %6.2f"
              % (a, b, acumulado, acumulado + b - a))
        acumulado += b - a
    if args.mapa:
        with open(args.mapa, "w", encoding="utf-8") as fh:
            json.dump(mapa, fh, indent=2)
    print("\nlisto: %s (%.1f MB)" % (args.salida, os.path.getsize(args.salida) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
