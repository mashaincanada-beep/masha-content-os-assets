# -*- coding: utf-8 -*-
"""Ambiente sonoro de estacion espacial: zumbido de motores, aire, pitidos e impactos."""
import numpy as np, os, wave

SR  = 48000
DUR = 9.17
N   = int(SR * DUR)
t   = np.arange(N) / SR
BASE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(11)

def env_exp(start, dec, amp=1.0):
    e = np.zeros(N); i = int(start * SR)
    if i >= N: return e
    k = np.arange(N - i) / SR
    e[i:] = amp * np.exp(-k / dec)
    return e

def lp_1pole(x, cutoff):
    """Filtro paso-bajo de un polo; cutoff puede ser escalar o vector."""
    c = np.full(N, cutoff, float) if np.isscalar(cutoff) else cutoff
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty(N); prev = 0.0
    for i in range(N):
        prev += a[i] * (x[i] - prev)
        y[i] = prev
    return y

# ---- zumbido de los motores de la cubierta ----
drone = np.zeros(N)
for f, g in [(41.2, .55), (55.0, .42), (82.5, .26), (110.0, .16), (164.8, .07)]:
    det = 1 + .0016 * np.sin(2 * np.pi * .11 * t + f)
    drone += g * np.sin(2 * np.pi * f * det * t)
drone *= .30 * (.78 + .22 * np.sin(2 * np.pi * .16 * t))

# ---- aire del sistema de soporte vital ----
noise = rng.normal(0, 1, N)
air   = lp_1pole(noise, 700 + 260 * np.sin(2 * np.pi * .13 * t)) * .085
air  += lp_1pole(noise, 130) * .16

# ---- barrido ascendente de arranque ----
sweep_f = 90 * np.exp(np.clip(t, 0, 1.15) * 2.6)
riser   = np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) * np.exp(-np.clip(t, 0, None) / .55) * .22
riser  += lp_1pole(noise, 300 + 4200 * np.clip(t / 1.15, 0, 1)) * np.exp(-t / .7) * .14

# ---- pitidos de interfaz ----
beeps = np.zeros(N)
for st, f, amp, dec in [(0.34, 1180, .16, .07), (0.62, 1560, .12, .05), (0.92, 1180, .12, .05),
                        (1.32, 2100, .13, .06), (2.46, 1760, .15, .08), (3.30, 880, .17, .12),
                        (6.05, 2100, .11, .05), (8.28, 1320, .15, .18)]:
    e = env_exp(st, dec, amp)
    beeps += np.sin(2 * np.pi * f * t) * e + .35 * np.sin(2 * np.pi * f * 2 * t) * e

# ---- impactos graves (arranque, apertura del ventanal, cierre) ----
sub = np.zeros(N)
for st, f, amp, dec in [(0.30, 44, .40, .70), (3.30, 38, .46, .95), (8.28, 34, .34, 1.10)]:
    e = env_exp(st, dec, amp)
    sub += np.sin(2 * np.pi * f * t * (1 - .18 * np.exp(-np.clip(t - st, 0, None) / .25))) * e

# ---- fallos / glitches sincronizados con la imagen ----
gl = np.zeros(N)
for st in (0.98, 3.34, 6.06):
    i0, i1 = int(st * SR), int((st + .09) * SR)
    gl[i0:i1] += rng.normal(0, 1, i1 - i0) * np.linspace(.32, 0, i1 - i0)

mix = drone + air + riser + beeps + sub + gl

# ---- eco corto: sensacion de modulo metalico ----
def echo(x, ms, fb, mix_g):
    d = int(SR * ms / 1000); y = x.copy()
    for k in range(1, 4):
        y[d * k:] += x[:-d * k] * (fb ** k) * mix_g
    return y
mix = echo(mix, 78, .55, .30)

# ---- estereo con leve descorrelacion ----
L = mix + np.roll(air, 220) * .35
R = mix + np.roll(air, -190) * .35
st = np.stack([L, R], 1)

# fundidos y normalizacion
fade = np.ones(N)
fade[:int(.06 * SR)] = np.linspace(0, 1, int(.06 * SR))
fade[-int(.45 * SR):] = np.linspace(1, 0, int(.45 * SR))
st *= fade[:, None]
st = np.tanh(st * 1.25) * .82
st /= max(1e-9, np.abs(st).max()); st *= .85

pcm = (st * 32767).astype('<i2')
with wave.open(f"{BASE}/ambience.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ambience.wav", round(DUR, 2), "s")
