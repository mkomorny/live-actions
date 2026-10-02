// Pure chord-rhythm + voicing transforms for MIDI clips.
//
// This module intentionally has NO dependency on @ableton-extensions/sdk so it
// can be unit-tested with plain vitest on any Node, and so the musical logic
// stays separable from the host wiring in extension.ts. The `Note` type below
// is structurally compatible with the SDK's `NoteDescription`, so the SDK's
// `MidiClip.notes` array can be passed straight in and the result assigned back.
//
// Conventions (v1):
//   - Times are in BEATS (same as the SDK).
//   - Assumes 4/4 (beatsPerBar = 4). Time-signature awareness is a v1.1 TODO.
//   - Chords are detected by clustering notes that share an onset, then reduced
//     to ONE chord per bar (the first chord in each bar wins). This fits a
//     one-chord-per-bar progression like Am–Dm–Em–Am; denser inputs are
//     simplified — documented, not silent magic.
//   - "Vary across phrase repetitions" is deterministic: a phrase is 4 bars,
//     and even/odd phrases use slightly different motifs. No RNG.

export interface Note {
  pitch: number; // MIDI note number
  startTime: number; // beats
  duration: number; // beats
  velocity?: number;
  muted?: boolean;
  probability?: number;
  releaseVelocity?: number;
  selected?: boolean;
  velocityDeviation?: number;
}

export const BEATS_PER_BAR = 4;
const ONSET_TOLERANCE = 0.125; // notes within an 1/32 of each other = one chord

export type RhythmStrategy =
  | "original"
  | "charleston"
  | "anticipation"
  | "slowStabs"
  | "sustainedMovingTop"
  | "arpeggiate";

export const STRATEGY_LABELS: Record<RhythmStrategy, string> = {
  original: "Keep timing",
  charleston: "Charleston",
  anticipation: "Anticipation",
  slowStabs: "Slow Harmonic + Stabs",
  sustainedMovingTop: "Sustained + Moving Top",
  arpeggiate: "Arpeggiate",
};

// Direction an arpeggio walks the chord's pitches across its span.
export type ArpDirection = "up" | "down" | "updown";

export const ARP_LABELS: Record<ArpDirection, string> = {
  up: "Up",
  down: "Down",
  updown: "Up & Down",
};

// A musical scale, mirroring what Live's `song` exposes (rootNote 0–11 +
// scaleIntervals). Used to keep melodic motion (moving top voice, arps) in key.
export interface Scale {
  root: number; // 0–11 pitch class of the tonic
  intervals: number[]; // semitone offsets from the root, ascending (e.g. natural minor [0,2,3,5,7,8,10])
}

// Voicing is an axis independent of rhythm: it re-spaces a chord's pitches and
// composes with any RhythmStrategy. "close" leaves the detected voicing as-is.
export type VoicingStyle = "close" | "drop2" | "drop24" | "spread" | "rootless";

export const VOICING_LABELS: Record<VoicingStyle, string> = {
  close: "Close (as-is)",
  drop2: "Drop-2",
  drop24: "Drop-2 & 4",
  spread: "Spread (open)",
  rootless: "Rootless",
};

/**
 * Re-voice an ascending, de-duplicated set of pitches. Pure pitch → pitch.
 *   - close:    identity.
 *   - drop2:    lower the 2nd voice from the top by an octave (the classic
 *               drop-2 — fuller, wider downward). Needs ≥2 pitches.
 *   - drop24:   lower the 2nd AND 4th voices from the top an octave — the very
 *               open drop-2-&-4 spread used for lush piano/guitar voicings.
 *               Needs ≥4 voices (a 7th chord); smaller chords are left as-is.
 *   - spread:   open voicing — raise the 2nd voice from the bottom by an octave
 *               so the inner voice sits on top (brighter, wider upward). Needs ≥3.
 *   - rootless: drop the root (lowest voice) so a bass instrument can imply it —
 *               the jazz-comping shell. Only meaningful on 7ths+ (≥4 voices); on
 *               a triad it would leave a bare 3rd+5th, so triads are left as-is.
 * Result is re-sorted ascending and de-duplicated; if a shift would collide or
 * the chord is too small for the move, the input is returned unchanged.
 */
