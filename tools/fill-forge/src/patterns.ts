// patterns.ts — the MUSICAL CONTENT layer. PURE, SDK-free, unit-testable.
//
// The old engine generated isolated gestures (an accelerating run of one voice).
// This is the replacement vocabulary: genre-authentic GROOVE cells and FILL
// figures authored as DATA on a step grid, which the fill engine arranges +
// ornaments into VoiceHits. Adding genres/figures = adding data here, not code.
//
// Authoring DSL — one string per voice "lane", one char per step:
//   O = open / loudest accent   X = accent      x = normal
//   n = soft                    o = ghost       . = rest
//   |                           = visual beat divider (ignored)
// `sub` is steps-per-beat the lane was written on: 4 = sixteenths (default),
//   3 = eighth-note triplets, 6 = sixteenth-note triplets (swung/shuffle feels).
// A trailing `~` on a lane key marks every hit in that lane as a flam (grace
// note just before) — see ORNAMENT handling in the engine.
import type { Genre } from "./fillengine.js";
import type { DrumVoice } from "./drumvoices.js";

export type Ornament = "flam" | "drag" | "ruff" | "ghost";

/** One struck note inside a figure: a voice at a beat offset with a velocity. */
export interface PatternHit {
  voice: DrumVoice;
  pos: number; // beats from the figure start
  vel: number; // 1..127
  orn?: Ornament;
}

export type FigureKind = "groove" | "fill";

/** A reusable figure — a groove cell (the beat) or a fill lick (the transition). */
export interface Figure {
  id: string;
  kind: FigureKind;
  lengthBeats: number;
  sub: number; // steps per beat the figure was authored on
  hits: PatternHit[];
}

// Velocity codes for the lane DSL.
const VEL: Record<string, number> = { O: 124, X: 106, x: 84, n: 64, o: 34 };

/** Parse one lane string into hits for a voice. `.`/space = rest, `|` ignored. */
function lane(voice: DrumVoice, str: string, sub: number, orn?: Ornament): PatternHit[] {
  const hits: PatternHit[] = [];
  let step = 0;
  for (const ch of str) {
    if (ch === "|") continue; // visual divider — no step
    if (ch === "." || ch === " ") {
      step++;
      continue;
    }
    const vel = VEL[ch];
    if (vel !== undefined) hits.push({ voice, pos: step / sub, vel, ...(orn ? { orn } : {}) });
    step++;
  }
  return hits;
}

type Lanes = Partial<Record<string, string>>;

/** Build a figure from per-voice lane strings. A `voice~` key flams that lane. */
function fig(id: string, kind: FigureKind, lengthBeats: number, sub: number, lanes: Lanes): Figure {
  const hits: PatternHit[] = [];
  for (const [key, str] of Object.entries(lanes)) {
    if (str === undefined) continue;
    const flam = key.endsWith("~");
    const voice = (flam ? key.slice(0, -1) : key) as DrumVoice;
    hits.push(...lane(voice, str, sub, flam ? "flam" : undefined));
  }
  hits.sort((a, b) => a.pos - b.pos || a.voice.localeCompare(b.voice));
  return { id, kind, lengthBeats, sub, hits };
}
const groove = (id: string, sub: number, lanes: Lanes, bars = 1): Figure =>
  fig(id, "groove", bars * 4, sub, lanes);
const fill = (id: string, beats: number, sub: number, lanes: Lanes): Figure =>
  fig(id, "fill", beats, sub, lanes);

/** A genre's vocabulary: groove cells, fill figures, default feel + resolution. */
export interface GenreBank {
  grooves: Figure[];
  fills: Figure[];
  swing: number; // baseline swing feel (0..1) applied unless the user overrides
  resolve: DrumVoice; // cymbal struck on the resolving downbeat
}

// ===========================================================================
// ELECTRONIC banks. (Classic / acoustic banks are appended below.)
// ===========================================================================

