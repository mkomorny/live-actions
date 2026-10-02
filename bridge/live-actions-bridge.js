// Live Actions — Max Audio Effect bridge.
// Desktop app talks OSC; this device talks Live Object Model.
// Live 12 ch. 31 (Max for Live / Live API). Do not construct LiveAPI in loadbang.
"use strict";

autowatch = 1;
inlets = 1;
outlets = 2;

// outlet 0: OSC message to udpsend
// outlet 1: status string for the device face

var ready = false;
var lastPing = 0;
// install.ps1 stamps a fresh value into the deployed copy on every install;
// this placeholder is what an un-redeployed or un-re-dropped device reports.
// hostTrackInfo() below puts this in both /live-actions/hello and /pong so
// the deploy script can confirm the running device is the one it just built.
var BRIDGE_BUILD = "dev";

function unwrap(v) {
    if (v === null || v === undefined) return v;
    if (typeof v === "object" && v.length !== undefined && typeof v !== "string") {
        return v.length ? v[0] : v;
    }
    return v;
}

function setStatus(msg) {
    // textedit doesn't accept a bare string message -- it needs the "set"
    // prefix to update its buffer without producing output (Max docs:
    // "set", followed by any message, sets the contents of the textedit
    // object's buffer while causing no output). Sending the string alone
    // used to log "textedit doesn't understand ..." and never rendered.
    // Split into separate word atoms rather than one atom containing
    // spaces -- a single space-containing atom round-trips through Max's
    // atom-to-text conversion wrapped in quotes (the same quoting print
    // uses for a symbol with an embedded space), which showed up on the
    // device face as a literal "quoted string".
    var text = String(msg);
    var words = text.split(/\s+/).filter(function (w) { return w.length > 0; });
    // outlet()'s array form is unrolled into a Max list (one level only) --
    // this js object predates the v8 engine, and its outlet() built-in
    // doesn't support Function.prototype.apply (confirmed live: it throws
    // "error calling function ..." on any caller using outlet.apply()).
    outlet(1, ["set"].concat(words.length ? words : [""]));
    post("live-actions-bridge: " + msg + "\n");
}

function sendOsc(address) {
    var args = arrayfromargs(arguments);
    outlet(0, args);
}

// UDP's own payload ceiling is 65507 bytes; Windows recvfrom on the app side
// raises WSAEMSGSIZE instead of silently truncating like POSIX, which used
// to permanently kill the app's listener thread on any reply this size (a
// Genius read_set against a real Set routinely clears it -- palReadSet has
// no cap of its own). 48000 still sat close enough to Max's own per-atom
// text ceiling that a large Genius/Pal reply occasionally arrived at the
// app as a fully-reassembled but EMPTY string (P4 A2) -- Max's own message
// plumbing silently dropped the oversized atom before udpsend ever saw it,
// which is a different failure than the UDP-datagram-size problem this
// chunking was originally built for. Kept well under both ceilings now.
// Small replies -- the overwhelming majority -- go out exactly as before:
// a single (key, payload) message.
var REPLY_CHUNK_LIMIT = 4000;

function sendChunked(address, key, payload) {
    var str = String(payload);
    if (str.length <= REPLY_CHUNK_LIMIT) {
        sendOsc(address, key, str);
        return;
    }
    var total = Math.ceil(str.length / REPLY_CHUNK_LIMIT);
    var i;
    for (i = 0; i < total; i++) {
        var piece = str.substring(i * REPLY_CHUNK_LIMIT, (i + 1) * REPLY_CHUNK_LIMIT);
        sendOsc(address, key, i, total, piece);
    }
}

function normalizeAddr(addr) {
    addr = String(addr || "");
    if (addr.charAt(0) === "/") addr = addr.substring(1);
    return addr;
}

function hostTrackInfo() {
    var info = { on_track: false, track: "", kind: "", path: "", id: "", build: BRIDGE_BUILD };
    try {
        var node = new LiveAPI("this_device");
        if (!node || Number(node.id) === 0) return info;
        var guard = 0;
        while (node && Number(node.id) !== 0 && guard < 16) {
            var parentRaw = node.get("canonical_parent");
            var parentId = extractId(parentRaw);
            if (!parentId) break;
            node = new LiveAPI("id " + parentId);
            if (!node || Number(node.id) === 0) break;
            var typ = String(node.type || "");
            if (typ === "Track") {
                var name = String(unwrap(node.get("name")) || "");
                var hasMidi = !!unwrap(node.get("has_midi_input"));
                var hasAudio = !!unwrap(node.get("has_audio_input"));
                var kind = "audio";
                if (hasMidi && !hasAudio) kind = "midi";
                info.on_track = true;
                info.track = name || ("Track id " + node.id);
                info.kind = kind;
                info.id = String(node.id);
                info.path = String(node.unquotedpath || node.path || "");
                return info;
            }
            guard += 1;
        }
    } catch (e) {
        return info;
    }
    return info;
}

function hostJson() {
    var info = hostTrackInfo();
    if (info.on_track) {
        setStatus("On track: " + info.track);
    } else {
        setStatus("Device not on a track");
    }
    return stringify(info);
}

var initTask = null;

function initBridge() {
    ready = true;
    var info = hostTrackInfo();
    if (info.on_track) {
        setStatus("On track: " + info.track + " — waiting for desktop app");
    } else {
        setStatus("Drop this device on a track");
    }
    sendOsc("/live-actions/hello", stringify(info));
}

function bang() {
    initBridge();
}

function loadbang() {
    setStatus("Waiting for Live…");
    try {
        if (initTask) {
            initTask.cancel();
        }
        initTask = new Task(function () {
            initBridge();
        }, this);
        initTask.schedule(250);
    } catch (eTask) {
        // Fallback if Task is unavailable
    }
}

function FullPacket() {
    // Defensive only -- shouldn't fire under normal decoded-message dispatch.
    // udpreceive has no "off" value for full-packet mode; the earlier
    // "@fullpacket 0" on the object itself was invalid syntax (Max Console:
    // "fullpacket" is not a valid attribute argument) and did nothing. The
    // decoded anything()/list() path below is the default -- just omit the
    // argument entirely, don't try to pass a falsy value to disable it.
    setStatus("Got raw OSC packet — remove any fullpacket argument from udpreceive");
}

function anything() {
    dispatch(messagename, arrayfromargs(arguments));
}

function list() {
    var a = arrayfromargs(arguments);
    if (!a.length) return;
    dispatch(a[0], a.slice(1));
}

function openhost() {
    initBridge();
    // [system] and [shell] are both blocked inside Max for Live's sandbox --
    // launchbrowser + the liveactions:// URL protocol (registered by
    // install.ps1) is the only mechanism that actually works here. A prior
    // version also tried a [system]-object fallback for when launchbrowser
    // failed; that object doesn't exist in Max at all ("system: No such
    // object", logged on every device load) and would have been blocked by
    // the M4L sandbox even under a real object name like [shell], so it
    // could never have fired. Removed rather than fixed under a different
    // object name.
    try {
        max.launchbrowser("liveactions://open");
        setStatus("Opening desktop host…");
    } catch (e) {
        setStatus("Couldn't open desktop host — run install.ps1.");
    }
}

function dispatch(addr, args) {
    var name = normalizeAddr(addr);
    if (!ready) {
        ready = true;
    }
    if (name === "live-actions/ping") {
        lastPing = Date.now();
        var info = hostTrackInfo();
        info.pong = lastPing;
        if (info.on_track) setStatus("Desktop app connected — " + info.track);
        else setStatus("Desktop app connected — not on a track");
        sendOsc("/live-actions/pong", stringify(info));
        return;
    }
    if (name === "live-actions/status") {
        sendOsc("/live-actions/status", statusJson());
        return;
    }
    if (name === "live-actions/tracks") {
        sendOsc("/live-actions/tracks", tracksJson());
        return;
    }
    if (name === "live-actions/run") {
        var id = args.length ? String(args[0]) : "";
        var payload = args.length > 1 ? String(args[1]) : "";
        runTool(id, payload);
        return;
    }
    if (name === "live-actions/api/get") {
        sendOsc("/live-actions/api/reply", apiGet(args));
        return;
    }
    if (name === "live-actions/api/set") {
        sendOsc("/live-actions/api/reply", apiSet(args));
        return;
    }
    if (name === "live-actions/api/call") {
        sendOsc("/live-actions/api/reply", apiCall(args));
        return;
    }
    if (name === "live-actions/call") {
        var reqId = args.length ? String(args[0]) : "";
        var action = args.length > 1 ? String(args[1]) : "";
        var payloadRaw = args.length > 2 ? String(args[2]) : "";
        var reply = handleLiveCall(action, parseJson(payloadRaw) || {});
        var replyStr = stringify(reply);
        if (replyStr.length > REPLY_CHUNK_LIMIT) {
            // Diagnostic for the still-unresolved "payload was empty" reports
            // against large Sets (v1.0.33 live test pass) -- everything about
            // the reassembly path checks out by inspection, so log the one
            // fact static reading can't produce: the real size and chunk
            // count Max is about to try to send. Check the Max Console next
            // time this happens.
            post("live-actions-bridge: chunking " + action + " reply, " + replyStr.length +
                " chars into " + Math.ceil(replyStr.length / REPLY_CHUNK_LIMIT) + " pieces\n");
        }
        sendChunked("/live-actions/reply", reqId, replyStr);
        return;
    }
    if (name === "live-actions/reset") {
        // Manual recovery path for the Max-side half of a dead bridge (the
        // app's "Reset Bridge" button sends this after rebuilding its own
        // listener socket) -- clears anything that could be stranding every
        // future run, then re-arms and replies fresh so the app doesn't have
        // to wait for the next ping cycle to see it come back.
        cancelSkeleton();
        skeletonJob = null;
        ready = false;
        tryReArm();
        setStatus(ready ? "Bridge reset." : "Bridge reset -- Live API still not reachable.");
        sendOsc("/live-actions/hello", hostJson());
        return;
    }
}

// ready is normally set once by bang() from live.thisdevice at load. If
// autowatch silently reloaded this script while the device was already
// sitting on a track -- install.ps1 rewrites the deployed js in place, and
// Max reloads a running js object's script on file change even without a
// re-drop -- ready resets to false and nothing ever re-bangs it, so every
// action fails forever even though the device still answers pings. A probe
// this far past load time can safely stand in for the missed bang: Live
// itself is already fully up by the time any OSC message reaches here, so
// this doesn't touch the "no LiveAPI in loadbang" constraint (that's about
// load time, not message time).
function tryReArm() {
    try {
        var probe = new LiveAPI("live_set");
        if (probe && (Number(probe.id) !== 0 || probe.path)) {
            ready = true;
            return true;
        }
    } catch (e) {}
    return false;
}

function liveApi(path) {
    if (!ready && !tryReArm()) return null;
    try {
        var strPath = String(path);
        var api = new LiveAPI(strPath);
        if (!api) return null;
        // Global singletons like live_app, live_app browser, and live_set have id == 0 or string paths
        if (strPath.indexOf("live_app") === 0 || strPath.indexOf("live_set") === 0) {
            if (api.unquotedpath || api.path || api.id != 0 || api.type) {
                return api;
            }
        }
        if (api.id == 0 && (!api.path || api.path === "")) return null;
        return api;
    } catch (e) {
        return null;
    }
}

function selectedTrackId() {
    var view = liveApi("live_set view");
    if (!view) return "";
    try {
        var raw = view.get("selected_track");
        if (raw && typeof raw === "object" && raw.length) {
            return String(raw[raw.length - 1]);
        }
        return String(unwrap(raw) || "");
    } catch (e) {
        return "";
    }
}

function describeTrack(path, index, kind) {
    var t = liveApi(path);
    if (!t) return null;
    if (!kind) {
        kind = unwrap(t.get("has_midi_input")) ? "midi" : "audio";
    }
    var name = String(unwrap(t.get("name")) || "");
    if (!name) {
        if (kind === "master") name = "Master";
        else if (kind === "return") name = "Return " + String(index + 1);
        else name = "Track " + String(index + 1);
    }
    var deviceNames = [];
    try {
        var devCount = t.getcount("devices");
        var di;
        for (di = 0; di < devCount; di++) {
            var dev = liveApi(path + " devices " + di);
            if (dev) deviceNames.push(String(unwrap(dev.get("name")) || ""));
        }
    } catch (eDevNames) {}
    return {
        key: kind + ":" + String(index),
        index: Number(index),
        id: String(t.id),
        name: name,
        kind: kind,
        path: path,
        devices: deviceNames
    };
}

function tracksJson() {
    var song = liveApi("live_set");
    if (!song) {
        return stringify({ ok: false, error: "Live API not ready. Is the device on a track?" });
    }
    var selectedId = selectedTrackId();
    var tracks = [];
    var i;
    var n = song.getcount("tracks");
    for (i = 0; i < n; i++) {
        var item = describeTrack("live_set tracks " + i, i, "");
        if (item) {
            item.selected_in_live = item.id === selectedId;
            tracks.push(item);
        }
    }
    var rn = song.getcount("return_tracks");
    for (i = 0; i < rn; i++) {
        var ret = describeTrack("live_set return_tracks " + i, i, "return");
        if (ret) {
            ret.selected_in_live = ret.id === selectedId;
            tracks.push(ret);
        }
    }
    var master = describeTrack("live_set master_track", 0, "master");
    if (master) {
        if (!master.name) master.name = "Master";
        master.selected_in_live = master.id === selectedId;
        tracks.push(master);
    }
    return stringify({ ok: true, selected_id: selectedId, tracks: tracks });
}

function statusJson() {
    var api = liveApi("live_set");
    if (!api) {
        return stringify({ ok: false, error: "Live API not ready. Is the device on a track?" });
    }
    var sigNum = unwrap(api.get("signature_numerator"));
    var sigDen = unwrap(api.get("signature_denominator"));
    var tracks = api.getcount("tracks");
    var host = hostTrackInfo();
    return stringify({
        ok: true,
        name: String(unwrap(api.get("name")) || ""),
        tempo: Number(unwrap(api.get("tempo"))),
        tracks: Number(tracks),
        time_signature: String(sigNum) + "/" + String(sigDen),
        on_track: host.on_track,
        host_track: host.track,
        host_kind: host.kind,
        host_path: host.path
    });
}

function apiGet(args) {
    if (args.length < 2) {
        return stringify({ ok: false, error: "api/get needs path and property" });
    }
    var api = liveApi(args[0]);
    if (!api) return stringify({ ok: false, error: "No Live object at " + args[0] });
    try {
        return stringify({ ok: true, value: api.get(String(args[1])) });
    } catch (e) {
        return stringify({ ok: false, error: String(e) });
    }
}

function apiSet(args) {
    if (args.length < 3) {
        return stringify({ ok: false, error: "api/set needs path, property, value" });
    }
    var api = liveApi(args[0]);
    if (!api) return stringify({ ok: false, error: "No Live object at " + args[0] });
    try {
        api.set(String(args[1]), args[2]);
        return stringify({ ok: true });
    } catch (e) {
        return stringify({ ok: false, error: String(e) });
    }
}

function apiCall(args) {
    if (args.length < 2) {
        return stringify({ ok: false, error: "api/call needs path and method" });
    }
    var api = liveApi(args[0]);
    if (!api) return stringify({ ok: false, error: "No Live object at " + args[0] });
    try {
        var result = api.call.apply(api, args.slice(1));
        return stringify({ ok: true, value: result });
    } catch (e) {
        return stringify({ ok: false, error: String(e) });
    }
}

function stringify(obj) {
    try {
        // Escape every non-ASCII character to \uXXXX. A track/clip/sample
        // name with real unicode (smart quotes, accents, emoji) otherwise
        // reaches Max's own text-atom encoding as multi-byte UTF-8, which
        // makes REPLY_CHUNK_LIMIT's plain .length-based math (a JS string
        // length is UTF-16 code units, not bytes) undercount the actual
        // atom size sendChunked() is trying to stay under.
        return JSON.stringify(obj).replace(/[-￿]/g, function (ch) {
            return "\\u" + ("0000" + ch.charCodeAt(0).toString(16)).slice(-4);
        });
    } catch (e) {
        return "{\"ok\":false,\"error\":\"json\"}";
    }
}

