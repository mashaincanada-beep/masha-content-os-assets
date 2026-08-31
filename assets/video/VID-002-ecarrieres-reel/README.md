# VID-002 — Reel Salon de l'emploi (ecarrieres.com)

Montaje de reel a partir de dos clips fuente: un talking-head (selfie hablando
a cámara) y una grabación de pantalla navegando ecarrieres.com (Salon de
l'emploi et de la formation continue, Palais des congrès de Montréal). Se
intercalan cortes a la web mientras continúa el audio de la narración, y se
cierra con una tarjeta de marca MIC — Masha In Canada.

- **Salida:** `reel_ecarrieres.mp4` — 1080×1920 (9:16), 30 fps, 1:19,27, H.264 + AAC.
- **Poster:** `poster.jpg`

## Estructura del montaje

| Tramo | Contenido |
|---|---|
| 0,0–9,0 s | Talking-head: gancho inicial |
| 9,0–13,8 s | B-roll: hero de ecarrieres.com (fecha/lugar del evento) |
| 13,8–24,0 s | Talking-head |
| 24,0–28,8 s | B-roll: bloque "250 exposants" |
| 28,8–40,0 s | Talking-head |
| 40,0–44,8 s | B-roll: buscador / mockup de laptop |
| 44,8–56,0 s | Talking-head |
| 56,0–60,8 s | B-roll: sección "Les espaces" |
| 60,8–73,77 s | Talking-head: cierre / CTA |
| 73,77–79,27 s | Tarjeta final de marca (logo MIC + mashaincanada.com) |

El audio del talking-head corre sin cortes de 0 a 73,77 s (es la columna
vertebral del reel); el video alterna entre la cámara y la grabación de
pantalla, con "flash cuts" (fundido a blanco de 0,08 s, sin insertar
fotogramas) en cada corte para no desincronizar audio/labios.

Además: gradación de color (contraste/saturación/nitidez, suavizado de piel
vía `hqdn3d`), watermark del logo MIC en la esquina inferior derecha durante
el talking-head y el b-roll (se retira antes de la tarjeta final), zoom fijo
sutil sobre la grabación de pantalla para que no se vea estática.

El audio original del talking-head se conserva intacto; se le suma una cama
ambiental sintetizada (pad suave), whooshes sintetizados en cada corte y un
carillón suave al entrar la tarjeta final — todo generado con numpy, sin
pistas con derechos de autor.

## Nota importante — edición de apariencia no realizada

Se pidió además cambiar la camiseta por una blusa de oficina y "peinar
mejor" en el video. Esto **no se hizo**: este pipeline usa únicamente
`ffmpeg`/`PIL` (recortes, gradación de color, overlays, síntesis de audio) y
no cuenta con un modelo de generación/edición de imagen o video con IA que
permita reemplazar ropa o restilizar cabello de forma realista. Lo que sí se
aplicó es una corrección fotográfica general (contraste, saturación,
nitidez, suavizado de piel) para un acabado más profesional. Para lograr el
cambio de vestuario/peinado, la opción más confiable sigue siendo regrabar
esa toma ya vestida así, o pasar el clip por una herramienta de edición de
imagen con IA fuera de este pipeline.

## Reproducir el montaje

```sh
pip install pillow numpy imageio-ffmpeg
python3 pipeline/1_make_segments.py   # recorta y gradúa los 9 segmentos (talking-head + b-roll)
python3 pipeline/2_make_audio.py      # extrae narración y sintetiza ambiente/whooshes/carillón
python3 pipeline/3_finalize.py        # tarjeta final, concat, watermark y mezcla de audio
```

Los scripts referencian las rutas originales de los clips subidos
(`/root/.claude/uploads/...`); para volver a correr el pipeline con otro
material hay que actualizar `A`/`B` en `pipeline/1_make_segments.py` y
`pipeline/2_make_audio.py`, y la ruta de origen del logo en
`pipeline/end_card_preview.png` (recortado de `assets/CID-001/01.png`) si se
regenera la tarjeta final.

## Nota técnica

El clip de grabación de pantalla trae metadata de duración de 52,96 s pero
el track de video en realidad deja de decodificar fotogramas nuevos hacia
los 26,4 s (el audio sí continúa completo) — probablemente el grabador de
pantalla de iOS se congeló a media grabación. Por eso el b-roll solo usa los
primeros ~19 s de ese clip, con margen de seguridad.
