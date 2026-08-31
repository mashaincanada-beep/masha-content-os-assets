"""Renders the branded end card, composites the base talking-head layer with
the 4 animated floating cards + logo watermark, concatenates the end card,
and muxes in the synthesized audio track."""
import subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "work")
BRAND = os.path.join(HERE, "brand_assets")

card_windows = [(9.0, 13.5), (24.0, 28.5), (40.0, 44.5), (56.0, 60.5)]
narr_dur = 73.77

# 1. end card video
end_dur = 5.5
end_vf = (f"fade=type=in:start_time=0:duration=0.28:color=white,"
          f"fade=type=out:start_time={round(end_dur-0.35,3)}:duration=0.35:color=black")
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-i", f"{BRAND}/end_card.png",
                "-t", str(end_dur), "-vf", f"scale=1080:1920,setsar=1,{end_vf},format=yuv420p",
                "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p", f"{W}/base/endcard.mp4"], check=True)
print("endcard rendered")

# 2. Composite base + 4 animated card overlays + watermark
inputs = ["-i", f"{W}/base/base_talkinghead.mp4"]
for i in range(1, 5):
    t0, _ = card_windows[i-1]
    inputs += ["-itsoffset", str(t0), "-framerate", "30", "-i", f"{W}/cards/{i}/c_%04d.png"]
inputs += ["-i", f"{BRAND}/watermark_logo.png"]
# input indices: 0=base, 1..4=cards, 5=watermark

filt = "[0:v][1:v]overlay=0:0:shortest=0[v1];"
filt += "[v1][2:v]overlay=0:0:shortest=0[v2];"
filt += "[v2][3:v]overlay=0:0:shortest=0[v3];"
filt += "[v3][4:v]overlay=0:0:shortest=0[v4];"
filt += f"[v4][5:v]overlay=W-w-40:H-h-70:enable='lt(t,{narr_dur-0.15})':format=auto[vout]"

composited = f"{W}/base/composited_talkinghead.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                *inputs,
                "-filter_complex", filt, "-map", "[vout]",
                "-t", str(narr_dur),
                "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p", composited], check=True)
print("composited talking-head + cards done")

# 3. concat composited talking-head clip with end card
list_path = f"{W}/concat_list.txt"
with open(list_path, "w") as f:
    f.write(f"file '{composited}'\n")
    f.write(f"file '{W}/base/endcard.mp4'\n")
silent_full = f"{W}/silent_full.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", list_path,
                "-c", "copy", silent_full], check=True)
print("concatenated")

# 4. mux final audio, bitrate-capped for a social-media-friendly file size
out_final = os.path.join(HERE, "..", "reel_ecarrieres.mp4")
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-i", silent_full, "-i", f"{W}/final_audio.wav",
                "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "slow", "-b:v", "2200k", "-maxrate", "2400k", "-bufsize", "4400k",
                "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", "-shortest",
                out_final], check=True)
print("FINAL:", out_final)
