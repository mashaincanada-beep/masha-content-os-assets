"""MIC Study Childhood Stories - film renderer.

produce(episode_module_path) turns a screenplay (a Python file defining
EPISODE) into:  master.mp4, upload.mp4 (<= 9.5 MB for the Meta uploader),
cover.png, subtitles.srt, qc/ contact sheets and qc.json.

Screenplay format: see ../README.md ("Screenplay format").
"""
import base64, copy, glob, importlib.util, json, math, os, random, re, shutil, subprocess, sys, time
import numpy as np
import soundfile as sf

from . import character as C
from . import audio as A

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
PARALLAX = {"far": 0.55, "mid": 1.0, "near": 1.35}
SAFE = {"left": 70, "right": 1010, "top": 250, "bottom": 1660}   # Reels UI safe area for text

EXPR = {  # eye, brow, mouth, blush, positive?
    "neutral": ("open", "neutral", "smile_small", 0.4, True),
    "calm": ("open", "soft", "smile_small", 0.4, True),
    "happy": ("open", "raised", "smile", 0.5, True),
    "joy": ("happy", "raised", "grin", 0.6, True),
    "proud": ("happy", "soft", "smile", 0.65, True),
    "tender": ("open", "soft", "smile", 0.45, True),
    "hopeful": ("open", "raised", "smile_small", 0.45, True),
    "determined": ("open", "focused", "smile_small", 0.45, True),
    "shy": ("down", "soft", "smile_small", 0.75, True),
    "curious": ("open", "raised", "neutral", 0.4, True),
    "thinking": ("open", "thinking", "purse", 0.4, False),
    "focused": ("open", "focused", "flat", 0.4, False),
    "unsure": ("open", "worried", "neutral", 0.45, False),
    "worried": ("open", "worried", "wavy", 0.5, False),
    "sad": ("down", "sad", "frown", 0.45, False),
    "disappointed": ("down", "sad", "flat", 0.45, False),
    "embarrassed": ("down", "worried", "flat", 0.9, False),
    "frustrated": ("half", "angry", "flat", 0.55, False),
    "surprised": ("wide", "raised", "o", 0.5, True),
    "tired": ("half", "neutral", "flat", 0.35, False),
    "nervous": ("open", "worried", "bite", 0.6, False),
}
TWEEN_KEYS = ["x", "y", "s", "lean", "tilt", "turn", "opacity", "bob_amp"]


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def load_episode(path):
    sys.path.insert(0, ENGINE)
    spec = importlib.util.spec_from_file_location("episode", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EPISODE


def font_css():
    css = ""
    for f in sorted(glob.glob(os.path.join(ENGINE, "fonts", "*.woff2"))):
        name = os.path.basename(f)
        fam = "Fraunces" if name.startswith("fraunces") else "Nunito"
        weight = re.search(r"-(\d{3})-", name).group(1)
        style = "italic" if "italic" in name else "normal"
        b64 = base64.b64encode(open(f, "rb").read()).decode()
        css += f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:{style};src:url(data:font/woff2;base64,{b64}) format('woff2');}}\n"
    return css


def logo_uri(dark=False):
    p = os.path.join(ENGINE, "brand", "logo-dark.png" if dark else "logo-light.png")
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()


# ================================================================ timeline
def _parse_t(v, lines, dur=None):
    """Beat time: number, 'L2', 'L2.end', 'L2+0.4', 'end-1.0'."""
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"^\s*(L(\d+)(\.end)?|end|start)\s*([+-]\s*[\d.]+)?\s*$", str(v))
    if not m:
        raise ValueError(f"bad beat time {v!r}")
    base = m.group(1)
    off = float(m.group(4).replace(" ", "")) if m.group(4) else 0.0
    if base == "end":
        return (dur or 0) + off
    if base == "start":
        return off
    i = int(m.group(2))
    ln = lines[i]
    return (ln["t1"] if m.group(3) else ln["t0"]) + off


def build_timeline(ep, cast):
    shots = []
    for si, sh in enumerate(ep["shots"]):
        t = sh.get("start", 0.5)
        lines, sfx_ev = [], []
        for item in sh.get("script", []):
            if "pause" in item:
                t += item["pause"]
                continue
            if "sfx" in item:
                sfx_ev.append({"name": item["sfx"], "t": t + item.get("gap", 0), "gain": item.get("gain", 0.8),
                               "pan": item.get("pan", 0), "kw": item.get("kw", {})})
                t += item.get("advance", 0)
                continue
            who = item["who"]
            t += item.get("gap", 0.0)
            spec = cast[who.split("#")[0]]
            vid, spd, pit = C.voice_for(spec)
            spd = item.get("speed", spd)
            clip = A.synth(item.get("say", item["line"]), vid, spd, pit)
            d = len(clip) / A.SR
            lines.append({"who": who, "text": A.display_text(item["line"]), "t0": t, "t1": t + d, "clip": clip,
                          "expr": item.get("expr"), "to": item.get("to"), "narr": who == "narrator",
                          "sub": item.get("sub", True), "env": A.envelope(clip, FPS), "loud": item.get("loud", False)})
            t += d + item.get("after", 0.38)
        dur = max(sh.get("min", 2.5), t - 0.38 + sh.get("tail", 0.9)) if lines else max(sh.get("min", 3.0), t + sh.get("tail", 0.0))
        dur = sh.get("dur", dur)
        for e in sh.get("sfx", []):
            sfx_ev.append({"name": e["name"], "t": _parse_t(e.get("t", 0), lines, dur), "gain": e.get("gain", 0.8),
                           "pan": e.get("pan", 0), "kw": e.get("kw", {})})
        shots.append({"i": si, "spec": sh, "lines": lines, "sfx": sfx_ev, "dur": round(dur * FPS) / FPS})
    # global times
    T = 0.0
    for k, s in enumerate(shots):
        tr = s["spec"].get("trans", "cut" if k else "fade")
        td = s["spec"].get("tdur", 0.7 if tr == "dissolve" else 0.45)
        s["trans"], s["tdur"] = tr, td
        if k and tr == "dissolve":
            T -= td
        s["T"] = round(T * FPS) / FPS
        T += s["dur"]
    return shots, round(T * FPS) / FPS


