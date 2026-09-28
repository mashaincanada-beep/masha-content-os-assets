"""MIC Study v3 hand-drawn sets and props (colored pencil + wobbly ink, same universe as the kit).

Every set function returns {"back": svg, "mid": svg, "fg": svg, "floor": y}
  back - wall / sky / far furniture (drawn behind the characters, parallax 0.9)
  mid  - furniture characters sit or stand behind (tables, counters, desks) - drawn over bodies, under arms
  fg   - foreground pieces (parallax 1.12)
Sets: kitchen, bedroom, classroom, living_room, park, store, stage, library, hallway.
Props (drawn after mid): book, worksheet, mug, pencil, coins, backpack, ball, lunchbox, plate_cookies, jar, trophy.
Episodes can add their own set functions with the same return shape (see VISUAL-V3.md).
"""
import math
import doodlefilm as D
from doodlefilm import K, spoly, seed

W, H = 1080, 1920


def wall_floor(wall="#FFE9CF", floor_col="#D7B98E", floor=1640):
    s = K.paper(W, H, "#FFF8EC")
    seed(1)
    s += K.pencil(f'<rect x="0" y="0" width="{W}" height="{floor}"/>', wall, (0, 0, W, floor), angle=-12, gap=18, tint=.08)
    seed(2)
    s += K.pencil(f'<rect x="0" y="{floor}" width="{W}" height="{H - floor}"/>', floor_col, (0, floor, W, H), angle=-4, gap=11, tint=.25)
    s += K.ink(f"M0 {floor + 2} Q540 {floor - 8} 1080 {floor + 4}", 3.5)
    return s


