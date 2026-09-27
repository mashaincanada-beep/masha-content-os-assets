"""MIC Study Childhood Stories - audio: voices, score, sound design, mix.

Everything here is generated locally:
  * voices   - see voice.py (voice system v2: ElevenLabs performance voices).
               synth() below is the Kokoro LAST-RESORT fallback only.
  * score    - an original piano / strings / celesta score synthesised note
               by note, following the mood of each part of the story.
  * sound    - procedural foley (pages, pencils, footsteps, kitchen, crowd,
               birds, applause...) and ambience beds, incl. crowd murmur
               made from TTS babble.
"""
import hashlib, json, math, os, re, subprocess, tempfile
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt

SR = 48000
CACHE = os.path.expanduser("~/.cache/micstudy")
os.makedirs(CACHE, exist_ok=True)
MODEL_DIR = os.environ.get("MICSTUDY_TTS_DIR", CACHE)
_kokoro = None


# ============================================================== utilities
def db(x):
    return 10 ** (x / 20.0)


def lowpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x, axis=0)


def highpass(x, fc, order=2):
    sos = butter(order, fc / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x, axis=0)


def bandpass(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, x, axis=0)


def env_adsr(n, a=0.005, d=0.0, s=1.0, r=0.05):
    e = np.ones(n) * s
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def to_stereo(x, pan=0.0):
    """pan -1 left .. +1 right (equal power)."""
    if x.ndim == 2:
        return x
    a = (pan + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], axis=1)


def place(buf, clip, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(buf) or len(clip) == 0:
        return
    if i < 0:
        clip, i = clip[-i:], 0
    j = min(len(buf), i + len(clip))
    buf[i:j] += clip[: j - i] * gain


def make_ir(seconds=2.2, bright=4500, seed=0):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
    ir = lowpass(ir, bright)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]
    return ir / np.sqrt((ir ** 2).sum(axis=0))


_IR = {}


def reverb(x, wet=0.25, seconds=2.2, bright=4500):
    key = (seconds, bright)
    if key not in _IR:
        _IR[key] = make_ir(seconds, bright)
    ir = _IR[key]
    xs = to_stereo(x)
    w = np.stack([fftconvolve(xs[:, c], ir[:, c])[: len(xs)] for c in range(2)], axis=1)
    return xs * (1 - wet) + w * wet * 1.4


# ============================================================== voices
def _k():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _kokoro


def _trim(a, thr=0.008, pad=0.04):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - int(pad * SR)), min(len(a), idx[-1] + int(pad * SR))
    return a[s:e]


def _pitch(a, p):
    if abs(p - 1.0) < 1e-3:
        return a
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
        sf.write(i, a, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", i, "-af",
                        f"asetrate={SR}*{p},aresample={SR},atempo={1 / p:.5f}", o], check=True)
        b, _ = sf.read(o)
    return b


PAUSE_RE = re.compile(r"\|\s*(\d+(?:\.\d+)?)\s*\|")


def display_text(t):
    return re.sub(r"\s+", " ", PAUSE_RE.sub(" ", t)).strip()


def synth(text, voice="af_heart", speed=1.0, pitch=1.0):
    """Speak `text`; `|0.6|` inside the text inserts a 0.6 s pause."""
    key = hashlib.md5(json.dumps([text, voice, speed, pitch, 3]).encode()).hexdigest()
    path = os.path.join(CACHE, f"tts_{key}.wav")
    if os.path.exists(path):
        a, _ = sf.read(path)
        return a
    parts = PAUSE_RE.split(text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(np.zeros(int(float(part) * SR)))
            continue
        part = part.strip()
        if not part:
            continue
        a, sr = _k().create(part, voice=voice, speed=speed, lang="en-us")
        a = resample_poly(a, SR, sr)
        a = _trim(a)
        out.append(_pitch(a, pitch))
    a = np.concatenate(out) if out else np.zeros(1)
    a = highpass(a, 70)
    peak = np.max(np.abs(a)) or 1
    a = a / peak * 0.8
    sf.write(path, a, SR)
    return a


def envelope(a, fps=30):
    """Per-frame mouth openness 0..1 from a voice clip."""
    hop = SR // fps
    n = int(math.ceil(len(a) / hop))
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(n)])
    if e.max() > 0:
        e = e / np.percentile(e[e > 0], 90)
    return np.clip(e, 0, 1.2)


