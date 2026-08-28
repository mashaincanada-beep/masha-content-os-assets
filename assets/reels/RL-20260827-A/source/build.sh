#!/usr/bin/env bash
# Reconstruye RL-20260827-A a partir del video original.
# Uso: ./build.sh /ruta/al/IMG_2296.mov
set -euo pipefail
SRC="$1"
cd "$(dirname "$0")"

# 1. Fuentes (Poppins para el logo, Dancing Script para la letra manuscrita; ambas OFL)
fetch_font () {  # $1 = familia (con +), $2 = peso, $3 = nombre de archivo
  [ -f "$3-$2.ttf" ] || curl -sS -o "$3-$2.ttf" "$(curl -sS \
    "https://fonts.googleapis.com/css2?family=$1:wght@$2" | grep -o 'https://[^)]*\.ttf' | head -1)"
}
for w in 600 700 800 900; do fetch_font "Poppins" "$w" "Poppins"; done
for w in 600 700;         do fetch_font "Dancing+Script" "$w" "DancingScript"; done

# 2. Base normalizada: 1080x1920, 30 fps, 30 s, con un ligero realce de color
ffmpeg -y -i "$SRC" -t 30 -map 0:v:0 -map 0:a:0 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,eq=contrast=1.06:saturation=1.12:brightness=0.008,unsharp=5:5:0.35,fps=30" \
  -c:v libx264 -preset veryfast -crf 15 -pix_fmt yuv420p -c:a pcm_s16le -ar 48000 -ac 2 base.mov

# 3. 900 PNG transparentes con la animación (Chromium + Playwright)
python3 shoot.py ALL frames

# 4. Composición final
ffmpeg -y -i base.mov -framerate 30 -start_number 0 -i frames/f_%05d.png \
  -filter_complex "[1:v]format=rgba,setpts=N/30/TB[o];[0:v][o]overlay=0:0:eof_action=repeat[v];\
[0:a]afade=t=in:st=0:d=0.6,afade=t=out:st=25.6:d=1.5[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 21 \
  -maxrate 8M -bufsize 12M -pix_fmt yuv420p -g 60 -c:a aac -b:a 160k -ar 48000 \
  -movflags +faststart -shortest ../RL-20260827-A.mp4

ffmpeg -y -ss 9 -i ../RL-20260827-A.mp4 -frames:v 1 -q:v 2 ../cover.jpg
