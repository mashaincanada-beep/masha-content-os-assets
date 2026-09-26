"""PILOT - FOUR QUARTERS  (engine test episode; not scheduled for publishing)

Concept sheet
1. Main child: Max Chen (Grade 4, age 9)
2. Setting: home + the corner market
3. Relationship: son / mother (Lin), grandson / grandfather (Grandpa Wei)
4. Situation: Max wants to buy Grandpa's favourite almond cookies with his own coins
5. Skill: money + mental addition (counting coins)          -> MATH
6. Tension: at the counter, with someone waiting, he loses count
7. Turning point: Mom offers ten minutes of practice, no pressure
8. Payoff: Saturday he counts it himself and gives Grandpa the gift
9. Parent message: practice shows up far from the page
10. Final line: "In a gift they chose, and paid for, all by themselves."
"""
from cs.scenekit import *

# ------------------------------------------------------------------ custom art
def armchair_back(x, y, c="#6F8FB8"):
    return (f'<rect x="{x - 230}" y="{y - 560}" width="460" height="560" rx="90" fill="{shade(c, 0.9)}"/>'
            f'<rect x="{x - 200}" y="{y - 110}" width="400" height="120" rx="30" fill="{c}"/>')

def armchair_front(x, y, c="#6F8FB8"):
    return (f'<rect x="{x - 250}" y="{y - 120}" width="90" height="250" rx="40" fill="{c}"/>'
            f'<rect x="{x + 160}" y="{y - 120}" width="90" height="250" rx="40" fill="{c}"/>'
            f'<rect x="{x - 250}" y="{y + 60}" width="500" height="100" rx="20" fill="{shade(c, 0.85)}"/>'
            f'<rect x="{x - 230}" y="{y + 150}" width="30" height="60" fill="#5A4636"/><rect x="{x + 200}" y="{y + 150}" width="30" height="60" fill="#5A4636"/>')

def newspaper(w=210):
    h = w * 0.72
    return (f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" fill="#F4F1EA" stroke="#D8D2C6" stroke-width="3"/>'
            f'<rect x="{-w * 0.42}" y="{-h * 0.4}" width="{w * 0.84}" height="{h * 0.14}" fill="#6B6275"/>'
            + "".join(f'<rect x="{-w * 0.42 + (i % 2) * w * 0.44}" y="{-h * 0.18 + (i // 2) * h * 0.11}" width="{w * 0.4}" height="{h * 0.05}" fill="#B8B0A4"/>' for i in range(10)))

def cookie_box(w=150):
    h = w * 0.62
    return (f'<rect x="{-w / 2}" y="{-h}" width="{w}" height="{h}" rx="10" fill="#E9A23B"/>'
            f'<rect x="{-w / 2}" y="{-h}" width="{w}" height="{h * 0.28}" rx="10" fill="#C7812A"/>'
            f'<ellipse cx="0" cy="{-h * 0.42}" rx="{w * 0.24}" ry="{h * 0.2}" fill="#FFF3DA"/>'
            f'<ellipse cx="{-w * 0.04}" cy="{-h * 0.44}" rx="{w * 0.13}" ry="{h * 0.1}" fill="#D9A15E"/>'
            f'<ellipse cx="{w * 0.05}" cy="{-h * 0.47}" rx="{w * 0.04}" ry="{h * 0.03}" fill="#FFF3DA"/>')

def register(x, y):
    return (f'<rect x="{x - 110}" y="{y - 150}" width="220" height="150" rx="16" fill="#4A5566"/>'
            f'<rect x="{x - 90}" y="{y - 230}" width="180" height="90" rx="10" fill="#2F3744"/>'
            f'<rect x="{x - 70}" y="{y - 212}" width="140" height="50" rx="6" fill="#9FF0B8"/>'
            + text(x, y - 175, "4.25", 34, "#1E4A2C", "Nunito", 900)
            + "".join(f'<rect x="{x - 80 + (i % 4) * 42}" y="{y - 125 + (i // 4) * 34}" width="32" height="24" rx="6" fill="#DCE3EC"/>' for i in range(12)))

