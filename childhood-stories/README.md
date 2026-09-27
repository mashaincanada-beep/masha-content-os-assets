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
- Visuals: illustrated storybook characters only (the engine rig). No photos, no realistic people.
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
- Narration: sparingly, only near the middle or end, never describing what we can see. Voice rules: section 2b.
- The end card narration is **two short lines**, different every week (see registry). Example of the shape:
  "Practice doesn't only change what children can do on a page." / "Sometimes it changes what they feel ready to do outside of it."
- Brand line rotates weekly (never the same as the last 3): "Practice for more than the page." · "Learning shows up everywhere." ·
  "Small practice. Bigger moments." · "Build skills for the moments that matter." · "Learning can be simpler." (new ones welcome, same tone).

## 2b. VOICE STANDARD (permanent, high priority - Maria, Sept 2026)

**Voice acting quality is as important as visual quality. A beautiful film with robotic dialogue does NOT pass QC.**
Engine: `engine/cs/voice.py` (voice system v2), cast: `engine/voice_cast.json`, tool: `engine/voices.py`.

**Providers, in order**
1. **ElevenLabs** `eleven_v3` (expressive, audio tags). Needs the API key in `$ELEVENLABS_API_KEY` or
   `~/.config/micstudy/elevenlabs.key` (never commit it - this repo is public).
2. **Kokoro** (the old local voices) - last-resort fallback only. Before using it, say so: the run reports
   "PREMIUM VOICES UNAVAILABLE: <reason>". A film voiced with the fallback is blocked by QC: it is saved to the repo as
   "Ready - not scheduled" and Maria decides. Never raise the pitch of an adult voice to make a child.

**Voice cast** (fixed, so recurring characters sound the same every week - `engine/voice_cast.json`)
- Narrator: warm adult woman, Canadian/North American English, calm, intimate, cinematic, thoughtful, never commercial. Different from every mom.
- Mothers: natural, conversational, warm but real. Fathers: calm, reassuring, conversational, never announcer-like.
- Young children (6-8) and older children (9-13): natural young voices designed for their age - not cartoonish, not squeaky,
  slightly imperfect rhythm; friends/classmates always distinct from the main child.
- Adults use ElevenLabs built-in voices; the narrator, the children and Grandma Rosa are custom voices made once with
  `python3 engine/voices.py design` (their ids are then committed). One-off adults come from `pools`. Avoid new child
  characters; if one is essential, add a designed voice for them to `voice_cast.json` (run `voices.py design <name>`).

**Acting direction - every spoken line has an intention.** Add `"emo"` to each line (default comes from the face `expr`):
`neutral, curious, hesitant, embarrassed, frustrated, tired, excited, quiet, whisper, reassuring, playful, proud, nervous,
relieved, thoughtful, sad, tender, storytelling`. The engine turns it into a v3 performance tag. You may also write tags inside
`"say"` for one-off moments, e.g. `"say": "[sighs] Okay. |0.4| One more time."` (tags never show in subtitles).
Real people pause, breathe, change speed and volume, stress a word, restart a phrase: write that in (`...`, `|0.4|`, a restart
like "I- I know this one"), but do not overdo stutters, and never make a child sound younger than their age.

**Child dialogue**: contractions, short sentences, pauses.
Bad "I do not understand this word." -> "I... don't know this word." Bad "Can you please read this book to me?" -> "Can you read it to me?"
Bad "I am bad at mathematics." -> "I'm just bad at math."

**Line by line, never a whole scene in one block.** Every line is generated on its own (pace, emotion, pauses, pronunciation,
volume and character stay controllable), then assembled with 150-600 ms of breathing room (`"after"`, default 0.38 s);
emotional pauses longer (`{"pause": 1.2}`).

**Narration** = storytelling, not advertising: slower, softer emphasis, natural pauses, slightly lower energy, warm. No
commercial rhythm, no constant enthusiasm, no radio voice, no perfectly even cadence.

**Emotional scenes: less dialogue. Let silence work.** Example: "I got the star." / "That sounds fun." / (pause) /
"...I don't have to say anything." The pause is part of the performance - do not fill it with narration.

**Post-processing (automatic)**: every line is levelled to the same loudness, lightly EQ'd, de-essed and gently compressed;
then placed in a small room matching the shot's `amb` (bedroom, kitchen, classroom, hallway, gym, outdoor...) - subtle, no
obvious reverb. Music ducks smoothly (about -10 dB, starting just before each line, easing back after); ambience dips slightly.

**Voice QC (automatic + you)** - every line is checked right after it is generated and **regenerated automatically (up to 3
takes)** if it is: unclear/mispronounced, too fast, too high-pitched, too low for a child's age (= an adult pretending to be a
child), monotone, or distorted. Then `qc/qc.json` -> `voice_flagged` lists anything still wrong. Blocking: any fallback voice,
any line still unclear / too high / adult-sounding child / distorted, or more than 2 lines still monotone or rushed.
The machine cannot judge acting taste, so also **read every line's transcript + emotion in `timeline.json`** and ask: would a
real child/parent say it like this? Anything unnaturally cheerful, emotionally wrong, or over-written: rewrite the line or change
its `emo`, and regenerate before the final render.

## 3. Production

