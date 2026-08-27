# RL-20260827-A — "La vida en Canadá" (camping)

Reel / Story vertical hecho sobre el video de camping (IMG_2296.mov).

| | |
|---|---|
| Archivo | `RL-20260827-A.mp4` |
| Formato | 1080 × 1920 (9:16), 30 fps, 30 s |
| Audio | ambiente original, con fade in (0.6 s) y fade out al cierre |
| Portada | `cover.jpg` (frame 9 s) |

## Guion en pantalla

| Tiempo | Etiqueta | Texto |
|---|---|---|
| 0.6 – 5.9 s | LA VIDA EN CANADÁ | No todo son **papeles** y aplicaciones. |
| 6.1 – 11.4 s | LO QUE NADIE POSTEA | A veces es un fin de semana entre árboles, una fogata y cero señal. |
| 11.6 – 16.9 s | LOS PRIMEROS MESES | Al principio cuesta. Y está bien que cueste. |
| 17.1 – 22.4 s | Y UN DÍA | Dejas de sobrevivir y empiezas a **vivir aquí**. |
| 22.6 – 25.9 s | — | Si estás empezando, escríbeme. Yo también empecé desde cero. |
| 25.9 – 30 s | Cierre | Logo MIC + "Tips reales para construir tu vida en Canadá" + @mashaincanada |

## Animación

- Entrada de texto palabra por palabra (fade + subida, escalonada 55 ms).
- Píldora de categoría con rebote suave y barra de color que crece de arriba a abajo.
- Salida de cada bloque con fade + desplazamiento hacia arriba.
- Cierre: panel crema de marca con círculos pastel, logo con pop de escala,
  hoja de maple con giro, y línea + handle que suben en secuencia.
- Marca de agua MIC arriba a la izquierda durante todo el video.

## Colores de marca usados

`#238FFE` azul · `#5FE127` verde · `#FE0178` magenta · `#F2EBDD` crema · `#1B1338` tinta

## Cómo regenerarlo

```bash
source/build.sh /ruta/al/IMG_2296.mov
```

Requiere `ffmpeg`, `python3`, `playwright` y Chromium. El texto y los tiempos
se editan en `source/overlay.html` (array `CARDS` y `OUTRO_START`).
