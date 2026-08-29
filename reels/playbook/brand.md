# Estilo visual — Masha In Canada

La fuente de verdad de valores exactos es `../brandkit.json`. Este documento
explica el criterio; el JSON manda sobre los numeros.

## Color

| Rol | Hex |
|---|---|
| Azul | `#1C8FFF` |
| Verde | `#5FE223` |
| Rosa | `#FE007A` |
| Blanco | `#FFFFFF` |
| Tinta (fondos y texto oscuro) | `#0B1220` |

**Un solo acento manda por Reel.** El azul es el color por defecto de lo
informativo, el verde de lo que abre oportunidad, el rosa de lo que corrige un
error o marca urgencia. Los otros dos colores pueden aparecer en un detalle
minimo (un punto, un subrayado, un borde) pero nunca compitiendo. Tres acentos
al mismo peso convierten el Reel en un semaforo.

El blanco es para el texto sobre video. La tinta es para el texto sobre
tarjetas claras y para las capas de contraste.

## Tipografia

- Sans geometrica, peso bold o extrabold para hook y cifras; regular o medium
  para el cuerpo.
- Nada por debajo de **52 px** sobre lienzo de 1080x1920. Es el limite real de
  lectura en un telefono sostenido a un brazo.
- Maximo **3 lineas** por pantalla. Si no cabe, el mensaje esta mal escrito, no
  falta espacio.
- Alineacion a la izquierda por defecto. El centrado se reserva a la pantalla
  de dato dominante y al CTA.

## Movimiento

Todo Reel tiene movimiento continuo. Un fondo estatico pierde retencion en el
primer segundo. El movimiento viene del video de fondo, no de animaciones de
texto agresivas: el texto entra con un fade-up corto y se queda quieto para
poder leerse.

Cambio de pantalla cada 3-5 segundos. Mas rapido no se lee; mas lento se
abandona.

## Seleccion de imagen y video

Se busca material que se parezca a la vida real de la audiencia: oficinas
canadienses reales, gente trabajando, transporte, ciudad, pantallas con
aplicaciones abiertas, manos escribiendo.

Se descarta: apretones de manos corporativos, equipos multiculturales sonriendo
a camara, graficos de bolsa genericos, rascacielos de stock, cualquier cosa que
parezca banco de imagenes de banco.

## Firma

Discreta, esquina inferior izquierda, 70% de opacidad, maximo 260 px de ancho.
No aparece sobre la pantalla del hook: ahi solo va el gancho.

Mientras `signature.logoAssetId` sea `null` en `brandkit.json`, la firma es el
wordmark de texto `@mashaincanada`. Para pasar al logo real basta subirlo una
vez a Canva y anotar su `asset_id` en ese campo.

## Lo que nunca se hace

- Rellenar la pantalla de texto.
- Poner mas de un mensaje por pantalla.
- Usar la misma plantilla dos veces en menos de 5 dias.
- Diseñar algo que se parezca a una diapositiva de PowerPoint: fondo plano,
  titulo arriba, viñetas debajo.
- Dejar texto fuera de la safe area, donde la interfaz de Instagram lo tapa.