```
bash childhood-stories/engine/setup.sh                                 # once per session (~1-2 min)
python3 childhood-stories/engine/produce.py episodes/<folder>/episode.py --preview   # stills + timing, ~2 min
python3 childhood-stories/engine/produce.py episodes/<folder>/episode.py             # full render + QC, ~8-10 min
```
Episode folder name: `YYYY-MM-DD-<slug>` (the Wednesday date). Outputs in that folder: `master.mp4`, `upload.mp4` (<= 9.5 MB,
what gets uploaded), `cover.png` (1080x1920), `subtitles.srt`, `timeline.json`, `render_log.json`, `qc/qc.json`, `qc/contact_*.jpg`,
`preview/` (stills). Start from `episodes/_pilot-four-quarters/episode.py` as a worked example.

### Screenplay format (`episode.py` defines `EPISODE`)
```python
from cs.scenekit import *            # sets + props helpers (see engine/cs/scenekit.py)
EPISODE = {
  "title": "Four Quarters", "slug": "four-quarters",
  "key": "D", "bpm": 76, "seed": 11,          # score key/tempo; change key + seed weekly
  "brand_line": "Small practice. Bigger moments.",
  "extra_cast": {...},                         # new characters (same fields as cast.json)
  "sets": {"kitchen": {"far": svg, "mid": svg, "front": svg, "near": svg}},
  "shots": [ SHOT, ... ],
  "end": {"narration": ["line 1", "line 2"], "music": "gentle"},
  "cover": {"shot": 2, "cam": [x, y, zoom], "title_y": 300, "override": {...}},
}
```
Layers and depth (camera parallax): `far` 0.55 (walls, sky), `mid` 1.0 (things behind the characters), actors 1.0,
`front` 1.0 (**furniture at the characters' depth that must cover them**: counters, tables, chair arms), `near` 1.35 (true
foreground only: blurred plants, leaves, audience heads). World view is 1080x1920; sets can extend to -240..1320 x -260..2180.

SHOT keys:
- `set`, `music` (curious, playful, uncertain, reflective, tender, hopeful, warm, gentle, silence), `amb` (home, kitchen,
  classroom, school, library, market, party, fair, gym, park, field, street, outdoor, night, room, none), `grade` (soft, warm,
  golden, cool, night, dim), `fx` (vignette, vignette_strong, dust), `trans` (cut, dissolve, fade) + `tdur`.
- `cam`: keyframes `[t, x, y, zoom]` (`t` may be `"end"`). Close-up ~1.5-1.8, medium ~1.2-1.4, wide ~1.0.
- `actors`: `{key: {x, y, s, expr, armL, armR, legs("stand"|"sit"), look(dx,dy), turn(-1..1), tilt, lean, eye, mouth, brow, auto_look}}`.
  Use `"key#2"` for a second copy. Children ~`s` 1.1-1.2 at y ~1760-1790; adults ~1.0 at y ~1690-1740.
- `expr`: neutral, calm, happy, joy, proud, tender, hopeful, determined, shy, curious, thinking, focused, unsure, worried, sad,
  disappointed, embarrassed, frustrated, surprised, tired, nervous.
- Arm poses: down, relaxed, hold, hold_low, raise, wave, hip, point, reach, chin, cross, shrug, cheer, chest, face, write, give,
  hug, tablet, counter, rest, thumbs, open, pocket - or explicit `[upper, fore]` angles.
- `script`: ordered items: `{"who", "line", "expr", "speed", "gap", "after", "say"}` (say = pronunciation override),
  `{"pause": s}`, `{"sfx": name, "gain", "pan"}`. Subtitles are generated from lines automatically.
- `beats`: `{"t", "who", "set": {...}, "dur"}`; `t` = seconds or `"L2"`, `"L2.end"`, `"L2+0.4"`, `"end-1"`.
  `set` can tween x/y/s/lean/tilt/turn/look/arms, switch expr/legs/eye/mouth, `walk_to: x`, `wave: true`, `auto_look`.
  Props: `{"t", "who": prop_id, "set": {x, y, s, rot, op, attach: [actor, "L"|"R", dx, dy] | None}}`.
- `props`: `{"id", "svg", "x", "y", "s", "rot", "squash" (0.5 = lying flat on a table), "layer" (front|back|near), "attach", "show": [t0, t1]}`.
- `sfx`: timed list `{"name", "t", "gain", "pan", "kw"}`. Sounds: page, pencil, footsteps, knock, door, chair, clink, pour,
  sizzle, chop, bell, chime, whistle, ball, kick, applause, coins, zip, click, whoosh, tick, birds, heartbeat, laugh_kid, gasp.
- `caption` (+`caption_t`) for small time cards ("That evening", "Saturday"); `title: True` on shot 1 shows the film title.
- `start`, `tail`, `min`, `dur` control timing. Target total **1:50-2:05** (hard limits 1:45-2:15 incl. the 4.8 s brand card).

### Staging checklist (use the preview sheets)
- Every speaking character's face is on screen and not covered. Children's hands reach what they touch (counters at chest height).
- Furniture at character depth goes in `front`, never `near`. Seated characters sit behind a `front` table.
- Vary shot sizes: open wide, move to medium and close-ups for emotion, wide again for payoff.
- Keep subtitles readable (engine keeps them in the Reels safe area; QC flags anything outside).

## 4. Quality control (fail-safe)

`produce.py` runs `cs/qc.py` automatically (exit code 2 = blocked). It checks: file opens, duration, 1080x1920, H.264 yuv420p 30 fps,
audio present and loud enough, no decode errors, no unexpected black frames, long frozen stretches, every dialogue line heard at
its time (speech recognition vs script), the VOICE QUALITY GATE (section 2b), subtitles present, subtitles inside the safe area, speakers on screen, cover size, upload size.

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
