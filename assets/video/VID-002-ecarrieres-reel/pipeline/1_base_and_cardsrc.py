"""Renders the continuous talking-head base layer plus the 4 cropped/graded
B-roll source frame sequences later animated into floating cards.
Uploaded source clips referenced by absolute path -- update A/B to re-run
against different source material."""
import subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
UP = "/root/.claude/uploads/77e0ac3b-6a16-50fa-94dd-0b297bd4299b"
A = f"{UP}/a36acd05-642079489E5D40A88B62134611002467.mp4"   # talking-head
B = f"{UP}/760ab1c2-05628B18AFBC49449F796CBB9AE77BBD.mp4"   # ecarrieres.com screen recording
W = os.path.join(os.path.dirname(__file__), "work")

A_GRADE = ("eq=contrast=1.09:brightness=0.02:saturation=1.14:gamma=1.03,"
           "hqdn3d=2:1.5:4:3,unsharp=5:5:0.4:5:5:0.25,"
           "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rm=0.02:gm=0.0:bm=-0.02")
B_GRADE = "eq=contrast=1.06:saturation=1.10:brightness=0.01"

NARR_DUR = 73.77

os.makedirs(f"{W}/base", exist_ok=True)

# --- 1. Base talking-head layer: full continuous clip, graded, gentle in/out fade ---
vf_base = (f"scale=1080:1920,setsar=1,{A_GRADE},fps=30,format=yuv420p,"
           f"fade=type=in:start_time=0:duration=0.25:color=white,"
           f"fade=type=out:start_time={NARR_DUR-0.3}:duration=0.3:color=white")
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-i", A, "-t", str(NARR_DUR), "-vf", vf_base, "-an",
                "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p", f"{W}/base/base_talkinghead.mp4"], check=True)
print("base rendered")

# --- 2. Four B-roll content slices, cropped/graded to card interior size 860x1400 ---
# NOTE: this screen recording's container metadata claims 52.96s but its video
# track actually stops decoding new frames ~26.4s (audio keeps going) -- likely
# an iOS screen-recorder stall. Only use 0-19.2s of B, well inside that limit.
# 1032x2236 source -> scale width 860 (x0.8333) -> 860x1863; skip status bar (~167px) -> crop 860x1400
card_windows = [(0.0, 4.5), (4.5, 9.0), (9.0, 13.5), (13.5, 18.0)]
vf_card = f"scale=860:1863,setsar=1,crop=860:1400:0:167,{B_GRADE},fps=30,format=rgba"

for i, (t0, t1) in enumerate(card_windows, start=1):
    outdir = f"{W}/cardsrc/{i}"
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", str(t0), "-to", str(t1), "-i", B,
                    "-vf", vf_card, "-an", "-r", "30",
                    f"{outdir}/f_%04d.png"], check=True)
    n = len(os.listdir(outdir))
    print(f"card {i} source frames:", n)

print("done")
