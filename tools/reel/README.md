# Reel builder — RL-20260828-A

Genera un reel vertical 1080x1920 a partir de un clip horizontal, con
rotulos animados, el logo MIC transformandose en una mariposa azul, y una
banda sonora sintetizada (pad ambiental + celesta + olas).

## Piezas

| Archivo | Que hace |
| --- | --- |
| `gen_audio.py` | Escribe el WAV estereo: pad D–A–Bm–G, motivo de celesta y olas de lago con rompiente lenta. |
| `butterfly.py` | Dibuja la mariposa vectorial en los azules de marca, con parametro de aleteo. |
| `gen_overlay.py` | Emite la capa RGBA 1080x1920 cruda (frases, logo, metamorfosis y vuelo). |

## Uso

```sh
# 1. banda sonora
python3 gen_audio.py track.wav

# 2. video base: fondo desenfocado + tarjeta cuadrada con esquinas redondeadas
python3 - <<'PY'
from PIL import Image, ImageDraw
m = Image.new("L", (1004, 1004), 0)
ImageDraw.Draw(m).rounded_rectangle([0, 0, 1003, 1003], 40, fill=255)
m.save("mask.png")
PY

ffmpeg -i ORIGEN.mp4 -i mask.png -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,\
gblur=sigma=34,eq=brightness=-0.09:saturation=0.72,setsar=1[bg];\
[0:v]crop=864:864:(iw-864)/2:0,scale=1004:1004,setsar=1[fg];\
[1:v]format=gray,setsar=1[mk];[fg][mk]alphamerge[fga];\
[bg][fga]overlay=38:356[v]" -map "[v]" -an \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 base.mp4

# 3. montaje final (la capa animada entra por tuberia)
python3 gen_overlay.py - | ffmpeg \
  -i base.mp4 \
  -f rawvideo -pixel_format rgba -video_size 1080x1920 -framerate 30 -i - \
  -i track.wav -i ORIGEN.mp4 \
  -filter_complex "[0:v]format=rgba[b];[b][1:v]overlay=0:0:format=rgb:shortest=1[vo];\
[3:a]highpass=f=170,volume=3.2,afade=t=in:st=0:d=1.8,afade=t=out:st=29.4:d=2.0[amb];\
[2:a][amb]amix=inputs=2:duration=first:weights=1 0.42:normalize=0[am];\
[am]loudnorm=I=-14:TP=-1.5:LRA=11[ao]" \
  -map "[vo]" -map "[ao]" -c:v libx264 -profile:v high -preset slow -crf 20 \
  -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -movflags +faststart -shortest reel.mp4
```

`gen_overlay.py` acepta `PREVIEW_TIMES="3.9,24.6"` para volcar solo esos
instantes como PNG y revisar la animacion sin renderizar los 942 fotogramas.

## Ajustes habituales

- Frases y tiempos de entrada/salida: constante `LINES` en `gen_overlay.py`.
- Metamorfosis: `T_SPLIT`, `T_MORPH`, `T_BORN`, `T_EXIT`.
- Vuelo: `WPTS` (curva) y `KEY_T` / `KEY_S` (ritmo sobre la curva).
- Dependencias: `numpy`, `pillow`, `scipy`, `ffmpeg`, y las fuentes
  Montserrat y Playfair Display en `fonts/`.
