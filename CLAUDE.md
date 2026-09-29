# Speak Like a Leader: High-Stakes Presence

A mobile-first, high-level communication trainer for any professional: speaking and presence in the moments
that matter (investors, executives, clients, negotiations, senior rooms, hard conversations). Industry-neutral.
Owner: Nick (CEO, Property Hub Cambodia), but the product is deliberately NOT specific to his company or to
real estate (his direction, 2026-09-29).

## What it is
- Single self-contained file: `index.html` (HTML + CSS + JS inline, no build step).
- Open it directly in a browser to test. No server needed.
- Progress is saved in `localStorage` under the key `sla-highstakes-v1` (per device).
- Live: https://narithkgame2.github.io/Speak-Like-A-Leader/ (GitHub Pages, public repo
  narithkgame2/Speak-Like-A-Leader, deploys from `main` about a minute after each push). https, so the
  microphone works on iPhone. Local testing: `python3 -m http.server 8000` in this folder.

## Structure
- Name: **Speak Like a Leader** (renamed 2026-09-29; summit rank "Trusted Leader"). iPhone app icon + web manifest:
  `icons/` (source `icons/icon.svg`, PNGs rendered with headless Chrome), `manifest.webmanifest`; opens full screen
  from the Home Screen as "Speak Leader".
- Units (`UNIT_DEF`, climbing order): Foundation, Clarity, First impressions, Presenting and persuading, Under pressure,
  Negotiation, Video calls, People and hard conversations, Listen and ask, Lead the room, Tough Q&A (the last three
  added 2026-09-29 at the top so nobody's progress moves back; Tough Q&A is High Camp). A lesson joins a unit with `unit:"Clarity"` (none =
  Foundation); a scenario joins by its `cat`. Each unit is a camp (`CAMPS`, `ALTS` up to 5,000 m, `RANKS` one per
  camp, `ZONES` scenery, 11 each; `ALTS`/`RANKS` 12 with the summit). 23 lessons (8 Foundation, 3 each for Clarity, Video
  calls, Listen and ask, Lead the room, Tough Q&A), 26 scenarios (A–Z: a 27th needs `letter()` to go past Z), 49 steps. Keep new lessons in
  the form `  { title:"…", unit:"…",` so tools/make_voice.py can read them.
- More session kinds on the lesson card engine (`lsess.kind`): 'lesson', 'r3', 'prep', 'breathe'; non-lesson kinds
  run on route `session`.
- Round 3 "Your words" (`ROUND3`, JSON by scenario index): no script; a question from the other person (or a coach
  instruction when `"coach": true`), three points to hit, record, listen back, tap the points you made (self-check;
  no speech recognition). Starts from a scenario once round 2 is done; `state.scR3`. Clips `r3-{scenario}-{k}`.
- Meeting prep (Prep tab, routes `prep` / `prepedit`, `state.preps`): who, goal, up to 6 key lines; per line tap
  words to stress and dots to pause (stored as word indices, `prepMarkup`), rehearse with record/compare, First vs
  Today, a "Ready" screen, and "Breathe first". The model is the device voice until "Use this take as my model"
  (saved like a studio take, id `pp-{id}-l{k}`). No reminders (needs a server).
- Lesson quizzes: one "Which is stronger?" (first example) plus `LESSON_QUIZ` (JSON by lesson index): `choice`,
  `weak` (tap the weak words, then Check), `stress` (tap the stressed word), `pause` (tap the gap; answer n =
  after word n). Word indices count words split on spaces. Coach clips `c-lesson{i}-q{k}` / `-why`.
- Quiz audio (`quizRead`, `quizVerdict`): on every quiz card the coach asks the question, then each answer is read
  aloud and highlighted (`.reading`); tapping any time stops it. Spoken answers use the model voice, described actions
  ("[sitting still…]") and choice options the coach. After a tap the coach says "Right." / "Not quite." (`c-fx-right`,
  `c-fx-wrong`) and the reason. "▶ Listen" replays. Clips: `qz{i}-a` / `qz{i}-b` (first example), `qz{i}-{k}-o{n}`
  (choice options), `qz{i}-{k}-t` (tap-quiz sentence). Coach off = silent unless Listen is tapped.
