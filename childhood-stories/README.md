# MIC Study - Childhood Stories

A weekly **2-minute emotional animated short film** for MIC Study (Instagram @hellomicstudy + Facebook Page "MIC Study"),
produced and published automatically **every Wednesday** by the scheduled task
"MIC Study Childhood Stories - Wednesday short film".

Nobody gives a weekly prompt. Each run invents the story, writes it, renders it, checks it, publishes it and logs it.

---

## 1. The creative standard

The benchmark is **"THE ROLE WITH NO LINES"**: a child gets a part with no speaking lines because reading aloud is hard,
practises, gains confidence and finally volunteers to read. Never recreate that plot. Match its *quality*.

The one idea behind every film:

> Academic practice is not only about grades. Math and Reading skills shape how children participate, communicate,
> understand the world, solve problems, help others and experience childhood.

What the parent should feel at the end: *"The little things my child practises today can show up in parts of their life I wasn't even thinking about."*

Order of experience: **STORY -> EMOTION -> RECOGNITION -> MESSAGE -> (only then) MIC STUDY.**

The test, every week: **"Would this still be a beautiful childhood story if the MIC Study logo disappeared?"** If not, rewrite it.

Hard rules
- Never guilt parents. Never imply a child who struggles is worth less. Never promise outcomes.
- What changes is confidence, participation, independence, understanding, willingness to try, expression, everyday problem solving - never the child's value.
- No product pitch inside the story. A MIC Study-style printable may appear naturally in a practice scene (`p_worksheet`). No features, prices, bundles or checkout, ever. No "BUY NOW".
- Visuals: MIC Study v3 handmade doodle style only (section 2c). No photos, no realistic people, no flat vector.
- All text written for Maria or the audience uses normal hyphens (-), never em or en dashes.

## 2. Story engine (do this before writing any screenplay)

1. Read `MIC-STUDY-STORY-REGISTRY.csv` (every past film) and the last 14 days of the "MIC Study Content Publishing Log" sheet.
2. Draft **3 concepts** internally. For each fill in: main child, age (Grades 1-9), setting, relationship
   (mother / father / sibling / friend / teacher / classmate / coach / grandparent), childhood situation, Math or Reading skill,
   initial emotional tension, small turning point, meaningful payoff, parent-facing message, final emotional line.
3. Score each 1-5 on: emotional connection, originality vs the registry, natural Math/Reading relevance, parent relatability,
   visual storytelling potential. Pick the highest total. Do not ask anyone.
4. Rotation rules (check against the registry):
   - Alternate Math and Reading over time (target 50/50; never 3 of the same in a row).
   - Rotate story worlds: school life, family life, friendship, extracurricular, everyday independence. **Not school two weeks in a row.**
   - Do not repeat a situation, emotional conflict, opening, ending, payoff type, or the same main relationship as the last 3 films.
   - Rotate the main child and family (recurring cast in `engine/cast.json`: the Riveras, the Okafors, the Chens, Noor, Jonah, Ava, Kai, Ms. Patel, Coach Ben, Grandma Rosa). Add new characters with `extra_cast` when useful. Children must span Grades 1-9 over time.
   - The seed examples (Lemonade Stand, Bedtime Story, Team Score, Birthday Invitation, Recipe, New Child) are illustrations of the idea, not a queue.

### Six-act structure (about 2:00 total)
| Act | What happens | Music mood |
|---|---|---|
| 1 Childhood moment | something the child genuinely cares about | `curious` / `playful` |
| 2 Small difficulty | reading or math becomes relevant | `curious` -> `uncertain` |
| 3 Emotional moment | hesitation, frustration, embarrassment, uncertainty, disappointment, confusion - subtle | `uncertain` / `reflective`, use silence |
| 4 Practice / discovery | small practice, trying again, asking, learning from a mistake - no magic transformation | `reflective` -> `hopeful` |
| 5 Payoff | the skill shows up again in real life: participation, confidence, independence, helping someone, joining, understanding, responsibility, speaking up, solving a real problem (rarely a grade) | `hopeful` -> `warm` |
| 6 Parent message | narrator connects it to the meaning of practice, then the end card | `warm` -> `gentle` |

### Dialogue and narration
- Children sound like children (short, halting, real). Parents sound like real parents. No exposition, no lessons in dialogue.
  Bad: "Reading comprehension is important because it develops cognitive abilities."
  Good: "I read it." / "What happened?" / "...I don't know." / (pause) / "Want to read it again with me?"
- Use `|0.6|` inside a line for a hesitation pause, and `{"pause": 0.8}` between lines for silence. Silence is a tool.
- Narration: sparingly, warm female narrator (`narrator` = Kokoro `af_heart`), only near the middle or end, never describing what we can see.
- The end card narration is **two short lines**, different every week (see registry). Example of the shape:
  "Practice doesn't only change what children can do on a page." / "Sometimes it changes what they feel ready to do outside of it."
