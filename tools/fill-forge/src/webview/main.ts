// Webview UI — P3. The full dialog: it reads the host-seeded FillContext, lets the
// user edit a FillSpec through every control (genre/technique/length/sliders/pad-map/
// reshuffle/variations), re-runs the PURE fill engine live on each change, and paints
// a velocity-shaded step grid + a build-up lane + a sweeping playhead. A percussive
// WebAudio "audition" plays the fill (preview only — writes nothing). On Insert it
// posts the edited FillSpec + chosen target back over the Live bridge; the host
// generates + writes the clip. Theme switcher mirrors Midnight Tools' mechanism
// (localStorage) but with Fill Forge's own palettes (design/themes.md). Ignite default.
import type { FillContext, FillRequest, OutputTarget } from "../protocol.js";
import { LIVE_ACTIONS_TARGETS, TARGET_LABELS } from "../protocol.js";
import {
  type FillSpec,
  type Genre,
  type Technique,
  type FillLength,
  type FillMode,
  type VoiceHit,
  GENRE_GROUPS,
  GENRE_LABELS,
  TECHNIQUE_LABELS,
  DEFAULT_FILL_SPEC,
  generateFill,
  generateFillVoices,
} from "../fillengine.js";
import { DRUM_VOICES, VOICE_LABELS, type DrumVoice } from "../drumvoices.js";

// ---- host bridge -----------------------------------------------------------
// window.liveActionsSend, injected by breakdowns_window.py (shared host for
// all webview tools), forwards a raw JSON string to window.pywebview.api.receive.
// NOT window.chrome.webview.postMessage -- that's pywebview's own internal
// js_api channel on the Windows edgechromium backend; hijacking it corrupts
// pywebview's own call protocol (see breakdowns_window.py's on_loaded).
type Outgoing = { method: "close_and_send"; params: [string | null] };
interface LiveBridge {
  webkit?: { messageHandlers?: { live?: { postMessage(m: Outgoing): void } } };
  liveActionsSend?: (raw: string) => void;
}
function send(payload: string | null): void {
  const w = window as unknown as LiveBridge;
  const msg: Outgoing = { method: "close_and_send", params: [payload] };
  if (w.webkit?.messageHandlers?.live) w.webkit.messageHandlers.live.postMessage(msg);
  else if (w.liveActionsSend) w.liveActionsSend(JSON.stringify(msg));
}

// ---- state -----------------------------------------------------------------
const ctx: FillContext = (window as unknown as { __CTX__?: FillContext }).__CTX__ ?? {
  source: "MidiClip",
  hasClip: false,
  beatsPerBar: 4,
  spec: DEFAULT_FILL_SPEC,
  availableTargets: LIVE_ACTIONS_TARGETS,
  noteCount: 0,
};

// The live, editable spec. Cloned from the host seed so edits stay webview-local
// until Insert posts it back.
const spec: FillSpec = { ...DEFAULT_FILL_SPEC, ...ctx.spec };
let target: OutputTarget = ctx.availableTargets[0] ?? "newTrack";
let hits: VoiceHit[] = [];

const lengthBeats = (): number => spec.lengthBars * spec.beatsPerBar;
const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

function recompute(): void {
  hits = generateFillVoices(spec);
}

/** The lanes the step grid shows: the full GM voice set, cymbals at the TOP and
 *  the kick at the BOTTOM (piano-roll convention, matching the design), so the
 *  grid always reads as a drum sequencer (active voices lit, the rest empty). */
function laneVoices(): DrumVoice[] {
  return [...DRUM_VOICES].reverse();
}

// Compact labels for the chips/tiles (the engine keeps the long names for clip
// naming); these match the Pencil design's wording.
const GENRE_SHORT: Record<Genre, string> = {
  melodicHouse: "Melodic House",
  darkTechno: "Dark Techno",
  dnb: "D&B",
  trap: "Trap",
  breakbeat: "Breakbeat",
  ambient: "Ambient",
  rock: "Rock",
  funk: "Funk",
  jazz: "Jazz",
  metal: "Metal",
  latin: "Latin",
  hipHop: "Hip-Hop",
  rnb: "R&B",
  reggae: "Reggae",
  disco: "Disco",
  pop: "Pop",
};
const TECH_SHORT: Record<Technique, string> = {
  snareRoll: "Snare Roll",
  tomCascade: "Tom Cascade",
  glitchStutter: "Glitch",
  buildUp: "Build-Up",
  halfTimeDropIn: "Half-Time",
  hatRun: "Hat Run",
  ghostGroove: "Groove Fill",
};
const ACCEL_TECHNIQUES: Technique[] = ["snareRoll", "tomCascade", "buildUp", "hatRun", "halfTimeDropIn"];

