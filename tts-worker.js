/* Makes lines in the lesson voice (Kokoro, via kokoro-js) on a background thread, so the app never freezes while
   it works. The page sends { id, parts: [{t:"text"} | {ms:650}], voice, speed }; the worker answers { id, wav }
   (16-bit mono WAV, 150 ms lead-in, same loudness as tools/make_voice.py) or { id, error }.
   Repeated phrases in the same voice are made once. */
let tts = null;
const seg = new Map();

async function model() {
  if (!tts) {
    const { KokoroTTS } = await import('https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm');
    tts = await KokoroTTS.from_pretrained('onnx-community/Kokoro-82M-v1.0-ONNX', { dtype: 'q8', device: 'wasm' });
  }
  return tts;
}

function wav(pcm, sr) {
  let sum = 0, cnt = 0, peak = 0;
  for (const x of pcm) { const a = Math.abs(x); if (a > peak) peak = a; if (a > 0.01) { sum += x * x; cnt++; } }
  const g = cnt ? Math.min(0.07 / Math.sqrt(sum / cnt), 0.9 / (peak || 1)) : 1, n = pcm.length;
  const v = new DataView(new ArrayBuffer(44 + n * 2)), str = (o, t) => [...t].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  str(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); str(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); str(36, 'data'); v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, pcm[i] * g)) * 32767, true);
  return v.buffer;
}

self.onmessage = async e => {
  const { id, parts, voice, speed } = e.data;
  try {
    const t = await model(); let sr = 24000; const out = [new Float32Array(3600)];   // 150 ms before the first word
    for (const p of parts) {
      if (p.ms) { out.push(new Float32Array(Math.round(sr * p.ms / 1000))); continue; }
      const k = p.t + '|' + voice + '|' + speed;
      if (!seg.has(k)) { const a = await t.generate(p.t, { voice, speed }); seg.set(k, [a.audio, a.sampling_rate]); }
      const [au, r] = seg.get(k); sr = r; out.push(au);
    }
    const n = out.reduce((x, a) => x + a.length, 0), pcm = new Float32Array(n); let o = 0;
    for (const a of out) { pcm.set(a, o); o += a.length; }
    const buf = wav(pcm, sr); self.postMessage({ id, wav: buf }, [buf]);
  } catch (err) { self.postMessage({ id, error: String(err && err.message || err) }); }
};
