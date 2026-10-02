/* Component markup for the shell. Ported 1:1 from previews/redesign-round/shared/shared.js
   so the DOM (and therefore the pixels) match the preview; the only differences are that
   data comes from LA.data (the Python session snapshot) instead of mock constants, that
   controls carry data-* hooks the controller needs, and that every manifest field is
   rendered (the preview truncated to 8). Nothing here names a colour, font or radius. */
(function () {
  const LA = (window.LA = window.LA || {});
  LA.data = {
    tools: [], tracks: [], targets: [], set: {}, connected: false, log: [], runs: {}, ticker: "", placement: null, confirm: null,
    genius: { busy: false, messages: [], agent: { slug: "", title: "Stock Genius" }, agents: [], model: "", status: { key: true }, pills: [] },
    prefs: { theme: "", themes: [], ports: {}, keys: [], agents: { enabled: [], available: [] }, paths: {}, tts: [], hasKey: false, customInstructions: { presets: [], setName: "", activeId: "" } },
  };
  LA.vals = {};   // field values typed so far: { toolId: { fieldId: value } }

  LA.esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const e = LA.esc;

  // "$0.10 in / $0.40 out" for a [input, output] $-per-1M-tokens pair, or "" when Python's
  // ai_pricing table (static, no provider exposes live pricing) doesn't know the model.
  LA.priceTag = (price) => (price ? ` · $${Number(price[0]).toFixed(2)} in / $${Number(price[1]).toFixed(2)} out` : "");

  const P = {
    bolt: "M13 2 4 14h7l-1 8 9-12h-7z",
    brain: "M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V4a3 3 0 0 0-3 0zm6 0a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1",
    gear: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-2a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V19a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H5a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3h0a1.6 1.6 0 0 0 1-1.5V5a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8v0a1.6 1.6 0 0 0 1.5 1H19a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z",
    right: "m9 6 6 6-6 6",
    down: "m6 9 6 6 6-6",
    x: "M6 6l12 12M18 6 6 18",
    play: "M7 4v16l13-8z",
    term: "m4 6 6 6-6 6M13 18h7",
    open: "M14 4h6v6M20 4l-9 9M18 14v6H4V6h6",
    "panel-l": "M4 5h16v14H4V5zM9 5v14",
    "panel-r": "M4 5h16v14H4V5zM15 5v14",
  };
  LA.icon = (n, s = 16) => `<svg class="la-ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${P[n] || ""}"/></svg>`;

  LA.byId = (id) => LA.data.tools.find((t) => t.id === id);
  LA.scopeOf = (t) => (t.scope === "set" ? { key: "set", label: "Set-Wide" } : t.ui === "webview" ? { key: "dialog", label: "Web Dialog" } : { key: "tracks", label: "Selected Tracks" });
  LA.scopePill = (t) => { const s = LA.scopeOf(t); return `<span class="la-pill" data-scope="${s.key}">${s.label}</span>`; };
  LA.toolStripe = (t) => `style="--tool:${e(t.accent || "#888")}"`;

  LA.pip = (label = true) => {
    const on = !!LA.data.connected;
    return `<span class="la-pip" data-on="${on}"><i></i>${label ? (on ? "Online" : "Offline") : ""}</span>`;
  };
  LA.chip = (k, v) => `<div class="la-chip"><span>${e(k)}</span><b>${e(v)}</b></div>`;
  LA.chips = () => { const s = LA.data.set || {}; return LA.chip("BPM", s.bpm == null ? "—" : s.bpm) + LA.chip("Sig", s.sig == null ? "—" : s.sig) + LA.chip("Tracks", LA.data.tracks.length); };
  LA.kind = (k) => `<span class="la-kind" data-kind="${e(k)}">${e(k)}</span>`;

  LA.isTargeted = (key) => LA.data.targets.indexOf(key) >= 0;
  LA.trackRow = (t) => {
    const on = LA.isTargeted(t.key);
    return `<label class="la-track${on ? " on" : ""}" data-act="toggle-track" data-key="${e(t.key)}">
      <span class="la-check" data-on="${on}"></span>
      <span class="la-track-n">${t.n}</span><span class="la-track-name">${e(t.name)}</span>${LA.kind(t.kind)}</label>`;
  };
  LA.trackList = () => LA.data.tracks.length
    ? LA.data.tracks.map(LA.trackRow).join("")
    : `<div class="la-track-empty">No tracks detected.<br>Connect to Live to list tracks.</div>`;
  LA.targetSummary = () => { const n = LA.data.targets.length; return n ? `${n} track${n > 1 ? "s" : ""} targeted` : "No tracks targeted"; };
  LA.quickPicks = () => `<div class="la-quick"><button class="la-btn mini" data-act="all">All</button><button class="la-btn mini" data-act="none">None</button><button class="la-btn mini" data-act="livesel">Live Sel</button></div>`;

  LA.toolCard = (t, opts = {}) => `<article class="la-card${opts.active ? " active" : ""}" ${LA.toolStripe(t)} data-act="open-tool" data-id="${e(t.id)}" tabindex="0">
      <i class="la-stripe"></i>
      <div class="la-card-top"><h3>${e(t.name)}</h3>${LA.scopePill(t)}</div>
      <p>${e(t.description || "Opens its own interactive action screen.")}</p>
      <div class="la-card-foot"><span class="la-btn primary sm">${t.ui === "webview" ? "Open Dialog " + LA.icon("open", 13) : "Open &amp; Configure " + LA.icon("right", 13)}</span></div>
    </article>`;

  /* ---- tool form ------------------------------------------------------------ */
  LA.fieldValue = (toolId, f) => { const v = (LA.vals[toolId] || {})[f.id]; return v === undefined ? f.default : v; };
  LA.field = (toolId, f) => {
    const hint = f.hint ? `<small>${e(f.hint)}</small>` : "";
    const v = LA.fieldValue(toolId, f);
    let ctl;
    if (f.type === "select" && f.options) ctl = `<select class="la-input" data-fid="${e(f.id)}">${f.options.map((o) => `<option${o === v ? " selected" : ""}>${e(o)}</option>`).join("")}</select>`;
    else if (f.type === "textarea") ctl = `<textarea class="la-input" rows="3" data-fid="${e(f.id)}">${e(v)}</textarea>`;
    else if (f.type === "file") ctl = `<div class="la-filepick"><input class="la-input" data-fid="${e(f.id)}" value="${e(v)}" placeholder="Choose a file…"><button class="la-btn ghost mini" data-act="pick-file" data-fid="${e(f.id)}">Browse</button></div>`;
    else ctl = `<input class="la-input" data-fid="${e(f.id)}" value="${e(v)}">`;
    const show = f.showIf ? ` data-showif="${e(JSON.stringify(f.showIf))}"` : "";
    return `<label class="la-field" data-field="${e(f.id)}"${show}><span>${e(f.label)}</span>${ctl}${hint}</label>`;
  };

  LA.scopeNote = (t) => {
    const s = LA.scopeOf(t);
    const n = LA.data.targets.length;
    return s.key === "set" ? "Runs on the whole Live Set — track selection is ignored."
      : s.key === "dialog" ? "Opens its own dialog window. Nothing is written until you confirm inside it."
      : `Runs on the ${n} ticked track${n === 1 ? "" : "s"} only.`;
  };

  LA.resultBox = (t) => {
    const r = LA.data.runs[t.id];
    return `<div class="la-result" data-result="${e(t.id)}" data-state="${e(r ? r.state : "")}"><span>RESULT</span>${e(r ? r.message : "Nothing run yet.")}</div>`;
  };

  LA.toolBody = (t) => {
    const running = (LA.data.runs[t.id] || {}).state === "running";
    const form = t.ui === "webview" ? "" : t.fields.map((f) => LA.field(t.id, f)).join("");
    const label = t.ui === "webview" ? "Open Interactive Dialog " + LA.icon("open", 14) : LA.icon("play", 13) + " " + e(t.runLabel || "Run Now");
    return `<div class="la-tool-body" ${LA.toolStripe(t)} data-tool="${e(t.id)}">
      <div class="la-tool-head"><i class="la-stripe"></i><div><h2>${e(t.name)}</h2>${LA.scopePill(t)}</div></div>
      <p class="la-lede">${e(t.description)}</p>
      <div class="la-note" data-scope-note>${e(LA.scopeNote(t))}</div>
      ${form}
      <div class="la-runrow"><button class="la-btn primary" data-act="run"${running ? " disabled" : ""}>${label}</button></div>
      ${LA.resultBox(t)}</div>`;
  };

  /* ---- Genius chat ----------------------------------------------------------- */
  // A tiny, safe markdown: everything is HTML-escaped FIRST, then only fences, `code` and **bold** are
  // re-introduced, so model output can never inject markup.
  LA.md = (text) => {
    const chunks = String(text == null ? "" : text).split(/(```[\s\S]*?```)/g);
    return chunks.map((chunk, i) => {
      if (i % 2) return `<pre class="la-code">${e(chunk.slice(3, -3).replace(/^[^\n]*\n/, (m) => (/^\w*\n$/.test(m) ? "" : m)))}</pre>`;
      // The block is its own line box, so the newlines that merely separate it from the prose
      // (kept literally by white-space: pre-wrap) would show up as blank lines.
      let t = chunk;
      if (i > 0) t = t.replace(/^\n/, "");
      if (i < chunks.length - 1) t = t.replace(/\n{1,2}$/, "");
      return e(t).replace(/`([^`\n]+)`/g, "<code>$1</code>").replace(/\*\*([^*\n]+)\*\*/g, "<b>$1</b>");
    }).join("");
  };

  LA.callChip = (p) => {
    const mark = p.state === "ok" ? " ✓" : p.state === "error" ? " ✗" : " …";
    const cls = p.state === "ok" ? "ok" : p.state === "error" ? "err" : "run";
    return `<span class="la-call ${cls}"${p.note ? ` title="${e(p.note)}"` : ""}>${e(p.name)}${mark}</span>`;
  };

  LA.botParts = (m) => {
    const streaming = m.state === "streaming";
    let out = "", calls = "";
    const flush = () => { if (calls) { out += `<div class="la-calls">${calls}</div>`; calls = ""; } };
    for (const p of m.parts) {
      if (p.kind === "call") { calls += LA.callChip(p); continue; }
      flush();
      if (p.kind === "think") out += `<details class="la-think"${streaming ? " open" : ""}><summary>Thinking</summary><div class="la-msg-text">${e(p.text)}</div></details>`;
      else out += `<div class="la-msg-text">${LA.md(p.text)}</div>`;
    }
    flush();
    if (!m.parts.length && streaming) out = `<div class="la-msg-text la-dim">Thinking…</div>`;
    if (m.state === "stopped") out += `<div class="la-msg-text la-dim">■ Stopped</div>`;
    if (m.error) out += `<div class="la-msg-text la-msg-err">${e(m.error)}</div>`;
    return out;
  };

  LA.bubble = (m) => m.role === "system"
    ? `<div class="la-sys" data-msg="${m.id}">${e(m.text)}</div>`
    : m.role === "user"
      ? `<div class="la-bubble user" data-msg="${m.id}"><span class="la-who">You</span><div class="la-msg-text">${e(m.text)}</div></div>`
      : `<div class="la-bubble bot" data-msg="${m.id}"><span class="la-who">Genius</span>${LA.botParts(m)}</div>`;

  LA.chat = () => `<div class="la-chat">${LA.data.genius.messages.map(LA.bubble).join("")}</div>`;

  LA.agentChips = () => {
    const G = LA.data.genius;
    const agent = G.agents.length
      ? `<select class="la-input la-agent-select" data-change="genius-agent" aria-label="Agent">${[{ slug: "", title: "Stock Genius" }, ...G.agents].map((a) => `<option value="${e(a.slug)}"${a.slug === G.agent.slug ? " selected" : ""}>${e(a.title)}</option>`).join("")}</select>`
      : `<span class="la-tag">${e(G.agent.title)}</span>`;
    const clear = !LA.data.demo && G.messages.length > 1 ? `<button class="la-btn ghost mini" data-act="genius-clear">Clear chat</button>` : "";
    return `${clear}${agent}${LA.ciSelect()}${LA.modelSelect()}`;
  };

  // Key + model picker: one optgroup per saved key, one option per model that
  // key can actually use. Python lists the provider's chat models and sends each
  // one a tiny tool-enabled test (shell_prefs.key_models); only models that
  // answered are here, and ones that were only busy (429/503) say so. Until a
  // key's test finishes, its group shows its saved model and "checking models…".
  // A saved model that failed the test stays visible, marked unavailable, only
  // for the key in use, so the header never goes blank. The value is
  // "keyId|model"; keys themselves never reach the page, only labels. Price is a
  // subtle $/1M-token tag from Python's static ai_pricing table -- absent for any
  // model that table doesn't recognize.
  LA.modelSelect = () => {
    const G = LA.data.genius, P = LA.data.prefs || {};
    const keys = P.keys || [];
    const byKey = P.modelsByKey || {}, busyBy = P.busyByKey || {}, priceBy = P.priceByKey || {};
    if (LA.data.demo || !keys.length || !P.activeKeyId) return `<span class="la-tag mono">${e(G.model)}</span>`;
    const groups = keys.map((k) => {
      const active = k.id === P.activeKeyId;
      const tested = Object.prototype.hasOwnProperty.call(byKey, k.id);
      const busy = busyBy[k.id] || [];
      const price = priceBy[k.id] || {};
      const models = tested ? [...byKey[k.id]] : [k.model].filter(Boolean);
      const mine = active ? G.model : k.model;
      const lost = tested && mine && !models.includes(mine) && active;
      if (lost) models.unshift(mine);
      const opts = models.map((m) => {
        const on = active && m === G.model;
        const tag = lost && m === mine ? " (unavailable)" : busy.includes(m) ? " (busy)" : "";
        return `<option value="${e(k.id + "|" + m)}"${on ? " selected" : ""}>${e(k.label)} · ${e(m)}${tag}${e(LA.priceTag(price[m]))}</option>`;
      });
      if (!tested) opts.push(`<option disabled>${e(k.label)} · checking models…</option>`);
      else if (!models.length) opts.push(`<option disabled>${e(k.label)} · no working models</option>`);
      return `<optgroup label="${e(k.label)}">${opts.join("")}</optgroup>`;
    }).join("");
    return `<select class="la-input la-model-select mono" data-change="genius-model" aria-label="API key and model" title="API key and model: only models that passed a live test are listed (switch between replies); price, when shown, is $/1M tokens in/out">${groups}</select>`;
  };

  // Custom-instruction preset switcher, beside the agent picker. The preset
  // library is global so rules are reusable, but the CHOICE is saved per Live
  // Set -- hence the tooltip naming the Set the choice applies to. Hidden
  // entirely until at least one preset exists, so the chat header stays quiet
  // for anyone not using the feature.
  LA.ciSelect = () => {
    const ci = (LA.data.prefs && LA.data.prefs.customInstructions) || null;
    if (!ci || !(ci.presets || []).length) return "";
    const where = ci.setName ? `for "${ci.setName}"` : "for this Live Set";
    const opts = [{ id: "", name: "No custom instructions" }, ...ci.presets]
      .map((p) => `<option value="${e(p.id)}"${p.id === (ci.activeId || "") ? " selected" : ""}>${e(p.name)}</option>`)
      .join("");
    return `<select class="la-input la-ci-select" data-change="genius-ci" aria-label="Custom instructions" title="Custom instructions ${e(where)}">${opts}</select>`;
  };

  // Shown only when Genius cannot answer at all. Never contains the key itself.
  LA.geniusNote = () => {
    const G = LA.data.genius;
    if (G.status.key) return "";
    return `<div class="la-note">Genius has no API key yet. Add one in Preferences → AI provider. <button class="la-btn ghost mini" data-act="settings">Open Preferences</button></div>`;
  };

  LA.sendButton = () => (LA.data.genius.busy
    ? `<button class="la-btn" data-act="genius-stop" data-genius-btn>■ Stop</button>`
    : `<button class="la-btn primary" data-act="genius-send" data-genius-btn>Send</button>`);

  LA.composer = (draft = "") => `<div class="la-composer"><div class="la-prompts">${LA.data.genius.pills.map((p, i) => `<button class="la-btn ghost mini" data-act="genius-pill" data-i="${i}">${e(p.label)}</button>`).join("")}</div>
    <div class="la-compose-row"><textarea class="la-input" rows="1" data-genius-input placeholder="Ask Genius to work on your Set…">${e(draft)}</textarea>${LA.sendButton()}</div></div>`;

  /* ---- chrome ---------------------------------------------------------------- */
  LA.consoleLines = () => LA.data.log.map((l) => `<div class="la-logline"><time>${e(l[0])}</time><em>${e(l[1])}</em><span>${e(l[2])}</span></div>`).join("");
  LA.statusbar = (S, showTargets = true) => `<div class="la-statusbar"><span class="grow">${e(LA.data.ticker)}${showTargets ? " · " + e(LA.targetSummary()) : ""}</span>
    <button class="la-btn mini ghost" data-act="copy-log">Copy</button>
    <button class="la-btn mini${S.console ? " on" : ""}" data-act="console">${LA.icon("term", 12)} ${S.console ? "Hide log" : "Console log"}</button></div>`;
  LA.consoleDrawer = (S) => (S.console ? `<div class="la-console la-scroll">${LA.consoleLines()}</div>` : "");
  LA.diagPanel = () => `<span class="la-section-title">Bridge diagnostics</span>
    <p class="la-muted" style="margin:4px 0 10px">${LA.data.connected ? "Bridge host: " + e(LA.data.hostTrack || "audio track") + " · “Live Actions Bridge”" : "Bridge offline — drop “Live Actions Bridge.amxd” on an audio track."}</p>
    <div class="la-quick"><button class="la-btn mini" data-act="diag-ping">Ping</button><button class="la-btn mini" data-act="diag-status">Status</button><button class="la-btn mini" data-act="diag-sync">Sync</button><button class="la-btn mini" data-act="diag-reset">Reset</button></div>`;
  LA.settingsModal = (S) => (S.settings ? `<div class="la-scrim" data-act="close-settings"></div><div class="la-modal"><div class="la-modal-head">${LA.Prefs.head()}</div><div class="la-modal-body la-scroll">${LA.Prefs.body()}</div></div>` : "");

  /* "Add to Live Set": the host tool's file is made; pick the clip slot it goes into. Built from the Preferences modal's own
     parts (scrim, modal, head, single-choice keyrows, primary / ghost buttons). `req` is Python's pending question
     (D.placement); `P` is the page-side choice ({ sel, warn }). */
  LA.slotRow = (s, sel) => `<div class="la-keyrow${sel === s.index ? " on" : ""}" data-act="place-pick" data-i="${s.index}" tabindex="0" role="radio" aria-checked="${sel === s.index}"><span class="la-check" data-on="${sel === s.index}"></span><b class="la-slot-n">${s.n}</b><span class="la-slot-name">${s.has ? (s.name ? "“" + e(s.name) + "”" : "occupied") : "empty"}</span>${s.has ? `<span class="la-muted">has a clip</span>` : ""}</div>`;
  LA.placeModal = (req, P) => (req ? `<div class="la-scrim la-place-scrim"></div><div class="la-modal la-place" role="dialog" aria-modal="true" aria-label="Place ${e(req.tool)}">
    <div class="la-modal-head"><b class="la-title" style="font-size:16px">Place ${e(req.tool)}</b><button class="la-iconbtn" data-act="place-cancel" aria-label="Cancel">${LA.icon("x")}</button></div>
    <div class="la-modal-body"><p class="la-lede">Choose a clip slot on “${e(req.track)}”:</p>
      <div class="la-slots la-scroll" role="radiogroup">${req.slots.map((s) => LA.slotRow(s, P.sel)).join("")}</div>
      <div class="la-note la-warn" data-place-warn${P.warn ? "" : " hidden"}>${e(P.warn)}</div>
      <div class="la-runrow"><button class="la-btn primary" data-act="place-ok">Place</button><button class="la-btn ghost" data-act="place-cancel">Cancel</button></div>
    </div></div>` : "");

  /* "May I run this?": a Genius tool that spends the user's API credit asks first. Same modal parts as
     the slot picker; `req` is Python's pending question (D.confirm) and `C` the page-side state ({ remember }).
     The remember box is worded per session on purpose -- ConfirmPicker holds it in memory, nothing is saved. */
  LA.confirmRow = (r) => `<div class="la-crow"><span class="la-clabel">${e(r.label)}</span><span class="la-cvalue">${e(r.value)}</span></div>`;
  LA.confirmModal = (req, C) => (req ? `<div class="la-scrim la-place-scrim"></div><div class="la-modal la-place la-confirm" role="dialog" aria-modal="true" aria-label="${e(req.title)}">
    <div class="la-modal-head"><b class="la-title" style="font-size:16px">${e(req.title)}</b><button class="la-iconbtn" data-act="confirm-cancel" aria-label="Cancel">${LA.icon("x")}</button></div>
    <div class="la-modal-body">${req.body ? `<p class="la-lede">${e(req.body)}</p>` : ""}
      <div class="la-crows la-scroll">${req.rows.map(LA.confirmRow).join("")}</div>
      <div class="la-keyrow${C.remember ? " on" : ""}" data-act="confirm-remember" tabindex="0" role="checkbox" aria-checked="${C.remember}"><span class="la-check" data-on="${C.remember}"></span><span>${e(req.rememberLabel)}</span></div>
      <div class="la-runrow"><button class="la-btn primary" data-act="confirm-ok">${e(req.confirmLabel)}</button><button class="la-btn ghost" data-act="confirm-cancel">Cancel</button></div>
    </div></div>` : "");

  LA.filterTools = (S) => LA.data.tools.filter((t) => !(S.filter && S.filter !== "all" && LA.scopeOf(t).key !== S.filter));
  LA.filterChips = (S) => [["all", "All"], ["tracks", "Selected tracks"], ["set", "Set-wide"], ["dialog", "Dialogs"]]
    .map(([k, l]) => `<button class="la-btn mini ghost${(S.filter || "all") === k ? " on" : ""}" data-act="filter" data-k="${k}">${l}</button>`).join("");
})();