# ================================================================ actor animation
class ActorTrack:
    def __init__(self, key, spec, g, sleeve, base, beats, lines, dur, seed):
        self.key, self.g, self.sleeve = key, g, sleeve
        b = {"x": 540, "y": 1700, "s": 1.0, "lean": 0, "tilt": 0, "turn": 0, "opacity": 1.0, "bob_amp": 1.0,
             "armL": "down", "armR": "down", "legs": "stand", "expr": "neutral", "look": (0, 0), "flip": False}
        b.update(base)
        if "expr" in base:
            b["expr"] = base["expr"]
        self.base = b
        self.beats = sorted(beats, key=lambda z: z["t"])
        self.lines = lines
        self.dur = dur
        rnd = random.Random(seed)
        self.blinks = []
        t = rnd.uniform(0.6, 2.0)
        while t < dur:
            self.blinks.append(t)
            t += rnd.uniform(2.2, 4.8)
        self.phase = rnd.random() * 6.28
        self.look_s = np.array(b["look"], dtype=float)
        self.turn_s = float(b["turn"])

    def _arm(self, v):
        return C.ARM_POSES[v] if isinstance(v, str) else tuple(v)

    def state_at(self, t, speaking_line, speaker_x):
        P = dict(self.base)
        armL, armR = self._arm(P["armL"]), self._arm(P["armR"])
        walk = None
        wave = None
        look_set = "look" in self.base and self.base["look"] != (0, 0)
        turn_set = "turn" in self.base and self.base.get("turn", 0) != 0
        for bt in self.beats:
            if bt["t"] > t:
                break
            st = bt["set"]
            k = ease((t - bt["t"]) / bt["dur"]) if bt["dur"] > 0 else 1.0
            for key in TWEEN_KEYS:
                if key in st:
                    P[key] = P[key] + (st[key] - P[key]) * k
            if "look" in st:
                lx, ly = P["look"]
                P["look"] = (lx + (st["look"][0] - lx) * k, ly + (st["look"][1] - ly) * k)
                look_set = st.get("look") is not None
            if "turn" in st:
                turn_set = True
            for nm in ("armL", "armR"):
                if nm in st:
                    tgt = self._arm(st[nm])
                    cur = armL if nm == "armL" else armR
                    new = (cur[0] + (tgt[0] - cur[0]) * k, cur[1] + (tgt[1] - cur[1]) * k)
                    if nm == "armL":
                        armL = new
                    else:
                        armR = new
            for key in ("expr", "legs", "flip", "eye", "mouth", "brow"):
                if key in st:
                    P[key] = st[key]
            if "walk_to" in st:
                x0 = P["x"]
                if t < bt["t"] + bt["dur"]:
                    walk = (t - bt["t"]) * 9.0
                P["x"] = x0 + (st["walk_to"] - x0) * min(1, (t - bt["t"]) / bt["dur"])
            if st.get("wave") and t < bt["t"] + bt["dur"]:
                wave = t - bt["t"]
            if st.get("auto_look") is not None:
                P["auto_look"] = st["auto_look"]
        # expression
        ex = EXPR.get(P["expr"], EXPR["neutral"])
        eye, brow, mouth, blush, positive = ex
        eye = P.get("eye", eye)
        brow = P.get("brow", brow)
        mouth = P.get("mouth", mouth)
        # speaking
        speaking = speaking_line is not None and speaking_line["who"] == self.key
        if speaking:
            ln = speaking_line
            if ln.get("expr"):
                ex = EXPR.get(ln["expr"], ex)
                eye, brow, mouth, blush, positive = ex
            fi = int((t - ln["t0"]) * FPS)
            e = ln["env"][fi] if 0 <= fi < len(ln["env"]) else 0
            if e > (0.55 if not ln.get("loud") else 0.45):
                mouth = "smile_open_b" if positive else "open_b"
            elif e > 0.14:
                mouth = "smile_open_s" if positive else "open_s"
            P["tilt"] += math.sin(t * 7.3 + self.phase) * 1.4 * min(1, e)
        # auto look toward whoever is speaking
        auto = P.get("auto_look", True)
        tgt_look = np.array(P["look"], dtype=float)
        tgt_turn = P["turn"]
        if auto and not look_set:
            if speaking and speaker_x is not None:
                d = np.sign(speaker_x - P["x"])
                tgt_look = np.array([d * 0.6, 0.0]); tgt_turn = d * 0.3
            elif speaker_x is not None and speaking_line and not speaking_line["narr"]:
                d = np.sign(speaker_x - P["x"]) if abs(speaker_x - P["x"]) > 5 else 0
                tgt_look = np.array([d * 0.85, 0.0])
                if not turn_set:
                    tgt_turn = d * 0.35
        self.look_s += (tgt_look - self.look_s) * 0.18
        self.turn_s += (tgt_turn - self.turn_s) * 0.12
        # blink
        if eye in ("open", "wide", "down"):
            for b0 in self.blinks:
                if 0 <= t - b0 < 0.12:
                    eye = "closed" if eye != "down" else "closed"
                    break
        bob = math.sin(t * 2 * math.pi / 3.4 + self.phase) * 2.2 * P["bob_amp"]
        if walk is not None:
            bob += abs(math.sin(walk)) * -6
        if wave is not None:
            armR = (armR[0] + math.sin(wave * 9) * 14, armR[1] + math.sin(wave * 9) * 18)
        Pf = {"x": P["x"], "y": P["y"], "s": P["s"], "lean": P["lean"], "bob": bob, "tilt": P["tilt"],
              "turn": self.turn_s, "look": tuple(self.look_s), "eye": eye, "brow": brow, "mouth": mouth,
              "blush": blush, "armL": armL, "armR": armR, "legs": P["legs"], "walk": walk,
              "flip": P.get("flip", False), "opacity": P["opacity"]}
        return Pf


