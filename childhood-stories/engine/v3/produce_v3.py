#!/usr/bin/env python3
"""Render + QC one Childhood Stories episode in the MIC Study v3 handmade doodle style.

usage: python3 engine/v3/produce_v3.py episodes/<folder>/episode.py [--preview] [--no-qc] [--resume] [--keep]

Same outputs as the old engine (so the rest of the Wednesday workflow is unchanged):
  master.mp4, upload.mp4 (<= 9.5 MB), cover.png, subtitles.srt, timeline.json, render_log.json, qc/...
It re-uses the engine's timeline (voices, pauses, sfx, transitions), sound mix, upload
compression and QC; only the drawing is v3.  Episode format: see engine/v3/VISUAL-V3.md.
"""
import argparse, base64, json, math, os, shutil, subprocess, sys, time
V3 = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(V3)
sys.path.insert(0, V3)
sys.path.insert(0, ENGINE)
import doodlefilm as D
import cast_v3 as CV
import sets_v3 as S
from doodlefilm import K, lerp, seed
from cs import film as F, audio as A

FPS, W, H = 30, 1080, 1920
EXPR = {  # smile, brow, default look
    "neutral": (.25, 0, None), "calm": (.3, -.1, None), "happy": (.6, -.3, None), "proud": (.7, -.2, None),
    "tender": (.4, -.1, None), "hopeful": (.35, .1, None), "curious": (.3, -.3, None), "focused": (.12, .2, (0, .9)),
    "unsure": (.1, .6, None), "worried": (.08, .9, None), "nervous": (.1, .8, None), "sad": (.05, .8, (0, .8)),
    "disappointed": (.04, .7, (0, .8)), "embarrassed": (.1, .5, (.2, .9)), "tired": (.1, .3, (0, .5)),
    "determined": (.2, -.4, None), "excited": (.75, -.4, None), "surprised": (.2, -.6, None), "relieved": (.5, 0, None),
    "frustrated": (.03, .5, (0, .6)), "thoughtful": (.2, .1, (.3, -.3)), "playful": (.6, -.3, None),
}
PAGE = D.PAGE.replace("</style>", """
#sub.narr{{top:auto;bottom:0;height:1920px;align-items:center}}
#sub.narr span{{font-family:'Architects Daughter',cursive;font-weight:400;font-size:62px;line-height:1.35;background:none;border:none;max-width:880px}}
#title{{position:absolute;left:0;right:0;top:1470px;text-align:center;font-family:'Architects Daughter',cursive;font-size:104px;
 color:#1f1b24;-webkit-text-stroke:2px #1f1b24;text-transform:uppercase;letter-spacing:2px;line-height:1.05;padding:0 60px;display:none}}
#logo{{position:absolute;width:118px;display:none}}
</style>""").replace('<div id="fade"></div>', '<div id="fade"></div><div id="title"></div><img id="logo"/>')


def logo_uri():
    return "data:image/png;base64," + base64.b64encode(open(os.path.join(ENGINE, "brand", "logo-light.png"), "rb").read()).decode()


# ------------------------------------------------------------------ states
def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _mix(a, b, k):
    if _num(a) and _num(b):
        return lerp(a, b, k)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b) and all(_num(x) for x in list(a) + list(b)):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return a if k < 1 else b


def key_state(keys, t, lines, dur):
    ks = sorted(((F._parse_t(k[0], lines, dur), k[1]) for k in keys), key=lambda x: x[0])
    st = {}
    for kt, d in ks:                      # carry forward everything up to t
        if kt <= t:
            st.update(d)
    nxt = [(kt, d) for kt, d in ks if kt > t]
    prev_t = max([kt for kt, _ in ks if kt <= t], default=None)
    if nxt and prev_t is not None:
        kt, d = nxt[0]
        span = kt - prev_t
        # moves take the last `ease` seconds before the next key (default: the whole gap, max 1.2 s)
        e = min(span, d.get("ease", 1.2))
        k = D.ease((t - (kt - e)) / e) if t > kt - e else 0.0
        for f, v in d.items():
            if f in st and f not in ("pose", "expr", "ease", "point"):
                st[f] = _mix(st[f], v, k)
        if d.get("pose") == "walk" or st.get("pose") == "walk":
            if k > 0 and _num(d.get("x")):
                st["pose"] = "walk" if k < 1 else d.get("pose", st.get("pose"))
    elif nxt and prev_t is None:
        st.update(nxt[0][1])
    return st