def store_counter(y=1470, x0=520):
    return (f'<rect x="{x0}" y="{y}" width="{X1 - x0}" height="{Y1 - y}" fill="#3E8E6B"/>'
            f'<rect x="{x0}" y="{y + 40}" width="{X1 - x0}" height="16" fill="#357A5C"/>'
            f'<rect x="{x0 - 16}" y="{y - 24}" width="{X1 - x0 + 16}" height="40" rx="8" fill="#EDE6DA"/>'
            + "".join(f'<rect x="{x}" y="{y + 90}" width="170" height="120" rx="10" fill="#4FA27C"/>' for x in range(x0 + 40, X1, 210)))

def pendant(x, y):
    ri, rd = radial("#FFE3A8", "#FFE3A8", 0.6, 0)
    return (rd + f'<circle cx="{x}" cy="{y + 120}" r="520" fill="url(#{ri})"/>'
            f'<rect x="{x - 3}" y="{Y0}" width="6" height="{y - Y0}" fill="#4A3F35"/>'
            f'<path d="M{x - 110},{y + 70} Q{x},{y - 40} {x + 110},{y + 70}Z" fill="#E4513C"/><ellipse cx="{x}" cy="{y + 72}" rx="40" ry="14" fill="#FFF3C4"/>')

def autumn_tree(x, y, s=1.0):
    return tree(x, y, s, leaf="#E9893B") + "".join(
        f'<circle cx="{x + dx * s}" cy="{y + dy * s}" r="{r * s}" fill="{c}"/>'
        for dx, dy, r, c in ((-80, -470, 70, "#F2B33D"), (90, -380, 60, "#D9643A"), (20, -560, 55, "#F2B33D")))

# ------------------------------------------------------------------ sets
SETS = {
    "living": {
        "far": wall("#F4DDBF", pattern="stripes", floor_y=1450) + floor(1450, "#B98A5E")
               + window(560, 330, 320, 400, "golden", curtain="#E98A6B")
               + picture(110, 420, 190, 150) + picture(170, 620, 120, 150, art="#F2C14E", kind="drawing")
               + door(-150, 900, 230, 560, "#C99366"),
        "mid": rug(620, 1640, 520, 110, "#C96B5A") + lamp(1000, 1480, 1.1) + plant(90, 1500, 1.0, "#6F8FB8")
               + armchair_back(720, 1560),
        "front": armchair_front(720, 1560),
        "near": fg_blur(plant(-120, 2140, 1.6, "#E98A6B", "#3F8F5B"), 9),
    },
    "store": {
        "far": wall("#E6F2EA", floor_y=1300) + floor(1300, "#D9D2C4", "tile")
               + f'<rect x="-120" y="110" width="760" height="140" rx="20" fill="#E4513C"/>' + text(260, 205, "CORNER MARKET", 64, "#FFFFFF", "Fraunces", 900)
               + market_shelf(-200, 330, 700, 3, 170, seed=5) + market_shelf(700, 330, 620, 3, 170, seed=8)
               + clock(900, 200, 55, h=10, m=10),
        "mid": "",
        "front": store_counter(1470, 520) + register(1030, 1470),
    },
    "street": {
        "far": sky("day", 1150) + cloud(200, 300, 1.2) + cloud(780, 460, 0.9)
               + house(150, 1150, 1.1, "#F6D6A8", "#D9644A", "#1C8FFF") + house(820, 1150, 1.0, "#CFE3F2", "#7C5CBF", "#FE007A"),
        "mid": ground(1350, "#9CCB7E") + f'<rect x="{X0}" y="1480" width="{X1 - X0}" height="{Y1 - 1480}" fill="#D8D2C8"/>'
               + "".join(f'<rect x="{x}" y="1480" width="5" height="{Y1 - 1480}" fill="#C4BDB2"/>' for x in range(X0, X1, 260))
               + autumn_tree(-40, 1400, 1.1) + autumn_tree(1120, 1420, 1.0) + fence(1440, "#FFFFFF"),
        "near": fg_blur("".join(f'<ellipse cx="{x}" cy="{y}" rx="26" ry="12" fill="{c}" transform="rotate({r} {x} {y})"/>'
                               for x, y, r, c in ((120, 1990, 20, "#E9893B"), (400, 2060, -30, "#D9643A"), (820, 2010, 40, "#F2B33D"), (980, 2100, 10, "#E9893B"))), 3),
    },
    "kitchen": {
        "far": wall("#F3DFC6", floor_y=1480, pattern="wainscot", pcolor="#EBD2B3") + floor(1480, "#A97C57")
               + window(360, 360, 300, 360, "dusk", curtain="#7FB7A4")
               + upper_cabinets(-230, 330, 520, 260, "#9FCBBE") + counter(-230, 1150, 520, cab="#7FB7A4")
               + fridge(800, 720, 280, 760),
        "mid": pendant(560, 560),
        "front": (f'<rect x="{X0}" y="1545" width="{X1 - X0}" height="{Y1 - 1545}" fill="#C98B5A"/>'
                 f'<rect x="{X0}" y="1530" width="{X1 - X0}" height="26" rx="8" fill="#D9A06C"/>'
                 + "".join(f'<rect x="{X0}" y="{y}" width="{X1 - X0}" height="4" fill="#B67C4E" opacity=".5"/>' for y in range(1620, 2180, 90))),
    },
}