def window(x, y, w, h, night=False, sd=3):
    seed(sd)
    sky = "#5C6BC0" if night else "#90CAF9"
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFF8EC"/>'
    s += K.pencil(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>', sky, (x, y, x + w, y + h), angle=-30, gap=8, tint=.25)
    s += K.ink(f"M{x} {y} L{x + w} {y + 2} L{x + w - 2} {y + h} L{x + 2} {y + h - 2} Z M{x + w / 2} {y + 1} L{x + w / 2 + 1} {y + h - 1} M{x + 1} {y + h / 2} L{x + w - 1} {y + h / 2 + 1}", 5)
    if night:
        mx, my = x + w * .25, y + h * .25
        s += f'<path d="M{mx} {my} a40 40 0 1 0 48 50 a32 32 0 1 1 -48 -50z" fill="#FFF59D" stroke="{D.INK}" stroke-width="3.5" filter="url(#ink)"/>'
        for i, (sx, sy, sr) in enumerate([(.8, .2, 15), (.72, .75, 11), (.18, .8, 10)]):
            seed(sd * 10 + i)
            s += K.star(x + w * sx, y + h * sy, sr)
    else:
        s += f'<circle cx="{x + w * .75}" cy="{y + h * .25}" r="{min(w, h) * .12:.0f}" fill="#FFD54F" stroke="{D.INK}" stroke-width="3" filter="url(#ink)"/>'
        s += K.ink(f"M{x + w * .15} {y + h * .3} q20 -20 40 0 q20 -20 40 0", 3, "#FFFFFF")
    for i, cx0 in enumerate((x - 40, x + w - 30)):
        seed(sd * 20 + i)
        s += spoly([(cx0, y - 30), (cx0 + 70, y - 30), (cx0 + 50, y + h + 30), (cx0 + 5, y + h + 40)], "#F48FB1", angle=85)
    s += K.ink(f"M{x - 50} {y - 30} L{x + w + 50} {y - 32}", 5)
    return s


def frame_drawing(x, y, sd=30):
    seed(sd)
    s = spoly([(x, y), (x + 170, y - 4), (x + 174, y + 140), (x - 4, y + 144)], "#FFFFFF", gap=9)
    seed(sd + 1)
    s += spoly([(x + 40, y + 100), (x + 90, y + 62), (x + 135, y + 100), (x + 135, y + 132), (x + 40, y + 132)], "#EF9A9A", gap=5, w=3)
    return s + f'<circle cx="{x + 142}" cy="{y + 36}" r="16" fill="#FFD54F" stroke="{D.INK}" stroke-width="2.5" filter="url(#ink)"/>'


def lamp(x, sd=40):
    seed(sd)
    return (K.ink(f"M{x} 0 L{x} 200", 3.5) + spoly([(x - 55, 200), (x + 55, 200), (x + 100, 285), (x - 100, 285)], "#FFCA28", angle=-20)
            + f'<ellipse cx="{x}" cy="1150" rx="520" ry="420" fill="url(#glow)"/>')


def table(x0=120, x1=960, top=1250, sd=70, color="#C8A27A"):
    seed(sd)
    s = spoly([(x0, top), (x1, top - 4), (x1 + 15, top + 35), (x0 - 12, top + 40)], color, angle=-8)
    seed(sd + 1)
    s += spoly([(x0 + 15, top + 40), (x1 - 10, top + 36), (x1 - 15, top + 85), (x0 + 20, top + 88)], "#B08968", angle=-8)
    return s + K.stick([(x0 + 40, top + 85), (x0 + 45, 1640)], 7) + K.stick([(x1 - 35, top + 82), (x1 - 40, 1640)], 7)


def chair(cx, seat=1250, color="#BCAAA4", sd=60):
    seed(sd)
    s = spoly([(cx - 85, seat - 270), (cx + 85, seat - 270), (cx + 80, seat), (cx - 80, seat)], color, angle=88, gap=7)
    s += K.ink(f"M{cx - 85} {seat - 220} L{cx + 85} {seat - 220} M{cx - 83} {seat - 160} L{cx + 83} {seat - 160}", 3)
    return s + K.stick([(cx - 78, seat + 80), (cx - 82, 1640)], 6) + K.stick([(cx + 78, seat + 80), (cx + 82, 1640)], 6)


# ------------------------------------------------------------------ sets
def kitchen(t=0, night=True, chairs=(430, 700), table_top=1250, **kw):
    back = wall_floor() + window(110, 330, 330, 400, night) + frame_drawing(610, 420) + lamp(540)
    seed(50)
    back += spoly([(900, 1170), (1080, 1170), (1080, 1640), (905, 1640)], "#A5D6A7", angle=-60)
    back += K.ink("M890 1170 L1080 1168", 6)
    seed(51)
    back += spoly([(930, 1100), (1030, 1100), (1022, 1168), (938, 1168)], "#90A4AE")
    for i in range(3):
        ph = t * 0.9 + i * 1.3
        yy = 1080 - (ph % 3) * 45
        back += (f'<path d="M{950 + i * 30} {yy:.0f} q-14 -18 0 -36 q14 -18 0 -36" stroke="#B0BEC5" stroke-width="4" fill="none" '
                 f'stroke-linecap="round" opacity="{max(0.0, 0.7 - (ph % 3) * 0.23):.2f}" filter="url(#ink)"/>')
    back += "".join(chair(c, table_top, sd=60 + i) for i, c in enumerate(chairs))
    return {"back": back, "mid": table(120, 960, table_top), "fg": plant(70, 1760), "floor": 1640, "table_top": table_top}


def bedroom(t=0, night=True, **kw):
    back = wall_floor("#E1D5F5", "#D7B98E") + window(640, 300, 300, 380, night, sd=5) + frame_drawing(160, 380, sd=33)
    seed(90)   # bed
    back += spoly([(60, 1280), (760, 1280), (760, 1480), (60, 1480)], "#90CAF9", cross=True)
    seed(91)
    back += spoly([(40, 1060), (120, 1060), (120, 1640), (40, 1640)], "#BCAAA4", angle=88)
    seed(92)
    back += spoly([(140, 1220), (330, 1210), (340, 1285), (130, 1290)], "#FFFFFF", gap=9)
    for i in range(5):
        seed(93 + i)
        back += K.star(220 + i * 110, 1380 + (i % 2) * 40, 14, "#FFD54F")
    back += K.stick([(80, 1480), (82, 1640)], 7) + K.stick([(740, 1480), (738, 1640)], 7)
    seed(98)   # bookshelf
    back += spoly([(830, 1060), (1060, 1060), (1060, 1640), (830, 1640)], "#D7CCC8", angle=80)
    for row in range(3):
        for j in range(5):
            seed(100 + row * 5 + j)
            c = ["#EF9A9A", "#90CAF9", "#A5D6A7", "#FFE082", "#CE93D8"][(row + j) % 5]
            bx = 845 + j * 42
            by = 1120 + row * 160
            back += spoly([(bx, by), (bx + 34, by), (bx + 34, by + 120), (bx, by + 120)], c, gap=4, w=3)
    return {"back": back, "mid": "", "fg": "", "floor": 1640, "bed_top": 1280}


def classroom(t=0, desks=(300, 780), desk_top=1300, **kw):
    back = wall_floor("#FFF3C4", "#CFD8DC") + window(820, 300, 220, 360, False, sd=7)
    seed(110)   # chalkboard
    back += spoly([(80, 300), (740, 296), (744, 760), (84, 764)], "#2E7D32", angle=-20, gap=6)
    back += K.ink("M84 300 L740 296 L744 760 L84 764 Z", 7, "#6D4C41")
    back += ('<text x="140" y="420" font-family="Architects Daughter" font-size="58" fill="#FFFFFF" opacity=".92">3 + 4 = 7</text>'
             '<text x="140" y="520" font-family="Architects Daughter" font-size="44" fill="#FFFFFF" opacity=".85">cat  hat  sat</text>')
    back += "".join(f'<text x="{110 + i * 70}" y="860" font-family="Architects Daughter" font-size="46" fill="{c}">{ch}</text>'
                    for i, (ch, c) in enumerate(zip("ABCDEFGHI", ["#E53935", "#FB8C00", "#FDD835", "#43A047", "#1E88E5", "#8E24AA", "#E53935", "#FB8C00", "#43A047"])))
    back += "".join(chair(c, desk_top - 20, "#FFCC80", sd=120 + i) for i, c in enumerate(desks))
    mid = ""
    for i, c in enumerate(desks):
        seed(130 + i)
        mid += spoly([(c - 170, desk_top), (c + 170, desk_top - 3), (c + 180, desk_top + 30), (c - 178, desk_top + 34)], "#BCAAA4", angle=-8)
        mid += K.stick([(c - 150, desk_top + 32), (c - 152, 1640)], 7) + K.stick([(c + 150, desk_top + 30), (c + 152, 1640)], 7)
    return {"back": back, "mid": mid, "fg": "", "floor": 1640, "table_top": desk_top}


def living_room(t=0, night=False, **kw):
    back = wall_floor("#DCEDC8", "#D7B98E") + window(120, 300, 300, 380, night, sd=9) + frame_drawing(700, 360, sd=36) + lamp(820)
    seed(140)   # sofa
    back += spoly([(80, 1180), (1000, 1176), (1010, 1330), (70, 1334)], "#F48FB1", cross=True)
    seed(141)
    back += spoly([(60, 1320), (1020, 1316), (1020, 1470), (60, 1474)], "#EC407A", angle=-30)
    for i in range(3):
        seed(142 + i)
        back += K.heart(260 + i * 280, 1250, 20, "#FFFFFF", fill=False)
    back += K.stick([(100, 1474), (104, 1640)], 7) + K.stick([(980, 1470), (976, 1640)], 7)
    seed(150)   # rug
    back += f'<ellipse cx="540" cy="1760" rx="420" ry="90" fill="#FFF8EC"/>' + K.pencil('<ellipse cx="540" cy="1760" rx="420" ry="90"/>', "#FFE082", (120, 1670, 960, 1850), gap=8, tint=.3)
    return {"back": back, "mid": "", "fg": plant(1010, 1760, sd=160), "floor": 1640, "seat": 1320}


def park(t=0, **kw):
    s = K.paper(W, H, "#FFF8EC")
    seed(170)
    s += K.pencil(f'<rect x="0" y="0" width="{W}" height="1500"/>', "#BBDEFB", (0, 0, W, 1500), angle=-10, gap=14, tint=.18)
    s += f'<circle cx="860" cy="300" r="70" fill="#FFE082" stroke="{D.INK}" stroke-width="4" filter="url(#ink)"/>'
    for i in range(8):
        a = i * math.pi / 4
        s += K.ink(f"M{860 + 90 * math.cos(a):.0f} {300 + 90 * math.sin(a):.0f} L{860 + 120 * math.cos(a):.0f} {300 + 120 * math.sin(a):.0f}", 4, "#FBC02D")
    for i, (cx, cy) in enumerate([(220, 280), (520, 220)]):
        drift = (t * 8) % 60
        s += f'<g opacity=".9">' + K.ink(f"M{cx - 80 + drift} {cy} q20 -45 60 -30 q25 -40 70 -10 q45 -5 40 40 q-40 15 -170 0z", 4, D.INK, "#FFFFFF") + "</g>"
    seed(171)
    s += K.pencil('<path d="M0 1380 Q540 1320 1080 1400 L1080 1920 L0 1920Z"/>', "#AED581", (0, 1320, W, H), angle=-20, gap=9, tint=.3)
    s += K.ink("M0 1380 Q540 1320 1080 1400", 4, "#558B2F")
    seed(172)   # tree
    s += spoly([(90, 1420), (150, 1420), (140, 900), (100, 900)], "#A1887F", angle=85)
    for i in range(40):
        seed(180 + i)
        s += K.leaf(120 + K.R.uniform(-150, 150), 820 + K.R.uniform(-150, 110), K.R.uniform(20, 30), K.R.uniform(0, 360))
    s += K.bush(700, 1340, 300, 90, flowers=7)
    return {"back": s, "mid": "", "fg": "".join(K.tuft(x, 1880, 18) for x in range(40, 1080, 90)), "floor": 1700}


def store(t=0, counter_top=1180, **kw):
    back = wall_floor("#FFF3E0", "#CFD8DC")
    for row in range(3):   # shelves with jars and boxes
        y = 360 + row * 230
        back += K.ink(f"M60 {y + 150} L1020 {y + 146}", 6, "#8D6E63")
        for j in range(8):
            seed(200 + row * 8 + j)
            c = ["#EF9A9A", "#90CAF9", "#A5D6A7", "#FFE082", "#CE93D8", "#FFAB91", "#80CBC4", "#F48FB1"][(row * 3 + j) % 8]
            bx = 90 + j * 118
            back += spoly([(bx, y + 40), (bx + 80, y + 40), (bx + 80, y + 148), (bx, y + 148)], c, gap=5)
    seed(230)
    mid = spoly([(420, counter_top), (1080, counter_top), (1080, 1640), (430, 1640)], "#FFCC80", angle=-60)
    mid += K.ink(f"M410 {counter_top} L1080 {counter_top - 2}", 7)
    seed(231)
    mid += spoly([(840, counter_top - 110), (1000, counter_top - 110), (1000, counter_top), (840, counter_top)], "#90A4AE")   # register
    return {"back": back, "mid": mid, "fg": "", "floor": 1640, "table_top": counter_top}


def stage(t=0, **kw):
    back = K.paper(W, H, "#FFF8EC")
    seed(240)
    back += K.pencil(f'<rect x="0" y="0" width="{W}" height="1500"/>', "#7E57C2", (0, 0, W, 1500), angle=-80, gap=9, tint=.25)
    for side, pts in enumerate(([(0, 0), (220, 0), (180, 1500), (0, 1500)], [(860, 0), (1080, 0), (1080, 1500), (900, 1500)])):
        seed(241 + side)
        back += spoly(pts, "#E53935", angle=88)
    seed(243)
    back += spoly([(0, 1500), (1080, 1500), (1080, 1640), (0, 1640)], "#BCAAA4", angle=-4)
    back += '<ellipse cx="540" cy="1400" rx="360" ry="500" fill="url(#glow)"/>'
    for i in range(6):
        seed(250 + i)
        back += K.star(160 + i * 150, 140 + (i % 2) * 60, 18, "#FFD54F")
    return {"back": back, "mid": "", "fg": "", "floor": 1600}


def library(t=0, **kw):
    back = wall_floor("#FFF3C4", "#D7B98E")
    for col in range(4):
        seed(260 + col)
        x = 40 + col * 260
        back += spoly([(x, 300), (x + 220, 300), (x + 220, 1640), (x, 1640)], "#D7CCC8", angle=80)
        for row in range(5):
            for j in range(4):
                seed(300 + col * 20 + row * 4 + j)
                c = ["#EF9A9A", "#90CAF9", "#A5D6A7", "#FFE082", "#CE93D8"][(col + row + j) % 5]
                bx, by = x + 14 + j * 50, 330 + row * 250
                back += spoly([(bx, by), (bx + 40, by), (bx + 40, by + 200), (bx, by + 200)], c, gap=4, w=3)
    return {"back": back, "mid": table(160, 920, 1300, sd=270, color="#BCAAA4"), "fg": "", "floor": 1640, "table_top": 1300}


def hallway(t=0, **kw):
    back = wall_floor("#E3F2FD", "#CFD8DC")
    for i in range(4):
        seed(320 + i)
        x = 60 + i * 250
        back += spoly([(x, 520), (x + 200, 520), (x + 200, 1640), (x, 1640)], ["#90CAF9", "#EF9A9A", "#A5D6A7", "#FFE082"][i], angle=88, gap=6)
        back += K.ink(f"M{x + 60} {640} L{x + 140} {640} M{x + 60} {660} L{x + 140} {660}", 3)
        back += f'<circle cx="{x + 170}" cy="1080" r="8" fill="{D.INK}"/>'
    back += K.ink("M40 360 L1040 356", 5) + "".join(
        f'<text x="{80 + i * 180}" y="330" font-family="Architects Daughter" font-size="40" fill="#8E24AA">{w}</text>' for i, w in enumerate(["read", "count", "try", "share", "grow"]))
    return {"back": back, "mid": "", "fg": "", "floor": 1640}


SETS = {"kitchen": kitchen, "bedroom": bedroom, "classroom": classroom, "living_room": living_room, "park": park,
        "store": store, "stage": stage, "library": library, "hallway": hallway}


# ------------------------------------------------------------------ props
def plant(x, y, sd=80):
    seed(sd)
    s = spoly([(x - 50, y), (x + 80, y), (x + 65, y + 160), (x - 35, y + 160)], "#FFAB91", angle=-30)
    for i in range(9):
        seed(sd + 1 + i)
        s += K.leaf(x + 15 + K.R.uniform(-40, 40), y - 70 + K.R.uniform(-60, 50), K.R.uniform(22, 30), K.R.uniform(-150, -20))
    return s


def book(x=470, y=1240, word=None, glow=0.0, sd=74, color="#FFFDF8"):
    seed(sd)
    s = spoly([(x - 130, y + 10), (x - 2, y - 4), (x, y - 65), (x - 118, y - 58)], color, gap=10)
    seed(sd + 1)
    s += spoly([(x, y - 4), (x + 140, y + 10), (x + 128, y - 58), (x, y - 65)], color, gap=10)
    for i in range(4):
        yy = y - 48 + i * 11
        s += K.ink(f"M{x - 106 + i * 2} {yy + 2} L{x - 15} {yy - 2}", 2, "#9E9E9E")
        if not word or i != 2:
            s += K.ink(f"M{x + 14} {yy - 1} L{x + 118 - i * 2} {yy + 3}", 2, "#9E9E9E")
    if word:
        if glow > 0:
            s += f'<ellipse cx="{x + 56}" cy="{y - 27}" rx="40" ry="11" fill="#FFE082" opacity="{0.75 * glow:.2f}"/>'
        s += f'<text x="{x + 28}" y="{y - 21}" font-family="Architects Daughter" font-size="17" fill="#1f1b24" transform="rotate(3 {x + 28} {y - 21})">{word}</text>'
    return s


def worksheet(x, y, sd=76, lines=("3 + 4 = __", "5 + 2 = __")):
    seed(sd)
    s = spoly([(x - 90, y - 120), (x + 90, y - 124), (x + 96, y + 4), (x - 94, y + 8)], "#FFFFFF", gap=10)
    for i, ln in enumerate(lines):
        s += f'<text x="{x - 70}" y="{y - 80 + i * 36}" font-family="Architects Daughter" font-size="24" fill="#1f1b24">{ln}</text>'
    return s + K.star(x + 70, y - 100, 12)


def mug(x, y, sd=72):
    seed(sd)
    return (spoly([(x - 27, y - 68), (x + 28, y - 68), (x + 24, y), (x - 23, y)], "#81D4FA")
            + K.ink(f"M{x + 28} {y - 53} q24 4 20 24 q-4 18 -22 16", 4) + K.heart(x, y - 33, 8, "#E91E63", fill=False))


def pencil(x, y, sd=73):
    seed(sd)
    return (spoly([(x, y), (x + 95, y - 18), (x + 98, y - 10), (x + 3, y + 8)], "#FFD54F", gap=4, w=3)
            + spoly([(x + 95, y - 18), (x + 112, y - 16), (x + 98, y - 10)], "#FFCCBC", gap=3, w=3))


def coins(x, y, n=5):
    return "".join(f'<ellipse cx="{x + i * 26}" cy="{y - (i % 2) * 6}" rx="14" ry="9" fill="#FFD54F" stroke="{D.INK}" stroke-width="3" filter="url(#ink)"/>' for i in range(n))


def backpack(x, y, color="#EF5350", sd=77):
    seed(sd)
    return (spoly([(x - 70, y - 190), (x + 70, y - 190), (x + 80, y), (x - 80, y)], color)
            + K.ink(f"M{x - 40} {y - 190} Q{x} {y - 250} {x + 40} {y - 190}", 5) + K.ink(f"M{x - 50} {y - 90} L{x + 50} {y - 90} L{x + 45} {y - 20} L{x - 45} {y - 20} Z", 3))


def ball(x, y, r=38, color="#FF7043", sd=78):
    seed(sd)
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFF8EC"/>' + K.pencil(f'<circle cx="{x}" cy="{y}" r="{r}"/>', color, (x - r, y - r, x + r, y + r), gap=6, tint=.4)
            + K.ink(f"M{x + r} {y} A{r} {r} 0 1 1 {x + r - .5} {y - 3} M{x - r} {y} Q{x} {y - 20} {x + r} {y}", 4))


