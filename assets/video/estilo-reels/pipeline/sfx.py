#!/usr/bin/env python3
"""Sintetiza los efectos de sonido del estilo y los coloca en una pista.

No hay libreria de sonidos en el repo: los dos efectos se generan por sintesis,
asi que suenan igual en cualquier maquina y no arrastran licencias.

- `bubble`: burbuja. Seno con la frecuencia subiendo rapido y caida exponencial.
- `typing`: tecleo. Tres o cuatro clics de ruido filtrado, uno detras de otro.

    python3 sfx.py guion.json pista.wav --duracion 60.6

Tambien se usa como modulo desde montar.py.
"""

import argparse
import json
import math
import os
import struct
import sys
import wave

SR = 48000


def _envolvente(n, caida):
    return [math.exp(-i / SR * caida) for i in range(n)]


def burbuja(f0=380.0, f1=1250.0, dur=0.085, caida=42.0):
    """Pop de burbuja: barrido ascendente corto con caida exponencial."""
    n = int(SR * dur)
    env = _envolvente(n, caida)
    salida, fase = [], 0.0
    for i in range(n):
        x = i / n
        f = f0 * (f1 / f0) ** (x ** 0.6)
        fase += 2 * math.pi * f / SR
        # El segundo armonico le da el punto "hueco" de la burbuja.
        v = math.sin(fase) + 0.22 * math.sin(2 * fase)
        salida.append(v * env[i])
    return _normalizar(salida)


def tecleo(clics=4, sep=0.055, dur_clic=0.022, semilla=7):
    """Tecleo: varios clics de ruido pasa-altos con un golpe grave debajo."""
    import random

    rnd = random.Random(semilla)
    n_total = int(SR * (sep * clics + dur_clic + 0.02))
    salida = [0.0] * n_total
    for c in range(clics):
        inicio = int(SR * sep * c * rnd.uniform(0.82, 1.18))
        n = int(SR * dur_clic)
        env = _envolvente(n, 320.0)
        anterior = 0.0
        fase = 0.0
        for i in range(n):
            ruido = rnd.uniform(-1, 1)
            # Diferencia de primer orden = pasa-altos barato: deja el clic seco.
            alto = ruido - anterior
            anterior = ruido
            fase += 2 * math.pi * 130.0 / SR
            grave = 0.35 * math.sin(fase) * math.exp(-i / SR * 700.0)
            j = inicio + i
            if j < n_total:
                salida[j] += (alto * 0.7 + grave) * env[i] * rnd.uniform(0.75, 1.0)
    return _normalizar(salida)


def _normalizar(muestras):
    pico = max((abs(v) for v in muestras), default=0.0)
    if pico < 1e-9:
        return muestras
    return [v / pico for v in muestras]


EFECTOS = {"bubble": burbuja, "typing": tecleo}
NIVEL = {"bubble": 0.16, "typing": 0.10}  # pico relativo, bajo la voz


def construir_pista(eventos, duracion, niveles=None):
    """Mezcla los efectos en una pista mono de `duracion` segundos.

    `eventos` es una lista de (segundo, nombre_del_efecto).
    """
    niveles = niveles or NIVEL
    cache = {}
    pista = [0.0] * int(SR * duracion + SR * 0.5)
    for t, nombre in eventos:
        if nombre not in EFECTOS:
            continue
        if nombre not in cache:
            cache[nombre] = EFECTOS[nombre]()
        muestras = cache[nombre]
        nivel = niveles.get(nombre, 0.12)
        inicio = int(SR * max(0.0, t))
        for i, v in enumerate(muestras):
            j = inicio + i
            if j < len(pista):
                pista[j] += v * nivel
    return pista


def escribir_wav(pista, destino):
    os.makedirs(os.path.dirname(os.path.abspath(destino)) or ".", exist_ok=True)
    with wave.open(destino, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        marco = bytearray()
        for v in pista:
            v = max(-1.0, min(1.0, v))
            marco += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(marco))
    return destino


def eventos_de_guion(guion):
    """Saca los eventos de sonido del guion.

    Cada grupo puede traer "sfx": "bubble" | "typing" | "no". Si no lo trae, se
    aplica la regla del estilo: burbuja cuando el grupo lleva emoji, tecleo
    cuando la linea de golpe va en el color de alarma, y silencio en el resto.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from subtitulos import agrupar_emoji, es_emoji

    eventos = []
    for grupo in guion["grupos"]:
        elegido = grupo.get("sfx")
        if elegido is None:
            texto = " ".join((grupo.get(k) or {}).get("texto", "") for k in ("l1", "l2"))
            tiene_emoji = any(es_emoji(u[0]) for u in agrupar_emoji(texto))
            color_alarma = (grupo.get("l2") or {}).get("color") in ("rosa", "rojo")
            elegido = "bubble" if tiene_emoji else ("typing" if color_alarma else "no")
        if elegido and elegido != "no":
            eventos.append((float(grupo["in"]), elegido))
    return eventos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("guion")
    ap.add_argument("salida")
    ap.add_argument("--duracion", type=float, required=True)
    args = ap.parse_args()
    with open(args.guion, encoding="utf-8") as fh:
        guion = json.load(fh)
    eventos = eventos_de_guion(guion)
    escribir_wav(construir_pista(eventos, args.duracion), args.salida)
    print("%d efectos en %s" % (len(eventos), args.salida))
    for t, n in eventos:
        print("  %6.2f s  %s" % (t, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