# ============================================================== score
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def midi_f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def piano(f, dur, vel=0.7, bright=1.0):
    n = int((dur + 0.02) * SR)
    t = np.arange(n) / SR
    tau = 2.6 * (261.6 / f) ** 0.45
    x = np.zeros(n)
    B = 0.00018
    for k in range(1, 9):
        fk = k * f * math.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        amp = (1 / k ** (1.6 - 0.4 * bright)) * (0.6 + 0.4 * vel)
        x += amp * np.sin(2 * math.pi * fk * t + 0.3 * k) * np.exp(-t * (1 + 0.55 * k) / tau)
    x *= env_adsr(n, 0.004, r=min(0.25, dur * 0.5))
    x += 0.002 * vel * np.random.default_rng(int(f)).standard_normal(n) * np.exp(-t * 60)
    return x * vel * 0.32


def strings(f, dur, vel=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        vib = 1 + 0.0025 * np.sin(2 * math.pi * 5.1 * t + det * 10)
        ph = 2 * math.pi * np.cumsum(ff * vib) / SR
        for k in range(1, 9):
            x += np.sin(k * ph) / k ** 1.35
    x = lowpass(x, min(3500, f * 6))
    x *= env_adsr(n, min(1.2, dur * 0.4), r=min(1.4, dur * 0.45))
    return x * vel * 0.05


def celesta(f, dur, vel=0.5):
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * math.pi * f * t) + 0.35 * np.sin(2 * math.pi * f * 4.02 * t) * np.exp(-t * 9)
         + 0.2 * np.sin(2 * math.pi * f * 2.76 * t) * np.exp(-t * 5)) * np.exp(-t * 3.2)
    return x * env_adsr(n, 0.002, r=0.05) * vel * 0.13


def bass(f, dur, vel=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * math.pi * f * t) + 0.25 * np.sin(4 * math.pi * f * t)) * np.exp(-t * 0.9)
    return x * env_adsr(n, 0.01, r=0.3) * vel * 0.2


PROG = {  # scale degrees (0 = I) per bar
    "curious": [0, 5, 3, 4], "uncertain": [5, 3, 1, 4], "reflective": [5, 3, 0, 4],
    "hopeful": [3, 0, 4, 5, 3, 4, 0, 0], "warm": [0, 4, 5, 3], "gentle": [3, 0, 4, 0],
    "playful": [0, 3, 4, 0], "tender": [0, 2, 3, 4],
}


