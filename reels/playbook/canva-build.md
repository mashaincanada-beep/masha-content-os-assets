# Cómo se construye el diseño en Canva

Geometría exacta para cada plantilla, sobre lienzo **1080×1920**. Todo se monta
con operaciones de `edit-design`; no se delega la composición a la generación
automática de Canva.

## Por qué no se usa `generate-design` para componer

Se probó. Devuelve una sola página, reescribe la copia por su cuenta e inventa
llamadas a la acción. Para un Reel de 7 pantallas con cifras que deben ser
exactas, eso no sirve. `generate-design` se usa **solo** para obtener un lienzo
inicial; después se borran sus elementos y se compone a mano.

## Procedimiento

1. `generate-design` con `design_type: "your_story"` y una consulta breve
   (basta el hook). Quédate con un candidato.
2. `create-design-from-candidate` → `design_id`.
3. `read-design` con `open_transaction: true` → `transaction_id` y los
   `locator_id` de los elementos que trae. **Bórralos todos.**
4. Compón la página 1 (hook). Después `add_page` ×6 con
   `background_color: "#0B1220"`, `width: 1080`, `height: 1920`.
5. `read-design` con el `transaction_id` y `page_indices: [2,3,4,5,6,7]` para
   obtener los `page_id` nuevos (`page_metadata` no los ve: solo lee lo ya
   guardado).
6. Por cada página: una llamada con las formas y los textos, y **otra** con el
   formato. `add_text` no acepta formato, así que el texto nace a 16 px en
   negro y hay que darle estilo en una segunda pasada con `format_text` sobre
   los `locator_id` que devolvió la primera.
7. `edit-design` con `finalize: "commit"` y `operations: []`.
8. `get-export-formats` y luego `export-design` con
   `{"type":"mp4","quality":"horizontal_1080p"}`.

## Regla de las 3 líneas

A 64 px sobre una caja de 900 px entran unos **20 caracteres por línea**. Por
eso `bodyMaxChars` es 60: son exactamente 3 líneas. Si subes el cuerpo a 72 px
entran 17 por línea y 60 caracteres se van a 4 líneas, que chocan con la firma.
Comprueba siempre el `height` que devuelve el elemento de texto: si supera
`fontSize × lineHeight × 3`, hay una línea de más.

## Geometría por plantilla

Todas las páginas de cuerpo llevan la firma en `(90, 1450)`, 36 px, opacidad
0,7, en `tinta` sobre fondo claro o en `blanco` sobre fondo oscuro. La página
del hook no lleva firma.

### Página de hook (todas las plantillas)

| Elemento | Geometría | Formato |
|---|---|---|
| Marco de video | `(0,0,1080,1920)` relleno `#141C2B` | — |
| Marcador `[CLIP 1]` | `(90,520)` ancho 900 | 34 px, bold, acento, centrado |
| Capa de contraste | `(0,900,1080,1020)` relleno `#0B1220` | opacidad 0,8 |
| Hook | `(90,1150)` ancho 900 | 96 px, bold, `#FFFFFF`, interlineado 1,05 |

### T2-split · Split horizontal 60/40  *(por defecto)*

| Elemento | Geometría | Formato |
|---|---|---|
| Marco de video | `(0,0,1080,1000)` relleno `#141C2B` | — |
| Marcador `[CLIP n]` | `(90,420)` ancho 900 | 32 px, bold, acento, centrado |
| Bloque de acento | `(0,1000,1080,920)` relleno del acento | — |
| Kicker | `(90,1080)` ancho 900 | 52 px, bold, `#0B1220` |
| Cuerpo | `(90,1180)` ancho 900 | 64 px, bold, `#0B1220`, interlineado 1,15 |

### T1-fullbleed · Video a sangre

Marco `(0,0,1080,1920)`; degradado `(0,760,1080,1160)` en `#0B1220` al 0,75;
kicker `(90,1120)`; cuerpo `(90,1220)` en `#FFFFFF`. Sin bloque de color.

### T3-tarjetas · Tarjetas apiladas

Marco a sangre + velo `#0B1220` al 0,55. Tarjeta `(90,1000,900,420)` en
`#FFFFFF`, `corner_rounding: 32`. Barra de acento `(90,1000,14,420)`. Kicker
`(150,1050)`, cuerpo `(150,1140)` en `#0B1220`, ancho 780.

### T4-dato · Dato dominante

Marco a sangre al 0,35 de opacidad. Cifra `(90,780)` ancho 900, **300 px**,
bold, acento, centrada. Etiqueta `(90,1160)` ancho 900, 64 px, `#FFFFFF`,
centrada. Cuerpo `(90,1280)`, 56 px, `#FFFFFF`, centrado.

### T5-linea · Línea de tiempo

Marco `(0,0,1080,900)`. Línea vertical `(140,1000,8,420)` en el acento. Punto
activo: círculo de 36 px en `(126, 1000 + 100·(n-1))`. Kicker `(220,1000)`,
cuerpo `(220,1090)` ancho 770 en `#FFFFFF`.

### T6-contraste · Antes / después

Columna izquierda `(0,1000,540,920)` en `#141C2B`, derecha `(540,1000,540,920)`
en el acento. Texto izquierdo `(90,1120)` ancho 420 en `#FFFFFF` con
`strikethrough`; texto derecho `(600,1120)` ancho 420 en `#0B1220`. 56 px ambos.

### Página de cierre (todas las plantillas)

Fondo `#0B1220`. Barra de acento `(90,700,180,16)`. CTA `(90,790)` ancho 900,
88 px, bold, `#FFFFFF`, interlineado 1,1. Firma `(90,1420)` en `#FFFFFF`.

## Marcadores de clip

Cada página de cuerpo lleva un texto `[CLIP n] <descripción del video>.
Arrastra aquí un video vertical de Canva.` dentro del marco. Es la única
instrucción manual que queda: al soltar el clip encima, el marcador queda
tapado.

La descripción sale de `visuals.clips[n]` del `reel.json` y debe ser concreta
(qué se ve, no qué se siente). Nunca "gente profesional colaborando".
