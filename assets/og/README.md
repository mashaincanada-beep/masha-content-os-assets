# Imágenes Open Graph (vista previa al compartir enlaces)

Imágenes de vista previa para cuando se comparten enlaces de `mashaincanada.com`
en Facebook, Instagram, WhatsApp, LinkedIn o X.

## Archivos

| Archivo | Página | Medidas | Peso |
|---|---|---|---|
| `paquete-de-optimizacion-og.jpg` | `https://mashaincanada.com/paquete-de-optimizacion/` | 1200 × 630 px | 86 KB |

La imagen se genera con `tools/make-og-image.py`, que toma la paleta y el logo MIC
directamente de los creativos reales del sistema de contenidos (`assets/CID-009/`),
para que la vista previa tenga exactamente la misma identidad visual que el resto
de las piezas de Masha in Canada.

## Metadatos que hay que publicar en la página

Estas son las etiquetas exactas que deben aparecer en el `<head>` de
`https://mashaincanada.com/paquete-de-optimizacion/`:

```html
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Masha in Canada" />
<meta property="og:locale" content="es_ES" />
<meta property="og:url" content="https://mashaincanada.com/paquete-de-optimizacion/" />
<meta property="og:title" content="Paquete de Optimización | Tu camino a una oferta laboral en Canadá" />
<meta property="og:description" content="Currículum, LinkedIn y estrategia de aplicación optimizados para el mercado canadiense. Destaca frente a empleadores y recruiters en Canadá con el acompañamiento de una Certified Résumé Strategist." />
<meta property="og:image" content="https://mashaincanada.com/wp-content/uploads/paquete-de-optimizacion-og.jpg" />
<meta property="og:image:secure_url" content="https://mashaincanada.com/wp-content/uploads/paquete-de-optimizacion-og.jpg" />
<meta property="og:image:type" content="image/jpeg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Paquete de Optimización de Masha in Canada: tu camino a una oferta laboral en Canadá empieza aquí." />

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Paquete de Optimización | Tu camino a una oferta laboral en Canadá" />
<meta name="twitter:description" content="Currículum, LinkedIn y estrategia de aplicación optimizados para el mercado canadiense." />
<meta name="twitter:image" content="https://mashaincanada.com/wp-content/uploads/paquete-de-optimizacion-og.jpg" />
```

La URL de `og:image` de arriba asume que el archivo se subió a la Biblioteca de
Medios de WordPress. Al subirlo, WordPress agrega el año y el mes a la ruta
(por ejemplo `/wp-content/uploads/2026/08/paquete-de-optimizacion-og.jpg`):
hay que usar la URL real que muestra la Biblioteca de Medios.

## Cómo publicarlos en WordPress

Ni WordPress ni Elementor generan etiquetas Open Graph por su cuenta: las produce
el plugin de SEO instalado. Por eso el cambio se hace en el plugin de SEO y **no
toca el diseño ni el contenido visible** de la página.

1. Subir `paquete-de-optimizacion-og.jpg` en **Medios → Añadir nuevo** y copiar la
   URL del archivo.
2. Editar la página *Paquete de Optimización* y abrir el panel del plugin de SEO
   (al final del editor de WordPress, no dentro del editor de Elementor —
   si la página abre directamente en Elementor, salir con
   **Menú de Elementor → Salir al escritorio**):
   - **Yoast SEO** → pestaña *Social* → *Facebook* → *Imagen*, *Título*, *Descripción*.
   - **Rank Math** → pestaña *Social* → *Facebook* → *Imagen de vista previa*, *Título*, *Descripción*.
   - **All in One SEO** → pestaña *Social Networks* → *Facebook*.
   - **SEOPress** → pestaña *Social* → *Open Graph*.
3. Pegar la URL de la imagen, el título y la descripción de la sección anterior y
   **Actualizar** la página.
4. Verificar en el [Sharing Debugger de Meta](https://developers.facebook.com/tools/debug/)
   con la URL de la página y pulsar **Scrape Again** para forzar el refresco de la
   caché de Facebook, Instagram y WhatsApp.

### Si el sitio no tiene plugin de SEO

Como alternativa, las etiquetas se pueden inyectar solo en esa página desde
**Elementor → Elementos personalizados / Custom Code** (Elementor Pro), con
ubicación `<head>` y la condición limitada a la página *Paquete de Optimización*,
pegando el bloque HTML de arriba. Si ya hay un plugin de SEO activo, no usar las
dos vías a la vez: se duplicarían las etiquetas y Meta tomaría la primera.

## Nota sobre cachés

WhatsApp, Facebook e Instagram guardan la vista previa en caché durante semanas.
Después de publicar los metadatos hay que pasar la URL por el Sharing Debugger de
Meta; recién ahí los enlaces nuevos muestran la imagen correcta. Los chats donde
el enlace ya se compartió antes pueden seguir mostrando la vista previa vieja.