// ---- theme palette (read CSS vars for the canvas) --------------------------
interface Palette {
  heat: string[];
  playhead: string;
  glow: string;
  border: string;
  borderHi: string;
  dim: string;
  text: string;
  padEmpty: string;
  snareRow: string;
}
function readPalette(): Palette {
  const cs = getComputedStyle(document.body);
  const g = (n: string): string => cs.getPropertyValue(n).trim();
  return {
    heat: [0, 1, 2, 3, 4, 5].map((i) => g(`--heat-${i}`)),
    playhead: g("--playhead"),
    glow: g("--playhead-glow"),
    border: g("--border"),
    borderHi: g("--border-hi"),
    dim: g("--dim"),
    text: g("--text"),
    padEmpty: g("--pad-empty"),
    snareRow: g("--snare-row"),
  };
}
let pal = readPalette();

/** Map a 0..1 velocity to its heat-ramp bucket (design/themes.md thresholds). */
function heatColor(v: number): string {
  const thresholds = [0.3, 0.46, 0.6, 0.74, 0.86];
  let i = 0;
  while (i < thresholds.length && v >= thresholds[i]!) i++;
  return pal.heat[i]!;
}

// ---- canvas preview --------------------------------------------------------
const GUTTER = 58; // left label gutter; shared by roll + lane so playheads align
const PAD_R = 10;

interface Plot {
  cw: number;
  ch: number;
  x0: number;
  plotW: number;
}
function prepCanvas(cv: HTMLCanvasElement): { c: CanvasRenderingContext2D; p: Plot } | null {
  const c = cv.getContext("2d");
  if (!c) return null;
  const dpr = window.devicePixelRatio || 1;
  const cw = cv.clientWidth;
  const ch = cv.clientHeight;
  cv.width = Math.round(cw * dpr);
  cv.height = Math.round(ch * dpr);
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, cw, ch);
  return { c, p: { cw, ch, x0: GUTTER, plotW: cw - GUTTER - PAD_R } };
}
const xForBeat = (b: number, p: Plot): number => p.x0 + (b / Math.max(0.001, lengthBeats())) * p.plotW;

/** The step grid: voice rows × 16th-note steps, each cell heat-shaded by the
 *  loudest hit landing in it (velocity = opacity too). A faint empty pad shows
 *  every slot, so the sequencer grid reads even when sparse. */
function drawRoll(playheadBeat: number | null): void {
  const cv = document.getElementById("roll") as HTMLCanvasElement | null;
  if (!cv) return;
  const prep = prepCanvas(cv);
  if (!prep) return;
  const { c, p } = prep;
  const rows = laneVoices();
  const len = lengthBeats();
  const steps = Math.max(1, Math.round(len * 4)); // 16th-note resolution
  const rowH = p.ch / rows.length;
  const stepW = p.plotW / steps;
  const cell = clamp(Math.min(20, stepW - 3, rowH - 8), 4, 20);

  c.textBaseline = "middle";
  c.font = "10px AbletonSansSmall, system-ui, sans-serif";

  rows.forEach((voice, ri) => {
    const ry = ri * rowH;
    // row background (snare row gets the warm highlight)
    if (voice === "snare") {
      c.fillStyle = pal.snareRow;
      c.fillRect(p.x0, ry, p.plotW, rowH);
    }
    // row label — the snare lane is brighter/bolder (it's the fill's home row)
    c.fillStyle = voice === "snare" ? pal.text : pal.dim;
    c.font = `${voice === "snare" ? "600 " : ""}10px AbletonSansSmall, system-ui, sans-serif`;
    c.textAlign = "left";
    c.fillText(VOICE_LABELS[voice], 6, ry + rowH / 2);

    // per-step max velocity for this voice
    const stepVel = new Array<number>(steps).fill(-1);
    for (const h of hits) {
      if (h.voice !== voice) continue;
      const s = clamp(Math.floor((h.startTime / len) * steps), 0, steps - 1);
      stepVel[s] = Math.max(stepVel[s]!, h.velocity / 127);
    }

    for (let s = 0; s < steps; s++) {
      const cx = p.x0 + s * stepW + (stepW - cell) / 2;
      const cy = ry + (rowH - cell) / 2;
      const v = stepVel[s]!;
      if (v < 0) {
        c.fillStyle = pal.padEmpty;
        c.globalAlpha = 1;
        roundRect(c, cx, cy, cell, cell, 3);
        c.fill();
      } else {
        c.fillStyle = heatColor(v);
        c.globalAlpha = 0.5 + 0.5 * v;
        roundRect(c, cx, cy, cell, cell, 3);
        c.fill();
        c.globalAlpha = 1;
      }
    }
  });

  drawBeatLines(c, p, len);
  drawPlayhead(c, p, playheadBeat);
}

