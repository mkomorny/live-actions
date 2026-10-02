// Abstract drum-voice vocabulary + pad-note maps. PURE — no SDK dependency, so
// it unit-tests SDK-free and is SHARED with the planned "Pocket Operations"
// sibling extension. The fill engine works entirely in terms of these abstract
// voices (Kick, Snare, …); a map turns a voice into a concrete MIDI pitch only
// at the very end, in extension.ts. That keeps the musical logic independent of
// any one Drum Rack's pad layout.
//
// Two maps ship because the two sibling extensions default to different layouts:
//   - GM_MAP        — General MIDI percussion (this extension's default).
//   - CHROMATIC_MAP — one voice per semitone from C1 (36), the layout Erin's
//                     Pocket Operations grooves assume. Provided here so both
//                     extensions agree on a single source of truth; Fill Forge
//                     does not use it by default.
// A real kit's pads can sit anywhere, so v1 also lets the host pass an override
// map (manual pad-map) — both built-ins are just the sensible starting points.

/**
 * The abstract drum voices a fill can address. Ordered low→high in the rough
 * register sense (kick at the bottom, cymbals at the top); CHROMATIC_MAP assigns
 * pitches in this order from note 36 upward, and tom cascades walk Hi→Mid→Low.
 */
export const DRUM_VOICES = [
  "kick",
  "rim",
  "snare",
  "clap",
  "lowTom",
  "midTom",
  "hiTom",
  "closedHat",
  "pedalHat",
  "openHat",
  "ride",
  "crash",
] as const;

export type DrumVoice = (typeof DRUM_VOICES)[number];

/** A concrete pad layout: every abstract voice → a MIDI note number. */
export type DrumMap = Record<DrumVoice, number>;

/** Human-readable labels for the UI step-grid rows. */
export const VOICE_LABELS: Record<DrumVoice, string> = {
  kick: "Kick",
  rim: "Rim",
  snare: "Snare",
  clap: "Clap",
  lowTom: "Low Tom",
  midTom: "Mid Tom",
  hiTom: "Hi Tom",
  closedHat: "Closed Hat",
  pedalHat: "Pedal Hat",
  openHat: "Open Hat",
  ride: "Ride",
  crash: "Crash",
};

/**
 * General MIDI percussion key map — the default for Fill Forge. Pitches follow
 * the GM drum standard so a fill lands on the right voices in any GM-compatible
 * Drum Rack (Live's stock kits are GM-keyed). Toms (Hi 50 / Mid 48 / Low 45)
 * descend in pitch so a Hi→Mid→Low cascade also descends musically.
 */
export const GM_MAP: DrumMap = {
  kick: 36,
  rim: 37,
  snare: 38,
  clap: 39,
  lowTom: 45,
  midTom: 48,
  hiTom: 50,
  closedHat: 42,
  pedalHat: 44,
  openHat: 46,
  ride: 51,
  crash: 49,
};

/**
 * Chromatic-from-36 map: voices laid out one per semitone starting at C1 (36),
 * in {@link DRUM_VOICES} order. This is the layout the Pocket Operations sibling
 * assumes; exported here so both extensions share one definition rather than
 * each hard-coding it. Not Fill Forge's default.
 */
export const CHROMATIC_MAP: DrumMap = Object.fromEntries(
  DRUM_VOICES.map((v, i) => [v, 36 + i]),
) as DrumMap;

/** Lowest / highest MIDI note any built-in map can emit (for range assertions). */
export const GM_MIN_PITCH = 36;
export const GM_MAX_PITCH = 51;
