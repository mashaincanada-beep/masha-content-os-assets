# Childhood Stories - MIC Study v3 visual standard

**Status: ACTIVE (approved by Maria, 2026-09-28).** The permanent rules live in README.md section 2c; production commands and the screenplay format in section 3.

## Style (same art language as the daily Stories, Carousels and Reels)
- Built on the approved daily kit `engine/v3/kit2.py` (style reference "Mom-daughter dates", v3 layout), unchanged.
- Warm cream paper `#FFF8EC` with subtle grain and fibres; colored-pencil / crayon hatching; thin wobbly ink (~4-5 px).
- Childlike doodle people: big round heads, dot eyes with a small highlight, soft brows, red curved smile, soft blush,
  scribbled two-tone hair, stick arms and legs, clothes filled with pencil strokes and real details (knit rows, cuffs,
  buttons, heart prints, bows, sneakers with laces).
- Props and decorations in the same technique: books, pencils, mugs, hearts, stars, flowers, moon, framed kid drawings.
- The whole world is drawn: rooms, furniture and backgrounds use the same pencil and ink. Never place doodle characters
  in vector or realistic backgrounds.
- Avoid: flat vector, Canva/stock, corporate, 3D, glossy, photoreal, generic AI cartoon, perfect anatomy.

## Cinematic rule - "a child's drawing brought gently to life"
- Shots: wide, medium, close two-shot, inserts (hands, pencil, the page), reaction shots; cuts between them.
- Camera: slow push-ins and pans (`camera_group`), subtle parallax (background ~0.9, foreground ~1.12).
- Hand-drawn boil: the ink wobble is re-drawn every 3 frames ("on threes"); geometry stays stable (per-element seeds),
  so it reads as a living drawing, not flicker.
- Acting: blinks, eye direction, worried or relaxed brows, a smile that grows slowly, talking mouths while a line is
  spoken, walking, sitting, pointing, page and hand movement, small environment motion (steam, floating hearts).
- Keep emotion subtle: looking down, a pause, a parent sitting beside, a small smile. No exaggerated faces.
- Solid shapes sit on an opaque paper base (`spoly`, face underlay), so pencil hatching never lets objects show through.

## Character continuity
Recurring characters keep their face design, hair colour and style, clothing palette, relative age and approved
voice. Clothing may change by scene; the illustration language never does. Define each recurring character once
as a draw function (e.g. `child_ava`, `mom_elena`) and reuse it.

## Text
- Minimal on-screen text; any text inside the art is handwritten (Architects Daughter / Gochi Hand).
- Subtitles stay highly readable: Nunito 800, ~50 px, dark ink on a cream rounded card with a thin ink border,
  inside the Reels safe area (around y 1500 on 1080x1920).
- No big corporate title cards inside emotional scenes. MIC Study appears only on the end card and the cover.

## Cover
A hand-drawn miniature movie poster in v3: the main character(s) at the key emotional moment, a short handwritten
title, warm cream paper, pencil texture, small official MIC Study logo. Never an educational infographic.

## Brand unity
Daily content = simpler, faster, educational. Childhood Stories = cinematic, emotional, more detailed.
Same art language, different storytelling depth.