/** The build-up lane: one velocity bar per hit at its TRUE (accelerating) time —
 *  this is where the crescendo + the rush into the downbeat actually read. */
function drawBuildup(playheadBeat: number | null): void {
  const cv = document.getElementById("buildup") as HTMLCanvasElement | null;
  if (!cv) return;
  const prep = prepCanvas(cv);
  if (!prep) return;
  const { c, p } = prep;
  const len = lengthBeats();
  const floorY = p.ch - 8;
  const topPad = 8;
  const maxH = floorY - topPad;

  drawBeatLines(c, p, len);
  for (const h of hits) {
    const v = h.velocity / 127;
    const x = xForBeat(h.startTime, p);
    const bh = (0.12 + 0.88 * v) * maxH;
    c.fillStyle = heatColor(v);
    c.globalAlpha = 0.55 + 0.45 * v;
    roundRect(c, x - 2.5, floorY - bh, 5, bh, 2);
    c.fill();
  }
  c.globalAlpha = 1;
  drawPlayhead(c, p, playheadBeat);
}

function drawBeatLines(c: CanvasRenderingContext2D, p: Plot, len: number): void {
  for (let b = 0; b <= len + 0.001; b++) {
    const x = xForBeat(b, p);
    c.strokeStyle = b % spec.beatsPerBar === 0 ? pal.borderHi : pal.border;
    c.lineWidth = 1;
    c.beginPath();
    c.moveTo(Math.round(x) + 0.5, 0);
    c.lineTo(Math.round(x) + 0.5, p.ch);
    c.stroke();
  }
}

function drawPlayhead(c: CanvasRenderingContext2D, p: Plot, beat: number | null): void {
  if (beat == null) return;
  const x = xForBeat(clamp(beat, 0, lengthBeats()), p);
  c.save();
  c.shadowColor = pal.glow;
  c.shadowBlur = 8;
  c.strokeStyle = pal.playhead;
  c.lineWidth = 1.5;
  c.beginPath();
  c.moveTo(x, 0);
  c.lineTo(x, p.ch);
  c.stroke();
  c.restore();
}

function roundRect(c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number): void {
  const rr = Math.min(r, w / 2, h / 2);
  c.beginPath();
  c.moveTo(x + rr, y);
  c.arcTo(x + w, y, x + w, y + h, rr);
  c.arcTo(x + w, y + h, x, y + h, rr);
  c.arcTo(x, y + h, x, y, rr);
  c.arcTo(x, y, x + w, y, rr);
  c.closePath();
}

function buildRuler(): void {
  const ruler = document.getElementById("ruler");
  if (!ruler) return;
  ruler.replaceChildren();
  const len = lengthBeats();
  // Position ticks in the same plot the canvas uses (x0=GUTTER … cw-PAD_R) so the
  // ruler labels line up with the canvas beat lines + playhead.
  const cw = (document.getElementById("roll") as HTMLCanvasElement | null)?.clientWidth ?? ruler.clientWidth;
  const plotW = Math.max(1, cw - GUTTER - PAD_R);
  for (let b = 0; b < len; b++) {
    const tick = document.createElement("div");
    const isBar = b % spec.beatsPerBar === 0;
    tick.className = "tick" + (isBar ? " beat" : "");
    tick.style.left = `${GUTTER + (b / len) * plotW}px`;
    // beat number within the bar (1..beatsPerBar), like the design's ruler
    tick.textContent = `${(b % spec.beatsPerBar) + 1}`;
    ruler.appendChild(tick);
  }
}