def chord(root_midi, degree, octave=0):
    """Triad (plus added 9th colour for some) built on a scale degree."""
    notes = []
    for step in (0, 2, 4):
        d = degree + step
        notes.append(root_midi + MAJOR[d % 7] + 12 * (d // 7) + 12 * octave)
    return notes


class Score:
    def __init__(self, key="D", bpm=78, seed=7):
        self.root = 60 + NOTE[key] - (12 if NOTE[key] > 5 else 0)
        self.beat = 60.0 / bpm
        self.bar = self.beat * 4
        rng = np.random.default_rng(seed)
        # a short memorable motif (scale degrees), reused in warm sections
        self.motif = [4, 5, 4, 2, 1, 2, 4, 0] if seed % 2 else [2, 4, 5, 4, 2, 1, 0, 1]
        self.rng = rng

    def _deg_midi(self, d, octave=1):
        return self.root + MAJOR[d % 7] + 12 * (d // 7) + 12 * octave

    def section(self, mood, dur):
        """Render one mood section of `dur` seconds (stereo)."""
        n = int((dur + 3.0) * SR)
        L = np.zeros(n)
        Rr = np.zeros(n)
        if mood in ("silence", None):
            return np.zeros((int(dur * SR), 2))
        prog = PROG.get(mood, PROG["reflective"])
        bars = int(math.ceil(dur / self.bar))
        b, bt = self.bar, self.beat

        def add(x, t, pan=0.0):
            s = to_stereo(x, pan)
            i = int(t * SR)
            j = min(n, i + len(s))
            if i < n:
                L[i:j] += s[: j - i, 0]
                Rr[i:j] += s[: j - i, 1]

        for bi in range(bars):
            t0 = bi * b
            deg = prog[bi % len(prog)]
            ch = chord(self.root, deg)
            last = bi == bars - 1
            if mood == "curious" or mood == "playful":
                pat = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]]
                for k, m in enumerate(pat):
                    add(piano(midi_f(m), bt * 0.5, 0.42 + 0.08 * (k % 4 == 0), 0.9), t0 + k * bt / 2, -0.2)
                if bi % 2 == 1:
                    for k, d in enumerate([4, 5, 7, 4] if bi % 4 == 1 else [2, 4, 5, 7]):
                        add(celesta(midi_f(self._deg_midi(deg + d, 2)), bt * 0.9, 0.55), t0 + k * bt, 0.35)
                add(strings(midi_f(ch[0] - 12), b, 0.35), t0, 0)
            elif mood == "uncertain":
                add(strings(midi_f(ch[0] - 12), b * 1.02, 0.5), t0, -0.1)
                add(strings(midi_f(ch[2]), b * 1.02, 0.25), t0, 0.2)
                for k, m in enumerate([ch[0] + 12, ch[2]]):
                    add(piano(midi_f(m), bt * 2, 0.35, 0.6), t0 + k * bt * 2 + bt * 0.5, 0.1)
            elif mood in ("reflective", "tender"):
                add(strings(midi_f(ch[0] - 12), b * 1.02, 0.42), t0, 0)
                add(strings(midi_f(ch[1]), b * 1.02, 0.22), t0, 0.15)
                for k, m in enumerate([ch[0], ch[2], ch[1] + 12, ch[2]]):
                    add(piano(midi_f(m), bt * 1.6, 0.45 - 0.05 * k, 0.75), t0 + k * bt, -0.15)
            elif mood == "hopeful":
                add(strings(midi_f(ch[0] - 12), b * 1.02, 0.35 + 0.4 * min(1, bi / max(1, bars - 1))), t0, 0)
                add(strings(midi_f(ch[2]), b * 1.02, 0.25 + 0.3 * min(1, bi / max(1, bars - 1))), t0, 0.2)
                pat = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[2], ch[1], ch[2]]
                for k, m in enumerate(pat):
                    add(piano(midi_f(m), bt * 0.9, 0.45, 0.85), t0 + k * bt / 2, -0.2)
                add(bass(midi_f(ch[0] - 24), b, 0.5), t0, 0)
            elif mood == "warm":
                add(strings(midi_f(ch[0] - 12), b * 1.02, 0.7), t0, -0.1)
                add(strings(midi_f(ch[1]), b * 1.02, 0.45), t0, 0.1)
                add(strings(midi_f(ch[2] + 12), b * 1.02, 0.3), t0, 0.25)
                pat = [ch[0], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[2], ch[1] + 12, ch[2]]
                for k, m in enumerate(pat):
                    add(piano(midi_f(m), bt * 0.9, 0.42, 0.9), t0 + k * bt / 2, -0.25)
                add(bass(midi_f(ch[0] - 24), b, 0.65), t0, 0)
                mo = self.motif[(bi % 2) * 4:(bi % 2) * 4 + 4]
                for k, d in enumerate(mo):
                    add(piano(midi_f(self._deg_midi(d, 1) + 12), bt * 1.2, 0.62, 1.1), t0 + k * bt, 0.15)
            elif mood == "gentle":
                add(strings(midi_f(ch[0] - 12), b * (1.6 if last else 1.02), 0.35), t0, 0)
                notes = [ch[0], ch[2], ch[1] + 12] if not last else [ch[0], ch[2], ch[1] + 12, ch[0] + 12]
                for k, m in enumerate(notes):
                    add(piano(midi_f(m), bt * (3 if last else 1.8), 0.42, 0.7), t0 + k * bt * (1.0 if not last else 0.5), -0.1)
        x = np.stack([L, Rr], axis=1)
        x = reverb(x, 0.32, 2.6, 5000)
        return x[: int(dur * SR) + int(2.0 * SR)]

    def render(self, regions, total):
        """regions: [(start, end, mood)] -> stereo music bed of `total` s."""
        out = np.zeros((int(total * SR) + SR, 2))
        xf = 1.2
        for idx, (s, e, mood) in enumerate(regions):
            if mood in ("silence", None):
                continue
            seg = self.section(mood, e - s + xf)
            n = len(seg)
            fade_in = int(xf * SR) if idx > 0 else int(0.4 * SR)
            g = np.ones(n)
            g[:fade_in] = np.linspace(0, 1, fade_in) ** 0.8
            end_i = int((e - s) * SR)
            tail = int(xf * SR * 1.6)
            if idx < len(regions) - 1 and end_i < n:
                g[end_i:min(n, end_i + tail)] = np.linspace(1, 0, min(n, end_i + tail) - end_i)
                g[min(n, end_i + tail):] = 0
            seg = seg * g[:, None]
            place(out, seg, s)
        # final fade
        fo = int(2.5 * SR)
        end = int(total * SR)
        out[end - fo:end] *= np.linspace(1, 0, fo)[:, None] ** 1.5
        out[end:] = 0
        return out[: int(total * SR)]


