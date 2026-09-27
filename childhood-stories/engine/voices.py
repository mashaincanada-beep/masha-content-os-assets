#!/usr/bin/env python3
"""MIC Study voice cast tool (voice system v2).

  python3 engine/voices.py status     # which provider will be used, which cast voices are missing
  python3 engine/voices.py design     # create the missing custom voices with ElevenLabs Voice Design
                                      #   (narrator, children, Grandma Rosa), save them to the account,
                                      #   write their voice_id into engine/voice_cast.json
  python3 engine/voices.py audition   # render a short test line per cast voice to engine/_auditions/

After `design`, commit engine/voice_cast.json so every future film uses the same voices.
"""
import base64, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from cs import voice as V, audio as A

# natural preview text per role (>= 100 characters, conversational, no lesson)
SAMPLES = {
    "narrator": "Some nights the reading goes slowly. The words get stuck, and the story waits... But one page at a time, "
                "something quiet starts to change. And one evening, nobody has to ask.",
    "child": "Wait, wait... I think I know this one. Um... It's not that I can't. It's just... it goes really fast, you know? "
             "Can we do it again? Just one more time. Okay. I'm ready.",
    "teen": "It's fine. Honestly, it's not a big deal... I just didn't get it the first time. Can you, like... show me again? "
            "Slower this time. Yeah. Okay, that actually makes sense.",
    "elder": "Come here, mijo, sit with me a minute... You know, when I was your age, I was scared of numbers too. "
             "Nobody is born knowing. We learn it slowly, together.",
}
# preferred median pitch window (Hz) for picking between the 3 design previews
TARGET = {6: (250, 340), 7: (245, 335), 8: (235, 325), 9: (225, 315), 10: (220, 310),
          11: (210, 300), 12: (200, 290), 13: (165, 260)}


def _pick(previews, name, cfg):
    best = None
    for p in previews:
        raw = base64.b64decode(p["audio_base_64"])
        try:
            a, sr = sf.read(io.BytesIO(raw))
        except Exception:
            import subprocess, tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
                f.write(raw); f.flush()
                out = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f.name, "-f", "wav", "-"], capture_output=True).stdout
            a, sr = sf.read(io.BytesIO(out))
        if a.ndim > 1:
            a = a.mean(axis=1)
        a = resample_poly(a, A.SR, sr)
        role = "narrator" if name == "narrator" else ("young_child" if cfg.get("age", 30) <= 8 else
                                                      "older_child" if cfg.get("age") else "adult")
        chk = V.analyse(a, "", role)
        med = chk.get("f0_median", 0)
        lo, hi = TARGET.get(cfg.get("age"), (140, 260))
        dist = 0 if lo <= med <= hi else min(abs(med - lo), abs(med - hi))
        score = dist + 40 * len([x for x in chk["problems"] if "monotone" in x or "high" in x]) - 10 * chk.get("f0_spread_st", 0)
        print(f"   preview {p['generated_voice_id'][:8]}  f0={med}Hz spread={chk.get('f0_spread_st')}st  score={score:.0f}")
        if best is None or score < best[0]:
            best = (score, p, a)
    return best


def design(only=None):
    cast = V.load_cast()
    changed = False
    os.makedirs(os.path.join(V.ENGINE, "_auditions"), exist_ok=True)
    for name, cfg in cast["voices"].items():
        if cfg.get("voice_id") or not cfg.get("design") or (only and name not in only):
            continue
        kind = "narrator" if name == "narrator" else ("elder" if "grand" in name else
                                                      "teen" if cfg.get("age", 0) >= 12 else "child")
        print(f"- designing {name} ...")
        try:
            r = V._req("POST", "/text-to-voice/design", {
                "voice_description": cfg["design"], "model_id": cast.get("design_model", "eleven_ttv_v3"),
                "text": SAMPLES[kind], "guidance_scale": 5, "loudness": 0.5}, timeout=300)
        except Exception as e:
            print(f"   FAILED: {e}")
            continue
        prev = r.get("previews", [])
        if not prev:
            print("   FAILED: no previews returned (the provider may not allow this description)")
            continue
        score, p, a = _pick(prev, name, cfg)
        sf.write(os.path.join(V.ENGINE, "_auditions", f"{name}.wav"), a, A.SR)
        c = V._req("POST", "/text-to-voice", {"voice_name": f"MIC Study - {name}", "voice_description": cfg["design"],
                                                "generated_voice_id": p["generated_voice_id"]}, timeout=120)
        cfg["voice_id"] = c["voice_id"]
        changed = True
        print(f"   saved as {c['voice_id']}")
        json.dump(cast, open(V.CAST_FILE, "w"), indent=2)
    return changed


def status():
    st = V.provider_status()
    cast = V.load_cast()
    print("provider:", st["provider"], "-", st["reason"])
    miss = [k for k, v in cast["voices"].items() if not v.get("voice_id")]
    print("cast voices missing:", ", ".join(miss) or "none")
    if st["provider"] == "elevenlabs":
        try:
            sub = V._req("GET", "/user/subscription", timeout=30)
            print(f"plan: {sub.get('tier')}  characters used {sub.get('character_count')}/{sub.get('character_limit')}  "
                  f"custom voices {sub.get('voice_slots_used', '?')}/{sub.get('voice_limit')}")
        except Exception as e:
            print("subscription check failed:", e)


def audition():
    out = os.path.join(V.ENGINE, "_auditions")
    os.makedirs(out, exist_ok=True)
    cast = json.load(open(os.path.join(V.ENGINE, "cast.json")))
    for name in V.load_cast()["voices"]:
        spec = cast.get(name, {"kind": "adult"})
        line = ("I... don't know this word. |0.4| Can you read it to me?" if spec.get("kind") == "child" else
                "Sometimes practice shows up far from the page." if name == "narrator" else
                "Hey. |0.3| Take your time. We're not in a hurry.")
        a, meta = V.speak(name, spec, {"line": line, "emo": "hesitant" if spec.get("kind") == "child" else "reassuring"})
        sf.write(os.path.join(out, f"{name}_line.wav"), a, A.SR)
        print(f"{name:13s} {meta['provider']:16s} f0={meta.get('f0_median')} wps={meta.get('wps')} problems={meta['problems']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "design":
        if V.provider_status()["provider"] != "elevenlabs":
            sys.exit("PREMIUM VOICES UNAVAILABLE: " + V.provider_status()["reason"])
        design(sys.argv[2:] or None)
        status()
    elif cmd == "audition":
        audition()
    else:
        status()
