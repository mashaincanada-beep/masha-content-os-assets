# VID-001 — Oficina orbital AURORA-7

Montaje VFX sobre un recorrido de interior grabado en iPhone: el piso se
reinterpreta como el modulo de oficina de una estacion espacial.

- **Salida:** `oficina_espacial.mp4` — 1080×1920 (9:16), 30 fps, 9,17 s, H.264 + AAC.
- **Poster:** `poster.jpg`

## Que se anade

| Momento | Efecto |
|---|---|
| 0,0–1,2 s | Arranque de sistemas: pantalla de carga, barras de interferencia y fallo de senal |
| 1,3–3,3 s | Reticula de analisis y fijado de objetivo sobre el entorno |
| 3,3–8,2 s | Ventanal exterior: campo de estrellas y limbo del planeta en orbita baja |
| Todo el clip | HUD (telemetria O2/gravedad/temperatura/presion, regla de eje Z, onda de escaneo), motas en gravedad cero, drones flotantes, barrido de escaneo |
| 8,3–9,2 s | Tarjeta final AURORA-7 |

Ademas: graduacion frio-teal, bloom, aberracion cromatica (con picos de glitch
sincronizados en 0,98 / 3,34 / 6,06 s), vineteado, lineas de barrido y grano.

El audio original venia practicamente en silencio (−65 dBFS RMS), asi que la
banda sonora se sintetiza entera: zumbido de motores, aire de soporte vital,
pitidos de interfaz, impactos graves y eco de modulo metalico.

## Reproducir el montaje

```sh
pip install pillow numpy imageio-ffmpeg
python3 pipeline/gen_overlays.py   # capas hud/ y glow/ (275 fotogramas) + scanlines.png
python3 pipeline/gen_audio.py      # ambience.wav
sh      pipeline/render.sh         # composicion y codificacion finales
```

`render.sh` espera la ruta del clip original en `SRC`.

## Nota tecnica

`unsharp` y `gblur` no aceptan RGB planar, asi que ffmpeg intercala una
conversion a YUV; si un `blend=all_mode=screen` cae despues, la mezcla se aplica
sobre los planos de croma y tine toda la imagen de magenta. Por eso la cadena
fuerza `format=gbrp` explicito en cada entrada de `blend`.

El material de origen es HLG/BT.2020 de 10 bits: la salida se reetiqueta a
BT.709 para que los reproductores no la interpreten como HDR.
