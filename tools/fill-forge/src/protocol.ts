// The host ↔ webview contract. PURE / SDK-free so BOTH the host (extension.ts,
// which imports the SDK) and the webview (main.ts, typechecked SDK-free in CI)
// can import it without dragging the SDK into the CI typecheck. The dialog is
// seeded with a FillContext and posts back a FillRequest (or null on Cancel).
import type { FillSpec } from "./fillengine.js";

/**
 * Where an inserted fill goes. Live Actions cannot see Live's Arrangement
 * time highlight, so `fillSelection` from the Suite extension is `playhead`.
 */
export type OutputTarget = "newClip" | "replace" | "newTrack" | "append" | "playhead";

export const TARGET_LABELS: Record<OutputTarget, string> = {
  newClip: "New clip",
  replace: "Replace",
  newTrack: "New track",
  append: "Append to end",
  playhead: "At playhead",
};

export const LIVE_ACTIONS_TARGETS: OutputTarget[] = [
  "newClip",
  "replace",
  "append",
  "newTrack",
  "playhead",
];

/** Pitched MIDI note ready for the Max bridge. Times are beats. */
export interface NoteOut {
  pitch: number;
  startTime: number;
  duration: number;
  velocity: number;
}

/** Which context-menu entry summoned the dialog. */
export type EntryPoint = "MidiClip" | "MidiTrack" | "DrumRack" | "ArrangementSelection";

/** Host → webview: everything the dialog needs to render and seed its controls. */
export interface FillContext {
  source: EntryPoint;
  hasClip: boolean;
  clipName?: string;
  clipDuration?: number; // beats
  beatsPerBar: number;
  tempo?: number;
  spec: FillSpec; // host-seeded default the dialog edits (controls arrive P3)
  availableTargets: OutputTarget[]; // constrained by what the host can resolve
  noteCount: number; // demo-fill size — P0/P2 proof; replaced by the live grid in P3
  selection?: { start: number; end: number }; // beats — ArrangementSelection (P5)
}

/** Webview → host, on Insert. Cancel/Escape posts null instead. */
export interface FillRequest {
  spec: FillSpec;
  target: OutputTarget;
  notes: NoteOut[];
  lengthBeats: number;
  name: string;
}