/** Repaint everything that depends on the spec. `playheadBeat` is the audition
 *  position (null = no playhead, or the scrubber's manual position). */
function paint(playheadBeat: number | null = manualPlayhead): void {
  drawRoll(playheadBeat);
  drawBuildup(playheadBeat);
}

/** The "1 bar · N hits · accelerating" detail beside the PREVIEW label. */
function updatePreviewTitle(): void {
  const detail = document.getElementById("previewDetail");
  if (!detail) return;
  const barLabel = `${spec.lengthBars === 0.5 ? "½" : spec.lengthBars} bar`;
  const accel = ACCEL_TECHNIQUES.includes(spec.technique) ? " · accelerating" : "";
  detail.innerHTML = `<b>${barLabel}</b> · ${hits.length} hits${accel}`;
}

/** The velocity heat-ramp legend (rebuilt on theme change — reads the palette). */
function buildLegend(): void {
  const host = document.getElementById("velLegend");
  if (!host) return;
  host.innerHTML =
    `<span class="lbl">quiet</span>` +
    pal.heat.map((c) => `<span class="sw" style="background:${c}"></span>`).join("") +
    `<span class="lbl">hard</span>`;
}

/** Re-run the engine and repaint. Called on every control change. */
function refresh(): void {
  recompute();
  buildRuler();
  updatePreviewTitle();
  paint();
}

// ---- controls --------------------------------------------------------------
function el<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}

// Which genre category's chips are showing (defaults to the current genre's).
let genreCat = GENRE_GROUPS.find((g) => g.genres.includes(spec.genre))?.label ?? GENRE_GROUPS[0]!.label;

function buildGenres(): void {
  const sel = el<HTMLSelectElement>("genreCat");
  if (sel.options.length === 0) {
    for (const g of GENRE_GROUPS) {
      const o = document.createElement("option");
      o.value = g.label;
      o.textContent = g.label;
      sel.appendChild(o);
    }
    sel.onchange = () => {
      genreCat = sel.value;
      buildGenres();
    };
  }
  sel.value = genreCat;
  const group = GENRE_GROUPS.find((g) => g.label === genreCat) ?? GENRE_GROUPS[0]!;
  const grid = el("genreGrid");
  grid.replaceChildren();
  for (const gkey of group.genres) {
    const b = document.createElement("button");
    b.className = "chip" + (gkey === spec.genre ? " active" : "");
    b.textContent = GENRE_SHORT[gkey];
    b.onclick = () => {
      spec.genre = gkey;
      buildGenres();
      refresh();
    };
    grid.appendChild(b);
  }
}

// Minimal glyphs hinting at each technique's gesture.
const TECH_ICONS: Record<Technique, string> = {
  snareRoll: '<path d="M3 18V8M7 18V7M11 18V5M14 18V6M17 18V3M20 18V5"/>',
  tomCascade: '<path d="M3 6h5v4M8 10h5v4M13 14h6"/>',
  glitchStutter: '<path d="M3 12h3v-5h3v10h3v-7h3v4h3"/>',
  buildUp: '<path d="M3 19L21 5M3 19h18"/>',
  halfTimeDropIn: '<path d="M4 6h7v12H4zM15 10h5v8h-5z"/>',
  hatRun: '<path d="M3 12h1M7 12h1M11 12h1M15 12h1M19 12h1M5 7h1M9 7h1M13 7h1M17 7h1"/>',
  ghostGroove: '<path d="M5 16a2 2 0 100-1M12 9a3 3 0 100-1M18 16a1.5 1.5 0 100-1"/>',
};
function buildTechniques(): void {
  const grid = el("techGrid");
  grid.replaceChildren();
  (Object.keys(TECHNIQUE_LABELS) as Technique[]).forEach((tkey) => {
    const b = document.createElement("button");
    b.className = "tile" + (tkey === spec.technique ? " active" : "");
    b.innerHTML =
      `<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${TECH_ICONS[tkey]}</svg>` +
      `<span class="tname">${TECH_SHORT[tkey]}</span>`;
    b.onclick = () => {
      spec.technique = tkey;
      buildTechniques();
      refresh();
    };
    grid.appendChild(b);
  });
}