# ================================================================ page
PAGE_JS = r"""
function camSet(id, tf){ document.getElementById(id).setAttribute('transform', tf); }
function propSet(id, tf, op){ const e=document.getElementById(id); e.setAttribute('transform', tf); e.setAttribute('opacity', op); }
function subSet(txt, narr, op, top){
  const s=document.getElementById('sub'); const t=document.getElementById('subt');
  if (top !== undefined && s.__top !== top){ s.style.top = top + 'px'; s.__top = top; }
  if (t.__txt !== txt){ t.textContent = txt; t.__txt = txt; }
  s.style.opacity = op; s.className = narr ? 'narr' : '';
}
function capSet(txt, op){ const c=document.getElementById('cap'); if (c.__t!==txt){c.textContent=txt;c.__t=txt;} c.style.opacity=op; }
function titleSet(op){ document.getElementById('title').style.opacity = op; }
function blackSet(op){ document.getElementById('black').style.opacity = op; }
function dust(t){
  const ps = document.querySelectorAll('.dust');
  ps.forEach((p,i)=>{ const sx=(i*137.5)%1080, sy=(i*271.3)%1920;
    const x=(sx + Math.sin(t*0.3+i)*40 + t*6)%1080, y=(sy - t*(8+i%5*2) + 1920*4)%1920;
    p.setAttribute('cx', x.toFixed(1)); p.setAttribute('cy', y.toFixed(1)); });
}
function steam(t){ document.querySelectorAll('.steam').forEach((p,i)=>{ p.setAttribute('opacity', (0.25+0.25*Math.sin(t*2+i)).toFixed(2));
  p.setAttribute('transform', `translate(${(Math.sin(t*1.5+i)*6).toFixed(1)},${(-((t*18+i*20)%40)).toFixed(1)})`); }); }
function subBox(){ const s=document.getElementById('sub'); if(!s.textContent.trim()||s.style.opacity==='0') return null;
  const r=s.getBoundingClientRect(); const t=document.getElementById('subt'); return [r.left,r.top,r.right,r.bottom,t.scrollWidth>t.clientWidth+2]; }
"""

FF_GRADES = {
    None: "", "none": "",
    "warm": "colorbalance=rs=.05:gs=.01:bs=-.05:rm=.04:gm=.0:bm=-.04",
    "golden": "colorbalance=rs=.08:gs=.03:bs=-.08:rm=.06:gm=.02:bm=-.06,eq=saturation=1.06",
    "cool": "colorbalance=rs=-.04:bs=.05:rm=-.03:bm=.04",
    "night": "eq=brightness=-.07:saturation=.82,colorbalance=bs=.08:bm=.06",
    "soft": "eq=contrast=.97:brightness=.012",
    "dim": "eq=brightness=-.05:saturation=.92",
}


def ff_filter(sh):
    f = [FF_GRADES.get(sh.get("grade", "soft"), "")]
    fx = sh.get("fx", ["vignette"])
    if "vignette_strong" in fx:
        f.append("vignette=angle=PI/4.2")
    elif "vignette" in fx:
        f.append("vignette=angle=PI/5.5")
    f = [x for x in f if x]
    return ",".join(f) if f else "null"


GRADES = {
    None: "", "none": "",
    "warm": "background:#FFB35C;mix-blend-mode:soft-light;opacity:.28",
    "golden": "background:#FF9A3C;mix-blend-mode:soft-light;opacity:.38",
    "cool": "background:#5C8DFF;mix-blend-mode:soft-light;opacity:.22",
    "night": "background:#2A2F6B;mix-blend-mode:multiply;opacity:.42",
    "soft": "background:#FFFFFF;mix-blend-mode:soft-light;opacity:.18",
    "dim": "background:#1E1A2E;mix-blend-mode:multiply;opacity:.22",
}


def page_html(shot, sets, rigs, ep, fonts_css, prop_defs):
    sh = shot["spec"]
    st = sets[sh["set"]]
    act_order = sorted(sh.get("actors", {}).items(), key=lambda kv: kv[1].get("y", 1700))
    actors_svg = ""
    props_front = {p["id"]: p for p in prop_defs if p.get("layer", "front") == "front"}
    attached_after = {}
    for p in props_front.values():
        if p.get("attach"):
            attached_after.setdefault(p["attach"][0], []).append(p)
    placed = set()
    for key, _ in act_order:
        actors_svg += rigs[key][0]
        for p in attached_after.get(key, []):
            actors_svg += f'<g id="p_{p["id"]}">{p["svg"]}</g>'
            placed.add(p["id"])
    actors_svg += st.get("front", "")
    for p in props_front.values():
        if p["id"] not in placed:
            actors_svg += f'<g id="p_{p["id"]}">{p["svg"]}</g>'
    back_props = "".join(f'<g id="p_{p["id"]}">{p["svg"]}</g>' for p in prop_defs if p.get("layer") == "back")
    near_props = "".join(f'<g id="p_{p["id"]}">{p["svg"]}</g>' for p in prop_defs if p.get("layer") == "near")
    fx = sh.get("fx", ["vignette"])
    dust = ""
    if "dust" in fx:
        dust = "".join(f'<circle class="dust" r="{1.5 + (i % 3)}" fill="#FFF6D6" opacity="{0.25 + 0.1 * (i % 4)}"/>' for i in range(40))
    grade = GRADES.get(sh.get("grade", "soft"), "")
    vign = "vignette" in fx or "vignette_strong" in fx
    vop = 0.55 if "vignette_strong" in fx else 0.32
    title = ep["title"].upper()
    endcss = ""
    if sh.get("endcard"):
        endcss = ("#sub{top:780px !important}#sub.narr #subt{background:none !important;color:#2B2230 !important;"
                  "font-size:62px !important;line-height:1.3 !important;max-width:880px !important}")
    return f"""<html><head><style>{fonts_css}{endcss}
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;overflow:hidden;background:#000}}
#stage{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}
.ov{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;pointer-events:none}}
#sub{{position:absolute;left:{SAFE['left'] + 40}px;right:{W - SAFE['right'] + 40}px;top:1330px;text-align:center;transition:none}}
#subt{{display:inline-block;max-width:820px;font-family:Nunito;font-weight:800;font-size:46px;line-height:1.28;color:#fff;
  background:rgba(30,24,40,.52);padding:14px 28px;border-radius:26px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
#sub.narr #subt{{font-family:Fraunces;font-style:italic;font-weight:600;background:rgba(30,24,40,.38)}}
#cap{{position:absolute;left:0;right:0;top:330px;text-align:center;font-family:Fraunces;font-style:italic;font-weight:600;font-size:52px;color:#fff;
  text-shadow:0 3px 18px rgba(0,0,0,.45);opacity:0}}
#title{{position:absolute;left:0;right:0;top:170px;padding:90px 0 110px;text-align:center;opacity:0;
  background:radial-gradient(ellipse 70% 60% at 50% 50%, rgba(25,15,35,.55), rgba(25,15,35,0))}}
#title .t{{font-family:Fraunces;font-weight:900;font-size:84px;letter-spacing:4px;color:#fff;text-shadow:0 4px 30px rgba(0,0,0,.5);line-height:1.05;padding:0 90px}}
#title .s{{font-family:Nunito;font-weight:800;font-size:30px;letter-spacing:8px;color:#fff;opacity:.9;margin-top:18px;text-shadow:0 2px 12px rgba(0,0,0,.5)}}
</style></head><body>
<svg id="stage" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<g id="L_far">{st.get('far', '')}</g>
<g id="L_mid">{st.get('mid', '')}{back_props}</g>
<g id="L_act">{actors_svg}</g>
<g id="L_near">{st.get('near', '')}{near_props}</g>
<g id="dustg">{dust}</g>
</svg>
<div id="title"><div class="t">{title}</div><div class="s">MIC STUDY &nbsp;·&nbsp; CHILDHOOD STORIES</div></div>
<div id="cap"></div>
<div id="sub"><span id="subt"></span></div>
<div class="ov" id="black" style="background:#000;opacity:0"></div>
<script>{C.APPLY_JS}{PAGE_JS}</script></body></html>"""


