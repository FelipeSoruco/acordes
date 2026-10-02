/* Motor de acordes: port a JS de acordes/*.py (detección, simplificación, digitaciones). */
const NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
const NOTE_INDEX = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
const QUALITIES = {
  maj: [0, 4, 7], min: [0, 3, 7], "7": [0, 4, 7, 10], maj7: [0, 4, 7, 11], min7: [0, 3, 7, 10],
  sus2: [0, 2, 7], sus4: [0, 5, 7], dim: [0, 3, 6], aug: [0, 4, 8],
};
const SUFFIX = { maj: "", min: "m", "7": "7", maj7: "maj7", min7: "m7", sus2: "sus2", sus4: "sus4", dim: "dim", aug: "aug" };
const PARSE = {
  "": "maj", maj: "maj", M: "maj", "5": "maj", "6": "maj", add9: "maj", add2: "maj", "69": "maj",
  m: "min", min: "min", "-": "min", m6: "min", madd9: "min", "7": "7", "9": "7", "11": "7", "13": "7",
  "7sus4": "7", maj7: "maj7", M7: "maj7", maj9: "maj7", m7: "min7", min7: "min7", "-7": "min7",
  m9: "min7", m11: "min7", sus: "sus4", sus4: "sus4", sus2: "sus2", dim: "dim", dim7: "dim", o: "dim",
  m7b5: "dim", aug: "aug", "+": "aug",
};
const mod12 = (n) => ((n % 12) + 12) % 12;
const chord = (root, quality = "maj") => ({ root: mod12(root), quality });
const chordName = (c) => NOTE_NAMES[c.root] + SUFFIX[c.quality];
const chordKey = (c) => (c ? c.root + c.quality : "N");
const sameChord = (a, b) => chordKey(a) === chordKey(b);
const transpose = (c, n) => chord(c.root + n, c.quality);