function buildSeg(
  id: string,
  options: Array<{ value: string; label: string }>,
  isActive: (v: string) => boolean,
  onPick: (v: string) => void,
): void {
  const seg = el(id);
  seg.replaceChildren();
  for (const o of options) {
    const b = document.createElement("button");
    b.className = isActive(o.value) ? "active" : "";
    b.textContent = o.label;
    b.onclick = () => onPick(o.value);
    seg.appendChild(b);
  }
}

const LENGTHS: Array<{ value: string; label: string; n: FillLength }> = [
  { value: "0.5", label: "½ bar", n: 0.5 },
  { value: "1", label: "1 bar", n: 1 },
  { value: "2", label: "2 bar", n: 2 },
];
function buildLength(): void {
  buildSeg(
    "lengthSeg",
    LENGTHS,
    (v) => Number(v) === spec.lengthBars,
    (v) => {
      spec.lengthBars = LENGTHS.find((l) => l.value === v)!.n;
      buildLength();
      refresh();
    },
  );
}

function buildContext(): void {
  buildSeg(
    "contextSeg",
    [
      { value: "groove", label: "Groove + fill" },
      { value: "fill", label: "Fill only" },
    ],
    (v) => v === spec.context,
    (v) => {
      spec.context = v as FillMode;
      buildContext();
      refresh();
    },
  );
}

function buildTargets(): void {
  buildSeg(
    "targets",
    ctx.availableTargets.map((t) => ({ value: t, label: TARGET_LABELS[t] })),
    (v) => v === target,
    (v) => {
      target = v as OutputTarget;
      buildTargets();
    },
  );
}

// Sliders. "Humanize" drives both timing + velocity jitter from one control.
interface SliderDef {
  key: string;
  name: string;
  get: () => number;
  set: (v: number) => void;
}
const SLIDERS: SliderDef[] = [
  { key: "intensity", name: "Intensity", get: () => spec.intensity, set: (v) => (spec.intensity = v) },
  { key: "density", name: "Density", get: () => spec.density, set: (v) => (spec.density = v) },
  { key: "swing", name: "Swing", get: () => spec.swing, set: (v) => (spec.swing = v) },
  {
    key: "humanize",
    name: "Humanize",
    get: () => spec.humTiming,
    set: (v) => {
      spec.humTiming = v;
      spec.humVel = v;
    },
  },
];
function buildSliders(): void {
  const host = el("sliders");
  host.replaceChildren();
  for (const s of SLIDERS) {
    const row = document.createElement("div");
    row.className = "slider";
    const srow = document.createElement("div");
    srow.className = "srow";
    const name = document.createElement("span");
    name.className = "sname";
    name.textContent = s.name;
    const val = document.createElement("span");
    val.className = "sval";
    val.textContent = `${Math.round(s.get() * 100)}%`;
    srow.append(name, val);
    const input = document.createElement("input");
    input.type = "range";
    input.min = "0";
    input.max = "100";
    const pct0 = Math.round(s.get() * 100);
    input.value = String(pct0);
    input.style.setProperty("--val", `${pct0}%`);
    input.oninput = () => {
      const v = Number(input.value) / 100;
      s.set(v);
      const pct = Math.round(v * 100);
      val.textContent = `${pct}%`;
      input.style.setProperty("--val", `${pct}%`); // grow the filled track
      refresh();
    };
    row.append(srow, input);
    host.appendChild(row);
  }
}

function buildActions(): void {
  el("reshuffle").onclick = () => {
    // A bigger deterministic jump — a genuinely different roll, same controls.
    spec.seed = (Math.imul(spec.seed || 1, 1664525) + 1013904223) >>> 0;
    refresh();
  };
  el("variations").onclick = () => {
    // Step to the next variation in sequence (small, browsable nudges).
    spec.seed = ((spec.seed || 0) + 1) >>> 0;
    refresh();
  };
}

function buildClipChip(): void {
  const chip = el("clipChip");
  let where: string;
  if (ctx.selection) {
    const beats = +(ctx.selection.end - ctx.selection.start).toFixed(2);
    where = `selection · ${beats} beat${beats === 1 ? "" : "s"}`;
  } else {
    where = ctx.hasClip ? ctx.clipName || "(unnamed clip)" : "no clip — creates one";
  }
  const meter = `${ctx.beatsPerBar}/4`;
  chip.innerHTML = `<span class="chip-dot"></span><b>${escapeHtml(where)}</b> · ${meter}${ctx.tempo ? ` · ${Math.round(ctx.tempo)} BPM` : ""}`;
}
function escapeHtml(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}

