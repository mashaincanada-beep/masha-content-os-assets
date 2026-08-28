# Análisis del reel de referencia

Medidas sacadas del reel que mandaste (grabación de pantalla de un reel de
`@brock11johnson`, "How to beat the Instagram algorithm"). Todo lo que hay aquí
está medido sobre el archivo, no es apreciación: son los números que usa
`preset.json`.

## Ficha del archivo

| Dato | Valor |
|---|---|
| Duración real del reel | 18,88 s (el contenedor dice 37,58 s porque la grabación va a 120 fps) |
| Grabación de pantalla | 1032×2236, 59,67 fps, H.264 |
| Audio | AAC 44,1 kHz estéreo |
| Sonoridad integrada | **−14,0 LUFS** |
| Rango de sonoridad (LRA) | **4,0 LU** — comprimido fuerte, nivel casi plano |
| Pico real | +0,3 dBFS (va pegado al techo) |
| Silencio total dentro del reel | **0,38 s** en 18,9 s (dos huecos de 0,18 s y 0,19 s) |
| Música de fondo | ninguna: en las pausas el nivel cae a −43,8 dB |

## Montaje

- **4 cortes** en 18,9 s (en 1,08 / 4,19 / 8,77 / 12,54 s), o sea uno cada 4,5 s.
- Son **cortes secos sobre el mismo encuadre**: cámara fija, mismo tamaño de
  plano, solo salta la pose. Comparando los fotogramas de antes y después de
  cada corte no hay reencuadre ni zoom.
- **Cero transiciones, cero zooms, cero b-roll, cero efectos de sonido.**
- Los cortes no están ahí por narrativa: están donde se quitó una pausa. Por eso
  quedan solo 0,38 s de silencio en todo el reel.

## Subtítulos

Dos líneas fijas, siempre en el mismo sitio, y **cambian de golpe: no hay
animación de entrada**. Lo comprobé fotograma a fotograma a 120 fps alrededor de
un cambio de grupo — de un fotograma al siguiente ya está el texto nuevo
completo, sin escalado ni fundido.

| Medida | Valor |
|---|---|
| Grupos de subtítulo | 18 en 18,88 s |
| Duración media de un grupo | **1,05 s** (rango 0,87–2,53 s) |
| Palabras por grupo | 4,4 de media (2 a 7) |
| Ritmo de habla | ~250 palabras por minuto |
| Centro vertical del bloque | 49,4 % de la altura del cuadro (fijo, no se mueve nunca) |
| Alto de mayúscula, línea de golpe | ~4,6 % de la altura del cuadro |
| Proporción entre líneas | la de golpe es ~1,35× la de apoyo |
| Ancho máximo ocupado | ~80 % del ancho del cuadro |

### Los dos registros

- **Línea 1 (apoyo)**: grotesca ancha en negrita, caja mixta, blanca, con
  **una sola palabra en cursiva** por grupo (*if the*, *also*, *never*, *same*,
  *a lot*, *ever*). La cursiva es el acento rítmico de la frase.
- **Línea 2 (golpe)**: condensada pesada, TODO EN MAYÚSCULAS, de color. Es la
  palabra que la gente se lleva del reel.
- **Excepción**: cuando la frase es puro puente y no tiene palabra de golpe
  ("You can think / about it like this"), las dos líneas van en la condensada al
  cuerpo pequeño y el color se pasa a la primera línea.

La tipografía original no es libre; los equivalentes gratuitos que usa el
pipeline y que dan el mismo aire son **Anton** para el golpe y **Roboto Bold /
Bold Italic** para el apoyo.

### Colores muestreados

| Uso | Color medido |
|---|---|
| Apoyo | `#FFFFFF` |
| Concepto clave / buena noticia | `#86F442` (verde ácido) |
| El problema | `#E8100C` (rojo) |
| Remate / apuesta | `#F3D914` (amarillo) |

El color no es decorativo, tiene significado fijo en todo el reel: verde para lo
que va bien ("MORE FAIR", "MORE COMPETITIVE", "IS TRUE"), rojo para el problema
("BAD NEWS", "MORE TRAFFIC", "LESS VIEWS"), amarillo para el remate
("EVERYONE", "RACE CAR", "BEFORE").

Todo el texto lleva **contorno negro grueso** (~0,8 % del ancho del cuadro) más
una sombra suave debajo. Por eso se lee igual sobre la cara, sobre el micrófono
o sobre el fondo claro.

### Emoji

Uno por grupo como máximo, en unos 8 de los 18 grupos, en línea con el texto
(casi siempre al principio o al final de la línea de apoyo) y a la altura de la
mayúscula. Funcionan como viñeta, no como decoración: ⚠️ con el problema, 🤖 con
el algoritmo, 🏎️ con la analogía del coche, 👀 con la caída de views.

## Guion (transcripción)

> Because if the **algorithm**… ⚠️ **bad news**… 🤖 The Instagram **algorithm**
> has never been **more fair** — how is that **bad news**? 👼 Because if the
> algorithm is fair to **everyone** ☑️ then it's also 🏃 "**more competitive**".
> You can think about it like this: we are now all "**racing**" in the same
> **race car** 🏎️. But that also **means** 🚦 there's a lot **more traffic** out
> on the **track**. So while it 📱 is true that the **average reel** 👀 is getting
> **less views** than ever **before**…

Estructura: **gancho a media frase** (empieza con "Because", sin presentación),
reencuadre de la mala noticia como buena, **una analogía concreta** (la carrera
de coches) y corte antes de cerrar, para que el bucle reenganche.

## Encuadre y luz

Plano medio corto, sujeto centrado, ojos en el tercio superior, micrófono de
brazo dentro de cuadro (a propósito: dice "esto es un podcast"), estanterías con
objetos detrás para dar profundidad y personalidad. Luz cálida práctica, sin
gradación de color agresiva. El bloque de subtítulos cae justo debajo de la
barbilla, en el pecho, que es donde no tapa nada.
