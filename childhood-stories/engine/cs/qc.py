"""MIC Study Childhood Stories - automatic quality control.

run_qc(episode_dir) checks the rendered files against the fail-safe list and
writes qc/qc.json plus contact sheets for a visual review.  It returns the
report dict; report["pass"] is False when anything blocks publishing.

Visual items a machine cannot judge (faces, hands, text clipping inside
art, logo look) are covered by the contact sheets, which the producer must
open and look at before publishing.
"""
import glob, json, math, os, re, subprocess
from difflib import SequenceMatcher


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                       capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _num_words(n):
    n = int(n)
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        # speech often says 425 as "four twenty five"
        return ONES[n // 100] + " " + (_num_words(n % 100) if n % 100 else "hundred")
    return " ".join(_num_words(int(d)) for d in str(n))


def _norm(s):
    s = s.lower().replace("’", "'").replace("$", " ")
    s = re.sub(r"(\d+)\.(\d+)", lambda m: _num_words(m.group(1)) + " " + _num_words(m.group(2)), s)
    s = re.sub(r"\d+", lambda m: " " + _num_words(m.group(0)) + " ", s)
    s = s.replace("-", " ")
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def contact_sheets(ep_dir, every=2.5):
    """Frames from the FINAL upload file (grading + compression included)."""
    from PIL import Image, ImageDraw
    fdir = os.path.join(ep_dir, "qc", "frames")
    os.makedirs(fdir, exist_ok=True)
    for f in glob.glob(os.path.join(fdir, "*.jpg")):
        os.remove(f)
    subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(ep_dir, "upload.mp4"), "-vf", f"fps=1/{every}",
                    "-q:v", "3", os.path.join(fdir, "f_%03d.jpg")], check=True)
    frames = sorted(glob.glob(os.path.join(fdir, "f_*.jpg")))
    sheets = []
    per = 12
    for k in range(0, len(frames), per):
        grp = frames[k:k + per]
        tw, th = 270, 480
        sheet = Image.new("RGB", (tw * 4, (th + 30) * math.ceil(len(grp) / 4)), "white")
        d = ImageDraw.Draw(sheet)
        for i, f in enumerate(grp):
            im = Image.open(f).convert("RGB").resize((tw, th))
            x, y = (i % 4) * tw, (i // 4) * (th + 30)
            sheet.paste(im, (x, y + 30))
            n = int(os.path.basename(f)[2:5])
            d.text((x + 6, y + 8), f"{(n - 1) * every:.1f}s", fill="black")
        out = os.path.join(ep_dir, "qc", f"contact_{k // per + 1:02d}.jpg")
        sheet.save(out, quality=88)
        sheets.append(out)
    return sheets


def run_qc(ep_dir, min_dur=105, max_dur=135, whisper_model="base.en"):
    rep = {"checks": {}, "blocking": [], "warnings": []}
    up = os.path.join(ep_dir, "upload.mp4")
    master = os.path.join(ep_dir, "master.mp4")
    cover = os.path.join(ep_dir, "cover.png")
    tl = json.load(open(os.path.join(ep_dir, "timeline.json")))
    rl = json.load(open(os.path.join(ep_dir, "render_log.json"))) if os.path.exists(os.path.join(ep_dir, "render_log.json")) else {}
    for f in (up, master, cover):
        if not os.path.exists(f):
            rep["blocking"].append(f"missing file {os.path.basename(f)}")
    if rep["blocking"]:
        rep["pass"] = False
        return rep
    info = probe(up)
    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    dur = float(info["format"]["duration"])
    size = os.path.getsize(up)
    rep["checks"]["duration_s"] = round(dur, 2)
    rep["checks"]["upload_bytes"] = size
    if not (min_dur <= dur <= max_dur):
        rep["blocking"].append(f"duration {dur:.1f}s outside {min_dur}-{max_dur}s")
    if not v:
        rep["blocking"].append("no video stream")
    else:
        vs = v[0]
        rep["checks"]["video"] = f'{vs["width"]}x{vs["height"]} {vs["codec_name"]} {vs.get("pix_fmt")} {vs.get("r_frame_rate")}'
        if (vs["width"], vs["height"]) != (1080, 1920):
            rep["blocking"].append("resolution is not 1080x1920")
        if vs["codec_name"] != "h264" or vs.get("pix_fmt") != "yuv420p":
            rep["blocking"].append("codec is not H.264 yuv420p")
        if vs.get("r_frame_rate") not in ("30/1", "30000/1000"):
            rep["blocking"].append(f"frame rate {vs.get('r_frame_rate')} is not 30")
    if not a:
        rep["blocking"].append("no audio stream")
    if size > 9.5e6:
        rep["blocking"].append(f"upload copy is {size / 1e6:.1f} MB (limit 9.5 MB)")
    # decode whole file: broken frames / black / frozen
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", up, "-vf", "blackdetect=d=0.6:pix_th=0.06,freezedetect=n=0.0005:d=6",
                        "-af", "volumedetect,silencedetect=n=-45dB:d=4", "-f", "null", "-"], capture_output=True, text=True)
    r2 = subprocess.run(["ffmpeg", "-i", up, "-vf", "blackdetect=d=0.6:pix_th=0.06,freezedetect=n=0.0005:d=6",
                         "-af", "volumedetect,silencedetect=n=-45dB:d=4", "-f", "null", "-"], capture_output=True, text=True)
    log = r2.stderr
    if r.stderr.strip():
        rep["blocking"].append("decode errors: " + r.stderr.strip()[:300])
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)
    bad_black = [(float(s), float(e)) for s, e in blacks if float(s) > 0.8 and float(e) < dur - 1.0]
    if bad_black:
        rep["blocking"].append(f"unexpected black frames at {bad_black}")
    freezes = re.findall(r"freeze_start: ([\d.]+)", log)
    if freezes:
        rep["warnings"].append(f"long still stretches (>6 s) start at {freezes[:5]} - check they are intentional")
    mv = re.search(r"mean_volume: ([-\d.]+) dB", log)
    mx = re.search(r"max_volume: ([-\d.]+) dB", log)
    rep["checks"]["mean_volume_db"] = float(mv.group(1)) if mv else None
    rep["checks"]["max_volume_db"] = float(mx.group(1)) if mx else None
    if mv and float(mv.group(1)) < -35:
        rep["blocking"].append("audio is nearly silent")
    sil = re.findall(r"silence_start: ([\d.]+)", log)
    if len(sil) > 2:
        rep["warnings"].append(f"{len(sil)} silent stretches over 4 s")
    # speech check: every line must be heard at the right time
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(whisper_model, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(master, word_timestamps=True, vad_filter=False, beam_size=1)
        words = [(w.start, w.end, w.word) for s in segs for w in (s.words or [])]
        bad = []
        scores = []
        for ln in tl["lines"]:
            heard = " ".join(w for s, e, w in words if s >= ln["t0"] - 0.6 and e <= ln["t1"] + 0.8)
            sc = SequenceMatcher(None, _norm(ln["text"]), _norm(heard)).ratio()
            scores.append(sc)
            if sc < 0.55 and len(_norm(ln["text"])) > 6:
                bad.append({"line": ln["text"], "heard": heard.strip(), "at": round(ln["t0"], 2), "score": round(sc, 2)})
        rep["checks"]["speech_match_avg"] = round(sum(scores) / max(1, len(scores)), 3)
        rep["checks"]["lines"] = len(tl["lines"])
        if bad:
            if len(bad) > max(2, 0.2 * len(tl["lines"])):
                rep["blocking"].append(f"{len(bad)} dialogue lines not understood at their timing")
            else:
                rep["warnings"].append("lines hard to understand (check wording/voice)")
            rep["checks"]["unclear_lines"] = bad
    except Exception as e:  # pragma: no cover
        rep["warnings"].append(f"speech check skipped: {e}")
    # VOICE QUALITY GATE (voice system v2): robotic dialogue must not pass
    vs = tl.get("voice", {})
    vlines = [ln for ln in tl["lines"] if ln.get("voice")]
    rep["checks"]["voice_provider"] = vs.get("provider")
    rep["checks"]["voice_regenerated_lines"] = vs.get("regenerated", 0)
    if vs.get("fallback_lines"):
        rep["blocking"].append(f"PREMIUM VOICES UNAVAILABLE ({vs.get('reason', '')}) - {vs['fallback_lines']} lines "
                               "voiced with the basic fallback engine; do not publish, report to Maria")
    flagged = [{"who": ln["who"], "line": ln["text"], "emo": ln["voice"].get("emo"), "problems": ln["voice"]["problems"]}
               for ln in vlines if ln["voice"].get("problems")]
    rep["checks"]["voice_flagged"] = flagged
    hard = [f for f in flagged if any(k in p for p in f["problems"] for k in ("unclear", "high-pitched", "clipping", "like an adult"))]
    soft = [f for f in flagged if f not in hard]
    if hard:
        rep["blocking"].append(f"{len(hard)} line(s) still unclear / too high / distorted after retakes: "
                               + "; ".join(f"{f['who']}: '{f['line'][:40]}' {f['problems']}" for f in hard[:4]))
    if len(soft) > 2:
        rep["blocking"].append(f"{len(soft)} lines still sound monotone or rushed after retakes - rewrite/redirect them")
    elif soft:
        rep["warnings"].append("voice lines to re-check: " + "; ".join(f"{f['who']}: '{f['line'][:40]}' {f['problems']}" for f in soft))
    # subtitles present for every line
    srt = open(os.path.join(ep_dir, "subtitles.srt")).read() if os.path.exists(os.path.join(ep_dir, "subtitles.srt")) else ""
    rep["checks"]["subtitle_cues"] = srt.count("-->")
    if srt.count("-->") < len(tl["lines"]) * 0.8:
        rep["blocking"].append("subtitles missing for some lines")
    # render-time issues (subtitle safe area, off-screen speakers)
    for i in rl.get("issues", []):
        rep["blocking"].append(i)
    for w in rl.get("warnings", []):
        rep["warnings"].append(w)
    # cover
    from PIL import Image
    ci = Image.open(cover)
    if ci.size != (1080, 1920):
        rep["blocking"].append(f"cover is {ci.size}, expected 1080x1920")
    rep["checks"]["cover"] = f"{ci.size[0]}x{ci.size[1]}"
    rep["contact_sheets"] = contact_sheets(ep_dir)
    rep["pass"] = not rep["blocking"]
    json.dump(rep, open(os.path.join(ep_dir, "qc", "qc.json"), "w"), indent=1)
    return rep