export function revoice(pitches: number[], style: VoicingStyle): number[] {
  const asc = [...new Set(pitches)].sort((a, b) => a - b);
  if (style === "close" || asc.length < 2) return asc;

  const next = [...asc];
  if (style === "drop2") {
    const i = asc.length - 2; // 2nd from top
    next[i] = asc[i]! - 12; // down an octave
  } else if (style === "drop24") {
    if (asc.length < 4) return asc; // need 4 voices for two downward drops
    next[asc.length - 2] = asc[asc.length - 2]! - 12; // 2nd from top
    next[asc.length - 4] = asc[asc.length - 4]! - 12; // 4th from top
  } else if (style === "spread") {
    if (asc.length < 3) return asc; // need an inner voice to open up
    next[1] = asc[1]! + 12; // 2nd from bottom, up an octave
  } else if (style === "rootless") {
    if (asc.length < 4) return asc; // shell voicing only meaningful on 7ths+
    next.shift(); // drop the root
  }
  return [...new Set(next)].sort((a, b) => a - b);
}

/** Pitch classes (0–11) belonging to a scale, de-duped. */
function scalePitchClasses(scale: Scale): number[] {
  return [...new Set(scale.intervals.map((i) => (((scale.root + i) % 12) + 12) % 12))].sort(
    (a, b) => a - b,
  );
}

/**
 * Snap a MIDI pitch to the nearest pitch belonging to the scale. Pure.
 * Searches ±6 semitones; ties (equal distance up vs down) resolve upward.
 * An empty scale (no intervals) returns the pitch unchanged.
 */
export function snapToScale(pitch: number, scale: Scale): number {
  const pcs = scalePitchClasses(scale);
  if (!pcs.length) return pitch;
  let best = pitch;
  let bestDist = Infinity;
  for (let d = -6; d <= 6; d++) {
    const pc = (((pitch + d) % 12) + 12) % 12;
    if (!pcs.includes(pc)) continue;
    const dist = Math.abs(d) - (d > 0 ? 1e-3 : 0); // tie → prefer up
    if (dist < bestDist) {
      bestDist = dist;
      best = pitch + d;
    }
  }
  return best;
}

/**
 * Move a pitch by N scale steps (signed; negative = down), landing on scale
 * tones and crossing octaves correctly. Off-scale inputs are first snapped.
 * Pure. An empty scale returns the pitch unchanged.
 */
export function scaleStep(pitch: number, steps: number, scale: Scale): number {
  const pcs = scalePitchClasses(scale);
  if (!pcs.length) return pitch;
  const snapped = snapToScale(pitch, scale);
  if (steps === 0) return snapped;
  const pc = ((snapped % 12) + 12) % 12;
  const degree = Math.max(0, pcs.indexOf(pc));
  const n = pcs.length;
  const target = degree + steps;
  const octave = Math.floor(snapped / 12) + Math.floor(target / n);
  const idx = ((target % n) + n) % n;
  return octave * 12 + pcs[idx]!;
}

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

// Chord-quality templates as interval sets (semitones above the root), longest
// first so 7ths win over the triad they contain. Exported so the chord model
// (chordmodel.ts) can build its quality→interval table from the same source,
// keeping detection and symbolic rendering from drifting apart.
export const CHORD_TEMPLATES: ReadonlyArray<readonly [string, number[]]> = [
  ["maj7", [0, 4, 7, 11]],
  ["m7", [0, 3, 7, 10]],
  ["7", [0, 4, 7, 10]],
  ["m7b5", [0, 3, 6, 10]],
  ["dim7", [0, 3, 6, 9]],
  ["6", [0, 4, 7, 9]],
  ["m6", [0, 3, 7, 9]],
  ["", [0, 4, 7]], // major triad
  ["m", [0, 3, 7]],
  ["dim", [0, 3, 6]],
  ["aug", [0, 4, 8]],
  ["sus2", [0, 2, 7]],
  ["sus4", [0, 5, 7]],
];

