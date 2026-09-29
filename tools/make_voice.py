#!/usr/bin/env python3
"""Generate every voice clip the app plays (model lines, other speakers, the coach). Free and offline.

Writes audio/{id}.m4a and audio/manifest.js, which index.html loads as window.AUDIO_FILES.
Pauses (‧‧‧) become real silences. Only clips whose text, voice or engine changed are regenerated.

Engine "kokoro" (default when installed): Kokoro-82M neural voices, much more natural than macOS voices.
  Setup once:  ~/.local/bin/uv venv tools/.venv --python 3.12
               ~/.local/bin/uv pip install --python tools/.venv/bin/python kokoro-onnx soundfile numpy
               download kokoro-v1.0.onnx + voices-v1.0.bin (github.com/thewh1teagle/kokoro-onnx releases,
               tag model-files-v1.0) into tools/models/  (both folders are git-ignored)
  Run:         tools/.venv/bin/python tools/make_voice.py
Engine "say" (fallback): macOS voices.  Run: python3 tools/make_voice.py --say
"""
import hashlib, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio")
MODELS = os.path.join(ROOT, "tools", "models")
SHORT, LONG = 650, 1300                                # ms of silence for ‧‧‧ and ‧‧‧‧‧

# Cast: (voice, speed). Kokoro speed is a multiplier; macOS say speed is words per minute.
CASTS = {
    "kokoro": dict(
        YOU=("am_michael", 0.92),                      # your lines: calm, unhurried
        COACH=("af_heart", 1.0),                       # the trainer: warm, clear
        MALE=[("am_fenrir", 1.0), ("bm_george", 1.0)],
        FEMALE=[("af_bella", 1.0), ("bf_emma", 1.0), ("af_nicole", 1.0)],
        NEUTRAL={"Host": ("af_nicole", 1.0), "Audience": ("bf_emma", 1.0), "Investor": ("am_fenrir", 1.0), "Client": ("am_fenrir", 1.0), "Dara": ("af_bella", 1.0)}),
    "say": dict(
        YOU=("Daniel", 165), COACH=("Moira", 175),
        MALE=[("Rishi", 180), ("Aman", 180)],
        FEMALE=[("Samantha", 180), ("Karen", 180), ("Moira", 180)],
        NEUTRAL={"Host": ("Samantha", 180), "Audience": ("Karen", 180), "Investor": ("Rishi", 175), "Client": ("Rishi", 175), "Dara": ("Tessa", 180)}),
}
ENGINE = "say" if "--say" in sys.argv or not os.path.exists(os.path.join(MODELS, "kokoro-v1.0.onnx")) else "kokoro"
CAST = CASTS[ENGINE]
YOU, COACH, MALE, FEMALE, NEUTRAL = CAST["YOU"], CAST["COACH"], CAST["MALE"], CAST["FEMALE"], CAST["NEUTRAL"]


def source():
    return open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def scenarios():
    s = source()
    i = s.index("const SCENARIOS = ") + len("const SCENARIOS = ")
    return json.loads(s[i:s.index("\n];", i) + 2])