const HOUSE: GenreBank = {
  swing: 0.08,
  resolve: "crash",
  grooves: [
    groove("house_four", 4, {
      kick: "X...|X...|X...|X...",
      clap: "....|X...|....|X...",
      closedHat: "..x.|..x.|..x.|..x.",
    }),
    groove("house_skip", 4, {
      kick: "X...|X...|X...|X...",
      clap: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
      openHat: "..o.|..o.|..o.|..o.",
    }),
  ],
  fills: [
    fill("house_clapbuild", 1, 4, { clap: "nxXO" }),
    fill("house_snareroll", 1, 4, { snare: "xxXO" }),
    fill("house_hatlift", 1, 4, { closedHat: "x.x.", openHat: "...O" }),
    fill("house_tomdrop", 2, 4, { midTom: "x...|x...", lowTom: "....|x...", snare: "....|..X." }),
    fill("house_clapsnare", 2, 4, { clap: "x...|x.x.", snare: "..o.|..oX" }),
  ],
};

const TECHNO: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("techno_drive", 4, {
      kick: "X...|X...|X...|X...",
      openHat: "..x.|..x.|..x.|..x.",
      rim: "....|x...|....|x...",
    }),
    groove("techno_clap", 4, {
      kick: "X...|X...|X...|X...",
      clap: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("techno_rumble", 2, 4, { kick: "X.X.|X.XX", closedHat: "x.x.|x.x." }),
    fill("techno_tomroll", 2, 4, { midTom: "x.x.|X.x.", lowTom: "..x.|..XO" }),
    fill("techno_clave", 2, 4, { rim: "x..x|..x.", clap: "....|X..O" }),
    fill("techno_hatdrive", 1, 4, { closedHat: "xXxO" }),
  ],
};

