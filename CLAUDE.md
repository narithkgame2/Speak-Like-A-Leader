# Speak Like an Advisor: High-Stakes Presence

A mobile-first training app for speaking and presence in high-stakes meetings
(investors, negotiations, senior partners, hard conversations). Not limited to real estate.
Owner: Nick (CEO, Property Hub Cambodia). Built for him first, then his team.

## What it is
- Single self-contained file: `index.html` (HTML + CSS + JS inline, no build step).
- Open it directly in a browser to test. No server needed.
- Progress is saved in `localStorage` under the key `sla-highstakes-v1` (per device).
- Live: https://narithkgame2.github.io/Speak-Like-A-Leader/ (GitHub Pages, public repo
  narithkgame2/Speak-Like-A-Leader, deploys from `main` about a minute after each push). https, so the
  microphone works on iPhone. Local testing: `python3 -m http.server 8000` in this folder.

## Structure
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
  a left rail at >=900px wide. Home is a mountain climb that goes bottom-up: unit 1 (the lessons) is Base Camp at
  the bottom, each scenario `cat` is a higher camp (`CAMPS`, `ALTS` in metres), the summit "Trusted Advisor" is
  at the top. `drawScene()` paints the mountain as inline SVG to fit the page (sky, distant ranges, an altitude
  zone per unit, trees/rocks/snow, clouds, sun or moon in dark mode) and calls `drawTrails()`; both rerun on
  resize, font load and theme change. Each unit's camp sign sits below its nodes; a brass flag marks the current
  node, and home opens scrolled to it (`scrollToNow`). "Your climb" card shows rank (`RANKS`, one per camp),
  altitude and a mini mountain profile; sticky right rail at >=1200px. Tapping a node opens a popover with Start.
  Practice sessions run full screen (`body.focus`).
- Streak: `state.days` holds the dates practiced (a lesson marked done, a rating, or a scenario line reviewed).
- Voice: each scenario line can have a recorded clip, id `s{scenario}-l{line}`. The model plays, in order:
  1) the user's own take from the Voice studio (route `studio`, under Settings; stored in IndexedDB `sla-voice`,
  this device only, trimmed to the speech), 2) a file in `audio/` listed in `audio/manifest.js`
  (`window.AUDIO_FILES` → `AUDIO`), 3) browser `speechSynthesis`.
- Settings → Model voice: **Recorded** (the generated files, default) or **Device voice** (`state.voiceSrc='device'`:
  skip `AUDIO` for model, other speakers and coach, and use the device's best speechSynthesis voice, ranked by
  `rankVoice` so Premium/Enhanced come first; the coach uses a different voice via `themVoice`). The user's own
  studio takes still win in both modes.
- `tools/make_voice.py` generates `audio/` + the manifest with macOS `say` (free, offline): ‧‧‧ become real
  silences, *stressed* words get `[[emph +]]`, each character gets a voice by title (Mr./Ms.). Rerun after editing
  any script line; only changed lines are regenerated. To upgrade quality, download a Premium voice in macOS
  Spoken Content settings and set `YOU` (and the cast) at the top of the script. Clips highlight words proportionally to word length; speechSynthesis uses
  `onboundary` (not supported by every voice). Settings → "Use my recordings as the model" (`state.useMine`).
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
- Model voice today: macOS voices (Daniel for "you"). Next: a Premium macOS voice, then Nick's own studio takes.
  Higgsfield was cancelled (2026-09-28); no paid AI voice.
- Progress is per device. A team version would need sign-in and a manager view.
- The user learns best by shadowing: reading along word by word with audio.
