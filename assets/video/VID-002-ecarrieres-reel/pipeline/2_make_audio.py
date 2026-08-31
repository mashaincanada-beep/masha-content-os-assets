import numpy as np, wave, subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
UP = "/root/.claude/uploads/77e0ac3b-6a16-50fa-94dd-0b297bd4299b"
A = f"{UP}/a36acd05-642079489E5D40A88B62134611002467.mp4"
WORK = "/tmp/claude-0/-home-user-masha-content-os-assets/77e0ac3b-6a16-50fa-94dd-0b297bd4299b/scratchpad/work"

SR = 48000
NARR_DUR = 73.77
END_DUR = 5.5
TOTAL = NARR_DUR + END_DUR
N = int(round(TOTAL * SR))

# ---- extract narration audio from clip A ----
narr_wav = f"{WORK}/narration.wav"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-i", A, "-t", str(NARR_DUR), "-ac", "2", "-ar", str(SR),
                "-vn", narr_wav], check=True)

with wave.open(narr_wav, "rb") as w:
    nframes = w.getnframes()
    raw = w.readframes(nframes)
    narr = np.frombuffer(raw, dtype="<i2").astype(np.float64).reshape(-1, 2) / 32768.0

mix = np.zeros((N, 2))
n_copy = min(len(narr), N)
mix[:n_copy] += narr[:n_copy]

t = np.arange(N) / SR
rng = np.random.default_rng(7)

def env_exp(start, dec, amp=1.0, n=N):
    e = np.zeros(n); i = int(start * SR)
    if i >= n: return e
    k = np.arange(n - i) / SR
    e[i:] = amp * np.exp(-k / dec)
    return e

def lp_1pole(x, cutoff):
    c = np.full(len(x), cutoff, float) if np.isscalar(cutoff) else cutoff
    a = 1 - np.exp(-2*np.pi*c/SR)
    y = np.empty(len(x)); prev = 0.0
    for i in range(len(x)):
        prev += a[i]*(x[i]-prev)
        y[i] = prev
    return y

# ---- soft ambient pad bed (very low, warm, unobtrusive) ----
pad = np.zeros(N)
for f, g in [(130.81, .35), (164.81, .28), (196.00, .22), (261.63, .12)]:  # C3 E3 G3 C4 chord
    det = 1 + 0.0009*np.sin(2*np.pi*0.07*t + f*0.01)
    pad += g*np.sin(2*np.pi*f*det*t)
pad *= 0.045 * (0.85 + 0.15*np.sin(2*np.pi*0.05*t))
pad_fade = np.ones(N)
fade_len = int(1.2*SR)
pad_fade[:fade_len] = np.linspace(0, 1, fade_len)
pad_fade[-int(2.0*SR):] = np.linspace(1, 0, int(2.0*SR))
pad *= pad_fade

# ---- whoosh SFX at each hard cut (11 cuts) ----
cut_times = [9.0, 13.8, 24.0, 28.8, 40.0, 44.8, 56.0, 60.8, 73.77]
whoosh = np.zeros(N)
for ct in cut_times:
    dur = 0.22
    i0 = int(ct*SR) - int(0.05*SR)
    i1 = i0 + int(dur*SR)
    if i0 < 0 or i1 > N: continue
    seg_n = i1 - i0
    tt = np.arange(seg_n)/SR
    noise = rng.normal(0, 1, seg_n)
    sweep_cut = 400 + 5200*(tt/dur)
    filt = lp_1pole(noise, sweep_cut)
    env = np.sin(np.pi*tt/dur)**1.5
    whoosh[i0:i1] += filt*env*0.5

# ---- soft chime at end card reveal (t = NARR_DUR) ----
chime = np.zeros(N)
for st, f, amp, dec in [(NARR_DUR, 880, .16, .35), (NARR_DUR+0.08, 1318.5, .13, .4), (NARR_DUR+0.16, 1760, .11, .5)]:
    e = env_exp(st, dec, amp)
    chime += np.sin(2*np.pi*f*t)*e

mono_extra = pad + whoosh + chime
mix[:, 0] += mono_extra
mix[:, 1] += mono_extra

# gentle soft-limit + normalize
mix = np.tanh(mix*1.15)
peak = np.abs(mix).max()
if peak > 0:
    mix = mix / peak * 0.92

pcm = (mix*32767).astype("<i2")
out_wav = f"{WORK}/final_audio.wav"
with wave.open(out_wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out_wav, "duration", TOTAL)
