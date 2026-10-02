/* Preferences modal. Markup is ported from previews/redesign-round/shared/shared.js settingsBody()
   (Appearance / Connection / AI provider / Agents / Folders, same classes, same order) with the real
   behaviour added. Python owns every value: each control commits with ONE call to api().prefs(op, args),
   which validates, persists and returns a fresh MASKED snapshot -- so there is no Save button, and an API
   key only ever travels page -> Python (from a password input), never back. This file only keeps what has
   not been committed yet (drafts), which panels are open, and the last result of a network probe. */
(function () {
  const LA = window.LA;
  const e = LA.esc;
  let C = null;                                   // { D, S, api, mark, app } handed over by app.js
  const UI = (LA.prefsUi = {
    themesOpen: false,                            // collapsed by default (the user's answer, 2026-09-20)
    addKey: false, modelPanel: false, showKey: false, confirmDel: "",
    draft: {}, err: {}, note: {}, busy: {},
    models: [], busyModels: [], modelPricing: {}, test: null, agentOpen: {}, agentGroups: {}, agentPick: "",
    tts: null, ttsOpen: {}, voices: {}, saved: 0,
    // Custom instructions: whole section collapsed by default, each preset card
    // collapsed too, and delete needs two clicks (a preset is not recoverable).
    ciOpen: false, ciCardOpen: {}, ciConfirmDel: "",
    nk: { key: "", label: "", provider: "", base: "", model: "" },
  });
  const P = () => C.D.prefs;
  const val = (k, committed) => (UI.draft[k] !== undefined ? UI.draft[k] : committed);
  const msg = (k) => (UI.err[k] ? `<small class="la-err">${e(UI.err[k])}</small>` : UI.note[k] ? `<small class="la-muted">${e(UI.note[k])}</small>` : "");
  const PROVIDERS = [["", "(detect / default)"], ["xai", "xAI"], ["openai", "OpenAI"], ["gemini", "Gemini"], ["anthropic", "Anthropic"]];
  const TTS_PROVIDERS = ["xai", "openai", "cartesia"];

  /* ---- markup ------------------------------------------------------------------ */
  const field = (label, pf, committed, extra = "") =>
    `<label class="la-field"><span>${e(label)}</span><input class="la-input" data-pf="${pf}" value="${e(val(pf, committed))}"${extra}>${msg(pf)}</label>`;
  const pathField = (label, key) =>
    `<label class="la-field"><span>${e(label)}</span><div class="la-filepick"><input class="la-input" data-pf="path:${key}" value="${e(val("path:" + key, P().paths[key]))}"><button class="la-btn ghost mini" data-act="pf-browse" data-key="${key}">Browse</button></div>${msg("path:" + key)}</label>`;

  const appearance = () => {
    const p = P(), open = UI.themesOpen, cur = p.themes.find((t) => t.slug === p.theme) || {};
    return `<section class="la-collapsible" data-open="${open}"><button class="la-collapse" data-act="pf-theme-toggle" aria-expanded="${open}">
        <span class="la-collapse-ic">${LA.icon(open ? "down" : "right", 16)}</span><h4>Appearance</h4>
        <span class="la-tag">${e(cur.label || "")}</span><span class="la-muted la-collapse-n">${p.themes.length} theme${p.themes.length === 1 ? "" : "s"}</span></button>
      ${open ? `<p class="la-muted">A theme is one file. Pick any design kit — layout never changes.</p>
      <div class="la-swatches">${p.themes.map((t) => `<button class="la-swatch${p.theme === t.slug ? " on" : ""}" data-act="pf-theme" data-slug="${e(t.slug)}"><i style="background:linear-gradient(135deg, ${e(t.bg)} 0 34%, ${e(t.surface)} 34% 62%, ${e(t.accent)} 62% 100%)"></i>${e(t.label)}</button>`).join("")}</div>${msg("theme")}` : ""}</section>`;
  };

  const connection = () => {
    const p = P();
    return `<section><h4>Connection</h4><div class="la-two">${field("App listen port (UDP)", "listen", p.ports.listen)}${field("Bridge send port (UDP)", "bridge", p.ports.bridge)}</div>${p.restart ? `<p class="la-muted la-restart">Restart Live Actions to use the new ports.</p>` : ""}</section>`;
  };

  const keyRow = (k) => {
    const on = k.id === P().activeKeyId;
    const del = UI.confirmDel === k.id
      ? `<button class="la-row-x warn" data-act="pf-del-key" data-id="${e(k.id)}">Delete?</button>`
      : `<button class="la-row-x" data-act="pf-del-key" data-id="${e(k.id)}" aria-label="Delete key" title="Delete key">✕</button>`;
    return `<div class="la-keyrow${on ? " on" : ""}" data-act="pf-use-key" data-id="${e(k.id)}" tabindex="0"><span class="la-check" data-on="${on}"></span><b>${e(k.label)}</b>${k.model ? `<span class="la-tag mono">${e(k.model)}</span>` : ""}<span class="la-muted">${e(k.masked)}</span>${del}</div>`;
  };

  const addKeyPanel = () => {
    const n = UI.nk, busy = UI.busy.detect;
    return `<div class="la-subpanel">
      <label class="la-field"><span>API key (any provider)</span><div class="la-filepick"><input class="la-input" data-pf="nk.key" type="${UI.showKey ? "text" : "password"}" autocomplete="off" spellcheck="false" value="${e(n.key)}" placeholder="Paste a key — it is only sent to Python"><button class="la-btn ghost mini" data-act="pf-show-key">${UI.showKey ? "Hide" : "Show"}</button></div>${msg("nk")}</label>
      <div class="la-two"><label class="la-field"><span>Label</span><input class="la-input" data-pf="nk.label" value="${e(n.label)}" placeholder="e.g. xAI · Main key"></label>
        <label class="la-field"><span>Provider</span><select class="la-input" data-pf="nk.provider">${PROVIDERS.map(([v, l]) => `<option value="${v}"${n.provider === v ? " selected" : ""}>${l}</option>`).join("")}</select></label></div>
      <div class="la-two"><label class="la-field"><span>Model</span><select class="la-input" data-pf="nk.model">${modelOptions(UI.models, n.model, UI.busyModels, UI.modelPricing)}</select></label>
        <label class="la-field"><span>API endpoint</span><input class="la-input" data-pf="nk.base" value="${e(n.base)}" placeholder="filled in from the provider"></label></div>
      <div class="la-runrow"><button class="la-btn ghost" data-act="pf-detect"${busy ? " disabled" : ""}>${busy ? "Detecting…" : "Detect provider"}</button><button class="la-btn primary" data-act="pf-save-key">Save key</button><button class="la-btn ghost" data-act="pf-add-toggle">Cancel</button></div>
      ${UI.note.detect ? `<p class="la-muted">${e(UI.note.detect)}</p>` : ""}</div>`;
  };

  // Model dropdown fed by the live-tested list (only models that answered). The
  // current value is kept as an option even when it is not in the list, marked,
  // so opening the panel never silently changes the model. `pricing`, when present,
  // adds a subtle $/1M-token tag from Python's static ai_pricing table.
  const modelOptions = (list, cur, busy, pricing) => {
    const opts = [...list];
    if (cur && !opts.includes(cur)) opts.unshift(cur);
    if (!opts.length) return `<option value="">Fetch models first (↻ Refresh models / Detect provider)</option>`;
    return opts.map((m) => `<option value="${e(m)}"${m === cur ? " selected" : ""}>${e(m)}${list.includes(m) ? ((busy || []).includes(m) ? " (busy)" : "") : " (not tested)"}${e(LA.priceTag((pricing || {})[m]))}</option>`).join("");
  };
  const keyModels = () => { const p = P(); return (p.modelsByKey || {})[p.activeKeyId] || UI.models; };

  const modelPanel = () => {
    const p = P(), busy = UI.busy.models;
    return `<div class="la-subpanel">
      <div class="la-two"><label class="la-field"><span>Model</span><select class="la-input" data-pf="model">${modelOptions(keyModels(), val("model", p.model), (p.busyByKey || {})[p.activeKeyId], (p.priceByKey || {})[p.activeKeyId] || UI.modelPricing)}</select>${msg("model")}</label>
        <label class="la-field"><span>API endpoint</span><input class="la-input" data-pf="apiBase" value="${e(val("apiBase", p.apiBase))}">${msg("apiBase")}</label></div>
      <div class="la-runrow"><button class="la-btn ghost" data-act="pf-refresh-models"${busy || !p.hasKey ? " disabled" : ""}>${busy ? "Fetching…" : "↻ Refresh models"}</button></div>
      ${msg("models")}</div>`;
  };

  const aiProvider = () => {
    const p = P();
    const testBox = UI.test ? `<div class="la-result" data-state="${UI.test.pending ? "running" : UI.test.ok ? "done" : "error"}"><span>KEY TEST</span>${e(UI.test.pending ? "Testing the active key…" : (UI.test.ok ? "Success: " : "Connection failed: ") + UI.test.message)}</div>` : "";
    return `<section><h4>AI provider</h4>
      ${p.keys.length ? p.keys.map(keyRow).join("") : `<p class="la-muted">No saved keys yet — use “Add key”.</p>`}
      ${msg("keys")}
      <div class="la-runrow"><button class="la-btn ghost" data-act="pf-test"${p.hasKey && !(UI.test && UI.test.pending) ? "" : " disabled"}>Test key</button><button class="la-btn ghost" data-act="pf-add-toggle">Add key</button>${p.hasKey ? `<button class="la-btn ghost" data-act="pf-model-toggle">Model &amp; endpoint</button>` : ""}</div>
      ${testBox}${UI.addKey ? addKeyPanel() : ""}${UI.modelPanel && p.hasKey ? modelPanel() : ""}
</section>`;
  };

  const agentPanel = (a) => {
    const groups = UI.agentGroups[a.slug];
    const body = !groups ? `<p class="la-muted">Loading tools…</p>` : groups.map((g) => `<div class="la-toolgroup"><div class="la-toolgroup-head"><b>${e(g.name)}</b><span><button class="la-btn ghost mini" data-act="pf-agent-group" data-slug="${e(a.slug)}" data-group="${e(g.name)}" data-on="1">All</button><button class="la-btn ghost mini" data-act="pf-agent-group" data-slug="${e(a.slug)}" data-group="${e(g.name)}" data-on="0">None</button></span></div>
      ${g.tools.map((t) => `<label class="la-tool"><input type="checkbox" data-ptool="1" data-slug="${e(a.slug)}" data-name="${e(t.name)}"${t.on ? " checked" : ""}> ${e(t.name)}</label>`).join("")}</div>`).join("");
    return `<div class="la-subpanel"><div class="la-runrow"><button class="la-btn ghost mini" data-act="pf-agent-remove" data-slug="${e(a.slug)}">Remove this agent</button></div>${body}</div>`;
  };

  const agents = () => {
    const p = P(), active = (C.D.genius.agent || {}).slug || "";
    const stock = `<div class="la-keyrow${active === "" ? " on" : ""}" data-act="pf-pick-agent" data-slug="" tabindex="0"><span class="la-check" data-on="${active === ""}"></span><b>Stock Genius</b><span class="la-muted">all tools enabled</span></div>`;
    const rows = p.agents.enabled.map((a) => `<div class="la-keyrow${active === a.slug ? " on" : ""}" data-act="pf-pick-agent" data-slug="${e(a.slug)}" tabindex="0"><span class="la-check" data-on="${active === a.slug}"></span><b>${e(a.title)}</b><span class="la-muted">${a.on === a.total ? "all tools enabled" : `${a.on} of ${a.total} tools`}</span><button class="la-row-x" data-act="pf-agent-open" data-slug="${e(a.slug)}" aria-label="Choose tools" title="Choose tools">${UI.agentOpen[a.slug] ? "▾" : "▸"}</button></div>${UI.agentOpen[a.slug] ? agentPanel(a) : ""}`).join("");
    const av = p.agents.available;
    const pick = av.length ? `<div class="la-runrow"><select class="la-input la-agent-pick" data-pf="agentPick">${av.map((a) => `<option value="${e(a.slug)}"${(UI.agentPick || av[0].slug) === a.slug ? " selected" : ""}>${e(a.title)}</option>`).join("")}</select><button class="la-btn ghost" data-act="pf-agent-enable">Enable agent</button></div>` : "";
    return `<section><h4>Agents</h4>${stock}${rows}${pick}${msg("agents")}</section>`;
  };

  const folders = () => `<section><h4>Folders</h4>${pathField("Tools folder", "tools_dir")}${pathField("Knowledge folder", "knowledge_dir")}${pathField("Music / audio database folder", "music_db_dir")}${pathField("Samples folder", "samples_dir")}${pathField("Plugin manuals folder (optional)", "plugin_docs_dir")}</section>`;

  /* -- TTS profiles: a working list; the page edits it, Python is sent the whole list on every change -- */
  const ttsList = () => {
    if (!UI.tts) UI.tts = P().tts.map((t, i) => ({ uid: "s" + i, src: t.src, name: t.name, provider: t.provider, key_mode: "keep", api_key: "", vault_id: "", hint: t.hint, voiceId: t.voiceId, model: t.model, speed: t.speed, language: t.language }));
    return UI.tts;
  };
  const ttsCard = (t) => {
    const open = UI.ttsOpen[t.uid] !== undefined ? UI.ttsOpen[t.uid] : !t.name;
    const vault = P().keys;
    // Pinning is by saved name (the same identity save_tts already keys profiles by),
    // matched against the page's own draft name -- so it can look briefly "off" while
    // a rename of the pinned card itself is mid-edit, same as every other draft field.
    const pinned = !!t.name && t.name === (P().activeTtsProfile || "");
    const pinTitle = pinned
      ? "Pinned — every generation (Genius and the Tool screen) uses only this profile's voice. Click to unpin."
      : t.name ? "Pin — lock every generation to only this voice" : "Name this profile first";
    const inp = (label, k, extra = "") => `<label class="la-field"><span>${label}</span><input class="la-input" data-pfc="${k}" data-uid="${t.uid}" value="${e(t[k])}"${extra}></label>`;
    return `<div class="la-ttscard"><div class="la-ttshead">
      <span class="la-check" data-act="pf-tts-pin" data-name="${e(pinned ? "" : t.name)}" data-on="${pinned}" title="${e(pinTitle)}" role="checkbox" aria-checked="${pinned}"${t.name ? "" : ' aria-disabled="true"'}></span>
      <button class="la-row-x" data-act="pf-tts-toggle" data-uid="${t.uid}" aria-label="Expand">${open ? "▾" : "▸"}</button><b data-act="pf-tts-toggle" data-uid="${t.uid}">${e(t.name || "(unnamed profile)")}</b><span class="la-tag mono">${e(t.provider)}</span>${pinned ? `<span class="la-tag" title="No other saved profile, and no per-run voice override, is used while this is pinned">only voice used</span>` : ""}<button class="la-row-x" data-act="pf-tts-remove" data-uid="${t.uid}" aria-label="Remove profile" title="Remove profile">✕</button></div>
      ${open ? `<div class="la-two">${inp("Profile name", "name")}<label class="la-field"><span>Provider</span><select class="la-input" data-pfc="provider" data-uid="${t.uid}">${TTS_PROVIDERS.map((p) => `<option${t.provider === p ? " selected" : ""}>${p}</option>`).join("")}</select></label></div>
        <div class="la-two"><label class="la-field"><span>API key</span><input class="la-input" type="password" autocomplete="off" data-pfc="api_key" data-uid="${t.uid}" value="${e(t.key_mode === "typed" ? t.api_key : "")}" placeholder="${e(t.key_mode === "vault" ? "using a saved key" : t.hint || "paste a key")}"></label>
          <label class="la-field"><span>…or use a saved key</span><select class="la-input" data-pfc="vault" data-uid="${t.uid}"><option value="">choose…</option>${vault.map((k) => `<option value="${e(k.id)}"${t.vault_id === k.id ? " selected" : ""}>${e(k.label)}</option>`).join("")}</select></label></div>
        <div class="la-two"><label class="la-field"><span>Voice ID</span><input class="la-input" data-pfc="voiceId" data-uid="${t.uid}" list="vl-${t.uid}" value="${e(t.voiceId)}"></label>${inp("Model", "model")}</div>
        <div class="la-two">${inp("Speed", "speed")}${inp("Language", "language")}</div>
        <datalist id="vl-${t.uid}">${(UI.voices[t.uid] || []).map((v) => `<option value="${e(v.voiceId)}">${e((v.custom ? "★ " : "") + v.name)}</option>`).join("")}</datalist>
        <div class="la-runrow"><button class="la-btn ghost mini" data-act="pf-tts-detect" data-uid="${t.uid}"${UI.busy["d" + t.uid] ? " disabled" : ""}>Detect provider</button><button class="la-btn ghost mini" data-act="pf-tts-voices" data-uid="${t.uid}"${UI.busy["v" + t.uid] ? " disabled" : ""}>↻ Refresh voices</button></div>${msg("tts:" + t.uid)}` : ""}</div>`;
  };
  const audio = () => `<section><h4>Audio tools</h4>${pathField("TTS output folder (blank = Samples folder\\TTS)", "tts_output_dir")}${pathField("Audio Sample output folder (blank = Samples folder\\Audio Samples)", "audio_sample_output_dir")}${pathField("ffmpeg.exe path (blank = use PATH)", "ffmpeg_path")}
    <p class="la-muted" style="margin-top:12px">Profiles (provider + API key + voice) used by the TTS Vocal tool. Check a profile's box to pin it as the only voice every generation may use — Genius and the Tool screen can no longer pick or override a different one until it's unchecked.</p>${ttsList().map(ttsCard).join("")}${msg("tts")}
    <div class="la-runrow"><button class="la-btn ghost" data-act="pf-tts-add">+ Add profile</button></div></section>`;

  /* Genius custom instructions. The preset library is global so one set of
     house rules is reusable across projects; which preset is ACTIVE is saved
     per Live Set, which is why "Use here" is a per-card action rather than a
     single radio list. The same choice is switchable from the dropdown beside
     the agent picker in the chat header. */
  const ciData = () => P().customInstructions || { presets: [], setName: "", activeId: "" };
  const ciCard = (p) => {
    const c = ciData();
    const open = !!UI.ciCardOpen[p.id];
    const active = p.id === c.activeId;
    const del = UI.ciConfirmDel === p.id;
    const count = String(p.body || "").split("\n").filter((l) => l.trim()).length;
    return `<div class="la-ttscard"><div class="la-ttshead">
      <button class="la-row-x" data-act="pf-ci-card" data-id="${e(p.id)}" aria-label="Expand">${open ? "▾" : "▸"}</button>
      <b data-act="pf-ci-card" data-id="${e(p.id)}">${e(p.name || "(unnamed preset)")}</b>
      <span class="la-tag mono">${count} line${count === 1 ? "" : "s"}</span>
      ${active ? `<span class="la-tag">active</span>` : `<button class="la-btn ghost mini" data-act="pf-ci-use" data-id="${e(p.id)}">Use here</button>`}
      <button class="la-row-x" data-act="pf-ci-remove" data-id="${e(p.id)}" aria-label="Delete preset" title="${del ? "Click again to delete" : "Delete preset"}">${del ? "Sure?" : "✕"}</button></div>
      ${open ? `<label class="la-field"><span>Name</span><input class="la-input" data-pf="ci:${e(p.id)}:name" value="${e(val("ci:" + p.id + ":name", p.name))}"></label>
        <label class="la-field"><span>Instructions — one per line</span><textarea class="la-input" rows="6" data-pf="ci:${e(p.id)}:body" placeholder="Keep replies under 150 words.&#10;Always name the Live track you changed.&#10;Suggest a reference track when mixing.">${e(val("ci:" + p.id + ":body", p.body))}</textarea></label>${msg("ci:" + p.id + ":body")}` : ""}</div>`;
  };
  const customInstr = () => {
    const c = ciData();
    const where = c.setName ? `"${c.setName}"` : "the open Live Set";
    const activeName = (c.presets.find((p) => p.id === c.activeId) || {}).name || "none";
    return `<section><h4><button class="la-row-x" data-act="pf-ci-toggle" aria-label="Expand">${UI.ciOpen ? "▾" : "▸"}</button> Genius custom instructions <span class="la-tag mono">${e(activeName)}</span></h4>
      ${UI.ciOpen ? `<p class="la-muted">Standing instructions for how Genius answers — length, tone, what to always mention. Presets are shared across projects; the one in use is remembered per Live Set (currently ${e(where)}) and can also be switched from the dropdown beside the agent picker in the chat.</p>
      ${c.presets.map(ciCard).join("")}${msg("ci")}
      <div class="la-runrow"><button class="la-btn ghost" data-act="pf-ci-add">+ Add preset</button>${c.activeId ? `<button class="la-btn ghost mini" data-act="pf-ci-use" data-id="">Use none for ${e(where)}</button>` : ""}</div>` : ""}</section>`;
  };

  const foot = () => `<section class="la-prefs-foot"><p class="la-muted">Changes save as you make them, to <code>${e(P().settingsFolder ? P().settingsFolder + "\\settings.json" : "settings.json")}</code>.</p>${P().settingsFolder ? `<button class="la-btn ghost mini" data-act="pf-open-folder">Open settings folder</button>` : ""}</section>`;

  LA.Prefs = {
    body: () => `<div class="la-settings">${appearance()}${connection()}${aiProvider()}${agents()}${customInstr()}${folders()}${audio()}${foot()}</div>`,
    head: () => `<b class="la-title" style="font-size:16px">Preferences</b>${UI.saved ? `<span class="la-muted la-saved">Saved</span>` : ""}<button class="la-iconbtn" data-act="close-settings" aria-label="Close">${LA.icon("x")}</button>`,
    ui: UI,
  };

  /* ---- behaviour ------------------------------------------------------------------ */
  let savedTimer = 0;
  const flashSaved = () => { UI.saved = 1; clearTimeout(savedTimer); savedTimer = setTimeout(() => { UI.saved = 0; C.mark("prefs"); }, 1400); };
  async function pcall(op, args, errKey) {
    let r;
    try { r = await C.api().prefs(op, args || {}); } catch (err) { r = { ok: false, error: String(err) }; }
    if (r && r.prefs) C.D.prefs = r.prefs;
    UI.err[errKey || op] = r && r.ok === false ? r.error : "";
    UI.note[errKey || op] = r && r.note ? r.note : "";
    if (r && r.ok !== false && !["test_key", "detect_provider", "list_models", "tts_detect", "tts_voices", "agent_tools"].includes(op)) flashSaved();
    C.mark("prefs");
    // The chat header carries the custom-instruction dropdown, so any ci_* edit
    // has to redraw it too -- otherwise renaming or unbinding a preset in
    // Preferences leaves the chat showing the old one.
    if (op.startsWith("ci_")) C.mark("ghead");
    return r || { ok: false };
  }
  const q = (sel) => C.app().querySelector(sel);

  async function commitField(pf, value) {
    const p = P();
    if (pf === "listen" || pf === "bridge") {
      const listen = val("listen", p.ports.listen), bridge = val("bridge", p.ports.bridge);
      const r = await pcall("set_ports", { listen, bridge }, pf);
      if (r.ok) { delete UI.draft.listen; delete UI.draft.bridge; UI.err.listen = UI.err.bridge = ""; }
      else UI.err[pf === "listen" ? "listen" : "bridge"] = r.error;
    } else if (pf.startsWith("path:")) {
      const r = await pcall("set_path", { key: pf.slice(5), value }, pf);
      if (r.ok && UI.draft[pf] === value) delete UI.draft[pf];
    } else if (pf.startsWith("ci:")) {
      // "ci:<preset id>:name" | "ci:<preset id>:body"
      const [, id, which] = pf.split(":");
      const r = await pcall("ci_update", which === "name" ? { id, name: value } : { id, body: value }, pf);
      if (r.ok && UI.draft[pf] === value) delete UI.draft[pf];
    } else if (pf === "model") { const r = await pcall("set_model", { model: value }, pf); if (r.ok && UI.draft[pf] === value) delete UI.draft[pf]; }
    else if (pf === "apiBase") { const r = await pcall("set_base", { api_base: value }, pf); if (r.ok && UI.draft[pf] === value) delete UI.draft[pf]; }
  }

  /* Commits are serialized and each builds its payload when it actually runs, so two quick edits (name, then key)
     can never interleave. A response only tidies entries that were NOT edited while it was in flight; otherwise it
     would wipe a key the user had just typed. */
  let ttsQueue = Promise.resolve();
  const commitTts = () => (ttsQueue = ttsQueue.then(runCommitTts, runCommitTts));
  async function runCommitTts() {
    const sent = ttsList().map((t) => ({ t, ver: t.ver || 0 }));
    const list = ttsList().map((t) => ({ src: t.src, name: t.name, provider: t.provider, key_mode: t.key_mode, api_key: t.api_key, vault_id: t.vault_id, voice_id: t.voiceId, model: t.model, speed: t.speed, language: t.language }));
    const r = await pcall("save_tts", { profiles: list }, "tts");
    if (!r.ok) return;
    const named = sent.filter((x) => x.t.name.trim());
    r.prefs.tts.forEach((p, i) => {
      const x = named[i];
      if (!x || (x.t.ver || 0) !== x.ver) return;        // edited meanwhile: its own (queued) commit will settle it
      x.t.src = i; x.t.key_mode = "keep"; x.t.api_key = ""; x.t.vault_id = ""; x.t.hint = p.hint;   // typed secrets leave page memory
    });
    C.mark("prefs");
  }
  const ttsBy = (uid) => ttsList().find((t) => t.uid === uid);
  let uidN = 0;

  const acts = {
    "pf-theme-toggle": () => { UI.themesOpen = !UI.themesOpen; C.mark("prefs"); },
    "pf-ci-toggle": () => { UI.ciOpen = !UI.ciOpen; C.mark("prefs"); },
    "pf-ci-card": (el) => { const id = el.dataset.id; UI.ciCardOpen[id] = !UI.ciCardOpen[id]; C.mark("prefs"); },
    "pf-ci-add": async () => {
      const r = await pcall("ci_create", { name: "New preset", body: "" }, "ci");
      // Open the new card straight away -- an empty collapsed card looks like
      // nothing happened.
      if (r.ok && r.createdId) UI.ciCardOpen[r.createdId] = true;
      C.mark("prefs");
    },
    "pf-ci-remove": (el) => {
      // Two clicks: a preset (and its wording) cannot be recovered, same
      // pattern as deleting a saved API key.
      if (UI.ciConfirmDel !== el.dataset.id) { UI.ciConfirmDel = el.dataset.id; C.mark("prefs"); return; }
      UI.ciConfirmDel = "";
      return pcall("ci_delete", { id: el.dataset.id }, "ci");
    },
    // Binds to whichever Live Set is open; an empty id unbinds it.
    "pf-ci-use": (el) => pcall("ci_bind", { id: el.dataset.id || "" }, "ci"),
    "pf-theme": async (el) => { const r = await pcall("set_theme", { slug: el.dataset.slug }, "theme"); if (r.ok) LA.setTheme(r.prefs.theme); },
    "pf-use-key": (el) => { if (el.dataset.id !== P().activeKeyId) return pcall("use_key", { id: el.dataset.id }, "keys"); },
    "pf-del-key": (el) => {
      if (UI.confirmDel !== el.dataset.id) { UI.confirmDel = el.dataset.id; C.mark("prefs"); return; }   // two clicks: a saved key cannot be recovered
      UI.confirmDel = ""; return pcall("delete_key", { id: el.dataset.id }, "keys");
    },
    "pf-add-toggle": () => { UI.addKey = !UI.addKey; if (!UI.addKey) { UI.nk = { key: "", label: "", provider: "", base: "", model: "" }; UI.note.detect = ""; UI.err.nk = ""; } C.mark("prefs"); },
    "pf-model-toggle": () => { UI.modelPanel = !UI.modelPanel; C.mark("prefs"); },
    "pf-show-key": () => { UI.showKey = !UI.showKey; C.mark("prefs"); },
    "pf-detect": async () => {
      if (!UI.nk.key.trim()) { UI.err.nk = "Paste an API key first."; C.mark("prefs"); return; }
      UI.busy.detect = true; UI.err.nk = ""; C.mark("prefs");
      const r = await pcall("detect_provider", { api_key: UI.nk.key }, "nk");
      UI.busy.detect = false;
      if (r.ok) {
        UI.note.detect = r.message;
        if (r.provider) {
          UI.nk.provider = r.provider; UI.nk.base = r.apiBase;
          const m = await pcall("list_models", { api_key: UI.nk.key, provider: r.provider, api_base: r.apiBase }, "nk");
          if (m.ok) { UI.models = m.models; UI.busyModels = m.busy || []; UI.modelPricing = m.pricing || {}; if (!UI.nk.model && m.models.length) UI.nk.model = m.models[0]; }
        }
      }
      C.mark("prefs");
    },
    "pf-save-key": async () => {
      const n = UI.nk;
      const r = await pcall("add_key", { api_key: n.key, label: n.label, provider: n.provider, api_base: n.base, model: n.model }, "nk");
      if (r.ok) { UI.addKey = false; UI.nk = { key: "", label: "", provider: "", base: "", model: "" }; UI.note.detect = ""; UI.test = null; C.mark("prefs"); }
    },
    "pf-test": async () => {
      UI.test = { pending: true }; C.mark("prefs");
      const r = await pcall("test_key", {}, "test");
      UI.test = r.ok ? r.test : { ok: false, message: r.error };
      C.mark("prefs");
    },
    "pf-refresh-models": async () => {
      UI.busy.models = true; C.mark("prefs");
      const r = await pcall("list_models", {}, "models");
      UI.busy.models = false;
      if (r.ok) { UI.models = r.models; UI.busyModels = r.busy || []; UI.modelPricing = r.pricing || {}; UI.note.models = r.models.length ? `${r.models.length} working models — pick one in the Model box; the endpoint follows.` : "No working models for this key — check the key, or that its project has the Generative Language API enabled."; }
      C.mark("prefs"); C.mark("ghead");
    },
    "pf-pick-agent": async (el) => { const r = await C.api().genius_set_agent(el.dataset.slug); if (r && r.ok === false) { UI.err.agents = r.error; C.mark("prefs"); } },
    "pf-agent-open": async (el) => {
      const slug = el.dataset.slug;
      UI.agentOpen[slug] = !UI.agentOpen[slug]; C.mark("prefs");
      if (UI.agentOpen[slug] && !UI.agentGroups[slug]) { const r = await pcall("agent_tools", { slug }, "agents"); if (r.ok) { UI.agentGroups[slug] = r.groups; C.mark("prefs"); } }
    },
    "pf-agent-tool": async (el) => {
      const r = await pcall("set_agent_tool", { slug: el.dataset.slug, name: el.dataset.name, on: el.checked }, "agents");
      if (r.ok) UI.agentGroups[el.dataset.slug] = r.groups; C.mark("prefs");
    },
    "pf-agent-group": async (el) => {
      const r = await pcall("set_agent_group", { slug: el.dataset.slug, group: el.dataset.group, on: el.dataset.on === "1" }, "agents");
      if (r.ok) UI.agentGroups[el.dataset.slug] = r.groups; C.mark("prefs");
    },
    "pf-agent-enable": async () => {
      const av = P().agents.available; const slug = UI.agentPick || (av[0] && av[0].slug);
      if (!slug) return;
      const r = await pcall("enable_agent", { slug }, "agents");
      if (r.ok) { UI.agentPick = ""; UI.agentOpen[slug] = true; const t = await pcall("agent_tools", { slug }, "agents"); if (t.ok) UI.agentGroups[slug] = t.groups; C.mark("prefs"); }
    },
    "pf-agent-remove": async (el) => { const slug = el.dataset.slug; const r = await pcall("remove_agent", { slug }, "agents"); if (r.ok) { delete UI.agentOpen[slug]; delete UI.agentGroups[slug]; C.mark("prefs"); } },
    "pf-browse": async (el) => {
      const key = el.dataset.key, cur = val("path:" + key, P().paths[key]);
      const isFile = key === "ffmpeg_path";
      const picked = isFile ? await C.api().pick_file(cur, key === "ffmpeg_path" ? [["ffmpeg", "*.exe"]] : [["Shortcut or script", "*.lnk,*.ps1"]]) : await C.api().pick_folder(cur);
      if (picked) { UI.draft["path:" + key] = picked; await commitField("path:" + key, picked); }
    },
    "pf-open-folder": () => pcall("open_settings_folder", {}, "folder"),
    "pf-tts-add": () => { const uid = "n" + ++uidN; UI.ttsOpen[uid] = true; ttsList().push({ uid, src: -1, name: "", provider: "xai", key_mode: "typed", api_key: "", vault_id: "", hint: "", voiceId: "", model: "", speed: "", language: "" }); C.mark("prefs"); },
    "pf-tts-toggle": (el) => { const t = ttsBy(el.dataset.uid); UI.ttsOpen[t.uid] = !(UI.ttsOpen[t.uid] !== undefined ? UI.ttsOpen[t.uid] : !t.name); C.mark("prefs"); },
    "pf-tts-remove": (el) => { UI.tts = ttsList().filter((t) => t.uid !== el.dataset.uid); C.mark("prefs"); return commitTts(); },
    "pf-tts-pin": (el) => {
      const willPin = el.getAttribute("data-on") !== "true";
      if (willPin && !el.dataset.name) return;             // unnamed/unsaved profile -- nothing to pin yet
      return pcall("tts_pin", { name: el.dataset.name }, "tts");
    },
    "pf-tts-detect": async (el) => {
      const t = ttsBy(el.dataset.uid); UI.busy["d" + t.uid] = true; C.mark("prefs");
      const r = await pcall("tts_detect", { src: t.src, api_key: t.key_mode === "typed" ? t.api_key : "" }, "tts:" + t.uid);
      UI.busy["d" + t.uid] = false;
      if (r.ok && r.provider) { t.provider = r.provider; UI.note["tts:" + t.uid] = r.message; C.mark("prefs"); await commitTts(); return acts["pf-tts-voices"](el); }
      if (r.ok) UI.note["tts:" + t.uid] = r.message;
      C.mark("prefs");
    },
    "pf-tts-voices": async (el) => {
      const t = ttsBy(el.dataset.uid); UI.busy["v" + t.uid] = true; C.mark("prefs");
      const r = await pcall("tts_voices", { provider: t.provider, src: t.src, api_key: t.key_mode === "typed" ? t.api_key : "" }, "tts:" + t.uid);
      UI.busy["v" + t.uid] = false;
      if (r.ok) { UI.voices[t.uid] = r.voices; UI.note["tts:" + t.uid] = `${r.voices.length} voice(s) found — pick one in the Voice ID box.`; }
      C.mark("prefs");
    },
  };

  /* Typing keeps a draft (so a re-render never eats it); the value is committed on `change` (blur / Enter). */
  function onInput(ev) {
    const t = ev.target, pf = t.dataset && t.dataset.pf, pfc = t.dataset && t.dataset.pfc;
    if (pf) {
      if (pf.startsWith("nk.")) UI.nk[pf.slice(3)] = t.value; else if (pf === "agentPick") UI.agentPick = t.value; else UI.draft[pf] = t.value;
    } else if (pfc) {
      const row = ttsBy(t.dataset.uid); if (!row) return;
      row.ver = (row.ver || 0) + 1;
      if (pfc === "api_key") { row.key_mode = "typed"; row.api_key = t.value; row.vault_id = ""; }
      else if (pfc !== "vault" && pfc !== "provider") row[pfc] = t.value;
    }
  }
  async function onChange(ev) {
    const t = ev.target, pf = t.dataset && t.dataset.pf, pfc = t.dataset && t.dataset.pfc;
    if (t.dataset && t.dataset.ptool) return acts["pf-agent-tool"](t);
    if (pf) {
      if (pf.startsWith("nk.")) { UI.nk[pf.slice(3)] = t.value; return; }
      if (pf === "agentPick") { UI.agentPick = t.value; return; }
      return commitField(pf, t.value);
    }
    if (pfc) {
      const row = ttsBy(t.dataset.uid); if (!row) return;
      row.ver = (row.ver || 0) + 1;
      if (pfc === "vault") {
        if (!t.value) return;
        row.key_mode = "vault"; row.vault_id = t.value; row.api_key = "";
        const k = P().keys.find((x) => x.id === t.value);
        if (k && TTS_PROVIDERS.includes(k.provider)) row.provider = k.provider;
      } else if (pfc === "provider") row.provider = t.value;
      else row[pfc] = t.value;
      await commitTts();
    }
  }

  LA.Prefs.init = (ctx) => { C = ctx; };
  LA.Prefs.acts = acts;
  LA.Prefs.onInput = onInput;
  LA.Prefs.onChange = onChange;
  LA.Prefs.render = () => {
    const modal = q(".la-modal");
    if (!modal) return;
    const body = modal.querySelector(".la-modal-body"), head = modal.querySelector(".la-modal-head");
    const top = body.scrollTop;
    const ae = document.activeElement;
    const key = ae && ae.matches && ae.matches("[data-pf],[data-pfc]") ? (ae.dataset.pf ? `[data-pf="${ae.dataset.pf}"]` : `[data-pfc="${ae.dataset.pfc}"][data-uid="${ae.dataset.uid}"]`) : null;
    const sel = key && ae.selectionStart != null ? [ae.selectionStart, ae.selectionEnd] : null;
    head.innerHTML = LA.Prefs.head();
    body.innerHTML = LA.Prefs.body();
    body.scrollTop = top;
    if (key) { const n = body.querySelector(key); if (n) { n.focus(); if (sel && n.setSelectionRange) try { n.setSelectionRange(sel[0], sel[1]); } catch (_) {} } }
  };
})();