function buildLogo(): void {
  const svg = document.getElementById("logo") as unknown as SVGSVGElement;
  svg.replaceChildren();
  const cols = 6;
  const rows = 3;
  const cw = 4;
  const ch = 5;
  const gx = 1;
  const gy = 1.5;
  // accelerating-build pattern: taller, hotter columns toward the right
  const litHeight = [1, 1, 2, 2, 3, 3];
  for (let cIdx = 0; cIdx < cols; cIdx++) {
    for (let r = 0; r < rows; r++) {
      const lit = r >= rows - litHeight[cIdx]!;
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", String(cIdx * (cw + gx)));
      rect.setAttribute("y", String(r * (ch + gy)));
      rect.setAttribute("width", String(cw));
      rect.setAttribute("height", String(ch));
      rect.setAttribute("rx", "1");
      rect.style.fill = lit ? (cIdx >= 4 ? "var(--accent-b)" : "var(--accent-a)") : "var(--border)";
      svg.appendChild(rect);
    }
  }
}

// ---- theme switcher (Fill Forge palettes) ----------------------------------
const THEMES: Array<{ id: string; name: string; sw: string }> = [
  { id: "ignite", name: "Ignite", sw: "linear-gradient(120deg,#FFD56A,#FF8C32)" },
  { id: "plasma", name: "Plasma", sw: "linear-gradient(120deg,#22D3EE,#7C3AED)" },
  { id: "acid", name: "Acid", sw: "linear-gradient(120deg,#A3E635,#14B8A6)" },
  { id: "ember", name: "Ember", sw: "linear-gradient(120deg,#FF6A3D,#FF2D8E)" },
  { id: "mono", name: "Mono", sw: "linear-gradient(120deg,#FFFFFF,#9AA0AD)" },
];
const THEME_KEY = "breakdowns-theme";
let currentTheme = "ignite";

function loadTheme(): string {
  try {
    const v = localStorage.getItem(THEME_KEY);
    if (v && THEMES.some((t) => t.id === v)) return v;
  } catch {
    /* storage unavailable in this WebView — fall back to default */
  }
  return "ignite";
}
function applyTheme(id: string): void {
  currentTheme = id;
  if (id === "ignite") delete document.body.dataset.theme;
  else document.body.dataset.theme = id;
  try {
    localStorage.setItem(THEME_KEY, id);
  } catch {
    /* ignore — choice just won't persist */
  }
  pal = readPalette(); // CSS vars changed; canvas reads the new heat ramp
  renderThemeList();
  buildLegend();
  paint();
}
function renderThemeList(): void {
  const host = el("themeList");
  host.replaceChildren();
  for (const t of THEMES) {
    const row = document.createElement("button");
    row.className = "theme-row" + (t.id === currentTheme ? " active" : "");
    row.innerHTML =
      `<span class="sw" style="background:${t.sw}"></span>` +
      `<span class="nm">${t.name}</span>` +
      `<span class="ck">✓</span>`;
    row.onclick = () => {
      applyTheme(t.id);
      closeThemePop();
    };
    host.appendChild(row);
  }
}
const themePopOpen = (): boolean => !(el("themePop") as HTMLElement).hidden;
function openThemePop(): void {
  const pop = el("themePop");
  const btn = el("themeBtn");
  pop.hidden = false;
  const r = btn.getBoundingClientRect();
  const pw = pop.offsetWidth;
  pop.style.left = `${Math.max(8, Math.min(r.right - pw, window.innerWidth - pw - 8))}px`;
  pop.style.top = `${r.bottom + 6}px`;
}
function closeThemePop(): void {
  el("themePop").hidden = true;
}
function buildThemeUI(): void {
  applyTheme(loadTheme());
  el("themeBtn").onclick = (e) => {
    e.stopPropagation();
    themePopOpen() ? closeThemePop() : openThemePop();
  };
  document.addEventListener("click", (e) => {
    if (!themePopOpen()) return;
    const tgt = e.target as Node;
    if (!el("themePop").contains(tgt) && !el("themeBtn").contains(tgt)) closeThemePop();
  });
}

