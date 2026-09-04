# Paquete de Optimización Profesional — animated Story (15 s)

| File | Use |
| --- | --- |
| `story.mp4` | **Upload this to Instagram Stories.** 1080x1920, 15.0 s, 30 fps, H.264 High / yuv420p, no audio (add music in the Instagram composer if wanted). |
| `poster.jpg` | Final frame, for thumbnails and the approval page. |
| `contact.jpg` | Twelve frames across the 15 s, for a one-glance review of the timing. |
| `story.html` | The animation as a self-contained page. Open it in any browser and it plays on a loop. |
| `source.png` | The flat design it was built from, normalised to 1080x1920. |

## Timing

| Time | What happens |
| --- | --- |
| 0.0–0.9 s | The design fades in from paper, settling from a slight zoom. |
| 0.35–1.3 s | "Masha in Canada" drops in, its rule draws. |
| 1.0–2.4 s | PAQUETE DE / OPTIMIZACIÓN / PROFESIONAL rise in one line at a time. |
| 2.25–2.75 s | The green rule draws. |
| 2.5–3.55 s | The four-line promise rises in, line by line. |
| 3.6–5.0 s | CV, LinkedIn, Cover Letter, Recursos pop in, with the dividers growing between them. |
| 4.9–6.0 s | The "Conoce el paquete" card slides in from the left; its link icon pops, then the arrow arrives. |
| 5.9–6.7 s | The heart pops and the closing note rises in. Everything is now on screen. |
| 6.6–15 s | Hold: the arrow nudges toward "link de mi bio" every 1.6 s, the heart beats every 2.2 s, the card pulses at 7.4 / 11.4 / 14.0 s, the link icon wiggles at 8.0 and 12.2 s, one light sweep crosses OPTIMIZACIÓN at 8.6 s, and the whole frame zooms in very slowly throughout. |

Built with `tools/story_animation/animate_story.py` in `masha-content-os-publisher`
from the single flattened design image — the design was cut back into layers, then
animated; no element was redrawn.
