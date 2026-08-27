"""Genera una cama musical suave de 60 s (pad + arpegio) para el video."""
import numpy as np, wave, struct, sys

SR, DUR = 44100, 60.0
n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(7)

def note(f):  # midi-ish helper: f already in Hz
    return f

# Progresion (4 s por acorde): F#m - D - A - E
CHORDS = [
    [185.00, 220.00, 277.18],   # F#m  (F#3 A3 C#4)
    [146.83, 185.00, 220.00],   # D    (D3 F#3 A3)
    [220.00, 277.18, 329.63],   # A    (A3 C#4 E4)
    [164.81, 207.65, 246.94],   # E    (E3 G#3 B3)
]
BAR = 4.0
pad = np.zeros(n)
arp = np.zeros(n)

for i in range(int(DUR / BAR)):
    ch = CHORDS[i % len(CHORDS)]
    a, b = i * BAR, (i + 1) * BAR
    i0, i1 = int(a * SR), int(min(b + 1.2, DUR) * SR)
    seg = np.arange(i1 - i0) / SR
    # envolvente suave del pad (attack 0.9 s, release largo)
    env = np.minimum(seg / 0.9, 1.0) * np.exp(-np.maximum(seg - BAR, 0) / 0.5)
    env *= np.clip((BAR + 1.2 - seg) / 1.2, 0, 1)
    for k, f in enumerate(ch):
        for det in (-0.6, 0.6):
            ph = rng.random() * 2 * np.pi
            v = np.sin(2 * np.pi * (f + det) * seg + ph)
            v += 0.28 * np.sin(2 * np.pi * 2 * (f + det) * seg + ph)
            v += 0.10 * np.sin(2 * np.pi * 3 * (f + det) * seg + ph)
            pad[i0:i1] += v * env * (0.16 if k == 0 else 0.11)
    # arpegio: nota cada 0.5 s subiendo una octava
    step = 0.5
    for s in range(int(BAR / step)):
        ts = a + s * step
        j0 = int(ts * SR); j1 = min(n, j0 + int(1.1 * SR))
        if j0 >= n: break
        d = np.arange(j1 - j0) / SR
        f = ch[s % len(ch)] * 2
        e = np.exp(-d * 5.2) * np.minimum(d / 0.004, 1.0)
        w = (np.sin(2 * np.pi * f * d) + 0.35 * np.sin(2 * np.pi * 2 * f * d)
             + 0.14 * np.sin(2 * np.pi * 3 * f * d))
        arp[j0:j1] += w * e * 0.085

# aire: ruido filtrado muy bajo
noise = rng.normal(0, 1, n)
k = 900
noise = np.convolve(noise, np.ones(k) / k, mode='same')
air = noise / (np.max(np.abs(noise)) + 1e-9) * 0.035

mix = pad + arp + air
# fades
fi, fo = int(1.4 * SR), int(2.2 * SR)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)
# leve realce al entrar a la seccion de jobs y al cierre
mix *= 1 + 0.10 * np.exp(-((t - 21.5) ** 2) / 2.0) + 0.10 * np.exp(-((t - 56.2) ** 2) / 2.0)

# estereo con leve ensanchado
delay = int(0.011 * SR)
L = mix.copy()
R = np.concatenate([np.zeros(delay), mix[:-delay]]) * 0.97 + mix * 0.03
st = np.stack([L, R], axis=1)
st = st / (np.max(np.abs(st)) + 1e-9) * 0.50   # pico ~ -6 dBFS, deja sitio a la voz

out = (st * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote', sys.argv[1], out.shape)