- Brand line rotates weekly (never the same as the last 3): "Practice for more than the page." · "Learning shows up everywhere." ·
  "Small practice. Bigger moments." · "Build skills for the moments that matter." · "Learning can be simpler." (new ones welcome, same tone).

## 2c. VISUAL STANDARD - MIC Study v3 handmade doodle (permanent, approved by Maria Sept 2026)

Every new Wednesday film uses the **same approved MIC Study v3 illustration style as the daily Stories, Carousels and Reels**,
brought to life as a short film. Same art language, different storytelling depth (daily = simpler and educational;
Childhood Stories = cinematic, emotional, more detailed). Think: **"a child's drawing brought gently to life."**

- Style: warm cream paper `#FFF8EC` with subtle grain; colored-pencil / crayon hatching; thin wobbly ink; childlike doodle
  people (big round heads, dot eyes with a highlight, soft brows, red curved smile, soft blush, scribbled two-tone hair, stick
  arms and legs, clothes filled with pencil strokes and real details: knit rows, cuffs, buttons, prints, bows, laced sneakers).
  Props and decorations (books, pencils, hearts, stars, flowers, moon...) drawn the same way. Built on the daily kit
  (`engine/v3/kit2.py`, style reference "Mom-daughter dates"), unchanged.
- The whole world is drawn: rooms, furniture and skies use the same pencil and ink. Never doodle characters on vector or
  realistic backgrounds. Avoid flat vector, Canva/stock, corporate, 3D, glossy, photoreal, generic AI cartoon, perfect anatomy.
- It must feel like a SHORT FILM, never a slideshow: wide / medium / close / insert / reaction shots and cuts; slow push-ins
  and pans; subtle parallax (background, midground, foreground); character movement (walking, sitting, looking away, hands,
  page turns, pointing); small facial reactions; pauses; environment motion (steam, clouds, floating pencil hearts). The ink
  "boils" gently (redrawn every 4 frames) so it reads as a living drawing.
- Emotion stays subtle: a child looking down at the page, a parent sitting beside them, a hand on a pencil, a small smile,
  silence before a line. Never exaggerated faces.
- Character continuity: recurring characters are generated from `engine/cast.json` by `engine/v3/cast_v3.py`, so face design,
  skin, hair style and colour, clothing palette and relative age stay the same every week (and their approved voice).
  Clothing may change by scene via `cast_overrides`; the illustration language never does.
- Text: minimal. Anything inside the art is handwritten (Architects Daughter / Gochi Hand). Subtitles stay highly readable
  (Nunito 800 on a cream card with a thin ink border, in the Reels safe area). No big corporate title cards inside scenes;
  MIC Study appears only on the end card, the brand card and the cover.
- Cover: a hand-drawn miniature movie poster - the main character(s) at the key emotional moment, a short handwritten title
  (ALL CAPS, yellow crayon underline), warm cream paper, small official MIC Study logo. Never an educational infographic.
- Upload size: the 9.5 MB upload limit softens the finest hatching; keep scenes uncluttered (1-3 characters, a few props),
  and prefer slow camera moves - the engine already keeps hatching stable between frames so texture survives.

## 3. Production (v3 engine)

```
bash childhood-stories/engine/setup.sh                                                   # once per session
python3 childhood-stories/engine/v3/produce_v3.py episodes/<folder>/episode.py --preview   # stills + timing + cover, ~1 min
python3 childhood-stories/engine/v3/produce_v3.py episodes/<folder>/episode.py             # full render + QC, ~20-30 min
```
Run the full render in the background (nohup) and poll: it takes longer than one shell command allows. `--resume` reuses
shots already rendered in `_work/` (only if those shots did not change). Episode folder: `YYYY-MM-DD-<slug>`. Outputs (same
as before): `master.mp4`, `upload.mp4` (<= 9.5 MB, what gets uploaded), `cover.png`, `subtitles.srt`, `timeline.json`,
`render_log.json`, `qc/qc.json`, `qc/contact_*.jpg`, `preview/` (sheet_*.jpg + cover.png).
Worked example: `episodes/_v3-pipeline-test/episode.py`. The old flat engine (`engine/produce.py`, `cs/scenekit.py`) is
retired for new films and kept only for the pilot.

### Screenplay format (`episode.py` defines `EPISODE`; plain data, no imports needed)
```python
EPISODE = {
  "title": "Through", "slug": "through", "key": "F", "bpm": 72, "seed": 23,   # change key + seed weekly
  "brand_line": "Small practice. Bigger moments.",
  "extra_cast": {...},            # new characters, same fields as cast.json (they are drawn in v3 automatically)
  "cast_overrides": {"ava": {"top": {"style": "hoodie", "color": "#90CAF9"}}},   # wardrobe change for this film
  "sets_v3": {"my_room": fn},     # optional custom set functions (same return shape as sets_v3.py)
  "shots": [ SHOT, ... ],
  "end": {"narration": ["line 1", "line 2"], "music": "gentle"},
  "cover": {"shot": 2, "t": "L0.end+1.2", "title": "Through"},
}
```
SHOT keys:
- `set`: kitchen, bedroom, classroom, living_room, park, store, stage, library, hallway (engine/v3/sets_v3.py) or a custom
  one; `set_kw` (e.g. `{"night": True}`, `{"chairs": [430, 700]}`, `{"desks": [300, 780]}`). Floor line y 1640 (park 1700,
  stage 1600); table tops ~1250 (kitchen), desks ~1300 (classroom), counter ~1180 (store).