def plain(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()


def coach_lines():
    """Every coach clip: session cues (COACH_FX), the tip for each of your lines, lesson intros and drill notes.
    Texts match coachText() in index.html, which the app uses when a clip is missing."""
    s = source(); out = {}
    i = s.index("const COACH_FX = ") + len("const COACH_FX = ")
    for k, v in json.loads(s[i:s.index("\n};", i) + 2]).items(): out[f"c-fx-{k}"] = v
    for si, sc in enumerate(scenarios()):
        out[f"c-sc{si}-intro"] = plain(f"{sc['setting']} Your goal: {sc['goal']}")
        for li, line in enumerate(sc["lines"]):
            if line[0] == "you" and len(line) > 2 and line[2]: out[f"c-s{si}-l{li}"] = plain(line[2])
    for n, l in enumerate(lessons()):
        out[f"c-lesson{n}-intro"] = plain(f"{l['title']}. {l['sub']} The rule. {l['rule']} {l['why']}")
        out[f"c-lesson{n}-drill"] = plain(f"{l['tag']} {l['drill_note']}")
        out[f"c-lesson{n}-rule"] = plain(f"{l['title']}. {l['rule']}")
        for k, pr in enumerate(l["pairs"]): out[f"c-lesson{n}-p{k}-note"] = plain(pr["note"])
    i = s.index("const LESSON_QUIZ = ") + len("const LESSON_QUIZ = ")
    for n, qs in json.loads(s[i:s.index("\n};", i) + 2]).items():
        for k, q in enumerate(qs): out[f"c-lesson{n}-q{k}"] = q["prompt"]; out[f"c-lesson{n}-q{k}-why"] = q["why"]
    return out


def lessons():
    """Read the LESSONS array (a JS literal) well enough for the fields the voice needs."""
    s = source(); body = s[s.index("const LESSONS = ["):s.index("\n];", s.index("const LESSONS = ["))]
    fields = lambda t: [(k, json.loads('"' + v + '"')) for k, v in re.findall(r'(\w+):"((?:[^"\\]|\\.)*)"', t)]
    out = []
    for block in body.split("\n  { title:")[1:]:
        f = fields("title:" + block)
        get = lambda key, after=0: next(v for j, (k, v) in enumerate(f) if k == key and j >= after)
        tag_at = next(j for j, (k, _) in enumerate(f) if k == "tag")
        pairs = []
        for pb in re.findall(r'\{moment:(.*?(?:"|true))\}', block):   # a pair ends at "} or true}; {name} inside text is fine
            pf = dict(fields("moment:" + pb)); pf["noPlay"] = "noPlay:true" in pb; pairs.append(pf)
        script = json.loads(re.search(r"script:(\[\[.*?\]\])", block).group(1))
        out.append({"title": get("title"), "sub": get("sub"), "rule": get("rule"), "why": get("why"), "tag": get("tag"),
                    "drill_note": get("note", tag_at), "pairs": pairs, "script": script})
    return out


def drill_markup(script):
    """Same as drillMarkup() in index.html."""
    m = {"pause": "‧‧‧", "pause-long": "‧‧‧‧‧", "breath": "", "note": ""}   # breaths: the breathing card
    parts = [m[ty] if ty in m else f"{t} ↘" if ty == "down" else f"*{t}*" if ty == "stress" else t for t, ty in script]
    return " ".join(p for p in parts if p)


def speakers(sc):
    """Map each speaker key in a scenario to a (voice, rate) pair."""
    who = [sc["them"] if w == "them" else w.split(":", 1)[1]
           for w in dict.fromkeys(l[0] for l in sc["lines"] if l[0] not in ("you", "stage"))]
    keys = [w for w in dict.fromkeys(l[0] for l in sc["lines"] if l[0] not in ("you", "stage"))]
    m = f = 0; cast = {"you": YOU}
    for key, name in zip(keys, who):
        if name in NEUTRAL: cast[key] = NEUTRAL[name]
        elif re.match(r"(Ms|Mrs|Miss)\.?\s", name): cast[key] = FEMALE[f % len(FEMALE)]; f += 1
        else: cast[key] = MALE[m % len(MALE)]; m += 1
    return cast


def to_say(text):
    """Script markup → macOS speech commands."""
    t = re.sub(r"\[[^\]]*\]", "", text).replace("↘", "")
    t = t.replace("‧‧‧‧‧", f" [[slnc {LONG}]] ").replace("‧‧‧", f" [[slnc {SHORT}]] ")
    t = re.sub(r"\*([^*]+)\*", lambda m: "[[emph +]] " + m.group(1), t)
    return re.sub(r"\s+", " ", t).strip()


def segments(text):
    """Script markup → [(text, None) | (None, silence_ms)], stage directions and marks removed."""
    out = []
    for part in re.split(r"(‧‧‧‧‧|‧‧‧)", re.sub(r"\[[^\]]*\]", "", text)):
        if part == "‧‧‧": out.append((None, SHORT))
        elif part == "‧‧‧‧‧": out.append((None, LONG))
        else:
            t = re.sub(r"\s+", " ", part.replace("↘", "").replace("*", "")).strip()
            if t: out.append((t, None))
    return out


class Kokoro:
    def __init__(self):
        try:
            import numpy, soundfile
            from kokoro_onnx import Kokoro as K
        except ImportError:
            sys.exit("Kokoro isn't installed for this Python. Run: tools/.venv/bin/python tools/make_voice.py")
        self.np, self.sf = numpy, soundfile
        self.k = K(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))

    def render(self, voice, speed, text, wav):
        np, parts, sr = self.np, [], 24000
        for t, ms in segments(text):
            if t is None: parts.append(np.zeros(int(sr * ms / 1000), dtype=np.float32)); continue
            a, sr = self.k.create(t, voice=voice, speed=speed, lang="en-gb" if voice.startswith("b") else "en-us")
            parts.append(a.astype(np.float32))
        a = np.concatenate(parts) if parts else np.zeros(sr // 10, dtype=np.float32)
        # Same loudness for every voice (RMS of the speech ~0.07) with headroom: peaks never above 0.9.
        voiced = a[np.abs(a) > 0.01]
        if voiced.size:
            rms, peak = float(np.sqrt(np.mean(voiced ** 2))), float(np.max(np.abs(a)))
            a = a * min(0.07 / rms, 0.9 / peak)
        self.sf.write(wav, a, sr)


def say_render(voice, rate, text, aiff):
    subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff, to_say(text)], check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    engine = Kokoro() if ENGINE == "kokoro" else None
    if not engine:
        installed = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        for v, _ in [CAST["YOU"], CAST["COACH"], *CAST["MALE"], *CAST["FEMALE"], *CAST["NEUTRAL"].values()]:
            if not re.search(rf"^{re.escape(v)}\s", installed, re.M): sys.exit(f"Voice not installed: {v}")
    manifest, made, kept, old = {}, 0, 0, {}
    mf = os.path.join(OUT, "manifest.js")
    if os.path.exists(mf):
        m = re.search(r"=\s*(\{.*\});?\s*$", open(mf, encoding="utf-8").read(), re.S)
        if m: old = json.loads(m.group(1))
    jobs = []
    for si, sc in enumerate(scenarios()):
        cast = speakers(sc)
        for li, (who, text, *_) in enumerate(sc["lines"]):
            if who != "stage": jobs.append((f"s{si}-l{li}", *cast[who], text))
    for n, l in enumerate(lessons()):   # lesson model lines: the stronger example and the drill
        k = next((k for k, pr in enumerate(l["pairs"]) if not pr["noPlay"] and "lang" not in pr), None)
        if k is not None: jobs.append((f"l{n}-p{k}", *YOU, l["pairs"][k]["better"]))
        jobs.append((f"l{n}-d", *YOU, drill_markup(l["script"])))
    for lid, text in coach_lines().items(): jobs.append((lid, *COACH, text))
    jobs = [j for j in jobs if not re.search(r"\{(name|intro)\}", j[3])]   # personal lines use the device voice
    for lid, voice, speed, text in jobs:
        h = hashlib.sha1(f"{ENGINE}|norm1|{voice}|{speed}|{SHORT}|{LONG}|{text}".encode()).hexdigest()[:12]
        fn = f"{lid}.m4a"; path = os.path.join(OUT, fn)
        if old.get(lid, {}).get("h") == h and os.path.exists(path):
            manifest[lid] = old[lid]; kept += 1; continue
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "clip.wav" if engine else "clip.aiff")
            engine.render(voice, speed, text, src) if engine else say_render(voice, speed, text, src)
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", src, path], check=True)
        manifest[lid] = {"url": f"audio/{fn}", "voice": voice, "h": h}; made += 1
        print(f"  {lid:18} {voice:10} {re.sub(chr(10), ' ', text)[:50]}", flush=True)
    with open(mf, "w", encoding="utf-8") as f:
        f.write("// Generated by tools/make_voice.py. Do not edit by hand.\nwindow.AUDIO_FILES = ")
        json.dump(manifest, f, ensure_ascii=False, indent=0)
        f.write(";\n")
    stale = [f for f in os.listdir(OUT) if f.endswith(".m4a") and f[:-4] not in manifest]
    for f in stale: os.remove(os.path.join(OUT, f))   # clips for lines that no longer exist or became personal
    print(f"Done ({ENGINE}): {made} generated, {kept} unchanged, {len(stale)} removed, {len(manifest)} clips in audio/manifest.js")


if __name__ == "__main__":
    main()