function parseJson(raw) {
    try {
        return JSON.parse(String(raw || ""));
    } catch (e) {
        return null;
    }
}

function extractId(raw) {
    if (raw === null || raw === undefined) return "";
    if (typeof raw === "object" && raw.length !== undefined && typeof raw !== "string") {
        return String(raw[raw.length - 1] || "");
    }
    return String(unwrap(raw) || "");
}

function liveApiId(id) {
    if (id === null || id === undefined || id === "") return null;
    try {
        var numId = Number(id);
        var api = new LiveAPI();
        if (!isNaN(numId) && numId !== 0) {
            api.id = numId;
        } else {
            api.goto("id " + String(id));
        }
        if (!api || api.info === "No object") {
            try {
                var api2 = new LiveAPI("id " + String(id));
                if (api2 && api2.info !== "No object") return api2;
            } catch (e2) {}
            return null;
        }
        return api;
    } catch (e) {
        return null;
    }
}

function toolJobs() {
    return {
        "clip-namer": runClipNamer,
        "arrangement-skeleton": runSkeleton,
        "mutate": runMutate,
        "empty-clips": runEmptyClips,
        "color-clips": runColorClips,
        "duplicate-clips": runDuplicateClips,
        "track-batch": runTrackBatch,
        "reveal-device": runRevealDevice,
        "fill-forge": runBreakdowns,
        "detect-key": runDetectKey,
        "song-mapper": runArrangementHelper
    };
}

function runTool(id, rawPayload) {
    var payload = parseJson(rawPayload);
    if (!payload || typeof payload !== "object") {
        sendChunked("/live-actions/result", "error", "Bad tool payload");
        setStatus("Run failed — bad JSON");
        return;
    }
    var jobs = toolJobs();
    if (jobs[id]) {
        try {
            var result = jobs[id](payload);
            if (result && result.pending) {
                setStatus(result.message || "Working…");
                return;
            }
            if (result && result.ok) {
                sendChunked("/live-actions/result", "ok", result.message);
                setStatus(result.message);
            } else {
                sendChunked("/live-actions/result", "error", (result && result.message) || "Failed");
                setStatus((id || "tool") + " — " + ((result && result.message) || "failed"));
            }
        } catch (e) {
            sendChunked("/live-actions/result", "error", String(e));
            setStatus((id || "tool") + " — error");
        }
        return;
    }
    sendOsc(
        "/live-actions/result",
        "error",
        "No job for this tool yet: " + (id || "(none)")
    );
    setStatus("Run ignored — " + (id || "unknown"));
}

function runToolDirect(id, payload) {
    var jobs = toolJobs();
    if (jobs[id]) {
        try {
            var result = jobs[id](payload);
            return result || { ok: true, message: "Executed " + id };
        } catch (e) {
            return { ok: false, error: String(e) };
        }
    }
    return { ok: false, error: "No job for tool: " + id };
}

function hexToLiveColor(hex) {
    if (typeof hex === "number") return hex;
    if (typeof hex === "string") {
        hex = hex.replace(/^#/, "");
        if (hex.length === 6) {
            return parseInt(hex, 16);
        }
    }
    return 0;
}

function handleLiveCall(action, params) {
    if (!ready) {
        return { ok: false, error: "Live API not ready" };
    }
    params = params || {};
    try {
        if (typeof palHandle === "function") {
            var palResult = palHandle(action, params);
            if (palResult) return palResult;
        }
        if (action === "arrangement_plan") {
            // Step 3 of the song-mapper plan (§4): read-only reply
            // built from the shared computeArrangementPlan (defined near
            // readArrangementClips) -- strips the live LiveAPI object
            // references (song, sectionTrack) that only arrangement_execute
            // needs, since those can't cross the JSON reply boundary.
            var apPlan = computeArrangementPlan(params);
            if (!apPlan.ok) return apPlan;
            return {
                ok: true,
                startPosition: apPlan.startPosition,
                clearEnd: apPlan.clearEnd,
                sectionCount: apPlan.sectionCount,
                remapTrackCount: apPlan.remapTrackCount,
                moved: apPlan.moved,
                dropped: apPlan.dropped,
                skipped: apPlan.skipped,
                unlooped: apPlan.unlooped,
                writeCount: apPlan.writeCount,
                undoStepCount: apPlan.undoStepCount,
                fingerprint: apPlan.fingerprint
            };
        }
        if (action === "arrangement_scan") {
            // Step 3b of the song-mapper plan (§3b/§6): read-only
            // edit-mode seed -- Python calls this
            // on a worker thread BEFORE opening the dialog, so isEditing/
            // sections/scanCount/nextId can be real instead of the honest
            // static defaults Steps 2-4 shipped with. Uses the same shared
            // readArrangementClips reader arrangement_plan uses, so the two
            // never disagree about what's on the track.
            if (skeletonBusy()) {
                return { ok: false, message: "A locator pass is still running. Wait for it to finish." };
            }
            var asTrackPath = String(params.trackPath || "");
            if (!asTrackPath) return { ok: false, message: "No section track chosen." };
            var asTrack = liveApi(asTrackPath);
            if (!asTrack) return { ok: false, message: "Could not access " + asTrackPath + "." };
            if (!unwrap(asTrack.get("has_midi_input"))) {
                return {
                    ok: false,
                    message: "'" + String(unwrap(asTrack.get("name")) || asTrackPath) +
                        "' is an audio track. Song Mapper needs a MIDI track."
                };
            }
            var asBeatsPerBar = songBarBeats();
            var asAllClips = readArrangementClips(asTrackPath);
            var asTotalCount = asAllClips.length;
            // >200 clips: seed only the first 200 into the editable list, but
            // report the REAL total as scanCount -- arrangement_plan's own
            // concurrency guard compares against this number later, so
            // truncating it here would make every subsequent run refuse.
            var asTruncated = asTotalCount > 200;
            var asClips = asTruncated ? asAllClips.slice(0, 200) : asAllClips;
            var asSections = [];
            var asIdx;
            for (asIdx = 0; asIdx < asClips.length; asIdx++) {
                var asClip = asClips[asIdx];
                var asBars = Math.max(1, Math.round(asClip.duration / asBeatsPerBar));
                var asColor = asClip.color;
                asSections.push({
                    id: asIdx,
                    name: asClip.name || ("Section " + (asIdx + 1)),
                    bars: asBars,
                    color: (isNaN(asColor) ? 0 : asColor)
                });
            }
            var asStartBar = asAllClips.length ? (Math.floor(asAllClips[0].start / asBeatsPerBar) + 1) : null;
            return {
                ok: true,
                isEditing: asTotalCount > 0,
                sections: asSections,
                scanCount: asTotalCount,
                nextId: asSections.length,
                startBar: asStartBar,
                truncated: asTruncated
            };
        }
        if (action === "read_set") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var numTracks = song.getcount("tracks");
            var tracks = [];
            var i;
            for (i = 0; i < numTracks; i++) {
                var tp = "live_set tracks " + i;
                var t = liveApi(tp);
                if (!t) continue;
                var kind = unwrap(t.get("has_midi_input")) ? "midi" : "audio";
                var tName = String(unwrap(t.get("name")) || ("Track " + (i + 1)));
                var tColor = unwrap(t.get("color"));
                var tMute = !!unwrap(t.get("mute"));
                var tSolo = !!unwrap(t.get("solo"));
                var tArm = !!unwrap(t.get("arm"));
                var volMixer = liveApi(tp + " mixer_device volume");
                var panMixer = liveApi(tp + " mixer_device panning");
                var vol = volMixer ? Number(unwrap(volMixer.get("value"))) : 0.85;
                var pan = panMixer ? Number(unwrap(panMixer.get("value"))) : 0.0;

                var slotCount = Math.min(16, t.getcount("clip_slots"));
                var slots = [];
                var s;
                for (s = 0; s < slotCount; s++) {
                    var sl = liveApi(tp + " clip_slots " + s);
                    if (!sl) continue;
                    var hasClip = !!unwrap(sl.get("has_clip"));
                    var slotInfo = { index: s, has_clip: hasClip };
                    if (hasClip) {
                        var cl = liveApi(tp + " clip_slots " + s + " clip");
                        if (cl) {
                            slotInfo.name = String(unwrap(cl.get("name")) || "");
                            slotInfo.color = unwrap(cl.get("color"));
                            slotInfo.length = Number(unwrap(cl.get("length")) || 0);
                            slotInfo.is_playing = !!unwrap(cl.get("is_playing"));
                            slotInfo.is_recording = !!unwrap(cl.get("is_recording"));
                        }
                    }
                    slots.push(slotInfo);
                }

                var devCount = t.getcount("devices");
                var devices = [];
                var d;
                for (d = 0; d < devCount; d++) {
                    var dev = liveApi(tp + " devices " + d);
                    if (!dev) continue;
                    devices.push({
                        index: d,
                        name: String(unwrap(dev.get("name")) || ""),
                        class_name: String(unwrap(dev.get("class_name")) || ""),
                        is_active: !!unwrap(dev.get("is_active"))
                    });
                }

                tracks.push({
                    index: i,
                    name: tName,
                    kind: kind,
                    color: tColor,
                    mute: tMute,
                    solo: tSolo,
                    arm: tArm,
                    volume: vol,
                    pan: pan,
                    clip_slots: slots,
                    devices: devices
                });
            }

            var numScenes = song.getcount("scenes");
            var scenes = [];
            for (i = 0; i < Math.min(32, numScenes); i++) {
                var sc = liveApi("live_set scenes " + i);
                if (sc) {
                    scenes.push({
                        index: i,
                        name: String(unwrap(sc.get("name")) || ("Scene " + (i + 1))),
                        color: unwrap(sc.get("color"))
                    });
                }
            }

            return {
                ok: true,
                set: {
                    name: String(unwrap(song.get("name")) || "Untitled"),
                    tempo: Number(unwrap(song.get("tempo"))),
                    time_signature: String(unwrap(song.get("signature_numerator"))) + "/" + String(unwrap(song.get("signature_denominator"))),
                    is_playing: !!unwrap(song.get("is_playing")),
                    current_song_time: Number(unwrap(song.get("current_song_time")) || 0),
                    track_count: numTracks,
                    scene_count: numScenes,
                    tracks: tracks,
                    scenes: scenes
                }
            };
        }

        if (action === "create_track") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var type = String(params.type || "midi").toLowerCase();
            var countBefore = song.getcount("tracks");
            var targetIdx = (params.index != null && params.index >= 0) ? params.index : -1;

            if (type === "midi") {
                song.call("create_midi_track", targetIdx);
            } else if (type === "audio") {
                song.call("create_audio_track", targetIdx);
            } else if (type === "return") {
                song.call("create_return_track");
                return { ok: true, message: "Created return track" };
            } else {
                return { ok: false, error: "Unknown track type: " + type };
            }

            var createdIdx = (targetIdx >= 0 && targetIdx < countBefore) ? targetIdx : (song.getcount("tracks") - 1);
            var createdTrack = liveApi("live_set tracks " + createdIdx);
            if (createdTrack) {
                if (params.name) createdTrack.set("name", String(params.name));
                if (params.color) createdTrack.set("color", hexToLiveColor(params.color));
            }
            return {
                ok: true,
                message: "Created " + type + " track " + palLiveNum(createdIdx) + (params.name ? " ('" + params.name + "')" : ""),
                track_index: createdIdx,
                name: params.name || ("Track " + (createdIdx + 1))
            };
        }

        if (action === "create_clip") {
            var trackIdx = Number(params.track_index != null ? params.track_index : 0);
            var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
            var slot = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
            if (!slot) return { ok: false, error: "Clip slot " + palLiveNum(trackIdx) + "/" + palLiveNum(slotIdx) + " not found" };

            if (unwrap(slot.get("has_clip"))) {
                slot.call("delete_clip");
            }
            var len = Number(params.length_beats || 4);
            slot.call("create_clip", len);
            var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
            if (clip) {
                if (params.name) clip.set("name", String(params.name));
                if (params.color) clip.set("color", hexToLiveColor(params.color));
            }
            return {
                ok: true,
                message: "Created clip at track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) + " (" + len + " beats)",
                track_index: trackIdx,
                slot_index: slotIdx,
                length_beats: len
            };
        }

        if (action === "write_notes") {
            var trackIdx = palTrackIndexFromParams(params, 0);
            var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
            var slot = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
            if (!slot) return { ok: false, error: "Clip slot " + palLiveNum(trackIdx) + "/" + palLiveNum(slotIdx) + " not found" };
            var wnTrack = liveApi("live_set tracks " + trackIdx);
            if (!wnTrack || !unwrap(wnTrack.get("has_midi_input"))) {
                // create_clip is MIDI-only; on an audio track it's a silent
                // no-op per clip.call()'s never-throws quirk, which used to
                // report a false "wrote N notes" success with nothing there.
                return { ok: false, error: "Track " + palLiveNum(trackIdx) + " is audio, not MIDI -- cannot write notes.", track_index: trackIdx, slot_index: slotIdx };
            }

            var rawNotes = params.notes || [];
            if (typeof rawNotes === "string") {
                try {
                    rawNotes = JSON.parse(rawNotes);
                } catch (e) {
                    return { ok: false, error: "'notes' string is not valid JSON: " + e.message };
                }
                if (!(rawNotes instanceof Array)) {
                    return { ok: false, error: "'notes' JSON must decode to an array" };
                }
            }
            var normNotes = [];
            var maxEnd = 4;
            for (var i = 0; i < rawNotes.length; i++) {
                var n = rawNotes[i];
                var st = Number(n.startTime != null ? n.startTime : (n.start_time != null ? n.start_time : 0));
                var dur = Number(n.duration != null ? n.duration : 0.25);
                var pit = Number(n.pitch != null ? n.pitch : 60);
                var vel = Number(n.velocity != null ? n.velocity : 100);
                var noteObj = { pitch: pit, startTime: st, duration: dur, velocity: vel, mute: !!n.mute };
                if (n.probability != null) noteObj.probability = Math.max(0, Math.min(1, Number(n.probability)));
                if (n.velocity_deviation != null) noteObj.velocity_deviation = Math.max(-127, Math.min(127, Number(n.velocity_deviation)));
                normNotes.push(noteObj);
                if (st + dur > maxEnd) maxEnd = st + dur;
            }

            if (!unwrap(slot.get("has_clip"))) {
                var clipLen = params.length_beats ? Number(params.length_beats) : Math.max(4, Math.ceil(maxEnd / 4) * 4);
                slot.call("create_clip", clipLen);
            }

            var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
            if (!clip) return { ok: false, error: "Could not access clip in slot" };

            if (params.name) clip.set("name", String(params.name));
            if (params.color) clip.set("color", hexToLiveColor(params.color));
            if (params.length_beats) {
                // clip.set("length") silently no-ops -- length is read-only
                // on Clip; loop_end is what actually resizes it (Low item).
                clip.set("loop_end", Number(params.length_beats));
            }

            writeNotes(clip, normNotes, params.replace !== false);
            return {
                ok: true,
                message: "Wrote " + normNotes.length + " notes into track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) + (params.name ? " ('" + params.name + "')" : ""),
                notes_written: normNotes.length,
                track_index: trackIdx,
                slot_index: slotIdx
            };
        }

        if (action === "read_clip_notes") {
            var trackIdx = Number(params.track_index != null ? params.track_index : 0);
            var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
            var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
            if (!clip) return { ok: false, error: "No clip in track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) };

            var clipLen = Number(unwrap(clip.get("length")) || 4);
            var clipName = String(unwrap(clip.get("name")) || "");

            var notes = [];
            try {
                var d = new Dict();
                clip.call("get_notes_extended", 0, 128, 0, clipLen, d);
                var parsed = JSON.parse(d.getjson());
                d.freepeer();
                if (parsed && parsed.notes) {
                    notes = parsed.notes;
                }
            } catch (e) {}

            return {
                ok: true,
                track_index: trackIdx,
                slot_index: slotIdx,
                name: clipName,
                length: clipLen,
                notes: notes
            };
        }

        if (action === "update_track") {
            var trackIdx = Number(params.track_index != null ? params.track_index : 0);
            var track = liveApi("live_set tracks " + trackIdx);
            if (!track) return { ok: false, error: "Track " + palLiveNum(trackIdx) + " not found" };

            if (params.name != null) track.set("name", String(params.name));
            if (params.color != null) track.set("color", hexToLiveColor(params.color));
            if (params.mute != null) track.set("mute", params.mute ? 1 : 0);
            if (params.solo != null) track.set("solo", params.solo ? 1 : 0);
            if (params.arm != null) track.set("arm", params.arm ? 1 : 0);
            if (params.volume != null) {
                var vm = liveApi("live_set tracks " + trackIdx + " mixer_device volume");
                if (vm) vm.set("value", Math.max(0.0, Math.min(1.0, Number(params.volume))));
            }
            if (params.pan != null) {
                var pm = liveApi("live_set tracks " + trackIdx + " mixer_device panning");
                if (pm) pm.set("value", Math.max(-1.0, Math.min(1.0, Number(params.pan))));
            }
            return { ok: true, message: "Updated track " + palLiveNum(trackIdx) };
        }

        if (action === "update_clip") {
            var trackIdx = Number(params.track_index != null ? params.track_index : 0);
            var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
            var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
            if (!clip) return { ok: false, error: "Clip not found" };

            if (params.name != null) clip.set("name", String(params.name));
            if (params.color != null) clip.set("color", hexToLiveColor(params.color));
            if (params.mute != null) clip.set("muted", params.mute ? 1 : 0);
            if (params.loop != null) clip.set("looping", params.loop ? 1 : 0);
            if (params.length_beats != null) {
                // clip.set("length") silently no-ops -- length is read-only
                // on Clip; loop_end is what actually resizes it (Low item).
                clip.set("loop_end", Number(params.length_beats));
            }
            return { ok: true, message: "Updated clip at track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) };
        }

        if (action === "playback") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var subAction = String(params.action || "play").toLowerCase();

            if (subAction === "play" || subAction === "start") {
                if (params.start_time != null) song.set("current_song_time", Number(params.start_time));
                song.call("start_playing");
                return { ok: true, message: "Playback started" };
            } else if (subAction === "stop") {
                song.call("stop_playing");
                return { ok: true, message: "Playback stopped" };
            } else if (subAction === "continue") {
                song.call("continue_playing");
                return { ok: true, message: "Playback resumed" };
            } else if (subAction === "fire_clip" || subAction === "play_clip") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
                var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
                if (!clip) return { ok: false, error: "Clip not found" };
                clip.call("fire");
                return { ok: true, message: "Fired clip at track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) };
            } else if (subAction === "stop_clip") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                var t = liveApi("live_set tracks " + trackIdx);
                if (t) t.call("stop_all_clips");
                return { ok: true, message: "Stopped clips on track " + palLiveNum(trackIdx) };
            } else if (subAction === "fire_scene" || subAction === "play_scene") {
                var sceneIdx = Number(params.scene_index != null ? params.scene_index : 0);
                var sc = liveApi("live_set scenes " + sceneIdx);
                if (!sc) return { ok: false, error: "Scene not found" };
                sc.call("fire");
                return { ok: true, message: "Fired scene " + sceneIdx };
            }
            return { ok: false, error: "Unknown playback action: " + subAction };
        }

        if (action === "set_tempo") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var tempo = Math.max(20.0, Math.min(999.0, Number(params.tempo || 120.0)));
            song.set("tempo", tempo);
            return { ok: true, message: "Tempo set to " + tempo + " BPM", tempo: tempo };
        }

        if (action === "create_scene") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var sceneIdx = params.scene_index != null ? Number(params.scene_index) : -1;
            song.call("create_scene", sceneIdx);
            var createdIdx = sceneIdx >= 0 ? sceneIdx : (song.getcount("scenes") - 1);
            var sc = liveApi("live_set scenes " + createdIdx);
            if (sc) {
                if (params.name) sc.set("name", String(params.name));
                if (params.color) sc.set("color", hexToLiveColor(params.color));
            }
            return { ok: true, message: "Created scene " + createdIdx, scene_index: createdIdx };
        }

        if (action === "delete") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var type = String(params.type || "clip").toLowerCase();
            if (type === "track") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                song.call("delete_track", trackIdx);
                return { ok: true, message: "Deleted track " + palLiveNum(trackIdx) };
            } else if (type === "clip") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
                var slot = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
                if (slot) slot.call("delete_clip");
                return { ok: true, message: "Deleted clip at track " + palLiveNum(trackIdx) + ", slot " + palLiveNum(slotIdx) };
            } else if (type === "scene") {
                var sceneIdx = Number(params.scene_index != null ? params.scene_index : 0);
                song.call("delete_scene", sceneIdx);
                return { ok: true, message: "Deleted scene " + sceneIdx };
            }
            return { ok: false, error: "Unknown delete type: " + type };
        }

        if (action === "duplicate") {
            var song = liveApi("live_set");
            if (!song) return { ok: false, error: "Cannot access live_set" };
            var type = String(params.type || "clip").toLowerCase();
            if (type === "track") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                song.call("duplicate_track", trackIdx);
                return { ok: true, message: "Duplicated track " + palLiveNum(trackIdx) };
            } else if (type === "clip") {
                var trackIdx = Number(params.track_index != null ? params.track_index : 0);
                var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
                var toSlot = Number(params.to_slot != null ? params.to_slot : (slotIdx + 1));
                var slot = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
                var destSlot = liveApi("live_set tracks " + trackIdx + " clip_slots " + toSlot);
                if (slot && destSlot) {
                    slot.call("duplicate_clip_to", "id", extractId(destSlot.id));
                    return { ok: true, message: "Duplicated clip to slot " + toSlot };
                }
                return { ok: false, error: "Could not duplicate clip" };
            }
            return { ok: false, error: "Unknown duplicate type: " + type };
        }

        // Note: "load_device" / "create_device" / "load_drum_rack" are claimed
        // earlier by palHandle (live-actions-pal.js, palCreateDevice) -- this
        // action never reaches this switch. Do not add a second handler here;
        // it would silently drift from palCreateDevice's behavior.

        if (action === "run_tool") {
            var toolId = String(params.tool_id || "");
            var toolPayload = params.payload || {};
            var res = runToolDirect(toolId, toolPayload);
            return res;
        }

        if (action === "detect_key") {
            return runDetectKey({
                fields: {
                    scope: params.scope,
                    profile: params.profile,
                    results: params.results,
                    track_index: params.track_index != null ? params.track_index : params.track_indexes
                },
                tracks: []
            });
        }

        return { ok: false, error: "Unknown action: " + action };
    } catch (e) {
        return { ok: false, error: String(e) };
    }
}

