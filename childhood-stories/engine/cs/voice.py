"""MIC Study Childhood Stories - VOICE SYSTEM v2 (performance voices).

Quality rule (Maria, Sept 2026): voice acting matters as much as the picture.
A beautiful film with robotic dialogue does not pass QC.

Provider order
  1. ElevenLabs (eleven_v3, expressive, audio tags)  - needs an API key
  2. Kokoro (local, basic)                             - LAST-RESORT FALLBACK only.
     Using it is always reported, and a film voiced with it is never
     published automatically (qc blocks it).

Every line is generated on its own (never a whole scene in one block), with
an acting intention (`emo`) per line, then cleaned up (level, gentle EQ,
de-ess, light compression) and checked.  Lines that fail the voice checks are
regenerated automatically (up to MAX_TAKES) before the film is rendered.

API key lookup (never commit a key - the repo is public):
  $ELEVENLABS_API_KEY, else the first line of ~/.config/micstudy/elevenlabs.key
"""
import base64, hashlib, json, math, os, re, subprocess, tempfile, time, urllib.error, urllib.request
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from . import audio as A

SR = A.SR
ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAST_FILE = os.path.join(ENGINE, "voice_cast.json")
KEY_FILE = os.path.expanduser("~/.config/micstudy/elevenlabs.key")
API = "https://api.elevenlabs.io/v1"
MAX_TAKES = 3

# acting intentions -> ElevenLabs v3 audio tag + stability (lower = more expressive)
EMOTIONS = {
    "neutral":     ("",                0.5),
    "curious":     ("[curious]",       0.5),
    "hesitant":    ("[hesitant]",      0.5),
    "embarrassed": ("[embarrassed]",   0.5),
    "frustrated":  ("[frustrated]",    0.35),
    "tired":       ("[tired]",         0.5),
    "excited":     ("[excited]",       0.35),
    "quiet":       ("[softly]",        0.5),
    "whisper":     ("[whispers]",      0.5),
    "reassuring":  ("[warmly]",        0.5),
    "playful":     ("[playfully]",     0.35),
    "proud":       ("[proudly]",       0.5),
    "nervous":     ("[nervous]",       0.5),
    "relieved":    ("[relieved]",      0.5),
    "thoughtful":  ("[thoughtfully]",  0.5),
    "sad":         ("[sadly]",         0.5),
    "tender":      ("[gently]",        0.5),
    "storytelling": ("[softly]",       0.5),
}
# face expression -> default acting intention (used when a line has no "emo")
EXPR_TO_EMO = {"curious": "curious", "unsure": "hesitant", "embarrassed": "embarrassed", "sad": "sad",
               "disappointed": "sad", "tender": "tender", "happy": "playful", "proud": "proud", "focused": "thoughtful",
               "determined": "proud", "hopeful": "curious", "tired": "tired", "calm": "neutral", "worried": "nervous",
               "nervous": "nervous", "excited": "excited", "frustrated": "frustrated", "relieved": "relieved"}

TAG_RE = re.compile(r"\[[a-zA-Z][a-zA-Z \-']*\]")
PAUSE_RE = A.PAUSE_RE

_status = {"provider": None, "reason": "", "fallback_lines": 0, "premium_lines": 0, "regenerated": 0}


# ------------------------------------------------------------------ provider
def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k and os.path.exists(KEY_FILE):
        lines = open(KEY_FILE).read().strip().splitlines()
        k = lines[0].strip() if lines else ""
    return k