const DNB: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("dnb_amen", 4, {
      kick: "X...|..X.|..X.|....",
      snare: "....|X.o.|..o.|X.o.",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
    groove("dnb_twostep", 4, {
      kick: "X...|....|..X.|....",
      snare: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("dnb_snarechop", 2, 4, { snare: "X.oX|o.XO" }),
    fill("dnb_doubles", 2, 4, { snare: "Xo.X|o.XX", kick: "....|X..." }),
    fill("dnb_rollup", 1, 6, { snare: "oxXXOO" }),
    fill("dnb_break", 2, 4, { snare: "X.o.|XoXO", kick: "..X.|...." }),
  ],
};

const TRAP: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("trap_half", 4, {
      kick: "X...|....|X.X.|....",
      clap: "....|....|X...|....",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
    groove("trap_rolls", 4, {
      kick: "X...|...X|..X.|....",
      clap: "....|....|X...|....",
      closedHat: "xxxx|xxxx|xxxx|xxxx",
    }),
  ],
  fills: [
    fill("trap_hatroll32", 1, 6, { closedHat: "xxXxXO" }),
    fill("trap_triplet", 2, 3, { closedHat: "xxX|xxX", clap: "...|..O" }),
    fill("trap_snareroll", 1, 6, { snare: "ooxXXO" }),
    fill("trap_808slide", 2, 4, { kick: "X...|..X.", clap: "....|X..O" }),
  ],
};

const BREAKBEAT: GenreBank = {
  swing: 0.12,
  resolve: "crash",
  grooves: [
    groove("break_funk", 4, {
      kick: "X..X|....|..X.|....",
      snare: "....|X.o.|....|Xo..",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
    groove("break_amen", 4, {
      kick: "X...|..X.|.X..|....",
      snare: "....|Xo.o|..X.|o.X.",
      openHat: "....|..o.|....|..o.",
    }),
  ],
  fills: [
    fill("break_chop", 2, 4, { snare: "X.oX|.oXO", kick: "..X.|...." }),
    fill("break_linear", 2, 4, { kick: "X...|.X..", snare: "..X.|...X", midTom: "....|X..." }),
    fill("break_tomtumble", 2, 4, { hiTom: "x.x.|....", midTom: "....|xx..", lowTom: "......XO" }),
  ],
};

const AMBIENT: GenreBank = {
  swing: 0.05,
  resolve: "ride",
  grooves: [
    groove("amb_pulse", 4, {
      kick: "X...|....|X...|....",
      closedHat: "....|n...|....|n...",
      rim: "....|....|..n.|....",
    }),
  ],
  fills: [
    fill("amb_swell", 2, 4, { midTom: "n...|..n.", ride: "....|...n" }),
    fill("amb_softroll", 2, 4, { snare: "o.o.|o.nx" }),
    fill("amb_rimtick", 2, 4, { rim: "n..n|.n.x", lowTom: "....|...n" }),
  ],
};

// ===========================================================================
// CLASSIC / ACOUSTIC banks.
// ===========================================================================

const ROCK: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("rock_basic", 4, {
      kick: "X...|..X.|X...|....",
      snare: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
    groove("rock_drive", 4, {
      kick: "X..X|....|X..X|....",
      snare: "....|X...|....|X...",
      closedHat: "X.X.|X.X.|X.X.|X.X.",
    }),
  ],
  fills: [
    fill("rock_tomdown", 2, 4, { snare: "XX..|....", hiTom: "..XX|....", midTom: "....|XX..", lowTom: "....|..XX" }),
    fill("rock_snare16", 1, 4, { snare: "xXxO" }),
    fill("rock_crashstop", 2, 4, { snare: "X...|X..X", midTom: "....|..X.", lowTom: "......X." }),
  ],
};

const FUNK: GenreBank = {
  swing: 0.1,
  resolve: "crash",
  grooves: [
    groove("funk_16", 4, {
      kick: "X..X|..X.|X...|..X.",
      snare: "....|Xo.o|..o.|Xo..",
      closedHat: "xXxx|xXxx|xXxx|xXxx",
    }),
  ],
  fills: [
    fill("funk_linear", 2, 4, { kick: "X...|.X..", snare: "..oX|o..X", hiTom: "....|..X." }),
    fill("funk_ghost", 2, 4, { snare: "oXoo|XooX", closedHat: "x.x.|x.x." }),
    fill("funk_tomtumble", 2, 4, { snare: "X.o.|....", hiTom: "..x.|x...", midTom: "....|.x.x", lowTom: "......XO" }),
  ],
};

const JAZZ: GenreBank = {
  swing: 0, // authored on the triplet grid already
  resolve: "ride",
  grooves: [
    groove("jazz_swing", 3, {
      ride: "X..|X.x|X..|X.x",
      pedalHat: "...|X..|...|X..",
    }),
  ],
  fills: [
    fill("jazz_comp", 2, 3, { snare: "o.X|..o", midTom: "...|X..", ride: "X..|..x" }),
    fill("jazz_trade", 2, 3, { snare: "X.o|X.o", hiTom: "..X|...", lowTom: "...|.X." }),
    fill("jazz_brush", 2, 3, { snare: "x.x|x.X", ride: "X..|X.." }),
  ],
};

const METAL: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("metal_double", 4, {
      kick: "X.X.|X.X.|X.X.|X.X.",
      snare: "....|X...|....|X...",
      closedHat: "X...|X...|X...|X...",
    }),
  ],
  fills: [
    fill("metal_tomblast", 2, 4, { hiTom: "XX..|....", midTom: "..XX|....", lowTom: "....|XXXX", kick: "X.X.|X.X." }),
    fill("metal_snareblast", 1, 4, { snare: "XXXX", kick: "X.X." }),
    fill("metal_gallop", 2, 4, { kick: "XXxX|XxXX", snare: "....|...X" }),
  ],
};

const LATIN: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("latin_songo", 4, {
      kick: "X..X|..X.|X..X|..X.",
      rim: "..x.|.x..|x...|x.x.",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("latin_tomconga", 2, 4, { hiTom: "x.X.|.x.x", midTom: "..x.|X.x.", lowTom: "....|..XO" }),
    fill("latin_clave", 2, 4, { rim: "x.x.|.x.x", clap: "....|X..O" }),
    fill("latin_tumbao", 2, 4, { lowTom: "x..x|..x.", hiTom: "..x.|x..X" }),
  ],
};

const HIPHOP: GenreBank = {
  swing: 0.18,
  resolve: "crash",
  grooves: [
    groove("hiphop_boombap", 4, {
      kick: "X...|....|X.X.|....",
      snare: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("hiphop_snareroll", 2, 4, { snare: "x.xo|X.xO", kick: "X...|...." }),
    fill("hiphop_flamsnare", 2, 4, { "snare~": "X...|..X.", kick: "..X.|....", snare: "....|...X" }),
    fill("hiphop_tomdrop", 2, 4, { snare: "X...|....", midTom: "..x.|x...", lowTom: "....|.X.O" }),
  ],
};

const RNB: GenreBank = {
  swing: 0.14,
  resolve: "ride",
  grooves: [
    groove("rnb_groove", 4, {
      kick: "X...|..X.|..X.|....",
      snare: "....|X.o.|..o.|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("rnb_ghostfill", 2, 4, { snare: "oXoo|Xo.X", closedHat: "x.x.|x.x." }),
    fill("rnb_tomsoul", 2, 4, { snare: "X.o.|....", midTom: "....|x.x.", lowTom: "......XO" }),
    fill("rnb_rimtick", 2, 4, { rim: "x.x.|x.x.", snare: "....|...X" }),
  ],
};

const REGGAE: GenreBank = {
  swing: 0.05,
  resolve: "crash",
  grooves: [
    groove("reggae_onedrop", 4, {
      kick: "....|....|X...|....",
      rim: "....|....|X...|....",
      closedHat: "..x.|..x.|..x.|..x.",
    }),
  ],
  fills: [
    fill("reggae_rimroll", 2, 4, { rim: "x.x.|xXxO" }),
    fill("reggae_tomfall", 2, 4, { hiTom: "x...|x...", midTom: "..x.|..x.", lowTom: "....|..XO" }),
    fill("reggae_snaredrop", 2, 4, { snare: "....|X..O", rim: "x.x.|...." }),
  ],
};

const DISCO: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("disco_four", 4, {
      kick: "X...|X...|X...|X...",
      clap: "....|X...|....|X...",
      openHat: "..x.|..x.|..x.|..x.",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("disco_tomroll", 2, 4, { hiTom: "x.x.|x.x.", midTom: "....|x.x.", lowTom: "......XO" }),
    fill("disco_snarebuild", 1, 4, { snare: "xxXO" }),
    fill("disco_clapbuild", 2, 4, { clap: "x.x.|xXxO", openHat: "....|...O" }),
  ],
};

const POP: GenreBank = {
  swing: 0,
  resolve: "crash",
  grooves: [
    groove("pop_basic", 4, {
      kick: "X...|....|X.X.|....",
      snare: "....|X...|....|X...",
      closedHat: "x.x.|x.x.|x.x.|x.x.",
    }),
  ],
  fills: [
    fill("pop_tomfill", 2, 4, { snare: "X.X.|....", midTom: "....|X.X.", lowTom: "......XO" }),
    fill("pop_snarebuild", 1, 4, { snare: "nxXO" }),
    fill("pop_crashstop", 2, 4, { snare: "X...|...X", hiTom: "....|.X.." }),
  ],
};

export const GENRE_BANKS: Record<Genre, GenreBank> = {
  melodicHouse: HOUSE,
  darkTechno: TECHNO,
  dnb: DNB,
  trap: TRAP,
  breakbeat: BREAKBEAT,
  ambient: AMBIENT,
  rock: ROCK,
  funk: FUNK,
  jazz: JAZZ,
  metal: METAL,
  latin: LATIN,
  hipHop: HIPHOP,
  rnb: RNB,
  reggae: REGGAE,
  disco: DISCO,
  pop: POP,
};
