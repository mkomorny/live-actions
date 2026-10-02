// The fill engine — PURE: FillSpec -> Note[]. No SDK dependency, so it unit-tests
// with plain vitest and stays separable from the host wiring in extension.ts.
//
// v2 (pattern-bank engine). A fill is ASSEMBLED, not a single gesture:
//   (a) Genre bank (./patterns) — authentic GROOVE cells + FILL figures as data.
//   (b) Context — "groove": a bar of genre groove that breaks into the fill;
//       "fill": the whole length is the transitional figure(s).
//   (c) Technique — the structural archetype that produces the fill content
//       (a genre figure, an accelerating roll, a tom cascade, a build, …).
//   (d) Expressive render — ornaments (flam/drag/ruff), a velocity escalation
//       toward the downbeat, then swing + humanize (reused from rhythm.ts).
// The engine speaks in abstract DrumVoices; pitches are assigned only at the very
// end via the pad map, so the musical logic is independent of any kit layout.
import { humanize, swing, type Note } from "./rhythm.js";
import { DRUM_VOICES, GM_MAP, type DrumMap, type DrumVoice } from "./drumvoices.js";
import { GENRE_BANKS, type Figure, type GenreBank, type Ornament } from "./patterns.js";

export type Genre =
  // electronic
  | "melodicHouse"
  | "darkTechno"
  | "dnb"
  | "trap"
  | "breakbeat"
  | "ambient"
  // classic / acoustic
  | "rock"
  | "funk"
  | "jazz"
  | "metal"
  | "latin"
  | "hipHop"
  | "rnb"
  | "reggae"
  | "disco"
  | "pop";

export const GENRE_LABELS: Record<Genre, string> = {
  melodicHouse: "Melodic House",
  darkTechno: "Dark Techno",
  dnb: "Drum & Bass",
  trap: "Trap",
  breakbeat: "Breakbeat",
  ambient: "Ambient",
  rock: "Rock",
  funk: "Funk",
  jazz: "Jazz",
  metal: "Metal",
  latin: "Latin",
  hipHop: "Hip-Hop",
  rnb: "R&B / Soul",
  reggae: "Reggae",
  disco: "Disco",
  pop: "Pop",
};

/** Genres grouped for the dialog's category switcher. */
export const GENRE_GROUPS: { label: string; genres: Genre[] }[] = [
  { label: "Electronic", genres: ["melodicHouse", "darkTechno", "dnb", "trap", "breakbeat", "ambient"] },
  { label: "Acoustic", genres: ["rock", "funk", "jazz", "metal", "latin", "hipHop", "rnb", "reggae", "disco", "pop"] },
];

export type Technique =
  | "snareRoll"
  | "tomCascade"
  | "glitchStutter"
  | "buildUp"
  | "halfTimeDropIn"
  | "hatRun"
  | "ghostGroove";

export const TECHNIQUE_LABELS: Record<Technique, string> = {
  snareRoll: "Snare Roll",
  tomCascade: "Tom Cascade",
  glitchStutter: "Glitch / Stutter",
  buildUp: "Build-Up",
  halfTimeDropIn: "Half-Time Drop-In",
  hatRun: "Hat Run",
  ghostGroove: "Groove Fill",
};

/** How the fill relates to the surrounding bar (named FillMode to avoid clashing
 *  with protocol.FillContext, the host↔webview payload). */
export type FillMode = "groove" | "fill";
export const FILL_MODE_LABELS: Record<FillMode, string> = {
  groove: "Groove + fill",
  fill: "Fill only",
};

/** A fill's length in bars. Always explicit — never inferred (the SDK can't read
 *  timeline position), so the user picks ½ / 1 / 2 bars. */
export type FillLength = 0.5 | 1 | 2;

/**
 * The complete description of a fill to generate.
 */
export interface FillSpec {
  genre: Genre;
  technique: Technique;
  context: FillMode; // groove+fill bar vs fill-only
  lengthBars: FillLength;
  beatsPerBar: number; // 4 in 4/4; meter the host detected (Scene signature)
  intensity: number; // 0..1 — accel γ + the build-up curve + velocity ceiling
  density: number; // 0..1 — how many hits pack the fill
  swing: number; // 0..1 — swing pass (combined with the genre's baseline)
  humTiming: number; // 0..1 — timing jitter scale for rhythm.humanize
  humVel: number; // 0..1 — velocity jitter scale for rhythm.humanize
  seed: number; // deterministic; Reshuffle bumps it
}

