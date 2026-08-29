# Estilo de reels — corte seco + subtítulos de dos registros

Esta carpeta define cómo se editan los reels de cabeza parlante de la cuenta y
trae las herramientas para aplicarlo. Sale de medir el reel de referencia que
mandaste; los números exactos están en [`referencia.md`](referencia.md) y
codificados en [`preset.json`](preset.json).

El estilo se aguanta sobre seis reglas. Si se copian esas seis, el reel ya se ve
como el de referencia aunque cambie el tema, la cara y el idioma.

## Las seis reglas

1. **Cámara fija, plano medio corto, un solo encuadre.** No hay zooms, no hay
   segundo ángulo, no hay b-roll. Lo único que cambia es lo que dices.
2. **Cero aire muerto.** Se corta cada pausa, cada "eeeh", cada respiración
   larga. En el reel de referencia quedan 0,38 s de silencio en 18,9 s. Los
   cortes son secos, sin transición, sobre el mismo encuadre: se notan y da
   igual, es parte del ritmo.
3. **Subtítulos de dos líneas, siempre en el mismo sitio.** Centro del bloque al
   49,4 % de la altura, a la altura del pecho. El bloque nunca se mueve entre
   grupos.
4. **Un grupo de subtítulo por segundo.** 4 o 5 palabras. En el reel de
   referencia cambian de golpe, sin animación; el pipeline les pone un rebote de
   entrada de 0,2 s que se quita con `--sin-animacion`.
5. **Dos registros tipográficos con trabajos distintos.** Línea de apoyo en
   grotesca ancha blanca (con *una* palabra en cursiva); línea de golpe en
   condensada pesada, mayúsculas, de color.
6. **El color significa algo y no cambia de significado dentro del reel.**
   En la paleta de marca: amarillo = concepto clave, rosa = el problema,
   blanco = apoyo.

