import os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")
CANVAS = (1080, 1920)
CARD_SIZE = (860, 1400)
RADIUS = 56
BORDER = 14

# per-card: (center_x, center_y, rotation_deg)
CARD_LAYOUT = [
    (540, 900, -4),
    (610, 950, 3),
    (470, 950, -3),
    (540, 900, 4),
]

def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=radius, fill=255)
    return m

def ease_out_back(t, overshoot=1.7):
    t = max(0.0, min(1.0, t))
    return 1 + (overshoot+1)*((t-1)**3) + overshoot*((t-1)**2)

def ease_in(t):
    return max(0.0, min(1.0, t))**2

def build_card(src_frame, rotation, opacity, scale):
    # 1. white border + rounded content -> card image
    bw, bh = CARD_SIZE[0]+BORDER*2, CARD_SIZE[1]+BORDER*2
    card = Image.new("RGBA", (bw, bh), (255, 255, 255, 255))
    mask_outer = rounded_mask((bw, bh), RADIUS+BORDER)
    card.putalpha(mask_outer)
    content = src_frame.convert("RGBA").resize(CARD_SIZE, Image.LANCZOS)
    content.putalpha(rounded_mask(CARD_SIZE, RADIUS))
    card.alpha_composite(content, (BORDER, BORDER))

    # 2. drop shadow
    shadow = Image.new("RGBA", (bw+80, bh+80), (0, 0, 0, 0))
    sm = rounded_mask((bw, bh), RADIUS+BORDER)
    shadow_layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 140))
    shadow_layer.putalpha(sm.point(lambda a: int(a*140/255)))
    shadow.alpha_composite(shadow_layer, (40, 55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))

    # 3. composite shadow + card
    combo = Image.new("RGBA", (bw+80, bh+80), (0, 0, 0, 0))
    combo.alpha_composite(shadow, (0, 0))
    combo.alpha_composite(card, (40, 40))

    # 4. scale + rotate
    if scale != 1.0:
        nw, nh = max(1, int(combo.width*scale)), max(1, int(combo.height*scale))
        combo = combo.resize((nw, nh), Image.LANCZOS)
    combo = combo.rotate(rotation, resample=Image.BICUBIC, expand=True)

    # 5. opacity
    if opacity < 1.0:
        a = combo.split()[3].point(lambda v: int(v*opacity))
        combo.putalpha(a)
    return combo

def render_card_sequence(idx, cx, cy, rotation):
    src_dir = f"{W}/cardsrc/{idx}"
    out_dir = f"{W}/cards/{idx}"
    os.makedirs(out_dir, exist_ok=True)
    frames = sorted(os.listdir(src_dir))
    n = len(frames)
    pop_in = 10
    pop_out = 10
    for i, fname in enumerate(frames):
        src = Image.open(f"{src_dir}/{fname}")
        if i < pop_in:
            t = i/(pop_in-1)
            scale = 0.55 + 0.5*ease_out_back(t)
            opacity = min(1.0, t*1.3)
        elif i >= n - pop_out:
            t = (n-1-i)/(pop_out-1)
            scale = 0.55 + 0.5*ease_out_back(t)
            opacity = min(1.0, t*1.3)
        else:
            # gentle continuous life: gentle scale breathing
            hold_t = (i - pop_in) / max(1, (n - pop_out - pop_in))
            scale = 1.0 + 0.015*np.sin(hold_t*np.pi*1.3)
            opacity = 1.0

        combo = build_card(src, rotation, opacity, scale)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        px = cx - combo.width//2
        py = cy - combo.height//2
        canvas.alpha_composite(combo, (px, py))
        canvas.save(f"{out_dir}/c_{i:04d}.png")
    print(f"card {idx}: {n} frames rendered")

for idx, (cx, cy, rot) in enumerate(CARD_LAYOUT, start=1):
    render_card_sequence(idx, cx, cy, rot)

print("all cards done")