def cam_at(keys, t, dur):
    ks = []
    for k in keys:
        tt = dur if k[0] == "end" else float(k[0])
        ks.append((tt, k[1], k[2], k[3]))
    ks.sort()
    if t <= ks[0][0]:
        return ks[0][1:]
    for a, b in zip(ks, ks[1:]):
        if a[0] <= t <= b[0]:
            u = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
            return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
    return ks[-1][1:]


def layer_tf(cx, cy, z, pf, t, drift=True):
    zz = 1 + (z - 1) * pf
    dx = dy = 0.0
    if drift:
        dx, dy = math.sin(t * 0.37) * 2.5, math.cos(t * 0.29) * 2.0
    px = 540 + (cx - 540) * pf + dx
    py = 960 + (cy - 960) * pf + dy
    return f"translate(540,960) scale({zz:.5f}) translate({-px:.2f},{-py:.2f})"


def world_to_screen(x, y, cam):
    cx, cy, z = cam
    return 540 + (x - cx) * z, 960 + (y - cy) * z


def face_boxes(tracks, states, cam):
    boxes = []
    for key, tr in tracks.items():
        P = states.get(key)
        if not P or P.get("opacity", 1) < 0.2:
            continue
        g = tr.g
        drop = g["legL"] * 0.5 * P["s"] if P.get("legs") == "sit" else 0
        hx, hy = world_to_screen(P["x"], P["y"] + drop + (g["headCY"]) * P["s"], cam)
        r = g["headR"] * P["s"] * cam[2] * 1.35
        boxes.append((hx - r, hy - r * 1.1, hx + r, hy + r * 1.1))
    return boxes


def choose_sub_band(txt, tracks, states, cam, endcard=False):
    if endcard:
        return 780
    lines = max(1, math.ceil(len(txt) / 30))
    h = lines * 59 + 30
    best, best_ov = 1330, 1e9
    for top in (1330, 1470, 1200, 260):
        ov = 0
        for (x0, y0, x1, y1) in face_boxes(tracks, states, cam):
            ix = max(0, min(x1, 950) - max(x0, 130))
            iy = max(0, min(y1, top + h) - max(y0, top))
            ov += ix * iy
        if ov == 0:
            return top
        if ov < best_ov:
            best, best_ov = top, ov
    return best


def split_sub(text, maxc=30):
    words = text.split()
    chunks, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > maxc * 2 and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += " " + w
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


