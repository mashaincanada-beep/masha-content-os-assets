# VID-002 · Salón del Empleo y la Formación Continua (Montreal, 14–15 oct 2026)

Reel en estilo MASHA · 1080x1920 · 30 fps · H.264 CRF 18 preset slow · AAC 192k · 79.3 s.

- `salon_empleo_montreal_1080x1920.mp4` — máster (fuente: reel hablado `reel_final_v3` + grabación de pantalla de ecarrieres.com).
- `build/overlay.html` — capa de marca determinista (`render(t)`: tarjetas, lower third, captions, mockups, momento wow).
- `build/capture.js` — captura frame a frame con Playwright/Chromium (1080x1920, dsf 1, espera `document.fonts.ready`).
- `build/compose.sh` — ensamblado ffmpeg (base + overlay PNG con alpha + mezcla de audio).
- `build/postqa.sh` — QA posterior: extracción exacta de frames con `-vsync 0` y medición EBU R128.
- `build/transcript_segments.json` — segmentación VAD + transcripción usada para los captions.

Audio: voz −16 LUFS, música (pista del reel de referencia, separada con Spleeter) −26 LUFS, fade-in 0.4 s, fade-out 1.9 s. Mezcla final −16.4 LUFS, pico −1.6 dBTP.