/**
 * Best-effort chord name for a set of pitches, e.g. "Am", "Dm7", "C", "Gsus4".
 * Pure. Tries each pitch class as the root and matches against common triad/7th
 * templates; the lowest note's pitch class breaks ties so inversions still read
 * sensibly. Returns just the bass note name (e.g. "A") when nothing matches, or
 * "" for an empty input.
 */
export function chordName(pitches: number[]): string {
  const pcs = [...new Set(pitches.map((p) => ((p % 12) + 12) % 12))];
  if (!pcs.length) return "";
  if (pcs.length === 1) return NOTE_NAMES[pcs[0]!]!;
  const bassPc = ((Math.min(...pitches) % 12) + 12) % 12;
  const have = new Set(pcs);

  let best: { name: string; rootIsBass: boolean } | null = null;
  for (const root of pcs) {
    const rel = new Set(pcs.map((pc) => (((pc - root) % 12) + 12) % 12));
    for (const [quality, tpl] of CHORD_TEMPLATES) {
      if (tpl.length !== rel.size) continue;
      if (!tpl.every((iv) => rel.has(iv))) continue;
      const name = NOTE_NAMES[root]! + quality;
      const rootIsBass = root === bassPc;
      // Prefer a match whose root is the bass note (root-position reading).
      if (!best || (rootIsBass && !best.rootIsBass)) best = { name, rootIsBass };
      break; // first (longest) template for this root wins
    }
  }
  if (best) return best.name;
  // Unmatched cluster: fall back to the bass note name (with a hint if extended).
  return NOTE_NAMES[bassPc]! + (have.size > 3 ? "…" : "");
}

/**
 * Structured counterpart to {@link chordName}: the best-fit root pitch-class +
 * quality suffix for a set of pitches, or null if nothing matches. The quality
 * is one of the {@link CHORD_TEMPLATES} suffixes ("" = major triad, "m", "m7",
 * …). Used by the chord model to seed a symbolic spec from detected pitches so
 * detected chords become editable. Pure.
 */
export function matchChord(pitches: number[]): { rootPc: number; quality: string } | null {
  const pcs = [...new Set(pitches.map((p) => ((p % 12) + 12) % 12))];
  if (!pcs.length) return null;
  if (pcs.length === 1) return { rootPc: pcs[0]!, quality: "" };
  const bassPc = ((Math.min(...pitches) % 12) + 12) % 12;
  let best: { rootPc: number; quality: string; rootIsBass: boolean } | null = null;
  for (const root of pcs) {
    const rel = new Set(pcs.map((pc) => (((pc - root) % 12) + 12) % 12));
    for (const [quality, tpl] of CHORD_TEMPLATES) {
      if (tpl.length !== rel.size) continue;
      if (!tpl.every((iv) => rel.has(iv))) continue;
      const rootIsBass = root === bassPc;
      if (!best || (rootIsBass && !best.rootIsBass)) best = { rootPc: root, quality, rootIsBass };
      break; // first (longest) template for this root wins
    }
  }
  return best ? { rootPc: best.rootPc, quality: best.quality } : null;
}

// A detected/working chord: a pitch set placed at a point in time. Exported so
// the shared chord model (chordmodel.ts) can build these directly and feed them
// to the same rhythm machinery without re-detecting. `notes` keeps the original
// cluster members so the "original" (Keep timing) strategy is truly lossless.
export interface Chord {
  start: number; // beats — onset of the chord
  span: number; // beats until the next chord (or the clip's end for the last)
  bar: number; // floor(start / beatsPerBar) — drives phrase parity
  pitches: number[]; // ascending, de-duplicated
  velocity: number; // representative (loudest) velocity of the source chord
  notes?: Note[]; // the exact source notes in this cluster (for "original")
}

