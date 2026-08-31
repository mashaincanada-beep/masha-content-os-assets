import subprocess, os

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
WORK = "/tmp/claude-0/-home-user-masha-content-os-assets/77e0ac3b-6a16-50fa-94dd-0b297bd4299b/scratchpad/work"
SEGS = f"{WORK}/segs"
FLASH = 0.08

# 1. Render end card as a 5.5s video clip with a fade-in from white and fade-out at tail
end_dur = 5.5
end_vf = (f"fade=type=in:start_time=0:duration=0.28:color=white,"
          f"fade=type=out:start_time={round(end_dur-0.35,3)}:duration=0.35:color=black")
endcard_mp4 = f"{SEGS}/seg_09.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-i", f"{WORK}/end_card.png",
                "-t", str(end_dur), "-vf", f"scale=1080:1920,setsar=1,{end_vf},format=yuv420p",
                "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p", endcard_mp4], check=True)
print("endcard rendered")

# 2. Concat all 12 segments (stream copy, same codec params)
list_path = f"{WORK}/concat_list.txt"
with open(list_path, "w") as f:
    for i in range(10):
        f.write(f"file '{SEGS}/seg_{i:02d}.mp4'\n")

silent_full = f"{WORK}/silent_full.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", list_path,
                "-c", "copy", silent_full], check=True)
print("concatenated silent video")

# 3. Overlay watermark logo (bottom-right, hidden during end card) + mux final audio
narr_dur = 73.77
wm_enable = f"lt(t,{narr_dur-0.15})"
vf = (f"[0:v][1:v]overlay=W-w-40:H-h-70:enable='{wm_enable}':format=auto[v]")

out_final = f"{WORK}/reel_mashaincanada_final.mp4"
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y",
                "-i", silent_full,
                "-i", f"{WORK}/watermark_logo.png",
                "-i", f"{WORK}/final_audio.wav",
                "-filter_complex", vf,
                "-map", "[v]", "-map", "2:a",
                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "192k", "-shortest",
                out_final], check=True)
print("FINAL:", out_final)
