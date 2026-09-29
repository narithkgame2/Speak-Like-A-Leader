#!/usr/bin/env python3
"""Generate the model voice for every scenario line with macOS text-to-speech (free, offline).

Writes audio/s{scenario}-l{line}.m4a and audio/manifest.js, which index.html loads as window.AUDIO_FILES.
Pauses (‧‧‧) become real silences and *stressed* words get emphasis, which the browser voice can't do.
Only lines whose text or voice changed are regenerated.

Usage:   python3 tools/make_voice.py            (from the project folder)
Better voices: System Settings → Accessibility → Spoken Content → System voice → Manage Voices, download a
Premium English voice (e.g. "Evan (Premium)", "Nathan (Premium)", "Jamie (Premium)"), set YOU below, run again.
"""
import hashlib, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio")

YOU = ("Daniel", 165)                                  # your lines: calm, unhurried
MALE = [("Rishi", 180), ("Aman", 180)]                 # Mr. ...; a second man gets the second voice
FEMALE = [("Samantha", 180), ("Karen", 180), ("Moira", 180)]
NEUTRAL = {"Host": ("Samantha", 180), "Audience": ("Karen", 180), "Investor": ("Rishi", 175), "Dara": ("Tessa", 180)}
COACH = ("Moira", 175)                                # the trainer: tips, instructions, feedback
SHORT, LONG = 650, 1300                                # ms of silence for ‧‧‧ and ‧‧‧‧‧


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
        out[f"c-sc{si}-intro"] = plain(f"{sc['title']}. {sc['setting']} Your goal: {sc['goal']}")
        for li, line in enumerate(sc["lines"]):
            if line[0] == "you" and len(line) > 2 and line[2]: out[f"c-s{si}-l{li}"] = plain(line[2])
    for n, l in enumerate(lessons()):
        out[f"c-lesson{n}-intro"] = plain(f"{l['title']}. {l['sub']} The rule. {l['rule']} {l['why']}")
        out[f"c-lesson{n}-drill"] = plain(f"{l['tag']} {l['drill_note']}")
        out[f"c-lesson{n}-rule"] = plain(f"{l['title']}. {l['rule']}")
        for k, pr in enumerate(l["pairs"]): out[f"c-lesson{n}-p{k}-note"] = plain(pr["note"])
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
        for pb in re.findall(r"\{moment:(.*?)\}", block):
            pf = dict(fields("moment:" + pb)); pf["noPlay"] = "noPlay:true" in pb; pairs.append(pf)
        script = json.loads(re.search(r"script:(\[\[.*?\]\])", block).group(1))
        out.append({"title": get("title"), "sub": get("sub"), "rule": get("rule"), "why": get("why"), "tag": get("tag"),
                    "drill_note": get("note", tag_at), "pairs": pairs, "script": script})
    return out


def drill_markup(script):
    """Same as drillMarkup() in index.html."""
    m = {"pause": "‧‧‧", "pause-long": "‧‧‧‧‧", "breath": "‧‧‧‧‧", "note": ""}
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


def main():
    os.makedirs(OUT, exist_ok=True)
    installed = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    manifest, made, kept = {}, 0, 0
    old = {}
    mf = os.path.join(OUT, "manifest.js")
    if os.path.exists(mf):
        m = re.search(r"=\s*(\{.*\});?\s*$", open(mf, encoding="utf-8").read(), re.S)
        if m: old = json.loads(m.group(1))
    jobs = []
    for si, sc in enumerate(scenarios()):
        cast = speakers(sc)
        for li, (who, text, *_) in enumerate(sc["lines"]):
            if who != "stage": jobs.append((f"s{si}-l{li}", *cast[who], to_say(text)))
    for n, l in enumerate(lessons()):   # lesson model lines: the stronger example and the drill
        k = next((k for k, pr in enumerate(l["pairs"]) if not pr["noPlay"] and "lang" not in pr), None)
        if k is not None: jobs.append((f"l{n}-p{k}", *YOU, to_say(l["pairs"][k]["better"])))
        jobs.append((f"l{n}-d", *YOU, to_say(drill_markup(l["script"]))))
    for lid, text in coach_lines().items(): jobs.append((lid, *COACH, to_say(text)))
    for lid, voice, rate, spoken in jobs:
            if not re.search(rf"^{re.escape(voice)}\s", installed, re.M): sys.exit(f"Voice not installed: {voice}")
            h = hashlib.sha1(f"{voice}|{rate}|{spoken}".encode()).hexdigest()[:12]
            fn = f"{lid}.m4a"
            path = os.path.join(OUT, fn)
            if old.get(lid, {}).get("h") == h and os.path.exists(path):
                manifest[lid] = old[lid]; kept += 1; continue
            with tempfile.NamedTemporaryFile(suffix=".aiff") as tmp:
                subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", tmp.name, spoken], check=True)
                subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "64000", tmp.name, path], check=True)
            manifest[lid] = {"url": f"audio/{fn}", "voice": voice, "h": h}; made += 1
            print(f"  {lid:8} {voice:9} {spoken[:60]}")
    with open(mf, "w", encoding="utf-8") as f:
        f.write("// Generated by tools/make_voice.py. Do not edit by hand.\nwindow.AUDIO_FILES = ")
        json.dump(manifest, f, ensure_ascii=False, indent=0)
        f.write(";\n")
    print(f"Done: {made} generated, {kept} unchanged, {len(manifest)} lines in audio/manifest.js")


if __name__ == "__main__":
    main()
