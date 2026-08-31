import subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
UP = "/root/.claude/uploads/77e0ac3b-6a16-50fa-94dd-0b297bd4299b"
A = f"{UP}/a36acd05-642079489E5D40A88B62134611002467.mp4"
B = f"{UP}/760ab1c2-05628B18AFBC49449F796CBB9AE77BBD.mp4"
OUT = "/tmp/claude-0/-home-user-masha-content-os-assets/77e0ac3b-6a16-50fa-94dd-0b297bd4299b/scratchpad/work/segs"
os.makedirs(OUT, exist_ok=True)

FLASH = 0.08  # flash-cut duration, seconds

# NOTE: clip B's video track actually stops decoding ~26.4s despite container
# metadata claiming 52.96s (audio continues, video freezes) -- only use 0-19.2s.
# (idx, source, start, end, kind, flash_in, flash_out)
segments = [
    (0, A, 0.0,   9.0,   'A', False, True),
    (1, B, 0.0,   4.8,   'B', True,  True),
    (2, A, 13.8,  24.0,  'A', True,  True),
    (3, B, 4.8,   9.6,   'B', True,  True),
    (4, A, 28.8,  40.0,  'A', True,  True),
    (5, B, 9.6,   14.4,  'B', True,  True),
    (6, A, 44.8,  56.0,  'A', True,  True),
    (7, B, 14.4,  19.2,  'B', True,  True),
    (8, A, 60.8,  73.77, 'A', True,  False),
]

A_GRADE = ("eq=contrast=1.09:brightness=0.02:saturation=1.14:gamma=1.03,"
           "hqdn3d=2:1.5:4:3,unsharp=5:5:0.4:5:5:0.25,"
           "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rm=0.02:gm=0.0:bm=-0.02")

B_GRADE = "eq=contrast=1.06:saturation=1.10:brightness=0.01"

for idx, src, t0, t1, kind, fin, fout in segments:
    dur = round(t1 - t0, 3)
    out = f"{OUT}/seg_{idx:02d}.mp4"

    if kind == 'A':
        vf = f"scale=1080:1920,setsar=1,{A_GRADE},fps=30,format=yuv420p"
    else:
        # 1032x2236 source -> fit width 1080 (x1.04651) -> 1080x2340,
        # then zoom x1.06 -> 1145x2480, crop to 1080x1920 (skip top status bar)
        vf = (f"scale=1145:2480,setsar=1,crop=1080:1920:32:223,"
              f"{B_GRADE},fps=30,format=yuv420p")

    if fin:
        vf += f",fade=type=in:start_time=0:duration={FLASH}:color=white"
    if fout:
        vf += f",fade=type=out:start_time={round(dur-FLASH,3)}:duration={FLASH}:color=white"

    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y",
           "-ss", str(t0), "-to", str(t1), "-i", src,
           "-vf", vf, "-an", "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
           "-pix_fmt", "yuv420p", out]
    print("Rendering", out, dur, "s")
    subprocess.run(cmd, check=True)

print("done", len(segments), "segments")
