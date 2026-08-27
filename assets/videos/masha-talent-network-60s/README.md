# MASHA Talent Network — video promocional de 60 s

Video vertical (9:16) que muestra la propuesta de valor de **MASHA Talent Network**:
te registras gratis, creas tu perfil una vez y la herramienta te trae ofertas
laborales en Canadá alineadas con tu perfil, listas para aplicar.

## Archivos

| Archivo | Uso |
|---|---|
| `masha-talent-network-60s.mp4` | **Versión principal** — 1080×1920, 30 fps, 60,0 s exactos, con cama musical suave |
| `masha-talent-network-60s-silent.mp4` | Misma imagen sin audio, para montar voz en off o música propia |
| `cover.jpg` | Frame de portada (miniatura) |
| `src/` | Fuente del video (HTML animado + script de render) |

Formato listo para Instagram Reels, TikTok, YouTube Shorts y Facebook Reels.

## Qué se ve en pantalla (shot list)

| Tiempo | Escena |
|---|---|
| 0:00–0:03.6 | Gancho de marca: «¿Buscas trabajo en Canadá? Deja que MASHA Talent lo busque por ti» |
| 0:03.6–0:09 | `talent.mashaincanada.com` — se escribe el correo y se pulsa **Crear mi perfil gratis** |
| 0:09–0:14 | Dashboard con perfil ya creado: 24 Recommended Jobs, 3 aplicaciones activas, perfil 100 % |
| 0:14–0:18.5 | Mi Perfil completo: datos, titular profesional, roles objetivo, skills y CV cargado |
| 0:18.5–0:21.5 | Se abre el menú y se entra a **Jobs → Recommended Jobs** |
| 0:21.5–0:33.6 | Listado de ofertas **en inglés** con % de match, ciudad, modalidad y salario; scroll y clic en la primera |
| 0:33.6–0:41 | Detalle de la oferta: rol, requisitos, salario y por qué coincide con el perfil |
| 0:41–0:46.6 | **Apply now** → aplica con CV y cover letter del perfil MIC → *Application submitted* |
| 0:46.6–0:52.2 | Herramientas MIC: los candados se abren → «Paquete de Optimización activo» |
| 0:52.2–0:56.2 | **MIC Partner Jobs — próximamente**: ofertas de empleadores en partnership con MIC |
| 0:56.2–1:00 | Cierre: «Crear tu perfil es GRATIS» + `talent.mashaincanada.com` |

## Guion de voz en off (español, ~150 palabras)

Grabar sobre `masha-talent-network-60s-silent.mp4`. Los tiempos son orientativos.

- **0:00** ¿Buscas trabajo en Canadá y sientes que aplicas a todo sin resultado? Deja que MASHA Talent lo busque por ti.
- **0:04** Entra a talent.mashaincanada.com y crea tu cuenta **gratis**. Sin tarjeta, sin costo.
- **0:09** Completas tu perfil una sola vez: tu experiencia, tus roles objetivo y tu CV.
- **0:19** Y desde ahí, en tu sección de Jobs ya tienes ofertas reales en Canadá alineadas con tu perfil: en inglés, con porcentaje de match, salario y ubicación.
- **0:32** Abres la que te interesa, ves la oferta completa y **aplicas ahí mismo** con tu perfil MIC.
- **0:47** Y con tu **Paquete de Optimización** desbloqueas todos los recursos: Método MIC, guías, plantillas y formación.
- **0:52** Muy pronto: ofertas de empleadores en partnership con MIC, para que apliques directamente a través de nosotros.
- **0:56** Crear tu perfil es gratis. Desbloquear todo su potencial, solo con el Paquete de Optimización. Te espero en talent.mashaincanada.com.

El video ya lleva subtítulos quemados en español, así que también funciona sin voz.

## Copy sugerido para el post

> Crear tu perfil en MASHA Talent Network es **gratis**. 🇨🇦
> Lo completas una vez y la herramienta te encuentra ofertas en Canadá que van con tu
> perfil, listas para aplicar — sin buscar en veinte portales distintos.
> Con el **Paquete de Optimización** desbloqueas Método MIC, guías, plantillas y formación.
> Y muy pronto: ofertas de empleadores en partnership con MIC para aplicar directamente
> a través de nosotros.
> 👉 talent.mashaincanada.com

## Nota importante

La interfaz del video es una **recreación** de `talent.mashaincanada.com`, hecha a partir
de la grabación de pantalla de la plataforma real (mismo header, menú, secciones y
estilo). El perfil de «María Fernanda Ríos» y las ofertas de trabajo son **ejemplos
ilustrativos**, no vacantes reales. Si prefieres cifras distintas (número de empleos,
salarios, rubro del perfil), están en `src/_04_script.html` (`JOBS`) y en
`src/_02_screens.html`.

## Cómo volver a generar el video

```bash
cd src
node render.js /ruta/frames full          # 1800 frames JPG 1080×1920
python3 music.py /ruta/music.wav          # cama musical de 60 s
ffmpeg -framerate 30 -i /ruta/frames/f_%05d.jpg -i /ruta/music.wav \
  -c:v libx264 -pix_fmt yuv420p -crf 19 -preset slow \
  -c:a aac -b:a 160k -shortest -movflags +faststart masha-talent-network-60s.mp4
```

`scene.html` se arma concatenando `_01_head.html`, `_02_screens.html`,
`_03_screens2.html` y `_04_script.html`. Toda la animación es determinista:
`window.__seek(t)` posiciona el video en el segundo `t`, y el render captura
un frame por cada 1/30 s. Abrir `scene.html` en el navegador y llamar
`__seek(25)` desde la consola permite revisar cualquier momento.