/** Sensible defaults — a Melodic House groove fill, 1 bar, medium feel. */
export const DEFAULT_FILL_SPEC: FillSpec = {
  genre: "melodicHouse",
  technique: "ghostGroove",
  context: "groove",
  lengthBars: 1,
  beatsPerBar: 4,
  intensity: 0.6,
  density: 0.5,
  swing: 0,
  humTiming: 0.3,
  humVel: 0.4,
  seed: 1,
};

// An abstract, pre-pitch hit: a voice struck at a time with a velocity. The
// engine produces these; mapVoices() turns them into pitched Notes at the end.
export interface VoiceHit {
  voice: DrumVoice;
  startTime: number; // beats
  duration: number; // beats
  velocity: number; // 1..127
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const lerp = (a: number, b: number, t: number) => a + (b - a) * clamp(t, 0, 1);
const clampVel = (v: number) => clamp(Math.round(v), 1, 127);

/** Small deterministic PRNG (mulberry32), shared with the sibling generator.
 *  Returns floats in [0, 1). Same seed → same sequence → stable previews/tests. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Monotonic-increasing build-up curve over u ∈ [0,1]. `shape` (0..1, from
 * intensity) bends a straight line toward an exponential "late surge". Always
 * non-decreasing in u, so rendered velocities build toward the downbeat. Pure.
 */
export function buildupCurve(u: number, shape: number): number {
  const x = clamp(u, 0, 1);
  const gamma = lerp(1, 2.6, shape); // ≥1 ⇒ convex, monotonic increasing
  return Math.pow(x, gamma);
}

/**
 * Accelerating onset times for `n` hits across `len` beats: t_i = len·(i/n)^γ.
 * With γ < 1 the gaps SHRINK as i grows, so hits accelerate into the downbeat.
 * γ is driven by intensity and clamped strictly below 1. Returns n times in
 * [0, len). Pure.
 */
export function accelTimes(n: number, len: number, intensity: number, gammaJitter = 0): number[] {
  const gamma = clamp(0.9 - 0.5 * clamp(intensity, 0, 1) + gammaJitter, 0.35, 0.95);
  const out: number[] = [];
  for (let i = 0; i < n; i++) out.push(len * Math.pow(i / n, gamma));
  return out;
}

// ---- assembly helpers ------------------------------------------------------

/** Note length heuristic per voice (beats). */
function voiceDur(v: DrumVoice): number {
  switch (v) {
    case "kick":
      return 0.16;
    case "snare":
    case "clap":
    case "rim":
      return 0.12;
    case "lowTom":
    case "midTom":
    case "hiTom":
      return 0.2;
    case "closedHat":
    case "pedalHat":
      return 0.05;
    case "openHat":
      return 0.18;
    case "ride":
      return 0.22;
    case "crash":
      return 0.6;
    default:
      return 0.12;
  }
}

const pick = <T>(arr: readonly T[], rng: () => number): T => arr[Math.floor(rng() * arr.length)]!;

/** Expand a flam/drag/ruff into grace VoiceHits just before the main hit. */
function ornamentHits(h: VoiceHit, orn: Ornament): VoiceHit[] {
  const mk = (dt: number, vf: number): VoiceHit => ({
    voice: h.voice,
    startTime: Math.max(0, h.startTime - dt),
    duration: 0.03,
    velocity: clampVel(h.velocity * vf),
  });
  switch (orn) {
    case "flam":
      return [mk(0.045, 0.55)];
    case "drag":
      return [mk(0.09, 0.4), mk(0.05, 0.45)];
    case "ruff":
      return [mk(0.12, 0.34), mk(0.08, 0.4), mk(0.04, 0.46)];
    case "ghost":
      return [];
  }
}

/** Materialize a figure at a beat offset, scaling velocity + expanding ornaments. */
function place(figure: Figure, at: number, velScale: number): VoiceHit[] {
  const out: VoiceHit[] = [];
  for (const ph of figure.hits) {
    const vh: VoiceHit = {
      voice: ph.voice,
      startTime: at + ph.pos,
      duration: voiceDur(ph.voice),
      velocity: clampVel(ph.vel * velScale),
    };
    if (ph.orn) out.push(...ornamentHits(vh, ph.orn));
    out.push(vh);
  }
  return out;
}

/** Loop a genre groove cell to cover `beats`, at a slightly reduced velocity so
 *  the fill that follows it stands out. */
function layGroove(bank: GenreBank, beats: number, intensity: number, rng: () => number): VoiceHit[] {
  if (beats <= 1e-6 || !bank.grooves.length) return [];
  const cell = pick(bank.grooves, rng);
  const vs = lerp(0.78, 0.95, intensity);
  const out: VoiceHit[] = [];
  for (let t = 0; t < beats - 1e-6; t += cell.lengthBeats) {
    for (const ph of cell.hits) {
      if (t + ph.pos < beats - 1e-6) {
        out.push({ voice: ph.voice, startTime: t + ph.pos, duration: voiceDur(ph.voice), velocity: clampVel(ph.vel * vs) });
      }
    }
  }
  return out;
}

// ---- technique fills (each writes its content into [0, window)) ------------

/** Roll — accelerating run of one voice building into the downbeat, with ghost
 *  taps + an optional resolve voice on the last hit. Kept as ONE technique. */
function rollFill(spec: FillSpec, window: number, rng: () => number, voice: DrumVoice, resolveVoice?: DrumVoice): VoiceHit[] {
  const perBar = lerp(8, 30, spec.density);
  const n = Math.max(3, Math.round((perBar * window) / spec.beatsPerBar));
  const times = accelTimes(n, window, spec.intensity, (rng() - 0.5) * 0.12);
  const base = lerp(34, 58, spec.intensity);
  const peak = lerp(96, 124, spec.intensity);
  const hits: VoiceHit[] = times.map((t, i) => {
    const u = n > 1 ? i / (n - 1) : 1;
    const next = times[i + 1];
    const span = next !== undefined ? next - t : 0.12;
    return { voice, startTime: t, duration: clamp(span * 0.9, 0.02, 0.25), velocity: clampVel(lerp(base, peak, buildupCurve(u, spec.intensity))) };
  });
  const ghosts = Math.round(lerp(0, 3, spec.density));
  for (let g = 0; g < ghosts; g++) {
    const i = Math.floor(rng() * Math.max(1, Math.floor(n / 2)));
    const t = times[i];
    if (t !== undefined) hits.push({ voice, startTime: Math.max(0, t - 0.04), duration: 0.04, velocity: clampVel(lerp(18, 38, rng())) });
  }
  if (resolveVoice && hits.length) {
    const last = hits[hits.length - 1]!;
    last.voice = resolveVoice;
    last.duration = 0.18;
  }
  return hits;
}

/** Concatenate genre FILL figures (seeded, escalating in velocity) over [0, window). */
function figureFill(bank: GenreBank, window: number, intensity: number, rng: () => number): VoiceHit[] {
  const out: VoiceHit[] = [];
  let t = 0;
  let guard = 0;
  while (t < window - 1e-6 && guard++ < 32) {
    const remain = window - t;
    const fitting = bank.fills.filter((f) => f.lengthBeats <= remain + 1e-6);
    const choices = fitting.length ? fitting : bank.fills;
    const f = pick(choices, rng);
    const velScale = lerp(0.82, 1.06, t / Math.max(window, 1e-6)) * lerp(0.85, 1.05, intensity);
    out.push(...place(f, t, velScale));
    t += f.lengthBeats;
    if (f.lengthBeats > remain + 1e-6) break; // an oversized figure landed; stop
  }
  return out;
}

/** Tom Cascade — toms descending Hi→Mid→Low, accelerating, with a flam on the last. */
function cascadeFill(spec: FillSpec, window: number, rng: () => number): VoiceHit[] {
  const toms: DrumVoice[] = ["hiTom", "midTom", "lowTom"];
  const n = Math.max(4, Math.round((lerp(6, 16, spec.density) * window) / spec.beatsPerBar));
  const times = accelTimes(n, window, spec.intensity, (rng() - 0.5) * 0.1);
  const base = lerp(44, 62, spec.intensity);
  const peak = lerp(100, 124, spec.intensity);
  const hits: VoiceHit[] = times.map((t, i) => {
    const u = n > 1 ? i / (n - 1) : 1;
    const idx = clamp(Math.floor((i / n) * 3 + (rng() - 0.5) * 0.6), 0, 2);
    const next = times[i + 1];
    const span = next !== undefined ? next - t : 0.15;
    return { voice: toms[idx]!, startTime: t, duration: clamp(span * 0.9, 0.04, 0.3), velocity: clampVel(lerp(base, peak, buildupCurve(u, spec.intensity))) };
  });
  const last = hits[hits.length - 1];
  if (last) hits.push(...ornamentHits(last, "flam"));
  return hits;
}

/** Glitch / Stutter — 2–4 retrigger bursts of a voice at a fast fixed subdivision. */
function stutterFill(spec: FillSpec, bank: GenreBank, window: number, rng: () => number): VoiceHit[] {
  const fromBank = Array.from(new Set(bank.fills.flatMap((f) => f.hits.map((h) => h.voice))));
  const voices: DrumVoice[] = fromBank.length ? fromBank : ["snare", "closedHat"];
  const out: VoiceHit[] = [];
  const groups = 2 + Math.floor(rng() * 3);
  for (let g = 0; g < groups; g++) {
    const start = rng() * (window * 0.85);
    const voice = pick(voices, rng);
    const reps = 3 + Math.floor(rng() * lerp(2, 6, spec.density));
    const div = 0.25 / (1 + Math.floor(rng() * 3)); // 16th / 32nd / 48th
    const bv = lerp(54, 112, rng());
    for (let r = 0; r < reps; r++) {
      const t = start + r * div;
      if (t >= window) break;
      out.push({ voice, startTime: t, duration: Math.max(0.02, div * 0.8), velocity: clampVel(bv * (1 - r * 0.04)) });
    }
  }
  if (out.length < 2) {
    out.push({ voice: "snare", startTime: 0, duration: 0.1, velocity: 90 });
    out.push({ voice: "snare", startTime: Math.min(window * 0.5, window - 0.1), duration: 0.1, velocity: 110 });
  }
  return out;
}

/** Build-Up — a genre fill (or roll) under a kick pulse rising on every beat. */
function buildFill(spec: FillSpec, bank: GenreBank, window: number, rng: () => number): VoiceHit[] {
  const dense: FillSpec = { ...spec, density: clamp(spec.density * 1.1 + 0.1, 0, 1) };
  const out = bank.fills.length ? figureFill(bank, window, 1, rng) : rollFill(dense, window, rng, "snare");
  for (let b = 0; b < window - 1e-6; b += 1) {
    const u = b / Math.max(1, window);
    out.push({ voice: "kick", startTime: b, duration: 0.12, velocity: clampVel(lerp(70, 116, u)) });
  }
  return out;
}

/** Half-Time Drop-In — kick on 1, big (flammed) snare on the half, accel pickup. */
function halfTimeFill(spec: FillSpec, window: number): VoiceHit[] {
  const hits: VoiceHit[] = [];
  hits.push({ voice: "kick", startTime: 0, duration: 0.14, velocity: 116 });
  const bigSnare: VoiceHit = { voice: "snare", startTime: window / 2, duration: 0.16, velocity: 122 };
  hits.push(...ornamentHits(bigSnare, "flam"), bigSnare);
  if (window >= 4) hits.push({ voice: "kick", startTime: window * 0.75, duration: 0.12, velocity: 104 });
  const pickupStart = Math.max(window / 2 + 0.25, window - 1);
  const span = window - pickupStart;
  if (span > 0.1) {
    const n = Math.max(2, Math.round(lerp(2, 6, spec.density)));
    accelTimes(n, span, spec.intensity).forEach((t, i) => {
      const u = n > 1 ? i / (n - 1) : 1;
      hits.push({ voice: "snare", startTime: pickupStart + t, duration: 0.06, velocity: clampVel(lerp(56, 118, u)) });
    });
  }
  return hits;
}

/** The fill content for the chosen technique, written into [0, window). */
function techniqueFill(spec: FillSpec, bank: GenreBank, window: number, rng: () => number): VoiceHit[] {
  switch (spec.technique) {
    case "snareRoll":
      return rollFill(spec, window, rng, "snare");
    case "hatRun":
      return rollFill(spec, window, rng, "closedHat", "openHat").map((h) => ({ ...h, velocity: clampVel(h.velocity * 0.8) }));
    case "tomCascade":
      return cascadeFill(spec, window, rng);
    case "glitchStutter":
      return stutterFill(spec, bank, window, rng);
    case "buildUp":
      return buildFill(spec, bank, window, rng);
    case "halfTimeDropIn":
      return halfTimeFill(spec, window);
    case "ghostGroove":
    default:
      return bank.fills.length ? figureFill(bank, window, spec.intensity, rng) : rollFill(spec, window, rng, "snare");
  }
}

/** A resolving cymbal on the fill's final hit (unless one is already there). */
function addResolve(hits: VoiceHit[], bank: GenreBank, len: number, intensity: number): void {
  if (!hits.length) return;
  const last = Math.min(hits.reduce((m, h) => Math.max(m, h.startTime), 0), len - 1e-4);
  const hasCymbal = hits.some((h) => (h.voice === "crash" || h.voice === "ride") && h.startTime >= last - 0.05);
  if (!hasCymbal) hits.push({ voice: bank.resolve, startTime: last, duration: voiceDur(bank.resolve), velocity: clampVel(lerp(104, 124, intensity)) });
}

/** Resolve abstract voices to pitched Notes via the pad map (GM + overrides). Pure. */
export function mapVoices(hits: VoiceHit[], map: DrumMap): Note[] {
  return hits.map((h) => ({
    pitch: map[h.voice],
    startTime: h.startTime,
    duration: h.duration,
    velocity: h.velocity,
  }));
}

/**
 * Generate a fill as abstract VoiceHits (pre-pitch). Pure & deterministic for a
 * given seed. Assembles [groove → fill] (or just fill) from the genre bank, adds
 * the resolving cymbal, then clamps/sorts. Times are beats, 0-based.
 */
export function generateFillVoices(spec: FillSpec): VoiceHit[] {
  const len = spec.lengthBars * spec.beatsPerBar;
  const bank = GENRE_BANKS[spec.genre];
  const rng = mulberry32(spec.seed);

  // The tail `window` beats are the fill; any groove precedes it (groove context).
  const window = spec.context === "fill" ? len : len <= 2 ? len : len / 2;
  const grooveBeats = Math.max(0, len - window);

  const out: VoiceHit[] = [];
  if (grooveBeats > 1e-6) out.push(...layGroove(bank, grooveBeats, spec.intensity, rng));
  for (const h of techniqueFill(spec, bank, window, rng)) {
    out.push({ ...h, startTime: h.startTime + grooveBeats });
  }
  addResolve(out, bank, len, spec.intensity);

  return out
    .filter((h) => h.startTime >= 0 && h.startTime < len)
    .map((h) => ({ ...h, velocity: clampVel(h.velocity) }))
    .sort((a, b) => a.startTime - b.startTime || a.voice.localeCompare(b.voice));
}

/**
 * Generate a fill as pitched, humanized, swung Notes ready for a Drum Rack clip.
 * `map` overrides the GM defaults per voice. Pure & deterministic for a seed.
 */
export function generateFill(spec: FillSpec, map: DrumMap = GM_MAP): Note[] {
  const merged: DrumMap = { ...GM_MAP, ...map };
  const bank = GENRE_BANKS[spec.genre];
  const hits = generateFillVoices(spec);
  let notes = mapVoices(hits, merged);
  // Final expressive pass: swing (user amount, floored by the genre's feel), then
  // humanize timing/velocity. Both reused unchanged from rhythm.ts.
  notes = swing(notes, Math.max(spec.swing, bank.swing));
  notes = humanize(notes, spec.humTiming * 0.04, Math.round(spec.humVel * 16));
  return notes.sort((a, b) => a.startTime - b.startTime || a.pitch - b.pitch);
}

// Re-export so the host/webview can import the voice vocabulary from one place.
export { DRUM_VOICES, GM_MAP, type DrumMap, type DrumVoice };