def actor_state(key, spec, shot, t, fi):
    a = shot["spec"]["actors"][key]
    lines = shot["lines"]
    st = key_state(a.get("keys", [[0, {k: v for k, v in a.items() if k != "keys"}]]), t, lines, shot["dur"])
    st.setdefault("floor", shot["_set"]["floor"])
    # expression: from keys, overridden by the speaker's line 'expr' from that line on
    ex = st.get("expr", "calm")
    for ln in lines:
        if ln["who"] == key and ln.get("expr") and ln["t0"] <= t:
            ex = ln["expr"]
    sm, br, lk = EXPR.get(ex, EXPR["calm"])
    st.setdefault("smile", sm)
    st.setdefault("brow", br)
    speaking = next((ln for ln in lines if ln["t0"] <= t <= ln["t1"]), None)
    if speaking and speaking["who"] == key:
        i = min(len(speaking["env"]) - 1, max(0, int((t - speaking["t0"]) * FPS)))
        st["talk"] = float(min(1.0, speaking["env"][i] * 1.1)) if speaking["env"][i] > 0.18 else 0.0
    if "look" not in st:
        if speaking and speaking["who"] != key and speaking["who"] in shot["spec"]["actors"]:
            ox = actor_x(speaking["who"], shot, t)
            st["look"] = (1.0 if ox > st["x"] else -1.0, 0.1)
        else:
            st["look"] = lk or (0.0, 0.2)
    period = 3.4 + (CV._h(key) % 13) / 10
    st["blink"] = ((t + CV._h(key) % 7 * 0.37) % period) < 0.13
    if st.get("pose") == "walk":
        st["phase"] = t * 6.5
    return st


def actor_x(key, shot, t):
    a = shot["spec"]["actors"][key]
    return key_state(a.get("keys", [[0, a]]), t, shot["lines"], shot["dur"]).get("x", 540)


# ------------------------------------------------------------------ frames
def cam_at(shot, t):
    keys = shot["spec"].get("cam", [[0, 540, 960, 1.0]])
    ks = sorted(((F._parse_t(k[0], shot["lines"], shot["dur"]), k[1:]) for k in keys), key=lambda x: x[0])
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, a), (t1, b) in zip(ks, ks[1:]):
        if t0 <= t <= t1:
            k = D.ease((t - t0) / max(1e-6, t1 - t0))
            return [lerp(x, y, k) for x, y in zip(a, b)]
    return ks[-1][1]


def endcard_set(t):
    s = K.paper(W, H, "#FFF8EC")
    for i, (x, y, r, c) in enumerate([(170, 330, 26, "#F06292"), (900, 420, 20, "#E91E63"), (820, 1600, 24, "#F48FB1"), (230, 1500, 18, "#EC407A")]):
        seed(500 + i)
        s += f'<g transform="translate(0 {math.sin(t * 1.3 + i) * 6:.1f})">' + K.heart(x, y, r, c) + "</g>"
    for i, (x, y) in enumerate([(640, 260), (330, 1720), (960, 1180)]):
        seed(520 + i)
        s += K.star(x, y, 16)
    s += K.vine(26, 640, 1300) + K.vine(1054, 560, 1140)
    return {"back": s, "mid": "", "fg": "", "floor": 1640}


def build_set(shot, t, ep):
    spec = shot["spec"]
    name = spec.get("set", "kitchen")
    if name == "__endcard":
        return endcard_set(t)
    fn = (ep.get("sets_v3") or {}).get(name) or S.SETS[name]
    return fn(t, **spec.get("set_kw", {}))