- Breathing card (`type:'breathe'`) replaces "breath" marks in a drill: 3 guided breaths, in 4 / out 6.
- First try vs today: every recorded line (scenario `s{si}-l{li}`, lesson `l{i}-p{k}` / `l{i}-d`) keeps its first
  and latest take in IndexedDB store `history` (db `sla-voice` v2). The review shows "First" (date, grey
  waveform, play) above "Today" when the first take is from an earlier session.
- Less waiting: the scenario setting (read without the title) auto-starts the lines; the round explanations
  (`c-fx-r1`, `c-fx-r2`) play once ever (`state.cues`). A scenario with round 1 done shows a brass ring
  (`.node.half`). Top bar stats are labelled ("3 days · 9 done"). Lessons have the speed button too.
- Lessons run as card sessions (`lsess`, `lessonCards`, `viewLessonSession`), one idea per screen:
  idea (rule; coach reads it; "Why it works" on tap) → one quiz per example ("Which is stronger?", tap = answer,
  the coach reads the reason) → "Now you say it" (the first playable example) → drill → [builder] → [timed] → done
  with "Next: …". The long lesson page (`viewLesson`) is kept as the "More" reference page.
- Lesson titles are short actions (Calm your nerves, Slow down, Use silence, ...), each with an icon (`LICO`).
- "Next up" everywhere: a fixed Continue button on home, "Next: …" at the end of lessons and scenarios
  (`nextItem()` = first unfinished step on the path, `nextUp()`).
- `LESSONS` array: 8 foundation lessons. Each has `title, sub, rule, why, pairs[], drill{tag, script, note}, own`,
  and optionally `practice{secs, note, list[]}` (timed questions) and `builder:true` (intro builder, lesson 6).
- `SCENARIOS` array: 16 full meeting scripts, grouped by `cat`. Each line is `[who, text, coachNote]`.
  `who` is `"you"`, `"them"`, `"them:Name"` (a second speaker) or `"stage"` (a stage direction).
- Script markup inside text: `‧‧‧` = short pause, `‧‧‧‧‧` = long pause, `↘` = pitch falls at the end,
  `*word*` = sentence stress (may span words: `*three years*`; never across a pause). Mark the one word per
  phrase that carries the meaning: new information, a contrast, or a number. Every "you" line has stress marks.
- Routes: home, lessons, lesson/i, scenarios, scenario/i, settings. Navigation: bottom tab bar on phones, which becomes
  a left rail at >=900px wide. Home is ONE screen, no page scroll: a mountain seen from afar with the trail switching
  back and forth up its face ("camera follows you"). Unit 1 (the lessons) is Base Camp at the bottom, each scenario
  `cat` is a higher camp (`CAMPS`, `ALTS` in metres), the summit "Trusted Leader" is at the top. World is 1000×1600
  (`MW`,`MH`,`PEAK`,`BASE_Y`); `mtnModel()` builds the trail and places the 34 steps along it, denser the higher
  they are; `mtnArt()` paints the SVG (sky, sun or moon and stars, ranges, massif with an altitude zone per camp,
  snow cap, trees/rocks/snow, clouds, tent, summit flag). `drawScene()` sizes `#mstage` to fill the viewport above
  the Continue bar and tab bar and builds HTML overlay buttons (steps `.mn`, camp chips `.mcamp`, `.msummit`);
  `mtnApply()` projects them with the camera `cam={x,y,s}` each frame and redraws the trail (brass up to you,
  dotted after). `camFor(step)`: before the first step and when all is done = whole mountain; otherwise a close
  view that follows you (scale >=0.9, steps ~95px apart), and in the last camp it frames you and the summit.
  Once per app load (`flown`), home opens on the whole mountain and flies in to you (`flyT`, 1.6s). Steps shrink to dots when crowded; camp chips show only
  when readable or it's your camp. "Whole mountain" / "Back to me" toggles `camMode`; tapping a camp chip zooms to
  it (`camCamp`); drag or wheel pans (`mtnDrag`); `camTo` tweens (reduced motion = jump). Tapping a step opens a
  bottom sheet (`mtnSheet`) with Start. Reruns on resize, font load and theme change. "Your climb" card shows rank
  (`RANKS`, one per camp), altitude and a mini mountain profile; sticky right rail at >=1200px. The Lessons tab is
  one numbered list of all lessons (row tinted by unit) plus the five principles.
  Practice sessions run full screen (`body.focus`).