- `music`, `amb`, `trans` (cut, dissolve, fade) + `tdur`, `start`, `tail`, `min`, `dur`, `sfx` - exactly as before.
- `cam`: keyframes `[t, x, y, zoom]` (`t` may be seconds, `"end"`, `"L2"`, `"L2.end+0.4"`). Wide 1.0-1.15, medium 1.35-1.55,
  close two-shot 1.8-2.1, insert on hands/page 2.2-2.6.
- `actors`: `{key: {"keys": [[t, state], ...]}}`. State fields (world coords): `x`, `y` (head centre), `pose`
  (stand | sit | walk), `expr`, `look` [dx, dy], `smile`, `brow`, `tilt`, `hand` / `hand2` [x, y] (right / left hand
  targets), `point` [dx, dy] (finger), `floor`, `scale`, `ease` (seconds the move takes before this key). Numbers ease
  smoothly between keys; walking = a key with a new `x` and `"pose": "walk"`. Blinks, talking mouths (from the voice),
  and looking at whoever is speaking are automatic. Give standing adults an explicit `y` (~760) if they later sit (~880).
- `expr`: neutral, calm, happy, proud, tender, hopeful, curious, focused, unsure, worried, nervous, sad, disappointed,
  embarrassed, tired, determined, excited, surprised, relieved, frustrated, thoughtful, playful. A line's `expr` applies to
  the speaker from that line on.
- `props`: `[["book", {"x", "y", "word", "glow_from": "L0"}], ["mug", {...}], ...]` - book, worksheet, mug, pencil, coins,
  backpack, ball, lunchbox, plate_cookies, jar, trophy, plant.
- `fx`: `[["hearts", "L0.end+0.3"]]` floating pencil hearts.
- `script`: as before (`who`, `line`, `expr`, `emo`, `speed`, `after`, `say`, `{"pause": s}`, `{"sfx": ...}`).

### Staging checklist (use preview/sheet_*.jpg)
- Every speaking character is in the shot and their face is visible; hands reach what they touch (child at table: hand y ~1242).
- Seated characters sit behind the table (set `mid`); standing ones behind counters look natural.
- Vary shot sizes: open wide, go medium and close for emotion, insert on hands/page, wide or close again for the payoff.
- Keep 1-3 characters per shot and a few props; subtitles stay readable.

## 4. Quality control (fail-safe)

`produce.py` runs `cs/qc.py` automatically (exit code 2 = blocked). It checks: file opens, duration, 1080x1920, H.264 yuv420p 30 fps,
audio present and loud enough, no decode errors, no unexpected black frames, long frozen stretches, every dialogue line heard at
its time (speech recognition vs script), subtitles present, subtitles inside the safe area, speakers on screen, cover size, upload size.

Then **look** at every `qc/contact_*.jpg` and `cover.png` (Read them): faces and hands not malformed, nothing clipped, logo correct
on the brand card and cover, staging makes sense, nothing realistic or photographic. Fix and re-render if anything is off.

If a stage fails: retry that stage once. If it still fails: **do not publish**. Log `FAILED | date | reason | stage` in the registry
and the publishing log, keep all files (commit them), and tell Maria.

## 5. Publishing

Same Meta Business Suite route as the existing MIC Study Reels task (Claude in Chrome, "MIC Study" account, Spanish UI):
Crear reel -> upload `upload.mp4` -> cover `cover.png` (Miniatura / Subir imagen) -> caption -> Programar for **Wednesday 17:30
America/Toronto** on Facebook "MIC Study" + Instagram @hellomicstudy. If the Programadas list already has a Reel at 17:30 that
Wednesday (booked before this series existed), use **15:00** instead. Never "Compartir ahora", never delete or move other posts,
never publish twice (check Programadas + Publicadas for this title first).

Caption: emotional, short, parent-focused, not a plot summary, new every week, then
`MIC Study` / `Math + Reading • Grades 1-9` / `micstudy.com`, then 5-8 rotating hashtags (always #MICStudy).

## 6. Registry

`MIC-STUDY-STORY-REGISTRY.csv` - one row per Wednesday (including FAILED runs):
`date,title,slug,setting,world,main_characters,relationship,skill_type,skill,core_conflict,emotional_lesson,final_message,brand_line,filename,publication_status,scheduled_time,notes`