// Strategy onset/duration patterns below are authored against a 4-beat
// reference bar, then mapped onto each chord's actual `span`. This makes the
// grooves scale to any harmonic rhythm (one, two, or more chords per bar) and
// reduces to the original numbers when a chord spans a full 4/4 bar.
const REF_BAR = 4;

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const clampVel = (v: number) => clamp(Math.round(v), 1, 127);

/** Phrase index parity (4-bar phrases) used to vary motifs across repeats. */
const phraseParity = (bar: number) => Math.floor(bar / 4) % 2;

/** Map a reference-bar beat (0..4) onto the chord's actual span. */
const at = (c: Chord, refBeat: number) => c.start + (refBeat / REF_BAR) * c.span;
/** Map a reference-bar duration onto the chord's actual span. */
const dur = (c: Chord, refBeats: number) => (refBeats / REF_BAR) * c.span;

/**
 * Cluster notes into chords by shared onset, keeping EVERY cluster (multiple
 * chords per bar are supported). Each chord's `span` is the gap to the next
 * chord's onset; the last chord spans to the furthest note-end in its cluster.
 * Exported for testing and reuse by the voicing transforms.
 */
export function detectChords(notes: Note[], beatsPerBar = BEATS_PER_BAR): Chord[] {
  const sorted = [...notes].sort((a, b) => a.startTime - b.startTime);

  interface Raw {
    start: number;
    pitches: number[];
    velocity: number;
    end: number; // furthest note-end in the cluster
    notes: Note[]; // the source notes in this cluster
  }
  const raws: Raw[] = [];
  let anchor = -Infinity;
  let pitches: number[] = [];
  let noteBuf: Note[] = [];
  let vel = 0;
  let end = 0;

  const flush = () => {
    if (!pitches.length) return;
    raws.push({
      start: anchor,
      pitches: [...new Set(pitches)].sort((a, b) => a - b),
      velocity: clampVel(vel || 100),
      end,
      notes: noteBuf,
    });
    pitches = [];
    noteBuf = [];
    vel = 0;
    end = 0;
  };

  for (const n of sorted) {
    if (n.startTime - anchor > ONSET_TOLERANCE) {
      flush();
      anchor = n.startTime;
    }
    pitches.push(n.pitch);
    noteBuf.push(n);
    vel = Math.max(vel, n.velocity ?? 100);
    end = Math.max(end, n.startTime + n.duration);
  }
  flush();

  return raws.map((r, i) => {
    const next = raws[i + 1];
    const span = next ? next.start - r.start : r.end - r.start;
    return {
      start: r.start,
      span: Math.max(span, 1e-6), // guard against zero-length chords
      bar: Math.floor(r.start / beatsPerBar + 1e-6),
      pitches: r.pitches,
      velocity: r.velocity,
      notes: r.notes.map((n) => ({ ...n })),
    };
  });
}

function emit(pitches: number[], start: number, dur: number, velocity: number): Note[] {
  const startTime = Math.max(0, start);
  return pitches.map((pitch) => ({
    pitch,
    startTime,
    duration: dur,
    velocity: clampVel(velocity),
  }));
}

// --- Strategies: Chord -> Note[] ------------------------------------------

function charleston(c: Chord): Note[] {
  // Beat 1 + the "and of 2" — the +1.5 on odd phrases adds a third hit.
  const onsets = phraseParity(c.bar) === 0 ? [0, 2.5] : [0, 1.5, 2.5];
  return onsets.flatMap((o) =>
    emit(c.pitches, at(c, o), dur(c, 0.5), o === 0 ? c.velocity : c.velocity - 12),
  );
}