- Levels and stars (Candy Crush-style, 2026-09-29): steps show numbers 1–49; finished steps show 1–3 brass stars
  (`state.stars`, key `l{i}` / `s{i}`, best kept; steps finished before stars existed show 3). Lesson stars = quizzes
  right + say cards with a "good" verdict; scenario stars = round-2 lines with "good" (`sess.good`); >=85% 3, >=50% 2,
  else 1 (`scoreStars`, `award`). The done card shows the stars. The first time a step is finished, `pendingUnlock`
  is set and the done card's main button becomes Continue (`tomap`) → home plays `playUnlock`: stars pop, the brass
  trail and the flag (`.mflag`, driven by `MTN.cutD` / `MTN.flagPt`) walk to the next step, which lights up; finishing
  a camp shows the "Camp reached · New rank" card (`gateHTML`; the summit gets its own). Camps above yours sit under
  mist (`.fog`, `.mcamp.locked`). Camp chips slide up/down to avoid covering steps.
- Offline (`sw.js`, `offlineInit`): the page, icons and clip list are network-first with a saved fallback; after the
  first visit all voice clips are saved in the background (cache `sla-clips-v1`, old versions removed) and answered
  with 206 range responses for Safari. Clip URLs carry `?v=<hash>` from the manifest, so regenerated clips replace
  saved ones. Settings shows "Ready offline" / "Saving for offline… n%". Only on http(s).
- Streak: `state.days` holds the dates practiced (a lesson marked done, a rating, or a scenario line reviewed).
- Voice: each scenario line can have a recorded clip, id `s{scenario}-l{line}`. The model plays, in order:
  1) the user's own take from the Voice studio (route `studio`, under Settings; stored in IndexedDB `sla-voice`,
  this device only, trimmed to the speech), 2) a file in `audio/` listed in `audio/manifest.js`
  (`window.AUDIO_FILES` → `AUDIO`), 3) browser `speechSynthesis`.
- Settings → Model voice: **Recorded** (the generated files, default) or **Device voice** (`state.voiceSrc='device'`:
  skip `AUDIO` for model, other speakers and coach, and use the device's best speechSynthesis voice, ranked by
  `rankVoice` so Premium/Enhanced come first; the coach uses a different voice via `themVoice`). The user's own
  studio takes still win in both modes.
- `tools/make_voice.py` generates `audio/` + the manifest, free and offline. Default engine: **Kokoro-82M** neural
  voices (run with `tools/.venv/bin/python tools/make_voice.py`; setup steps in the script header; `tools/.venv/`
  and `tools/models/` are git-ignored). Cast: you = am_michael (speed 0.92), coach = af_heart, men = am_fenrir /
  bm_george, women = af_bella / bf_emma / af_nicole. Pauses are exact silences between separately generated
  phrases; Kokoro ignores stress marks. `--say` falls back to macOS voices. Rerun after editing any script line;
  only changed clips regenerate. Clips highlight words over voiced time; speechSynthesis uses `onboundary`.
