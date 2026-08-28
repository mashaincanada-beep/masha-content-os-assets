# RL-20260827-A — "La vida en Canadá" (camping)

Reel / Story vertical sobre el video de camping (IMG_2296.mov). El texto se
escribe a mano, en cursiva, como una nota personal.

| | |
|---|---|
| Archivo | `RL-20260827-A.mp4` |
| Formato | 1080 × 1920 (9:16), 30 fps, 30 s |
| Audio | ambiente original, con fade in (0.6 s) y fade out al cierre |
| Portada | `cover.jpg` (frame 3.8 s) |
| Tipografías | Dancing Script (texto manuscrito) · Poppins (logo y handle) |

## Guion en pantalla

| Empieza a escribirse | Sale | Texto |
|---|---|---|
| 0.70 s | 5.30 s | No todo son **papeles** *(magenta)* / y aplicaciones. |
| 5.55 s | 10.90 s | A veces es un fin / de semana entre árboles, / una fogata y cero señal. |
| 11.15 s | 15.90 s | Al principio cuesta. / Y está bien que cueste. |
| 16.15 s | 20.80 s | Dejas de sobrevivir / y empiezas a **vivir aquí**. *(verde)* |
| 21.05 s | 25.90 s | Si estás empezando, / escríbeme. Yo también / empecé desde cero. |
| 25.95 s | 30 s | Cierre: logo MIC + "Tips reales para construir tu vida en Canadá" + @mashaincanada |

## Animación

- Cada línea se **escribe** de izquierda a derecha (máscara `clip-path` a
  velocidad constante), con un punto de tinta que avanza en la punta del trazo.
- Ritmo: 0.049 s por carácter, 0.16 s de pausa entre líneas; cada bloque sale
  con fade + desplazamiento hacia arriba antes de que entre el siguiente.
- Cada nota va ligeramente inclinada (±1°) para que no se vea alineada a regla.
- Cierre: panel crema con círculos pastel, logo con pop de escala, hoja de
  maple con giro, y frase + handle que suben en secuencia.
- Marca de agua MIC arriba a la izquierda durante todo el video.

## Colores de marca usados

`#238FFE` azul · `#5FE127` verde · `#FE0178` magenta · `#F2EBDD` crema · `#1B1338` tinta

## Cómo regenerarlo

```bash
source/build.sh /ruta/al/IMG_2296.mov
```

Requiere `ffmpeg`, `python3`, `playwright` y Chromium. El texto, los tiempos y
la velocidad de escritura se editan en `source/overlay.html`
(array `CARDS`, constantes `SPEED`, `GAP` y `OUTRO_START`).
