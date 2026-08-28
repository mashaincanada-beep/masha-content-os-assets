"""Banda sonora del reel: pad ambiental suave, celesta y olas de lago."""
import sys, math
import numpy as np
from scipy import signal
import wave

SR = 48000
DUR = 31.41
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(20260828)


def butter(x, cutoff, btype, order=4):
    wn = (np.asarray(cutoff, float) / (SR / 2)) if isinstance(cutoff, (list, tuple)) \
        else float(cutoff) / (SR / 2)
    sos = signal.butter(order, wn, btype=btype, output="sos")
    return signal.sosfilt(sos, x)


def semis(name, octv):
    """Semitonos respecto a A4."""
    base = {"C": 3, "C#": 4, "D": 5, "D#": 6, "E": 7, "F": 8, "F#": 9,
            "G": 10, "G#": 11, "A": 12, "A#": 13, "B": 14}[name]
    return base + 12 * (octv - 4) - 12


def hz(st):
    return 440.0 * 2 ** (st / 12.0)


def env(start, dur, atk, rel):
    e = np.zeros(N)
    i0, i1 = max(0, int(start * SR)), min(N, int((start + dur) * SR))
    if i1 <= i0:
        return e
    seg = np.ones(i1 - i0)
    na = min(int(atk * SR), len(seg) // 2)
    nr = min(int(rel * SR), len(seg) - na)
    if na > 0:
        seg[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    if nr > 0:
        seg[-nr:] = np.sin(np.linspace(np.pi / 2, 0, nr)) ** 2
    e[i0:i1] = seg
    return e


# ------------------------------------------------------------------ pad
# Progresion calida en Re mayor: D - A - Bm - G
VOICINGS = [
    [semis("D", 2), semis("D", 3), semis("A", 3), semis("F#", 4), semis("A", 4)],
    [semis("A", 1), semis("A", 2), semis("E", 3), semis("C#", 4), semis("E", 4)],
    [semis("B", 1), semis("B", 2), semis("F#", 3), semis("D", 4), semis("F#", 4)],
    [semis("G", 1), semis("G", 2), semis("D", 3), semis("B", 3), semis("D", 4)],
]
BAR = DUR / 4.0

pad_l = np.zeros(N)
pad_r = np.zeros(N)
for ci, voic in enumerate(VOICINGS):
    e = env(max(0.0, ci * BAR - 1.4), BAR + 3.0, 2.4, 2.6)
    for vi, st in enumerate(voic):
        f = hz(st)
        amp = 0.30 / (1 + 0.6 * vi)
        for det, side in ((-0.14, -1), (0.14, 1)):
            drift = 1.6 * np.sin(2 * np.pi * (0.05 + 0.012 * vi) * t + vi)
            ph = 2 * np.pi * (f + det) * t + drift
            w = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
            breath = 0.82 + 0.18 * np.sin(2 * np.pi * 0.065 * t + vi * 1.3)
            sig = w * e * amp * breath
            if side < 0:
                pad_l += sig * 0.74; pad_r += sig * 0.40
            else:
                pad_l += sig * 0.40; pad_r += sig * 0.74

# el pad se queda calido, sin agudos duros
pad_l = butter(pad_l, 5200, "low")
pad_r = butter(pad_r, 5200, "low")

# ------------------------------------------------------------------ celesta
def celesta(freq, start, dur=2.8, amp=0.34):
    i0 = int(start * SR)
    n = min(int(dur * SR), N - i0)
    if n <= 0:
        return np.zeros(N)
    tt = np.arange(n) / SR
    body = (np.sin(2 * np.pi * freq * tt)
            + 0.40 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-tt * 4.5)
            + 0.16 * np.sin(2 * np.pi * freq * 3.01 * tt) * np.exp(-tt * 7.5)
            + 0.06 * np.sin(2 * np.pi * freq * 5.4 * tt) * np.exp(-tt * 12.0))
    out = np.zeros(N)
    out[i0:i0 + n] = body * np.exp(-tt * 2.0) * np.minimum(1.0, tt / 0.006) * amp
    return out


MELODY = [(2.4, ("F#", 5)), (4.1, ("A", 5)), (6.2, ("E", 5)), (8.5, ("C#", 5)),
          (10.3, ("E", 5)), (12.1, ("A", 5)), (14.4, ("F#", 5)), (16.2, ("D", 5)),
          (18.3, ("F#", 5)), (20.5, ("B", 4)), (22.4, ("D", 5)), (24.1, ("A", 5)),
          (26.0, ("F#", 5)), (27.7, ("D", 5)), (29.5, ("A", 4))]
mel = np.zeros(N)
for st, (nm, oc) in MELODY:
    mel += celesta(hz(semis(nm, oc)), st)

# ------------------------------------------------------------------ olas
def waves(seed_off):
    n = rng.normal(0, 1, N)
    # ruido marron: mucho cuerpo grave, casi nada de siseo
    brown = np.cumsum(n)
    brown = butter(brown, 20, "high")
    brown /= np.std(brown) + 1e-9
    body = butter(butter(brown, 520, "low"), 55, "high")
    body /= np.std(body) + 1e-9
    # espuma: banda media estrecha y discreta
    foam = butter(n, [900, 4800], "bandpass")
    foam /= np.std(foam) + 1e-9

    # envolvente de rompiente: varios ciclos lentos incoherentes
    e = np.zeros(N)
    for per, ph, w in ((6.7, 0.0, 1.0), (9.3, 1.7, 0.72), (4.4, 3.1, 0.48)):
        e += w * (0.5 + 0.5 * np.sin(2 * np.pi * t / per + ph + seed_off))
    e = np.clip(e / 2.2, 0, 1) ** 2.0
    swell = 0.32 + 0.68 * e
    out = body * swell * 0.92 + foam * (swell ** 2.6) * 0.34
    return butter(out, 9500, "low")


w_l, w_r = waves(0.0), waves(0.95)

# ------------------------------------------------------------------ reverb
def reverb(x, decay=2.2, mix=0.34):
    ln = int(decay * SR)
    ir = rng.normal(0, 1, ln) * np.exp(-np.arange(ln) / (decay * SR / 4.0))
    pre = int(0.014 * SR)
    ir[:pre] *= np.linspace(0, 1, pre)
    ir = butter(ir, 4000, "low")
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    wet = signal.fftconvolve(x, ir)[:N]
    return (1 - mix) * x + mix * wet * 1.7


pad_l, pad_r = reverb(pad_l, 2.4, 0.36), reverb(pad_r, 2.4, 0.36)
mel_l = reverb(mel, 2.8, 0.46)
mel_r = reverb(np.concatenate((np.zeros(680), mel))[:N], 2.8, 0.46)


def at(x, db):
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (db / 20)


L = at(pad_l, -9.0) + at(mel_l, -15.0) + at(w_l, -12.0)
R = at(pad_r, -9.0) + at(mel_r, -15.0) + at(w_r, -12.0)

fi, fo_ = int(2.2 * SR), int(3.2 * SR)
fade = np.ones(N)
fade[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
fade[-fo_:] = np.sin(np.linspace(np.pi / 2, 0, fo_)) ** 2
L *= fade; R *= fade

L = np.tanh(L / 0.9) * 0.9
R = np.tanh(R / 0.9) * 0.9

pcm = (np.clip(np.stack([L, R], 1), -1, 1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("escrito", sys.argv[1], pcm.shape)