Y lo que el reel de referencia **no** lleva, que es tan importante como lo
anterior: sin música de fondo, sin efectos de sonido, sin transiciones, sin
animación de texto, sin stickers, sin marca de agua, sin intro. El pipeline sí
trae sonidos, rebote de entrada y golpe en los cortes, porque se pidieron
aparte; están todos apagables y documentados en
[Efectos y transiciones](#efectos-y-transiciones).

## Rodaje

- Vertical 9:16, 1080×1920 mínimo, 30 fps.
- Plano medio corto: ojos en el tercio superior, hombros dentro de cuadro. El
  pecho tiene que quedar libre porque ahí van los subtítulos.
- Fondo con profundidad y objetos tuyos (estantería, plantas, cuadros). No pared
  lisa.
- Micrófono dentro de cuadro si lo tienes: en este formato suma, no resta.
- Luz principal cálida delante, algo de contraluz detrás. Sin filtros ni
  gradaciones raras.
- Graba del tirón y equivócate tranquila: las pausas y los tropiezos se cortan
  después.

## Guion hablado

- Empieza **a media frase**, sin presentarte. El reel de referencia arranca con
  "Because…".
- ~250 palabras por minuto. Rápido, sin arrastrar.
- Una idea por segundo, una analogía concreta en el medio, y **corta antes de
  cerrar del todo** para que el bucle reenganche.
- 15–25 s. El de referencia dura 18,9 s.

## Montaje

```sh
# 1. quitar el aire muerto (deja los cortes secos)
python3 pipeline/quitar_pausas.py crudo.mp4 cortado.mp4

# 2. escribir el guion de subtítulos contra cortado.mp4 (formato más abajo)

# 3. cachear los emoji que uses (una vez por emoji nuevo)
python3 pipeline/emoji_cache.py --de-guion guion.json

# 4. montar: encuadre 9:16 + subtítulos quemados + voz normalizada
python3 pipeline/montar.py --video cortado.mp4 --guion guion.json --salida reel.mp4
```

Extras de `montar.py`, todos opcionales:

| Opción | Para qué |
|---|---|
| `--maquillaje` | retoque leve de piel y luz |
| `--tapar 1330,590` | tapa una banda del clip original (subtítulos ya quemados, marcas de agua) con un desenfoque degradado; `y0,alto` en píxeles del lienzo final |
| `--centro-subs 0.70` | sube o baja el bloque de subtítulos |
| `--cortes 2.35,7.17` | golpe de zoom, destello y whoosh en cada corte seco |
| `--sin-animacion` | subtítulos que cambian de golpe, sin rebote de entrada |
| `--sin-sfx` | monta sin los efectos de sonido |
| `--paleta viral` | usa la paleta del reel de referencia |
| `--crf 22` | comprime más el archivo final (por defecto 19) |
| `--sin-audio-norm` | deja el audio sin normalizar |

Antes de la primera vez:

```sh
sh fuentes/descargar.sh                       # Anton, Roboto y Noto Color Emoji
pip install pillow imageio-ffmpeg             # imprescindible
pip install fonttools uharfbuzz cairosvg      # solo para rasterizar emoji nuevos
```

`quitar_pausas.py` imprime la equivalencia de tiempos entre la toma cruda y el
clip cortado, que es lo que necesitas para poner los `in`/`out` del guion.

## El sistema de subtítulos

| | Línea de apoyo (`l1`) | Línea de golpe (`l2`) |
|---|---|---|
| Qué hace | prepara la frase | la palabra que se llevan |
| Tipografía | Roboto Bold / Bold Italic | Anton |
| Caja | mixta | MAYÚSCULAS |
| Cuerpo a 1080×1920 | 92 px | 120 px |
| Color | blanco casi siempre | el de la idea |
| Cursiva | una palabra por grupo, marcada `*así*` | nunca |

- Interlineado 140 px, bloque centrado horizontalmente, ancho máximo 86 % del
  cuadro (si no cabe, el grupo entero encoge; no se parte en tres líneas).
- Contorno negro de 9 px **más** sombra suave debajo. Es lo que hace que el
  texto se lea sobre la cara y sobre el fondo claro sin caja de color.
- **Excepción `neutro`**: frases puente sin palabra de golpe. Las dos líneas van
  en Anton a 96 px, caja mixta, y el color se pasa a la primera línea.

### Colores

La paleta activa es `mic`, que traslada el kit de carruseles a vídeo (los tonos
van más saturados que en los PNG porque sobre imagen en movimiento el amarillo
crema y el rosa suave desaparecen):

| Nombre | Hex | Cuándo |
|---|---|---|
| `blanco` | `#FFFFFF` | línea de apoyo, y remates neutros |
| `amarillo` | `#F5D33F` | el concepto clave, lo que hay que recordar |
| `rosa` | `#FF4F97` | el problema, el error, lo que se pierde |
| `verde` | `#86F442` | opcional, para "esto sí funciona" |

En `preset.json` está también la paleta `viral`, que es literalmente la del reel
de referencia (verde ácido / rojo / amarillo). Se activa con
`--paleta viral` o con `"paleta": "viral"` en el guion. Sirve para probar, pero
la de marca es la que hace que el reel se reconozca como tuyo.

### Emoji

Uno por grupo como máximo y solo cuando aporta: ⚠️ para el aviso, 👀 para
"mira esto", 🇨🇦 para Canadá. Van en línea dentro del texto, a la altura de la
mayúscula, casi siempre al principio de la línea de apoyo. Si el emoji no está
cacheado el subtítulo se dibuja sin él y el render avisa; no rompe nada.

## Efectos y transiciones

Nada de esto está en el reel de referencia, que es voz sola y cortes secos sin
adorno. Se añadió después, por encargo, y todo se puede quitar con un flag.

### Efectos de sonido

Se sintetizan en `pipeline/sfx.py` — nada de librerías ni licencias:

- `bubble` — burbuja corta, un barrido ascendente de 85 ms.
- `typing` — cuatro clics de tecleo secos, 250 ms en total.
- `whoosh` — barrido de aire de 340 ms para los cortes.

Los dos primeros se colocan al empezar un grupo de subtítulo, no en cada cambio:
con uno cada 5 o 6 segundos se notan; en cada línea cansan. La regla por defecto,
que se puede pisar poniendo `"sfx": "bubble" | "typing" | "no"` en cualquier
grupo del guion:

- burbuja si el grupo lleva emoji,
- tecleo si la línea de golpe va en el color de alarma (`rosa` o `rojo`),
- nada en el resto.

El whoosh va solo, uno por corte seco, y arranca 0,12 s antes del corte para
taparlo.

Los picos están en `sfx` dentro de `preset.json` y salen a unos **−13 dBFS**,
mezclados debajo de la voz normalizada y con un limitador al final. La primera
versión iba a −18 y quedaba tapada por la voz: por debajo de −16 no se oyen.

### Animación de entrada del subtítulo

El grupo entra con un rebote de tres fotogramas: 1,16× → 1,05× → 0,985× → 1×,
dos fotogramas cada uno (0,2 s en total). Escala desde el centro del bloque, no
desde el del cuadro. Es lo que hace que la burbuja tenga sentido: el sonido cae
justo en el fotograma grande.

Está en `animacion` dentro de `preset.json` y se quita con `--sin-animacion`,
que devuelve el cambio seco del reel de referencia.

### Transición en los cortes

En cada corte seco: un empujón de zoom del 9 % que se desinfla en 0,3 s, un
destello corto y el whoosh. Los segundos de corte los imprime
`quitar_pausas.py`; se le pasan a `montar.py` con `--cortes 2.35,7.17,…`. Sin
esa lista no hay transiciones. Está en `transicion` dentro de `preset.json`.

## Maquillaje

`--maquillaje` es un retoque leve, no un filtro de belleza: desenfoque bilateral
que empareja la piel pero respeta los bordes (ojos, gafas y pelo se quedan
nítidos), un punto de glow, algo de brillo y una corrección parcial del amarillo
de la luz. Todo está en `maquillaje` dentro de `preset.json`; `suavizado` es el
mando principal (0,55 = leve, 0,75 ya se nota).

Se aplica a todo el cuadro, sin máscara de piel: se probó una y en una oficina
de paredes beis marcaba las paredes como piel. Como el fondo de estos reels ya
va desenfocado, suavizarlo no se ve.

## Audio

- Voz sola. **Sin música de fondo**: en el reel de referencia el nivel cae a
  −43,8 dB en las pausas, no hay cama.
- Comprimida fuerte y plana: −14,0 LUFS integrados con un rango de 4 LU.
  `montar.py` lo aplica con `loudnorm=I=-14:TP=-1:LRA=5`.
- Si grabas con el micro del móvil, acércate: el estilo no perdona una voz
  lejana porque no hay música que la disimule.

## Exportación

1080×1920, 30 fps, H.264 high, CRF 19, AAC 192 kbps, BT.709, `+faststart`.
Todo eso ya lo pone `montar.py`.

## Formato del guion

Ver [`guion.ejemplo.json`](guion.ejemplo.json), que es el que monta la demo.

```json
{
  "paleta": "mic",
  "grupos": [
    {
      "in": 0.00, "out": 1.00,
      "l1": { "texto": "⚠️ Si aplicas *sin* esto" },
      "l2": { "texto": "te van a rechazar", "color": "rosa" }
    }
  ]
}
```

- `in` / `out` en segundos contra el clip cortado.
- `l1` / `l2`: si falta una, el grupo va a una sola línea (y `l2` sigue yendo en
  la condensada aunque quede sola).
- `estilo` opcional: `apoyo`, `golpe` o `neutro`.
- `color` opcional: un nombre de la paleta activa. Por defecto `blanco`.
- `sfx` opcional: `bubble`, `typing` o `no`. Si no se pone, manda la regla de
  arriba.
- `*asteriscos*` para la cursiva. El texto de `l2` se pasa a mayúsculas solo.

A nivel de guion, además de `paleta` y `lienzo`, se puede poner `centro_subs`
para mover el bloque en ese reel concreto.

## Demo

[`demo/demo-estilo.mp4`](demo/demo-estilo.mp4) monta `guion.ejemplo.json` sobre
un clip que ya estaba en el repo (el de VID-001). El vídeo de fondo no tiene
nada que ver con el texto: está solo para ver el sistema de subtítulos
funcionando sobre imagen real, con la posición, los cuerpos y los colores
definitivos. Se montó con `--sin-audio-norm` porque ese clip lleva una banda
sintética, no una voz.

## Antes de publicar

- [ ] ¿Hay algún silencio de más de 0,3 s? Fuera.
- [ ] ¿El primer segundo ya dice algo, sin presentación?
- [ ] ¿Cada grupo de subtítulo dura ~1 s y tiene 4 o 5 palabras?
- [ ] ¿La línea de golpe se entiende sola, sin la de apoyo?
- [ ] ¿Los colores siguen significando lo mismo del principio al final?
- [ ] ¿Un emoji por grupo como mucho, y ninguno decorativo?
- [ ] ¿Se lee todo con el móvil a un brazo de distancia y sin sonido?
- [ ] ¿El texto queda por encima de la interfaz de Instagram (nada por debajo
      del 78 % de la altura)?