# ============================================================== sound effects
def _noise(n, seed=0):
    return np.random.default_rng(seed).standard_normal(n)


def sfx(name, seed=0, **kw):
    r = np.random.default_rng(seed)
    t_ = lambda d: np.arange(int(d * SR)) / SR
    if name == "page":
        out = np.zeros(int(0.6 * SR))
        for k, (st, d) in enumerate(((0.0, 0.18), (0.16, 0.3))):
            n = int(d * SR)
            x = bandpass(_noise(n, seed + k), 1500, 7000) * np.sin(np.linspace(0, math.pi, n)) ** 2
            place(out, x * (0.25 if k == 0 else 0.45), st)
        return out
    if name == "pencil":
        d = kw.get("dur", 1.2)
        n = int(d * SR)
        x = bandpass(_noise(n, seed), 2500, 8000)
        mod = (np.sin(2 * math.pi * 7 * t_(d) + r.random()) > 0.2).astype(float)
        mod = lowpass(mod, 40)
        return x * mod * 0.12
    if name == "footsteps":
        k = kw.get("n", 4)
        gap = kw.get("gap", 0.45)
        out = np.zeros(int((k * gap + 0.3) * SR))
        for i in range(k):
            n = int(0.09 * SR)
            x = lowpass(_noise(n, seed + i), 900) * np.exp(-np.arange(n) / SR * 45)
            place(out, x * (0.5 + 0.1 * r.random()), i * gap)
        return out
    if name == "knock":
        out = np.zeros(int(0.8 * SR))
        for i in range(3):
            n = int(0.08 * SR)
            tt = np.arange(n) / SR
            x = (np.sin(2 * math.pi * 180 * tt) + 0.5 * lowpass(_noise(n, i), 1200)) * np.exp(-tt * 55)
            place(out, x * 0.6, i * 0.2)
        return out
    if name == "door":
        d = 1.0
        tt = t_(d)
        creak = np.sin(2 * math.pi * (300 + 80 * np.sin(2 * math.pi * 1.5 * tt)) * tt) * 0.05 * np.exp(-tt * 1.2)
        th = np.zeros_like(tt)
        n = int(0.15 * SR)
        th[int(0.7 * SR):int(0.7 * SR) + n] = lowpass(_noise(n, seed), 300)[:len(th[int(0.7 * SR):int(0.7 * SR) + n])] * np.exp(-np.arange(n) / SR * 25)
        return bandpass(creak, 200, 2000) + th * 0.7
    if name == "chair":
        d = 0.6
        tt = t_(d)
        x = bandpass(_noise(len(tt), seed), 300, 1800) * (1 + np.sin(2 * math.pi * 30 * tt)) * np.sin(np.linspace(0, math.pi, len(tt)))
        return x * 0.18
    if name in ("clink", "cup"):
        d = 0.8
        tt = t_(d)
        f = kw.get("f", 2400 + 300 * r.random())
        return (np.sin(2 * math.pi * f * tt) + 0.5 * np.sin(2 * math.pi * f * 2.7 * tt)) * np.exp(-tt * 9) * 0.12
    if name == "pour":
        d = kw.get("dur", 1.5)
        tt = t_(d)
        x = bandpass(_noise(len(tt), seed), 400, 3000)
        return x * np.sin(np.linspace(0, math.pi, len(tt))) ** 0.5 * 0.08
    if name == "sizzle":
        d = kw.get("dur", 3.0)
        x = highpass(_noise(int(d * SR), seed), 3000) * (0.6 + 0.4 * (r.random(int(d * SR)) > 0.97))
        return x * 0.03
    if name == "chop":
        k = kw.get("n", 4)
        out = np.zeros(int((k * 0.3 + 0.2) * SR))
        for i in range(k):
            n = int(0.06 * SR)
            tt = np.arange(n) / SR
            place(out, (lowpass(_noise(n, i), 2500) + np.sin(2 * math.pi * 220 * tt)) * np.exp(-tt * 70) * 0.4, i * 0.3)
        return out
    if name == "bell":  # school bell
        d = kw.get("dur", 1.6)
        tt = t_(d)
        x = np.sin(2 * math.pi * 1800 * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 22 * tt)))
        return bandpass(x, 800, 5000) * env_adsr(len(tt), 0.01, r=0.2) * 0.05
    if name == "chime":  # soft magical chime (use sparingly)
        out = np.zeros(int(1.6 * SR))
        for i, m in enumerate((84, 88, 91, 96)):
            place(out, celesta(midi_f(m), 1.0, 0.6), i * 0.09)
        return out
    if name == "whistle":
        d = kw.get("dur", 0.7)
        tt = t_(d)
        f = 2900 + 120 * np.sin(2 * math.pi * 28 * tt)
        return np.sin(2 * math.pi * np.cumsum(f) / SR) * env_adsr(len(tt), 0.02, r=0.08) * 0.08
    if name == "ball":
        k = kw.get("n", 3)
        out = np.zeros(int(1.5 * SR))
        tt0 = 0.0
        for i in range(k):
            n = int(0.12 * SR)
            tt = np.arange(n) / SR
            place(out, (np.sin(2 * math.pi * 110 * tt) + 0.4 * lowpass(_noise(n, i), 600)) * np.exp(-tt * 30) * (0.7 - i * 0.18), tt0)
            tt0 += 0.42 - i * 0.12
        return out
    if name == "kick":
        n = int(0.15 * SR)
        tt = np.arange(n) / SR
        return (np.sin(2 * math.pi * 90 * tt) + lowpass(_noise(n, seed), 1500) * 0.6) * np.exp(-tt * 35) * 0.7
    if name == "applause":
        d = kw.get("dur", 3.0)
        out = np.zeros(int(d * SR))
        for i in range(int(d * 90)):
            n = int(0.02 * SR)
            c = bandpass(_noise(n, seed * 1000 + i), 800, 6000) * np.exp(-np.arange(n) / SR * 150)
            place(out, c * (0.3 + 0.7 * r.random()), r.random() * (d - 0.05))
        return out * np.sin(np.linspace(0, math.pi, len(out))) ** 0.3 * 0.35
    if name == "coins":
        out = np.zeros(int(0.9 * SR))
        for i in range(kw.get("n", 5)):
            place(out, sfx("clink", seed + i, f=3200 + 900 * r.random()) * 0.8, i * 0.07 + 0.05 * r.random())
        return out
    if name == "zip":
        d = 0.5
        tt = t_(d)
        x = bandpass(_noise(len(tt), seed), 2000, 7000) * (np.sin(2 * math.pi * 60 * tt) > 0)
        return x * 0.08
    if name == "click":
        n = int(0.02 * SR)
        return bandpass(_noise(n, seed), 1500, 6000) * np.exp(-np.arange(n) / SR * 300) * 0.3
    if name == "whoosh":
        d = 0.7
        tt = t_(d)
        x = bandpass(_noise(len(tt), seed), 500, 4000) * np.sin(np.linspace(0, math.pi, len(tt))) ** 2
        return x * 0.05
    if name == "tick":
        d = kw.get("dur", 3.0)
        out = np.zeros(int(d * SR))
        for i in range(int(d)):
            place(out, sfx("click", i) * 0.6, i)
        return out
    if name == "birds":
        d = kw.get("dur", 4.0)
        out = np.zeros(int(d * SR))
        for i in range(int(d * 1.5)):
            n = int(0.12 * SR)
            tt = np.arange(n) / SR
            f0 = 3000 + 1500 * r.random()
            ch = np.sin(2 * math.pi * np.cumsum(f0 + 900 * np.sin(2 * math.pi * 30 * tt)) / SR) * np.sin(np.linspace(0, math.pi, n))
            place(out, ch * 0.04, r.random() * (d - 0.2))
        return out
    if name == "heartbeat":
        out = np.zeros(int(1.0 * SR))
        for st in (0, 0.25):
            n = int(0.12 * SR)
            tt = np.arange(n) / SR
            place(out, np.sin(2 * math.pi * 55 * tt) * np.exp(-tt * 30) * 0.5, st)
        return out
    if name == "laugh_kid":
        return synth("hee hee!", "af_sky", 1.1, 1.28) * 0.5
    if name == "gasp":
        n = int(0.4 * SR)
        return bandpass(_noise(n, seed), 600, 3000) * np.sin(np.linspace(0, math.pi, n)) ** 2 * 0.12
    raise ValueError(f"unknown sfx {name}")