def frame_svg(shot, ep, cast, t, fi):
    st_set = shot["_set"] = build_set(shot, t, ep)
    cx, cy, s = cam_at(shot, t)
    bodies, arms = "", ""
    for key in shot["spec"].get("actors", {}):
        spec = cast[key.split("#")[0]]
        st = actor_state(key, spec, shot, t, fi)
        bodies += CV.draw_body(key, spec, st)
        arms += CV.draw_arms(key, spec, st)
    props = ""
    for p in shot["spec"].get("props", []):
        name, kw = (p[0], dict(p[1])) if isinstance(p, (list, tuple)) else (p, {})
        if "glow_from" in kw:
            g0 = F._parse_t(kw.pop("glow_from"), shot["lines"], shot["dur"])
            kw["glow"] = max(0.0, min(1.0, (t - g0) / 0.8))
        props += S.PROPS[name](**kw)
    fx = ""
    for f in shot["spec"].get("fx", []):
        if f[0] == "hearts":
            t0 = F._parse_t(f[1], shot["lines"], shot["dur"])
            if t > t0:
                fx += D.floating_hearts(t, t0)
    layers = (D.camera_group(st_set["back"], cx, cy, s, 0.9)
              + D.camera_group(bodies + st_set["mid"] + props + arms + fx, cx, cy, s, 1.0)
              + D.camera_group(st_set.get("fg", ""), cx, cy, s, 1.12))
    return D.svg_frame(layers, (fi // 4) % 3)


def sub_at(shot, t):
    for ln in shot["lines"]:
        if not ln.get("sub", True):
            continue
        a, b = ln["t0"], ln["t1"] + 0.25
        if a <= t <= b:
            chunks = F.split_sub(ln["text"], 30)
            k = min(len(chunks) - 1, int((t - a) / max(1e-6, (b - a) / len(chunks))))
            op = min(1, (t - a) / 0.12, (b - t) / 0.12)
            return chunks[k], op, ln["narr"]
    return "", 0, False


def render_shot(shot, ep, cast, out_path, page, qc, only=None):
    fdir = out_path + "_frames"
    os.makedirs(fdir, exist_ok=True)
    nf = int(round(shot["dur"] * FPS))
    frames = only if only is not None else range(nf)
    for fi in frames:
        t = fi / FPS
        svg = frame_svg(shot, ep, cast, t, fi)
        txt, op, narr = sub_at(shot, t)
        page.evaluate('([svg, txt, op, narr]) => {document.getElementById("art").innerHTML = svg;'
                      'const s=document.getElementById("sub"); s.className = narr ? "narr" : "";'
                      'document.getElementById("subt").textContent = txt; s.style.opacity = op;}', [svg, txt, op, narr])
        page.screenshot(path=os.path.join(fdir, f"f_{fi:04d}.jpg"), type="jpeg", quality=94)
    if only is not None:
        return fdir
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "f_%04d.jpg"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out_path], check=True)
    shutil.rmtree(fdir, ignore_errors=True)
    # render checks: every speaking character must be on screen unless marked off-screen
    for ln in shot["lines"]:
        if not ln["narr"] and ln["who"] not in shot["spec"].get("actors", {}) and not ln.get("off"):
            qc["warnings"].append(f"shot {shot['i']}: '{ln['who']}' speaks but is not in the shot (add \"off\": true if intended)")