def lunchbox(x, y, color="#4DB6AC", sd=79):
    seed(sd)
    return spoly([(x - 70, y - 80), (x + 70, y - 80), (x + 70, y), (x - 70, y)], color) + K.ink(f"M{x - 25} {y - 80} Q{x} {y - 115} {x + 25} {y - 80}", 5)


def plate_cookies(x, y, n=4):
    s = f'<ellipse cx="{x}" cy="{y}" rx="80" ry="18" fill="#FFFFFF" stroke="{D.INK}" stroke-width="3.5" filter="url(#ink)"/>'
    return s + "".join(f'<circle cx="{x - 45 + i * 30}" cy="{y - 14 - (i % 2) * 8}" r="18" fill="#D7A86E" stroke="{D.INK}" stroke-width="3" filter="url(#ink)"/>' for i in range(n))


def jar(x, y, sd=81):
    seed(sd)
    return spoly([(x - 40, y - 110), (x + 40, y - 110), (x + 44, y), (x - 44, y)], "#E1F5FE", gap=9) + coins(x - 26, y - 20, 3)


def trophy(x, y, sd=82):
    seed(sd)
    return (spoly([(x - 45, y - 140), (x + 45, y - 140), (x + 20, y - 60), (x - 20, y - 60)], "#FFD54F")
            + spoly([(x - 12, y - 60), (x + 12, y - 60), (x + 30, y), (x - 30, y)], "#FFB300") + K.star(x, y - 105, 16, "#FFFFFF"))


PROPS = {"book": book, "worksheet": worksheet, "mug": mug, "pencil": pencil, "coins": coins, "backpack": backpack, "ball": ball,
         "lunchbox": lunchbox, "plate_cookies": plate_cookies, "jar": jar, "trophy": trophy, "plant": plant}