BABBLE_LINES = ["Did you see the game last night?", "I think it's on the second page.", "Can I borrow a pencil?",
                "We're going to Grandma's this weekend.", "That was so funny!", "Wait, which one is it?",
                "I like the blue one better.", "Okay, okay, let me try.", "Look at this one.", "My turn next!",
                "Where did you put it?", "I'm almost done.", "Is it lunch yet?", "No way!"]


def babble(kind="kids", dur=14.0, layers=6):
    path = os.path.join(CACHE, f"babble_{kind}_{int(dur)}.wav")
    if os.path.exists(path):
        a, _ = sf.read(path)
        return a
    rng = np.random.default_rng(3 if kind == "kids" else 4)
    voices = (["af_sky", "af_nova", "af_bella", "af_river", "af_nicole", "am_puck"] if kind == "kids"
              else ["af_sarah", "am_michael", "af_kore", "am_adam", "af_aoede", "am_eric"])
    out = np.zeros((int(dur * SR), 2))
    for li in range(layers):
        t = rng.random() * 1.5
        v = voices[li % len(voices)]
        pitch = (1.15 + 0.1 * rng.random()) if kind == "kids" else 1.0
        while t < dur:
            line = BABBLE_LINES[rng.integers(len(BABBLE_LINES))]
            a = synth(line, v, 1.0 + 0.1 * rng.random(), pitch)
            place(out, to_stereo(a, rng.uniform(-0.8, 0.8)) * 0.35, t)
            t += len(a) / SR + 0.4 + rng.random() * 1.5
    out = lowpass(out, 2600)
    out = reverb(out, 0.5, 1.4, 3000)
    sf.write(path, out, SR)
    return out