# ================================================================ shot render
def render_shot(shot, ep, sets, cast, out_path, browser, fonts_css, qc, frame_dump=None, only_frames=None):
    sh = shot["spec"]
    dur = shot["dur"]
    nf = int(round(dur * FPS))
    rigs = {}
    tracks = {}
    for idx, (key, base) in enumerate(sh.get("actors", {}).items()):
        spec = cast[key.split("#")[0]]
        svg, g, sleeve = C.build_svg(key.replace("#", "_"), spec)
        rigs[key] = (svg, g, sleeve)
    lines = shot["lines"]
    beats_by = {}
    for b in sh.get("beats", []):
        t = _parse_t(b.get("t", 0), lines, dur)
        beats_by.setdefault(b["who"], []).append({"t": t, "dur": b.get("dur", 0.4), "set": b.get("set", {})})
    for idx, (key, base) in enumerate(sh.get("actors", {}).items()):
        svg, g, sleeve = rigs[key]
        tracks[key] = ActorTrack(key.replace("#", "_"), cast[key.split("#")[0]], g, sleeve, base, beats_by.get(key, []), lines, dur, seed=shot["i"] * 31 + idx)
    # props
    prop_defs = []
    for p in sh.get("props", []):
        prop_defs.append(dict(p))
    html = page_html(shot, sets, rigs, ep, fonts_css, prop_defs)
    page = browser.new_page(viewport={"width": W, "height": H})
    page.set_content(html)
    page.wait_for_timeout(150)
    enc = None
    if only_frames is None:
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                                "-vf", ff_filter(sh), "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out_path],
                               stdin=subprocess.PIPE)
    subs = []
    for ln in lines:
        if not ln["sub"]:
            continue
        chunks = split_sub(ln["text"])
        total = sum(len(c) for c in chunks)
        t = ln["t0"]
        for c in chunks:
            d = (ln["t1"] - ln["t0"]) * len(c) / total
            subs.append((t, t + d + (0.25 if c == chunks[-1] else 0), c, ln["narr"]))
            t += d
    prop_beats = {}
    for b in sh.get("beats", []):
        if any(p["id"] == b["who"] for p in prop_defs):
            prop_beats.setdefault(b["who"], []).append({"t": _parse_t(b.get("t", 0), lines, dur), "dur": b.get("dur", 0.4), "set": b.get("set", {})})
    cap = sh.get("caption")
    last_sub = None
    sub_top = {}
    for fi in range(nf):
        t = fi / FPS
        cam = cam_at(sh.get("cam", [[0, 540, 960, 1.0]]), t, dur)
        drift = sh.get("drift", True)
        js = []
        for L, pf in PARALLAX.items():
            js.append(f"camSet('L_{L}', '{layer_tf(cam[0], cam[1], cam[2], pf, t, drift)}');")
        js.append(f"camSet('L_act', '{layer_tf(cam[0], cam[1], cam[2], 1.0, t, drift)}');")
        # who is speaking
        speaking = None
        for ln in lines:
            if ln["t0"] <= t <= ln["t1"]:
                speaking = ln
        speaker_x = None
        if speaking and speaking["who"] in tracks:
            speaker_x = tracks[speaking["who"]].base["x"]
        states = {}
        for key, tr in tracks.items():
            P = tr.state_at(t, speaking if (speaking and speaking["who"] == key) else (speaking if speaking else None), speaker_x)
            states[key] = P
            stt = C.frame_state(tr.key, tr.g, tr.sleeve, P)
            js.append(f"applyActor({json.dumps(stt)});")
        # props
        for p in prop_defs:
            x, y, s, rot, op = p.get("x", 540), p.get("y", 1500), p.get("s", 1.0), p.get("rot", 0), 1.0
            att = p.get("attach")
            show = p.get("show")
            for b in prop_beats.get(p["id"], []):
                if b["t"] > t:
                    break
                k = ease((t - b["t"]) / b["dur"]) if b["dur"] > 0 else 1
                for kk, cur in (("x", x), ("y", y), ("s", s), ("rot", rot)):
                    if kk in b["set"]:
                        val = cur + (b["set"][kk] - cur) * k
                        if kk == "x": x = val
                        elif kk == "y": y = val
                        elif kk == "s": s = val
                        else: rot = val
                if "op" in b["set"]:
                    op = op + (b["set"]["op"] - op) * k
                if "attach" in b["set"]:
                    att = b["set"]["attach"]
            if att:
                who, hand = att[0], att[1]
                dx, dy = (att[2], att[3]) if len(att) > 3 else (0, 0)
                if who in states:
                    hx, hy = C.hand_world(tracks[who].g, states[who], hand)
                    x, y = hx + dx * states[who]["s"], hy + dy * states[who]["s"]
                    s = s * states[who]["s"]
                    op *= states[who]["opacity"]
            if show and not (show[0] <= t <= show[1]):
                op = 0
            js.append(f"propSet('p_{p['id']}', 'translate({x:.1f},{y:.1f}) rotate({rot:.2f}) scale({s:.4f},{s * p.get('squash', 1):.4f})', {op:.3f});")
        # subtitles (placed in the band that covers no face)
        cur = None
        for ci, (s0, s1, txt, narr) in enumerate(subs):
            if s0 <= t <= s1:
                cur = (txt, narr, min(1, (t - s0) / 0.12, (s1 - t) / 0.12), ci)
        if cur:
            ci = cur[3]
            if ci not in sub_top:
                sub_top[ci] = choose_sub_band(cur[0], tracks, states, cam, bool(sh.get("endcard")))
            js.append(f"subSet({json.dumps(cur[0])}, {str(cur[1]).lower()}, {cur[2]:.2f}, {sub_top[ci]});")
        else:
            js.append("subSet('', false, 0);")
        if cap:
            c0, c1 = sh.get("caption_t", [0.3, min(dur - 0.3, 3.0)])
            op = max(0, min(1, (t - c0) / 0.5, (c1 - t) / 0.5)) if c0 <= t <= c1 else 0
            js.append(f"capSet({json.dumps(cap)}, {op:.2f});")
        if sh.get("title"):
            t0, t1 = sh.get("title_t", [0.6, 4.2])
            op = max(0, min(1, (t - t0) / 0.8, (t1 - t) / 0.8)) if t0 <= t <= t1 else 0
            js.append(f"titleSet({op:.2f});")
        # fades to/from black
        bop = 0.0
        if shot["trans"] == "fade" and t < shot["tdur"]:
            bop = 1 - t / shot["tdur"]
        if sh.get("fade_out") and t > dur - sh.get("fade_out"):
            bop = max(bop, (t - (dur - sh["fade_out"])) / sh["fade_out"])
        js.append(f"blackSet({bop:.3f}); dust({t:.3f}); steam({t:.3f});")
        page.evaluate("\n".join(js))
        if only_frames is not None:
            if fi in only_frames:
                page.screenshot(path=only_frames[fi], type="png")
            continue
        png = page.screenshot(type="jpeg", quality=95)
        enc.stdin.write(png)
        # QC: subtitle box and speaker on screen
        if cur and cur[0] != last_sub:
            box = page.evaluate("subBox()")
            if box:
                l, tp, r, b, overflow = box
                if l < SAFE["left"] or r > SAFE["right"] or b > SAFE["bottom"] or overflow:
                    qc["issues"].append(f"shot {shot['i']}: subtitle outside safe area or clipped: {cur[0]!r} box={[round(v) for v in box[:4]]}")
            last_sub = cur[0]
        if speaking and speaking["who"] in tracks and abs(t - (speaking["t0"] + 0.2)) < 0.5 / FPS:
            P = states[speaking["who"]]
            g = tracks[speaking["who"]].g
            hx, hy = world_to_screen(P["x"], P["y"] + g["headCY"] * P["s"], cam)
            if not (70 <= hx <= W - 70 and 120 <= hy <= H - 300):
                qc["warnings"].append(f"shot {shot['i']}: {speaking['who']} speaks while off-screen (head at {hx:.0f},{hy:.0f})")
        if frame_dump is not None and fi in frame_dump:
            with open(frame_dump[fi], "wb") as fh:
                fh.write(png)
    if enc:
        enc.stdin.close()
        enc.wait()
    page.close()


# ================================================================ end card
def end_card_shot(ep, cast):
    end = ep.get("end", {})
    shot = {
        "set": end.get("set", "__endcard"),
        "cam": end.get("cam", [[0, 540, 960, 1.0], ["end", 540, 940, 1.04]]),
        "actors": end.get("actors", {}),
        "props": end.get("props", []),
        "beats": end.get("beats", []),
        "script": [{"who": "narrator", "line": l, "after": 0.7} for l in end.get("narration", [])],
        "start": end.get("start", 0.6), "tail": 0.6, "music": end.get("music", "gentle"), "amb": None,
        "trans": end.get("trans", "dissolve"), "tdur": 0.9, "grade": end.get("grade", "soft"),
        "fx": [], "endcard": True,
    }
    return shot