// ---- percussive audition (WebAudio — preview only, writes nothing) ----------
let audioCtx: AudioContext | null = null;
let audSources: AudioScheduledSourceNode[] = [];
let auditioning = false;
let audT0 = 0;
let audSpb = 0.5;
let audRaf: number | null = null;
let audEnd: number | null = null;
let manualPlayhead: number | null = null;

type VoiceClass = "kick" | "snareLike" | "tom" | "hat" | "cymbal";
function voiceClass(v: DrumVoice): VoiceClass {
  if (v === "kick") return "kick";
  if (v === "snare" || v === "clap" || v === "rim") return "snareLike";
  if (v === "lowTom" || v === "midTom" || v === "hiTom") return "tom";
  if (v === "closedHat" || v === "pedalHat" || v === "openHat") return "hat";
  return "cymbal";
}
function tomFreq(v: DrumVoice): number {
  return v === "hiTom" ? 220 : v === "midTom" ? 165 : 120;
}
function noiseBuffer(ac: AudioContext, secs: number): AudioBuffer {
  const n = Math.floor(ac.sampleRate * secs);
  const buf = ac.createBuffer(1, n, ac.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
  return buf;
}
function trackSource(s: AudioScheduledSourceNode): void {
  audSources.push(s);
}
/** Schedule one drum hit. Synthesis branches by voice class so a snare reads as
 *  noise, a kick as a pitch-dropping thump, toms tonal, hats/cymbals bright. */
function scheduleHit(ac: AudioContext, master: GainNode, h: VoiceHit, t: number): void {
  const vel = h.velocity / 127;
  const cls = voiceClass(h.voice);
  const g = ac.createGain();
  g.connect(master);

  if (cls === "kick") {
    const o = ac.createOscillator();
    o.type = "sine";
    o.frequency.setValueAtTime(150, t);
    o.frequency.exponentialRampToValueAtTime(48, t + 0.12);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.9 * vel + 0.1, t + 0.004);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
    o.connect(g);
    o.start(t);
    o.stop(t + 0.26);
    trackSource(o);
    return;
  }
  if (cls === "tom") {
    const o = ac.createOscillator();
    o.type = "sine";
    const f = tomFreq(h.voice);
    o.frequency.setValueAtTime(f * 1.4, t);
    o.frequency.exponentialRampToValueAtTime(f, t + 0.14);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.7 * vel + 0.08, t + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.26);
    o.connect(g);
    o.start(t);
    o.stop(t + 0.3);
    trackSource(o);
    return;
  }
  // noise-based: snareLike / hat / cymbal
  const isCym = cls === "cymbal";
  const isHat = cls === "hat";
  const open = h.voice === "openHat" || h.voice === "crash" || h.voice === "ride";
  const dur = isCym ? (open ? 0.5 : 0.18) : isHat ? (open ? 0.22 : 0.05) : 0.18;
  const src = ac.createBufferSource();
  src.buffer = noiseBuffer(ac, dur + 0.02);
  const hp = ac.createBiquadFilter();
  hp.type = "highpass";
  hp.frequency.value = isHat || isCym ? 7000 : 1400;
  const peak = (isHat ? 0.5 : isCym ? 0.45 : 0.8) * vel + 0.05;
  g.gain.setValueAtTime(peak, t);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  src.connect(hp);
  hp.connect(g);
  // snare body: a short triangle tone under the noise
  if (cls === "snareLike") {
    const o = ac.createOscillator();
    o.type = "triangle";
    o.frequency.setValueAtTime(190, t);
    const og = ac.createGain();
    og.gain.setValueAtTime(0.4 * vel, t);
    og.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    o.connect(og);
    og.connect(master);
    o.start(t);
    o.stop(t + 0.14);
    trackSource(o);
  }
  src.start(t);
  src.stop(t + dur + 0.02);
  trackSource(src);
}
function setAuditionUI(on: boolean): void {
  auditioning = on;
  // bottom-left transport: icon-only play/pause
  el("audition").classList.toggle("playing", on);
  el("audIcon").textContent = on ? "⏸" : "▶";
  // top-right labelled button
  el("auditionTop").classList.toggle("playing", on);
  el("audTopIcon").textContent = on ? "◼" : "▶";
  el("audTopLabel").textContent = on ? "Stop" : "Audition";
}
function stopAudition(): void {
  if (audRaf !== null) cancelAnimationFrame(audRaf);
  audRaf = null;
  if (audEnd !== null) clearTimeout(audEnd);
  audEnd = null;
  const now = audioCtx ? audioCtx.currentTime : 0;
  for (const s of audSources) {
    try {
      s.stop(now);
    } catch {
      /* already stopped */
    }
  }
  audSources = [];
  setAuditionUI(false);
  manualPlayhead = null;
  setScrub(0);
  paint(null);
}
/** Sync the scrubber position + filled track + "bar X.Y" readout to a beat. */
function setScrub(beat: number): void {
  const len = lengthBeats();
  const frac = clamp(len > 0 ? beat / len : 0, 0, 1);
  const scrub = el<HTMLInputElement>("scrub");
  scrub.value = String(Math.round(frac * 1000));
  scrub.style.setProperty("--val", `${frac * 100}%`);
  const ro = document.getElementById("posReadout");
  if (ro) {
    const bar = Math.floor(beat / spec.beatsPerBar) + 1;
    const beatInBar = Math.floor(beat % spec.beatsPerBar) + 1;
    ro.textContent = `bar ${bar}.${beatInBar}`;
  }
}