def ambience(kind, dur, seed=0):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    base = lowpass(rng.standard_normal((n, 2)), 500) * 0.006   # room tone
    if kind in ("room", "home", "bedroom", "library", None):
        pass
    if kind == "kitchen":
        tt = np.arange(n) / SR
        base += to_stereo(np.sin(2 * math.pi * 100 * tt) * 0.003)
    if kind in ("classroom", "hallway", "cafeteria", "school"):
        b = babble("kids")
        reps = int(math.ceil(n / len(b)))
        base += np.tile(b, (reps, 1))[:n] * (0.35 if kind == "classroom" else 0.6)
    if kind in ("party", "fair", "market", "stage_crowd", "gym"):
        b1, b2 = babble("kids"), babble("adults")
        reps = int(math.ceil(n / len(b1)))
        base += np.tile(b1, (reps, 1))[:n] * 0.4 + np.tile(b2, (reps, 1))[:n] * 0.35
    if kind in ("outdoor", "park", "yard", "field", "street"):
        base += lowpass(rng.standard_normal((n, 2)), 300) * 0.02
        place(base, to_stereo(sfx("birds", seed, dur=min(dur, 20))), 0.5)
        if kind in ("park", "field"):
            b = babble("kids")
            reps = int(math.ceil(n / len(b)))
            base += reverb(np.tile(b, (reps, 1))[:n] * 0.12, 0.7, 2.0, 2000)
    if kind == "night":
        tt = np.arange(n) / SR
        chirp = (np.sin(2 * math.pi * 4200 * tt) * (np.sin(2 * math.pi * 3 * tt) > 0.85)) * 0.004
        base += to_stereo(chirp, 0.5) + to_stereo(np.roll(chirp, SR // 3), -0.5)
    fi = int(min(1.0, dur / 4) * SR)
    base[:fi] *= np.linspace(0, 1, fi)[:, None]
    base[-fi:] *= np.linspace(1, 0, fi)[:, None]
    return base


# ============================================================== mix
# small, believable rooms per scene: (wet, seconds, brightness Hz, early-reflection delay ms)
ROOMS = {
    "bedroom":   (0.05, 0.35, 3800, 7),  "home": (0.06, 0.45, 4200, 9),  "room": (0.06, 0.45, 4200, 9),
    "kitchen":   (0.08, 0.55, 5200, 8),  "library": (0.07, 0.8, 3800, 14), "classroom": (0.10, 0.75, 4800, 13),
    "school":    (0.10, 0.75, 4800, 13), "cafeteria": (0.13, 0.95, 4800, 16), "hallway": (0.15, 1.1, 4200, 18),
    "gym":       (0.16, 1.4, 4200, 22),  "stage": (0.14, 1.3, 4200, 20),  "store": (0.08, 0.6, 5000, 10),
    "car":       (0.02, 0.15, 3000, 3),  "outdoor": (0.02, 0.2, 6000, 0), "park": (0.02, 0.2, 6000, 0),
    "street":    (0.03, 0.25, 6000, 0),  "yard": (0.02, 0.2, 6000, 0),
}


def room(x, kind, pan=0.0, narrator=False):
    """Place a (mono) voice inside the scene: a touch of early reflection +
    a short, dark tail.  Subtle on purpose - no obvious reverb."""
    if narrator:
        return reverb(to_stereo(x, 0), 0.04, 0.5, 6000)          # close, intimate
    wet, secs, bright, er = ROOMS.get(kind or "room", ROOMS["room"])
    st = to_stereo(x, pan * 0.35)
    if er:
        d = int(er / 1000 * SR)
        refl = np.zeros_like(st)
        refl[d:] += st[:-d, ::-1] * 0.10                          # crossed early reflection
        st = st + lowpass(refl, bright)
    return reverb(st, wet, secs, bright)


def duck_curve(speech_mask, depth_db=-10.0, look_ahead=0.20, attack=0.12, release=0.65):
    """Smooth music ducking: starts slightly before a line, eases down,
    and breathes back up slowly after it (no pumping, no abrupt steps)."""
    n = len(speech_mask)
    la = int(look_ahead * SR)
    m = np.zeros(n)
    m[:n - la] = speech_mask[la:]
    m = np.maximum(m, speech_mask)
    step = 240                                                    # control rate 200 Hz
    c = m[::step]
    env = np.zeros_like(c)
    a_c = 1 - math.exp(-step / (attack * SR))
    r_c = 1 - math.exp(-step / (release * SR))
    e = 0.0
    for i, v in enumerate(c):
        e += (v - e) * (a_c if v > e else r_c)
        env[i] = e
    env = np.interp(np.arange(n), np.arange(len(c)) * step, env)
    return 10 ** (depth_db * env / 20)


def mix(total, dialogue, sfx_events, amb_regions, music, out_path, room_kind=None):
    """dialogue: [(t, clip, pan, is_narrator[, room])], sfx_events: [(t, clip, gain, pan)],
    amb_regions: [(s, e, kind)], music: stereo array."""
    n = int(total * SR)
    dia = np.zeros((n, 2))
    speech_mask = np.zeros(n)
    for d in dialogue:
        t, clip, pan, narr = d[:4]
        kind = d[4] if len(d) > 4 else room_kind
        c = highpass(clip.copy(), 80)
        place(dia, room(c, kind, pan, narr), t)
        i = int(t * SR)
        speech_mask[i:min(n, i + len(clip))] = 1
    fx = np.zeros((n, 2))
    for t, clip, gain, pan in sfx_events:
        place(fx, to_stereo(clip, pan) * gain, t)
    amb = np.zeros((n, 2))
    for s, e, kind in amb_regions:
        if kind in (None, "none"):
            continue
        a = ambience(kind, e - s + 1.0, seed=int(s))
        place(amb, a, max(0, s - 0.5))
    # music ducking under speech (smooth, anticipatory)
    duck = duck_curve(speech_mask)
    mus = music[:n] if len(music) >= n else np.pad(music, ((0, n - len(music)), (0, 0)))
    mus = mus * duck[:, None]
    # ambience dips a little under dialogue too, so words stay in front
    amb = amb * (0.55 + 0.45 * duck_curve(speech_mask, depth_db=-4.0))[:, None] if len(amb) else amb
    mixd = dia * 1.0 + fx * 0.9 + amb * 0.9 + mus * db(-6)
    peak = np.max(np.abs(mixd)) or 1
    mixd = mixd / peak * 0.9
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "raw.wav")
        sf.write(raw, mixd, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                        "loudnorm=I=-15:TP=-1.5:LRA=11,alimiter=limit=0.82:level=false", "-ar", str(SR), out_path], check=True)
    # stems for troubleshooting
    stem_dir = os.path.join(os.path.dirname(out_path), "stems")
    os.makedirs(stem_dir, exist_ok=True)
    sf.write(os.path.join(stem_dir, "dialogue.wav"), dia, SR)
    sf.write(os.path.join(stem_dir, "music.wav"), mus, SR)
    sf.write(os.path.join(stem_dir, "fx_amb.wav"), fx + amb, SR)
    return out_path