def endcard_bg():
    return ('<defs><linearGradient id="ecg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF7EC"/>'
            '<stop offset="1" stop-color="#FFE9D6"/></linearGradient></defs>'
            '<rect x="-300" y="-300" width="1700" height="2600" fill="url(#ecg)"/>'
            '<circle cx="120" cy="300" r="220" fill="#1C8FFF" opacity=".06"/><circle cx="980" cy="1650" r="260" fill="#FE007A" opacity=".05"/>'
            '<circle cx="900" cy="420" r="120" fill="#5FE223" opacity=".06"/>')


def brand_card_html(ep, fonts_css):
    line = ep.get("brand_line", "Practice for more than the page.")
    return f"""<html><head><style>{fonts_css}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:linear-gradient(#FFF8EE,#FFEBDA)}}
.c{{position:absolute;left:0;right:0;text-align:center}}
#logo{{top:560px}} #logo img{{width:430px}}
#mr{{top:930px;font-family:Nunito;font-weight:900;font-size:58px;color:#2B2230;letter-spacing:1px}}
#gr{{top:1010px;font-family:Nunito;font-weight:800;font-size:40px;color:#6B6275;letter-spacing:6px}}
#bl{{top:1150px;font-family:Fraunces;font-style:italic;font-weight:600;font-size:54px;color:#2B2230;padding:0 110px}}
#url{{top:1330px;font-family:Nunito;font-weight:800;font-size:40px;color:#1C8FFF;letter-spacing:2px}}
.dot{{position:absolute;border-radius:50%}}
</style></head><body>
<div class="dot" style="left:-120px;top:180px;width:420px;height:420px;background:#1C8FFF;opacity:.06"></div>
<div class="dot" style="right:-160px;bottom:160px;width:520px;height:520px;background:#FE007A;opacity:.05"></div>
<div class="c" id="logo"><img src="{logo_uri(False)}"/></div>
<div class="c" id="mr">Math + Reading</div>
<div class="c" id="gr">GRADES 1-9</div>
<div class="c" id="bl">{line}</div>
<div class="c" id="url">micstudy.com</div>
<div id="black" style="position:absolute;inset:0;background:#000;opacity:0"></div>
<script>function f(o,ids){{for(const [id,v] of Object.entries(ids)){{document.getElementById(id).style.opacity=v;}} document.getElementById('black').style.opacity=o;}}</script>
</body></html>"""


def render_brand_card(ep, out_path, browser, fonts_css, dur=4.8, frame_dump=None):
    page = browser.new_page(viewport={"width": W, "height": H})
    page.set_content(brand_card_html(ep, fonts_css))
    page.wait_for_timeout(150)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    nf = int(dur * FPS)
    for fi in range(nf):
        t = fi / FPS
        a = lambda t0: max(0, min(1, (t - t0) / 0.6))
        ids = {"logo": a(0.2), "mr": a(0.8), "gr": a(1.0), "bl": a(1.6), "url": a(2.2)}
        bo = max(0, (t - (dur - 0.6)) / 0.6)
        page.evaluate(f"f({bo:.3f}, {json.dumps(ids)})")
        png = page.screenshot(type="png")
        enc.stdin.write(png)
        if frame_dump is not None and fi in frame_dump:
            open(frame_dump[fi], "wb").write(png)
    enc.stdin.close()
    enc.wait()
    page.close()


# ================================================================ cover
def render_cover(ep, sets, cast, out_path, browser, fonts_css):
    cv = ep.get("cover", {})
    si = cv.get("shot", 0)
    sh = copy.deepcopy(ep["shots"][si])
    sh.update(cv.get("override", {}))
    sh["script"] = []
    sh["title"] = False
    sh["caption"] = None
    shot = {"i": 900, "spec": sh, "lines": [], "sfx": [], "dur": 1 / FPS, "trans": "cut", "tdur": 0}
    rigs = {}
    for key in sh.get("actors", {}):
        rigs[key] = C.build_svg(key.replace("#", "_"), cast[key.split("#")[0]])
    html = page_html(shot, sets, rigs, ep, fonts_css, sh.get("props", []))
    page = browser.new_page(viewport={"width": W, "height": H})
    page.set_content(html)
    page.wait_for_timeout(150)
    cam = cv.get("cam", sh.get("cam", [[0, 540, 960, 1.0]])[0][1:])
    js = [f"camSet('L_{L}', '{layer_tf(cam[0], cam[1], cam[2], pf, 0, False)}');" for L, pf in PARALLAX.items()]
    js.append(f"camSet('L_act', '{layer_tf(cam[0], cam[1], cam[2], 1.0, 0, False)}');")
    lines = []
    for key, base in sh.get("actors", {}).items():
        svg, g, sleeve = rigs[key]
        tr = ActorTrack(key.replace("#", "_"), cast[key.split("#")[0]], g, sleeve, base, [], lines, 1, 1)
        P = tr.state_at(5.0, None, None)
        js.append(f"applyActor({json.dumps(C.frame_state(tr.key, g, sleeve, P))});")
    for p in sh.get("props", []):
        x, y, s, rot = p.get("x", 540), p.get("y", 1500), p.get("s", 1), p.get("rot", 0)
        if p.get("attach"):
            who, hand = p["attach"][0], p["attach"][1]
            dx, dy = (p["attach"][2], p["attach"][3]) if len(p["attach"]) > 3 else (0, 0)
            base = sh["actors"][who]
            tr = ActorTrack(who, cast[who.split('#')[0]], rigs[who][1], rigs[who][2], base, [], [], 1, 1)
            P = tr.state_at(5.0, None, None)
            hx, hy = C.hand_world(rigs[who][1], P, hand)
            x, y, s = hx + dx * P["s"], hy + dy * P["s"], s * P["s"]
        js.append(f"propSet('p_{p['id']}', 'translate({x:.1f},{y:.1f}) rotate({rot}) scale({s},{s * p.get('squash', 1)})', 1);")
    title = ep["title"].upper()
    js.append(f"""
      document.getElementById('sub').style.display='none';
      const d=document.createElement('div'); d.style.cssText='position:absolute;inset:0;background:linear-gradient(rgba(20,12,30,{.72 if int(cv.get("title_y", 1360)) < 900 else .55}) 0%,rgba(20,12,30,0) 34%,rgba(20,12,30,0) 62%,rgba(20,12,30,{.4 if int(cv.get("title_y", 1360)) < 900 else .72}) 100%)';
      document.body.appendChild(d);
      const t=document.createElement('div'); t.style.cssText='position:absolute;left:70px;right:70px;top:{int(cv.get("title_y", 1360))}px;text-align:center;font-family:Fraunces;font-weight:900;font-size:{int(cv.get("title_size", 104))}px;line-height:1.02;color:#fff;letter-spacing:3px;text-shadow:0 6px 34px rgba(0,0,0,.55)';
      t.textContent={json.dumps(title)}; document.body.appendChild(t);
      const s=document.createElement('div'); s.style.cssText='position:absolute;left:0;right:0;top:{(int(cv.get("title_y", 1360)) - 70) if int(cv.get("title_y", 1360)) < 900 else 300}px;text-align:center;font-family:Nunito;font-weight:800;font-size:30px;letter-spacing:9px;color:#fff;opacity:.92;text-shadow:0 2px 14px rgba(0,0,0,.5)';
      s.textContent="A MIC STUDY CHILDHOOD STORY"; document.body.appendChild(s);
      const l=document.createElement('img'); l.src='{logo_uri(True)}'; l.style.cssText='position:absolute;right:70px;top:1700px;width:170px';
      document.body.appendChild(l);""")
    page.evaluate("\n".join(js))
    page.wait_for_timeout(200)
    # make sure the title fits: shrink if it overflows
    page.evaluate("""(()=>{const ts=[...document.body.children].filter(e=>e.textContent && e.style.fontFamily==='Fraunces');
       for(const t of ts){ let fs=parseInt(t.style.fontSize); while(t.getBoundingClientRect().height>260 && fs>60){fs-=4;t.style.fontSize=fs+'px';} }})()""")
    page.screenshot(path=out_path, type="png")
    page.close()