function auditionTick(): void {
  if (!auditioning || !audioCtx) return;
  const beat = (audioCtx.currentTime - audT0) / audSpb;
  paint(beat);
  setScrub(beat);
  audRaf = requestAnimationFrame(auditionTick);
}
function toggleAudition(): void {
  if (auditioning) return stopAudition();
  if (!hits.length) return;
  const AC = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext };
  const Ctor = AC.AudioContext ?? AC.webkitAudioContext;
  if (!Ctor) return;
  if (!audioCtx) audioCtx = new Ctor();
  const ac = audioCtx;
  void ac.resume?.();
  const tempo = ctx.tempo && ctx.tempo > 0 ? ctx.tempo : 120;
  const spb = 60 / tempo;
  const t0 = ac.currentTime + 0.08;
  const master = ac.createGain();
  master.gain.value = 0.5;
  master.connect(ac.destination);
  const len = lengthBeats();
  for (const h of hits) scheduleHit(ac, master, h, t0 + h.startTime * spb);
  audT0 = t0;
  audSpb = spb;
  setAuditionUI(true);
  audRaf = requestAnimationFrame(auditionTick);
  audEnd = window.setTimeout(
    () => {
      audEnd = null;
      stopAudition();
    },
    (len * spb + 0.5) * 1000,
  );
}

// ---- insert / cancel -------------------------------------------------------
function insert(): void {
  stopAudition();
  const notes = generateFill(spec).map((n) => ({
    pitch: n.pitch,
    startTime: n.startTime,
    duration: n.duration,
    velocity: n.velocity ?? 100,
  }));
  const req: FillRequest = {
    spec,
    target,
    notes,
    lengthBeats: lengthBeats(),
    name: `Fill Forge — ${GENRE_LABELS[spec.genre]} ${TECHNIQUE_LABELS[spec.technique]}`,
  };
  send(JSON.stringify(req));
}

// ---- boot ------------------------------------------------------------------
function init(): void {
  buildLogo();
  buildClipChip();
  buildGenres();
  buildTechniques();
  buildLength();
  buildContext();
  buildSliders();
  buildActions();
  buildTargets();
  buildThemeUI(); // applies saved theme + first palette read

  el("audition").onclick = toggleAudition;
  el("auditionTop").onclick = toggleAudition;
  const scrub = el<HTMLInputElement>("scrub");
  scrub.oninput = () => {
    if (auditioning) return; // playback drives it while playing
    manualPlayhead = (Number(scrub.value) / 1000) * lengthBeats();
    setScrub(manualPlayhead);
    paint(manualPlayhead);
  };
  el("insert").onclick = insert;
  el("cancel").onclick = () => {
    stopAudition();
    send(null);
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") insert();
    else if (e.key === "Escape") {
      if (auditioning) stopAudition();
      else send(null);
    } else if (e.key === " ") {
      e.preventDefault();
      toggleAudition();
    }
  });
  window.addEventListener("resize", () => paint());

  setScrub(0); // initialize the scrubber fill + "bar 1.1" readout
  refresh(); // first engine run + paint
}

init();
