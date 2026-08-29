# Reel diario — Masha In Canada

Un Reel vertical al día, en español, sobre el mercado laboral canadiense. El
sistema investiga primero, decide el tema después y construye el diseño en
Canva, sin repetir tema, hook, plantilla ni CTA.

La pregunta que el sistema se hace cada mañana, antes de nada:

> ¿Qué información sería especialmente útil o interesante **hoy** para una
> persona hispanohablante que quiere conseguir mejores oportunidades laborales
> en Canadá?

## El flujo de cada día

```
1. plan-reel.mjs        ──▶  qué está permitido hoy
                             (categoría, plantilla, familia de hook, CTA, cupo promocional)
2. investigación web    ──▶  el hallazgo del día, con fuente enlazable
3. guion + caption      ──▶  reels/RE-AAAA-MM-DD/reel.json
4. verify-reel.mjs      ──▶  puerta: límites de texto, fuentes, repeticiones
5. Canva                ──▶  diseño 9:16 de 7 páginas + export MP4
6. record-reel.mjs      ──▶  el ledger recuerda, para que mañana no se repita
7. commit + push
```

## Por qué hay un ledger

El modelo que escribe el Reel de mañana no recuerda el de hoy. Si la variedad
dependiera de su criterio, en dos semanas estaría publicando el mismo Reel con
otras palabras.

Por eso la rotación no es un consejo, es un cálculo. `state/ledger.json` guarda
lo que se publicó y `tools/ledger.mjs` decide qué está en enfriamiento:

| Elemento | No se repite hasta |
|---|---|
| Categoría (17 en total) | 8 días |
| Plantilla visual (6 en total) | 5 días |
| Familia de hook (10 en total) | 4 días |
| CTA | 3 días (el de DM, 2) |
| Oferta MIC | 6 días |
| Hook literal | 60 días |
| Primera línea del caption | 30 días |
| Tema (solape de palabras clave > 40%) | 21 días |

Además: máximo **2 Reels promocionales cada 7 días**. El resto es valor puro.

`verify-reel.mjs` aplica todo esto y falla con código 1 si algo se repite, si
un texto se pasa de largo o si un Reel noticioso no trae fuente enlazable. Un
Reel que no pasa esa puerta no se registra ni se publica.

## Ficheros

```
reels/
  brandkit.json            colores, tipografía, zona segura, límites, firma
  ROUTINE.md               el prompt exacto que ejecuta la Routine diaria
  playbook/
    topics.json            17 categorías + reglas de enfriamiento y cupo promocional
    hooks.json             10 familias, 50 patrones de gancho
    templates.json         6 layouts distintos, con su dirección para Canva
    ctas.json              4 CTA y cuándo usar cada uno
    offers.json            ofertas MIC y a qué temas se enganchan de forma natural
    brand.md               criterio visual: color, tipografía, movimiento, qué nunca hacer
    captions.md            estructura del caption y bolsas de hashtags
    sources.md             qué fuentes se revisan y en qué orden
  state/ledger.json        historial (lo escribe record-reel.mjs)
  tools/
    ledger.mjs             reglas de rotación y validación
    plan-reel.mjs          imprime el plan del día
    verify-reel.mjs        valida un reel.json
    record-reel.mjs        lo registra en el historial
    ledger.test.mjs        pruebas de que las reglas muerden
  RE-AAAA-MM-DD/           un Reel: reel.json, script.md, caption.md, sources.md
```

## Uso manual

```sh
node reels/tools/plan-reel.mjs                          # el plan de hoy
node reels/tools/plan-reel.mjs --category=salarios      # forzar categoría (avisa si está en enfriamiento)
node reels/tools/verify-reel.mjs reels/RE-2026-08-29/reel.json
node reels/tools/record-reel.mjs reels/RE-2026-08-29/reel.json
node --test reels/tools/ledger.test.mjs                 # 9 pruebas de las reglas
```

Node 18+. Sin dependencias.

## Qué es automático y qué no

**Automático:** investigación, elección del tema, guion, caption, hashtags,
composición del diseño 9:16 de 7 páginas en Canva con los colores, tamaños y
zona segura de la marca, export a MP4, y el registro en el ledger.

**Manual (dos minutos):**

1. **Los clips de video.** El conector de Canva no expone la búsqueda de su
   biblioteca de stock, así que el sistema no puede elegir los clips por ti.
   Cada página trae en la zona superior un marcador `[CLIP n]` con la
   descripción exacta del video que le corresponde: abre el diseño, arrastra
   encima el clip y listo. El marcador queda tapado.
2. **Añadir el conector de Canva a la Routine, una sola vez.** La Routine se
   creó sin él (la API no permitía transferirlo desde esta sesión). Ábrela en
   las Routines de claude.ai y añade **Canva**. Hasta entonces la Routine
   entrega guion y caption, pero no el diseño.
3. **Publicar en Instagram.** No hay conector de Instagram en la cuenta, así
   que la publicación no se puede automatizar desde aquí. El MP4 y el caption
   quedan listos para subir.

Para pasar del wordmark de texto al logo real: súbelo una vez a Canva, copia su
`asset_id` (empieza por `M`) y ponlo en `signature.logoAssetId` de
`brandkit.json`. A partir de ese día el Reel lo inserta solo.