# ================================================================ assembly
def assemble(segments, out_path, total):
    """segments: [(path, T, dur, trans, tdur)] -> single video (no audio)."""
    inputs = []
    for p, *_ in segments:
        inputs += ["-i", p]
    fc = [f"[{k}:v]setpts=PTS-STARTPTS,fps={FPS},format=yuv420p,settb=AVTB[i{k}]" for k in range(len(segments))]
    cur = "[i0]"
    acc = segments[0][2]
    for k in range(1, len(segments)):
        p, T, d, tr, td = segments[k]
        out = f"[v{k}]"
        if tr == "dissolve":
            off = acc - td
            fc.append(f"{cur}[i{k}]xfade=transition=fade:duration={td:.3f}:offset={off:.3f},settb=AVTB{out}")
            acc = acc - td + d
        else:
            fc.append(f"{cur}[i{k}]concat=n=2:v=1:a=0,settb=AVTB{out}")
            acc = acc + d
        cur = out
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(fc), "-map", cur,
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", "-r", str(FPS), out_path]
    subprocess.run(cmd, check=True)
    return acc


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# ================================================================ main
def preview(ep_path, out_dir=None, per_shot=3):
    """Quick stills (start / middle / end of every shot) + contact sheet, no video."""
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    ep = load_episode(ep_path)
    out_dir = out_dir or os.path.dirname(os.path.abspath(ep_path))
    pdir = os.path.join(out_dir, "preview")
    shutil.rmtree(pdir, ignore_errors=True)
    os.makedirs(pdir)
    cast = json.load(open(os.path.join(ENGINE, "cast.json")))
    cast.update(ep.get("extra_cast", {}))
    sets = dict(ep["sets"]); sets["__endcard"] = {"far": endcard_bg()}
    ep = dict(ep)
    ep["shots"] = list(ep["shots"]) + ([end_card_shot(ep, cast)] if ep.get("end", {}).get("narration") else [])
    shots, total = build_timeline(ep, cast)
    qc = {"issues": [], "warnings": []}
    files = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        fonts_css = font_css()
        for s in shots:
            nf = int(s["dur"] * FPS)
            pts = sorted(set([min(nf - 1, int(nf * k / (per_shot - 1))) if per_shot > 1 else 0 for k in range(per_shot)]))
            pts = [max(0, min(nf - 1, x if x < nf - 1 else nf - 2)) for x in pts]
            fr = {fi: os.path.join(pdir, f"s{s['i']:02d}_{fi / FPS:05.2f}.png") for fi in pts}
            render_shot(s, ep, sets, cast, None, b, fonts_css, qc, only_frames=fr)
            files += [fr[k] for k in sorted(fr)]
        render_cover(ep, sets, cast, os.path.join(pdir, "cover.png"), b, fonts_css)
        b.close()
    # sheets, one row per shot
    tw, th = 216, 384
    rows = [files[i:i + per_shot] for i in range(0, len(files), per_shot)]
    for k in range(0, len(rows), 4):
        grp = rows[k:k + 4]
        sheet = Image.new("RGB", (tw * per_shot, (th + 24) * len(grp)), "white")
        d = ImageDraw.Draw(sheet)
        for r, row in enumerate(grp):
            for c, f in enumerate(row):
                sheet.paste(Image.open(f).convert("RGB").resize((tw, th)), (c * tw, r * (th + 24) + 24))
                d.text((c * tw + 4, r * (th + 24) + 6), os.path.basename(f)[:-4], fill="black")
        sheet.save(os.path.join(pdir, f"sheet_{k // 4 + 1:02d}.jpg"), quality=85)
    print(json.dumps({"total_seconds": round(total + 4.8, 1), "shots": [(s["i"], round(s["dur"], 1)) for s in shots],
                      "issues": qc["issues"], "warnings": qc["warnings"]}))
    return total + 4.8


def _prepare(ep_path):
    ep = load_episode(ep_path)
    cast = json.load(open(os.path.join(ENGINE, "cast.json")))
    cast.update(ep.get("extra_cast", {}))
    for k, v in ep.get("cast_overrides", {}).items():
        cast[k] = {**cast[k], **v}
    sets = dict(ep["sets"])
    sets["__endcard"] = {"far": endcard_bg()}
    ep = dict(ep)
    ep["shots"] = list(ep["shots"]) + ([end_card_shot(ep, cast)] if ep.get("end", {}).get("narration") else [])
    return ep, cast, sets


def _render_worker(ep_path, idxs, work, qcdir):
    from playwright.sync_api import sync_playwright
    ep, cast, sets = _prepare(ep_path)
    shots, total = build_timeline(ep, cast)
    qc = {"issues": [], "warnings": []}
    fonts_css = font_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for i in idxs:
            s = shots[i]
            seg = os.path.join(work, f"shot_{s['i']:02d}.mp4")
            t0 = time.time()
            render_shot(s, ep, sets, cast, seg, browser, fonts_css, qc, None)
            print(f"  shot {s['i']:2d}  {s['dur']:5.2f}s  rendered in {time.time() - t0:5.1f}s", flush=True)
        browser.close()
    return qc