- Coach voice (the trainer, Moira): clips `c-fx-*` (session cues and spoken feedback, texts in `COACH_FX`),
  `c-s{si}-l{li}` (the coach note for each "you" line), `c-lesson{i}-rule` / `-p{k}-note` (lesson cards),
  `c-lesson{i}-intro` / `-drill` (buttons on the More page). Lesson model clips: `l{i}-p{k}`, `l{i}-d` (drill). In practice: intro at round start, then per line their line → coach tip → model
  (round 2: "Your turn."), spoken verdict after each recording (`judge().key`), and a line at round end. Toggle:
  "Coach on/off" in the practice bar and Settings (`state.coachVoice`). Missing clips fall back to the browser voice.
  All clips play through one shared `PLAYER` element so iPhones allow the spoken feedback after the first tap.
- Scenarios start directly (`startScenario`: from Continue, the path or the list) on a setting card (who, where,
  goal; the coach reads clip `c-sc{i}-intro`) → Start → lines. Round 2 is picked automatically once round 1 is done
  (`state.scR1`). ✕ returns to where you came from; the done card offers "Next: …" and More (the scenario page
  with the full script and "Make it yours"). On screens >=1200px the Continue button sits in the "Your climb" card.
- Scenario practice is guided shadowing (modelled on BoldVoice / ELSA), one of your lines at a time:
  Listen (their line, then the model line) → Record (mic) → Compare (play model / me / both, rough pace and
  pause feedback from the recording) → Try again or Good, next. Round 1 = read along, Round 2 = line hidden,
  from memory. Finishing round 2 marks the scenario practiced. Session state lives in `sess` (not saved).
- Recording uses `getUserMedia` + `MediaRecorder` and needs a secure context (https or localhost).
  Recordings stay in memory only. `analyze()` measures speaking time, pauses (>=360ms), and `end` = volume of the
  last ~300ms of voice vs the whole line (below 0.55 = "last word faded", Lesson 2).
- Profile: a one-time welcome screen (`viewWelcome`, `state.onboarded`) asks name + who you help / what they get
  / without what (`state.intro`, same data as the Lesson 6 builder; Settings → "Your introduction" reopens it).
  Script text may contain `{name}` and `{intro}`; `personal()` fills them everywhere text is parsed or shown
  (`parseLine`, `fmt`, `segsOf`, `renderScript`, `quizText`). Personal lines have no recorded clip
  (`isPersonal`; the generator skips them) and play in the device voice.
- Scenario lines render as chat bubbles: `them` left, `you` right, a second speaker gets `.alt`.

## Teaching principles (keep these when adding content)
1. Never apologize for being there. 2. Fewer words. 3. Answer first.
4. Ask instead of defending. 5. Let silence work.
- Every example shows "what most people say" vs "what to say instead", plus a one-line reason.
- Users must rewrite lines in their own words. Scripts are for training delivery, not for memorizing.
- Stories and personal claims in scripts must be true. Mark invented ones clearly for the user to replace.

## Design
- Duolingo structure (learning path, full-screen practice, result banner), premium finish. Never copy their logo,
  mascot or colors.
- Warm paper background (#F6F4EF), white cards with 1px borders and soft shadows, dark ink primary buttons,
  brass (`--gold`) for achievements, progress and pause markers. Each unit has a deep jewel tone (`.u-green` = emerald,
  `.u-blue` = sapphire, ...) used as a gradient. Dark theme via `prefers-color-scheme`.
- Fonts: Spectral (headings, script lines), Inter (UI). Small labels: tiny uppercase with wide letter spacing.
  Buttons use normal case. Small gold text uses `--gold-text` for contrast.
- Practice results use a tinted footer banner: green = good, gold = almost, blue = neutral, with ONE short tip.
- Minimal text (Nick's feedback 2026-09-29: too much text was confusing). Say a thing once, or let the coach voice
  say it: no helper sentences under headings, no explainer cards, list rows show titles only, the written coach note
  and marker legend only appear when the coach voice is off. Prefer short labels ("Skip", "Both", "Listen").

## Known limitations / ideas
- Model voice: Kokoro neural voices (2026-09-29), replacing robotic macOS voices. Next: Nick's own studio takes.
  Higgsfield was cancelled (2026-09-28); no paid AI voice.
- Progress is per device. A team version would need sign-in and a manager view.
- The user learns best by shadowing: reading along word by word with audio.