WORKSHEET = p_worksheet(210, "#1C8FFF", "math")

EPISODE = {
    "title": "Four Quarters",
    "slug": "four-quarters",
    "key": "D", "bpm": 76, "seed": 11,
    "brand_line": "Small practice. Bigger moments.",
    "extra_cast": {
        "mr_hassan": {"name": "Mr. Hassan", "role": "store owner", "kind": "adult", "sex": "m", "skin": "brown",
                      "hair": {"style": "adult_m", "color": "#1E1614"}, "beard": True,
                      "top": {"style": "shirt", "color": "#F2C14E", "accent": "#FFFFFF"},
                      "bottom": {"style": "pants", "color": "#3A3F4B"}, "voice": {"id": "am_liam", "speed": 0.95, "pitch": 1.0}},
    },
    "sets": SETS,
    "shots": [
        # 1 - living room: the secret plan (Grandpa dozing in the background)
        {"set": "living", "music": "curious", "amb": "home", "title": True, "title_t": [0.8, 4.6], "trans": "fade", "tdur": 0.8,
         "grade": "warm", "fx": ["vignette", "dust"], "start": 2.9,
         "cam": [[0, 560, 1080, 1.1], ["end", 440, 1160, 1.22]],
         "actors": {"grandpa_wei": {"x": 720, "y": 1720, "s": 1.02, "legs": "sit", "expr": "calm", "eye": "closed", "armL": "hold_low", "armR": "hold_low", "auto_look": False},
                    "max": {"x": 330, "y": 1790, "s": 1.18, "expr": "curious", "armL": "down", "armR": "hold"},
                    "lin": {"x": 140, "y": 1740, "s": 1.02, "expr": "tender", "turn": 0.4}},
         "props": [{"id": "paper", "svg": newspaper(), "attach": ["grandpa_wei", "R", -60, -10], "rot": -8},
                   {"id": "jar", "svg": p_jar(90, "¢"), "attach": ["max", "R", -10, 40]}],
         "script": [
             {"who": "max", "line": "Grandpa's birthday is on Saturday.", "expr": "curious", "speed": 0.95},
             {"who": "lin", "line": "Mm-hm. What do you want to give him?"},
             {"who": "max", "line": "His almond cookies. |0.3| The ones he always buys.", "expr": "happy"},
             {"sfx": "coins", "gain": 0.6},
             {"who": "max", "line": "But this time... |0.4| I want to buy them myself.", "expr": "determined"},
             {"who": "lin", "line": "With your own money?", "expr": "happy"},
             {"who": "max", "line": "Every coin.", "expr": "proud"},
         ],
         "beats": [{"t": "L3", "who": "max", "set": {"armR": [-20, -150]}, "dur": 0.4},
                   {"t": "L3.end", "who": "max", "set": {"armR": "hold"}, "dur": 0.5}],
         "tail": 0.8},

        # 2 - store: arriving at the counter
        {"set": "store", "music": "curious", "amb": "market", "trans": "dissolve", "tdur": 0.7, "grade": "soft",
         "cam": [[0, 540, 1000, 1.0], ["end", 560, 1080, 1.08]],
         "sfx": [{"name": "chime", "t": 0.2, "gain": 0.35}, {"name": "footsteps", "t": 0.3, "gain": 0.5, "kw": {"n": 4, "gap": 0.35}}],
         "actors": {"mr_hassan": {"x": 840, "y": 1660, "s": 1.02, "expr": "happy", "armL": "hold_low", "armR": "down"},
                    "max": {"x": -120, "y": 1780, "s": 1.15, "expr": "hopeful", "armL": "down", "armR": "hold"}},
         "beats": [{"t": 0.2, "who": "max", "set": {"walk_to": 410}, "dur": 1.6},
                   {"t": "L1", "who": "max", "set": {"armR": "reach"}, "dur": 0.4},
                   {"t": "L1+0.5", "who": "box", "set": {"attach": None, "x": 640, "y": 1462}, "dur": 0.01},
                   {"t": "L1+0.6", "who": "max", "set": {"armR": "counter"}, "dur": 0.4}],
         "props": [{"id": "box", "svg": cookie_box(), "attach": ["max", "R", 10, 30]}],
         "start": 1.4,
         "script": [
             {"who": "mr_hassan", "line": "Morning, Max! Just you today?", "expr": "happy"},
             {"who": "max", "line": "Just me. |0.2| Just these, please.", "expr": "hopeful"},
             {"who": "mr_hassan", "line": "That's four twenty-five.", "expr": "calm"},
         ],
         "tail": 0.4},

        # 3 - counting at the counter (closer)
        {"set": "store", "music": "uncertain", "amb": "market", "grade": "soft", "trans": "cut",
         "cam": [[0, 540, 1300, 1.55], ["end", 530, 1320, 1.7]],
         "actors": {"mr_hassan": {"x": 840, "y": 1660, "s": 1.02, "expr": "calm", "armL": "hold_low", "armR": "down"},
                    "max": {"x": 410, "y": 1780, "s": 1.15, "expr": "focused", "armL": "down", "armR": "counter", "look": (0.3, 0.8), "auto_look": False}},
         "props": [{"id": "box", "svg": cookie_box(), "x": 640, "y": 1462},
                   {"id": "coins", "svg": p_coins(5), "x": 585, "y": 1462, "s": 1.0}],
         "start": 0.5,
         "script": [
             {"sfx": "coins", "gain": 0.7},
             {"who": "max", "line": "Twenty-five... |0.5| fifty... |0.5| seventy-five...", "expr": "focused", "speed": 0.9},
             {"who": "max", "line": "a dollar... |0.4| a dollar... um...", "expr": "unsure", "speed": 0.9},
             {"pause": 0.8},
         ],
         "beats": [{"t": "L1+0.6", "who": "max", "set": {"look": (-0.9, 0), "turn": -0.4}, "dur": 0.4}],
         "tail": 0.2},

        # 4 - the line behind him
        {"set": "store", "music": "uncertain", "amb": "market", "grade": "soft", "trans": "cut",
         "cam": [[0, 280, 1250, 1.45], ["end", 300, 1250, 1.5]],
         "sfx": [{"name": "footsteps", "t": 0.6, "gain": 0.35, "kw": {"n": 3, "gap": 0.5}}],
         "actors": {"jonah": {"x": 150, "y": 1700, "s": 1.05, "expr": "tired", "armL": "cross", "armR": "cross", "look": (0.5, -0.2), "auto_look": False},
                    "grace": {"x": 10, "y": 1680, "s": 0.95, "expr": "calm", "armL": "hold_low", "armR": "down", "look": (1, 0), "auto_look": False},
                    "max": {"x": 430, "y": 1780, "s": 1.15, "expr": "embarrassed", "armL": "down", "armR": "rest", "look": (-0.8, 0), "turn": -0.5, "auto_look": False}},
         "beats": [{"t": 1.0, "who": "jonah", "set": {"look": (1, 0.6), "tilt": -3}, "dur": 0.6}],
         "min": 2.8},

        # 5 - "I'll come back."
        {"set": "store", "music": "uncertain", "amb": "market", "grade": "soft", "trans": "cut",
         "cam": [[0, 600, 1290, 1.45], ["end", 610, 1290, 1.5]],
         "actors": {"mr_hassan": {"x": 840, "y": 1660, "s": 1.02, "expr": "tender", "armL": "hold_low", "armR": "down"},
                    "max": {"x": 410, "y": 1780, "s": 1.15, "expr": "embarrassed", "armL": "down", "armR": "counter"}},
         "props": [{"id": "box", "svg": cookie_box(), "x": 640, "y": 1462},
                   {"id": "coins", "svg": p_coins(5), "x": 585, "y": 1462}],
         "start": 0.4,
         "script": [
             {"who": "mr_hassan", "line": "Hey. |0.3| Take your time, buddy.", "expr": "tender", "speed": 0.92},
             {"pause": 0.9},
             {"who": "max", "line": "It's okay.", "expr": "embarrassed", "speed": 0.9},
             {"pause": 0.5},
             {"who": "max", "line": "I'll come back.", "expr": "sad", "speed": 0.88},
             {"sfx": "coins", "gain": 0.5},
         ],
         "beats": [{"t": "L2+0.3", "who": "max", "set": {"armR": "reach", "look": (0.4, 0.8)}, "dur": 0.5},
                   {"t": "L2+0.9", "who": "coins", "set": {"op": 0}, "dur": 0.3},
                   {"t": "L2+1.0", "who": "max", "set": {"armR": "hold", "walk_to": 150}, "dur": 1.6},
                   {"t": "L2+1.0", "who": "max", "set": {"turn": -0.6}, "dur": 0.4}],
         "tail": 1.0},

        # 6 - walking home, autumn
        {"set": "street", "music": "reflective", "amb": "street", "grade": "golden", "trans": "dissolve", "tdur": 0.9,
         "fx": ["vignette", "dust"],
         "cam": [[0, 640, 1150, 1.1], ["end", 440, 1180, 1.12]],
         "sfx": [{"name": "footsteps", "t": 0.3, "gain": 0.45, "kw": {"n": 9, "gap": 0.52}}],
         "actors": {"max": {"x": 1000, "y": 1760, "s": 1.1, "expr": "sad", "armL": "down", "armR": "hold_low", "turn": -0.4, "look": (-0.3, 0.8), "auto_look": False}},
         "props": [{"id": "jar", "svg": p_jar(80, "¢"), "attach": ["max", "R", 0, 20]}],
         "beats": [{"t": 0.2, "who": "max", "set": {"walk_to": 120}, "dur": 5.0}],
         "min": 4.6},

        # 7 - kitchen evening: Mom notices
        {"set": "kitchen", "music": "reflective", "amb": "kitchen", "grade": "warm", "trans": "dissolve", "tdur": 0.8,
         "caption": "That evening", "caption_t": [0.4, 2.6],
         "cam": [[0, 560, 1250, 1.2], ["end", 580, 1260, 1.28]],
         "actors": {"max": {"x": 380, "y": 1660, "s": 1.2, "legs": "sit", "expr": "disappointed", "armL": "hold_low", "armR": "hold_low", "look": (0, 0.8), "auto_look": False},
                    "lin": {"x": 1180, "y": 1700, "s": 1.02, "expr": "tender", "armL": "down", "armR": "down", "turn": -0.4}},
         "props": [{"id": "jar", "svg": p_jar(90, "¢"), "x": 520, "y": 1640}],
         "beats": [{"t": 0.3, "who": "lin", "set": {"walk_to": 760}, "dur": 1.8},
                   {"t": 2.1, "who": "lin", "set": {"legs": "sit", "y": 1690}, "dur": 0.3},
                   {"t": "L0", "who": "max", "set": {"auto_look": True}, "dur": 0.1},
                   {"t": "L4", "who": "lin", "set": {"armR": "reach"}, "dur": 0.5}],
         "start": 2.4,
         "script": [
             {"who": "lin", "line": "No cookies?", "expr": "tender", "speed": 0.92},
             {"who": "max", "line": "I couldn't count it fast enough. |0.5| There were people waiting.", "expr": "disappointed", "speed": 0.92},
             {"pause": 0.7},
             {"who": "lin", "line": "That's a hard moment.", "expr": "tender", "speed": 0.9},
             {"pause": 0.4},
             {"who": "lin", "line": "Want to practise a little? |0.3| Just ten minutes.", "expr": "hopeful"},
             {"who": "max", "line": "...Right now?", "expr": "unsure"},
             {"who": "lin", "line": "Right now. Just us.", "expr": "happy"},
         ],
         "tail": 1.0},

        # 8 - practice, Monday
        {"set": "kitchen", "music": "hopeful", "amb": "kitchen", "grade": "warm", "trans": "dissolve", "tdur": 0.6,
         "caption": "Monday", "caption_t": [0.2, 1.8],
         "cam": [[0, 560, 1350, 1.55], ["end", 560, 1360, 1.6]],
         "actors": {"max": {"x": 400, "y": 1660, "s": 1.2, "legs": "sit", "expr": "focused", "armL": "rest", "armR": "rest", "look": (0.3, 0.9), "auto_look": False},
                    "lin": {"x": 760, "y": 1690, "s": 1.02, "legs": "sit", "expr": "tender", "armL": "hold_low", "armR": "hold_low", "look": (-0.6, 0.6), "auto_look": False}},
         "props": [{"id": "ws", "svg": WORKSHEET, "x": 580, "y": 1700, "s": 1.0, "rot": -6, "squash": 0.5},
                   {"id": "coins", "svg": p_coins(4), "x": 400, "y": 1650}],
         "start": 1.2,
         "script": [
             {"sfx": "coins", "gain": 0.5},
             {"who": "max", "line": "Quarter, quarter... |0.3| that's fifty.", "expr": "focused", "speed": 0.92},
             {"who": "lin", "line": "And the next one?", "expr": "tender"},
             {"who": "max", "line": "Seventy-five!", "expr": "happy"},
         ],
         "tail": 0.5},

        # 9 - practice, Wednesday: catching his own mistake
        {"set": "kitchen", "music": "hopeful", "amb": "kitchen", "grade": "warm", "trans": "dissolve", "tdur": 0.5,
         "caption": "Wednesday", "caption_t": [0.2, 1.8],
         "cam": [[0, 560, 1290, 1.42], ["end", 555, 1295, 1.48]],
         "actors": {"max": {"x": 400, "y": 1660, "s": 1.2, "legs": "sit", "expr": "focused", "armL": "rest", "armR": "rest", "look": (0.3, 0.9), "auto_look": False},
                    "lin": {"x": 760, "y": 1690, "s": 1.02, "legs": "sit", "expr": "tender", "armL": "hold_low", "armR": "hold_low"}},
         "props": [{"id": "ws", "svg": WORKSHEET, "x": 580, "y": 1700, "s": 1.0, "rot": 4, "squash": 0.5},
                   {"id": "coins", "svg": p_coins(6), "x": 400, "y": 1650}],
         "start": 1.2,
         "script": [
             {"who": "max", "line": "A dollar ten... |0.5| no, wait.", "expr": "thinking", "speed": 0.95},
             {"pause": 0.4},
             {"who": "max", "line": "A dollar fifteen.", "expr": "determined"},
             {"who": "lin", "line": "You caught that yourself.", "expr": "proud"},
         ],
         "beats": [{"t": "L0+0.9", "who": "max", "set": {"look": (0.6, -0.6)}, "dur": 0.3},
                   {"t": "L1", "who": "max", "set": {"look": (0.3, 0.9)}, "dur": 0.3},
                   {"t": "L2", "who": "max", "set": {"expr": "proud", "look": (1, 0), "turn": 0.35}, "dur": 0.3}],
         "tail": 0.6},

        # 10 - Friday: alone, quietly
        {"set": "kitchen", "music": "hopeful", "amb": "kitchen", "grade": "warm", "trans": "dissolve", "tdur": 0.5,
         "caption": "Friday", "caption_t": [0.2, 1.8],
         "cam": [[0, 420, 1300, 1.6], ["end", 420, 1290, 1.66]],
         "actors": {"max": {"x": 400, "y": 1660, "s": 1.2, "legs": "sit", "expr": "focused", "armL": "rest", "armR": "rest", "look": (0.3, 0.9), "auto_look": False}},
         "props": [{"id": "coins", "svg": p_coins(6), "x": 470, "y": 1660}],
         "start": 1.0,
         "script": [
             {"sfx": "coins", "gain": 0.4},
             {"who": "max", "line": "Four dollars... |0.5| and twenty-five cents.", "expr": "focused", "speed": 0.92},
         ],
         "beats": [{"t": "L0.end", "who": "max", "set": {"expr": "proud", "look": (0, 0)}, "dur": 0.4}],
         "tail": 1.2},

        # 11 - Saturday, the counter again
        {"set": "store", "music": "hopeful", "amb": "market", "grade": "soft", "trans": "dissolve", "tdur": 0.7,
         "caption": "Saturday", "caption_t": [0.2, 1.8],
         "cam": [[0, 600, 1210, 1.3], ["end", 590, 1230, 1.38]],
         "actors": {"mr_hassan": {"x": 840, "y": 1660, "s": 1.02, "expr": "happy", "armL": "hold_low", "armR": "down"},
                    "jonah": {"x": 250, "y": 1690, "s": 1.0, "expr": "calm", "armL": "down", "armR": "down"},
                    "max": {"x": 410, "y": 1780, "s": 1.15, "expr": "determined", "armL": "down", "armR": "counter"}},
         "props": [{"id": "box", "svg": cookie_box(), "x": 640, "y": 1462},
                   {"id": "coins", "svg": p_coins(5), "x": 585, "y": 1462}],
         "start": 1.3,
         "script": [
             {"who": "mr_hassan", "line": "Four twenty-five, right?", "expr": "happy"},
             {"who": "max", "line": "Right.", "expr": "determined"},
             {"sfx": "coins", "gain": 0.6},
             {"who": "max", "line": "One, two, three, four dollars. |0.5| And twenty-five cents.", "expr": "determined", "speed": 0.95},
             {"pause": 0.3},
             {"who": "mr_hassan", "line": "Exactly right.", "expr": "joy"},
         ],
         "beats": [{"t": "L1", "who": "max", "set": {"look": (0.4, 0.8)}, "dur": 0.3},
                   {"t": "L2.end", "who": "max", "set": {"look": (1, 0), "expr": "proud"}, "dur": 0.3},
                   {"t": "L3", "who": "max", "set": {"expr": "joy"}, "dur": 0.2}],
         "tail": 0.8},

        # 12 - Jonah's small nod
        {"set": "store", "music": "warm", "amb": "market", "grade": "soft", "trans": "cut",
         "cam": [[0, 360, 1250, 1.38], ["end", 370, 1250, 1.42]],
         "actors": {"jonah": {"x": 150, "y": 1700, "s": 1.05, "expr": "happy", "armL": "down", "armR": "down", "look": (1, 0), "turn": 0.4, "auto_look": False},
                    "max": {"x": 470, "y": 1780, "s": 1.15, "expr": "proud", "armL": "hold", "armR": "hold", "look": (-1, 0), "turn": -0.5, "auto_look": False}},
         "props": [{"id": "box", "svg": cookie_box(), "attach": ["max", "L", 30, 20]}],
         "start": 0.4,
         "script": [{"who": "jonah", "line": "Nice counting.", "expr": "happy"}],
         "beats": [{"t": "L0", "who": "jonah", "set": {"armR": "thumbs", "tilt": 3}, "dur": 0.4}],
         "tail": 1.1},

        # 13 - the gift
        {"set": "living", "music": "warm", "amb": "home", "grade": "golden", "trans": "dissolve", "tdur": 0.9, "fx": ["vignette", "dust"],
         "cam": [[0, 580, 1200, 1.2], ["end", 620, 1220, 1.34]],
         "actors": {"grandpa_wei": {"x": 720, "y": 1720, "s": 1.02, "legs": "sit", "expr": "calm", "armL": "hold_low", "armR": "hold_low"},
                    "max": {"x": 390, "y": 1790, "s": 1.18, "expr": "proud", "armL": "down", "armR": "give"},
                    "lin": {"x": 40, "y": 1720, "s": 1.0, "expr": "tender", "armL": "chest", "armR": "down", "look": (1, 0), "auto_look": False}},
         "props": [{"id": "box", "svg": cookie_box(), "attach": ["max", "R", 10, -10]}],
         "start": 0.6,
         "script": [
             {"who": "max", "line": "Happy birthday, Grandpa.", "expr": "happy", "to": "grandpa_wei"},
             {"who": "grandpa_wei", "line": "My almond cookies!", "expr": "surprised"},
             {"who": "max", "line": "I bought them myself. |0.4| I counted every coin.", "expr": "proud"},
             {"pause": 0.6},
             {"who": "grandpa_wei", "line": "Every coin?", "expr": "tender", "speed": 0.85},
             {"who": "max", "line": "Every single one.", "expr": "joy"},
         ],
         "beats": [{"t": "L1", "who": "grandpa_wei", "set": {"armL": "give", "armR": "hold", "lean": -4}, "dur": 0.6},
                   {"t": "L1+0.6", "who": "box", "set": {"attach": ["grandpa_wei", "R", 0, -20]}, "dur": 0.01},
                   {"t": "L1+0.6", "who": "max", "set": {"armL": "down", "armR": "hold"}, "dur": 0.5},
                   {"t": "L4.end+0.3", "who": "grandpa_wei", "set": {"armL": "reach", "armR": "hold", "expr": "joy", "lean": -6}, "dur": 0.7},
                   {"t": "L4.end+0.3", "who": "max", "set": {"x": 420, "armL": "down", "armR": "reach", "expr": "joy", "lean": 3}, "dur": 0.8}],
         "tail": 1.8},

        # 14 - Lin in the doorway, narration
        {"set": "living", "music": "warm", "amb": "home", "grade": "golden", "trans": "cut", "fx": ["vignette", "dust"],
         "cam": [[0, 120, 1220, 1.6], ["end", 140, 1210, 1.7]],
         "actors": {"lin": {"x": 60, "y": 1720, "s": 1.0, "expr": "tender", "armL": "chest", "armR": "down", "look": (1, 0), "turn": 0.4, "auto_look": False}},
         "start": 0.6,
         "script": [{"who": "narrator", "line": "It was never really about the cookies."}],
         "tail": 1.2},
    ],
    "end": {
        "narration": ["Sometimes practice shows up far from the page.",
                      "In a gift they chose... |0.3| and paid for, all by themselves."],
        "music": "gentle",
    },
    "cover": {"shot": 2, "cam": [560, 1420, 1.5], "title_y": 300, "title_size": 110,
              "override": {"actors": {"mr_hassan": {"x": 840, "y": 1660, "s": 1.02, "expr": "calm", "armL": "hold_low", "armR": "down"},
                                      "max": {"x": 410, "y": 1780, "s": 1.15, "expr": "unsure", "armL": "down", "armR": "counter", "look": (0.3, 0.8)}}}},
}