def brand_card(ep, out_path, page, dur=4.8):
    """v3 brand card: handwritten on cream paper, official logo, rotating brand line."""
    line = ep.get("brand_line", "Practice for more than the page.")
    fdir = out_path + "_frames"
    os.makedirs(fdir, exist_ok=True)
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        s = K.paper(W, H, "#FFF8EC")
        for i, (x, y, r) in enumerate([(200, 420, 24), (880, 520, 18), (860, 1560, 22), (220, 1480, 16)]):
            seed(600 + i)
            s += f'<g transform="translate(0 {math.sin(t * 1.4 + i) * 6:.1f})">' + K.heart(x, y, r, "#F06292") + "</g>"
        a = lambda t0: max(0.0, min(1.0, (t - t0) / 0.6))
        s += (f'<image href="{logo_uri()}" x="325" y="560" width="430" opacity="{a(0.2):.2f}"/>'
              f'<text x="540" y="960" text-anchor="middle" font-family="Architects Daughter" font-size="66" fill="#1f1b24" opacity="{a(0.8):.2f}">Math + Reading</text>'
              f'<text x="540" y="1040" text-anchor="middle" font-family="Architects Daughter" font-size="46" fill="#6B6275" letter-spacing="6" opacity="{a(1.0):.2f}">GRADES 1-9</text>'
              f'<g opacity="{a(1.6):.2f}">' + K.underline(230, 1200, 620) +
              f'<text x="540" y="1180" text-anchor="middle" font-family="Architects Daughter" font-size="58" fill="#1f1b24">{line}</text></g>'
              f'<text x="540" y="1340" text-anchor="middle" font-family="Architects Daughter" font-size="46" fill="#D81B60" opacity="{a(2.2):.2f}">micstudy.com</text>')
        fade = max(0.0, (t - (dur - 0.6)) / 0.6)
        page.evaluate('([svg, f]) => {document.getElementById("art").innerHTML = svg; document.getElementById("sub").style.opacity = 0;'
                      'document.getElementById("fade").style.opacity = f;}', [D.svg_frame(s, (fi // 4) % 3), fade])
        page.screenshot(path=os.path.join(fdir, f"f_{fi:04d}.jpg"), type="jpeg", quality=94)
    page.evaluate('document.getElementById("fade").style.opacity = 0')
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fdir, "f_%04d.jpg"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out_path], check=True)
    shutil.rmtree(fdir, ignore_errors=True)


def cover(ep, shots, cast, out_png, page):
    """Hand-drawn miniature movie poster: key emotional frame, short handwritten title, small logo."""
    c = ep.get("cover", {})
    shot = shots[c.get("shot", max(0, len(shots) // 2))]
    t = F._parse_t(c.get("t", shot["dur"] / 2), shot["lines"], shot["dur"])
    svg = frame_svg(shot, ep, cast, t, 0)
    title = c.get("title", ep.get("title", ""))
    page.evaluate('([svg, title, logo]) => {document.getElementById("art").innerHTML = svg; document.getElementById("sub").style.opacity = 0;'
                  'const T=document.getElementById("title"); T.textContent = title; T.style.display = "block";'
                  'const L=document.getElementById("logo"); L.src = logo; L.style.display = "block"; L.style.right = "70px"; L.style.top = "290px";}',
                  [svg.replace("</svg>", '<path d="M0 1392 Q270 1374 540 1388 T1080 1380 L1080 1920 L0 1920Z" fill="#FFF8EC"/>'
                               + K.ink("M0 1392 Q270 1374 540 1388 T1080 1380", 4)
                               + K.underline(170, 1560, 740, h=26) + "</svg>"), title, logo_uri()])
    page.wait_for_timeout(120)
    page.screenshot(path=out_png, type="png")
    page.evaluate('document.getElementById("title").style.display = "none"; document.getElementById("logo").style.display = "none";')


# ------------------------------------------------------------------ pipeline
def prepare(ep_path):
    ep = F.load_episode(ep_path)
    cast = json.load(open(os.path.join(ENGINE, "cast.json")))
    cast.update(ep.get("extra_cast", {}))
    for k, v in ep.get("cast_overrides", {}).items():
        cast[k] = {**cast[k], **v}
    for sh in ep["shots"]:
        for key in sh.get("actors", {}):
            if key.split("#")[0] not in cast:
                raise KeyError(f"actor {key!r} is not in cast.json or extra_cast")
    ep = dict(ep)
    ep["shots"] = list(ep["shots"]) + ([F.end_card_shot(ep, cast)] if ep.get("end", {}).get("narration") else [])
    shots, total_story = F.build_timeline(ep, cast)
    for s in shots:
        s["_set"] = build_set(s, 0, ep)
    return ep, cast, shots, total_story


def new_page(browser):
    pg = browser.new_page(viewport={"width": W, "height": H})
    pg.set_content(PAGE.format(fonts=D.font_face_css()))
    pg.evaluate("document.fonts.ready")
    return pg


def _worker(ep_path, idxs, work):
    from playwright.sync_api import sync_playwright
    ep, cast, shots, _ = prepare(ep_path)
    qc = {"issues": [], "warnings": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = new_page(b)
        for i in idxs:
            t0 = time.time()
            render_shot(shots[i], ep, cast, os.path.join(work, f"shot_{i:02d}.mp4"), pg, qc)
            print(f"  shot {i:2d}  {shots[i]['dur']:5.2f}s  rendered in {time.time() - t0:5.1f}s", flush=True)
        b.close()
    return qc


def preview(ep_path, out_dir):
    """Stills (start/middle/end of each shot) + contact sheets + cover, and the timing."""
    from playwright.sync_api import sync_playwright
    from PIL import Image
    ep, cast, shots, total_story = prepare(ep_path)
    pdir = os.path.join(out_dir, "preview")
    shutil.rmtree(pdir, ignore_errors=True)
    os.makedirs(pdir)
    files = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = new_page(b)
        for s in shots:
            nf = int(round(s["dur"] * FPS))
            pts = sorted({2, nf // 2, max(0, nf - 3)})
            fdir = render_shot(s, ep, cast, os.path.join(pdir, f"s{s['i']:02d}"), pg, {"issues": [], "warnings": []}, only=pts)
            for fi in pts:
                files.append((s["i"], fi / FPS, os.path.join(fdir, f"f_{fi:04d}.jpg")))
        cover(ep, shots, cast, os.path.join(pdir, "cover.png"), pg)
        b.close()
    per = 9
    for k in range(0, len(files), per):
        grp = files[k:k + per]
        sheet = Image.new("RGB", (3 * 360, ((len(grp) + 2) // 3) * 660), "white")
        for j, (si, t, f) in enumerate(grp):
            im = Image.open(f).resize((360, 640))
            sheet.paste(im, ((j % 3) * 360, (j // 3) * 660))
        sheet.save(os.path.join(pdir, f"sheet_{k // per + 1:02d}.jpg"), quality=85)
    info = {"total_seconds": round(total_story + 4.8, 1), "shots": [[s["i"], round(s["dur"], 1)] for s in shots]}
    print(json.dumps(info))
    return info


def produce(ep_path, out_dir=None, resume=False, keep=False):
    from playwright.sync_api import sync_playwright
    from concurrent.futures import ProcessPoolExecutor
    t_start = time.time()
    out_dir = out_dir or os.path.dirname(os.path.abspath(ep_path))
    work = os.path.join(out_dir, "_work")
    os.makedirs(work, exist_ok=True)
    qcdir = os.path.join(out_dir, "qc")
    if not resume:
        shutil.rmtree(qcdir, ignore_errors=True)
    os.makedirs(qcdir, exist_ok=True)
    ep, cast, shots, total_story = prepare(ep_path)
    brand_dur = 4.8
    total = total_story + brand_dur
    qc = {"issues": [], "warnings": [], "stages": {"timeline": {"shots": len(shots), "duration": round(total, 2)}, "style": "v3"}}
    workers = max(1, min(int(os.environ.get("MICSTUDY_WORKERS", os.cpu_count() or 1)), 3))
    todo = [i for i in range(len(shots)) if not (resume and os.path.exists(os.path.join(work, f"shot_{i:02d}.mp4")))]
    buckets, loads = [[] for _ in range(workers)], [0.0] * workers
    for i in sorted(todo, key=lambda i: -shots[i]["dur"]):
        k = loads.index(min(loads))
        buckets[k].append(i)
        loads[k] += shots[i]["dur"]
    with ProcessPoolExecutor(workers) as ex:
        for r in [ex.submit(_worker, ep_path, bk, work) for bk in buckets if bk]:
            res = r.result()
            qc["issues"] += res["issues"]
            qc["warnings"] += res["warnings"]
    segs = [(os.path.join(work, f"shot_{s['i']:02d}.mp4"), s["T"], s["dur"], s["trans"] if s["i"] else "cut", s["tdur"]) for s in shots]
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = new_page(b)
        bc = os.path.join(work, "brand.mp4")
        brand_card(ep, bc, pg, brand_dur)
        segs.append((bc, total_story, brand_dur, "cut", 0))
        cover(ep, shots, cast, os.path.join(out_dir, "cover.png"), pg)
        b.close()
    video = os.path.join(work, "video.mp4")
    F.assemble(segs, video, total)
    # ---------------- audio (same as the main engine)
    dialogue, sfx_ev, amb, music_regions, srt = [], [], [], [], []
    for s in shots:
        sh = s["spec"]
        for ln in s["lines"]:
            pan = 0.0
            if not ln["narr"] and ln["who"] in sh.get("actors", {}):
                pan = max(-1, min(1, (actor_x(ln["who"], s, ln["t0"]) - 540) / 540))
            dialogue.append((s["T"] + ln["t0"], ln["clip"], pan, ln["narr"]))
            if ln["sub"]:
                srt.append((s["T"] + ln["t0"], s["T"] + ln["t1"] + 0.25, ln["text"]))
        for e in s["sfx"]:
            clip = A.sfx(e["name"], seed=s["i"] * 10 + len(sfx_ev), **e.get("kw", {}))
            sfx_ev.append((s["T"] + e["t"], clip, e["gain"], e["pan"]))
        amb.append((s["T"], s["T"] + s["dur"], sh.get("amb", "room")))
        music_regions.append([s["T"], s["T"] + s["dur"], sh.get("music", "reflective")])
    music_regions.append([total_story, total, "gentle"])
    merged = []
    for r in music_regions:
        if merged and merged[-1][2] == r[2]:
            merged[-1][1] = r[1]
        else:
            if merged:
                merged[-1][1] = r[0]
            merged.append(list(r))
    music = A.Score(ep.get("key", "D"), ep.get("bpm", 78), ep.get("seed", 7)).render([tuple(m) for m in merged], total)
    wav = os.path.join(work, "mix.wav")
    A.mix(total, dialogue, sfx_ev, amb, music, wav)
    with open(os.path.join(out_dir, "subtitles.srt"), "w") as f:
        for i, (a, b2, txt) in enumerate(srt, 1):
            f.write(f"{i}\n{F.srt_time(a)} --> {F.srt_time(b2)}\n{txt}\n\n")
    master = os.path.join(out_dir, "master.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", master], check=True)
    F.make_upload_copy(master, os.path.join(out_dir, "upload.mp4"), qc)
    json.dump({"style": "v3", "lines": [{"who": ln["who"], "text": ln["text"], "t0": s["T"] + ln["t0"], "t1": s["T"] + ln["t1"]}
                                        for s in shots for ln in s["lines"]], "total": total},
              open(os.path.join(out_dir, "timeline.json"), "w"), indent=1)
    qc["stages"]["render_seconds"] = round(time.time() - t_start)
    json.dump(qc, open(os.path.join(out_dir, "render_log.json"), "w"), indent=1)
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    print(f"done in {time.time() - t_start:.0f}s -> {master}")
    return master


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-qc", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    d = os.path.dirname(os.path.abspath(a.episode))
    if a.preview:
        preview(a.episode, d)
        sys.exit(0)
    produce(a.episode, d, resume=a.resume, keep=a.keep)
    if not a.no_qc:
        from cs import qc as Q
        rep = Q.run_qc(d)
        print(json.dumps({k: rep[k] for k in ("pass", "blocking", "warnings", "checks")}, indent=1))
        sys.exit(0 if rep["pass"] else 2)
