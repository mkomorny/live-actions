/* Shell controller: Layout A · Workbench, driven by the Python session model.
   Python is authoritative -- this file keeps a mirror (LA.data) built from get_state()
   and patched by pushed events, and turns clicks into ShellApi calls. It never
   invents state (e.g. the ticked-track set the next Run uses is Python's).

   Rendering is by REGION (top / left / main / right / console / status) rather than
   a full innerHTML rebuild, so a bridge push -- a log line, a status tick -- can never
   wipe half-typed field values, focus or scroll position in another region. */
(function () {
  const LA = window.LA;
  const D = LA.data;
  const S = { page: "genius", tool: null, filter: "all", console: false, settings: false, pop: null, draft: "", drawer: null };
  const P = { id: null, sel: null, warn: "", confirmed: false };
  const C = { id: null, remember: false };                         // the open "may I spend your credit?" question (D.confirm is Python's)   // the open "choose a clip slot" question (D.placement is Python's; this is the page-side choice)
  const app = () => document.getElementById("app");
  const api = () => window.pywebview.api;

  /* ---- region markup (concatenated == the preview's full layout-a render) ---- */
  const R = {
    top: () => `<header class="A-top">
      <div class="la-brand"><i>${LA.icon("bolt", 13)}</i><span class="la-brand-word">Live Actions</span></div>
      ${S.page === "actions" ? `<button class="la-iconbtn A-drawer-toggle" data-act="drawer" data-k="left" title="Target tracks" aria-label="Target tracks">${LA.icon("panel-l", 18)}</button>` : ""}
      <nav><button class="la-tab${S.page === "genius" ? " on" : ""}" data-act="page" data-k="genius">${LA.icon("brain", 14)} Genius</button>
           <button class="la-tab${S.page === "actions" ? " on" : ""}" data-act="page" data-k="actions">${LA.icon("bolt", 14)} Tools</button></nav>
      <span class="grow"></span>
      ${S.page === "actions" && S.tool ? `<button class="la-iconbtn A-drawer-toggle" data-act="drawer" data-k="right" title="Action detail" aria-label="Action detail">${LA.icon("panel-r", 18)}</button>` : ""}
      <button class="la-btn ghost" data-act="diag" data-keep>${LA.pip()}</button>
      <button class="la-iconbtn" data-act="settings" title="Preferences" aria-label="Preferences">${LA.icon("gear", 18)}</button>
      ${S.pop === "diag" ? `<div class="la-pop" style="right:58px;top:52px;width:300px">${LA.diagPanel()}</div>` : ""}
    </header>`,
    left: () => `<aside class="A-left">
      <div class="la-panel set"><span class="la-section-title">Live Set</span><b>${LA.esc((D.set || {}).name || "")}</b><div class="la-chips">${LA.chips()}</div></div>
      <div class="la-panel A-tracks">
        <div class="head"><span class="la-section-title">Target tracks</span></div>
        ${LA.quickPicks()}<div class="sum">${LA.esc(LA.targetSummary())}</div>
        <div class="la-scroll" style="flex:1">${LA.trackList()}</div>
      </div></aside>`,
    main: () => {
      const tools = LA.filterTools(S);
      return `<main class="A-main"><div class="A-headrow"><div><h1 class="la-title">Studio Actions</h1><span class="la-muted">${tools.length} of ${D.tools.length} actions</span></div>
        <div class="A-filters">${LA.filterChips(S)}</div></div>
      <div class="la-scroll" style="flex:1"><div class="A-grid">${tools.map((t) => LA.toolCard(t, { active: t.id === S.tool })).join("")}</div></div></main>`;
    },
    right: () => `<aside class="A-right la-scroll">${S.tool && LA.byId(S.tool) ? LA.toolBody(LA.byId(S.tool)) : `<div class="A-empty">Select an action to configure and run it here.<br>The catalog stays where it is.</div>`}</aside>`,
    ghead: () => `<div class="A-headrow"><div><h1 class="la-title">Genius</h1><span class="la-muted">Genius finds the tracks it needs by number or name — nothing to tick here.</span></div><div class="A-agent">${LA.agentChips()}</div></div>`,
    gnote: () => `<div class="A-gnote">${LA.geniusNote()}</div>`,
    gbtn: () => LA.sendButton(),
    genius: () => `<main class="A-main A-genius"><div class="A-genius-wrap">${R.ghead()}${R.gnote()}<div class="la-scroll" style="flex:1">${LA.chat()}</div>${LA.composer(S.draft)}</div></main>`,
    console: () => LA.consoleDrawer(S),
    status: () => LA.statusbar(S, S.page !== "genius"),
    modal: () => LA.settingsModal(S),
  };

  const body = () => `<div class="A-body${S.page === "genius" ? " solo" : ""}" data-drawer="${S.drawer || ""}">${S.page === "genius" ? R.genius() : R.left() + R.main() + R.right()}${S.page === "actions" ? '<div class="la-scrim" data-act="drawer-close"></div>' : ""}</div>`;
  const full = () => R.top() + body() + R.console() + R.status() + R.modal();

  /* ---- swapping ------------------------------------------------------------- */
  const scrollers = (root) => [root, ...root.querySelectorAll(".la-scroll")].filter((n) => n.classList && n.classList.contains("la-scroll"));
  function swap(selector, html) {
    const el = app().querySelector(selector);
    if (!el) return;
    const saved = scrollers(el).map((n) => n.scrollTop);
    const tpl = document.createElement("template");
    tpl.innerHTML = html.trim();
    const next = tpl.content.firstElementChild;
    if (!next) { el.remove(); return; }
    el.replaceWith(next);
    scrollers(next).forEach((n, i) => (n.scrollTop = saved[i] || 0));
    return next;
  }
  const SEL = { top: ".A-top", left: ".A-left", main: ".A-main", right: ".A-right", status: ".la-statusbar", ghead: ".A-genius .A-headrow", gnote: ".A-gnote", gbtn: "[data-genius-btn]" };

  function drawAll() {
    const a = app();
    const ae = document.activeElement;
    const active = ae && ae.dataset ? ae.dataset.fid : null;
    const composing = !!(ae && ae.hasAttribute && ae.hasAttribute("data-genius-input"));
    a.innerHTML = full();
    LA.applyShowIf();
    if (active) { const n = a.querySelector(`[data-fid="${active}"]`); if (n) n.focus(); }
    scrollConsole();
    const sc = a.querySelector(".A-genius .la-scroll");
    if (sc) sc.scrollTop = sc.scrollHeight;
    const ta = a.querySelector("[data-genius-input]");
    if (ta) { fit(ta); if (composing) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); } }
  }
  function scrollConsole() { const c = app().querySelector(".la-console"); if (c) c.scrollTop = c.scrollHeight; }

  /* ---- "Add to Live Set": Python's pending question, drawn in its own root so a full redraw of #app never wipes a choice ---- */
  function drawPlace() {
    const host = document.getElementById("place");
    const req = D.placement || null;
    if (!req) { P.id = null; P.sel = null; P.warn = ""; P.confirmed = false; host.innerHTML = ""; return; }
    const fresh = P.id !== req.id;
    if (fresh) {
      const firstEmpty = req.slots.find((s) => !s.has);
      Object.assign(P, { id: req.id, sel: firstEmpty ? firstEmpty.index : null, warn: "", confirmed: false });
    }
    const old = host.querySelector(".la-slots");
    const top = old ? old.scrollTop : 0;
    const ae = document.activeElement;
    const rowFocus = ae && ae.dataset && ae.matches && ae.matches("[data-act=\"place-pick\"]") ? ae.dataset.i : null;
    host.innerHTML = LA.placeModal(req, P);
    const list = host.querySelector(".la-slots");
    if (list) list.scrollTop = top;
    if (fresh) {
      const on = host.querySelector(".la-keyrow.on");
      if (on) on.scrollIntoView({ block: "nearest" });
      const ok = host.querySelector('[data-act="place-ok"]');
      if (ok) ok.focus();
    } else if (rowFocus !== null) {
      const row = host.querySelector(`[data-act="place-pick"][data-i="${rowFocus}"]`);
      if (row) row.focus();
    }
  }

  /* ---- spend approval: same own-root trick as drawPlace, so a redraw never loses the checkbox ---- */
  function drawConfirm() {
    const host = document.getElementById("confirm");
    const req = D.confirm || null;
    if (!req) { C.id = null; C.remember = false; host.innerHTML = ""; return; }
    if (C.id !== req.id) Object.assign(C, { id: req.id, remember: false });
    host.innerHTML = LA.confirmModal(req, C);
    const ok = host.querySelector('[data-act="confirm-ok"]');
    if (ok) ok.focus();
  }

  const dirty = new Set();
  let raf = 0;
  function mark(...names) {
    names.forEach((n) => dirty.add(n));
    if (!raf) raf = requestAnimationFrame(flush);
  }
  function flush() {
    raf = 0;
    const names = [...dirty]; dirty.clear();
    if (names.includes("all")) return drawAll();
    for (const n of names) {
      if (n === "console") {
        const c = app().querySelector(".la-console");
        if (c) { const atEnd = c.scrollTop + c.clientHeight >= c.scrollHeight - 4; c.innerHTML = LA.consoleLines(); if (atEnd) c.scrollTop = c.scrollHeight; }
      } else if (n === "result") {
        const t = S.tool && LA.byId(S.tool);
        const box = t && app().querySelector(`[data-result="${t.id}"]`);
        if (box) { const tmp = document.createElement("template"); tmp.innerHTML = LA.resultBox(t).trim(); box.replaceWith(tmp.content.firstElementChild); }
        const btn = app().querySelector('.A-right [data-act="run"]');
        if (btn && t) btn.disabled = ((D.runs[t.id] || {}).state === "running");
      } else if (n === "scope-note") {
        const t = S.tool && LA.byId(S.tool);
        const note = app().querySelector("[data-scope-note]");
        if (t && note) note.textContent = LA.scopeNote(t);
      } else if (n === "diag") {
        if (S.pop === "diag") mark("top");
      } else if (n === "gchat") {
        flushChat();
      } else if (n === "place") {
        drawPlace();
      } else if (n === "confirm") {
        drawConfirm();
      } else if (n === "prefs") {
        if (S.settings) LA.Prefs.render();
      } else if (SEL[n]) {
        swap(SEL[n], R[n]());
        if (n === "right") LA.applyShowIf();
      }
    }
  }

  /* ---- events pushed from Python (UiBus) ------------------------------------ */
  const REGIONS = {
    connected: ["top", "status"], hostTrack: ["diag"], set: ["left"], tracks: ["left", "status", "scope-note"],
    targets: ["left", "status", "scope-note"], ticker: ["status"], runs: ["result"], tools: ["main", "right"], theme: [], placement: ["place"], confirm: ["confirm"],
  };
  function applyEvent(evt) {
    if (evt.type === "log") {
      D.log.push(evt.line);
      if (D.log.length > 1000) D.log.splice(0, D.log.length - 1000);
      if (S.console) mark("console");
    } else if (evt.type === "genius") {
      applyGenius(evt);
    } else if (evt.type === "patch") {
      for (const k of Object.keys(evt.patch)) {
        if (k === "runs") Object.assign(D.runs, evt.patch.runs);
        else D[k] = evt.patch[k];
        mark(...(REGIONS[k] || []));
      }
    }
  }
  /* ---- Genius mirror: the same reducer as test_shell_genius.Page ------------------ */
  const gdirty = new Set();
  let gfull = false, forceBottom = false;
  function applyGenius(e) {
    const G = D.genius;
    const msg = (id) => G.messages.find((m) => m.id === id);
    const dirty = (id) => { gdirty.add(id); if (S.page === "genius") mark("gchat"); };
    const m = e.id !== undefined ? msg(e.id) : null;
    switch (e.op) {
      case "add": G.messages.push(e.msg); if (e.msg.role === "user") forceBottom = true; dirty(e.msg.id);
        if (G.messages.length === 2 && S.page === "genius") mark("ghead"); break;
      case "part": if (m) { m.parts.push(e.part); dirty(m.id); } break;
      case "text": if (m && m.parts[e.i]) { const p = m.parts[e.i]; p.text = p.text.slice(0, e.offset) + e.text; dirty(m.id); } break;
      case "settext": if (m && m.parts[e.i]) { m.parts[e.i].text = e.text; dirty(m.id); } break;
      case "call": if (m && m.parts[e.i]) { m.parts[e.i].state = e.state; m.parts[e.i].note = e.note; dirty(m.id); } break;
      case "done": if (m) { m.state = e.state; if (e.error) m.error = e.error; dirty(m.id); }
        G.busy = false; if (S.page === "genius") mark("gbtn"); break;
      case "busy": G.busy = !!e.busy; if (S.page === "genius") mark("gbtn"); break;
      case "clear": G.messages = e.messages; G.busy = false; gfull = true;
        if (S.page === "genius") mark("gchat", "gbtn", "ghead"); break;
      case "agent": G.agent = e.agent; G.agents = e.agents; G.model = e.model; if (e.status) G.status = e.status;
        if (S.page === "genius") mark("ghead", "gnote"); if (S.settings) mark("prefs"); break;
    }
  }
  function flushChat() {
    const scroller = app().querySelector(".A-genius .la-scroll");
    const chat = scroller && scroller.querySelector(".la-chat");
    if (!chat) { gdirty.clear(); gfull = false; return; }
    const atEnd = forceBottom || scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 24;
    forceBottom = false;
    const node = (m) => { const t = document.createElement("template"); t.innerHTML = LA.bubble(m).trim(); return t.content.firstElementChild; };
    if (gfull) chat.innerHTML = D.genius.messages.map(LA.bubble).join("");
    else for (const id of gdirty) {
      const m = D.genius.messages.find((x) => x.id === id);
      if (!m) continue;
      const old = chat.querySelector(`[data-msg="${id}"]`);
      if (old) old.replaceWith(node(m)); else chat.appendChild(node(m));
    }
    gdirty.clear(); gfull = false;
    if (atEnd) scroller.scrollTop = scroller.scrollHeight;
  }
  /* The composer grows with what is typed (up to ~6 lines), then scrolls. */
  function fit(ta) {
    ta.style.height = "";
    const multi = ta.scrollHeight > ta.clientHeight;
    if (!multi) { ta.style.overflowY = "hidden"; return; }
    const border = ta.offsetHeight - ta.clientHeight;
    const cs = getComputedStyle(ta);
    const line = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.3;
    const pad = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const max = line * 6 + pad;
    ta.style.height = Math.min(ta.scrollHeight, max) + border + "px";
    ta.style.overflowY = ta.scrollHeight > max ? "auto" : "hidden";
  }

  let booted = false;
  const backlog = [];
  window.__uiBusRecv = function (evt) { if (booted) applyEvent(evt); else backlog.push(evt); };

  /* ---- showIf (hide, never destroy: values survive) --------------------------- */
  LA.applyShowIf = function () {
    app().querySelectorAll("[data-showif]").forEach((row) => {
      let cond; try { cond = JSON.parse(row.dataset.showif); } catch (_) { return; }
      const ctl = app().querySelector(`.A-right [data-fid="${cond.field}"]`);
      const v = ctl ? String(ctl.value).trim() : "";
      let ok = true;
      if (Array.isArray(cond.in) && cond.in.map(String).indexOf(v) < 0) ok = false;
      if (Array.isArray(cond.notIn) && cond.notIn.map(String).indexOf(v) >= 0) ok = false;
      row.style.display = ok ? "" : "none";
    });
  };

  /* ---- theme hook ------------------------------------------------------------- */
  LA.setTheme = (slug) => {
    const link = document.getElementById("la-theme");
    const href = `css/themes/${slug}.css`;
    if (link && link.getAttribute("href") !== href) link.setAttribute("href", href);
  };

  /* ---- actions ---------------------------------------------------------------- */
  const collect = () => {
    const out = {};
    app().querySelectorAll(".A-right [data-fid]").forEach((n) => { if (n.dataset.act !== "pick-file") out[n.dataset.fid] = n.value; });
    return out;
  };
  const setTargets = (keys) => { if (Array.isArray(keys)) { D.targets = keys; mark("left", "status", "scope-note"); } };
  const setDrawer = (k) => {
    S.drawer = k;
    const b = app().querySelector(".A-body");
    if (b) b.dataset.drawer = k || "";
  };
  const openTool = (id) => {
    S.tool = id;
    mark("main", "right");
    if (matchMedia("(max-width: 859px)").matches) { setDrawer("right"); mark("top"); }
  };

  async function copyLog(btn) {
    let text = ""; try { text = await api().log_text(); } catch (_) { text = D.log.map((l) => `${l[0]}  ${l[1]} ${l[2]}`).join("\n"); }
    const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand("copy"); } catch (_) {}
    ta.remove();
    if (btn) { const old = btn.textContent; btn.textContent = ok ? "Copied" : "Copy failed"; setTimeout(() => { if (btn.isConnected) btn.textContent = old; }, 1200); }
  }

  const ACTS = {
    page: (el) => { S.page = el.dataset.k; S.pop = null; S.drawer = null; mark("all"); },
    drawer: (el) => setDrawer(S.drawer === el.dataset.k ? null : el.dataset.k),
    "drawer-close": () => setDrawer(null),
    diag: () => { S.pop = S.pop === "diag" ? null : "diag"; mark("top"); },
    "diag-ping": () => api().ping(),
    "diag-status": () => api().request_status(),
    "diag-sync": () => api().request_tracks(),
    "diag-reset": () => api().reset_bridge(),
    filter: (el) => { S.filter = el.dataset.k; mark("main"); },
    "open-tool": (el) => openTool(el.dataset.id),
    "toggle-track": async (el) => setTargets(await api().toggle_track(el.dataset.key)),
    all: async () => setTargets(await api().select_all()),
    none: async () => setTargets(await api().select_none()),
    livesel: async () => setTargets(await api().use_live_selection()),
    console: () => { S.console = !S.console; mark("all"); },
    "copy-log": (el) => copyLog(el),
    settings: () => { S.settings = true; S.pop = null; mark("all"); },
    "close-settings": () => { S.settings = false; mark("all"); },
    "place-pick": (el) => {
      const i = Number(el.dataset.i);
      if (P.sel !== i) Object.assign(P, { sel: i, warn: "", confirmed: false });
      drawPlace();
    },
    "place-ok": async () => {
      const req = D.placement;
      if (!req) return;
      if (P.sel === null) { P.warn = "Pick a slot first."; drawPlace(); return; }
      const r = await api().place_answer(req.id, P.sel, P.confirmed);
      if (r && r.needsConfirm) { P.confirmed = true; P.warn = r.message || "That slot has a clip — click Place again to replace it."; drawPlace(); }
      else if (r && !r.ok && !r.stale) { P.warn = r.error || "Could not place that."; drawPlace(); }
    },
    "place-cancel": () => { const req = D.placement; return req && api().place_answer(req.id, null, false); },
    "confirm-remember": () => { C.remember = !C.remember; drawConfirm(); },
    "confirm-ok": () => { const req = D.confirm; return req && api().confirm_answer(req.id, true, C.remember); },
    // Cancel, Escape and the scrim all mean "no". Declining must never be the same click as approving.
    "confirm-cancel": () => { const req = D.confirm; return req && api().confirm_answer(req.id, false, false); },
    "genius-send": async () => {
      const ta = app().querySelector("[data-genius-input]");
      const text = (ta ? ta.value : S.draft).trim();
      if (!text || D.genius.busy) return;
      forceBottom = true;
      const r = await api().genius_send(text);
      if (r && r.ok) { S.draft = ""; if (ta) { ta.value = ""; fit(ta); } }
    },
    "genius-stop": () => api().genius_stop(),
    "genius-clear": () => api().genius_clear(),
    "genius-pill": (el) => { const p = D.genius.pills[Number(el.dataset.i)]; forceBottom = true; return p && api().genius_send(p.prompt); },
    run: () => {
      const t = S.tool && LA.byId(S.tool);
      if (!t) return;
      const vals = collect();
      LA.vals[t.id] = Object.assign(LA.vals[t.id] || {}, vals);
      return api().run_tool(t.id, vals);
    },
    "pick-file": async (el) => {
      const t = S.tool && LA.byId(S.tool);
      const fid = el.dataset.fid;
      const input = app().querySelector(`.A-right input[data-fid="${fid}"]`);
      const def = t && t.fields.find((f) => f.id === fid);
      const picked = await api().pick_file(input ? input.value : "", (def && def.filetypes) || null);
      if (picked && input) { input.value = picked; (LA.vals[t.id] = LA.vals[t.id] || {})[fid] = picked; LA.applyShowIf(); }
    },
  };

  Object.assign(ACTS, LA.Prefs.acts);

  function onClick(ev) {
    if (!ev.target.closest(".la-pop") && !ev.target.closest('[data-act="diag"]') && S.pop) { S.pop = null; mark("top"); }
    const el = ev.target.closest("[data-act]");
    if (!el || el.disabled) return;
    const f = ACTS[el.dataset.act];
    if (f) { try { const r = f(el); if (r && r.catch) r.catch((err) => console.error(err)); } catch (err) { console.error(err); } }
  }

  /* Fill the header picker's model lists once per launch. Each key is listed and
     its models live-tested in Python (a few seconds per key), so all keys run at
     once and each group fills in as its own test finishes. A redraw while the
     picker is open would close it, so a result that lands then waits for blur. */
  function redrawPicker() {
    const open = document.activeElement && document.activeElement.matches && document.activeElement.matches(".la-model-select");
    if (open) document.activeElement.addEventListener("blur", () => mark("ghead"), { once: true });
    else mark("ghead");
  }
  async function loadKeyModels() {
    if (D.demo || !D.prefs || !(D.prefs.keys || []).length) return;
    await Promise.all(D.prefs.keys.map(async (k) => {
      try {
        const res = await api().prefs("key_models", { id: k.id });
        if (res && res.prefs) D.prefs = res.prefs;
      } catch (err) { console.error(err); }
      redrawPicker();
      if (S.settings) mark("prefs");
    }));
  }

  /* ---- boot -------------------------------------------------------------------- */
  async function boot() {
    const snap = await api().get_state();
    Object.assign(D, snap);
    LA.Prefs.init({ D, S, api, mark, app });
    LA.setTheme(D.theme);
    if (D.demo && D.tools.some((t) => t.id === "detect-key")) S.tool = "detect-key";   // the reference shot has Detect Key open
    drawAll();
    drawPlace();
    drawConfirm();
    booted = true;
    backlog.splice(0).forEach(applyEvent);
    loadKeyModels();
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", (ev) => {
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches && ev.target.matches(".la-card")) { ev.preventDefault(); ev.target.click(); }
      else if (ev.key === "Enter" && ev.target.matches && ev.target.matches('.A-right input.la-input[data-fid]')) { ev.preventDefault(); ACTS.run(); }
      else if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches && ev.target.matches(".la-keyrow[data-act]")) { ev.preventDefault(); ev.target.click(); }
      else if (ev.key === "Enter" && !ev.shiftKey && !ev.isComposing && ev.target.matches && ev.target.matches("[data-genius-input]")) { ev.preventDefault(); ACTS["genius-send"](); }
      if (D.placement && ev.target.closest && ev.target.closest(".la-place") && (ev.key === "ArrowDown" || ev.key === "ArrowUp")) {
        ev.preventDefault();
        const slots = D.placement.slots;
        const at = Math.max(0, slots.findIndex((s) => s.index === P.sel));
        const next = slots[Math.min(slots.length - 1, Math.max(0, at + (ev.key === "ArrowDown" ? 1 : -1)))];
        if (next) { Object.assign(P, { sel: next.index, warn: "", confirmed: false }); drawPlace(); const row = document.querySelector(`#place [data-act="place-pick"][data-i="${next.index}"]`); if (row) { row.focus(); row.scrollIntoView({ block: "nearest" }); } }
        return;
      }
      if (ev.key === "Escape" && D.confirm) { ev.preventDefault(); ACTS["confirm-cancel"](); return; }
      if (ev.key === "Escape" && D.placement) { ev.preventDefault(); ACTS["place-cancel"](); return; }
      if (ev.key === "Escape" && S.drawer) { ev.preventDefault(); setDrawer(null); return; }
      if (ev.key === "Escape" && (S.settings || S.pop)) { S.settings = false; S.pop = null; mark("all"); }
    });
    window.addEventListener("resize", () => { if (S.drawer && !matchMedia("(max-width: 859px)").matches) setDrawer(null); });
    document.addEventListener("input", (ev) => { if (ev.target.dataset && (ev.target.dataset.pf || ev.target.dataset.pfc)) LA.Prefs.onInput(ev); });
    document.addEventListener("change", (ev) => { if (ev.target.dataset && (ev.target.dataset.pf || ev.target.dataset.pfc || ev.target.dataset.ptool)) LA.Prefs.onChange(ev); });
    document.addEventListener("input", (ev) => { if (ev.target.matches && ev.target.matches("[data-genius-input]")) { S.draft = ev.target.value; fit(ev.target); } });
    document.addEventListener("change", (ev) => {
      if (ev.target.dataset && ev.target.dataset.change === "genius-agent") Promise.resolve(api().genius_set_agent(ev.target.value)).catch((err) => console.error(err));
      // Key + model picker: one save switches both (use_key_model), and the
      // Genius session posts the "Now using ..." line itself.
      if (ev.target.dataset && ev.target.dataset.change === "genius-model") {
        const v = String(ev.target.value || ""), at = v.indexOf("|");
        if (at < 0 || D.genius.busy) { mark("ghead"); return; }
        Promise.resolve(api().prefs("use_key_model", { id: v.slice(0, at), model: v.slice(at + 1) }))
          .then((res) => {
            if (res && res.prefs) D.prefs = res.prefs;
            mark("ghead");
            if (S.settings) mark("prefs");
          })
          .catch((err) => console.error(err));
      }
      // Custom-instruction preset. ci_bind saves the choice against the Live
      // Set that is currently open and returns a fresh prefs snapshot, so the
      // header (and Preferences, if it is open) redraw from the same source.
      if (ev.target.dataset && ev.target.dataset.change === "genius-ci") {
        Promise.resolve(api().prefs("ci_bind", { id: ev.target.value }))
          .then((res) => {
            if (res && res.prefs) {
              D.prefs = res.prefs;
              mark("ghead");
              if (S.settings) mark("prefs");
            }
          })
          .catch((err) => console.error(err));
      }
    });
    const onField = (ev) => {
      const fid = ev.target.dataset && ev.target.dataset.fid;
      if (!fid || !S.tool) return;
      (LA.vals[S.tool] = LA.vals[S.tool] || {})[fid] = ev.target.value;
      LA.applyShowIf();
    };
    document.addEventListener("input", onField);
    document.addEventListener("change", onField);
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => document.body.setAttribute("data-ready", "1"));
  }

  if (window.pywebview && window.pywebview.api) boot();
  else window.addEventListener("pywebviewready", boot);
})();