function parseChord(text) {
  const m = /^([A-G])([#b]?)([^/]*)(?:\/([A-G][#b]?))?$/.exec(text.trim());
  if (!m) throw new Error("Acorde no reconocido: " + text);
  const q = PARSE[m[3]];
  if (q === undefined) throw new Error("Calidad de acorde no reconocida: " + text);
  return chord(NOTE_INDEX[m[1]] + ({ "#": 1, b: -1, "": 0 })[m[2]], q);
}

/* ---------- texto <-> beats ---------- */
function parseTextChart(text, beatsPerBar = 4) {
  let title = "";
  const bars = [];
  for (let line of text.split("\n")) {
    line = line.trim();
    if (!line) continue;
    if (line.startsWith("#")) { title = title || line.replace(/^#+\s*/, ""); continue; }
    for (const bar of line.split("|")) {
      const tokens = bar.trim().split(/\s+/).filter(Boolean);
      if (tokens.length) bars.push(tokens);
    }
  }
  const beats = [];
  for (const tokens of bars) {
    const cs = tokens.map((t) => (["N", "N.C.", "-"].includes(t) ? null : parseChord(t)));
    for (let i = 0; i < beatsPerBar; i++) beats.push(cs[Math.floor((i * cs.length) / beatsPerBar)]);
  }
  return { beats, beatsPerBar, title };
}

function chartToText(beats, beatsPerBar = 4, title = "") {
  const lines = title ? ["# " + title] : [];
  const bars = [];
  for (let i = 0; i < beats.length; i += beatsPerBar) {
    const runs = [];
    for (const c of beats.slice(i, i + beatsPerBar)) {
      if (!runs.length || !sameChord(runs[runs.length - 1], c)) runs.push(c);
    }
    bars.push(runs.slice(0, beatsPerBar).map((c) => (c ? chordName(c) : "N.C.")).join(" "));
  }
  for (let i = 0; i < bars.length; i += 4) lines.push("| " + bars.slice(i, i + 4).join(" | ") + " |");
  return lines.join("\n");
}

/* ---------- digitaciones ---------- */
const parseFrets = (s) => (s.includes(",") ? s.split(",") : s.split("")).map((p) => (p === "x" ? null : +p));
const OPEN = {
  C: "x32010", Cmaj7: "x32000", C7: "x32310", D: "xx0232", Dm: "xx0231", D7: "xx0212", Dmaj7: "xx0222",
  Dm7: "xx0211", Dsus4: "xx0233", Dsus2: "xx0230", E: "022100", Em: "022000", E7: "020100", Em7: "022030",
  Emaj7: "021100", Esus4: "022200", G: "320003", G7: "320001", Gmaj7: "320002", A: "x02220", Am: "x02210",
  A7: "x02020", Am7: "x02010", Amaj7: "x02120", Asus2: "x02200", Asus4: "x02230", B7: "x21202",
};
const EASY = { F: "xx3211", Fmaj7: "xx3210" };
const E_SHAPE = { maj: [0, 2, 2, 1, 0, 0], min: [0, 2, 2, 0, 0, 0], "7": [0, 2, 0, 1, 0, 0], min7: [0, 2, 0, 0, 0, 0],
  maj7: [0, 2, 1, 1, 0, 0], sus4: [0, 2, 2, 2, 0, 0], sus2: [0, 2, 4, 4, 0, 0], dim: [0, 1, 2, 0, null, null], aug: [0, 3, 2, 1, 1, 0] };
const A_SHAPE = { maj: [null, 0, 2, 2, 2, 0], min: [null, 0, 2, 2, 1, 0], "7": [null, 0, 2, 0, 2, 0], min7: [null, 0, 2, 0, 1, 0],
  maj7: [null, 0, 2, 1, 2, 0], sus4: [null, 0, 2, 2, 3, 0], sus2: [null, 0, 2, 2, 0, 0], dim: [null, 0, 1, 2, 1, null], aug: [null, 0, 3, 2, 2, 1] };
const OPEN_SHAPES = Object.fromEntries(Object.entries(OPEN).map(([n, s]) => [chordKey(parseChord(n)), parseFrets(s)]));
const EASY_SHAPES = Object.fromEntries(Object.entries(EASY).map(([n, s]) => [chordKey(parseChord(n)), parseFrets(s)]));

function openDifficulty(c) {
  let d = 1;
  if (["7", "min7", "maj7", "sus2", "sus4"].includes(c.quality)) d += 0.3;
  if (["G", "C", "G7", "Cmaj7", "Dmaj7"].includes(chordName(c))) d += 0.4;
  return d;
}
function candidateShapes(c) {
  const out = [], k = chordKey(c);
  if (OPEN_SHAPES[k]) out.push({ chord: c, frets: OPEN_SHAPES[k], barre: false, difficulty: openDifficulty(c) });
  if (EASY_SHAPES[k]) out.push({ chord: c, frets: EASY_SHAPES[k], barre: false, difficulty: 2 });
  for (const [table, stringRoot] of [[E_SHAPE, 4], [A_SHAPE, 9]]) {
    if (!table[c.quality]) continue;
    let fret = mod12(c.root - stringRoot);
    if (fret === 0 && OPEN_SHAPES[k]) continue;
    fret = fret || 12;
    out.push({ chord: c, frets: table[c.quality].map((o) => (o === null ? null : o + fret)), barre: true, difficulty: 3 + 0.1 * fret });
  }
  return out;
}
const SHAPE_CACHE = new Map();
function bestShape(c) {
  const k = chordKey(c);
  if (!SHAPE_CACHE.has(k)) SHAPE_CACHE.set(k, candidateShapes(c).reduce((a, b) => (b.difficulty < a.difficulty ? b : a)));
  return SHAPE_CACHE.get(k);
}

/* ---------- simplificación ---------- */
const LEVELS = {
  1: { maj7: "maj", "7": "maj", min7: "min", sus2: "maj", sus4: "maj", dim: "min", aug: "maj" },
  2: { maj7: "maj", dim: "min", aug: "maj" },
  3: {},
};
const MIN_BEATS = { 1: 2, 2: 1, 3: 1 };

function reduceChord(c, level) {
  return c ? chord(c.root, LEVELS[level][c.quality] || c.quality) : null;
}
function absorbShort(beats, minBeats) {
  if (minBeats <= 1 || !beats.length) return beats;
  const out = beats.slice();
  for (let changed = true; changed;) {
    changed = false;
    const runs = [];
    for (let i = 0; i < out.length;) {
      let j = i;
      while (j < out.length && sameChord(out[j], out[i])) j++;
      runs.push([i, j]);
      i = j;
    }
    for (let k = 0; k < runs.length; k++) {
      const [a, b] = runs[k];
      if (b - a < minBeats && runs.length > 1) {
        const src = k > 0 ? out[runs[k - 1][0]] : out[runs[k + 1][0]];
        for (let x = a; x < b; x++) out[x] = src;
        changed = true;
        break;
      }
    }
  }
  return out;
}
function costFor(beats, shift) {
  let total = 0, n = 0;
  for (const c of beats) if (c) { total += bestShape(transpose(c, -shift)).difficulty; n++; }
  return n ? total / n : 0;
}
function simplify(beats, level = 2, allowCapo = true) {
  const reduced = absorbShort(beats.map((c) => reduceChord(c, level)), MIN_BEATS[level]);
  let capo = 0, best = Infinity;
  for (let k = 0; k <= (allowCapo ? 7 : 0); k++) {
    const cost = Math.round(costFor(reduced, k) * 1e6) / 1e6;
    if (cost < best) { best = cost; capo = k; }
  }
  return { beats: reduced.map((c) => (c ? transpose(c, -capo) : null)), capo, difficulty: costFor(reduced, capo) };
}

/* ---------- detección desde audio ---------- */
const PRIOR = { maj: 0, min: 0, "7": 0.06, min7: 0.06, maj7: 0.08, sus2: 0.1, sus4: 0.1, dim: 0.1, aug: 0.12 };
const TEMPLATES = (() => {
  const chords = [], rows = [], prior = [];
  for (const [q, iv] of Object.entries(QUALITIES)) {
    for (let root = 0; root < 12; root++) {
      const v = new Float64Array(12);
      for (const i of iv) v[(root + i) % 12] = 1;
      v[root] += 0.5;
      const n = Math.hypot(...v);
      rows.push(v.map((x) => x / n)); chords.push(chord(root, q)); prior.push(PRIOR[q]);
    }
  }
  return { chords, rows, prior };
})();

function viterbiChords(frames, energies, switchPenalty = 1.2, beta = 12) {
  // frames: array de Float64Array(12) (un chroma por beat)
  const { chords, rows, prior } = TEMPLATES, K = chords.length, T = frames.length;
  if (!T) return [];
  const norms = frames.map((f) => Math.hypot(...f)), energy = energies || norms;
  const maxE = Math.max(...energy);
  const obs = frames.map((f, t) => {
    const n = Math.max(norms[t], 1e-9);
    return rows.map((r, k) => { let s = 0; for (let i = 0; i < 12; i++) s += r[i] * f[i]; return beta * (s / n - prior[k]); });
  });
  const delta = [Float64Array.from(obs[0])], back = [new Int32Array(K)];
  for (let t = 1; t < T; t++) {
    const prev = delta[t - 1];
    let bi = 0;
    for (let k = 1; k < K; k++) if (prev[k] > prev[bi]) bi = k;
    const sw = prev[bi] - switchPenalty, d = new Float64Array(K), b = new Int32Array(K);
    for (let k = 0; k < K; k++) {
      if (prev[k] >= sw) { d[k] = prev[k] + obs[t][k]; b[k] = k; } else { d[k] = sw + obs[t][k]; b[k] = bi; }
    }
    delta.push(d); back.push(b);
  }
  const path = [0];
  const last = delta[T - 1];
  for (let k = 1; k < K; k++) if (last[k] > last[path[0]]) path[0] = k;
  for (let t = T - 1; t > 0; t--) path.push(back[t][path[path.length - 1]]);
  path.reverse();
  return path.map((k, t) => (energy[t] < 0.05 * maxE ? null : chords[k]));
}

function makeFFT(n) {
  const rev = new Uint32Array(n), bits = Math.log2(n);
  for (let i = 0; i < n; i++) { let r = 0; for (let b = 0; b < bits; b++) r |= ((i >> b) & 1) << (bits - 1 - b); rev[i] = r; }
  const cos = new Float64Array(n / 2), sin = new Float64Array(n / 2);
  for (let i = 0; i < n / 2; i++) { cos[i] = Math.cos((2 * Math.PI * i) / n); sin[i] = -Math.sin((2 * Math.PI * i) / n); }
  return (re, im) => {
    for (let i = 0; i < n; i++) { const j = rev[i]; if (j > i) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
    for (let size = 2; size <= n; size <<= 1) {
      const half = size >> 1, step = n / size;
      for (let s = 0; s < n; s += size) {
        for (let k = 0; k < half; k++) {
          const a = s + k, b = a + half, wr = cos[k * step], wi = sin[k * step];
          const xr = re[b] * wr - im[b] * wi, xi = re[b] * wi + im[b] * wr;
          re[b] = re[a] - xr; im[b] = im[a] - xi; re[a] += xr; im[a] += xi;
        }
      }
    }
  };
}

const FRAME = 4096, HOP = 512;
async function analyze(samples, sr, onProgress) {
  const fft = makeFFT(FRAME), win = new Float64Array(FRAME);
  for (let i = 0; i < FRAME; i++) win[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / FRAME);
  const nFrames = Math.max(0, Math.floor((samples.length - FRAME) / HOP) + 1);
  const binPc = new Int8Array(FRAME / 2), binW = new Float64Array(FRAME / 2);
  for (let k = 1; k < FRAME / 2; k++) {
    const f = (k * sr) / FRAME;
    if (f < 65 || f > 2000) { binPc[k] = -1; continue; }
    const midi = 69 + 12 * Math.log2(f / 440), r = Math.round(midi);
    if (Math.abs(midi - r) > 0.35) { binPc[k] = -1; continue; }
    binPc[k] = mod12(r); binW[k] = 1 / (1 + Math.max(0, midi - 60) / 24);
  }
  const chroma = new Float64Array(nFrames * 12), flux = new Float64Array(nFrames), energy = new Float64Array(nFrames);
  const re = new Float64Array(FRAME), im = new Float64Array(FRAME), prev = new Float64Array(FRAME / 2);
  for (let t = 0; t < nFrames; t++) {
    const off = t * HOP;
    for (let i = 0; i < FRAME; i++) { re[i] = samples[off + i] * win[i]; im[i] = 0; }
    fft(re, im);
    let fl = 0, en = 0;
    for (let k = 1; k < FRAME / 2; k++) {
      const mag = Math.sqrt(Math.hypot(re[k], im[k]));  // compresión
      const d = mag - prev[k];
      if (d > 0 && k < 600) fl += d;
      prev[k] = mag;
      if (binPc[k] >= 0) { chroma[t * 12 + binPc[k]] += mag * binW[k]; en += mag; }
    }
    flux[t] = fl; energy[t] = en;
    if (t % 150 === 0) { onProgress && onProgress(t / nFrames); await new Promise((r) => setTimeout(r, 0)); }
  }
  return { chroma, flux, energy, nFrames, hopSec: HOP / sr };
}

function estimateBeats(flux, hopSec) {
  const n = flux.length, f = new Float64Array(n);
  const W = Math.round(0.5 / hopSec);  // quita la media local
  for (let t = 0; t < n; t++) {
    let s = 0, c = 0;
    for (let i = Math.max(0, t - W); i < Math.min(n, t + W); i++) { s += flux[i]; c++; }
    f[t] = Math.max(0, flux[t] - s / c);
  }
  let bestLag = 0, bestScore = -1, tempo = 0;
  for (let bpm = 60; bpm <= 180; bpm += 0.5) {
    const lag = 60 / (bpm * hopSec), lo = Math.floor(lag), frac = lag - lo;
    let s = 0;
    for (let t = 0; t + lo + 1 < n; t++) s += f[t] * (f[t + lo] * (1 - frac) + f[t + lo + 1] * frac);
    s *= Math.exp(-0.5 * (Math.log2(bpm / 105) / 0.8) ** 2);
    if (s > bestScore) { bestScore = s; bestLag = lag; tempo = bpm; }
  }
  // seguimiento por programación dinámica (Ellis): premia onsets y periodo estable
  let sd = 0;
  for (let t = 0; t < n; t++) sd += f[t] * f[t];
  sd = Math.sqrt(sd / n) || 1;
  const cum = new Float64Array(n), from = new Int32Array(n).fill(-1), tau = bestLag, tight = 100;
  for (let t = 0; t < n; t++) {
    let best = 0, arg = -1;
    for (let p = Math.max(0, Math.round(t - 2 * tau)); p <= Math.round(t - tau / 2); p++) {
      const sc = cum[p] - tight * Math.log((t - p) / tau) ** 2;
      if (arg < 0 || sc > best) { best = sc; arg = p; }
    }
    cum[t] = f[t] / sd + (arg >= 0 ? best : 0);
    from[t] = arg;
  }
  let end = Math.max(0, n - Math.round(tau));
  for (let t = end; t < n; t++) if (cum[t] > cum[end]) end = t;
  const beats = [];
  for (let t = end; t >= 0; t = from[t]) { beats.push(t); if (from[t] < 0) break; }
  beats.reverse();
  while (beats[0] - tau >= 0) beats.unshift(Math.round(beats[0] - tau));
  return { beats, tempo };
}

function alignBars(chords, beatsPerBar) {
  if (chords.length < 2 * beatsPerBar + beatsPerBar) return chords;
  let bestO = 0, bestS = -1;
  for (let o = 0; o < beatsPerBar; o++) {
    let s = 0;
    for (let i = 1; i < chords.length; i++)
      if ((i - o) % beatsPerBar === 0 && !sameChord(chords[i], chords[i - 1])) s++;
    if (s > bestS) { bestS = s; bestO = o; }
  }
  const pad = (beatsPerBar - bestO) % beatsPerBar;  // completa el primer compás
  return Array(pad).fill(chords[0]).concat(chords);
}

async function detectChords(samples, sr, beatsPerBar = 4, onProgress) {
  const a = await analyze(samples, sr, onProgress);
  const { beats, tempo } = estimateBeats(a.flux, a.hopSec);
  const frames = [], energies = [];
  for (let b = 0; b + 1 < beats.length; b++) {
    const v = new Float64Array(12);
    let e = 0;
    for (let t = beats[b]; t < beats[b + 1] && t < a.nFrames; t++) {
      let n = 0;
      for (let i = 0; i < 12; i++) n += a.chroma[t * 12 + i] ** 2;
      n = Math.sqrt(n) || 1;
      const w = 1;
      e += a.energy[t];
      for (let i = 0; i < 12; i++) v[i] += (a.chroma[t * 12 + i] / n) * w;
    }
    frames.push(v); energies.push(e / (beats[b + 1] - beats[b]));
  }
  const chords = alignBars(viterbiChords(frames, energies), beatsPerBar);
  return { beats: chords, tempo, beatsPerBar };
}

/* ---------- importar una cifra pegada (acordes sobre la letra) ---------- */
function importCifra(text) {
  const out = [], pending = [];
  const flush = () => {
    for (let i = 0; i < pending.length; i += 4) out.push("| " + pending.slice(i, i + 4).join(" | ") + " |");
    pending.length = 0;
  };
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const sec = /^\[([^\]]+)\]/.exec(line) || /^(intro|verso|estrofa|refr[aã]o|coro|estribillo|ponte|puente|solo|final|outro|pre-?coro)\b[^a-z]*$/i.exec(line);
    if (sec) { flush(); out.push("# " + sec[1].trim()); continue; }
    if (/^(tom|capo|cejilla|afina)/i.test(line)) continue;
    const tokens = line.replace(/[|()\[\]]/g, " ").replace(/\b\d+\s*x\b|\bx\s*\d+\b/gi, " ").split(/\s+/).filter(Boolean);
    if (!tokens.length) continue;
    try { for (const t of tokens) parseChord(t); } catch { continue; }  // línea de letra
    pending.push(...tokens);
  }
  flush();
  if (!out.some((l) => l.startsWith("|"))) throw new Error("No encontré acordes en el texto pegado.");
  return out.join("\n");
}

if (typeof module !== "undefined") module.exports = { importCifra, analyze, estimateBeats, parseChord, parseTextChart, chartToText, simplify, bestShape, candidateShapes, chordName, detectChords, viterbiChords, chord };