def _req(method, path, body=None, key=None, timeout=120, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"xi-api-key": key or api_key(), "Content-Type": "application/json",
                                        "Accept": "audio/*" if raw else "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                b = resp.read()
                return b if raw else json.loads(b or b"{}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")[:400]
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"ElevenLabs HTTP {e.code}: {msg}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"ElevenLabs unreachable: {e}")


def provider_status(check=True):
    """Decide the provider once per run. Returns dict(provider, reason)."""
    if _status["provider"]:
        return _status
    cast = load_cast()
    if os.environ.get("MICSTUDY_VOICE_PROVIDER") == "kokoro":
        _status.update(provider="kokoro", reason="forced by MICSTUDY_VOICE_PROVIDER=kokoro")
        return _status
    if not api_key():
        _status.update(provider="kokoro", reason="PREMIUM VOICES UNAVAILABLE: no ElevenLabs API key "
                       "(ELEVENLABS_API_KEY or ~/.config/micstudy/elevenlabs.key)")
        return _status
    missing = [c for c, v in cast["voices"].items() if not v.get("voice_id")]
    if check:
        try:
            _req("GET", "/user", timeout=30)
        except Exception as e:
            _status.update(provider="kokoro", reason=f"PREMIUM VOICES UNAVAILABLE: {e}")
            return _status
    _status.update(provider="elevenlabs", reason="ok", missing_voice_ids=missing)
    return _status


def load_cast():
    return json.load(open(CAST_FILE))


# ------------------------------------------------------------------ text prep
def spoken_parts(text):
    """Split on long pauses (|>=0.8|); short pauses become '...' so the actor
    keeps one natural breath.  Returns [('say', str) | ('rest', seconds)]."""
    out, cur = [], ""
    bits = PAUSE_RE.split(text)
    for i, b in enumerate(bits):
        if i % 2 == 1:
            s = float(b)
            if s >= 0.8:
                if cur.strip():
                    out.append(("say", cur.strip()))
                cur = ""
                out.append(("rest", s))
            else:
                cur = cur.rstrip()
                cur += ("" if cur.endswith(("...", "…")) else "...") + " "
        else:
            cur += b
    if cur.strip():
        out.append(("say", cur.strip()))
    return [(k, re.sub(r"\s+", " ", v) if k == "say" else v) for k, v in out]


def display_text(t):
    return re.sub(r"\s+", " ", TAG_RE.sub("", PAUSE_RE.sub(" ", t))).strip()


# ------------------------------------------------------------------ post
def _ff(a, chain):
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
        sf.write(i, a, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", i, "-af", chain, "-ar", str(SR), o], check=True)
        b, _ = sf.read(o)
    return b


def polish(a, role="child"):
    """Clean one line: gentle EQ, de-ess, light compression, consistent level.
    Deliberately subtle - no effects, no reverb (the room is added in the mix)."""
    if len(a) < SR * 0.05:
        return a
    chain = ("highpass=f=75,"
             "equalizer=f=220:t=q:w=1.0:g=-1.2,"          # less boxiness
             "equalizer=f=3200:t=q:w=1.4:g=0.8,"          # presence
             "deesser=i=0.35:m=0.5:f=0.5,"
             "equalizer=f=9500:t=h:w=0.7:g=-1.5,"         # tame synthetic fizz
             "acompressor=threshold=-22dB:ratio=2.2:attack=10:release=140:makeup=1.5")
    b = _ff(a, chain)
    # level: active-speech RMS to -20 dBFS
    fr = int(0.02 * SR)
    n = len(b) // fr
    if n:
        r = np.sqrt(np.mean(b[:n * fr].reshape(n, fr) ** 2, axis=1))
        act = r[r > np.max(r) * 0.12]
        rms = np.sqrt(np.mean(act ** 2)) if len(act) else np.sqrt(np.mean(b ** 2))
        if rms > 0:
            b = b * (A.db(-20) / rms)
    pk = np.max(np.abs(b)) or 1
    if pk > 0.95:
        b = b / pk * 0.95
    return b


def _tempo(a, speed):
    if abs(speed - 1.0) < 0.015:
        return a
    return _ff(a, f"atempo={max(0.7, min(1.3, speed)):.4f}")


# ------------------------------------------------------------------ engines
def _eleven(text, vcfg, emo, take, prev_text="", next_text=""):
    model = vcfg.get("model") or load_cast().get("model", "eleven_v3")
    tag, stab = EMOTIONS.get(emo or "neutral", ("", 0.5))
    stab = vcfg.get("stability", stab)
    if take > 1:   # a retake: nudge towards a different, still natural read
        stab = [0.5, 0.35, 0.65][(take - 1) % 3]
    t = text if (not tag or TAG_RE.match(text)) else f"{tag} {text}"
    body = {"text": t, "model_id": model, "seed": int(hashlib.md5(t.encode()).hexdigest()[:6], 16) + take,
            "voice_settings": {"stability": stab, "similarity_boost": vcfg.get("similarity", 0.8)}}
    if model != "eleven_v3":
        body["text"] = TAG_RE.sub("", t).strip()
        body["voice_settings"].update(style=vcfg.get("style", 0.35), use_speaker_boost=True)
        if prev_text:
            body["previous_text"] = display_text(prev_text)
        if next_text:
            body["next_text"] = display_text(next_text)
    pcm = _req("POST", f"/text-to-speech/{vcfg['voice_id']}?output_format=pcm_44100", body, raw=True, timeout=180)
    a = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    return resample_poly(a, SR, 44100)


def _kokoro(text, fb):
    return A.synth(TAG_RE.sub("", text), fb.get("id", "af_heart"), fb.get("speed", 1.0), fb.get("pitch", 1.0))


# ------------------------------------------------------------------ checks
_wm = None


def _whisper():
    global _wm
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _wm


def analyse(a, text, role, age=None):
    """Measurable voice checks for one line. Returns dict with 'problems'."""
    from difflib import SequenceMatcher
    from . import qc as Q
    res = {"problems": []}
    dur = len(a) / SR
    # intelligibility
    try:
        segs, _ = _whisper().transcribe(a.astype(np.float32) if SR == 16000 else resample_poly(a, 16000, SR).astype(np.float32),
                                        beam_size=1, vad_filter=False, language="en")
        heard = " ".join(s.text for s in segs)
        sc = SequenceMatcher(None, Q._norm(display_text(text)), Q._norm(heard)).ratio()
        res["heard"], res["clarity"] = heard.strip(), round(sc, 2)
        numeric = bool(re.search(r"\d", heard))          # "$1.15" vs "a dollar fifteen" is a spelling issue, not speech
        if sc < 0.72 and len(Q._norm(display_text(text))) > 5 and not numeric:
            res["problems"].append(f"unclear/mispronounced (heard '{heard.strip()[:60]}')")
    except Exception as e:  # pragma: no cover
        res["clarity_error"] = str(e)[:100]
    # pace: words per second, not counting deliberate pauses longer than 0.3 s
    words = len(display_text(text).split())
    fr = int(0.02 * SR)
    n = len(a) // fr
    talk_t = dur
    if n:
        r = np.sqrt(np.mean(a[:n * fr].reshape(n, fr) ** 2, axis=1))
        quiet = r < np.max(r) * 0.03
        gaps, run = 0, 0
        for q in quiet:
            run = run + 1 if q else 0
            if run == 16:
                gaps += 16
            elif run > 16:
                gaps += 1
        talk_t = max(0.3, dur - gaps * 0.02)
    wps = words / talk_t
    res["wps"] = round(wps, 2)
    lim = {"narrator": 2.9, "young_child": 3.4, "older_child": 3.6}.get(role, 3.7)
    if words >= 4 and wps > lim:
        res["problems"].append(f"too fast ({wps:.1f} words/s, max {lim})")
    # pitch: too high (cartoon) / monotone (robotic)
    try:
        import parselmouth
        snd = parselmouth.Sound(a.astype(np.float64), SR)
        f0 = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=650).selected_array["frequency"]
        f0 = f0[f0 > 0]
        if len(f0) > 20:
            med = float(np.median(f0))
            st = 12 * np.log2(f0 / med)
            spread = float(np.std(st))
            res["f0_median"], res["f0_spread_st"] = round(med), round(spread, 2)
            ceiling = {"young_child": 390, "older_child": 360}.get(role, 330)
            if med > ceiling:
                res["problems"].append(f"too high-pitched ({med:.0f} Hz median)")
            # an adult voice pretending to be a child sits too LOW for the child's age
            if role in ("young_child", "older_child"):
                ag = age or (7 if role == "young_child" else 10)
                floor = 230 if ag <= 8 else 215 if ag <= 11 else 150
                if med < floor:
                    res["problems"].append(f"sounds like an adult, not a {ag}-year-old ({med:.0f} Hz median)")
            if dur > 1.4 and spread < 1.1:
                res["problems"].append(f"monotone ({spread:.1f} semitone spread)")
    except Exception as e:  # pragma: no cover
        res["pitch_error"] = str(e)[:100]
    if np.mean(np.abs(a) > 0.985) > 0.001:
        res["problems"].append("clipping / harsh artifacts")
    return res


def role_of(who, spec):
    if who == "narrator":
        return "narrator"
    if spec.get("kind") == "child":
        return "young_child" if spec.get("age", 9) <= 8 else "older_child"
    r = (spec.get("role") or "").lower()
    if "grand" in r:
        return "elder"
    if "mom" in r or "mother" in r:
        return "mother"
    if "dad" in r or "father" in r:
        return "father"
    return "adult"


# ------------------------------------------------------------------ main entry
_line_log = []
_pool_map = {}


def _pool_voice(base, spec, cast):
    """Voice for a character outside the fixed cast, stable within one film."""
    if base in _pool_map:
        return _pool_map[base]
    used = {v.get("voice_id") for v in _pool_map.values()}
    if spec.get("kind") == "child":
        age = spec.get("age", 9)
        kids = sorted([(abs(v.get("age", 9) - age), k) for k, v in cast["voices"].items()
                       if v.get("age") and v.get("voice_id") and v["voice_id"] not in used])
        cfg = dict(cast["voices"][kids[0][1]]) if kids else {}
        cfg["note"] = f"one-off child voiced with recurring voice '{kids[0][1]}'" if kids else "no child voice available"
    else:
        pool = cast["pools"]["adult_male" if spec.get("sex") == "m" else "adult_female"]
        vid = next((p for p in pool if p not in used), pool[0])
        cfg = {"voice_id": vid, "speed": 0.97}
    _pool_map[base] = cfg
    return cfg


def speak(who, spec, item, prev_item=None, next_item=None):
    """Voice one script line.  Returns (clip, meta)."""
    st = provider_status()
    base = who.split("#")[0]
    text = item.get("say", item["line"])
    emo = item.get("emo") or EXPR_TO_EMO.get(item.get("expr") or "", "storytelling" if base == "narrator" else "neutral")
    role = role_of(base, spec)
    cast = load_cast()
    vcfg = cast["voices"].get(base) or _pool_voice(base, spec, cast)
    fb = (spec.get("voice") or {}) if base != "narrator" else cast.get("narrator_fallback", {"id": "af_heart", "speed": 0.92})
    speed = item.get("speed", vcfg.get("speed", 1.0))
    meta = {"who": who, "role": role, "emo": emo, "text": display_text(item["line"])}
    use_premium = st["provider"] == "elevenlabs" and vcfg.get("voice_id")
    if st["provider"] == "elevenlabs" and not vcfg.get("voice_id"):
        meta["note"] = f"no ElevenLabs voice for '{base}' in voice_cast.json - run engine/voices.py design"
    best = None
    takes = MAX_TAKES if use_premium else 1
    for take in range(1, takes + 1):
        key = hashlib.md5(json.dumps([text, emo, vcfg.get("voice_id"), cast.get("model"), take, speed,
                                      bool(use_premium), fb, 5]).encode()).hexdigest()
        path = os.path.join(A.CACHE, f"v2_{key}.wav")
        if os.path.exists(path):
            a, _ = sf.read(path)
        else:
            if use_premium:
                chunks = []
                for kind, v in spoken_parts(text):
                    if kind == "rest":
                        chunks.append(np.zeros(int(v * SR)))
                    else:
                        c = _eleven(v, vcfg, emo, take,
                                    prev_item.get("line", "") if prev_item else "",
                                    next_item.get("line", "") if next_item else "")
                        chunks.append(A._trim(c, thr=0.01, pad=0.06))
                a = np.concatenate(chunks) if chunks else np.zeros(1)
                a = _tempo(a, speed)
            else:
                a = _kokoro(text, fb)   # speed already applied by Kokoro
                a = _tempo(a, 1.0)
            a = polish(a, role)
            sf.write(path, a, SR)
        chk = analyse(a, item["line"], role, spec.get("age"))
        score = len(chk["problems"]) * 10 - chk.get("clarity", 0.8)
        if best is None or score < best[0]:
            best = (score, a, chk, take)
        if not chk["problems"]:
            break
        if use_premium and take < takes:
            _status["regenerated"] += 1
    _, a, chk, take = best
    meta.update(provider="elevenlabs" if use_premium else "kokoro-fallback", take=take, **chk)
    if use_premium:
        _status["premium_lines"] += 1
    else:
        _status["fallback_lines"] += 1
    _line_log.append(meta)
    return a, meta


def report():
    """Summary for render_log / qc."""
    st = dict(_status)
    st["lines"] = list(_line_log)
    return st