function anticipation(c: Chord): Note[] {
  // Pull the chord change earlier than its onset (except the very first chord),
  // then sustain across it. Odd phrases anticipate by a 1/16 instead of a 1/8.
  const ant = c.start === 0 ? 0 : phraseParity(c.bar) === 0 ? 0.5 : 0.25;
  return emit(c.pitches, c.start - dur(c, ant), c.span + dur(c, ant), c.velocity);
}

function slowStabs(c: Chord): Note[] {
  // Slow harmonic motion: a quiet sustained pad of the lower voices for the
  // chord's span, punctuated by short full-chord stabs on the offbeats.
  const lower = c.pitches.slice(0, Math.max(1, c.pitches.length - 1));
  const pad = emit(lower, c.start, c.span, c.velocity - 20);
  const stabOnsets = phraseParity(c.bar) === 0 ? [1.5, 3.5] : [2.5];
  const stabs = stabOnsets.flatMap((o) => emit(c.pitches, at(c, o), dur(c, 0.25), c.velocity));
  return [...pad, ...stabs];
}

function sustainedMovingTop(c: Chord, scale?: Scale): Note[] {
  // Hold the chord; re-articulate the top voice to add melodic motion. With a
  // scale, the top voice WALKS up the scale (genuine melody); without one it is
  // re-articulated at pitch (the original, key-agnostic behaviour).
  const held = emit(c.pitches, c.start, c.span, c.velocity);
  const top = Math.max(...c.pitches); // chords always have >=1 pitch (see detectChords)
  const moves = phraseParity(c.bar) === 0 ? [2, 3] : [1.5, 2.5, 3.5];
  const motion = moves.flatMap((o, i) => {
    const pitch = scale ? scaleStep(top, i + 1, scale) : top;
    return emit([pitch], at(c, o), dur(c, 0.5), c.velocity - 10);
  });
  return [...held, ...motion];
}

function arpeggiate(c: Chord, dir: ArpDirection, scale?: Scale): Note[] {
  // Spread the chord's pitches across its span as an even run of single notes.
  // Odd phrases run two passes (double-time) for added motion. A scale only
  // snaps the pitches (they are already chord tones, so this is a safety net for
  // re-voiced chords); it does not invent passing tones.
  const asc = [...c.pitches];
  let seq: number[];
  if (dir === "down") seq = [...asc].reverse();
  else if (dir === "updown" && asc.length > 2) seq = [...asc, ...asc.slice(1, -1).reverse()];
  else seq = asc; // "up", or too few voices to fold
  if (scale) seq = seq.map((p) => snapToScale(p, scale));

  const passes = phraseParity(c.bar) === 0 ? 1 : 2;
  const full = passes === 1 ? seq : [...seq, ...seq];
  const step = c.span / full.length;
  return full.map((pitch, i) => ({
    pitch,
    startTime: c.start + i * step,
    duration: step,
    velocity: clampVel(c.velocity - (i % 2 ? 8 : 0)),
  }));
}

// The strategies with a uniform (chord) -> notes shape. `arpeggiate`, the
// scale-aware `sustainedMovingTop`, and the pass-through `original` take special
// handling and are dispatched in chordsToNotes, so they are not in this map.
type SimpleStrategy = Exclude<RhythmStrategy, "arpeggiate" | "sustainedMovingTop" | "original">;
const STRATEGIES: Record<SimpleStrategy, (c: Chord) => Note[]> = {
  charleston,
  anticipation,
  slowStabs,
};

/** Extra, strategy-specific knobs for {@link reRhythm}. All optional. */
export interface ReRhythmOptions {
  /** Direction for the "arpeggiate" strategy (default "up"). */
  arp?: ArpDirection;
  /** When set, melodic strategies keep moving voices in this key. */
  scale?: Scale;
}

/**
 * Render an already-detected (or model-built) list of chords with the chosen
 * strategy. Pure: Chord[] -> Note[]. Shared by {@link reRhythm} (which detects
 * from raw notes) and the chord-model pipeline (which builds chords directly),
 * so both go through identical groove logic without re-detecting.
 *
 * The "original" (Keep timing) strategy is a pass-through: it emits each chord's
 * source `notes` verbatim, so a clip's own rhythm survives untouched. When a
 * chord has no source notes (e.g. a freshly generated block) it falls back to a
 * sustained block across the chord's span. Voicing does not apply to "original".
 */
