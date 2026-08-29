# VID-002 — Beneficios obligatorios en Canadá

Toma de cabeza parlante grabada en la oficina, montada con el
[estilo de reels](../estilo-reels/README.md).

- **Salida:** `beneficios_canada.mp4` — 1080×1920 (9:16), 30 fps, ~60,6 s.
- **Poster:** `poster.jpg`
- **Guion de subtítulos:** `guion.json` (38 grupos, transcritos del propio audio).

## Qué se le hizo

| Paso | Qué |
|---|---|
| Corte | `quitar_pausas.py` quitó 1,21 s de aire muerto en 8 tramos. La toma ya venía muy seguida: quedó en 60,60 s. |
| Encuadre | Ninguno. El original ya era 9:16 (864×1536), solo se escaló a 1080×1920. |
| Subtítulos quemados | El clip traía los subtítulos automáticos de Instagram entre el 73 % y el 83,5 % de la altura. Se tapan con una banda desenfocada (`--tapar 1330,590`, sigma 90) y encima van los nuevos. |
| Subtítulos nuevos | Los dos registros del estilo, paleta de marca. El bloque va al 70 % de la altura en vez de al 49 % para caer sobre la banda tapada. |
| Sonido | 10 efectos sintetizados: burbuja en los grupos con emoji, tecleo en los de color de alarma. Uno cada ~6 s. |
| Maquillaje | `--maquillaje`: piel suavizada al 55 %, brillo suave, algo menos de amarillo de los fluorescentes. Ojos y gafas quedan nítidos. |
| Voz | Normalizada de −24,3 LUFS a −14 LUFS, con limitador al final. |

## Reproducir el montaje

```sh
cd ../estilo-reels

# 1. quitar el aire muerto de la toma cruda
#    (umbral fijo a proposito: los tiempos del guion salen de este corte)
python3 pipeline/quitar_pausas.py CRUDO.mov beneficios_cortado.mp4 --umbral-db -32

# 2. cachear los emoji del guion (⚖️ 👓 💰 💆 👀 🇨🇦)
python3 pipeline/emoji_cache.py --de-guion ../VID-002-beneficios-canada/guion.json

# 3. montar
python3 pipeline/montar.py \
  --video beneficios_cortado.mp4 \
  --guion ../VID-002-beneficios-canada/guion.json \
  --salida ../VID-002-beneficios-canada/beneficios_canada.mp4 \
  --maquillaje --tapar 1330,590
```

## Notas para la próxima toma

- **Dura 60 s.** El estilo está calibrado para 15–25 s: el reel de referencia
  dura 18,9 s. Aquí hay material para tres reels — el del oftalmólogo y las
  gafas al 100 % es el que tiene gancho propio y se sostiene solo.
- **Empezar por el gancho.** Los primeros 8 s son preámbulo ("bueno les cuento
  también algo, una recomendación para los que estén trabajando aquí"). Si el
  reel arrancara en "el seguro de salud de mi empresa da 100 por 100 del valor
  de los anteojos", el primer segundo ya tendría la sorpresa dentro.
- **No dejar quemados los subtítulos automáticos.** Taparlos cuesta una banda
  desenfocada que se come el 30 % inferior del cuadro. Exportando el clip sin
  subtítulos, los nuevos irían al 49 % de la altura, sobre el pecho, que es
  donde los pone el estilo.
- **Micrófono.** Se grabó con auriculares y la voz entró a −24 LUFS; el
  normalizado la sube pero también sube el zumbido de la oficina. Grabar más
  cerca o con micro de solapa dejaría la voz más limpia.