function loadDeviceOntoTrack(trackIdx, deviceName) {
    // There is no Browser / BrowserItem class in the Live Object Model exposed
    // to Max for Live (live_app only has a "view" child) -- "live_app browser"
    // and BrowserItem.load_item() are not real LOM surface, which is why this
    // used to silently fail. Track.insert_device(device_name) is the real,
    // documented method (Live 12.3+). It only supports native Live devices --
    // Max for Live devices and plug-ins still have to be dragged from the
    // browser by hand.
    var track = liveApi("live_set tracks " + trackIdx);
    if (!track) return { ok: false, error: "Track " + palLiveNum(trackIdx) + " not found" };

    var targetName = String(deviceName || "").trim();
    if (!targetName) return { ok: false, error: "No device name given" };

    var view = liveApi("live_set view");
    if (view) {
        try {
            view.set("selected_track", "id", extractId(track.id));
        } catch (e) {}
    }

    var devCountBefore = track.getcount("devices");

    try {
        track.call("insert_device", targetName);
    } catch (e) {
        return {
            ok: false,
            error: "Could not insert '" + targetName + "': " + String(e) +
                ". insert_device only supports native Live devices (not Max for " +
                "Live devices or plug-ins), and the name must match what Live's " +
                "browser shows exactly, e.g. 'Drum Rack', 'EQ Eight', 'Operator'.",
            track_index: trackIdx,
            device_name: targetName
        };
    }

    var devCountAfter = track.getcount("devices");
    if (devCountAfter > devCountBefore) {
        var newIndex = devCountAfter - 1;
        var actualName = targetName;
        try {
            var inserted = liveApi("live_set tracks " + trackIdx + " devices " + newIndex);
            if (inserted) actualName = String(unwrap(inserted.get("name")) || targetName);
        } catch (eName) {}
        return {
            ok: true,
            message: "Inserted '" + actualName + "' onto track " + palLiveNum(trackIdx) + " at device " + palLiveNum(newIndex),
            track_index: trackIdx,
            device_index: newIndex,
            device_name: actualName
        };
    }

    return {
        ok: false,
        error: "Live did not insert '" + targetName + "'. Check the exact device " +
            "name (as shown in Live's browser) and that it is a native device.",
        track_index: trackIdx,
        device_name: targetName
    };
}

function midiTracksFromPayload(payload) {
    var tracks = payload.tracks || [];
    var out = [];
    var i;
    for (i = 0; i < tracks.length; i++) {
        var t = tracks[i];
        if (!t || !t.path) continue;
        if (String(t.kind || "") !== "midi") continue;
        if (!liveApi(t.path)) continue;
        out.push(t);
    }
    return out;
}

function runBreakdowns(payload) {
    var fields = payload.fields || {};
    var target = String(fields.target || "newClip");
    var notes = fields.notes || [];
    var lengthBeats = Number(fields.lengthBeats || 4);
    var name = String(fields.name || "Fill Forge");
    if (!notes.length) {
        return { ok: false, message: "That fill has no notes." };
    }
    if (!(lengthBeats > 0)) lengthBeats = 4;

    var midi = midiTracksFromPayload(payload);
    var result;
    if (target === "newTrack") {
        result = breakdownsNewTrack(notes, lengthBeats, name);
    } else if (target === "replace") {
        result = breakdownsReplace(midi, notes, lengthBeats, name);
    } else if (target === "append") {
        result = breakdownsAppend(midi, notes, lengthBeats, name);
    } else if (target === "playhead") {
        result = breakdownsPlayhead(midi, notes, lengthBeats, name);
    } else {
        result = breakdownsNewClip(midi, notes, lengthBeats, name);
    }
    if (result && result.ok) return result;
    return { ok: false, message: (result && result.message) || "Insert failed" };
}