export function chordsToNotes(
  chords: Chord[],
  strategy: RhythmStrategy,
  beatsPerBar = BEATS_PER_BAR,
  opts: ReRhythmOptions = {},
): Note[] {
  void beatsPerBar; // phrase parity rides on each chord's precomputed `bar`
  const fn = (c: Chord): Note[] => {
    switch (strategy) {
      case "original":
        return (c.notes && c.notes.length ? c.notes : emit(c.pitches, c.start, c.span, c.velocity)).map(
          (n) => ({ ...n }),
        );
      case "arpeggiate":
        return arpeggiate(c, opts.arp ?? "up", opts.scale);
      case "sustainedMovingTop":
        return sustainedMovingTop(c, opts.scale);
      default:
        return STRATEGIES[strategy](c);
    }
  };
  return chords.flatMap(fn).sort((a, b) => a.startTime - b.startTime || a.pitch - b.pitch);
}

/**
 * Re-rhythm a clip's notes with the chosen strategy and (optionally) re-voice
 * each detected chord first. Pure: notes -> notes. Voicing composes with rhythm
 * because it only rewrites the chord's pitch set before the strategy runs.
 */
export function reRhythm(
  notes: Note[],
  strategy: RhythmStrategy,
  voicing: VoicingStyle = "close",
  beatsPerBar = BEATS_PER_BAR,
  opts: ReRhythmOptions = {},
): Note[] {
  const chords = detectChords(notes, beatsPerBar).map((c) =>
    voicing === "close" || strategy === "original" ? c : { ...c, pitches: revoice(c.pitches, voicing) },
  );
  return chordsToNotes(chords, strategy, beatsPerBar, opts);
}

/**
 * Swing: delay notes that land on an offbeat of the given subdivision. Pure.
 *   - amount 0 = straight; amount 1 = full triplet swing (an eighth offbeat
 *     moves from the 1/2 point of the beat to 2/3).
 *   - subdivision is in beats (0.5 = eighth-note swing, the default).
 * Only onsets sitting ~on an offbeat grid line are nudged; on-beat and clearly
 * off-grid notes are left alone. Each swung note's END is held in place by
 * trimming its duration, so it never bleeds past the following onset.
 */
export function swing(notes: Note[], amount: number, subdivision = 0.5): Note[] {
  if (amount <= 0) return notes.map((n) => ({ ...n }));
  const shiftMax = subdivision / 3; // offbeat 0.5 -> 0.667 of the beat at amount=1
  return notes.map((n) => {
    const idx = Math.round(n.startTime / subdivision);
    const onGrid = Math.abs(n.startTime - idx * subdivision) < 1e-6;
    if (!onGrid || idx % 2 === 0) return { ...n };
    const shift = amount * shiftMax;
    return { ...n, startTime: n.startTime + shift, duration: Math.max(1e-4, n.duration - shift) };
  });
}

/**
 * Deterministic humanize: nudge timing and set per-note velocityDeviation.
 * Deterministic (hash of index+pitch) so it is testable and idempotent-ish.
 */
export function humanize(notes: Note[], timing = 0.02, vel = 8): Note[] {
  return notes.map((n, i) => {
    const h = (i * 2654435761 + n.pitch * 40503) >>> 0; // cheap integer hash
    const tNudge = (((h % 5) - 2) / 2) * timing; // in [-timing, +timing]
    const vNudge = ((h >>> 3) % (2 * vel + 1)) - vel; // in [-vel, +vel] (unsigned shift!)
    return {
      ...n,
      startTime: Math.max(0, n.startTime + tNudge),
      velocityDeviation: vNudge,
    };
  });
}
