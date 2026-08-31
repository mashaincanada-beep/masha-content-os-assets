import numpy as np, wave, subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
UP = "/root/.claude/uploads/77e0ac3b-6a16-50fa-94dd-0b297bd4299b"
A = f"{UP}/a36acd05-642079489E5D40A88B62134611002467.mp4"
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")

SR = 48000
NARR_DUR = 73.77
END_DUR = 5.5
TOTAL = NARR_DUR + END_DUR
N = int(round(TOTAL*SR))

narr_wav = f"{W}/narration.wav"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-i", A, "-t", str(NARR_DUR), "-ac", "2", "-ar", str(SR),
                "-vn", narr_wav], check=True)
with wave.open(narr_wav, "rb") as w:
    raw = w.readframes(w.getnframes())
    narr = np.frombuffer(raw, dtype="<i2").astype(np.float64).reshape(-1, 2)/32768.0

mix = np.zeros((N, 2))
nc = min(len(narr), N)
mix[:nc] += narr[:nc]

t = np.arange(N)/SR

def env_exp(start, dec, amp=1.0):
    e = np.zeros(N); i = int(start*SR)
    if i >= N: return e
    k = np.arange(N-i)/SR
    e[i:] = amp*np.exp(-k/dec)
    return e

# ---- soft ambient pad bed ----
pad = np.zeros(N)
for f, g in [(130.81, .35), (164.81, .28), (196.00, .22), (261.63, .12)]:
    det = 1 + 0.0009*np.sin(2*np.pi*0.07*t + f*0.01)
    pad += g*np.sin(2*np.pi*f*det*t)
pad *= 0.045*(0.85 + 0.15*np.sin(2*np.pi*0.05*t))
fade = np.ones(N)
fl = int(1.2*SR); fade[:fl] = np.linspace(0, 1, fl)
fade[-int(2.0*SR):] = np.linspace(1, 0, int(2.0*SR))
pad *= fade

# ---- cute bubble-pop sfx: quick pitch-drop chirp + tiny sparkle ----
def bubble_pop(n_samp, f0, f1, amp, rise=False):
    tt = np.arange(n_samp)/SR
    dur = n_samp/SR
    if rise:
        freq = f1 + (f0-f1)*np.exp(-tt/(dur*0.35))
    else:
        freq = f0 + (f1-f0)*(1-np.exp(-tt/(dur*0.28)))
    phase = 2*np.pi*np.cumsum(freq)/SR
    env = np.sin(np.pi*np.clip(tt/dur, 0, 1))**0.7
    tone = np.sin(phase)*env
    sparkle = np.sin(2*np.pi*(freq*2.4)*tt)*env*0.25
    return (tone+sparkle)*amp

pops = np.zeros(N)
card_in_times  = [9.0, 24.0, 40.0, 56.0]
card_out_times = [13.5, 28.5, 44.5, 60.5]

for ct in card_in_times:
    i0 = int(ct*SR); dur_samp = int(0.16*SR)
    if i0+dur_samp > N: continue
    pops[i0:i0+dur_samp] += bubble_pop(dur_samp, 1500, 550, 0.55, rise=False)

for ct in card_out_times:
    i0 = int((ct-0.02)*SR); dur_samp = int(0.12*SR)
    if i0+dur_samp > N or i0 < 0: continue
    pops[i0:i0+dur_samp] += bubble_pop(dur_samp, 500, 1300, 0.32, rise=True)

# ---- soft chime at end-card reveal ----
chime = np.zeros(N)
for st, f, amp, dec in [(NARR_DUR, 880, .16, .35), (NARR_DUR+0.08, 1318.5, .13, .4), (NARR_DUR+0.16, 1760, .11, .5)]:
    e = env_exp(st, dec, amp)
    chime += np.sin(2*np.pi*f*t)*e

mono_extra = pad + pops + chime
mix[:, 0] += mono_extra
mix[:, 1] += mono_extra

mix = np.tanh(mix*1.15)
peak = np.abs(mix).max()
if peak > 0:
    mix = mix/peak*0.92

pcm = (mix*32767).astype("<i2")
out_wav = f"{W}/final_audio.wav"
with wave.open(out_wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out_wav, "duration", TOTAL)