function clipPath(clip) {
    try {
        return String(clip.unquotedpath || clip.path || "").replace(/^['"]|['"]$/g, "");
    } catch (e) {
        return "";
    }
}

function clipTrackPath(clip) {
    var path = clipPath(clip);
    var match = path.match(/^(live_set tracks \d+)/);
    return match ? match[1] : "";
}

function trackAllowed(path, midi) {
    var i;
    for (i = 0; i < midi.length; i++) {
        if (String(midi[i].path) === path) return true;
    }
    return false;
}

function detailMidiClip() {
    var view = liveApi("live_set view");
    if (!view) return null;
    var clip = liveApiId(extractId(view.get("detail_clip")));
    if (clip && unwrap(clip.get("is_midi_clip"))) return clip;
    var slot = liveApiId(extractId(view.get("highlighted_clip_slot")));
    if (!slot || !unwrap(slot.get("has_clip"))) return null;
    var fromSlot = liveApi(String(slot.unquotedpath || slot.path).replace(/^['"]|['"]$/g, "") + " clip");
    if (fromSlot && unwrap(fromSlot.get("is_midi_clip"))) return fromSlot;
    return null;
}

function detailAudioClip() {
    var view = liveApi("live_set view");
    if (!view) return null;
    var clip = liveApiId(extractId(view.get("detail_clip")));
    if (!clip) return null;
    // Deliberately no highlighted_clip_slot fallback like detailMidiClip() has --
    // that resolves a session-slot clip, and callers only ever operate on an
    // Arrangement clip. A session clip must be rejected, not silently accepted.
    if (unwrap(clip.get("is_audio_clip")) && unwrap(clip.get("is_arrangement_clip"))) return clip;
    return null;
}

// {start, span} in beats for an Arrangement clip's own timeline footprint --
// distinct from its internal loop window (loop_start/loop_end). Prefers
// end_time - start_time over length: on a looped Arrangement clip, length can
// be just the loop length (e.g. 1 bar) while the clip actually covers many
// bars, and using length here would under-count the real span.
function arrangementClipSpan(clip) {
    var start = Number(unwrap(clip.get("start_time")) || 0);
    var span = 0;
    try {
        var end = unwrap(clip.get("end_time"));
        if (end !== null && end !== undefined && end !== "") span = Number(end) - start;
    } catch (e) {}
    if (!(span > 0)) {
        try { span = Number(unwrap(clip.get("length")) || 0); } catch (e2) {}
    }
    return { start: start, span: span };
}

// Deletes every Arrangement clip on `track` overlapping [startBeats, endBeats).
// Iterates arrangement_clips backwards -- deleting shifts later indices, so a
// forward loop would skip clips.
function clearArrangementRange(track, trackPath, startBeats, endBeats) {
    var count = track.getcount("arrangement_clips");
    var i;
    for (i = count - 1; i >= 0; i--) {
        var clip = liveApi(trackPath + " arrangement_clips " + i);
        if (!clip) continue;
        var span = arrangementClipSpan(clip);
        if (span.start < endBeats && span.start + span.span > startBeats) {
            try { track.call("delete_clip", clip); } catch (e) {}
        }
    }
}

// Reads every Arrangement clip on a track, sorted by start time. Shared by
// arrangement_plan and (later) arrangement_scan -- plan's §4 "Shared reader".
// Duration comes from arrangementClipSpan (end_time - start_time), not
// clipLength()/length, which reads loop_end and under-counts a looped clip's
// real Arrangement footprint.
function readArrangementClips(trackPath) {
    var track = liveApi(trackPath), out = [], i;
    if (!track) return out;
    var n = track.getcount("arrangement_clips");
    for (i = 0; i < n; i++) {
        var c = liveApi(trackPath + " arrangement_clips " + i);
        if (!c) continue;
        var sp = arrangementClipSpan(c);
        out.push({
            id: String(c.id),
            start: sp.start,
            duration: sp.span,
            name: String(unwrap(c.get("name")) || ""),
            color: Number(unwrap(c.get("color"))),
            looping: !!unwrap(c.get("looping")),
            isMidi: !!unwrap(c.get("is_midi_clip"))
        });
    }
    out.sort(function (a, b) { return a.start - b.start; });
    return out;
}

// Shared by arrangement_plan (read-only reply) and arrangement_execute
// (recomputed fresh immediately before writing -- "never apply a stale
// queue", plan §4). Returns {ok:false,...} on any guard failure -- safe to
// return directly as a handleLiveCall reply -- or a full internal plan
// object including live LiveAPI object references (song, sectionTrack)
// that only arrangement_execute uses. arrangement_plan strips those before
// replying, since object references can't cross the JSON reply boundary.
function computeArrangementPlan(params) {
    if (skeletonBusy()) {
        return { ok: false, message: "A locator pass is still running. Wait for it to finish." };
    }
    var song = liveApi("live_set");
    if (!song) return { ok: false, message: "Cannot access live_set." };
    var bar = songBarBeats();

    var sections = params.sections || [];
    var sectionTrackPath = String(params.sectionTrackPath || "");
    var remapAll = !!params.remapAllTracks;
    var isEditing = !!params.isEditing;
    var scanCount = Number(params.scanCount || 0);
    var tickedPaths = params.tickedTrackPaths || [];
    var beatsPerBar = Number(params.beatsPerBar || 0);

    if (!sectionTrackPath) return { ok: false, message: "No section track chosen." };
    var sectionTrack = liveApi(sectionTrackPath);
    if (!sectionTrack) return { ok: false, message: "Could not access the section track." };
    if (!unwrap(sectionTrack.get("has_midi_input"))) {
        return { ok: false, message: "The section track must be a MIDI track." };
    }

    // Concurrency/staleness guard: the dialog captured beatsPerBar from the
    // signature at open time (see _arrangement_helper_context in helper.py).
    // Live 12 Standard's LOM has no per-bar signature history to check
    // *within* the affected range directly, so this catches the practical
    // case -- the signature changed between dialog-open and Create-click --
    // rather than overclaiming a check the LOM can't perform.
    if (beatsPerBar > 0 && beatsPerBar !== bar) {
        return { ok: false, message: "Time signature changed since this dialog opened. Run again." };
    }

    // Remap set: ticked tracks (minus the section track), or every eligible
    // track when Whole Project is on. Group and frozen tracks are skipped
    // either way; return/master tracks are never reachable here since this
    // only walks "live_set tracks".
    var remapPaths = [];
    var seenRemap = {};
    var addRemap = function (p) {
        if (!p || p === sectionTrackPath || seenRemap[p]) return;
        var rTrack = liveApi(p);
        if (!rTrack) return;
        try { if (unwrap(rTrack.get("is_foldable"))) return; } catch (eFold) {}
        try { if (unwrap(rTrack.get("is_frozen"))) return; } catch (eFroz) {}
        seenRemap[p] = true;
        remapPaths.push(p);
    };
    if (remapAll) {
        var totalTracks = song.getcount("tracks");
        var rt;
        for (rt = 0; rt < totalTracks; rt++) addRemap("live_set tracks " + rt);
    } else {
        var pi;
        for (pi = 0; pi < tickedPaths.length; pi++) addRemap(String(tickedPaths[pi]));
    }

    // Old layout + concurrency guard against the section track itself
    // changing since the dialog opened.
    var oldLayout = readArrangementClips(sectionTrackPath);
    if (oldLayout.length !== scanCount) {
        return {
            ok: false,
            message: "Section track changed since the dialog opened (" + scanCount + " → " +
                oldLayout.length + " clips). Run again."
        };
    }
    var startPosition = (isEditing && oldLayout.length) ? oldLayout[0].start :
        Number(unwrap(song.get("current_song_time")) || 0);
    var arrangementOldEnd = startPosition;
    var oi;
    for (oi = 0; oi < oldLayout.length; oi++) {
        var oldEnd = oldLayout[oi].start + oldLayout[oi].duration;
        if (oldEnd > arrangementOldEnd) arrangementOldEnd = oldEnd;
    }

    // New layout + moveMap. Keep the old id only when it's a real,
    // not-yet-used index into oldLayout -- guards against drag-duplicated
    // ids trying to consume the same source twice.
    var newLayout = [];
    var usedOld = {};
    var cursor = startPosition;
    var ni;
    for (ni = 0; ni < sections.length; ni++) {
        var sec = sections[ni] || {};
        var secBars = Number(sec.bars) || 0;
        var secDuration = secBars * bar;
        var rawId = sec.id;
        var keepsOldId = (typeof rawId === "number" && rawId >= 0 &&
            rawId < oldLayout.length && !usedOld[rawId]);
        if (keepsOldId) usedOld[rawId] = true;
        newLayout.push({
            oldIndex: keepsOldId ? rawId : -1,
            name: String(sec.name || ""),
            color: Number(sec.color) || 0,
            start: cursor,
            duration: secDuration
        });
        cursor += secDuration;
    }
    var arrangementNewEnd = cursor;
    var clearEnd = Math.max(arrangementOldEnd, arrangementNewEnd);

    var moveMap = {};
    var mi;
    for (mi = 0; mi < newLayout.length; mi++) {
        if (newLayout[mi].oldIndex >= 0) moveMap[newLayout[mi].oldIndex] = newLayout[mi];
    }

    // Snapshot the moves per remap track -- ids only, nothing written.
    var queued = [];
    var dropped = 0, skipped = 0;
    var rti;
    for (rti = 0; rti < remapPaths.length; rti++) {
        var remapClips = readArrangementClips(remapPaths[rti]);
        var rci;
        for (rci = 0; rci < remapClips.length; rci++) {
            var rc = remapClips[rci];
            if (rc.start < startPosition || rc.start >= arrangementOldEnd) continue;
            var oldSection = null, oldSecIdx = -1, osi;
            for (osi = 0; osi < oldLayout.length; osi++) {
                var os = oldLayout[osi];
                if (rc.start >= os.start && rc.start < os.start + os.duration) {
                    oldSection = os;
                    oldSecIdx = osi;
                    break;
                }
            }
            if (!oldSection) { skipped++; continue; }
            var move = moveMap[oldSecIdx];
            var offset = rc.start - oldSection.start;
            if (!move || offset >= move.duration) { dropped++; continue; }
            var finalStart = move.start + offset;
            var clamped = Math.min(rc.duration, oldSection.duration - offset, move.duration - offset);
            if (!(clamped > 0)) { dropped++; continue; }
            queued.push({
                trackPath: remapPaths[rti],
                id: rc.id,
                origStart: rc.start,
                finalStart: finalStart,
                clamped: clamped,
                looping: rc.looping,
                overhangs: clamped < rc.duration
            });
        }
    }

    // Real counts. writeCount approximates park+delete+land+delete per
    // moved clip (primary, probe-passed path -- see plan §The collision
    // hole and the parking lane), plus section-track rebuild and locator
    // create/delete.
    var sectionCreates = newLayout.length;
    var sectionDeletes = oldLayout.length;
    var locatorOps = params.createLocators ? (sectionDeletes + sectionCreates) : 0;
    var moved = queued.length;
    var writeCount = (4 * moved) + sectionCreates + sectionDeletes + locatorOps;
    var unlooped = 0, qi;
    for (qi = 0; qi < queued.length; qi++) {
        if (queued[qi].overhangs) unlooped++;
    }

    // Safety cap on total write ops -- tunable during build, starting at
    // 80. Checked here (used by both arrangement_plan and
    // arrangement_execute, since both call this function) so a stale or
    // bypassed Python pre-confirm gate still can't reach a write phase with
    // an oversized job.
    var CAP = 80;
    if (writeCount > CAP) {
        return {
            ok: false,
            capped: true,
            message: "This run would take " + writeCount + " write operations, above the " +
                CAP + "-operation safety cap.",
            writeCount: writeCount,
            cap: CAP
        };
    }

    var fingerprintIds = [];
    for (qi = 0; qi < queued.length; qi++) fingerprintIds.push(queued[qi].id);

    return {
        ok: true,
        song: song,
        sectionTrack: sectionTrack,
        sectionTrackPath: sectionTrackPath,
        bar: bar,
        startPosition: startPosition,
        clearEnd: clearEnd,
        oldLayout: oldLayout,
        newLayout: newLayout,
        queued: queued,
        remapPaths: remapPaths,
        createLocators: !!params.createLocators,
        renameTrack: !!params.renameTrack,
        sectionCount: sectionCreates,
        remapTrackCount: remapPaths.length,
        moved: moved,
        dropped: dropped,
        skipped: skipped,
        unlooped: unlooped,
        writeCount: writeCount,
        undoStepCount: writeCount,
        fingerprint: { scanCount: oldLayout.length, clipIds: fingerprintIds }
    };
}

function firstEmptySlot(trackPath) {
    var track = liveApi(trackPath);
    if (!track) return null;
    var n = track.getcount("clip_slots");
    var i;
    for (i = 0; i < n; i++) {
        var slot = liveApi(trackPath + " clip_slots " + i);
        if (slot && !unwrap(slot.get("has_clip"))) return slot;
    }
    var song = liveApi("live_set");
    if (!song) return null;
    song.call("create_scene", -1);
    n = track.getcount("clip_slots");
    return liveApi(trackPath + " clip_slots " + (n - 1));
}

function writeNotes(clip, notes, replaceAll) {
    if (!clip) throw new Error("No clip");

    // ── Clear existing notes ────────────────────────────────────────────────────
    // Always use remove_notes_extended (Live 11+). The old select_all_notes /
    // replace_selected_notes / notes / done protocol triggers Live's MPE warning.
    if (replaceAll) {
        try {
            clip.call("remove_notes_extended", 0, 128, 0, 100000);
        } catch (e) {}
    }

    // ── Write new notes ─────────────────────────────────────────────────────────
    // Use Dict-based add_new_notes (Live 11+). Never fall back to the legacy
    // note / done protocol — that is what triggers the MPE/velocity-deviation
    // warning dialog shown to the user.
    var payload = { notes: [] };
    var i;
    for (i = 0; i < notes.length; i++) {
        var n = notes[i];
        var st  = Number(n.start_time != null ? n.start_time : (n.startTime != null ? n.startTime : 0));
        var dur = Number(n.duration  != null ? n.duration  : 0.25);
        var pit = Math.max(0, Math.min(127, Math.round(Number(n.pitch != null ? n.pitch : 60))));
        var vel = Math.max(1, Math.min(127, Math.round(Number(n.velocity != null ? n.velocity : 100))));
        var noteItem = {
            pitch:      pit,
            start_time: st,
            duration:   Math.max(0.01, dur),
            velocity:   vel,
            mute:       n.mute ? 1 : 0
        };
        if (n.probability != null) {
            noteItem.probability = Math.max(0, Math.min(1, Number(n.probability)));
        }
        if (n.velocity_deviation != null) {
            noteItem.velocity_deviation = Math.max(-127, Math.min(127, Number(n.velocity_deviation)));
        }
        payload.notes.push(noteItem);
    }
    var d = new Dict();
    d.parse(JSON.stringify(payload));
    clip.call("add_new_notes", d);
    d.freepeer();
}

function offsetNotes(notes, delta) {
    var out = [];
    var i;
    for (i = 0; i < notes.length; i++) {
        var n = notes[i];
        var item = {
            pitch: n.pitch,
            startTime: Number(n.startTime) + delta,
            duration: n.duration,
            velocity: n.velocity,
            mute: !!n.mute
        };
        if (n.probability != null) item.probability = n.probability;
        if (n.velocity_deviation != null) item.velocity_deviation = n.velocity_deviation;
        out.push(item);
    }
    return out;
}

function setClipName(clip, name) {
    try {
        clip.set("name", name);
    } catch (e) {}
}

function setClipLength(clip, lengthBeats) {
    try {
        clip.set("loop_end", lengthBeats);
        clip.set("end_marker", lengthBeats);
    } catch (e) {}
}

function clipLength(clip) {
    var end = Number(unwrap(clip.get("loop_end")));
    if (end > 0) return end;
    var len = Number(unwrap(clip.get("length")));
    return len > 0 ? len : 0;
}

function createSessionClip(trackPath, lengthBeats, name, notes) {
    var slot = firstEmptySlot(trackPath);
    if (!slot) throw new Error("No empty clip slot on " + trackPath);
    slot.call("create_clip", lengthBeats);
    var clip = liveApi(String(slot.unquotedpath || slot.path).replace(/^['"]|['"]$/g, "") + " clip");
    if (!clip) throw new Error("Created clip was not found");
    setClipLength(clip, lengthBeats);
    writeNotes(clip, notes, false);
    setClipName(clip, name);
    return clip;
}

function breakdownsNewClip(midi, notes, lengthBeats, name) {
    if (!midi.length) {
        return { ok: false, message: "Tick a MIDI track for New clip." };
    }
    var i;
    for (i = 0; i < midi.length; i++) {
        createSessionClip(midi[i].path, lengthBeats, name, notes);
    }
    return {
        ok: true,
        message: "New clip on " + midi.length + " MIDI track(s), " + notes.length + " notes."
    };
}

function breakdownsNewTrack(notes, lengthBeats, name) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, message: "Live API not ready." };
    var index = song.getcount("tracks");
    song.call("create_midi_track", -1);
    var path = "live_set tracks " + index;
    var track = liveApi(path);
    if (!track) return { ok: false, message: "Could not create a MIDI track." };
    try {
        track.set("name", name);
    } catch (e) {}
    createSessionClip(path, lengthBeats, name, notes);
    return { ok: true, message: "New MIDI track + clip, " + notes.length + " notes." };
}

function breakdownsReplace(midi, notes, lengthBeats, name) {
    var clip = detailMidiClip();
    if (!clip) return { ok: false, message: "Select a MIDI clip in Live to Replace." };
    var path = clipTrackPath(clip);
    if (midi.length && path && !trackAllowed(path, midi)) {
        return { ok: false, message: "The selected clip is not on a ticked MIDI track." };
    }
    setClipLength(clip, lengthBeats);
    writeNotes(clip, notes, true);
    setClipName(clip, name);
    return { ok: true, message: "Replaced selected clip, " + notes.length + " notes." };
}

function breakdownsAppend(midi, notes, lengthBeats, name) {
    var clip = detailMidiClip();
    if (!clip) return { ok: false, message: "Select a MIDI clip in Live to Append." };
    var path = clipTrackPath(clip);
    if (midi.length && path && !trackAllowed(path, midi)) {
        return { ok: false, message: "The selected clip is not on a ticked MIDI track." };
    }
    var start = clipLength(clip);
    if (!(start > 0)) start = 0;
    var shifted = offsetNotes(notes, start);
    writeNotes(clip, shifted, false);
    setClipLength(clip, start + lengthBeats);
    return { ok: true, message: "Appended " + notes.length + " notes to the selected clip." };
}

function breakdownsPlayhead(midi, notes, lengthBeats, name) {
    if (!midi.length) {
        return { ok: false, message: "Tick a MIDI track for At playhead." };
    }
    var song = liveApi("live_set");
    if (!song) return { ok: false, message: "Live API not ready." };
    var start = Number(unwrap(song.get("current_song_time")));
    if (!(start >= 0)) start = 0;
    var i;
    for (i = 0; i < midi.length; i++) {
        var track = liveApi(midi[i].path);
        if (!track) continue;
        var created = track.call("create_midi_clip", start, lengthBeats);
        var clip = liveApiId(extractId(created));
        if (!clip) {
            // Some Live builds return the clip as the last arrangement clip.
            var count = track.getcount("arrangement_clips");
            if (count > 0) clip = liveApi(midi[i].path + " arrangement_clips " + (count - 1));
        }
        if (!clip) throw new Error("Could not create an Arrangement clip on " + midi[i].path);
        setClipLength(clip, lengthBeats);
        writeNotes(clip, notes, false);
        setClipName(clip, name);
    }
    return {
        ok: true,
        message: "Arrangement clip at playhead on " + midi.length + " track(s), " + notes.length + " notes."
    };
}

// Live Actions tool jobs. Included by live-actions-bridge.js.
// Uses liveApi / unwrap / firstEmptySlot / writeNotes from the main file.

function mulberry32(seed) {
    var state = seed >>> 0;
    return function () {
        state = (state + 0x6d2b79f5) >>> 0;
        var t = state;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function deriveSeed(baseSeed, variationIndex) {
    return ((baseSeed >>> 0) ^ Math.imul(variationIndex >>> 0, 0x9e3779b9)) >>> 0;
}

function payloadFields(payload) {
    return payload && payload.fields ? payload.fields : {};
}

function payloadTracks(payload) {
    var tracks = (payload && payload.tracks) || [];
    var out = [];
    var i;
    for (i = 0; i < tracks.length; i++) {
        if (tracks[i] && tracks[i].path && liveApi(tracks[i].path)) out.push(tracks[i]);
    }
    return out;
}

function songBarBeats() {
    var song = liveApi("live_set");
    if (!song) return 4;
    var n = Number(unwrap(song.get("signature_numerator")));
    return n > 0 ? n : 4;
}

function slotHasClip(trackPath, slotIndex) {
    var slot = liveApi(trackPath + " clip_slots " + slotIndex);
    return !!(slot && unwrap(slot.get("has_clip")));
}

function slotClip(trackPath, slotIndex) {
    if (!slotHasClip(trackPath, slotIndex)) return null;
    return liveApi(trackPath + " clip_slots " + slotIndex + " clip");
}

function eachSessionClip(tracks, fn) {
    var t;
    var count = 0;
    for (t = 0; t < tracks.length; t++) {
        var track = liveApi(tracks[t].path);
        if (!track) continue;
        var n = track.getcount("clip_slots");
        var s;
        for (s = 0; s < n; s++) {
            var clip = slotClip(tracks[t].path, s);
            if (!clip) continue;
            fn(clip, tracks[t], s, liveApi(tracks[t].path + " clip_slots " + s));
            count += 1;
        }
    }
    return count;
}

function applyNamePattern(pattern, ctx) {
    var out = String(pattern || "{track} {bar} take");
    out = out.replace(/\{track\}/gi, ctx.track || "track");
    out = out.replace(/\{bar\}/gi, String(ctx.bar != null ? ctx.bar : 1));
    out = out.replace(/\{index\}/gi, String(ctx.index != null ? ctx.index : 1));
    out = out.replace(/\{take\}/gi, String(ctx.take != null ? ctx.take : ctx.index || 1));
    out = out.replace(/\{kind\}/gi, ctx.kind || "track");
    out = out.replace(/\{name\}/gi, ctx.name || ctx.track || "track");
    return out.replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "");
}

function runClipNamer(payload) {
    var tracks = payloadTracks(payload);
    if (!tracks.length) return { ok: false, message: "Tick at least one track." };
    var pattern = String(payloadFields(payload).pattern || "{track} {bar} take");
    var renamed = 0;
    var t;
    for (t = 0; t < tracks.length; t++) {
        var track = liveApi(tracks[t].path);
        if (!track) continue;
        var trackName = String(unwrap(track.get("name")) || tracks[t].name || "track");
        var n = track.getcount("clip_slots");
        var take = 0;
        var s;
        for (s = 0; s < n; s++) {
            var clip = slotClip(tracks[t].path, s);
            if (!clip) continue;
            take += 1;
            clip.set(
                "name",
                applyNamePattern(pattern, {
                    track: trackName,
                    name: trackName,
                    kind: tracks[t].kind || "track",
                    bar: s + 1,
                    index: take,
                    take: take
                })
            );
            renamed += 1;
        }
    }
    if (!renamed) return { ok: false, message: "No clips on the ticked tracks." };
    return { ok: true, message: "Renamed " + renamed + " clip(s)." };
}

var skeletonJob = null;
var skeletonTask = null;

// The three call sites below (arrangement_scan, computeArrangementPlan,
// arrangement_execute) all guard on "is a locator pass running" before they
// let a new one start. Checking skeletonJob alone can't tell a real
// in-flight pass from an orphaned one: skeletonTask should always be
// non-null whenever skeletonJob is (a fresh Task is scheduled synchronously
// right after every job object is built -- see runSkeleton and the
// arrangement_execute locator-reuse job below), so skeletonTask === null
// with skeletonJob still set means the job object was built but something
// threw before that Task got scheduled, orphaning it exactly the way
// skeletonTick's own deadline/try-catch guards against for the run loop
// itself. Age-gate it too as a second backstop in case that invariant is
// ever wrong in some path this doesn't anticipate. Either way, a stale job
// must never permanently block every future run behind "A locator pass is
// still running" with no recovery but a re-drop.
function skeletonBusy() {
    if (!skeletonJob) return false;
    if (skeletonTask) return true;
    var age = skeletonJob.startedAt ? Date.now() - skeletonJob.startedAt : Infinity;
    if (age > SKELETON_DEADLINE_MS) {
        skeletonJob = null;
        return false;
    }
    return true;
}

function parseSections(raw) {
    var parts = String(raw || "").split(",");
    var out = [];
    var i;
    for (i = 0; i < parts.length; i++) {
        var chunk = String(parts[i] || "").replace(/^\s+|\s+$/g, "");
        if (!chunk) continue;
        var match = chunk.match(/^(.*?)[\s:]+(\d+)\s*$/);
        if (!match) return { error: "Could not parse \"" + chunk + "\". Use Intro 8, Verse 16." };
        var name = String(match[1] || "").replace(/^\s+|\s+$/g, "");
        var bars = parseInt(match[2], 10);
        if (!name || !(bars > 0)) return { error: "Need a name and bar count in \"" + chunk + "\"." };
        out.push({ name: name, bars: bars });
    }
    return { sections: out };
}

function cancelSkeleton() {
    if (skeletonTask) {
        try { skeletonTask.cancel(); } catch (e) {}
        skeletonTask = null;
    }
}

function showArranger() {
    var view = liveApi("live_app view");
    if (!view) return;
    try { view.call("show_view", "Arranger"); } catch (e) {}
}

function stopTransport(song) {
    if (!song) return;
    try { song.set("is_playing", 0); } catch (e) {}
    try { song.call("stop_playing"); } catch (e) {}
}

function movePlayhead(song, beats) {
    if (!song) return false;
    try { song.set("start_time", beats); } catch (e) {}
    try { song.set("current_song_time", beats); } catch (e) {}
    var now = Number(unwrap(song.get("current_song_time")));
    if (isNaN(now) || Math.abs(now - beats) > 0.08) {
        try { song.call("jump_by", beats - (isNaN(now) ? 0 : now)); } catch (e) {}
        now = Number(unwrap(song.get("current_song_time")));
    }
    return !isNaN(now) && Math.abs(now - beats) <= 0.35;
}

// Live-probed 2026-08-22 against a real 8-section song-mapper run:
// returning the FIRST cue within eps (by cue_points' own time-sorted index
// order) rather than the CLOSEST one let a leftover cue point from an
// earlier, unrelated test -- sitting at nearly the same bar as a
// freshly-created one, since repeated preset bar lengths (8, 16...) land on
// the same round bar numbers run after run -- get matched and renamed
// instead of the cue this job actually just created. The new cue is always
// at-or-near the intended beat by construction (movePlayhead + immediate
// set_or_delete_cue), so "closest wins" reliably picks the right one even
// when a stale cue is also technically within eps.
function cueNear(beats, eps) {
    var song = liveApi("live_set");
    if (!song) return null;
    var n = song.getcount("cue_points");
    var best = null, bestDist = Infinity, i;
    for (i = 0; i < n; i++) {
        var cue = liveApi("live_set cue_points " + i);
        if (!cue) continue;
        var dist = Math.abs(Number(unwrap(cue.get("time"))) - beats);
        if (dist <= eps && dist < bestDist) {
            best = cue;
            bestDist = dist;
        }
    }
    return best;
}

// Live-probed 2026-08-23 (song-mapper Step 5, first real edit-mode
// run with a non-empty oldLayout): this used to return true unconditionally
// once a nearby cue was found, even though cue.set("name", ...) can silently
// throw right after set_or_delete_cue() creates that same cue in the same
// tick (a LiveAPI object isn't always fully settable the instant it's
// created). The caller trusted that false "success" and marked the item
// done, so skeletonTick's own pass-1/pass-2 retry never got a chance to fix
// it -- cues were left with Live's own default numeric name instead of the
// section name. Reading the name back and comparing catches that case so
// the retry mechanism that already exists actually runs.
function nameCueAt(beats, name) {
    var cue = cueNear(beats, 0.5);
    if (!cue) return false;
    try { cue.set("name", name); } catch (e) {}
    var actual = "";
    try { actual = String(unwrap(cue.get("name")) || ""); } catch (e2) {}
    return actual === name;
}

function finishSkeleton(ok, message) {
    cancelSkeleton();
    skeletonJob = null;
    sendChunked("/live-actions/result", ok ? "ok" : "error", message);
    setStatus(message);
}

// Wall-clock budget for one locator pass. If a stuck job (a LiveAPI throw on
// every retry -- e.g. the "Cannot access live_set" case logged in
// DEBUGGING TO DO LIST.md 2.5) never reaches a finishSkeleton() call, this
// is the backstop that fails it out loud instead of leaving skeletonJob set
// forever, which previously blocked every future run behind "A locator pass
// is still running" (the three guards on skeletonJob) with no way out short
// of re-dropping the device.
var SKELETON_DEADLINE_MS = 60000;

function skeletonTick() {
    var job = skeletonJob;
    if (!job) return;
    if (!job.startedAt) job.startedAt = Date.now();
    if (Date.now() - job.startedAt > SKELETON_DEADLINE_MS) {
        finishSkeleton(
            false,
            "Locator pass timed out after " + Math.round(SKELETON_DEADLINE_MS / 1000) + "s. " +
                "Nothing further was written this run."
        );
        return;
    }
    try {
        skeletonTickStep(job);
    } catch (e) {
        // An uncaught throw anywhere below used to abort the tick before its
        // own trailing "new Task(skeletonTick).schedule(...)" ran, so
        // nothing ever rescheduled and skeletonJob stayed non-null forever.
        // Fail this run loudly instead and clear the job so the next run
        // isn't refused because of it.
        finishSkeleton(false, "Locator pass failed: " + String(e));
    }
}

function skeletonTickStep(job) {
    var song = liveApi("live_set");
    if (!song) {
        finishSkeleton(false, "Live API not ready. Drop Live Actions on an audio track.");
        return;
    }

    // Delete stage (plan §5, additions for arrangement_execute's locator
    // reuse): removes old cue points before creating new ones. runSkeleton's
    // own jobs never set job.stage, so they fall straight through to the
    // create-stage logic below, unchanged and untouched by this addition.
    if (job.stage === "delete") {
        if (job.deleteIndex >= job.deletes.length) {
            job.stage = "create";
            job.index = 0;
            job.pass = 1;
            skeletonTask = new Task(skeletonTick);
            skeletonTask.schedule(20);
            return;
        }
        var delBeats = job.deletes[job.deleteIndex];
        // Live-probed 2026-08-22 (this stage's first real exercise, on an
        // edit-mode run): set_or_delete_cue() is a toggle keyed on whether a
        // cue exists AT THE EXACT CURRENT PLAYHEAD TIME, not "near" it --
        // moving to delBeats (our own recorded value, which can differ from
        // the cue's actual stored time by a float rounding hair) can miss
        // that exact match and CREATE a duplicate cue instead of deleting
        // the old one. Find the real cue first and move to ITS stored time,
        // so the toggle lands exactly on it.
        var delCue = cueNear(delBeats, 0.5);
        if (delCue) {
            var delTime = Number(unwrap(delCue.get("time")));
            if (isNaN(delTime)) delTime = delBeats;
            movePlayhead(song, delTime);
            if (cueNear(delTime, 0.02)) {
                try { song.call("set_or_delete_cue"); } catch (eDel) {}
            }
            // Live-probed 2026-08-23 (Step 5 follow-up): the create-stage
            // verifies success by reading the cue back (nameCueAt) and
            // retries across two full passes when it fails, because a
            // LiveAPI cue object isn't always immediately settable/toggleable
            // in the same tick it was touched. The delete stage had no
            // equivalent check -- it trusted set_or_delete_cue()
            // unconditionally and moved on. An unverified failed delete
            // leaves the stale old cue sitting exactly where a resize/reorder
            // edit shifts the next section's cue to land, which reproduces as
            // the stray/mislabeled-locator symptom seen live near a shifted
            // section boundary. Retry a bounded number of times before giving
            // up on this one and moving on, mirroring the create stage's own
            // eventual give-up rather than looping forever.
            if (cueNear(delTime, 0.1)) {
                job.deleteAttempts = (job.deleteAttempts || 0) + 1;
                if (job.deleteAttempts < 4) {
                    skeletonTask = new Task(skeletonTick);
                    skeletonTask.schedule(60);
                    return;
                }
            }
            job.deleteAttempts = 0;
        }
        job.deleteIndex += 1;
        skeletonTask = new Task(skeletonTick);
        skeletonTask.schedule(40);
        return;
    }

    if (job.index >= job.items.length) {
        if (job.made < job.items.length && job.pass === 1) {
            job.pass = 2;
            job.index = 0;
            try {
                song.set("current_song_time", job.items[0].beats);
                song.call("start_playing");
            } catch (e) {}
            skeletonTask = new Task(skeletonTick);
            skeletonTask.schedule(80);
            return;
        }
        stopTransport(song);
        try { song.set("current_song_time", job.prevTime); } catch (e) {}
        // job.doneMessage / job.prefix (plan §5): arrangement_execute names
        // its own section-creation summary and a distinct locator label;
        // runSkeleton's jobs leave both unset, so this reduces to the
        // original "Locators: N section(s)..." text exactly.
        var lead = job.doneMessage ? job.doneMessage + " " : "";
        if (!job.made && !job.items.length) {
            finishSkeleton(true, job.doneMessage || "Nothing to place.");
            return;
        }
        if (!job.made) {
            finishSkeleton(false, lead + "Live did not create locators. Stay in Arrangement view and run again.");
            return;
        }
        finishSkeleton(
            true,
            lead + (job.prefix || "Locators") + ": " + job.made + " section(s), last mark at bar " +
                (job.endBeats / job.bar + 1) + "."
        );
        return;
    }

    var item = job.items[job.index];
    if (item.done) {
        job.index += 1;
        skeletonTask = new Task(skeletonTick);
        skeletonTask.schedule(20);
        return;
    }

    if (nameCueAt(item.beats, item.name) && cueNear(item.beats, 0.5)) {
        item.done = true;
        job.made += 1;
        job.index += 1;
        skeletonTask = new Task(skeletonTick);
        skeletonTask.schedule(20);
        return;
    }

    movePlayhead(song, item.beats);
    if (job.pass === 2) {
        try { song.set("current_song_time", item.beats); } catch (e) {}
    }
    // Live-probed 2026-08-22 against a real Set (song-mapper Step 4):
    // gating this on is_cue_point_selected() -- Live's "is the transport
    // sitting on an existing cue" flag -- silently skips cue creation at
    // beat 0 specifically, even though no cue point actually exists there.
    // set_or_delete_cue() is a toggle (create if none exists at the current
    // position, delete if one does), so the real question is "does a cue
    // point actually exist here" -- cueNear already answers that directly
    // and correctly (it's what verifies success two lines down), so use it
    // for the gate too instead of trusting is_cue_point_selected's
    // apparently-unreliable-at-zero semantics.
    //
    // Live-probed 2026-08-23 (Step 5, first real edit-mode run with tightly
    // spaced sections): this used 0.08 beats here, tighter than the 0.35
    // beats movePlayhead itself accepts as "close enough" and the 0.5 beats
    // nameCueAt's own cueNear search uses. When a landing drifted between
    // 0.08 and 0.35 beats off target -- close enough for movePlayhead to
    // call it success, too far for this check to see it -- this gate
    // wrongly concluded "nothing here yet" on a retry pass and created a
    // second, duplicate cue right next to the first. Matching the 0.5-beat
    // radius used everywhere else this job asks "does this section already
    // have its cue" closes that gap; sections are realistically many beats
    // apart, so 0.5 beats can't bleed into a neighboring section's cue.
    if (!cueNear(item.beats, 0.5)) {
        try { song.call("set_or_delete_cue"); } catch (e) {}
    }
    if (nameCueAt(item.beats, item.name)) {
        item.done = true;
        job.made += 1;
    }
    job.index += 1;
    skeletonTask = new Task(skeletonTick);
    skeletonTask.schedule(job.pass === 2 ? 70 : 40);
}

function runSkeleton(payload) {
    var parsed = parseSections(payloadFields(payload).sections);
    if (parsed.error) return { ok: false, message: parsed.error };
    if (!parsed.sections.length) return { ok: false, message: "Add sections like Intro 8, Verse 16." };
    var song = liveApi("live_set");
    if (!song) return { ok: false, message: "Live API not ready. Drop Live Actions on an audio track." };

    cancelSkeleton();
    showArranger();
    stopTransport(song);

    var bar = songBarBeats();
    var beats = 0;
    var items = [];
    var i;
    for (i = 0; i < parsed.sections.length; i++) {
        items.push({
            name: parsed.sections[i].name,
            bars: parsed.sections[i].bars,
            beats: beats,
            done: false
        });
        beats += parsed.sections[i].bars * bar;
    }

    skeletonJob = {
        items: items,
        index: 0,
        made: 0,
        pass: 1,
        endBeats: beats,
        bar: bar,
        prevTime: Number(unwrap(song.get("current_song_time")))
    };
    setStatus("Placing locators…");
    skeletonTask = new Task(skeletonTick);
    skeletonTask.schedule(30);
    return { ok: true, pending: true, message: "Placing locators…" };
}

function copyNoteLocal(n) {
    return {
        pitch: n.pitch,
        startTime: n.startTime,
        duration: n.duration,
        velocity: n.velocity,
        probability: n.probability == null ? 1 : n.probability
    };
}

function mutateShuffle(indices, rng) {
    var i;
    for (i = indices.length - 1; i > 0; i--) {
        var j = Math.floor(rng() * (i + 1));
        var tmp = indices[i];
        indices[i] = indices[j];
        indices[j] = tmp;
    }
}

function mutateDrop(notes, amount, rng) {
    var frac = Math.max(0, Math.min(1, amount));
    var dropCount = Math.floor(frac * notes.length);
    if (dropCount <= 0) return notes.slice();
    if (dropCount >= notes.length) return [];
    var indices = notes.map(function (_, i) { return i; });
    mutateShuffle(indices, rng);
    var dropSet = {};
    var i;
    for (i = 0; i < dropCount; i++) dropSet[indices[i]] = true;
    return notes.filter(function (_, idx) { return !dropSet[idx]; });
}

function mutateSwap(notes, amount, rng) {
    var out = notes.map(copyNoteLocal);
    var pairCount = Math.floor(out.length / 2);
    var swapCount = Math.floor(Math.max(0, Math.min(1, amount)) * pairCount);
    if (swapCount <= 0) return out;
    var indices = out.map(function (_, i) { return i; });
    mutateShuffle(indices, rng);
    var i;
    for (i = 0; i < swapCount; i++) {
        var a = indices[i * 2];
        var b = indices[i * 2 + 1];
        var tmp = out[a].pitch;
        out[a].pitch = out[b].pitch;
        out[b].pitch = tmp;
    }
    return out;
}

function mutateVel(notes, range, rng) {
    return notes.map(function (n) {
        var next = copyNoteLocal(n);
        var vel = n.velocity == null ? 100 : n.velocity;
        next.velocity = Math.round(Math.max(1, Math.min(127, vel + (rng() * 2 - 1) * range)));
        return next;
    });
}

function mutateStart(notes, range, rng, bounds) {
    return notes.map(function (n) {
        var next = copyNoteLocal(n);
        next.startTime = Math.max(bounds.start, Math.min(bounds.end, n.startTime + (rng() * 2 - 1) * range));
        return next;
    });
}

function mutateOnceLocal(notes, fields, rng, bounds) {
    var next = mutateDrop(notes, Number(fields.drop || 0), rng);
    next = mutateSwap(next, Number(fields.swap || 0), rng);
    next = mutateStart(next, Number(fields.startRange || 0), rng, bounds);
    next = mutateVel(next, Number(fields.velRange || 0), rng);
    return next;
}

function readClipNotes(clip) {
    var raw = clip.call("get_notes_extended", 0, 128, 0, 100000);
    var parsed = null;
    if (typeof raw === "string") {
        try {
            parsed = JSON.parse(raw);
        } catch (e) {}
    } else if (raw && raw.notes) {
        parsed = raw;
    } else {
        try {
            raw = clip.call("get_all_notes_extended");
            if (typeof raw === "string") parsed = JSON.parse(raw);
            else if (raw && raw.notes) parsed = raw;
        } catch (e2) {}
    }
    if (!parsed || !parsed.notes) return [];
    return parsed.notes.map(function (n) {
        return {
            pitch: Number(n.pitch),
            startTime: Number(n.start_time != null ? n.start_time : n.startTime),
            duration: Number(n.duration),
            velocity: Number(n.velocity),
            probability: n.probability == null ? 1 : Number(n.probability),
            mute: !!n.mute
        };
    });
}

function clipBoundsLocal(notes) {
    if (!notes.length) return { start: 0, end: 4 };
    var start = Infinity;
    var end = 0;
    var i;
    for (i = 0; i < notes.length; i++) {
        if (notes[i].startTime < start) start = notes[i].startTime;
        var noteEnd = notes[i].startTime + notes[i].duration;
        if (noteEnd > end) end = noteEnd;
    }
    if (start === Infinity) start = 0;
    if (end <= start) end = start + 4;
    return { start: start, end: end };
}

function sourceMidiClip(payload) {
    var midi = midiTracksFromPayload(payload);
    var clip = detailMidiClip();
    if (clip) {
        var path = clipTrackPath(clip);
        if (!midi.length || !path || trackAllowed(path, midi)) return clip;
    }
    var t;
    for (t = 0; t < midi.length; t++) {
        var track = liveApi(midi[t].path);
        if (!track) continue;
        var n = track.getcount("clip_slots");
        var s;
        for (s = 0; s < n; s++) {
            var found = slotClip(midi[t].path, s);
            if (found && unwrap(found.get("is_midi_clip"))) return found;
        }
    }
    return null;
}

function runMutate(payload) {
    var midi = midiTracksFromPayload(payload);
    if (!midi.length) return { ok: false, message: "Tick a MIDI track." };
    var clip = sourceMidiClip(payload);
    if (!clip) return { ok: false, message: "Select a MIDI clip on a ticked track." };
    var notes = readClipNotes(clip);
    if (!notes.length) return { ok: false, message: "That clip has no notes." };
    var fields = payloadFields(payload);
    var count = Math.max(1, Math.min(16, parseInt(fields.count, 10) || 4));
    var seed = Math.max(1, parseInt(fields.seed, 10) || 1);
    var mode = String(fields.mode || "independent").toLowerCase();
    var bounds = clipBoundsLocal(notes);
    var length = Number(unwrap(clip.get("length")));
    if (!(length > 0)) length = Math.max(4, bounds.end);
    var baseName = String(unwrap(clip.get("name")) || "clip");
    var trackPath = clipTrackPath(clip) || midi[0].path;
    var written = 0;
    var current = notes.map(copyNoteLocal);
    var i;
    for (i = 0; i < count; i++) {
        var rng = mulberry32(deriveSeed(seed, i));
        var variant = mode.indexOf("cumul") === 0
            ? mutateOnceLocal(current, fields, rng, bounds)
            : mutateOnceLocal(notes, fields, rng, bounds);
        current = variant.map(copyNoteLocal);
        var slot = firstEmptySlot(trackPath);
        if (!slot) return { ok: false, message: "Wrote " + written + ". Need more empty clip slots." };
        slot.call("create_clip", Math.max(length, 0.25));
        var dest = liveApi(String(slot.unquotedpath || slot.path).replace(/^['"]|['"]$/g, "") + " clip");
        if (!dest) continue;
        setClipLength(dest, length);
        writeNotes(dest, variant, false);
        setClipName(dest, baseName + " var. " + (i + 1));
        written += 1;
    }
    return { ok: true, message: "Wrote " + written + " mutated clip(s) on " + trackPath + "." };
}

// ── Detect Key ───────────────────────────────────────────────────────────────
// Krumhansl-Schmuckler-style key finding: literature pitch-class weight
// profiles (Major/Minor) correlated against clip content, combined with
// structural (non-pitch-class) tonic evidence -- bass, downbeats, and
// cadence position -- to name both the parent diatonic collection and which
// of its 7 degrees is the tonic. Reimplemented from the published method,
// not translated from any third-party source (see
// docs/plans/v1.0.4-key-detection-two-pass.md and git history / App Changes
// Tracker for provenance, including the same-version design this replaced --
// see below).
//
// v1.0.4 replaces an earlier same-version attempt that reweighted a single
// pitch-class histogram (bass/downbeat/cadence/velocity) and correlated it
// against one rotated-major template per (root, family). That could not
// work: for the 5 non-Major/Minor families the template is built by
// rotating the major profile by the family's scale-degree offset, so every
// (root, family) pair sharing the same parent collection produces a
// BYTE-IDENTICAL template -- C Major, D Dorian, E Phrygian, F Lydian,
// G Mixolydian and B Locrian all reduce to the same 12 numbers. Pearson
// correlation is a pure function of its two vectors, so no amount of
// histogram reweighting can ever separate scores measured against an
// identical template. detectKeys() below fixes this structurally: the
// collection and the tonic are two different terms in one score, not one
// correlation asked to answer both questions.

// Tuned against tools/detect-key/test-detect-key.mjs, not derived from
// theory -- kept as named vars, not inlined, so they're easy to find and
// re-tune. W_FIT is the anchor and should not move; if a test case fails,
// retune the others first and record which case moved which constant in
// docs/plans/v1.0.4-key-detection-two-pass.md.
var W_FIT = 1.0;      // collection (note-set) fit -- separates different parent scales
var W_PROFILE = 0.6;  // empirical tonal-hierarchy fit at this candidate's tonic
var W_TONIC = 0.8;    // structural tonic salience (bass/downbeat/cadence, below)
var W_BASS = 0.8;     // salience: time-sampled lowest-sounding pitch
var W_LAST = 1.0;     // salience: final onset cluster (cadences resolve; trust them most)
var W_DOWN = 0.7;     // salience: duration weighted by downbeat/strongbeat position
var W_FIRST = 0.3;    // salience: opening onset cluster (pickups are weak evidence)
var MODE_PRIOR = {    // additive; breaks residual ties among equally-fit candidates
    Major: 0.10, Minor: 0.08, Mixolydian: 0.03, Dorian: 0.03,
    Lydian: 0, Phrygian: 0, Locrian: -0.25  // Locrian needs loud evidence, not a default
};
var DOWNBEAT_W = 3.0;      // note starts on the bar's downbeat
var STRONGBEAT_W = 2.0;    // note starts on beat 3 -- 4/4-only, see metricWeight()
var OFFBEAT_W = 0.5;       // note starts off the beat grid (syncopation)
var BASS_SAMPLE_STEP = 1.0;    // beats between bass samples
var BEAT_EPS = 0.03;       // float tolerance for onset/beat-position comparisons
var TIE_EPSILON = 0.03;    // raw-score gap below which the top two results "tie"

function keyProfiles() {
    return {
        "krumhansl-kessler": {
            major: [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
            minor: [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        },
        "temperley": {
            major: [5.0, 2.0, 3.5, 2.0, 4.5, 4.0, 2.0, 4.5, 2.0, 3.5, 1.5, 4.0],
            minor: [5.0, 2.0, 3.5, 4.5, 2.0, 4.0, 2.0, 4.5, 3.5, 2.0, 1.5, 4.0]
        }
    };
}

// out[i] = arr[(i + shift) mod 12]. Used to rotate a chromatic 12-value
// profile so a different pitch class (root) becomes the reference tonic.
function rotateArray(arr, shift) {
    var out = new Array(12);
    var s = ((shift % 12) + 12) % 12;
    var i;
    for (i = 0; i < 12; i++) {
        out[i] = arr[(i + s) % 12];
    }
    return out;
}

function pearsonCorr(x, y) {
    var n = x.length;
    var sumX = 0, sumY = 0;
    var i;
    for (i = 0; i < n; i++) {
        sumX += x[i];
        sumY += y[i];
    }
    var meanX = sumX / n;
    var meanY = sumY / n;
    var num = 0, denX = 0, denY = 0;
    for (i = 0; i < n; i++) {
        var dx = x[i] - meanX;
        var dy = y[i] - meanY;
        num += dx * dy;
        denX += dx * dx;
        denY += dy * dy;
    }
    var den = Math.sqrt(denX * denY);
    return den === 0 ? 0 : num / den;
}

// beatsPerBar: Live measures a note's startTime in quarter-note beats
// regardless of meter, so beats-per-bar is numerator * 4/denominator
// (4/4 -> 4, 3/4 -> 3, 6/8 -> 3, 7/8 -> 3.5) -- NOT the numerator alone.
// palParseDuration's n/N fix relies on the same underlying fact for note
// *values* (always 4/N); kept as a separate helper on purpose -- merging
// the two is how a meter bug like that one comes back.
function beatsPerBar(numerator, denominator) {
    var den = Number(denominator) || 4;
    var num = Number(numerator) || 4;
    return num * 4 / den;
}

// Weights a note by its own onset position only -- a whole note starting
// off-beat keeps the off-beat multiplier for its full duration, it does not
// earn credit for covering a later downbeat (the cheap rule; splitting a
// note's weight across the beats it spans is a different, larger feature).
// Assumes the clip's own beat 0 lands on a bar downbeat, true for how Live
// places MIDI clip content in practice -- a clip that itself starts mid-bar
// has its whole metric grid rotated by this approximation. STRONGBEAT_W
// (beat 3) is a 4/4-only special case, not general meter support.
function metricWeight(startTime, bpb) {
    var barPos = startTime % bpb;
    if (barPos < 0) barPos += bpb;
    if (barPos < BEAT_EPS || barPos > bpb - BEAT_EPS) return DOWNBEAT_W;
    if (bpb === 4 && Math.abs(barPos - 2) < BEAT_EPS) return STRONGBEAT_W;
    if (Math.abs(barPos - Math.round(barPos)) < BEAT_EPS) return 1;
    return OFFBEAT_W;
}

function addAnalysis(a, b) {
    function addArr(x, y) {
        var out = new Array(12);
        var i;
        for (i = 0; i < 12; i++) out[i] = (x[i] || 0) + (y[i] || 0);
        return out;
    }
    return {
        histogram: addArr(a.histogram, b.histogram),
        bass: addArr(a.bass, b.bass),
        down: addArr(a.down, b.down),
        first: addArr(a.first, b.first),
        last: addArr(a.last, b.last)
    };
}

// One clip's evidence, split into five separate 12-bin arrays rather than
// one merged histogram -- merging them is exactly what made v1.0.3's
// mode-disambiguation attempt structurally impossible (see the comment
// above this section). Each array answers a different question and feeds a
// different term in detectKeys():
//   histogram -- duration x velocity only. The note-set signal: which pitch
//     classes are present and how much. Feeds collection fit and profile
//     fit. Deliberately NOT metric- or boundary-weighted: a bass pedal or a
//     final chord must not be able to distort which *notes* are in play.
//   bass      -- time-sampled: +1 per beat-step where this pitch class is
//     the lowest sounding. What anchors the bass right now is a property of
//     a moment, not of one note in isolation, so it's sampled rather than
//     summed per-note (a walking bassline would otherwise dilute its own
//     target). clipEnd comes from the notes themselves, not Live's loop
//     length, so an empty tail can't invent a sample.
//   down      -- +duration for onsets that land on a bar downbeat or (4/4
//     only) beat 3; everything else contributes 0. Reuses metricWeight()'s
//     classification but only keeps the two "this is metrically strong"
//     cases -- general on/off-beat distinctions belong to rhythm, not tonic
//     salience.
//   first/last -- +1 per note in the clip's opening / closing onset cluster
//     (every note within BEAT_EPS of the min/max startTime, so a final
//     triad credits all three of its pitch classes, not just one).
// bpb (beats per bar) is a plain number, never read from Live here -- that's
// what lets the harness pass 4 / 3 / 3.5 directly and prove the denominator
// is actually used. Skips muted notes and notes with probability 0.
function analyzeClip(notes, bpb) {
    var histogram = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var bass = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var down = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var first = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var last = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var active = [];
    var i;
    for (i = 0; i < notes.length; i++) {
        var n = notes[i];
        if (n.mute) continue;
        if (n.probability === 0) continue;
        active.push(n);
    }
    if (!active.length) return { histogram: histogram, bass: bass, down: down, first: first, last: last };

    var minStart = Infinity, maxStart = -Infinity;
    for (i = 0; i < active.length; i++) {
        if (active[i].startTime < minStart) minStart = active[i].startTime;
        if (active[i].startTime > maxStart) maxStart = active[i].startTime;
    }

    for (i = 0; i < active.length; i++) {
        var note = active[i];
        var pc = ((Math.round(note.pitch) % 12) + 12) % 12;
        var dur = Math.max(0, Number(note.duration) || 0);
        var vel = Number(note.velocity);
        if (isNaN(vel)) vel = 100;
        vel = Math.max(0, Math.min(127, vel));
        var velFactor = 0.6 + 0.4 * (vel / 127);
        histogram[pc] += dur * velFactor;

        var metric = metricWeight(note.startTime, bpb);
        if (metric > 1) down[pc] += dur * metric;  // only downbeat/strongbeat count as evidence

        if (Math.abs(note.startTime - minStart) < BEAT_EPS) first[pc] += 1;
        if (Math.abs(note.startTime - maxStart) < BEAT_EPS) last[pc] += 1;
    }

    var clipEnd = 0;
    for (i = 0; i < active.length; i++) {
        var end = active[i].startTime + active[i].duration;
        if (end > clipEnd) clipEnd = end;
    }
    var t;
    for (t = 0; t < clipEnd; t += BASS_SAMPLE_STEP) {
        var lowest = null;
        for (i = 0; i < active.length; i++) {
            var nn = active[i];
            if (nn.startTime <= t && t < nn.startTime + nn.duration) {
                if (lowest === null || nn.pitch < lowest) lowest = nn.pitch;
            }
        }
        if (lowest !== null) {
            var bassPc = ((Math.round(lowest) % 12) + 12) % 12;
            bass[bassPc] += 1;
        }
    }

    return { histogram: histogram, bass: bass, down: down, first: first, last: last };
}

var MAJOR_SCALE_STEPS = [0, 2, 4, 5, 7, 9, 11];  // semitone offsets of a major scale's 7 degrees

// True diatonic-collection mask, not a K-S profile: 1 at each pitch class in
// the major scale rooted at parentRoot, 0 elsewhere. Mode-neutral by
// construction -- it can't prefer one tonic over another inside the same
// 7 notes, which is what makes it able to separate candidates a rotated
// K-S profile cannot (see detectKeys()).
function collectionMask(parentRoot) {
    var mask = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var i;
    for (i = 0; i < MAJOR_SCALE_STEPS.length; i++) {
        mask[(parentRoot + MAJOR_SCALE_STEPS[i]) % 12] = 1;
    }
    return mask;
}

// Sum-normalises a 12-bin accumulator to sum 1 (all-zero stays all-zero,
// rather than dividing by zero). Sum-, not max-, normalisation is
// deliberate: it preserves margin, so a pedal that owns 100% of the bass
// samples outranks a walking bass whose target owns only 30% of them.
function normalizeBins(arr) {
    var sum = 0, i;
    for (i = 0; i < 12; i++) sum += arr[i];
    var out = new Array(12);
    for (i = 0; i < 12; i++) out[i] = sum > 0 ? arr[i] / sum : 0;
    return out;
}

// 7 families x 12 roots, sorted best-first, top score normalised to 100%.
// Takes the 5-array analysis from analyzeClip (or several summed with
// addAnalysis for multi-clip scopes), not a single histogram -- see the
// comment above this section for why a single merged histogram/template
// pair cannot distinguish relative modes, which is the defect this scoring
// model fixes. Each candidate (root, family) is scored on four
// structurally different terms so no two candidates can be forced to tie:
//   collectionFit  -- pearsonCorr(histogram, collectionMask(parent)).
//     Mode-neutral: separates candidates whose 7-note collections differ
//     (e.g. C Major's collection vs D Major's), regardless of tonic.
//   profileFit     -- pearsonCorr(histogram, rotateArray(base, -root)),
//     base = the minor K-S profile for minor-3rd families (Dorian, Phrygian,
//     Minor, Locrian) or the major K-S profile for major-3rd families
//     (Major, Lydian, Mixolydian). This is what actually fixes the tie: D
//     Dorian now correlates against the minor profile rooted at D, not the
//     major profile rooted at C, so it's a genuinely different vector from
//     C Major. (Still degenerate *within* same-third, same-root families --
//     e.g. Dorian vs Phrygian at the same root -- but those differ in note
//     content, so collectionFit separates them instead.)
//   tonicSalience  -- structural evidence this root is home: a weighted mix
//     of sum-normalised bass/last/downbeat/first accumulators (see
//     analyzeClip), each contributing on its own scale so sampled-bass
//     counts and duration-beats are never added raw.
//   modePrior      -- small additive constant (MODE_PRIOR) that breaks the
//     residual tie when fit and salience are equal too (e.g. a bare
//     arpeggio that fits Major, Lydian and Mixolydian identically) --
//     Major/Minor win that by default, Locrian is pushed down hard since it
//     needs loud evidence, not a default.
// This is statistical scoring, not a guarantee -- sparse, rootless, or
// non-cadential material (e.g. a static pad with no clear bass or cadence)
// can still tie; runDetectKey reports that honestly instead of asserting a
// false-confident winner. Track/set scope additionally pools analyses
// across every clip on the track/Set (via addAnalysis), which answers "what
// does this collection lean toward," not "this is the one tonic" -- see the
// mixture note in runDetectKey's message and in APP-DETAILS.txt.
function detectKeys(analysis, profileId) {
    var profiles = keyProfiles();
    var table = profiles[profileId] || profiles["krumhansl-kessler"];
    var majorFlats = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];
    var minorMix = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
    // offset = semitone distance of this family's tonic from the parent
    // major scale's own tonic (e.g. Dorian's tonic is the parent major
    // scale's 2nd degree, so offset 2); third selects which K-S profile
    // shape approximates this family's tonal hierarchy for profileFit.
    var families = [
        { name: "Major", offset: 0, third: "major" },
        { name: "Minor", offset: 9, third: "minor" },
        { name: "Dorian", offset: 2, third: "minor" },
        { name: "Phrygian", offset: 4, third: "minor" },
        { name: "Lydian", offset: 5, third: "major" },
        { name: "Mixolydian", offset: 7, third: "major" },
        { name: "Locrian", offset: 11, third: "minor" }
    ];

    var bassN = normalizeBins(analysis.bass);
    var lastN = normalizeBins(analysis.last);
    var downN = normalizeBins(analysis.down);
    var firstN = normalizeBins(analysis.first);
    var salienceWeightSum = W_BASS + W_LAST + W_DOWN + W_FIRST;
    var salience = new Array(12);
    var p;
    for (p = 0; p < 12; p++) {
        salience[p] = (W_BASS * bassN[p] + W_LAST * lastN[p] + W_DOWN * downN[p] + W_FIRST * firstN[p]) / salienceWeightSum;
    }

    var results = [];
    var f, r;
    for (f = 0; f < families.length; f++) {
        var fam = families[f];
        var base = table[fam.third];
        var spelling = fam.name === "Minor" ? minorMix : majorFlats;
        for (r = 0; r < 12; r++) {
            var parent = ((r - fam.offset) % 12 + 12) % 12;
            var collectionFit = pearsonCorr(analysis.histogram, collectionMask(parent));
            var profileFit = pearsonCorr(analysis.histogram, rotateArray(base, -r));
            var prior = MODE_PRIOR[fam.name] || 0;
            var score = W_FIT * collectionFit + W_PROFILE * profileFit + W_TONIC * salience[r] + prior;
            results.push({
                root: spelling[r], family: fam.name, score: score,
                collection: majorFlats[parent], collectionFit: collectionFit,
                profileFit: profileFit, tonicSalience: salience[r]
            });
        }
    }
    results.sort(function (a, b) { return b.score - a.score; });
    var top = results.length ? results[0].score : 0;
    var i;
    for (i = 0; i < results.length; i++) {
        var pct = top > 0 ? Math.round((results[i].score / top) * 100) : 0;
        results[i].percent = Math.max(0, Math.min(100, pct));
    }
    return results;
}

// Analyzes and sums per clip (see the detectKeys comment for why): startTime
// is clip-relative, so flattening notes from multiple clips into one array
// before analysis would collide their timelines and lose per-clip onset
// context entirely. bpb is threaded down from runDetectKey.
function detectKeyTracksNotes(tracks, bpb) {
    var analysis = { histogram: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], bass: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], down: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], first: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], last: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] };
    var noteCount = 0;
    var clips = 0;
    var t;
    for (t = 0; t < tracks.length; t++) {
        var track = liveApi(tracks[t].path);
        if (!track) continue;
        var n = track.getcount("clip_slots");
        var s;
        for (s = 0; s < n; s++) {
            var clip = slotClip(tracks[t].path, s);
            if (!clip || !unwrap(clip.get("is_midi_clip"))) continue;
            var clipNotes = readClipNotes(clip);
            analysis = addAnalysis(analysis, analyzeClip(clipNotes, bpb));
            noteCount += clipNotes.length;
            clips += 1;
        }
    }
    return { analysis: analysis, noteCount: noteCount, clips: clips };
}

function detectKeyClipNotes(payload, bpb) {
    var clip = sourceMidiClip(payload);
    if (!clip) return { analysis: null, noteCount: 0, clips: 0, error: "Select a MIDI clip, or tick a MIDI track with a clip." };
    var notes = readClipNotes(clip);
    return { analysis: analyzeClip(notes, bpb), noteCount: notes.length, clips: 1 };
}

// Tools-tab path uses payload.tracks (ticked tracks); Genius has no ticked
// tracks, so it falls back to fields.track_index / track_indexes (comma or
// space separated) resolved straight to "live_set tracks N".
function detectKeyTrackNotes(payload, fields, bpb) {
    var midi = midiTracksFromPayload(payload);
    if (!midi.length) {
        var raw = fields.track_index != null ? fields.track_index : fields.track_indexes;
        var indexes = String(raw == null ? "" : raw).split(/[,\s]+/).filter(function (s) { return s !== ""; });
        var t;
        for (t = 0; t < indexes.length; t++) {
            var n = parseInt(indexes[t], 10);
            if (!isNaN(n)) midi.push({ path: "live_set tracks " + n, kind: "midi" });
        }
    }
    if (!midi.length) return { analysis: null, noteCount: 0, clips: 0, error: "Tick a MIDI track, or pass a track_index." };
    return detectKeyTracksNotes(midi, bpb);
}

function detectKeySetNotes(bpb) {
    var song = liveApi("live_set");
    if (!song) return { analysis: null, noteCount: 0, clips: 0, error: "Live API not ready." };
    var n = song.getcount("tracks");
    var midi = [];
    var i;
    for (i = 0; i < n; i++) {
        var path = "live_set tracks " + i;
        var track = liveApi(path);
        if (track && unwrap(track.get("has_midi_input"))) midi.push({ path: path });
    }
    if (!midi.length) return { analysis: null, noteCount: 0, clips: 0, error: "No MIDI tracks in the Set." };
    return detectKeyTracksNotes(midi, bpb);
}

// Result message is one flat OSC string with three sinks: the run-footer
// label truncates at 80 chars, the status ticker at 60, and only the
// collapsed-by-default console log drawer shows it whole (helper.py). The
// close call is the one piece of honesty in this message, so it goes right
// after the top pick, not appended at the end where a long clip's counts
// and mixture caveat would push it past the truncation point.
function runDetectKey(payload) {
    var fields = payloadFields(payload);
    var scope = String(fields.scope || "clip").toLowerCase();
    var profileId = String(fields.profile || "krumhansl-kessler").toLowerCase().indexOf("temp") === 0
        ? "temperley" : "krumhansl-kessler";
    var resultsCount = Math.max(1, Math.min(12, parseInt(fields.results, 10) || 3));

    var song = liveApi("live_set");
    var bpb = song
        ? beatsPerBar(unwrap(song.get("signature_numerator")), unwrap(song.get("signature_denominator")))
        : 4;

    var picked;
    if (scope.indexOf("track") === 0) {
        picked = detectKeyTrackNotes(payload, fields, bpb);
    } else if (scope.indexOf("set") === 0) {
        picked = detectKeySetNotes(bpb);
    } else {
        picked = detectKeyClipNotes(payload, bpb);
    }
    if (picked.error) return { ok: false, message: picked.error };
    if (!picked.noteCount) return { ok: false, message: "No notes found in that scope." };

    var ranked = detectKeys(picked.analysis, profileId);
    var closeCall = "";
    if (ranked.length > 1 && (ranked[0].score - ranked[1].score) < TIE_EPSILON) {
        closeCall = " (close: " + ranked[1].root + " " + ranked[1].family + ")";
    }
    var parts = ranked.slice(0, resultsCount).map(function (r, i) {
        var text = r.root + " " + r.family + " " + r.percent + "%";
        return i === 0 ? text + closeCall : text;
    });
    var message = parts.join(" · ") + " — " + picked.noteCount + " notes, " +
        picked.clips + " clip" + (picked.clips === 1 ? "" : "s");
    if (picked.clips > 1 && scope.indexOf("clip") !== 0) {
        message += ". Pooled across " + picked.clips + " clips — what this " +
            (scope.indexOf("set") === 0 ? "Set" : "track") + " leans toward, not one tonic.";
    }
    return { ok: true, message: message };
}

function runEmptyClips(payload) {
    var midi = midiTracksFromPayload(payload);
    if (!midi.length) return { ok: false, message: "Tick a MIDI track." };
    var length = Number(payloadFields(payload).length || 4);
    if (!(length > 0)) length = 4;
    var name = String(payloadFields(payload).name || "Empty");
    var made = 0;
    var i;
    for (i = 0; i < midi.length; i++) {
        var slot = firstEmptySlot(midi[i].path);
        if (!slot) continue;
        slot.call("create_clip", length);
        var clip = liveApi(String(slot.unquotedpath || slot.path).replace(/^['"]|['"]$/g, "") + " clip");
        if (clip) {
            setClipLength(clip, length);
            setClipName(clip, name);
            made += 1;
        }
    }
    if (!made) return { ok: false, message: "No empty slots on the ticked MIDI tracks." };
    return { ok: true, message: "Empty MIDI clip on " + made + " track(s)." };
}

function parseColorInt(raw) {
    var text = String(raw || "").replace(/^\s+|\s+$/g, "");
    if (!text) return null;
    if (text.charAt(0) === "#") text = text.substring(1);
    if (/^[0-9a-fA-F]{6}$/.test(text)) {
        return parseInt(text, 16);
    }
    var n = parseInt(text, 10);
    return isNaN(n) ? null : n;
}

function runColorClips(payload) {
    var tracks = payloadTracks(payload);
    if (!tracks.length) return { ok: false, message: "Tick at least one track." };
    var color = parseColorInt(payloadFields(payload).color);
    if (color === null) return { ok: false, message: "Use a color like #3b82f6." };
    var alsoScenes = String(payloadFields(payload).also_scenes || "").toLowerCase();
    alsoScenes = alsoScenes === "yes" || alsoScenes === "true" || alsoScenes === "1";
    var clips = 0;
    var scenes = {};
    eachSessionClip(tracks, function (clip, track, slotIndex) {
        try {
            clip.set("color", color);
            clips += 1;
        } catch (e) {}
        if (alsoScenes) scenes[slotIndex] = true;
    });
    var sceneCount = 0;
    var key;
    for (key in scenes) {
        if (!Object.prototype.hasOwnProperty.call(scenes, key)) continue;
        var scene = liveApi("live_set scenes " + key);
        if (!scene) continue;
        try {
            scene.set("color", color);
            sceneCount += 1;
        } catch (e2) {}
    }
    if (!clips) return { ok: false, message: "No clips on the ticked tracks." };
    var extra = sceneCount ? " and " + sceneCount + " scene(s)" : "";
    return { ok: true, message: "Colored " + clips + " clip(s)" + extra + "." };
}

function runDuplicateClips(payload) {
    var tracks = payloadTracks(payload);
    if (!tracks.length) return { ok: false, message: "Tick at least one track." };
    var copied = 0;
    var t;
    for (t = 0; t < tracks.length; t++) {
        var track = liveApi(tracks[t].path);
        if (!track) continue;
        var n = track.getcount("clip_slots");
        var sources = [];
        var s;
        for (s = 0; s < n; s++) {
            if (slotHasClip(tracks[t].path, s)) sources.push(s);
        }
        for (s = 0; s < sources.length; s++) {
            var dest = firstEmptySlot(tracks[t].path);
            if (!dest) break;
            var src = liveApi(tracks[t].path + " clip_slots " + sources[s]);
            try {
                src.call("duplicate_clip_to", "id", extractId(dest.id));
                if (unwrap(dest.get("has_clip"))) copied += 1;
            } catch (e) {}
        }
    }
    if (!copied) return { ok: false, message: "Nothing to duplicate, or no empty slots." };
    return { ok: true, message: "Duplicated " + copied + " clip(s) into empty slots." };
}

function sendIndexFromLetter(raw) {
    var text = String(raw || "A").replace(/^\s+|\s+$/g, "");
    if (!text) return 0;
    var letter = text.charAt(0).toUpperCase();
    if (letter >= "A" && letter <= "Z") return letter.charCodeAt(0) - 65;
    var n = parseInt(text, 10);
    return isNaN(n) ? 0 : n;
}

function runTrackBatch(payload) {
    var tracks = payloadTracks(payload);
    if (!tracks.length) return { ok: false, message: "Tick at least one track." };
    var fields = payloadFields(payload);
    var action = String(fields.action || "rename").toLowerCase().replace(/^\s+|\s+$/g, "");
    var done = 0;
    var i;
    for (i = 0; i < tracks.length; i++) {
        var track = liveApi(tracks[i].path);
        if (!track) continue;
        var kind = tracks[i].kind || "track";
        if (action === "rename") {
            var current = String(unwrap(track.get("name")) || tracks[i].name || "track");
            track.set(
                "name",
                applyNamePattern(fields.pattern || "{name}", {
                    name: current,
                    track: current,
                    kind: kind,
                    index: (tracks[i].index != null ? Number(tracks[i].index) : i) + 1,
                    bar: i + 1,
                    take: i + 1
                })
            );
            done += 1;
        } else if (action === "arm") {
            if (kind === "return" || kind === "master") continue;
            try {
                track.set("arm", 1);
                done += 1;
            } catch (e) {}
        } else if (action === "unarm") {
            if (kind === "return" || kind === "master") continue;
            try {
                track.set("arm", 0);
                done += 1;
            } catch (e2) {}
        } else if (action === "mute") {
            try {
                track.set("mute", 1);
                done += 1;
            } catch (e3) {}
        } else if (action === "unmute") {
            try {
                track.set("mute", 0);
                done += 1;
            } catch (e4) {}
        } else if (action === "send") {
            var idx = sendIndexFromLetter(fields.send || "A");
            var value = Number(fields.value);
            if (isNaN(value)) value = 0.5;
            if (value > 1 && value <= 100) value = value / 100;
            value = Math.max(0, Math.min(1, value));
            try {
                var send = liveApi(tracks[i].path + " mixer_device sends " + idx);
                if (send) {
                    send.set("value", value);
                    done += 1;
                }
            } catch (e5) {}
        } else {
            return { ok: false, message: "Action must be rename, arm, unarm, mute, unmute, or send." };
        }
    }
    if (!done) return { ok: false, message: "Nothing changed. Check the action and the ticked tracks." };
    return { ok: true, message: "Track " + action + ": " + done + " track(s)." };
}

function runRevealDevice(payload) {
    var tracks = payloadTracks(payload);
    if (!tracks.length) return { ok: false, message: "Tick the track that holds the device." };
    var needle = String(payloadFields(payload).name || "Chord Explorer").toLowerCase();
    var view = liveApi("live_set view");
    if (!view) return { ok: false, message: "Live API not ready." };
    var t;
    for (t = 0; t < tracks.length; t++) {
        var track = liveApi(tracks[t].path);
        if (!track) continue;
        var n = track.getcount("devices");
        var d;
        for (d = 0; d < n; d++) {
            var device = liveApi(tracks[t].path + " devices " + d);
            if (!device) continue;
            var name = String(unwrap(device.get("name")) || "").toLowerCase();
            if (name.indexOf(needle) === -1) continue;
            try {
                view.set("selected_track", "id", extractId(track.id));
            } catch (e) {}
            try {
                view.call("select_device", "id", extractId(device.id));
            } catch (e2) {}
            return { ok: true, message: "Selected " + unwrap(device.get("name")) + " on " + unwrap(track.get("name")) + "." };
        }
    }
    return { ok: false, message: "No device matching \"" + needle + "\" on the ticked tracks." };
}

// Creates one section-marker MIDI clip on the section track. Mirrors the
// created-clip resolution fallback already proven by
// Crops a clip's Arrangement footprint to `beats`.
// Live-probed 2026-08-20: looping must be OFF first --
// with looping=1, loop_end moves what plays but not the Arrangement block.
// Returns true if the clip had to be un-looped, so the caller can report it.
function trimArrangementClip(clip, beats) {
    var unlooped = false;
    var sm = Number(unwrap(clip.get("start_marker"))) || 0;
    try {
        if (unwrap(clip.get("looping"))) {
            clip.set("looping", 0);
            unlooped = true;
        }
        clip.set("loop_start", sm);
        clip.set("loop_end", sm + beats);
        clip.set("start_marker", sm);
        clip.set("end_marker", sm + beats);
    } catch (e) {}
    return unlooped;
}

// Phase 1 of the song-mapper move algorithm (plan "The collision
// hole and the parking lane"). Runs BEFORE the section track is touched --
// if parking fails hard, the section track is still untouched. Per remap
// track: duplicate every queued clip to a shared parking area past the end
// of that track's own material, spacing each by clamped+4 bars so parked
// copies never overlap each other, then delete the original immediately
// once its copy has landed. Uses duplicate_clip_to_arrangement with the
// "id " + id calling form ONLY -- Step 0 live-probed (2026-08-20) that the
// bare-int form silently no-ops (ok:true, value:0, no clip created) while
// "id " + id works and preserves every audio-fidelity field (warp_mode,
// markers, loop points, gain, pitch). Do not "simplify" this back to the
// bare form.
function parkQueuedClips(plan) {
    var byTrack = {}, order = [], i;
    for (i = 0; i < plan.queued.length; i++) {
        var q = plan.queued[i];
        if (!byTrack[q.trackPath]) { byTrack[q.trackPath] = []; order.push(q.trackPath); }
        byTrack[q.trackPath].push(q);
    }
    var parked = [], parkFailed = 0, parkBases = [];
    for (var ti = 0; ti < order.length; ti++) {
        var trackPath = order[ti];
        var remapTrack = liveApi(trackPath);
        if (!remapTrack) { parkFailed += byTrack[trackPath].length; continue; }
        var trackClips = readArrangementClips(trackPath);
        var lastEnd = plan.clearEnd;
        for (var tci = 0; tci < trackClips.length; tci++) {
            var tcEnd = trackClips[tci].start + trackClips[tci].duration;
            if (tcEnd > lastEnd) lastEnd = tcEnd;
        }
        var parkBase = lastEnd + (16 * plan.bar);
        parkBases.push({ trackPath: trackPath, parkBase: parkBase });
        var parkCursor = parkBase;
        var group = byTrack[trackPath];
        for (var gi = 0; gi < group.length; gi++) {
            var mv = group[gi];
            var srcClip = liveApiId(mv.id);
            if (!srcClip) { parkFailed++; parkCursor += mv.clamped + (4 * plan.bar); continue; }
            var parkedClip = null;
            try {
                var dupResult = remapTrack.call("duplicate_clip_to_arrangement", "id " + mv.id, parkCursor);
                parkedClip = liveApiId(extractId(dupResult));
            } catch (eDup) {}
            if (!parkedClip) {
                var pcnt = remapTrack.getcount("arrangement_clips");
                for (var pj = pcnt - 1; pj >= 0; pj--) {
                    var pcand = liveApi(trackPath + " arrangement_clips " + pj);
                    if (!pcand) continue;
                    var pcs = Number(unwrap(pcand.get("start_time")));
                    if (!isNaN(pcs) && Math.abs(pcs - parkCursor) < 1e-4) { parkedClip = pcand; break; }
                }
            }
            if (!parkedClip) { parkFailed++; parkCursor += mv.clamped + (4 * plan.bar); continue; }
            // Copy landed -- safe to delete the original now.
            try { remapTrack.call("delete_clip", srcClip); } catch (eDelSrc) {}
            parked.push({
                trackPath: trackPath,
                parkedId: String(parkedClip.id),
                finalStart: mv.finalStart,
                clamped: mv.clamped,
                origStart: mv.origStart
            });
            parkCursor += mv.clamped + (4 * plan.bar);
        }
    }
    return { parked: parked, parkFailed: parkFailed, parkBases: parkBases };
}

// Phase 3 of the move algorithm -- land each parked copy at its real
// destination (plan §4 step 5, Decision E). Runs AFTER Phase 2 has
// rebuilt the section track, so landed material never collides with the
// freshly created section clips. A clip that already fits its new section
// lands untouched, looping intact; only a genuine overhang gets un-looped
// and cropped via trimArrangementClip. A landing failure attempts a
// best-effort restore to origStart and is counted as failed, per plan §6.
function landParkedClips(parked, plan) {
    var landed = 0, landFailed = 0, unlooped = 0, i;
    for (i = 0; i < parked.length; i++) {
        var pk = parked[i];
        var remapTrack = liveApi(pk.trackPath);
        var parkedClipObj = liveApiId(pk.parkedId);
        if (!remapTrack || !parkedClipObj) { landFailed++; continue; }
        var parkedSpan = arrangementClipSpan(parkedClipObj);
        var fits = pk.clamped >= parkedSpan.span - 0.01;
        var landedClip = null;
        try {
            var landResult = remapTrack.call("duplicate_clip_to_arrangement", "id " + pk.parkedId, pk.finalStart);
            landedClip = liveApiId(extractId(landResult));
        } catch (eLand) {}
        if (!landedClip) {
            var lcnt = remapTrack.getcount("arrangement_clips");
            for (var lj = lcnt - 1; lj >= 0; lj--) {
                var lcand = liveApi(pk.trackPath + " arrangement_clips " + lj);
                if (!lcand) continue;
                var lcs = Number(unwrap(lcand.get("start_time")));
                if (!isNaN(lcs) && Math.abs(lcs - pk.finalStart) < 1e-4) { landedClip = lcand; break; }
            }
        }
        if (!landedClip) {
            // Best-effort restore -- the parked copy is the only surviving
            // material, so put a copy of it back where the original was.
            try { remapTrack.call("duplicate_clip_to_arrangement", "id " + pk.parkedId, pk.origStart); } catch (eRestore) {}
            try { remapTrack.call("delete_clip", parkedClipObj); } catch (eDelPark) {}
            landFailed++;
            continue;
        }
        if (!fits) {
            // Verify against arrangementClipSpan afterward rather than
            // trusting the set calls silently (plan §4 step 5).
            if (trimArrangementClip(landedClip, pk.clamped)) unlooped++;
        }
        try { remapTrack.call("delete_clip", parkedClipObj); } catch (eDelPark2) {}
        landed++;
    }
    return { landed: landed, landFailed: landFailed, unlooped: unlooped };
}

// breakdownsPlayhead: resolve via liveApiId(extractId(...)) first, fall
// back to matching by start_time if the return value doesn't resolve
// directly (match by position, not "last index",
// since creation order need not match final arrangement order).
function createArrangementSectionClip(track, trackPath, section) {
    var created;
    try {
        created = track.call("create_midi_clip", section.start, section.duration);
    } catch (eCreate) {
        return null;
    }
    var clip = liveApiId(extractId(created));
    if (!clip) {
        var cnt = track.getcount("arrangement_clips");
        var j;
        for (j = cnt - 1; j >= 0; j--) {
            var candidate = liveApi(trackPath + " arrangement_clips " + j);
            if (!candidate) continue;
            var cs = Number(unwrap(candidate.get("start_time")));
            if (!isNaN(cs) && Math.abs(cs - section.start) < 1e-4) { clip = candidate; break; }
        }
    }
    if (!clip) return null;
    try { clip.set("name", section.name); } catch (eName) {}
    try { clip.set("color", section.color); } catch (eColor) {}
    // create_midi_clip's own length isn't guaranteed to match exactly --
    // verify against arrangementClipSpan and crop via the unlooped path if
    // it doesn't (the only mechanism proven to resize an Arrangement clip's
    // footprint -- see trimArrangementClip's own comment, plan §4 step 5).
    var span = arrangementClipSpan(clip);
    if (Math.abs(span.span - section.duration) > 0.01) {
        try {
            if (unwrap(clip.get("looping"))) clip.set("looping", 0);
            clip.set("loop_start", 0);
            clip.set("loop_end", section.duration);
            clip.set("start_marker", 0);
            clip.set("end_marker", section.duration);
        } catch (eTrim) {}
    }
    return clip;
}

function runArrangementHelper(payload) {
    // Step 5 of the song-mapper plan: the parking-lane move
    // algorithm ("The collision hole and the parking lane" + §4 Phase
    // 1/3), on top of Step 4's create-mode rebuild. Fingerprint-gated
    // against a freshly recomputed plan, then writes. Ordering matters --
    // Phase 1 (park+delete existing clips on remap tracks) runs BEFORE
    // Phase 2 (rebuild the section track) so a hard parking failure
    // leaves the section track untouched; Phase 3 (land parked copies)
    // runs AFTER Phase 2 so landed material never collides with the
    // freshly created section clips.
    if (skeletonBusy()) {
        return { ok: false, message: "A locator pass is still running. Wait for it to finish." };
    }
    var fields = payloadFields(payload);
    var expected = fields.fingerprint || {};
    var plan = computeArrangementPlan(fields);
    if (!plan.ok) return plan;

    // Fingerprint check, first thing, before any write -- never apply a
    // stale queue (plan §4 "arrangement_execute" step 1).
    var expectedIds = (expected.clipIds || []).slice().sort();
    var actualIds = plan.fingerprint.clipIds.slice().sort();
    var scanMismatch = Number(expected.scanCount) !== plan.fingerprint.scanCount;
    var idsMismatch = expectedIds.length !== actualIds.length ||
        expectedIds.join(",") !== actualIds.join(",");
    if (scanMismatch || idsMismatch) {
        return { ok: false, message: "Set changed since the plan was computed. Run again." };
    }

    showArranger();
    stopTransport(plan.song);

    var t0 = Date.now();

    // Phase 1 -- park and delete existing clips on remap tracks. Always
    // an empty no-op in create mode (plan.queued is empty against an
    // empty section track), genuinely exercised in edit mode.
    var parkResult = parkQueuedClips(plan);

    // Phase 2 -- rebuild the section track.
    clearArrangementRange(plan.sectionTrack, plan.sectionTrackPath, plan.startPosition, plan.clearEnd);
    var created = 0, sectionFailed = 0, i;
    for (i = 0; i < plan.newLayout.length; i++) {
        var clip = createArrangementSectionClip(plan.sectionTrack, plan.sectionTrackPath, plan.newLayout[i]);
        if (clip) created++; else sectionFailed++;
    }

    if (plan.renameTrack) {
        try { plan.sectionTrack.set("name", "Arrangement"); } catch (eRename) {}
    }

    // Phase 3 -- land parked copies at their real destination.
    var landResult = landParkedClips(parkResult.parked, plan);
    var totalFailed = parkResult.parkFailed + landResult.landFailed + sectionFailed;
    var elapsed = Date.now() - t0;

    var msg = "Arrangement: " + created + " section(s) created, " +
        landResult.landed + " moved" +
        (plan.dropped ? ", " + plan.dropped + " dropped" : "") +
        (plan.skipped ? ", " + plan.skipped + " left in place" : "") +
        (landResult.unlooped ? ", " + landResult.unlooped + " un-looped to fit" : "") +
        (totalFailed ? ", " + totalFailed + " failed" : "") +
        " (" + elapsed + "ms).";

    // Named failure mode (plan §6): a crash between parking and landing
    // leaves parked copies past the song end, near parkBase, not
    // auto-restored -- name it so leftovers are findable.
    if (totalFailed && parkResult.parkBases.length) {
        var parkBarList = [];
        for (i = 0; i < parkResult.parkBases.length; i++) {
            parkBarList.push(Math.floor(parkResult.parkBases[i].parkBase / plan.bar) + 1);
        }
        msg += " Check for leftover material near bar " + parkBarList.join(", ") + ".";
    }

    if (!plan.createLocators || !plan.newLayout.length) {
        return { ok: true, message: msg };
    }

    // Locators -- reuse the existing skeletonJob/skeletonTick engine (§5),
    // generalized with a delete stage that clears old cues (from
    // plan.oldLayout -- non-empty once Step 3b's arrangement_scan seeds a
    // real edit-mode session) before creating new ones at the new layout.
    var items = [];
    for (i = 0; i < plan.newLayout.length; i++) {
        items.push({ name: plan.newLayout[i].name, beats: plan.newLayout[i].start, done: false });
    }
    var deletes = [];
    for (i = 0; i < plan.oldLayout.length; i++) deletes.push(plan.oldLayout[i].start);

    skeletonJob = {
        stage: deletes.length ? "delete" : "create",
        deletes: deletes,
        deleteIndex: 0,
        items: items,
        index: 0,
        made: 0,
        pass: 1,
        endBeats: items[items.length - 1].beats,
        bar: plan.bar,
        prefix: "Arrangement locators",
        doneMessage: msg,
        prevTime: Number(unwrap(plan.song.get("current_song_time")))
    };
    setStatus("Placing section locators…");
    skeletonTask = new Task(skeletonTick);
    skeletonTask.schedule(30);
    return { ok: true, pending: true, message: "Creating sections, then placing locators…" };
}

include("live-actions-pal.js");