def produce(ep_path, out_dir=None, only_cover=False, keep_segments=False, resume=False):
    from playwright.sync_api import sync_playwright
    t_start = time.time()
    ep = load_episode(ep_path)
    out_dir = out_dir or os.path.dirname(os.path.abspath(ep_path))
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(out_dir, "_work")
    os.makedirs(work, exist_ok=True)
    qcdir = os.path.join(out_dir, "qc")
    if not resume:
        shutil.rmtree(qcdir, ignore_errors=True)
    os.makedirs(qcdir, exist_ok=True)
    cast = json.load(open(os.path.join(ENGINE, "cast.json")))
    cast.update(ep.get("extra_cast", {}))
    for k, v in ep.get("cast_overrides", {}).items():
        cast[k] = {**cast[k], **v}
    for sh in ep["shots"]:
        for key in sh.get("actors", {}):
            if key.split("#")[0] not in cast:
                raise KeyError(f"actor {key!r} is not in cast.json or extra_cast")
    sets = dict(ep["sets"])
    sets["__endcard"] = {"far": endcard_bg()}
    ep = dict(ep)
    ep["shots"] = list(ep["shots"]) + ([end_card_shot(ep, cast)] if ep.get("end", {}).get("narration") else [])
    qc = {"issues": [], "warnings": [], "stages": {}}
    shots, total_story = build_timeline(ep, cast)
    brand_dur = 4.8
    total = total_story + brand_dur
    qc["stages"]["timeline"] = {"shots": len(shots), "duration": round(total, 2)}
    fonts_css = font_css()
    segs = []
    contact = {}
    if not only_cover:
        from concurrent.futures import ProcessPoolExecutor
        workers = max(1, min(int(os.environ.get("MICSTUDY_WORKERS", os.cpu_count() or 1)), 3))
        todo = [i for i in range(len(shots)) if not (resume and os.path.exists(os.path.join(work, f"shot_{i:02d}.mp4")))]
        order = sorted(todo, key=lambda i: -shots[i]["dur"])
        buckets = [[] for _ in range(workers)]
        loads = [0.0] * workers
        for i in order:
            k = loads.index(min(loads))
            buckets[k].append(i)
            loads[k] += shots[i]["dur"]
        jobs = []
        with ProcessPoolExecutor(workers) as ex:
            for b in buckets:
                if b:
                    jobs.append(ex.submit(_render_worker, ep_path, b, work, qcdir))
            for j in jobs:
                res = j.result()
                qc["issues"] += res["issues"]
                qc["warnings"] += res["warnings"]
        for s in shots:
            seg = os.path.join(work, f"shot_{s['i']:02d}.mp4")
            segs.append((seg, s["T"], s["dur"], s["trans"] if s["i"] else "cut", s["tdur"]))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        if not only_cover:
            bc = os.path.join(work, "brand.mp4")
            render_brand_card(ep, bc, browser, fonts_css, brand_dur, None)
            segs.append((bc, total_story, brand_dur, "cut", 0))
        render_cover(ep, sets, cast, os.path.join(out_dir, "cover.png"), browser, fonts_css)
        browser.close()
    if only_cover:
        return
    video = os.path.join(work, "video.mp4")
    vdur = assemble(segs, video, total)
    # ---------------- audio
    dialogue, sfx_ev, amb, music_regions = [], [], [], []
    srt = []
    for s in shots:
        sh = s["spec"]
        for ln in s["lines"]:
            pan = 0.0
            if not ln["narr"] and ln["who"] in sh.get("actors", {}):
                x = sh["actors"][ln["who"]].get("x", 540)
                pan = max(-1, min(1, (x - 540) / 540))
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
    score = A.Score(ep.get("key", "D"), ep.get("bpm", 78), ep.get("seed", 7))
    music = score.render([tuple(m) for m in merged], total)
    wav = os.path.join(work, "mix.wav")
    A.mix(total, dialogue, sfx_ev, amb, music, wav)
    with open(os.path.join(out_dir, "subtitles.srt"), "w") as f:
        for i, (a, b, txt) in enumerate(srt, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")
    master = os.path.join(out_dir, "master.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", master], check=True)
    make_upload_copy(master, os.path.join(out_dir, "upload.mp4"), qc)
    json.dump({"lines": [{"who": ln["who"], "text": ln["text"], "t0": s["T"] + ln["t0"], "t1": s["T"] + ln["t1"]}
                         for s in shots for ln in s["lines"]], "total": total},
              open(os.path.join(out_dir, "timeline.json"), "w"), indent=1)
    qc["stages"]["render_seconds"] = round(time.time() - t_start)
    json.dump(qc, open(os.path.join(out_dir, "render_log.json"), "w"), indent=1)
    if not keep_segments:
        shutil.rmtree(work, ignore_errors=True)
    print(f"done in {time.time() - t_start:.0f}s -> {master}")
    return master


def make_upload_copy(master, out, qc, limit_mb=9.5, target_mib=8.7):
    size = os.path.getsize(master)
    if size <= limit_mb * 1e6:
        shutil.copy(master, out)
        qc["stages"]["upload_copy"] = {"compressed": False, "bytes": size}
        return
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", master],
                               capture_output=True, text=True).stdout)
    abr = 96
    vbr = int(target_mib * 1024 * 1024 * 8 / dur / 1000 - abr)
    d = os.path.dirname(out)
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{vbr}k", "-pix_fmt", "yuv420p", "-profile:v", "high",
              "-tune", "animation", "-x264-params", "aq-mode=3"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master] + common + ["-pass", "1", "-passlogfile", os.path.join(d, "x264p"), "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master] + common + ["-pass", "2", "-passlogfile", os.path.join(d, "x264p"),
                    "-c:a", "aac", "-b:a", f"{abr}k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    for f in glob.glob(os.path.join(d, "x264p*")):
        os.remove(f)
    r = subprocess.run(["ffmpeg", "-i", out, "-i", master, "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"All:([\d.]+)", r.stderr)
    ssim = float(m.group(1)) if m else None
    qc["stages"]["upload_copy"] = {"compressed": True, "bytes": os.path.getsize(out), "video_kbps": vbr, "ssim": ssim}
