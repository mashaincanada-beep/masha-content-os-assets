# VID-002 — Reel Salon de l'emploi (ecarrieres.com)

Montaje de reel a partir de dos clips fuente: un talking-head (selfie hablando
a cámara) y una grabación de pantalla navegando ecarrieres.com (Salon de
l'emploi et de la formation continue, Palais des congrès de Montréal). El
talking-head queda en pantalla completa todo el tiempo; la web aparece como
tarjetas flotantes que hacen "pop" sobre el video, con un cierre de marca MIC
— Masha In Canada.

- **Salida:** `reel_ecarrieres.mp4` — 1080×1920 (9:16), 30 fps, 1:19,27, H.264 + AAC.
- **Poster:** `poster.jpg`

## Estructura del montaje (v2)

| Tramo | Contenido |
|---|---|
| 0,0–9,0 s | Talking-head |
| 9,0–13,5 s | Talking-head + tarjeta flotante: hero de ecarrieres.com |
| 13,5–24,0 s | Talking-head |
| 24,0–28,5 s | Talking-head + tarjeta flotante: bloque "250 exposants" |
| 28,5–40,0 s | Talking-head |
| 40,0–44,5 s | Talking-head + tarjeta flotante: buscador / mockup de laptop |
| 44,5–56,0 s | Talking-head |
| 56,0–60,5 s | Talking-head + tarjeta flotante: sección "Les espaces" |
| 60,5–73,77 s | Talking-head: cierre / CTA |
| 73,77–79,27 s | Tarjeta final de marca (logo MIC + mashaincanada.com) |

El talking-head corre **sin ningún corte** de 0 a 73,77 s (ni de video ni de
audio) — la cámara nunca desaparece de pantalla. En los 4 momentos de arriba,
un recorte de la grabación de pantalla se anima como una tarjeta con esquinas
redondeadas, borde blanco y sombra, que "aparece" con un rebote elástico
(escala + opacidad, ligera inclinación orgánica que alterna por tarjeta) y
luego "desaparece" con la misma animación invertida — nada de cortes secos.
Cada tarjeta tiene además un ligero movimiento de respiración mientras está
en pantalla para que no se vea estática.

Además: gradación de color (contraste/saturación/nitidez, suavizado de piel
vía `hqdn3d`) sobre el talking-head, watermark del logo MIC en la esquina
inferior derecha (se retira antes de la tarjeta final).

## Audio

El audio del talking-head se conserva intacto de punta a punta. Se le suma
(todo sintetizado con numpy, sin pistas con derechos de autor):
- una cama ambiental suave de fondo,
- un sonido de **burbuja** (bubble-pop) al aparecer y al desaparecer cada
  tarjeta flotante — reemplaza al whoosh de la v1, que no encajaba con el
  tono del reel,
- un carillón suave al entrar la tarjeta final.

**Sin subtítulos** en esta versión — no hay forma de transcribir el audio de
forma confiable en este pipeline (sin acceso a un modelo de speech-to-text),
y la usuaria prefirió omitirlos antes que arriesgar subtítulos incorrectos.
Si se quiere agregarlos después, hace falta el texto exacto de la narración;
una vez se tenga, se puede quemar como una capa adicional sobre
`reel_ecarrieres.mp4` sin tener que rehacer el resto del montaje.

## Nota — edición de apariencia no realizada

También se pidió (en la v1) cambiar la camiseta por una blusa de oficina y
"peinar mejor" en el video. Esto **no se hizo**: este pipeline usa
únicamente `ffmpeg`/`PIL` (recortes, gradación de color, overlays, síntesis
de audio) y no cuenta con un modelo de generación/edición de imagen o video
con IA que permita reemplazar ropa o restilizar cabello de forma realista.
Lo que sí se aplicó es una corrección fotográfica general (contraste,
saturación, nitidez, suavizado de piel) para un acabado más profesional.

## Reproducir el montaje

```sh
pip install pillow numpy imageio-ffmpeg
python3 pipeline/1_base_and_cardsrc.py   # talking-head base + 4 secuencias de frames del b-roll
python3 pipeline/2_make_cards.py         # anima cada tarjeta flotante (pop in/out) con PIL
python3 pipeline/3_make_audio.py         # extrae narración y sintetiza ambiente/burbujas/carillón
python3 pipeline/4_finalize.py           # tarjeta final, composición, concat y mezcla de audio
```

Los scripts 1 y 3 referencian las rutas originales de los clips subidos
(`/root/.claude/uploads/...`); para volver a correr el pipeline con otro
material hay que actualizar `A`/`B` ahí. Los assets de marca reutilizables
(logo con fondo transparente y tarjeta final ya diseñada) están en
`pipeline/brand_assets/`.

## Nota técnica

El clip de grabación de pantalla trae metadata de duración de 52,96 s pero
el track de video en realidad deja de decodificar fotogramas nuevos hacia
los 26,4 s (el audio sí continúa completo) — probablemente el grabador de
pantalla de iOS se congeló a media grabación. Por eso las tarjetas solo usan
los primeros ~18 s de ese clip, con margen de seguridad.
