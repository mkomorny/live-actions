// Pal-parity Live Object Model actions for Live Actions Genius.
// Mirrors official Producer Pal ppal-* jobs using this device's LiveAPI.
// Included by live-actions-bridge.js. Do not construct LiveAPI in loadbang.

// 0-based internal index -> the 1-based number Live's own UI shows (S1.1,
// v1.0.32). For human-readable message/error text only -- never for a LOM
// path segment, which stays 0-based. Passes non-numbers through unchanged
// so it's safe to wrap a value that might occasionally be a name/letter.
function palLiveNum(i) {
    return (typeof i === "number" && !isNaN(i) && i >= 0) ? (i + 1) : i;
}

// Extracts the trailing numeric id token from a Max .call() return value in
// any of its observed shapes -- ["id", N], the doubled ["id", "id", N], the
// bare string "id N", or a bare number/numeric string N -- or null if none
// can be found. A literal id of 0 is a valid token, not "missing" (S1.3.3).
function palParseEnvelopeIdToken(ret) {
    var idToken = null;
    if (ret instanceof Array) {
        idToken = ret.length ? ret[ret.length - 1] : null;
    } else if (typeof ret === "string") {
        var parts = ret.replace(/^\s+|\s+$/g, "").split(/\s+/);
        idToken = parts.length ? parts[parts.length - 1] : null;
    } else if (ret !== null && ret !== undefined) {
        idToken = ret;
    }
    if (idToken === null || idToken === undefined || idToken === "" || isNaN(Number(idToken))) return null;
    return idToken;
}

function palHandle(action, params) {
    params = params || {};
    var name = String(action || "");

    if (name === "connect") return palConnect();
    if (name === "read_set") return palReadSet(params);
    if (name === "update_set" || name === "update_live_set" || name === "set_tempo") {
        return palUpdateSet(params);
    }
    if (name === "read_track") return palReadTrack(params);
    if (name === "update_track") return palUpdateTrack(params);
    if (name === "create_track") return palCreateTrack(params);
    if (name === "read_scene") return palReadScene(params);
    if (name === "update_scene") return palUpdateScene(params);
    if (name === "create_scene") return palCreateScene(params);
    if (name === "read_clip" || name === "read_clip_notes") return palReadClip(params);
    if (name === "update_clip") return palUpdateClip(params);
    if (name === "create_clip") return palCreateClip(params);
    if (name === "remove_notes" || name === "remove_notes_from_clip") return palRemoveNotes(params);
    if (name === "read_device") return palReadDevice(params);
    if (name === "update_device") return palUpdateDevice(params);
    if (name === "read_macros" || name === "get_macros") return palReadMacros(params);
    if (name === "update_macro" || name === "set_macro") return palUpdateMacro(params);
    if (name === "read_meter" || name === "get_meter" || name === "get_track_meter" || name === "get_master_meter") {
        return palReadMeter(params);
    }
    if (name === "create_device" || name === "load_device" || name === "load_drum_rack" || name === "list_devices") {
        return palCreateDevice(params, name);
    }
    if (name === "delete") return palDelete(params);
    if (name === "duplicate") return palDuplicate(params);
    if (name === "duplicate_to_arrangement") return palDuplicateToArrangement(params);
    if (name === "read_arrangement_clips" || name === "get_arrangement_clips") return palReadArrangementClips(params);
    if (name === "update_arrangement_clip" || name === "set_arrangement_clip_name") return palUpdateArrangementClip(params);
    if (name === "capture_midi") return palCaptureMidi();
    if (name === "back_to_arranger") return palBackToArranger();
    if (name === "re_enable_automation") return palReEnableAutomation();
    if (name === "crossfader" || name === "set_crossfader" || name === "set_crossfade_assign") return palCrossfader(params);
    if (name === "create_take_lane") return palCreateTakeLane(params);
    if (name === "fold_state" || name === "set_fold_state" || name === "get_group_info") return palFoldState(params);
    if (name === "groove_pool" || name === "get_grooves" || name === "set_clip_groove") return palGroovePool(params);
    if (name === "duplicate_loop") return palDuplicateLoop(params);
    if (name === "undo") return palUndo();
    if (name === "redo") return palRedo();
    if (name === "jump_to_time" || name === "set_playhead") return palJumpToTime(params);
    if (name === "set_overdub" || name === "overdub") return palSetOverdub(params);
    if (name === "read_arrangement_length" || name === "get_arrangement_length") return palReadArrangementLength();
    if (name === "move_arrangement_clip") return palMoveArrangementClip(params);
    if (name === "read_arrangement_notes" || name === "get_arrangement_clip_notes") return palReadArrangementNotes(params);
    if (name === "write_arrangement_notes" || name === "set_arrangement_clip_notes" || name === "add_notes_to_arrangement_clip") return palWriteArrangementNotes(params);
    if (name === "remove_arrangement_notes" || name === "remove_arrangement_clip_notes") return palRemoveArrangementNotes(params);
    if (name === "read_take_lanes" || name === "get_take_lanes") return palReadTakeLanes(params);
    if (name === "update_take_lane" || name === "set_take_lane_name") return palUpdateTakeLane(params);
    if (name === "create_take_lane_clip" || name === "create_take_lane_midi_clip") return palCreateTakeLaneClip(params);
    if (name === "batch_tracks" || name === "unarm_all" || name === "unmute_all" || name === "unsolo_all" || name === "solo_exclusive") {
        return palBatchTracks(params, name);
    }
    if (name === "stop_all_clips") return palStopAllClips();
    if (name === "tap_tempo") return palTapTempo();
    if (name === "continue_playing") return palContinuePlaying();
    if (name === "scrub" || name === "scrub_by") return palScrub(params);
    if (name === "jump_cue" || name === "jump_to_next_cue" || name === "jump_to_prev_cue") return palJumpCue(params);
    if (name === "set_punch" || name === "punch") return palSetPunch(params);
    if (name === "set_cue_volume" || name === "cue_volume") return palSetCueVolume(params);
    if (name === "move_device") return palMoveDevice(params);
    if (name === "read_drum_pads" || name === "get_drum_rack_pads") return palReadDrumPads(params);
    if (name === "update_drum_pad" || name === "set_drum_rack_pad") return palUpdateDrumPad(params);
    if (name === "focus_view" || name === "view_state") return palFocusView(params);
    if (name === "read_link_status" || name === "link_status") return palReadLinkStatus();
    if (name === "inspect_plugin" || name === "device_inspect_plugin") return palInspectPlugin(params);
    if (name === "session_snapshot") return palSessionSnapshot(params);
    if (name === "map_rack_magnitude" || name === "magnitude_map") return palMapRackMagnitude(params);
    if (name === "get_selected" || name === "read_selected") return palGetSelected();
    if (name === "clear_clip_envelopes" || name === "clear_all_envelopes") return palClearClipEnvelopes(params);
    if (name === "set_clip_follow_action") return palSetClipFollowAction(params);
    if (name === "get_clip_follow_action") return palGetClipFollowAction(params);
    if (name === "set_clip_launch_mode") return palSetClipLaunchMode(params);
    if (name === "set_clip_fades") return palSetClipFades(params);
    if (name === "set_clip_markers") return palSetClipMarkers(params);
    if (name === "manage_warp_markers" || name === "warp_markers") return palManageWarpMarkers(params);
    if (name === "set_clip_automation") return palSetClipAutomation(params);
    if (name === "get_clip_automation") return palGetClipAutomation(params);
    if (name === "commit_groove") return palCommitGroove(params);
    if (name === "select") return palSelect(params);
    if (name === "playback") return palPlayback(params);
    if (name === "record_to_arrangement") return palRecordToArrangement(params);
    if (name === "library") return palLibrary(params);
    if (name === "live_api" || name === "api") return palLiveApi(params);
    // v1.0.39 -- verified against the Live 12.3.6 LOM truth table (app/lom_surface.json)
    if (name === "set_loop_region") return palSetLoopRegion(params);
    if (name === "set_groove_amount") return palSetGrooveAmount(params);
    if (name === "nudge") return palNudge(params);
    if (name === "set_swing") return palSetSwing(params);
    if (name === "set_appointed_device") return palSetAppointedDevice(params);
    if (name === "set_automation_record") return palSetAutomationRecord(params);
    if (name === "read_param_range") return palReadParamRange(params);
    if (name === "set_param_raw") return palSetParamRaw(params);
    if (name === "show_message") return palShowMessage(params);
    if (name === "read_dialog") return palReadDialog(params);
    if (name === "read_cpu") return palReadCpu();
    if (name === "view_control") return palViewControl(params);
    if (name === "read_selected_notes") return palReadSelectedNotes(params);
    return null;
}

// ── v1.0.39: new actions verified present + settable in the Live 12.3.6 LOM
// truth table (app/lom_surface.json / test_lom_surface.py) before being
// written, per docs/plans/v1.0.39-lom-truth-table-and-verified-actions.md.

function palSetLoopRegion(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready. Drop Live Actions Bridge on an audio track." };
    var changes = [];
    var notApplied = [];
    // Bounds before enable: setting them first means, if "loop"'s own
    // read-back happens to work, it's checked against the already-correct
    // region rather than a stale one about to change underneath it.
    if (params.loop_start != null) {
        var ls = Number(params.loop_start);
        if (palSetChecked(song, "loop_start", ls)) changes.push("loop_start=" + ls);
        else notApplied.push("loop_start");
    }
    if (params.loop_length != null) {
        var ll = Number(params.loop_length);
        if (palSetChecked(song, "loop_length", ll)) changes.push("loop_length=" + ll);
        else notApplied.push("loop_length");
    }
    // Song.loop's own .get() has been observed (live-verified, v1.0.39
    // verification pass) to read back the value from BEFORE a same-tick
    // .set() -- the same lag confirmed on Song.session_automation_record.
    // Trust the set() rather than gating ok on a read-back this property
    // can spuriously fail even when the write itself did take.
    if (params.enabled != null || params.loop != null) {
        var en = (params.enabled != null ? params.enabled : params.loop) ? 1 : 0;
        try { song.set("loop", en); changes.push("loop=" + (en ? "on" : "off") + " (unverified -- this property's own read-back lags the write by a tick)"); }
        catch (eLoop) { notApplied.push("enabled"); }
    }
    if (!changes.length && !notApplied.length) {
        return { ok: false, error: "Provide loop_start, loop_length, and/or enabled" };
    }
    var result = { ok: notApplied.length === 0, message: changes.length ? ("Set " + changes.join(", ")) : "No changes applied" };
    if (notApplied.length) result.not_applied = notApplied;
    return result;
}

function palSetGrooveAmount(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    if (params.amount == null) return { ok: false, error: "Provide amount (0.0-1.0)" };
    var amt = Math.max(0, Math.min(1, Number(params.amount)));
    if (!palSetChecked(song, "groove_amount", amt)) return { ok: false, error: "groove_amount did not take " + amt };
    return { ok: true, message: "Set global groove amount to " + amt };
}

// Song.nudge_up/nudge_down are momentary (Live pulses the transport nudge on
// the set, not a state you can read back) -- there is nothing to verify
// after the write, unlike palSetChecked's read-after-write pattern elsewhere.
function palNudge(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var dir = String((params && params.direction) || "").toLowerCase();
    if (dir !== "up" && dir !== "down") return { ok: false, error: "direction must be 'up' or 'down'" };
    var prop = dir === "up" ? "nudge_up" : "nudge_down";
    try {
        song.set(prop, 1);
        song.set(prop, 0);
    } catch (e) {
        return { ok: false, error: "nudge " + dir + " failed: " + String(e) };
    }
    return { ok: true, message: "Nudged " + dir };
}

function palSetSwing(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    if (params.amount == null) return { ok: false, error: "Provide amount (0.0-1.0)" };
    var amt = Math.max(0, Math.min(1, Number(params.amount)));
    if (!palSetChecked(song, "swing_amount", amt)) return { ok: false, error: "swing_amount did not take " + amt };
    return { ok: true, message: "Set global swing amount to " + amt };
}

function palSetAppointedDevice(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path or track_index + device_index" };
    if (loc.trackResolvedBy === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.trackName + "'" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found" };
    try { song.set("appointed_device", "id", extractId(device.id)); } catch (e) {
        return { ok: false, error: "appointed_device set failed: " + String(e) };
    }
    var after = null;
    // extractId() already unwraps a ["id", N] reply by taking its LAST
    // element -- wrapping the .get() reply in unwrap() first (as this did
    // originally) collapses it to its FIRST element instead, the literal
    // string "id", never the numeric id. That bug made every write look
    // unverified even when it had actually taken (live-verified: v1.0.39
    // verification pass).
    try { after = extractId(song.get("appointed_device")); } catch (e2) {}
    var ok = String(after) === String(extractId(device.id));
    return {
        ok: ok,
        message: ok
            ? "Appointed device '" + String(unwrap(device.get("name")) || "") + "' as the target for external control surfaces"
            : "appointed_device write did not verify by read-back"
    };
}

function palSetAutomationRecord(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    if (params.enabled == null) return { ok: false, error: "Provide enabled (true/false)" };
    var en = params.enabled ? 1 : 0;
    // Live-verified (v1.0.39 verification pass): Song.session_automation_record's
    // own .get() reads back the value from BEFORE a same-tick .set() -- two
    // ops in one dispatch call see the stale value, even though the write
    // itself does take (confirmed via a separate round-trip call with a real
    // gap after it). palSetChecked's read-after-write pattern can't verify
    // this property; trust the set() here instead of gating on it.
    try { song.set("session_automation_record", en); } catch (e) {
        return { ok: false, error: "session_automation_record set failed: " + String(e) };
    }
    return { ok: true, message: "Session automation record " + (en ? "enabled" : "disabled") + " (unverified -- this property's own read-back lags the write by a tick)" };
}

// Locates a device parameter by 0-based param_index or by exact (case-
// insensitive) param_name, reusing palDeviceParams's existing scan rather
// than duplicating the parameter-walk loop.
function palFindParamApi(device, params) {
    var plist = palDeviceParams(device, "");
    var needle = params.param_name != null ? String(params.param_name).toLowerCase()
        : (params.paramName != null ? String(params.paramName).toLowerCase() : null);
    var idx = params.param_index != null ? Number(params.param_index)
        : (params.paramIndex != null ? Number(params.paramIndex) : null);
    var i;
    for (i = 0; i < plist.length; i++) {
        if ((needle != null && plist[i].name.toLowerCase() === needle) || (idx != null && plist[i].index === idx)) {
            return plist[i];
        }
    }
    return null;
}

function palReadParamRange(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path or track_index + device_index" };
    if (loc.trackResolvedBy === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.trackName + "'" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found" };
    var found = palFindParamApi(device, params);
    if (!found) return { ok: false, error: "Parameter not found -- give param_name or param_index" };
    var p = liveApi((device.unquotedpath || device.path) + " parameters " + found.index);
    if (!p) return { ok: false, error: "Could not resolve parameter object" };
    var out = {
        ok: true,
        name: found.name,
        index: found.index,
        value: Number(unwrap(p.get("value"))),
        min: Number(unwrap(p.get("min"))),
        max: Number(unwrap(p.get("max")))
    };
    try { out.is_quantized = !!unwrap(p.get("is_quantized")); } catch (e) {}
    try {
        var items = unwrap(p.get("value_items"));
        if (items instanceof Array) out.value_items = items.map(String);
    } catch (e2) {}
    // display_value is a real (settable) DeviceParameter FLOAT property --
    // "the current value as visible in the GUI" -- distinct from the
    // formatted STRING str_for_value() returns. Reading the real property
    // here (read-only) is what probe 1 checks before the write path
    // (palApplyParamValue) is allowed to rely on it -- see KNOWN_ABSENT-
    // adjacent note in test_lom_surface.py and the plan's Part B2 item 1.
    try { out.display_value = Number(unwrap(p.get("display_value"))); } catch (e3) {}
    try { out.display_string = String(unwrap(p.call("str_for_value", out.value)) || ""); } catch (e4) {}
    return out;
}

function palSetParamRaw(params) {
    if (params.value == null) return { ok: false, error: "Provide value (raw float within the parameter's min/max)" };
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path or track_index + device_index" };
    if (loc.trackResolvedBy === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.trackName + "'" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found" };
    var found = palFindParamApi(device, params);
    if (!found) return { ok: false, error: "Parameter not found -- give param_name or param_index" };
    var p = liveApi((device.unquotedpath || device.path) + " parameters " + found.index);
    if (!p) return { ok: false, error: "Could not resolve parameter object" };
    var minVal = Number(unwrap(p.get("min")));
    var maxVal = Number(unwrap(p.get("max")));
    var raw = Number(params.value);
    if (!isNaN(minVal) && !isNaN(maxVal) && maxVal > minVal) {
        raw = Math.max(minVal, Math.min(maxVal, raw));
    }
    if (!palSetChecked(p, "value", raw)) {
        return { ok: false, error: "Raw value " + raw + " did not take (outside range, or parameter is read-only)" };
    }
    var displayAfter = null;
    try { displayAfter = String(unwrap(p.call("str_for_value", raw)) || ""); } catch (e) {}
    return { ok: true, message: "Set '" + found.name + "' raw value to " + raw, value: raw, display_after: displayAfter };
}

function palShowMessage(params) {
    var app = liveApi("live_app");
    if (!app) return { ok: false, error: "Live API not ready" };
    var text = String((params && (params.text || params.message)) || "");
    if (!text) return { ok: false, error: "Provide text" };
    try { app.call("show_message", text); } catch (e) {
        return { ok: false, error: "show_message failed: " + String(e) };
    }
    return { ok: true, message: "Shown in Live's status bar: " + text };
}

// Application.current_dialog_message / press_current_dialog_button directly
// address the Class-D bug where a Live modal blocks the M4L thread and any
// other tool call times out at 10s (DEBUGGING TO DO LIST.md:323-341) -- this
// is the one tool that can see and dismiss the dialog instead of hanging.
function palReadDialog(params) {
    var app = liveApi("live_app");
    if (!app) return { ok: false, error: "Live API not ready" };
    var pressNum = params && (params.press_button_number != null ? params.press_button_number : params.pressButtonNumber);
    if (pressNum != null) {
        var btn = Number(pressNum) - 1;
        try { app.call("press_current_dialog_button", btn); } catch (e) {
            return { ok: false, error: "press_current_dialog_button failed: " + String(e) };
        }
        return { ok: true, message: "Pressed dialog button " + (btn + 1) };
    }
    var message = "";
    var buttonCount = 0;
    try { message = String(unwrap(app.get("current_dialog_message")) || ""); } catch (e2) {}
    try { buttonCount = Number(unwrap(app.get("current_dialog_button_count"))) || 0; } catch (e3) {}
    return {
        ok: true,
        has_dialog: !!message,
        message: message || "(no dialog currently open)",
        button_count: buttonCount
    };
}

function palReadCpu() {
    var app = liveApi("live_app");
    if (!app) return { ok: false, error: "Live API not ready" };
    var avg = null, peak = null;
    try { avg = Number(unwrap(app.get("average_process_usage"))); } catch (e) {}
    try { peak = Number(unwrap(app.get("peak_process_usage"))); } catch (e2) {}
    return {
        ok: true,
        average_process_usage: avg,
        peak_process_usage: peak,
        message: "average_process_usage=" + avg + ", peak_process_usage=" + peak
    };
}

// zoom_view/scroll_view take an undocumented (int, object, bool) signature
// in the 12.3.6 reference -- the int enum's values aren't recoverable from
// static introspection, so they're left out here rather than guessed; the
// probe runbook (Part B) is the place to pin them down in a later pass.
function palViewControl(params) {
    var view = liveApi("live_app view");
    if (!view) return { ok: false, error: "Live API not ready" };
    var action = String((params && params.action) || "list").toLowerCase();
    if (action === "list") {
        var names = [];
        // unwrap() collapses ANY array-like value down to its first element
        // -- correct for a .get()'s single-value-wrapped-in-an-array reply,
        // but wrong here: available_main_views() already returns a genuine
        // multi-element StringVector, and unwrap() was silently reducing it
        // to just "Browser" (live-verified: v1.0.39 verification pass).
        try {
            var raw = view.call("available_main_views");
            if (raw instanceof Array) names = raw.map(String);
        } catch (e) {}
        return { ok: true, available_views: names };
    }
    var viewName = String((params && (params.view_name || params.view)) || "");
    if (!viewName) return { ok: false, error: "Provide view_name (action='list' for valid names)" };
    if (action === "show" || action === "focus") {
        var callName = action === "focus" ? "focus_view" : "show_view";
        try { view.call(callName, viewName); } catch (e2) { return { ok: false, error: callName + " failed: " + String(e2) }; }
        var vis1 = false;
        try { vis1 = !!unwrap(view.call("is_view_visible", viewName)); } catch (e3) {}
        return { ok: vis1, message: (action === "focus" ? "Focused" : "Showed") + " view '" + viewName + "'", is_visible: vis1 };
    }
    if (action === "hide") {
        try { view.call("hide_view", viewName); } catch (e4) { return { ok: false, error: "hide_view failed: " + String(e4) }; }
        var vis2 = true;
        try { vis2 = !!unwrap(view.call("is_view_visible", viewName)); } catch (e5) {}
        return { ok: !vis2, message: "Hid view '" + viewName + "'", is_visible: vis2 };
    }
    if (action === "is_visible") {
        var vis3 = false;
        try { vis3 = !!unwrap(view.call("is_view_visible", viewName)); } catch (e6) {}
        return { ok: true, is_visible: vis3 };
    }
    return { ok: false, error: "Unknown action '" + action + "'. Use list/show/hide/is_visible/focus." };
}

// Reads whatever notes are currently selected in the MIDI Note editor for
// this clip. Calling convention mirrors the sibling get_notes_extended
// (Dict out-param) rather than the bare Python signature reported by the
// LOM reference, which doesn't show Max for Live's Dict-passing quirk --
// unverified against real Ableton until the probe runbook (Part B) runs.
function palReadSelectedNotes(params) {
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "No clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (!unwrap(clip.get("is_midi_clip"))) {
        return { ok: false, error: "Clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) + " is audio, not MIDI." };
    }
    var notes = [];
    try {
        var d = new Dict();
        clip.call("get_selected_notes_extended", d);
        var parsed = JSON.parse(d.getjson());
        d.freepeer();
        if (parsed && parsed.notes) notes = parsed.notes;
    } catch (e) {}
    return {
        ok: true,
        track_index: loc.track,
        slot_index: loc.slot,
        notes: notes,
        count: notes.length,
        message: notes.length
            ? ("Read " + notes.length + " selected note(s)")
            : "No notes are currently selected in the MIDI editor for this clip"
    };
}

function palConnect() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready. Drop Live Actions Bridge on an audio track." };
    var app = liveApi("live_app");
    var version = "";
    // Application has no "version"/"major_version" PROPERTY (neither exists
    // on any LOM class, per app/lom_surface.json) -- get_version_string() /
    // get_major_version() are METHODS. The old .get() calls silently no-op
    // in Max's LiveAPI JS (M1), so live_version has always come back "".
    try {
        if (app) version = String(unwrap(app.call("get_version_string")) || "");
        if (!version && app) version = String(unwrap(app.call("get_major_version")) || "");
    } catch (e) {}
    var scale = palReadScale(song);
    return {
        ok: true,
        message: "Connected to Live Set '" + String(unwrap(song.get("name")) || "Untitled") + "'",
        live_version: version,
        set: {
            name: String(unwrap(song.get("name")) || "Untitled"),
            tempo: Number(unwrap(song.get("tempo"))),
            time_signature: palTimeSig(song),
            scale: scale,
            track_count: song.getcount("tracks"),
            scene_count: song.getcount("scenes"),
            return_count: song.getcount("return_tracks"),
            is_playing: !!unwrap(song.get("is_playing"))
        }
    };
}

function palTimeSig(song) {
    return String(unwrap(song.get("signature_numerator"))) + "/" + String(unwrap(song.get("signature_denominator")));
}

function palReadScale(song) {
    var mode = 0;
    var root = 0;
    var name = "";
    try { mode = Number(unwrap(song.get("scale_mode")) || 0); } catch (e) {}
    try { root = Number(unwrap(song.get("root_note")) || 0); } catch (e2) {}
    try { name = String(unwrap(song.get("scale_name")) || ""); } catch (e3) {}
    var roots = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    var label = "";
    if (mode && name) label = roots[((root % 12) + 12) % 12] + " " + name;
    return { enabled: !!mode, root_note: root, scale_name: name, label: label };
}

// Resolves a track name typed by the user to a track_index. Case-insensitive
// exact match wins; failing that, a unique case-insensitive substring match.
// Returns -1 on no match or an ambiguous substring match -- callers must not
// silently fall back to 0 on -1, since that would recreate the exact
// wrong-track bug this resolver exists to fix.
function palResolveTrackIndex(name) {
    var needle = String(name || "").trim().toLowerCase();
    if (!needle) return -1;
    var song = liveApi("live_set");
    if (!song) return -1;
    var n = 0;
    try { n = song.getcount("tracks"); } catch (e) { return -1; }
    var i, tName;
    for (i = 0; i < n; i++) {
        var t = liveApi("live_set tracks " + i);
        if (!t) continue;
        tName = String(unwrap(t.get("name")) || "").toLowerCase();
        if (tName === needle) return i;
    }
    var matches = [];
    for (i = 0; i < n; i++) {
        var t2 = liveApi("live_set tracks " + i);
        if (!t2) continue;
        tName = String(unwrap(t2.get("name")) || "").toLowerCase();
        if (tName.indexOf(needle) !== -1) matches.push(i);
    }
    return matches.length === 1 ? matches[0] : -1;
}

// Shared track-index resolution for every track-scoped pal function.
// Precedence: explicit track_index/trackIndex always wins; else
// track_name/trackName is resolved via palResolveTrackIndex (returns -1,
// not dflt, if the name doesn't resolve -- a bad liveApi path fails cleanly
// via the caller's existing "Track not found" guard rather than silently
// hitting some other track); else dflt (default 0, the pre-existing
// behavior when no track param at all is given).
function palTrackIndexFromParams(params, dflt) {
    if (params.track_index != null) return Number(params.track_index);
    if (params.trackIndex != null) return Number(params.trackIndex);
    var nameParam = params.track_name || params.trackName;
    if (nameParam) return palResolveTrackIndex(nameParam);
    return dflt != null ? dflt : 0;
}

function palTrackPath(params) {
    var kind = String(params.track_type || params.trackType || params.kind || "").toLowerCase();
    if (kind === "master") return { path: "live_set master_track", kind: "master", index: 0, name: null, resolved_by: "index" };
    var hasIndex = params.track_index != null || params.trackIndex != null;
    var nameParam = params.track_name || params.trackName;
    var idx, resolvedBy;
    if (hasIndex) {
        idx = Number(params.track_index != null ? params.track_index : params.trackIndex);
        resolvedBy = "index";
    } else if (nameParam) {
        idx = palResolveTrackIndex(nameParam);
        resolvedBy = idx >= 0 ? "name" : "name_not_found";
    } else {
        idx = 0;
        resolvedBy = "default";
    }
    if (kind === "return") return { path: "live_set return_tracks " + idx, kind: "return", index: idx, name: nameParam || null, resolved_by: resolvedBy };
    return { path: "live_set tracks " + idx, kind: "", index: idx, name: nameParam || null, resolved_by: resolvedBy };
}

// LiveAPI .set() in Max JS posts errors to the Max Console but never throws
// (M1), so a try{A}catch{fallback} around a set() is dead code -- the catch
// never runs even when the property doesn't exist in this LOM/Live version.
// The only honest way to know a set "took" is to read the property back
// afterward and compare. Returns true only if the post-set value matches
// (float tolerance) what was requested.
function palSetChecked(api, prop, value) {
    if (!api) return false;
    try { api.set(prop, value); } catch (e) { return false; }
    var after = unwrap(api.get(prop));
    if (typeof value === "number") {
        var num = Number(after);
        return !isNaN(num) && Math.abs(num - value) < 1e-6;
    }
    if (typeof value === "boolean") {
        return !!after === value;
    }
    return after === value || String(after) === String(value);
}

function palIncludeHas(include, key) {
    if (!include || !include.length) return key === "overview";
    var i;
    for (i = 0; i < include.length; i++) {
        var v = String(include[i] || "").toLowerCase();
        if (v === "*" || v === key) return true;
    }
    return false;
}

function palMixer(path) {
    var vol = liveApi(path + " mixer_device volume");
    var pan = liveApi(path + " mixer_device panning");
    var out = {
        volume: vol ? Number(unwrap(vol.get("value"))) : null,
        pan: pan ? Number(unwrap(pan.get("value"))) : null,
        sends: []
    };
    var mixer = liveApi(path + " mixer_device");
    if (!mixer) return out;
    var n = 0;
    try { n = mixer.getcount("sends"); } catch (e) { n = 0; }
    var i;
    for (i = 0; i < n; i++) {
        var s = liveApi(path + " mixer_device sends " + i);
        if (!s) continue;
        out.sends.push({
            index: i,
            letter: String.fromCharCode(65 + i),
            value: Number(unwrap(s.get("value")))
        });
    }
    return out;
}

function palRoutings(track) {
    var out = {};
    var keys = [
        "current_input_routing",
        "current_input_sub_routing",
        "current_output_routing",
        "current_output_sub_routing",
        "current_monitoring_state"
    ];
    var i;
    for (i = 0; i < keys.length; i++) {
        try { out[keys[i]] = unwrap(track.get(keys[i])); } catch (e) {}
    }
    return out;
}

function palAvailableRoutings(track) {
    var out = {};
    var keys = [
        "available_input_routing_types",
        "available_input_routing_channels",
        "available_output_routing_types",
        "available_output_routing_channels"
    ];
    var i;
    for (i = 0; i < keys.length; i++) {
        try { out[keys[i]] = track.get(keys[i]); } catch (e) {}
    }
    return out;
}

function palDescribeDevices(path) {
    var t = liveApi(path);
    if (!t) return [];
    var n = t.getcount("devices");
    var devices = [];
    var i;
    for (i = 0; i < n; i++) {
        var d = liveApi(path + " devices " + i);
        if (!d) continue;
        devices.push({
            index: i,
            path: "d" + i,
            name: String(unwrap(d.get("name")) || ""),
            class_name: String(unwrap(d.get("class_name")) || ""),
            class_display_name: String(unwrap(d.get("class_display_name")) || ""),
            is_active: !!unwrap(d.get("is_active")),
            can_have_chains: !!unwrap(d.get("can_have_chains")),
            can_have_drum_pads: !!unwrap(d.get("can_have_drum_pads"))
        });
    }
    return devices;
}

function palSessionSlots(path, maxSlots, withNotes) {
    var t = liveApi(path);
    if (!t) return [];
    var n = t.getcount("clip_slots");
    if (maxSlots && n > maxSlots) n = maxSlots;
    var slots = [];
    var i;
    for (i = 0; i < n; i++) {
        var sl = liveApi(path + " clip_slots " + i);
        if (!sl) continue;
        var has = !!unwrap(sl.get("has_clip"));
        var info = { index: i, has_clip: has };
        if (has) {
            var cl = liveApi(path + " clip_slots " + i + " clip");
            if (cl) info.clip = palClipOverview(cl, withNotes);
        }
        slots.push(info);
    }
    return slots;
}

function palClipOverview(cl, withNotes) {
    var info = {
        name: String(unwrap(cl.get("name")) || ""),
        color: unwrap(cl.get("color")),
        length: Number(unwrap(cl.get("length")) || 0),
        looping: !!unwrap(cl.get("looping")),
        is_midi: !!unwrap(cl.get("is_midi_clip")),
        is_audio: !!unwrap(cl.get("is_audio_clip")),
        is_playing: !!unwrap(cl.get("is_playing")),
        muted: !!unwrap(cl.get("muted"))
    };
    if (withNotes && info.is_midi) {
        var noteResult = palGetNotes(cl);
        info.notes = noteResult.notes;
        if (noteResult.truncated) {
            info.notes_truncated = true;
            info.note_count = noteResult.total;
        }
    }
    if (info.is_audio) {
        try { info.warping = !!unwrap(cl.get("warping")); } catch (e) {}
        try { info.pitch_coarse = Number(unwrap(cl.get("pitch_coarse")) || 0); } catch (e2) {}
        try { info.gain = Number(unwrap(cl.get("gain")) || 0); } catch (e3) {}
        try {
            var sample = liveApi(cl.unquotedpath + " sample");
            if (sample) {
                info.sample_file = String(unwrap(sample.get("file_path")) || "");
            }
        } catch (e4) {}
    }
    return info;
}

// Genius/Pal clip reads had no cap of their own, unlike arrangement_scan's
// documented 200-clip cap -- a dense clip's full note list is one of the
// biggest single contributors to a reply blowing past one UDP datagram
// (bridge/live-actions-bridge.js's sendChunked now splits an oversized reply
// instead of losing it, but there's no reason to ship megabytes of notes
// through several dozen chunks when Genius only needs a representative
// read). Cap it and report the real count honestly, same pattern
// arrangement_scan already established.
var PAL_NOTES_CAP = 500;

function palGetNotes(clip) {
    var result = { notes: [], truncated: false, total: 0 };
    if (!clip) return result;
    var clipLen = Number(unwrap(clip.get("length")) || 4);
    try {
        var d = new Dict();
        clip.call("get_notes_extended", 0, 128, 0, clipLen, d);
        var parsed = JSON.parse(d.getjson());
        d.freepeer();
        var all = (parsed && parsed.notes) || [];
        result.total = all.length;
        if (all.length > PAL_NOTES_CAP) {
            result.notes = all.slice(0, PAL_NOTES_CAP);
            result.truncated = true;
        } else {
            result.notes = all;
        }
    } catch (e) {}
    return result;
}

function palDrumMap(path, deviceIndex) {
    var rack = liveApi(path + " devices " + deviceIndex);
    if (!rack || !unwrap(rack.get("can_have_drum_pads"))) return null;
    var n = 0;
    try { n = rack.getcount("drum_pads"); } catch (e) { return null; }
    var pads = [];
    var i;
    for (i = 0; i < n; i++) {
        var pad = liveApi(path + " devices " + deviceIndex + " drum_pads " + i);
        if (!pad) continue;
        var chains = 0;
        try { chains = pad.getcount("chains"); } catch (e2) {}
        if (!chains) continue;
        pads.push({
            note: i,
            name: palPitchName(i),
            pad_name: String(unwrap(pad.get("name")) || ""),
            mute: !!unwrap(pad.get("mute")),
            solo: !!unwrap(pad.get("solo")),
            chains: chains
        });
    }
    return pads;
}

function palPitchName(note) {
    var names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    var n = Number(note);
    var oct = Math.floor(n / 12) - 2;
    return names[((n % 12) + 12) % 12] + String(oct);
}

function palNoteToPitch(raw) {
    if (raw === null || raw === undefined) return NaN;
    if (typeof raw === "number") return raw;
    var s = String(raw).replace(/^\s+|\s+$/g, "");
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    var m = s.match(/^([A-Ga-g])([#b]?)(-?\d+)$/);
    if (!m) return NaN;
    var map = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 };
    var n = map[m[1].toLowerCase()];
    if (m[2] === "#") n += 1;
    if (m[2] === "b") n -= 1;
    return (parseInt(m[3], 10) + 2) * 12 + n;
}

function palParseDuration(raw, beatsPerBar) {
    var s = String(raw || "").replace(/^\s+|\s+$/g, "");
    if (!s) return 1;
    var bar = s.match(/^(\d+(?:\.\d+)?)bar$/i);
    if (bar) return Number(bar[1]) * beatsPerBar;
    // n/N is always 4/N quarter-note beats -- an eighth note is 0.5 beats
    // regardless of meter. Not beatsPerBar/N: that was only ever correct in
    // 4/4 (see docs/plans/v1.0.4-key-detection-mode-weighting.md).
    var frac = s.match(/^n\/(\d+)$/i);
    if (frac) return 4 / Number(frac[1]);
    var num = Number(s);
    if (!isNaN(num)) return num;
    return 1;
}

function palBarBeatToBeats(raw, beatsPerBar) {
    var s = String(raw || "").replace(/^\s+|\s+$/g, "");
    var m = s.match(/^(\d+)\|(\d+(?:\.\d+)?)$/);
    if (m) return (Number(m[1]) - 1) * beatsPerBar + (Number(m[2]) - 1);
    var n = Number(s);
    return isNaN(n) ? 0 : n;
}

function palParseNotes(raw, beatsPerBar) {
    if (!raw) return [];
    if (typeof raw === "string" && /^\s*\[/.test(raw)) {
        try {
            var parsed = JSON.parse(raw);
            if (parsed instanceof Array) raw = parsed;
        } catch (e) {
            // not JSON -- fall through to the Pal text tokenizer below
        }
    }
    if (raw instanceof Array) {
        var out = [];
        var i;
        for (i = 0; i < raw.length; i++) {
            var n = raw[i] || {};
            var item = {
                pitch: palNoteToPitch(n.pitch != null ? n.pitch : n.note),
                startTime: Number(n.startTime != null ? n.startTime : (n.start_time != null ? n.start_time : 0)),
                duration: Number(n.duration != null ? n.duration : 0.25),
                velocity: Number(n.velocity != null ? n.velocity : 100),
                mute: !!n.mute
            };
            if (n.probability != null) item.probability = Math.max(0, Math.min(1, Number(n.probability)));
            if (n.velocity_deviation != null) item.velocity_deviation = Math.max(-127, Math.min(127, Number(n.velocity_deviation)));
            out.push(item);
        }
        return out;
    }
    var text = String(raw);
    var notes = [];
    var vel = 100;
    var dur = 0.25;
    var tokens = text.replace(/\n/g, " ").split(/\s+/);
    var i;
    for (i = 0; i < tokens.length; i++) {
        var tok = tokens[i];
        if (!tok) continue;
        if (/^v\d+$/i.test(tok)) {
            vel = parseInt(tok.slice(1), 10);
            continue;
        }
        if (/^n\/\d+$/i.test(tok) || /^n\d/.test(tok) || /bar$/i.test(tok)) {
            dur = palParseDuration(tok.replace(/^n(?=\d)/, "n/"), beatsPerBar);
            if (/^n\/\d+$/i.test(tok)) dur = 4 / Number(tok.slice(2));
            continue;
        }
        var pitch = palNoteToPitch(tok);
        if (isNaN(pitch)) continue;
        var timeTok = tokens[i + 1];
        var start = 0;
        if (timeTok && (/\|/.test(timeTok) || /^[\d.]+$/.test(timeTok))) {
            start = palBarBeatToBeats(timeTok, beatsPerBar);
            i += 1;
        }
        notes.push({ pitch: pitch, startTime: start, duration: dur, velocity: vel, mute: false });
    }
    return notes;
}

function palCuePoints() {
    var song = liveApi("live_set");
    if (!song) return [];
    var n = 0;
    try { n = song.getcount("cue_points"); } catch (e) { return []; }
    var out = [];
    var i;
    for (i = 0; i < n; i++) {
        var c = liveApi("live_set cue_points " + i);
        if (!c) continue;
        out.push({
            index: i,
            id: "locator-" + i,
            name: String(unwrap(c.get("name")) || ""),
            time: Number(unwrap(c.get("time")) || 0)
        });
    }
    return out;
}

// Same reasoning as PAL_NOTES_CAP: with include:"*", palReadSet attaches
// devices plus up to 16 clip slots per track, unbounded by track count. A
// realistically large Set (60+ tracks) reading through Genius was the
// actual trigger for the bridge-timeout-disconnect fix this caps against.
// track_count on the reply stays the real total either way -- only the
// per-track detail array is capped, same honesty contract as
// arrangement_scan's scanCount vs. its truncated clip list.
var PAL_TRACKS_CAP = 60;

function palReadSet(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var include = params.include || ["tracks", "scenes"];
    if (typeof include === "string") include = include.split(",");
    var wantAll = palIncludeHas(include, "*");
    var set = {
        name: String(unwrap(song.get("name")) || "Untitled"),
        tempo: Number(unwrap(song.get("tempo"))),
        time_signature: palTimeSig(song),
        scale: palReadScale(song),
        is_playing: !!unwrap(song.get("is_playing")),
        current_song_time: Number(unwrap(song.get("current_song_time")) || 0),
        metronome: !!unwrap(song.get("metronome")),
        clip_trigger_quantization: Number(unwrap(song.get("clip_trigger_quantization")) || 0),
        track_count: song.getcount("tracks"),
        scene_count: song.getcount("scenes"),
        return_count: song.getcount("return_tracks")
    };
    if (wantAll || palIncludeHas(include, "tracks")) {
        set.tracks = [];
        var i;
        var totalTracks = song.getcount("tracks");
        var n = Math.min(totalTracks, PAL_TRACKS_CAP);
        if (totalTracks > PAL_TRACKS_CAP) set.tracks_truncated = true;
        for (i = 0; i < n; i++) {
            var tp = "live_set tracks " + i;
            var t = liveApi(tp);
            if (!t) continue;
            var kind = unwrap(t.get("has_midi_input")) ? "midi" : "audio";
            var item = {
                index: i,
                kind: kind,
                name: String(unwrap(t.get("name")) || ("Track " + (i + 1))),
                color: unwrap(t.get("color")),
                mute: !!unwrap(t.get("mute")),
                solo: !!unwrap(t.get("solo")),
                arm: !!unwrap(t.get("arm"))
            };
            if (wantAll || palIncludeHas(include, "mixer")) item.mixer = palMixer(tp);
            if (wantAll || palIncludeHas(include, "routings")) item.routings = palRoutings(t);
            if (wantAll || palIncludeHas(include, "color")) item.color = unwrap(t.get("color"));
            item.devices = palDescribeDevices(tp);
            item.clip_slots = palSessionSlots(tp, 16, false);
            set.tracks.push(item);
        }
        var rn = song.getcount("return_tracks");
        set.returns = [];
        for (i = 0; i < rn; i++) {
            var rp = "live_set return_tracks " + i;
            var r = liveApi(rp);
            if (!r) continue;
            set.returns.push({
                index: i,
                kind: "return",
                name: String(unwrap(r.get("name")) || ("Return " + (i + 1))),
                mute: !!unwrap(r.get("mute")),
                devices: palDescribeDevices(rp)
            });
        }
        var master = liveApi("live_set master_track");
        if (master) {
            set.master = {
                kind: "master",
                name: String(unwrap(master.get("name")) || "Master"),
                devices: palDescribeDevices("live_set master_track")
            };
            if (wantAll || palIncludeHas(include, "mixer")) {
                set.master.mixer = palMixer("live_set master_track");
            }
        }
    }
    if (wantAll || palIncludeHas(include, "scenes")) {
        set.scenes = [];
        var sn = song.getcount("scenes");
        var s;
        for (s = 0; s < Math.min(64, sn); s++) {
            var sc = liveApi("live_set scenes " + s);
            if (!sc) continue;
            set.scenes.push({
                index: s,
                name: String(unwrap(sc.get("name")) || ("Scene " + (s + 1))),
                color: unwrap(sc.get("color"))
            });
        }
    }
    if (wantAll || palIncludeHas(include, "locators")) {
        set.locators = palCuePoints();
    }
    return { ok: true, set: set };
}

function palParseScale(text) {
    var s = String(text || "").replace(/^\s+|\s+$/g, "");
    if (!s) return { enabled: false };
    var roots = {
        "c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5,
        "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11
    };
    var m = s.match(/^([A-Ga-g][#b]?)\s+(.+)$/);
    if (!m) return { enabled: true, scale_name: s };
    var root = roots[m[1].toLowerCase()];
    return { enabled: true, root_note: root, scale_name: m[2] };
}

function palUpdateSet(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var changes = [];
    if (params.tempo != null) {
        var tempo = Math.max(20, Math.min(999, Number(params.tempo)));
        song.set("tempo", tempo);
        changes.push("tempo=" + tempo);
    }
    if (params.timeSignature || params.time_signature) {
        var ts = String(params.timeSignature || params.time_signature);
        var parts = ts.split("/");
        if (parts.length === 2) {
            song.set("signature_numerator", Number(parts[0]));
            song.set("signature_denominator", Number(parts[1]));
            changes.push("time_signature=" + ts);
        }
    }
    if (params.scale !== undefined) {
        if (params.scale === "" || params.scale === null) {
            try { song.set("scale_mode", 0); } catch (e) {}
            changes.push("scale=off");
        } else {
            var sc = palParseScale(params.scale);
            try { song.set("scale_mode", 1); } catch (e2) {}
            if (sc.root_note != null) {
                try { song.set("root_note", sc.root_note); } catch (e3) {}
            }
            if (sc.scale_name) {
                try { song.set("scale_name", sc.scale_name); } catch (e4) {}
            }
            changes.push("scale=" + params.scale);
        }
    }
    if (params.metronome != null) {
        var metro = (params.metronome === true || params.metronome === 1 || params.metronome === "1" || params.metronome === "true" || params.metronome === "on") ? 1 : 0;
        try {
            song.set("metronome", metro);
            changes.push("metronome=" + (metro ? "on" : "off"));
        } catch (eMetro) {}
    }
    if (params.clip_trigger_quantization != null || params.clipTriggerQuantization != null) {
        var ctq = Number(params.clip_trigger_quantization != null ? params.clip_trigger_quantization : params.clipTriggerQuantization);
        try {
            song.set("clip_trigger_quantization", ctq);
            changes.push("clip_trigger_quantization=" + ctq);
        } catch (eCtq) {}
    }
    var locOp = params.locatorOperation || params.locator_operation;
    if (locOp) {
        var locRes = palLocatorOp(song, locOp, params);
        if (!locRes.ok) return locRes;
        changes.push(locRes.message);
    }
    if (!changes.length && params.tempo == null) {
        return { ok: true, message: "Live Set unchanged", set: palConnect().set };
    }
    return { ok: true, message: "Updated Live Set: " + changes.join(", ") };
}

function palLocatorOp(song, op, params) {
    op = String(op).toLowerCase();
    var beatsPerBar = Number(unwrap(song.get("signature_numerator")) || 4);
    if (op === "create") {
        var time = params.locatorTime || params.locator_time;
        var beats = palBarBeatToBeats(time != null ? time : 0, beatsPerBar);
        var name = params.locatorName || params.locator_name;

        // set_or_delete_cue is a TOGGLE -- if a cue already sits at this beat,
        // calling it again would delete the existing locator instead of
        // creating a new one. Rename in place instead (M6).
        var existingCues = palCuePoints();
        var ei;
        for (ei = 0; ei < existingCues.length; ei++) {
            if (Math.abs(existingCues[ei].time - beats) < 0.05) {
                if (name) {
                    var ec = liveApi("live_set cue_points " + existingCues[ei].index);
                    if (ec) ec.set("name", String(name));
                }
                return { ok: true, message: "Locator already existed at that time" + (name ? " -- renamed it" : "") };
            }
        }

        var origTime = Number(unwrap(song.get("current_song_time")) || 0);
        try { song.set("current_song_time", beats); } catch (e) {}
        try { song.call("set_or_delete_cue"); } catch (e2) {}
        try { song.set("current_song_time", origTime); } catch (eRestore) {}
        if (name) {
            var cues = palCuePoints();
            var i;
            for (i = 0; i < cues.length; i++) {
                if (Math.abs(cues[i].time - beats) < 0.05) {
                    var c = liveApi("live_set cue_points " + cues[i].index);
                    if (c) c.set("name", String(name));
                }
            }
        }
        return { ok: true, message: "created locator" };
    }
    if (op === "delete" || op === "rename") {
        var cues = palCuePoints();
        var target = params.locatorId || params.locator_id || params.locatorName || params.locator_name;
        var time = params.locatorTime || params.locator_time;
        var i;
        for (i = 0; i < cues.length; i++) {
            var match = false;
            if (target && (cues[i].id === String(target) || cues[i].name === String(target))) match = true;
            if (time != null && Math.abs(cues[i].time - palBarBeatToBeats(time, beatsPerBar)) < 0.05) match = true;
            if (!match) continue;
            if (op === "rename") {
                var c = liveApi("live_set cue_points " + cues[i].index);
                if (c) c.set("name", String(params.locatorName || params.locator_name || cues[i].name));
                return { ok: true, message: "renamed locator" };
            }
            try { song.set("current_song_time", cues[i].time); } catch (e3) {}
            try { song.call("set_or_delete_cue"); } catch (e4) {}
            return { ok: true, message: "deleted locator" };
        }
        return { ok: false, error: "Locator not found" };
    }
    return { ok: false, error: "Unknown locator operation: " + op };
}

function palReadTrack(params) {
    var loc = palTrackPath(params);
    if (loc.resolved_by === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.name + "'" };
    var t = liveApi(loc.path);
    if (!t) return { ok: false, error: "Track not found" };
    var include = params.include || [];
    if (typeof include === "string") include = include.split(",");
    var wantAll = palIncludeHas(include, "*");
    var kind = loc.kind || (unwrap(t.get("has_midi_input")) ? "midi" : "audio");
    var out = {
        ok: true,
        index: loc.index,
        resolved_by: loc.resolved_by,
        kind: kind,
        path: loc.path,
        name: String(unwrap(t.get("name")) || ""),
        color: unwrap(t.get("color")),
        mute: !!unwrap(t.get("mute")),
        solo: !!unwrap(t.get("solo")),
        arm: loc.kind === "master" ? false : !!unwrap(t.get("arm"))
    };
    if (wantAll || palIncludeHas(include, "mixer") || !include.length) out.mixer = palMixer(loc.path);
    if (wantAll || palIncludeHas(include, "routings")) out.routings = palRoutings(t);
    if (wantAll || palIncludeHas(include, "available-routings")) out.available_routings = palAvailableRoutings(t);
    if (wantAll || palIncludeHas(include, "devices") || !include.length) out.devices = palDescribeDevices(loc.path);
    if (wantAll || palIncludeHas(include, "session-clips") || palIncludeHas(include, "clips") || !include.length) {
        out.session_clips = palSessionSlots(loc.path, 0, wantAll || palIncludeHas(include, "notes"));
    }
    if (wantAll || palIncludeHas(include, "arrangement-clips") || palIncludeHas(include, "arrangement_clips")) {
        out.arrangement_clips = palReadArrangementClips({ track_index: loc.index, track_type: loc.kind, path: loc.path }).clips || [];
    }
    if (wantAll || palIncludeHas(include, "drum-map")) {
        var devices = out.devices || palDescribeDevices(loc.path);
        out.drum_map = [];
        var i;
        for (i = 0; i < devices.length; i++) {
            if (devices[i].can_have_drum_pads) {
                out.drum_map = palDrumMap(loc.path, devices[i].index) || [];
                break;
            }
        }
    }
    try {
        var ms = unwrap(t.get("current_monitoring_state"));
        if (ms != null) {
            var msNames = ["in", "auto", "off"];
            out.monitoring = msNames[Number(ms)] || String(ms);
        }
    } catch (eMon) {}
    if (loc.kind !== "master") {
        try {
            var md = liveApi(loc.path + " mixer_device");
            if (md) {
                var ca = unwrap(md.get("crossfade_assign"));
                var caNames = ["a", "none", "b"];
                if (ca != null) out.crossfade_assign = caNames[Number(ca)] || String(ca);
            }
        } catch (eCa) {}
    }
    try {
        var td = liveApi(loc.path + " mixer_device track_delay");
        if (td) {
            out.delay_ms = Number(unwrap(td.get("value")) || 0);
        }
    } catch (eTd2) {}
    return out;
}

function palSelectTrack(path) {
    var track = liveApi(path);
    var view = liveApi("live_set view");
    if (!track || !view) return;
    try { view.set("selected_track", "id", extractId(track.id)); } catch (e) {
        try { view.set("selected_track", "id " + track.id); } catch (e2) {}
    }
}

function palUpdateTrack(params) {
    var loc = palTrackPath(params);
    if (loc.resolved_by === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.name + "'" };
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track " + loc.index + " not found" };
    if (params.name != null) track.set("name", String(params.name));
    if (params.color != null) track.set("color", hexToLiveColor(params.color));
    if (params.mute != null) track.set("mute", params.mute ? 1 : 0);
    if (params.solo != null) track.set("solo", params.solo ? 1 : 0);
    if (params.arm != null && loc.kind !== "master") track.set("arm", params.arm ? 1 : 0);
    if (params.volume != null || params.gainDb != null || params.gain_db != null) {
        var vm = liveApi(loc.path + " mixer_device volume");
        if (vm) {
            var v = params.volume;
            if (v == null) v = palDbToLive(Number(params.gainDb != null ? params.gainDb : params.gain_db));
            vm.set("value", Math.max(0, Math.min(1, Number(v))));
        }
    }
    if (params.pan != null) {
        var pm = liveApi(loc.path + " mixer_device panning");
        if (pm) pm.set("value", Math.max(-1, Math.min(1, Number(params.pan))));
    }
    if (params.sendGainDb != null || params.send_gain != null || params.send != null) {
        var letter = String(params.sendReturn || params.send_return || params.send || "A");
        var si = palSendIndex(letter);
        var send = liveApi(loc.path + " mixer_device sends " + si);
        if (send) {
            var sv = params.send_gain != null ? Number(params.send_gain) : palDbToLive(Number(params.sendGainDb || params.send_gain_db || 0));
            send.set("value", Math.max(0, Math.min(1, sv)));
        }
    }
    if (params.monitoring || params.monitoringState || params.monitoring_state) {
        var mon = String(params.monitoring || params.monitoringState || params.monitoring_state).toLowerCase();
        var monMap = { "in": 0, "auto": 1, "off": 2 };
        if (monMap[mon] != null) {
            try { track.set("current_monitoring_state", monMap[mon]); } catch (e) {}
        }
    }
    if (params.delay_ms != null || params.delayMs != null || params.delay != null) {
        var dms = Number(params.delay_ms != null ? params.delay_ms : (params.delayMs != null ? params.delayMs : params.delay));
        var td2 = liveApi(loc.path + " mixer_device track_delay");
        if (td2) {
            try { td2.set("value", dms); } catch (eTd) {}
        }
    }
    if (params.crossfade_assign != null || params.crossfadeAssign != null) {
        var cfa = params.crossfade_assign != null ? params.crossfade_assign : params.crossfadeAssign;
        var cfaMap = { "a": 0, "none": 1, "b": 2 };
        if (typeof cfa === "string" && cfaMap[cfa.toLowerCase()] != null) cfa = cfaMap[cfa.toLowerCase()];
        var md2 = liveApi(loc.path + " mixer_device");
        if (md2) {
            try { md2.set("crossfade_assign", Number(cfa)); } catch (eCfa) {}
        }
    }
    if (params.inputRoutingTypeId || params.input_routing_type) {
        try { track.set("current_input_routing", String(params.inputRoutingTypeId || params.input_routing_type)); } catch (e) {}
    }
    if (params.inputRoutingChannelId || params.input_routing_channel) {
        try { track.set("current_input_sub_routing", String(params.inputRoutingChannelId || params.input_routing_channel)); } catch (e2) {}
    }
    if (params.outputRoutingTypeId || params.output_routing_type) {
        try { track.set("current_output_routing", String(params.outputRoutingTypeId || params.output_routing_type)); } catch (e3) {}
    }
    if (params.outputRoutingChannelId || params.output_routing_channel) {
        try { track.set("current_output_sub_routing", String(params.outputRoutingChannelId || params.output_routing_channel)); } catch (e4) {}
    }
    var resolvedNote = loc.resolved_by === "name" ? " [resolved by name '" + loc.name + "']" : "";
    return { ok: true, index: loc.index, resolved_by: loc.resolved_by, message: "Updated track_index " + loc.index + " (" + (unwrap(track.get("name")) || loc.kind) + ")" + resolvedNote };
}

function palSendIndex(raw) {
    var s = String(raw || "A").replace(/^\s+|\s+$/g, "");
    if (/^\d+$/.test(s)) return parseInt(s, 10);
    var ch = s.charAt(0).toUpperCase();
    return Math.max(0, ch.charCodeAt(0) - 65);
}

function palDbToLive(db) {
    if (db <= -70) return 0;
    return Math.pow(10, db / 20);
}

function palCreateTrack(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var type = String(params.type || "midi").toLowerCase();
    var count = Math.max(1, Number(params.count || 1));
    var names = String(params.name || "").split(",");
    var colors = String(params.color || "").split(",");
    var created = [];
    var i;
    for (i = 0; i < count; i++) {
        var countBefore = song.getcount("tracks");
        var targetIdx = (params.trackIndex != null || params.index != null)
            ? Number(params.trackIndex != null ? params.trackIndex : params.index)
            : -1;
        if (type === "midi") song.call("create_midi_track", targetIdx);
        else if (type === "audio") song.call("create_audio_track", targetIdx);
        else if (type === "return") {
            song.call("create_return_track");
            created.push({ kind: "return" });
            continue;
        } else return { ok: false, error: "Unknown track type: " + type };
        var createdIdx = (targetIdx >= 0 && targetIdx < countBefore) ? targetIdx : (song.getcount("tracks") - 1);
        var createdTrack = liveApi("live_set tracks " + createdIdx);
        var nm = names[i] || names[0];
        var col = colors[i] || colors[0];
        if (createdTrack) {
            if (nm) createdTrack.set("name", String(nm).replace(/^\s+|\s+$/g, ""));
            if (col) createdTrack.set("color", hexToLiveColor(col));
            if (params.mute != null) createdTrack.set("mute", params.mute ? 1 : 0);
            if (params.solo != null) createdTrack.set("solo", params.solo ? 1 : 0);
            if (params.arm != null) createdTrack.set("arm", params.arm ? 1 : 0);
        }
        created.push({ index: createdIdx, name: nm || ("Track " + (createdIdx + 1)), type: type });
    }
    return {
        ok: true,
        message: "Created " + created.length + " " + type + " track(s)",
        tracks: created,
        track_index: created.length ? created[0].index : -1
    };
}

function palReadScene(params) {
    var idx = Number(params.scene_index != null ? params.scene_index : (params.sceneIndex != null ? params.sceneIndex : 0));
    var sc = liveApi("live_set scenes " + idx);
    if (!sc) return { ok: false, error: "Scene " + idx + " not found" };
    var include = params.include || [];
    if (typeof include === "string") include = include.split(",");
    var wantAll = palIncludeHas(include, "*");
    var out = {
        ok: true,
        index: idx,
        name: String(unwrap(sc.get("name")) || ""),
        color: unwrap(sc.get("color"))
    };
    try { out.tempo = Number(unwrap(sc.get("tempo"))); } catch (e) {}
    if (wantAll || palIncludeHas(include, "clips") || !include.length) {
        var song = liveApi("live_set");
        var n = song ? song.getcount("tracks") : 0;
        out.clips = [];
        var i;
        for (i = 0; i < n; i++) {
            var sl = liveApi("live_set tracks " + i + " clip_slots " + idx);
            if (!sl || !unwrap(sl.get("has_clip"))) continue;
            var cl = liveApi("live_set tracks " + i + " clip_slots " + idx + " clip");
            if (!cl) continue;
            var info = palClipOverview(cl, wantAll || palIncludeHas(include, "notes"));
            info.track_index = i;
            info.slot_index = idx;
            out.clips.push(info);
        }
    }
    return out;
}

function palUpdateScene(params) {
    var ids = String(params.ids || "");
    var indexes = [];
    if (params.scene_index != null || params.sceneIndex != null) {
        indexes.push(Number(params.scene_index != null ? params.scene_index : params.sceneIndex));
    } else if (ids) {
        var parts = ids.split(",");
        var i;
        for (i = 0; i < parts.length; i++) {
            var p = String(parts[i]).replace(/^\s+|\s+$/g, "");
            if (/^\d+$/.test(p)) indexes.push(parseInt(p, 10));
            else if (/^scene-?(\d+)$/i.test(p)) indexes.push(parseInt(p.replace(/^[^\d]+/, ""), 10));
        }
    }
    if (!indexes.length) return { ok: false, error: "Provide scene_index or ids" };
    var names = String(params.name || "").split(",");
    var colors = String(params.color || "").split(",");
    var updated = 0;
    var i;
    for (i = 0; i < indexes.length; i++) {
        var sc = liveApi("live_set scenes " + indexes[i]);
        if (!sc) continue;
        var nm = names[i] || names[0];
        var col = colors[i] || colors[0];
        if (nm) sc.set("name", String(nm).replace(/^\s+|\s+$/g, ""));
        if (col) sc.set("color", hexToLiveColor(col));
        if (params.tempo != null) {
            try { sc.set("tempo", Number(params.tempo)); } catch (e) {}
        }
        updated += 1;
    }
    return { ok: true, message: "Updated " + updated + " scene(s)" };
}

function palCreateScene(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    if (params.capture) {
        try { song.call("capture_and_insert_scene"); } catch (e) {
            try { song.call("capture_scene"); } catch (e2) {
                return { ok: false, error: "Scene capture is not available: " + e };
            }
        }
        var capturedIdx = song.getcount("scenes") - 1;
        var cap = liveApi("live_set scenes " + capturedIdx);
        if (cap && params.name) cap.set("name", String(params.name));
        return { ok: true, message: "Captured playing clips into scene " + capturedIdx, scene_index: capturedIdx };
    }
    var count = Math.max(1, Number(params.count || 1));
    var names = String(params.name || "").split(",");
    var created = [];
    var i;
    for (i = 0; i < count; i++) {
        var sceneIdx = params.scene_index != null ? Number(params.scene_index) : (params.sceneIndex != null ? Number(params.sceneIndex) : -1);
        song.call("create_scene", sceneIdx);
        var createdIdx = sceneIdx >= 0 ? sceneIdx : (song.getcount("scenes") - 1);
        var sc = liveApi("live_set scenes " + createdIdx);
        var nm = names[i] || names[0];
        if (sc) {
            if (nm) sc.set("name", String(nm).replace(/^\s+|\s+$/g, ""));
            if (params.color) sc.set("color", hexToLiveColor(params.color));
        }
        created.push(createdIdx);
    }
    return { ok: true, message: "Created scene(s) " + created.join(", "), scene_index: created[0], scenes: created };
}

function palClipFromParams(params) {
    if (params.slot) {
        var slot = String(params.slot).split(",")[0];
        var parts = slot.split("/");
        return {
            track: Number(parts[0]),
            slot: Number(parts[1]),
            path: "live_set tracks " + Number(parts[0]) + " clip_slots " + Number(parts[1]) + " clip"
        };
    }
    var trackIdx = palTrackIndexFromParams(params, 0);
    var slotIdx = Number(params.slot_index != null ? params.slot_index : (params.slotIndex != null ? params.slotIndex : (params.clip_index != null ? params.clip_index : (params.clipIndex != null ? params.clipIndex : 0))));
    return {
        track: trackIdx,
        slot: slotIdx,
        path: "live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip"
    };
}

// Like palClipFromParams, but also accepts arrangement_clip_index/clip_index
// to address an Arrangement-timeline clip instead of a Session clip -- used
// by the automation/envelope tools, which previously only reached Session
// clips even though their sibling live_clear_clip_envelopes already
// accepted both (the asymmetry S1.3 fixes).
function palAutomationClipFromParams(params) {
    if (params.arrangement_clip_index != null || params.arrangementClipIndex != null) {
        var trackIdx = palTrackIndexFromParams(params, 0);
        var aIdx = Number(params.arrangement_clip_index != null ? params.arrangement_clip_index : params.arrangementClipIndex);
        return {
            track: trackIdx,
            slot: aIdx,
            is_arrangement: true,
            path: "live_set tracks " + trackIdx + " arrangement_clips " + aIdx
        };
    }
    var loc = palClipFromParams(params);
    loc.is_arrangement = false;
    return loc;
}

function palReadClip(params) {
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "No clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    var include = params.include || ["notes", "timing"];
    if (typeof include === "string") include = include.split(",");
    var wantAll = palIncludeHas(include, "*");
    var out = palClipOverview(clip, wantAll || palIncludeHas(include, "notes"));
    out.ok = true;
    out.track_index = loc.track;
    out.slot_index = loc.slot;
    if (wantAll || palIncludeHas(include, "timing")) {
        out.timing = {
            start_marker: Number(unwrap(clip.get("start_marker")) || 0),
            end_marker: Number(unwrap(clip.get("end_marker")) || 0),
            loop_start: Number(unwrap(clip.get("loop_start")) || 0),
            loop_end: Number(unwrap(clip.get("loop_end")) || 0),
            looping: !!unwrap(clip.get("looping"))
        };
    }
    if ((wantAll || palIncludeHas(include, "warp") || palIncludeHas(include, "sample")) && out.is_audio) {
        try { out.warp_mode = unwrap(clip.get("warp_mode")); } catch (e) {}
    }
    try { out.launch_mode = unwrap(clip.get("launch_mode")); } catch (eLm) {}
    try { out.launch_quantization = unwrap(clip.get("launch_quantization")); } catch (eLq) {}
    try { out.legato = !!unwrap(clip.get("legato")); } catch (eLeg) {}
    try { out.velocity_amount = unwrap(clip.get("velocity_amount")); } catch (eVa) {}
    try {
        var faNames = ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"];
        var faA = unwrap(clip.get("follow_action_a"));
        if (faA !== undefined && faA !== null) {
            out.follow_action_a = Number(faA);
            out.follow_action_a_name = (Number(faA) >= 0 && Number(faA) < faNames.length) ? faNames[Number(faA)] : "unknown";
        }
        var faB = unwrap(clip.get("follow_action_b"));
        if (faB !== undefined && faB !== null) {
            out.follow_action_b = Number(faB);
            out.follow_action_b_name = (Number(faB) >= 0 && Number(faB) < faNames.length) ? faNames[Number(faB)] : "unknown";
        }
        var faC = unwrap(clip.get("follow_action_chance"));
        if (faC !== undefined && faC !== null) out.follow_action_chance = Number(faC);
        var faT = unwrap(clip.get("follow_action_time"));
        if (faT !== undefined && faT !== null) out.follow_action_time = Number(faT);
        var faEn = unwrap(clip.get("follow_action_enabled"));
        if (faEn !== undefined && faEn !== null) out.follow_action_enabled = !!faEn;
    } catch (eFa) {}
    if (out.is_audio) {
        try { out.gain = unwrap(clip.get("gain")); } catch (eG) {}
        try { out.pitch_coarse = unwrap(clip.get("pitch_coarse")); } catch (eP) {}
        try { out.ram_mode = !!unwrap(clip.get("ram_mode")); } catch (eR) {}
        try { out.warping = !!unwrap(clip.get("warping")); } catch (eW) {}
        try { out.fade_in_start = unwrap(clip.get("fade_in_start")); } catch (eFis) {}
        try { out.fade_in_end = unwrap(clip.get("fade_in_end")); } catch (eFie) {}
        try { out.fade_out_start = unwrap(clip.get("fade_out_start")); } catch (eFos) {}
        try { out.fade_out_end = unwrap(clip.get("fade_out_end")); } catch (eFoe) {}
    }
    return out;
}

function palUpdateClip(params) {
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (params.name != null) clip.set("name", String(params.name));
    if (params.color != null) clip.set("color", hexToLiveColor(params.color));
    if (params.mute != null) clip.set("muted", params.mute ? 1 : 0);
    if (params.loop != null || params.looping != null) {
        clip.set("looping", (params.loop != null ? params.loop : params.looping) ? 1 : 0);
    }
    if (params.length_beats != null || params.length != null) {
        // clip.set("length") silently no-ops -- length is read-only on
        // Clip; loop_end is what actually resizes it (Low item, confirmed
        // 2026-08-20).
        var len = params.length_beats != null ? Number(params.length_beats) : palParseDuration(params.length, 4);
        clip.set("loop_end", len);
    }
    var ucNotApplied = [];
    if (params.warping != null) {
        if (!palSetChecked(clip, "warping", params.warping ? 1 : 0)) ucNotApplied.push("warping");
    }
    if (params.pitch != null || params.pitchShift != null || params.pitch_shift != null) {
        var pVal = params.pitch != null ? params.pitch : (params.pitchShift != null ? params.pitchShift : params.pitch_shift);
        if (!palSetChecked(clip, "pitch_coarse", Number(pVal))) ucNotApplied.push("pitch");
    }
    if (params.launch_mode != null || params.launchMode != null) {
        var lm = params.launch_mode != null ? params.launch_mode : params.launchMode;
        var lmMap = { "trigger": 0, "gate": 1, "toggle": 2, "repeat": 3 };
        if (typeof lm === "string" && lmMap[lm.toLowerCase()] != null) lm = lmMap[lm.toLowerCase()];
        if (!palSetChecked(clip, "launch_mode", Number(lm))) ucNotApplied.push("launch_mode");
    }
    if (params.launch_quantization != null || params.launchQuantization != null) {
        var lq = params.launch_quantization != null ? params.launch_quantization : params.launchQuantization;
        var lqMap = { "global": 0, "none": 1, "8_bars": 2, "8 bars": 2, "4_bars": 3, "4 bars": 3, "2_bars": 4, "2 bars": 4, "1_bar": 5, "1 bar": 5, "1/2": 6, "1/2t": 7, "1/4": 8, "1/4t": 9, "1/8": 10, "1/8t": 11, "1/16": 12, "1/16t": 13, "1/32": 14 };
        if (typeof lq === "string" && lqMap[lq.toLowerCase()] != null) lq = lqMap[lq.toLowerCase()];
        if (!palSetChecked(clip, "launch_quantization", Number(lq))) ucNotApplied.push("launch_quantization");
    }
    if (params.legato != null) {
        if (!palSetChecked(clip, "legato", params.legato ? 1 : 0)) ucNotApplied.push("legato");
    }
    if (params.start_marker != null) {
        try { clip.set("start_marker", Number(params.start_marker)); } catch (eSm) {}
    }
    if (params.end_marker != null) {
        try { clip.set("end_marker", Number(params.end_marker)); } catch (eEm) {}
    }
    if (params.fade_in_start != null && !palSetChecked(clip, "fade_in_start", Number(params.fade_in_start))) ucNotApplied.push("fade_in_start");
    if (params.fade_in_end != null && !palSetChecked(clip, "fade_in_end", Number(params.fade_in_end))) ucNotApplied.push("fade_in_end");
    if (params.fade_out_start != null && !palSetChecked(clip, "fade_out_start", Number(params.fade_out_start))) ucNotApplied.push("fade_out_start");
    if (params.fade_out_end != null && !palSetChecked(clip, "fade_out_end", Number(params.fade_out_end))) ucNotApplied.push("fade_out_end");
    var faActionMap = { "none": 0, "stop": 1, "again": 2, "previous": 3, "prev": 3, "next": 4, "first": 5, "last": 6, "any": 7, "other": 8, "jump": 9 };
    if (params.follow_action_a != null || params.action_a != null) {
        var actA = params.follow_action_a != null ? params.follow_action_a : params.action_a;
        if (typeof actA === "string" && faActionMap[actA.toLowerCase()] != null) actA = faActionMap[actA.toLowerCase()];
        if (!palSetChecked(clip, "follow_action_a", Number(actA))) ucNotApplied.push("follow_action_a");
    }
    if (params.follow_action_b != null || params.action_b != null) {
        var actB = params.follow_action_b != null ? params.follow_action_b : params.action_b;
        if (typeof actB === "string" && faActionMap[actB.toLowerCase()] != null) actB = faActionMap[actB.toLowerCase()];
        if (!palSetChecked(clip, "follow_action_b", Number(actB))) ucNotApplied.push("follow_action_b");
    }
    if (params.follow_action_chance != null || params.chance != null) {
        var actCh = params.follow_action_chance != null ? params.follow_action_chance : params.chance;
        if (!palSetChecked(clip, "follow_action_chance", Math.max(0, Math.min(1, Number(actCh))))) ucNotApplied.push("follow_action_chance");
    }
    if (params.follow_action_time != null || params.time != null) {
        var actTm = params.follow_action_time != null ? params.follow_action_time : params.time;
        if (!palSetChecked(clip, "follow_action_time", Number(actTm))) ucNotApplied.push("follow_action_time");
    }
    if (params.follow_action_enabled != null || params.enabled != null) {
        var actEn = (params.follow_action_enabled != null ? params.follow_action_enabled : params.enabled) ? 1 : 0;
        if (!palSetChecked(clip, "follow_action_enabled", actEn)) ucNotApplied.push("follow_action_enabled");
    }
    if (params.velocity_amount != null || params.velocityAmount != null) {
        var vaVal = Number(params.velocity_amount != null ? params.velocity_amount : params.velocityAmount);
        if (!palSetChecked(clip, "velocity_amount", vaVal)) ucNotApplied.push("velocity_amount");
    }
    if (params.gain != null) {
        if (!palSetChecked(clip, "gain", Number(params.gain))) ucNotApplied.push("gain");
    }
    if (params.warp_mode != null || params.warpMode != null) {
        var wm = params.warp_mode != null ? params.warp_mode : params.warpMode;
        var wmMap = { "beats": 0, "tones": 1, "texture": 2, "re-pitch": 3, "repitch": 3, "complex": 4, "complex_pro": 6, "complexpro": 6 };
        if (typeof wm === "string" && wmMap[wm.toLowerCase()] != null) wm = wmMap[wm.toLowerCase()];
        if (!palSetChecked(clip, "warp_mode", Number(wm))) ucNotApplied.push("warp_mode");
    }
    if (params.ram_mode != null || params.ramMode != null) {
        var rm = (params.ram_mode != null ? params.ram_mode : params.ramMode) ? 1 : 0;
        if (!palSetChecked(clip, "ram_mode", rm)) ucNotApplied.push("ram_mode");
    }
    if (params.notes) {
        var song = liveApi("live_set");
        var bpb = song ? Number(unwrap(song.get("signature_numerator")) || 4) : 4;
        var notes = palParseNotes(params.notes, bpb);
        writeNotes(clip, notes, params.replace !== false);
    }
    if (params.quantize != null) {
        try {
            clip.call("quantize", 5, Number(params.quantize));
        } catch (e3) {}
    }
    var ucResult = { ok: true, message: "Updated clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (ucNotApplied.length) {
        ucResult.not_applied = ucNotApplied;
        ucResult.message += " (some fields not applied)";
    }
    return ucResult;
}

function palCreateClip(params) {
    var song = liveApi("live_set");
    var bpb = song ? Number(unwrap(song.get("signature_numerator")) || 4) : 4;
    var trackIdx = palTrackIndexFromParams(params, 0);
    var slotIdx = Number(params.slot_index != null ? params.slot_index : 0);
    if (params.slot) {
        var sp = String(params.slot).split(",")[0].split("/");
        trackIdx = Number(sp[0]);
        slotIdx = Number(sp[1]);
    }
    var sampleFile = params.sampleFile || params.sample_file;
    var arrStart = params.arrangementStart || params.arrangement_start;

    if (arrStart != null) {
        var track = liveApi("live_set tracks " + trackIdx);
        if (!track) return { ok: false, error: "Track " + trackIdx + " not found" };
        var startBeats = palBarBeatToBeats(arrStart, bpb);
        var length = params.length_beats != null ? Number(params.length_beats) : palParseDuration(params.length || "4bar", bpb);
        try {
            if (sampleFile) track.call("create_audio_clip", String(sampleFile), startBeats);
            else track.call("create_midi_clip", startBeats, length);
        } catch (e) {
            return { ok: false, error: "Could not create arrangement clip: " + e };
        }
        return { ok: true, message: "Created arrangement clip on track " + trackIdx + " at " + arrStart };
    }

    var slot = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
    if (!slot) return { ok: false, error: "Clip slot " + trackIdx + "/" + slotIdx + " not found" };
    if (unwrap(slot.get("has_clip"))) slot.call("delete_clip");

    if (sampleFile) {
        palSelectTrack("live_set tracks " + trackIdx);
        var view = liveApi("live_set view");
        try {
            var slotApi = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx);
            if (view && slotApi) view.set("highlighted_clip_slot", "id", extractId(slotApi.id));
        } catch (e2) {}
        // ClipSlot.create_audio_clip(path) is the real, documented LOM method.
        try { slot.call("create_audio_clip", String(sampleFile)); } catch (e3) {}
        var audioClip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
        if (audioClip) {
            if (params.name) audioClip.set("name", String(params.name));
            if (params.color) audioClip.set("color", hexToLiveColor(params.color));
            return { ok: true, message: "Created audio clip at track " + trackIdx + ", slot " + slotIdx, track_index: trackIdx, slot_index: slotIdx };
        }
        return { ok: false, error: "Could not create audio clip from " + sampleFile };
    }

    var len = params.length_beats != null ? Number(params.length_beats) : palParseDuration(params.length || "4bar", bpb);
    slot.call("create_clip", len);
    var clip = liveApi("live_set tracks " + trackIdx + " clip_slots " + slotIdx + " clip");
    if (clip) {
        if (params.name) clip.set("name", String(params.name));
        if (params.color) clip.set("color", hexToLiveColor(params.color));
        if (params.looping != null) clip.set("looping", params.looping ? 1 : 0);
        if (params.notes) writeNotes(clip, palParseNotes(params.notes, bpb), true);
    }
    if (params.auto === "play-clip" && clip) {
        try { clip.call("fire"); } catch (e4) {}
    }
    if (params.auto === "play-scene") {
        var sc = liveApi("live_set scenes " + slotIdx);
        if (sc) try { sc.call("fire"); } catch (e5) {}
    }
    return {
        ok: true,
        message: "Created clip at track " + trackIdx + ", slot " + slotIdx + " (" + len + " beats)",
        track_index: trackIdx,
        slot_index: slotIdx,
        length_beats: len
    };
}

function palFindDevice(params) {
    if (params.path) {
        var parsed = palParseDevicePath(params.path.split(",")[0]);
        if (parsed) return parsed;
    }
    var loc = palTrackPath(params);
    var idx = Number(params.device_index != null ? params.device_index : (params.deviceIndex != null ? params.deviceIndex : 0));
    return {
        trackPath: loc.path, devicePath: loc.path + " devices " + idx, deviceIndex: idx,
        trackIndex: loc.index, trackResolvedBy: loc.resolved_by, trackName: loc.name
    };
}

function palParseDevicePath(raw) {
    var s = String(raw || "").replace(/^\s+|\s+$/g, "");
    var trackKind = "";
    var trackIdx = 0;
    var m = s.match(/^t(\d+)/i);
    var rm = s.match(/^r(\d+)/i);
    if (m) trackIdx = parseInt(m[1], 10);
    else if (rm) {
        trackKind = "return";
        trackIdx = parseInt(rm[1], 10);
    } else if (/^master/i.test(s)) {
        trackKind = "master";
    } else return null;
    var trackPath = trackKind === "return"
        ? "live_set return_tracks " + trackIdx
        : (trackKind === "master" ? "live_set master_track" : "live_set tracks " + trackIdx);
    var devicePath = trackPath;
    var parts = s.split("/");
    var i;
    for (i = 1; i < parts.length; i++) {
        var p = parts[i];
        var dm = p.match(/^d(\d+)$/i);
        var cm = p.match(/^c(\d+)$/i);
        var pm = p.match(/^p([A-Ga-g][#b]?-?\d+)$/i);
        var pnum = p.match(/^p(\d+)$/i);
        if (dm) devicePath += " devices " + dm[1];
        else if (cm) devicePath += " chains " + cm[1];
        else if (pm) {
            var note = palNoteToPitch(pm[1]);
            devicePath += " drum_pads " + note;
        } else if (pnum) devicePath += " drum_pads " + pnum[1];
    }
    return { trackPath: trackPath, devicePath: devicePath };
}

function palReadDevice(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path (e.g. t0/d0) or track_index + device_index" };
    if (loc.trackResolvedBy === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.trackName + "'" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found at " + loc.devicePath };
    var include = params.include || ["params"];
    if (typeof include === "string") include = include.split(",");
    var wantAll = palIncludeHas(include, "*");
    var out = {
        ok: true,
        path: loc.devicePath,
        name: String(unwrap(device.get("name")) || ""),
        class_name: String(unwrap(device.get("class_name")) || ""),
        class_display_name: String(unwrap(device.get("class_display_name")) || ""),
        is_active: !!unwrap(device.get("is_active")),
        can_have_chains: !!unwrap(device.get("can_have_chains")),
        can_have_drum_pads: !!unwrap(device.get("can_have_drum_pads"))
    };
    if (wantAll || palIncludeHas(include, "params") || palIncludeHas(include, "param-values")) {
        out.params = palDeviceParams(device, params.paramSearch || params.param_search);
    }
    if ((wantAll || palIncludeHas(include, "chains")) && out.can_have_chains) {
        out.chains = palDeviceChains(loc.devicePath);
    }
    if ((wantAll || palIncludeHas(include, "drum-pads") || palIncludeHas(include, "drum-map")) && out.can_have_drum_pads) {
        var parentTrack = loc.trackPath;
        var dMatch = loc.devicePath.match(/devices (\d+)/);
        var dIdx = dMatch ? Number(dMatch[1]) : 0;
        out.drum_map = palDrumMap(parentTrack, dIdx);
    }
    return out;
}

function palDeviceParams(device, search) {
    var n = 0;
    try { n = device.getcount("parameters"); } catch (e) { return []; }
    var needle = String(search || "").toLowerCase();
    var params = [];
    var i;
    var base = device.unquotedpath || device.path;
    for (i = 0; i < n; i++) {
        var p = liveApi(base + " parameters " + i);
        if (!p) continue;
        var pname = String(unwrap(p.get("name")) || "");
        if (needle && pname.toLowerCase().indexOf(needle) === -1) continue;
        var item = {
            index: i,
            name: pname,
            value: Number(unwrap(p.get("value"))),
            min: Number(unwrap(p.get("min"))),
            max: Number(unwrap(p.get("max")))
        };
        // str_for_value(value) formats the CURRENT value on demand and is
        // reliable; the value_string property is a stale/wrong cache for
        // some parameter types in M4L (H8/S1.3.4).
        try { item.value_string = String(unwrap(p.call("str_for_value", item.value)) || ""); } catch (e2) {}
        params.push(item);
    }
    return params;
}

function palDeviceChains(devicePath) {
    var rack = liveApi(devicePath);
    if (!rack) return [];
    var n = 0;
    try { n = rack.getcount("chains"); } catch (e) { return []; }
    var out = [];
    var i;
    for (i = 0; i < n; i++) {
        var c = liveApi(devicePath + " chains " + i);
        if (!c) continue;
        out.push({
            index: i,
            name: String(unwrap(c.get("name")) || ""),
            devices: palDescribeDevices(devicePath + " chains " + i)
        });
    }
    return out;
}

// LiveAPI's set("value_string", ...) is a silent no-op for DeviceParameter
// (H8) -- it never throws, so a try/catch fallback around it never runs and
// the caller wrongly sees "applied". There is also no LOM setter that takes
// display text directly for a continuous (non-quantized) parameter. So:
// quantized params (value_items non-empty) match the text against the item
// list and set the index; continuous params parse a leading number out of
// the text (e.g. "-6 dB" -> -6) and bisect str_for_value() to find the raw
// value whose displayed number is closest.
function palLeadingNumber(text) {
    var m = String(text == null ? "" : text).match(/-?\d+(\.\d+)?/);
    return m ? Number(m[0]) : NaN;
}

function palValueItemIndex(p, text) {
    var items = null;
    try { items = unwrap(p.get("value_items")); } catch (e) { items = null; }
    if (!items || !items.length) return null;
    var needle = String(text).toLowerCase().replace(/^\s+|\s+$/g, "");
    for (var i = 0; i < items.length; i++) {
        if (String(items[i]).toLowerCase() === needle) return i;
    }
    return null;
}

function palValueForDisplayString(p, text, minVal, maxVal) {
    var target = palLeadingNumber(text);
    if (isNaN(target) || isNaN(minVal) || isNaN(maxVal) || minVal === maxVal || !p.call) return null;
    function numAt(v) { return palLeadingNumber(unwrap(p.call("str_for_value", v))); }
    var lowNum = numAt(minVal);
    var highNum = numAt(maxVal);
    if (isNaN(lowNum) || isNaN(highNum)) return null;
    var ascending = highNum >= lowNum;
    var lo = minVal, hi = maxVal, best = minVal, bestDist = Infinity;
    for (var iter = 0; iter < 24; iter++) {
        var mid = (lo + hi) / 2;
        var midNum = numAt(mid);
        if (isNaN(midNum)) break;
        var dist = Math.abs(midNum - target);
        if (dist < bestDist) { bestDist = dist; best = mid; }
        if (ascending ? midNum < target : midNum > target) lo = mid; else hi = mid;
    }
    if (bestDist > 0) return best; // never landed exactly on target's rounded text -- closest we found

    // Many raw values can round to the same displayed number (e.g. a wide
    // "40%" band on Delay Feedback) -- a naive bisection can land right at
    // that band's edge instead of its middle, and a later re-read then
    // rounds the OTHER way (H8: asked for 40%, read back as 38%). Widen
    // outward from `best` in both directions to find the band's true edges
    // and return their midpoint so the written value re-reads stably.
    function edgeToward(extreme) {
        var inside = best, outside = extreme;
        if (numAt(outside) === target) return outside; // whole rest of the range is still target
        for (var i = 0; i < 24; i++) {
            var mid = (inside + outside) / 2;
            if (numAt(mid) === target) inside = mid; else outside = mid;
        }
        return inside;
    }
    var edgeLow = edgeToward(minVal);
    var edgeHigh = edgeToward(maxVal);
    return (edgeLow + edgeHigh) / 2;
}

// Resolves `rawValue` (number or display-unit string) to a settable raw
// float and writes it, clamped to [minVal, maxVal]. Returns
// { ok, display_after, value_after } -- ok is true only when the
// post-write DISPLAYED number matches what was actually requested (when
// rawValue was display text), not merely "the raw value changed from
// before" -- H8: a value that rounds to a neighboring display band (e.g.
// requesting Delay Feedback "40%" and landing at a raw value that reads
// back as "38%") used to report success anyway.
// Attempts the direct display_value write path -- display_value is a real,
// settable DeviceParameter FLOAT property ("the current value as visible in
// the GUI"), confirmed live via the v1.0.39 probe runbook (Part B probe 1:
// two distinct targets both landed within 1.0 of a quantized parameter's
// nearest legal step on a real running Live 12.4.15b3). Where the raw value
// scale differs from the displayed number (e.g. dB), this is exact; the old
// str_for_value bisection could only converge to the nearest displayed band.
// Returns null (never throws) if display_value doesn't move at all despite a
// real requested change -- LiveAPI .set() never throws on an unsupported
// property (M1), so a silent no-op read-back is the only honest signal that
// this path isn't supported here, and the caller falls back to the bisection.
function palTryDisplayValue(p, requestedNum, minVal, maxVal) {
    var target = requestedNum;
    if (!isNaN(minVal) && !isNaN(maxVal) && maxVal > minVal) {
        target = Math.max(minVal, Math.min(maxVal, target));
    }
    var beforeDv;
    try { beforeDv = Number(unwrap(p.get("display_value"))); } catch (e) { return null; }
    if (isNaN(beforeDv)) return null;
    try { p.set("display_value", target); } catch (e2) { return null; }
    var afterDv;
    try { afterDv = Number(unwrap(p.get("display_value"))); } catch (e3) { return null; }
    if (isNaN(afterDv)) return null;
    if (Math.abs(afterDv - beforeDv) < 1e-6 && Math.abs(beforeDv - target) > 0.5) return null;
    if (Math.abs(afterDv - target) > 1.0) return null;
    var valueAfter = Number(unwrap(p.get("value")));
    var displayAfter = null;
    try { displayAfter = String(unwrap(p.call("str_for_value", valueAfter)) || ""); } catch (e4) {}
    return { ok: true, display_after: displayAfter, value_after: valueAfter };
}

function palApplyParamValue(p, rawValue, minVal, maxVal) {
    var beforeVal = Number(unwrap(p.get("value")));
    var num = Number(rawValue);
    var isPlainNumber = !isNaN(num) && String(rawValue).replace(/^\s+|\s+$/g, "") !== "" &&
        String(rawValue).indexOf(" ") === -1 && !/^[A-Ga-g]/i.test(String(rawValue));
    var requestedNum = isPlainNumber ? null : palLeadingNumber(rawValue);
    var finalVal;
    if (isPlainNumber) {
        finalVal = num;
    } else {
        var itemIdx = palValueItemIndex(p, rawValue);
        if (itemIdx != null) {
            finalVal = itemIdx;
        } else {
            if (requestedNum != null && !isNaN(requestedNum)) {
                var dvResult = palTryDisplayValue(p, requestedNum, minVal, maxVal);
                if (dvResult) return dvResult;
            }
            finalVal = palValueForDisplayString(p, rawValue, minVal, maxVal);
            if (finalVal == null) return { ok: false, display_after: null, value_after: beforeVal };
        }
    }
    if (!isNaN(minVal) && !isNaN(maxVal) && maxVal > minVal) {
        finalVal = Math.max(minVal, Math.min(maxVal, finalVal));
    }
    try { p.set("value", finalVal); } catch (eSet) {
        return { ok: false, display_after: null, value_after: beforeVal };
    }
    var afterVal = Number(unwrap(p.get("value")));
    var displayAfter = null;
    try { displayAfter = String(unwrap(p.call("str_for_value", afterVal)) || ""); } catch (eDisp) {}
    var ok;
    if (requestedNum != null && !isNaN(requestedNum)) {
        // rawValue named a display number -- success means the write
        // actually landed on that number, not just "value moved".
        ok = !isNaN(palLeadingNumber(displayAfter)) && palLeadingNumber(displayAfter) === requestedNum;
    } else if (Math.abs(afterVal - finalVal) < 1e-6) {
        ok = true;
    } else {
        // Some quantized/stepped params round to the nearest valid step --
        // treat "changed from before" as success too when there was no
        // display text to hold it to.
        ok = Math.abs(afterVal - beforeVal) > 1e-6;
    }
    return { ok: ok, display_after: displayAfter, value_after: afterVal };
}

// Returns { ok, display_after } -- see palApplyParamValue for what "ok"
// actually verifies (the post-write DISPLAYED number, not just "it moved").
function palSetDeviceParamVerbose(device, name, value) {
    var params = palDeviceParams(device, "");
    var needle = String(name || "").toLowerCase();
    var i;
    for (i = 0; i < params.length; i++) {
        if (params[i].name.toLowerCase() === needle || String(params[i].index) === needle) {
            var p = liveApi((device.unquotedpath || device.path) + " parameters " + params[i].index);
            if (!p) return { ok: false, display_after: null };
            var applied = palApplyParamValue(p, value, params[i].min, params[i].max);
            return { ok: applied.ok, display_after: applied.display_after };
        }
    }
    return { ok: false, display_after: null };
}

// Shared by palAssignDeviceSample and palAssignPadSample below. Max's LiveAPI.call
// on a rejected or missing method typically posts to the Max Console instead of
// throwing, so a replace_sample call() that raised nothing is not proof the file
// loaded -- these read the device's own sample.file_path back and compare it to
// what was actually requested (same idiom as palClipOverview's audio-clip read),
// and build an honest failure report when it doesn't match: the real exception (if
// any), what the device actually holds now, the running version ONLY when it
// genuinely is below 12.4 (never asserted as the cause otherwise, since we do not
// know why it failed until the read-back says so), and the working alternatives so
// the model's next move is another tool call, not a hand-off to the user.
function palPathsMatch(a, b) {
    function norm(p) { return String(p || "").replace(/\\/g, "/").toLowerCase(); }
    var na = norm(a), nb = norm(b);
    if (!na || !nb) return false;
    if (na === nb) return true;
    var partsA = na.split("/");
    var partsB = nb.split("/");
    return partsA[partsA.length - 1] === partsB[partsB.length - 1];
}

function palReadBackSampleFile(devicePath) {
    try {
        var sample = liveApi(devicePath + " sample");
        if (sample) return String(unwrap(sample.get("file_path")) || "");
    } catch (e) {}
    return "";
}

function palLiveVersionString() {
    try {
        var app = liveApi("live_app");
        if (app) return String(unwrap(app.call("get_version_string")) || "");
    } catch (e) {}
    return "";
}

// True/false against a parsed "major.minor" prefix, or null when the version
// string can't be parsed -- null must never be treated as "too old".
function palVersionAtLeast(versionString, major, minor) {
    var m = String(versionString || "").match(/(\d+)\.(\d+)/);
    if (!m) return null;
    var vMajor = parseInt(m[1], 10);
    var vMinor = parseInt(m[2], 10);
    if (vMajor !== major) return vMajor > major;
    return vMinor >= minor;
}

function palSampleLoadFailure(target, absolutePath, loadedPath, callError) {
    var versionString = palLiveVersionString();
    var tooOld = palVersionAtLeast(versionString, 12, 4) === false;

    var reason;
    if (callError) {
        reason = String(callError);
    } else if (loadedPath) {
        reason = "the device's sample is '" + loadedPath + "', not the requested file";
    } else {
        reason = "the device reports no sample loaded";
    }

    var msg = "could not load '" + absolutePath + "' into " + target + ": " + reason + ".";
    if (tooOld) {
        msg += " Running Live " + versionString + " -- SimplerDevice.replace_sample needs Live 12.4+.";
    }
    msg += " Try live_create_clip with sample_file on an audio track, or live_load_browser_item.";

    return { ok: false, error: msg, file_path: loadedPath };
}

// Loads a sample onto a Drum Rack pad with no Browser/BrowserItem access --
// that class genuinely still doesn't exist in the Max for Live LOM. Instead:
// find or create the DrumChain for the pad's note (RackDevice.insert_chain,
// Live 12.3+), put a Simpler on it (Chain.insert_device, Live 12.3+, native
// devices only), then load the file by absolute path (SimplerDevice.replace_sample)
// and verify it actually landed via read-back -- see palSampleLoadFailure above.
function palAssignPadSample(rackPath, rack, noteToken, absolutePath) {
    var note = palNoteToPitch(noteToken);
    if (isNaN(note)) return { ok: false, error: "could not parse pad note '" + noteToken + "'" };
    absolutePath = String(absolutePath || "").replace(/^\s+|\s+$/g, "");
    if (!absolutePath) return { ok: false, error: "no sample file path given" };

    var chainCount = 0;
    try { chainCount = rack.getcount("chains"); } catch (e) {
        return { ok: false, error: "could not read Rack chains (requires Live 12.3+): " + String(e) };
    }

    var chainPath = null;
    var i;
    for (i = 0; i < chainCount; i++) {
        var c = liveApi(rackPath + " chains " + i);
        if (c && Number(unwrap(c.get("in_note"))) === note) {
            chainPath = rackPath + " chains " + i;
            break;
        }
    }

    if (!chainPath) {
        try {
            rack.call("insert_chain");
        } catch (e2) {
            return { ok: false, error: "could not add a Drum Rack chain (requires Live 12.3+): " + String(e2) };
        }
        var newCount = 0;
        try { newCount = rack.getcount("chains"); } catch (e3) { newCount = 0; }
        chainPath = rackPath + " chains " + (newCount - 1);
        var newChain = liveApi(chainPath);
        if (!newChain) return { ok: false, error: "could not access the new Rack chain" };
        try { newChain.set("in_note", note); } catch (e4) {
            return { ok: false, error: "could not assign pad note to the new chain: " + String(e4) };
        }
    }

    var chain = liveApi(chainPath);
    if (!chain) return { ok: false, error: "could not access the chain for pad " + noteToken };

    var devCount = 0;
    try { devCount = chain.getcount("devices"); } catch (e5) { devCount = 0; }
    if (devCount === 0) {
        try {
            chain.call("insert_device", "Simpler");
        } catch (e6) {
            return { ok: false, error: "could not insert Simpler onto pad " + noteToken + " (requires Live 12.3+): " + String(e6) };
        }
        try { devCount = chain.getcount("devices"); } catch (e7) { devCount = 0; }
    }
    if (devCount === 0) {
        return { ok: false, error: "Simpler was not inserted onto pad " + noteToken };
    }

    var simplerPath = chainPath + " devices " + (devCount - 1);
    var simpler = liveApi(simplerPath);
    if (!simpler) return { ok: false, error: "could not access the device on pad " + noteToken };

    var callError = null;
    try {
        simpler.call("replace_sample", absolutePath);
    } catch (e8) {
        callError = e8;
    }

    var loadedPath = palReadBackSampleFile(simplerPath);
    if (loadedPath && palPathsMatch(loadedPath, absolutePath)) {
        return { ok: true, message: "Loaded sample onto pad " + noteToken + " (" + loadedPath + ")" };
    }

    return palSampleLoadFailure("pad " + noteToken, absolutePath, loadedPath, callError);
}

// Loads a sample into a Simpler that is already on a track (or on a rack chain),
// which palAssignPadSample above only does for a Drum Rack pad. Same underlying
// method -- SimplerDevice.replace_sample -- reached by addressing the device
// directly instead of a pad note, so a plain "MIDI track + Simpler" layout finally
// has a way in. Verifies via read-back, same as palAssignPadSample.
//
// Simpler only, on purpose: replace_sample is a SimplerDevice method and Sampler has
// no LOM equivalent, so the class is checked first and the refusal names the real
// reason rather than surfacing a bare LiveAPI error.
function palAssignDeviceSample(device, absolutePath) {
    absolutePath = String(absolutePath || "").replace(/^\s+|\s+$/g, "");
    if (!absolutePath) return { ok: false, error: "no sample file path given" };

    var className = "";
    try { className = String(unwrap(device.get("class_name")) || ""); } catch (e) { className = ""; }
    if (className && className.indexOf("Simpler") < 0) {
        return {
            ok: false,
            error: "device is a " + className + ", not a Simpler -- only Simpler can load a sample by " +
                "path (Sampler has no LOM method for it). Put a Simpler on the track, or load the file " +
                "as an audio clip instead"
        };
    }

    var callError = null;
    try {
        device.call("replace_sample", absolutePath);
    } catch (e2) {
        callError = e2;
    }

    var devicePath = device.unquotedpath || device.path;
    var loadedPath = palReadBackSampleFile(devicePath);
    if (loadedPath && palPathsMatch(loadedPath, absolutePath)) {
        return { ok: true, message: "Loaded sample into " + (className || "device") + " (" + loadedPath + ")" };
    }

    return palSampleLoadFailure(className || "the device", absolutePath, loadedPath, callError);
}

function palUpdateDevice(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path or track_index + device_index" };
    if (loc.trackResolvedBy === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.trackName + "'" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found" };
    if (params.name != null) {
        try { device.set("name", String(params.name)); } catch (e) {}
    }
    if (params.is_active != null) {
        try { device.set("is_active", params.is_active ? 1 : 0); } catch (e2) {}
    }
    if (params.is_collapsed != null || params.collapsed != null) {
        try { device.set("is_collapsed", (params.is_collapsed != null ? params.is_collapsed : params.collapsed) ? 1 : 0); } catch (eColl) {}
    }
    var applied = [];
    var skipped = [];
    var displayAfter = {};
    var plist = params.params;
    if (plist && plist.length) {
        var i;
        for (i = 0; i < plist.length; i++) {
            var item = plist[i] || {};
            var pname = String(item.name || "");
            var pval = item.value;
            var pad = pname.match(/^p([A-Ga-g][#b]?-?\d+|C\d+)\/(.*)$/i);
            if (pad && (pad[2] === "sample" || pad[2].indexOf("sample") >= 0)) {
                var padResult = palAssignPadSample(loc.devicePath, device, pad[1], pval);
                if (padResult && padResult.ok) applied.push(pname);
                else skipped.push(pname + " (" + ((padResult && padResult.error) || "could not load sample") + ")");
                continue;
            }
            var lowerName = pname.toLowerCase();
            if (lowerName === "sample" || lowerName === "sample_file" || lowerName === "samplefile") {
                var sampleResult = palAssignDeviceSample(device, pval);
                if (sampleResult && sampleResult.ok) applied.push(pname);
                else skipped.push(pname + " (" + ((sampleResult && sampleResult.error) || "could not load sample") + ")");
                continue;
            }
            var setResult = palSetDeviceParamVerbose(device, pname, pval);
            if (setResult.ok) {
                applied.push(pname);
                if (setResult.display_after != null) displayAfter[pname] = setResult.display_after;
            } else {
                skipped.push(pname);
            }
        }
    }
    if (params.mute != null) {
        try { device.set("mute", params.mute ? 1 : 0); } catch (e3) {}
    }
    if (params.solo != null) {
        try { device.set("solo", params.solo ? 1 : 0); } catch (e4) {}
    }
    var result = { ok: skipped.length === 0, message: "Updated device '" + unwrap(device.get("name")) + "'", params_set: applied };
    if (skipped.length) result.params_skipped = skipped;
    var hasDisplayAfter = false;
    for (var dispKey in displayAfter) { if (displayAfter.hasOwnProperty(dispKey)) { hasDisplayAfter = true; break; } }
    if (hasDisplayAfter) result.display_after = displayAfter;
    return result;
}

// There is still no Browser / BrowserItem class in the Live Object Model
// exposed to Max for Live, so nothing here can walk Live's browser -- packs,
// presets, plug-ins stay drag-and-drop only. Loading a sample onto a Drum
// Rack pad doesn't need the browser though: see palAssignPadSample (chain
// insert + Simpler + SimplerDevice.replace_sample, Live 12.3/12.4+). This
// list is the fixed set of names Track.insert_device()/Chain.insert_device()
// can actually insert (Live 12.3+, native devices only -- Max for Live
// devices and plug-ins are never eligible).
var PAL_NATIVE_DEVICES = [
    "Analog", "Collision", "Drift", "Drum Rack", "Drum Cell", "Drum Sampler", "Electric",
    "External Instrument", "Impulse", "Meld", "Operator", "Sampler", "Simpler",
    "Tension", "Wavetable",
    "Instrument Rack", "Audio Effect Rack", "MIDI Effect Rack",
    "Delay", "Echo", "Filter Delay", "Grain Delay",
    "Compressor", "Gate", "Glue Compressor", "Limiter", "Multiband Dynamics",
    "Channel EQ", "EQ Eight", "EQ Three",
    "Amp", "Cabinet", "Drum Buss", "Dynamic Tube", "Erosion", "Overdrive",
    "Pedal", "Redux", "Roar", "Saturator", "Vinyl Distortion",
    "Auto Filter", "Auto Pan", "Auto Shift", "Chorus-Ensemble", "Corpus",
    "Phaser-Flanger", "Resonators", "Shifter",
    "Hybrid Reverb", "Reverb",
    "Spectral Resonator", "Spectral Time", "Vocoder",
    "Beat Repeat", "Looper",
    "External Audio Effect", "Spectrum", "Tuner", "Utility",
    "Arpeggiator", "CC Control", "Chord", "Note Length", "Pitch", "Random",
    "Scale", "Velocity"
];

function palCreateDevice(params, actionName) {
    if (actionName === "list_devices" || !params.device_name && !params.deviceName && !params.name && actionName !== "load_drum_rack") {
        return {
            ok: true,
            message: "Native devices insert_device can add by name (Live 12.3+; Max for Live devices and plug-ins are never eligible)",
            devices: PAL_NATIVE_DEVICES
        };
    }
    var loc = palTrackPath(params);
    if (loc.resolved_by === "name_not_found") return { ok: false, error: "No track found matching name '" + loc.name + "'" };
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found" };
    var devName = String(params.device_name || params.deviceName || params.name || (actionName === "load_drum_rack" ? "Drum Rack" : ""));
    if (!devName) return { ok: false, error: "Provide device_name (or omit it to list devices)" };
    palSelectTrack(loc.path);
    var before = track.getcount("devices");
    var result = loadDeviceOntoTrack(loc.index, devName);
    var after = track.getcount("devices");
    if (params.params && after > before) {
        var updateResult = palUpdateDevice({
            track_index: loc.index,
            device_index: after - 1,
            params: params.params
        });
        if (updateResult) {
            if (updateResult.params_set) result.params_set = updateResult.params_set;
            if (updateResult.params_skipped) result.params_skipped = updateResult.params_skipped;
        }
    }
    if (result && result.ok === false && after <= before) return result;
    return result || { ok: true, message: "Requested '" + devName + "' on track " + loc.index, track_index: loc.index };
}

function palDelete(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var type = String(params.type || "clip").toLowerCase();
    if (type === "track") {
        var loc = palTrackPath(params);
        if (loc.kind === "return") song.call("delete_return_track", loc.index);
        else song.call("delete_track", loc.index);
        return { ok: true, message: "Deleted " + (loc.kind || "track") + " " + loc.index };
    }
    if (type === "clip") {
        var cloc = palClipFromParams(params);
        var slot = liveApi("live_set tracks " + cloc.track + " clip_slots " + cloc.slot);
        if (slot) slot.call("delete_clip");
        return { ok: true, message: "Deleted clip at track " + palLiveNum(cloc.track) + ", slot " + palLiveNum(cloc.slot) };
    }
    if (type === "arrangement_clip" || type === "arrangement-clip") {
        var trkIdx = Number(params.track_index != null ? params.track_index : (params.trackIndex != null ? params.trackIndex : 0));
        var track = liveApi("live_set tracks " + trkIdx);
        if (!track) return { ok: false, error: "Track " + trkIdx + " not found" };
        var clipIdx = params.clip_index != null ? Number(params.clip_index) : (params.clipIndex != null ? Number(params.clipIndex) : -1);
        var clip = null;
        if (clipIdx >= 0) {
            clip = liveApi("live_set tracks " + trkIdx + " arrangement_clips " + clipIdx);
        } else if (params.clip_id || params.id) {
            clip = liveApi("id " + (params.clip_id || params.id));
        }
        if (!clip) return { ok: false, error: "Arrangement clip not found on track " + trkIdx };
        try {
            track.call("delete_clip", "id", extractId(clip.id));
            return { ok: true, message: "Deleted arrangement clip on track " + trkIdx };
        } catch (e1) {
            try {
                track.call("delete_clip", clip);
                return { ok: true, message: "Deleted arrangement clip on track " + trkIdx };
            } catch (e2) {
                return { ok: false, error: "Could not delete arrangement clip: " + String(e2) };
            }
        }
    }
    if (type === "scene") {
        var sceneIdx = Number(params.scene_index != null ? params.scene_index : (params.sceneIndex != null ? params.sceneIndex : 0));
        song.call("delete_scene", sceneIdx);
        return { ok: true, message: "Deleted scene " + sceneIdx };
    }
    if (type === "device" || type === "drum-pad") {
        var dloc = palFindDevice(params);
        if (!dloc) return { ok: false, error: "Provide path for device delete" };
        var parentPath = dloc.devicePath.replace(/ devices \d+$/, "");
        var m = dloc.devicePath.match(/devices (\d+)$/);
        var parent = liveApi(parentPath);
        if (parent && m) {
            try { parent.call("delete_device", Number(m[1])); } catch (e) {
                return { ok: false, error: "Could not delete device: " + e };
            }
            return { ok: true, message: "Deleted device" };
        }
        return { ok: false, error: "Could not resolve device parent" };
    }
    return { ok: false, error: "Unknown delete type: " + type };
}

function palDuplicate(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var type = String(params.type || "clip").toLowerCase();
    if (type === "track") {
        var loc = palTrackPath(params);
        song.call("duplicate_track", loc.index);
        return { ok: true, message: "Duplicated track " + loc.index };
    }
    if (type === "scene") {
        var sceneIdx = Number(params.scene_index != null ? params.scene_index : (params.sceneIndex != null ? params.sceneIndex : 0));
        song.call("duplicate_scene", sceneIdx);
        return { ok: true, message: "Duplicated scene " + sceneIdx };
    }
    if (type === "clip") {
        var isArr = params.destination_time != null || params.destinationTime != null || params.arrangement_time != null || params.to_arrangement;
        if (isArr) {
            return palDuplicateToArrangement(params);
        }
        var cloc = palClipFromParams(params);
        var toSlot = Number(params.to_slot != null ? params.to_slot : (params.toSlot != null ? String(params.toSlot).split("/")[1] : cloc.slot + 1));
        var slot = liveApi("live_set tracks " + cloc.track + " clip_slots " + cloc.slot);
        var dest = liveApi("live_set tracks " + cloc.track + " clip_slots " + toSlot);
        if (slot && dest) {
            slot.call("duplicate_clip_to", "id", extractId(dest.id));
            return { ok: true, message: "Duplicated clip to slot " + toSlot };
        }
        return { ok: false, error: "Could not duplicate clip" };
    }
    if (type === "device") {
        return { ok: false, error: "Device duplicate: create the same native device on the destination track instead." };
    }
    return { ok: false, error: "Unknown duplicate type: " + type };
}

function palSelect(params) {
    var view = liveApi("live_set view");
    if (!view) return { ok: false, error: "No Live view" };
    if (params.view) {
        var v = String(params.view).toLowerCase();
        try { view.call("show_view", v === "arrangement" ? "Arranger" : "Session"); } catch (e) {}
    }
    if (params.track_index != null || params.trackIndex != null || params.track_type || params.trackType || params.track_name || params.trackName) {
        var selLoc = palTrackPath(params);
        if (selLoc.resolved_by === "name_not_found") return { ok: false, error: "No track found matching name '" + selLoc.name + "'" };
        palSelectTrack(selLoc.path);
    }
    if (params.scene_index != null || params.sceneIndex != null) {
        var sceneIdx = Number(params.scene_index != null ? params.scene_index : params.sceneIndex);
        var sc = liveApi("live_set scenes " + sceneIdx);
        if (sc) {
            try { view.set("selected_scene", "id", extractId(sc.id)); } catch (e2) {}
        }
    }
    if (params.slot) {
        var loc = palClipFromParams(params);
        palSelectTrack("live_set tracks " + loc.track);
        var sl = liveApi("live_set tracks " + loc.track + " clip_slots " + loc.slot);
        if (sl) {
            try { view.set("highlighted_clip_slot", "id", extractId(sl.id)); } catch (e3) {}
        }
        var clip = liveApi(loc.path);
        if (clip) {
            try { view.set("detail_clip", "id", extractId(clip.id)); } catch (e4) {}
        }
    }
    if (params.devicePath || params.device_path || params.path) {
        var dloc = palParseDevicePath(params.devicePath || params.device_path || params.path);
        if (dloc) {
            palSelectTrack(dloc.trackPath);
            var device = liveApi(dloc.devicePath);
            if (device) {
                try { view.call("select_device", "id", extractId(device.id)); } catch (e5) {}
            }
        }
    }
    if (params.openPluginWindow != null || params.open_plugin_window != null) {
        var want = params.openPluginWindow != null ? params.openPluginWindow : params.open_plugin_window;
        var dloc2 = palFindDevice(params);
        if (dloc2) {
            var dview = liveApi(dloc2.devicePath + " view");
            if (dview) {
                try { dview.set("is_showing_on_surface", want ? 1 : 0); } catch (e6) {}
            }
        }
    }
    return { ok: true, message: "Selection updated" };
}

function palPlayback(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var sub = String(params.action || "play").toLowerCase();
    var bpb = Number(unwrap(song.get("signature_numerator")) || 4);
    if (sub === "play" || sub === "start" || sub === "play-arrangement") {
        if (params.startTime || params.start_time) {
            song.set("current_song_time", palBarBeatToBeats(params.startTime || params.start_time, bpb));
        }
        if (params.startLocator || params.start_locator) {
            var cues = palCuePoints();
            var i;
            for (i = 0; i < cues.length; i++) {
                if (cues[i].name === String(params.startLocator || params.start_locator) || cues[i].id === String(params.startLocator || params.start_locator)) {
                    song.set("current_song_time", cues[i].time);
                    break;
                }
            }
        }
        song.call("start_playing");
        return { ok: true, message: "Playback started" };
    }
    if (sub === "stop") {
        song.call("stop_playing");
        return { ok: true, message: "Playback stopped" };
    }
    if (sub === "continue") {
        song.call("continue_playing");
        return { ok: true, message: "Playback resumed" };
    }
    if (sub === "update-arrangement" || sub === "update_arrangement") {
        if (params.loop != null) song.set("loop", params.loop ? 1 : 0);
        if (params.loopStart || params.loop_start) song.set("loop_start", palBarBeatToBeats(params.loopStart || params.loop_start, bpb));
        if (params.loopEnd || params.loop_end) {
            var end = palBarBeatToBeats(params.loopEnd || params.loop_end, bpb);
            var start = Number(unwrap(song.get("loop_start")) || 0);
            song.set("loop_length", Math.max(0.25, end - start));
        }
        return { ok: true, message: "Arrangement loop updated" };
    }
    if (sub === "fire_clip" || sub === "play_clip" || sub === "play-session-clips") {
        var loc = palClipFromParams(params);
        var clip = liveApi(loc.path);
        if (!clip) return { ok: false, error: "Clip not found" };
        clip.call("fire");
        return { ok: true, message: "Fired clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    }
    if (sub === "stop_clip" || sub === "stop-session-clips") {
        var tidx = palTrackIndexFromParams(params, 0);
        var t = liveApi("live_set tracks " + tidx);
        if (t) t.call("stop_all_clips");
        return { ok: true, message: "Stopped clips on track " + tidx };
    }
    if (sub === "stop-all-session-clips") {
        try { song.call("stop_all_clips"); } catch (e) {}
        return { ok: true, message: "Stopped all session clips" };
    }
    if (sub === "fire_scene" || sub === "play_scene" || sub === "play-scene") {
        var sceneIdx = Number(params.scene_index != null ? params.scene_index : (params.sceneIndex != null ? params.sceneIndex : 0));
        var sc = liveApi("live_set scenes " + sceneIdx);
        if (!sc) return { ok: false, error: "Scene not found" };
        sc.call("fire");
        return { ok: true, message: "Fired scene " + sceneIdx };
    }
    return { ok: false, error: "Unknown playback action: " + sub };
}

// Session-to-Arrangement capture: unlike create_scene's capture=true (which
// snapshots currently playing clips into a NEW SESSION scene -- Song's own
// capture_and_insert_scene), this arms Song.record_mode (the global
// Arrangement Record button) and fires a scene so the Arrangement timeline
// actually records the session performance, same as pressing Record then
// launching a scene by hand. Genuinely async in wall-clock terms -- a
// recording runs for real beats of real time -- so this never blocks: with
// duration_beats it schedules a Task (same pattern as skeletonTask/
// skeletonTick) to flip record_mode back off, and returns immediately either
// way. op=stop (or no duration_beats) is how a caller ends it explicitly.
var arrRecTask = null;

function arrRecAutoStop() {
    var song = liveApi("live_set");
    if (song) { try { song.set("record_mode", 0); } catch (e) {} }
    arrRecTask = null;
}

function palRecordToArrangement(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    var op = String(params.op || params.action || "start").toLowerCase();

    if (arrRecTask) { try { arrRecTask.cancel(); } catch (eCancel) {} arrRecTask = null; }

    if (op === "stop") {
        try { song.set("record_mode", 0); } catch (e2) {}
        if (params.stop_playback || params.stopPlayback) {
            try { song.call("stop_playing"); } catch (e3) {}
        }
        return { ok: true, message: "Stopped recording into Arrangement." };
    }

    var sceneIdx = params.scene_index != null ? Number(params.scene_index) : (params.sceneIndex != null ? Number(params.sceneIndex) : null);
    if (sceneIdx == null) return { ok: false, error: "Provide scene_index to record into the Arrangement." };
    var scene = liveApi("live_set scenes " + sceneIdx);
    if (!scene) return { ok: false, error: "Scene " + sceneIdx + " not found" };

    try { song.set("record_mode", 1); } catch (e4) {
        return { ok: false, error: "Could not arm Arrangement Record: " + e4 };
    }
    if (!unwrap(song.get("is_playing"))) {
        try { song.call("start_playing"); } catch (e5) {}
    }
    try { scene.call("fire"); } catch (e6) {
        try { song.set("record_mode", 0); } catch (e7) {}
        return { ok: false, error: "Could not fire scene " + sceneIdx + ": " + e6 };
    }

    var durationBeats = params.duration_beats != null ? Number(params.duration_beats) : (params.durationBeats != null ? Number(params.durationBeats) : null);
    if (durationBeats != null && durationBeats > 0) {
        var tempo = Number(unwrap(song.get("tempo"))) || 120;
        var ms = Math.round((durationBeats * 60000) / tempo);
        arrRecTask = new Task(arrRecAutoStop);
        arrRecTask.schedule(ms);
        return {
            ok: true,
            message: "Recording scene " + sceneIdx + " into Arrangement for " + durationBeats + " beats (~" + Math.round(ms / 1000) + "s) -- will auto-stop.",
            scene_index: sceneIdx,
            auto_stop_ms: ms
        };
    }

    return {
        ok: true,
        message: "Recording scene " + sceneIdx + " into Arrangement -- call live_record_to_arrangement again with op=\"stop\" to finish.",
        scene_index: sceneIdx
    };
}

// There is no Browser / BrowserItem class in the Live Object Model exposed to
// Max for Live (confirmed against the Max9 LOM reference, and probed live in
// v1.0.34: `live_app browser` -> exists:false, 0 children, 3/3), so Live's own
// browser -- packs, sounds, presets, plugins, Max for Live devices -- cannot
// be walked or searched from HERE at all. That limit is specific to this
// engine and is still accurate for it; this function stays as the M4L
// fallback and keeps telling the truth about what M4L can do.
//
// As of v1.1.0 the browser IS reachable, just not through this file: engine E2
// (the LiveActionsRS Remote Script, remote_script/LiveActionsRS) runs inside
// Live's own Python where Application.browser exists. genius_client.py routes
// live_library search/listPlugins to E2 when it is answering and falls back
// here when it isn't, and live_browse / live_load_browser_item /
// live_preview_browser_item are E2-only. Do not try to "fix" the stubs below
// by adding a browser path in Max -- there is nothing to bind to.
function palLibrary(params) {
    var act = String(params.action || "search").toLowerCase();
    if (act === "listplugins" || act === "list_plugins") {
        return {
            ok: true,
            plugins: [],
            note: "Live's installed plug-in list cannot be read through the Live Object Model. Enable the LiveActionsRS Remote Script (engine E2) and Genius can list real VST/VST3, or check Live's Plug-Ins browser panel directly."
        };
    }
    if (act === "listtags" || act === "list_tags" || act === "listcategories" || act === "list_categories") {
        return {
            ok: true,
            categories: ["drums", "instruments", "sounds", "audio_effects", "midi_effects", "samples", "user_library", "packs", "plugins", "max_for_live"]
        };
    }
    return {
        ok: true,
        action: "search",
        query: params.query || "",
        results: [],
        note: "Live's own browser cannot be searched through the Live Object Model -- these results from the Max for Live engine are always empty. Enable the LiveActionsRS Remote Script (engine E2) to search the real browser; otherwise only the user's disk Samples folder can be searched (live_find_samples, or the disk results appended alongside this)."
    };
}

function palLiveApi(params) {
    var path = params.path || "live_set";
    var ops = params.operations || [];
    if (!ops.length) return { ok: false, error: "operations array required" };
    var api = liveApi(path);
    if (!api) return { ok: false, error: "No Live object at " + path };
    var results = [];
    var i;
    for (i = 0; i < Math.min(50, ops.length); i++) {
        var op = ops[i] || {};
        var typ = String(op.type || "get").toLowerCase();
        try {
            if (typ === "goto" || typ === "set_path") {
                var next = String(op.value || op.path || "");
                api = liveApi(next);
                if (!api) {
                    results.push({ ok: false, error: "goto failed: " + next });
                    break;
                }
                results.push({ ok: true, path: next });
            } else if (typ === "get" || typ === "get_property" || typ === "getproperty") {
                results.push({ ok: true, property: op.property, value: api.get(String(op.property)) });
            } else if (typ === "set" || typ === "set_property" || typ === "setproperty") {
                // op.args, when given, lets a diagnostic op exercise the
                // multi-arg .set(prop, "id", N) idiom this codebase uses for
                // object-reference properties elsewhere in pal.js -- the
                // single-value form below can't reach that call shape.
                if (op.args && op.args.length) {
                    api.set.apply(api, [String(op.property)].concat(op.args));
                    results.push({ ok: true, property: op.property, args: op.args });
                } else {
                    api.set(String(op.property), op.value);
                    results.push({ ok: true, property: op.property, value: op.value });
                }
            } else if (typ === "call" || typ === "call_method") {
                var args = [String(op.method || "")].concat(op.args || []);
                var value = api.call.apply(api, args);
                results.push({ ok: true, method: op.method, value: value });
            } else if (typ === "info") {
                results.push({ ok: true, info: String(api.info || "") });
            } else if (typ === "getcount") {
                results.push({ ok: true, property: op.property, value: api.getcount(String(op.property)) });
            } else if (typ === "exists") {
                results.push({ ok: true, exists: !!(api && api.id != 0) });
            } else {
                results.push({ ok: false, error: "Unknown op: " + typ });
            }
        } catch (e) {
            results.push({ ok: false, error: String(e) });
        }
    }
    return { ok: true, path: path, results: results };
}

function palReadMeter(params) {
    var loc = palTrackPath(params);
    var t = liveApi(loc.path);
    if (!t) return { ok: false, error: "Track not found at " + loc.path };
    var song = liveApi("live_set");
    var left = 0;
    var right = 0;
    var level = 0;
    try { left = Number(unwrap(t.get("output_meter_left")) || 0); } catch (e1) {}
    try { right = Number(unwrap(t.get("output_meter_right")) || 0); } catch (e2) {}
    try { level = Number(unwrap(t.get("output_meter_level")) || 0); } catch (e3) {}
    var isPlaying = false;
    try { isPlaying = !!unwrap(song.get("is_playing")); } catch (e4) {}
    return {
        ok: true,
        track_index: loc.index,
        track_kind: loc.kind || "regular",
        path: loc.path,
        name: String(unwrap(t.get("name")) || ""),
        output_meter_left: left,
        output_meter_right: right,
        output_meter_level: level,
        is_playing: isPlaying
    };
}

function palReadMacros(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path (e.g. t0/d0) or track_index + device_index" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found at " + loc.devicePath };
    var canHaveChains = false;
    try { canHaveChains = !!unwrap(device.get("can_have_chains")); } catch (e) {}
    if (!canHaveChains) {
        return { ok: false, error: "Device '" + String(unwrap(device.get("name")) || "") + "' is not a Rack (no macros)" };
    }
    var paramCount = 0;
    try { paramCount = device.getcount("parameters"); } catch (e2) { return { ok: false, error: "Could not count device parameters" }; }
    var macros = [];
    var base = device.unquotedpath || device.path;
    var i;
    for (i = 0; i < paramCount; i++) {
        var p = liveApi(base + " parameters " + i);
        if (!p) continue;
        var pname = String(unwrap(p.get("name")) || "");
        if (pname === "Device On") continue;
        var isEnabled = true;
        try { isEnabled = !!unwrap(p.get("is_enabled")); } catch (e3) {}
        var isQuantized = false;
        try { isQuantized = !!unwrap(p.get("is_quantized")); } catch (e4) {}
        var macroVal = Number(unwrap(p.get("value")));
        var valStr = "";
        // str_for_value(value), not the value_string property -- see H8/S1.3.4 note above.
        try { valStr = String(unwrap(p.call("str_for_value", macroVal)) || ""); } catch (e5) {}
        macros.push({
            index: i,
            name: pname,
            value: macroVal,
            min: Number(unwrap(p.get("min"))),
            max: Number(unwrap(p.get("max"))),
            is_enabled: isEnabled,
            is_quantized: isQuantized,
            value_string: valStr
        });
    }
    return {
        ok: true,
        path: loc.devicePath,
        device_name: String(unwrap(device.get("name")) || ""),
        macro_count: macros.length,
        macros: macros
    };
}

function palUpdateMacro(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path (e.g. t0/d0) or track_index + device_index" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found at " + loc.devicePath };
    var canHaveChains = false;
    try { canHaveChains = !!unwrap(device.get("can_have_chains")); } catch (e) {}
    if (!canHaveChains) {
        return { ok: false, error: "Device '" + String(unwrap(device.get("name")) || "") + "' is not a Rack" };
    }
    var macroTarget = params.macro != null ? params.macro : params.macro_index;
    if (macroTarget == null && params.name != null) macroTarget = params.name;
    if (macroTarget == null) return { ok: false, error: "Provide macro name or index" };

    var paramCount = 0;
    try { paramCount = device.getcount("parameters"); } catch (e2) { return { ok: false, error: "Could not count device parameters" }; }
    var base = device.unquotedpath || device.path;
    var targetP = null;
    var targetIdx = -1;
    var targetName = "";
    var needle = String(macroTarget).toLowerCase();

    var i;
    for (i = 0; i < paramCount; i++) {
        var p = liveApi(base + " parameters " + i);
        if (!p) continue;
        var pname = String(unwrap(p.get("name")) || "");
        if (pname === "Device On") continue;
        if (pname.toLowerCase() === needle || String(i) === needle) {
            targetP = p;
            targetIdx = i;
            targetName = pname;
            break;
        }
    }
    if (!targetP) {
        return { ok: false, error: "Macro '" + macroTarget + "' not found on device" };
    }

    var minVal = Number(unwrap(targetP.get("min")));
    var maxVal = Number(unwrap(targetP.get("max")));
    var finalVal = minVal;

    if (params.value_normalized != null) {
        var norm = Math.max(0.0, Math.min(1.0, Number(params.value_normalized)));
        finalVal = minVal + norm * (maxVal - minVal);
        targetP.set("value", finalVal);
    } else if (params.value != null) {
        var applied = palApplyParamValue(targetP, params.value, minVal, maxVal);
        if (!applied.ok) {
            return {
                ok: false,
                error: "Could not set macro '" + targetName + "' to '" + params.value + "'",
                name: targetName,
                index: targetIdx,
                display_after: applied.display_after
            };
        }
    } else {
        return { ok: false, error: "Provide value or value_normalized" };
    }

    var updatedVal = Number(unwrap(targetP.get("value")));
    var valStr = "";
    // str_for_value(value), not the value_string property -- see H8/S1.3.4 note above.
    try { valStr = String(unwrap(targetP.call("str_for_value", updatedVal)) || ""); } catch (eVal) {}

    return {
        ok: true,
        message: "Set macro '" + targetName + "' to " + updatedVal + (valStr ? " (" + valStr + ")" : ""),
        name: targetName,
        index: targetIdx,
        value: updatedVal,
        value_string: valStr,
        display_after: valStr
    };
}

function palRemoveNotes(params) {
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "No clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (!unwrap(clip.get("is_midi_clip"))) {
        return { ok: false, error: "Clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) + " is audio, not MIDI.", track_index: loc.track, slot_index: loc.slot };
    }
    var fromTime = params.from_time != null ? Number(params.from_time) : (params.fromTime != null ? Number(params.fromTime) : 0.0);
    var clipLen = 10000.0;
    try { clipLen = Number(unwrap(clip.get("length")) || 10000.0); } catch (eLen) {}
    var timeSpan = params.time_span != null ? Number(params.time_span) : (params.timeSpan != null ? Number(params.timeSpan) : clipLen);
    var fromPitch = params.from_pitch != null ? Number(params.from_pitch) : (params.fromPitch != null ? Number(params.fromPitch) : 0);
    var pitchSpan = params.pitch_span != null ? Number(params.pitch_span) : (params.pitchSpan != null ? Number(params.pitchSpan) : 128);

    // clip.call() never throws on an unsupported method (M1), so verify by
    // note count instead of trusting the absence of an exception. Only
    // remove_notes_extended (Live 11+) is used here -- the old remove_notes
    // dictionary API is what triggers Live's "older process... loss of MPE,
    // probability, velocity deviation and release velocity" warning dialog,
    // so it must never be called even as a fallback.
    var beforeCount = palGetNotes(clip).total;
    try { clip.call("remove_notes_extended", fromPitch, pitchSpan, fromTime, timeSpan); } catch (e1) {}
    var afterCount = palGetNotes(clip).total;
    if (afterCount < beforeCount) {
        return {
            ok: true,
            message: "Removed " + (beforeCount - afterCount) + " note(s) from pitch " + fromPitch + " (span " + pitchSpan + "), time " + fromTime + " (span " + timeSpan + ")",
            track_index: loc.track,
            slot_index: loc.slot,
            notes_removed: beforeCount - afterCount
        };
    }
    if (beforeCount === 0) {
        return { ok: true, message: "No notes in range to remove", track_index: loc.track, slot_index: loc.slot, notes_removed: 0 };
    }
    return { ok: false, error: "remove_notes did not remove any notes (count unchanged at " + beforeCount + ")", track_index: loc.track, slot_index: loc.slot };
}

function palDuplicateToArrangement(params) {
    var cloc = palClipFromParams(params);
    var destTime = Number(params.destination_time != null ? params.destination_time : (params.destinationTime != null ? params.destinationTime : (params.arrangement_time != null ? params.arrangement_time : 0.0)));
    var targetTrackIdx = params.to_track_index != null ? Number(params.to_track_index) : (params.to_track != null ? Number(params.to_track) : cloc.track);
    var track = liveApi("live_set tracks " + targetTrackIdx);
    if (!track) return { ok: false, error: "Target track " + palLiveNum(targetTrackIdx) + " not found" };

    var sourceSlot = liveApi("live_set tracks " + cloc.track + " clip_slots " + cloc.slot);
    if (!sourceSlot) return { ok: false, error: "Source slot not found at track " + palLiveNum(cloc.track) + ", slot " + palLiveNum(cloc.slot) };
    if (!unwrap(sourceSlot.get("has_clip"))) {
        return { ok: false, error: "No clip in slot " + palLiveNum(cloc.slot) + " on track " + palLiveNum(cloc.track) };
    }
    var clip = liveApi(cloc.path);
    if (!clip) return { ok: false, error: "Source clip not found at track " + palLiveNum(cloc.track) + ", slot " + palLiveNum(cloc.slot) };

    // duplicate_clip_to_arrangement never throws on a type mismatch (M1) --
    // check it up front instead of only inferring failure from a count that
    // didn't change.
    if (targetTrackIdx !== cloc.track) {
        var clipIsMidi = !!unwrap(clip.get("is_midi_clip"));
        var targetHasMidi = !!unwrap(track.get("has_midi_input"));
        var targetHasAudio = !!unwrap(track.get("has_audio_input"));
        if (clipIsMidi && !targetHasMidi) {
            return { ok: false, error: "Cannot duplicate a MIDI clip onto audio track " + palLiveNum(targetTrackIdx), track_index: targetTrackIdx, source_track: cloc.track, source_slot: cloc.slot };
        }
        if (!clipIsMidi && !targetHasAudio) {
            return { ok: false, error: "Cannot duplicate an audio clip onto MIDI track " + palLiveNum(targetTrackIdx), track_index: targetTrackIdx, source_track: cloc.track, source_slot: cloc.slot };
        }
    }

    var clipName = String(unwrap(clip.get("name")) || "Clip");
    var clipId = extractId(clip.id);

    var beforeCount = 0;
    try { beforeCount = track.getcount("arrangement_clips"); } catch (eCnt) {}
    try { track.call("duplicate_clip_to_arrangement", "id", clipId, destTime); } catch (e1) {}
    var afterCount = beforeCount;
    try { afterCount = track.getcount("arrangement_clips"); } catch (eCnt2) {}

    if (afterCount > beforeCount) {
        return {
            ok: true,
            message: "Duplicated clip '" + clipName + "' to Arrangement at beat " + destTime + " on track " + palLiveNum(targetTrackIdx),
            track_index: targetTrackIdx,
            source_track: cloc.track,
            source_slot: cloc.slot,
            clip_name: clipName,
            destination_time: destTime
        };
    }
    return {
        ok: false,
        error: "duplicate_clip_to_arrangement did not create a new arrangement clip (count unchanged at " + beforeCount + ")",
        track_index: targetTrackIdx,
        source_track: cloc.track,
        source_slot: cloc.slot
    };
}

function palReadArrangementClips(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found at " + loc.path };
    var n = 0;
    try { n = track.getcount("arrangement_clips"); } catch (e) { n = 0; }
    var clips = [];
    var i;
    for (i = 0; i < n; i++) {
        var c = liveApi(loc.path + " arrangement_clips " + i);
        if (!c) continue;
        var start = Number(unwrap(c.get("start_time")) || 0);
        var span = 0;
        try {
            var end = unwrap(c.get("end_time"));
            if (end !== null && end !== undefined && end !== "") span = Number(end) - start;
        } catch (eEnd) {}
        if (!(span > 0)) {
            try { span = Number(unwrap(c.get("length")) || 0); } catch (eLen) {}
        }
        clips.push({
            index: i,
            id: String(c.id || ""),
            name: String(unwrap(c.get("name")) || ""),
            start_time: start,
            end_time: start + span,
            length: span,
            color: unwrap(c.get("color")),
            looping: !!unwrap(c.get("looping")),
            is_midi_clip: !!unwrap(c.get("is_midi_clip")),
            is_audio_clip: !!unwrap(c.get("is_audio_clip")),
            is_playing: !!unwrap(c.get("is_playing")),
            muted: !!unwrap(c.get("muted"))
        });
    }
    clips.sort(function (a, b) { return a.start_time - b.start_time; });
    return {
        ok: true,
        track_index: loc.index,
        track_name: String(unwrap(track.get("name")) || ""),
        clip_count: clips.length,
        clips: clips
    };
}

function palUpdateArrangementClip(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found at " + loc.path };
    var clipIdx = params.clip_index != null ? Number(params.clip_index) : (params.clipIndex != null ? Number(params.clipIndex) : -1);
    var clip = null;
    if (clipIdx >= 0) {
        clip = liveApi(loc.path + " arrangement_clips " + clipIdx);
    } else if (params.clip_id || params.id) {
        clip = liveApi("id " + (params.clip_id || params.id));
    }
    if (!clip) return { ok: false, error: "Arrangement clip not found on track " + loc.index };
    var changes = [];
    if (params.name != null) {
        clip.set("name", String(params.name));
        changes.push("name=" + params.name);
    }
    if (params.color != null) {
        clip.set("color", hexToLiveColor(params.color));
        changes.push("color=" + params.color);
    }
    if (params.mute != null) {
        clip.set("muted", params.mute ? 1 : 0);
        changes.push("muted=" + (params.mute ? "true" : "false"));
    }
    return {
        ok: true,
        message: "Updated arrangement clip: " + (changes.join(", ") || "no changes"),
        track_index: loc.index,
        clip_index: clipIdx,
        name: String(unwrap(clip.get("name")) || "")
    };
}

function palCaptureMidi() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("capture_midi");
        return { ok: true, message: "Captured recently played MIDI into a new clip" };
    } catch (e) {
        return { ok: false, error: "capture_midi failed: " + String(e) };
    }
}

function palBackToArranger() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    if (palSetChecked(song, "back_to_arranger", 0)) {
        return { ok: true, message: "Returned playback control to the Arrangement timeline" };
    }
    try { song.call("back_to_arranger"); } catch (e) {}
    if (Number(unwrap(song.get("back_to_arranger"))) === 0) {
        return { ok: true, message: "Returned playback control to the Arrangement timeline" };
    }
    return { ok: false, error: "back_to_arranger could not be cleared (property/method may not exist in this Live version)" };
}

function palReEnableAutomation() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("re_enable_automation");
        return { ok: true, message: "Re-enabled manual parameter overrides on automation" };
    } catch (e) {
        return { ok: false, error: "re_enable_automation failed: " + String(e) };
    }
}

function palCrossfader(params) {
    params = params || {};
    var master = liveApi("live_set master_track mixer_device crossfader");
    var res = { ok: true };
    if (params.value != null && master) {
        var val = Math.max(-1.0, Math.min(1.0, Number(params.value)));
        master.set("value", val);
        res.crossfader = val;
        res.message = "Set master crossfader to " + val;
    } else if (master) {
        res.crossfader = Number(unwrap(master.get("value")));
    }
    if (params.track_index != null && params.assign != null) {
        var tMixer = liveApi("live_set tracks " + params.track_index + " mixer_device");
        if (tMixer) {
            var assignVal = Number(params.assign);
            if (typeof params.assign === "string") {
                var aLow = params.assign.toLowerCase().trim();
                if (aLow === "a") assignVal = 0;
                else if (aLow === "b") assignVal = 2;
                else assignVal = 1;
            }
            tMixer.set("crossfade_assign", assignVal);
            res.track_index = Number(params.track_index);
            res.crossfade_assign = assignVal;
            res.message = (res.message ? res.message + "; " : "") + "Assigned track " + params.track_index + " to crossfade " + (assignVal === 0 ? "A" : (assignVal === 2 ? "B" : "None"));
        }
    }
    return res;
}

function palCreateTakeLane(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found at " + loc.path };
    try {
        track.call("create_take_lane");
        var count = 0;
        try { count = track.getcount("take_lanes"); } catch (e) {}
        return {
            ok: true,
            message: "Created take lane on track " + loc.index + " ('" + String(unwrap(track.get("name")) || "") + "')",
            track_index: loc.index,
            take_lane_count: count
        };
    } catch (err) {
        return { ok: false, error: "create_take_lane failed: " + String(err) };
    }
}

function palFoldState(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found at " + loc.path };
    var isFoldable = false;
    try { isFoldable = !!unwrap(track.get("is_foldable")); } catch (e) {}
    var foldState = null;
    if (isFoldable) {
        if (params.folded != null) {
            var fVal = (params.folded === true || params.folded === 1 || params.folded === "true") ? 1 : 0;
            track.set("fold_state", fVal);
        }
        try { foldState = !!unwrap(track.get("fold_state")); } catch (e2) {}
    }
    return {
        ok: true,
        track_index: loc.index,
        track_name: String(unwrap(track.get("name")) || ""),
        is_foldable: isFoldable,
        fold_state: foldState,
        message: isFoldable ? ("Group track is " + (foldState ? "folded (collapsed)" : "unfolded (expanded)")) : "Track is not a group track"
    };
}

function palGroovePool(params) {
    params = params || {};
    var gp = liveApi("live_set groove_pool");
    var count = 0;
    try { count = gp ? gp.getcount("grooves") : 0; } catch (e) { count = 0; }
    var grooves = [];
    var i;
    for (i = 0; i < count; i++) {
        var g = liveApi("live_set groove_pool grooves " + i);
        if (g) {
            grooves.push({
                index: i,
                name: String(unwrap(g.get("name")) || ("Groove " + i))
            });
        }
    }
    var res = { ok: true, groove_count: count, grooves: grooves };

    if (params.track_index != null && (params.clip_index != null || params.slot_index != null)) {
        var slotIdx = params.clip_index != null ? params.clip_index : params.slot_index;
        var clip = liveApi("live_set tracks " + params.track_index + " clip_slots " + slotIdx + " clip");
        if (clip) {
            if (params.groove_index != null) {
                var gTarget = liveApi("live_set groove_pool grooves " + params.groove_index);
                if (gTarget) {
                    try {
                        clip.set("groove", "id", extractId(gTarget.id));
                        res.assigned_groove = params.groove_index;
                        res.message = "Assigned groove " + params.groove_index + " to track " + params.track_index + ", clip " + slotIdx;
                    } catch (eSet) {
                        res.warning = "Could not attach groove: " + String(eSet);
                    }
                }
            } else if (params.clear === true) {
                try {
                    clip.set("groove", "id", 0);
                    res.message = "Cleared groove from clip";
                } catch (eClr) {}
            }
        }
    }
    return res;
}

function palDuplicateLoop(params) {
    var cloc = palClipFromParams(params);
    var clip = liveApi(cloc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(cloc.track) + ", slot " + palLiveNum(cloc.slot) };
    try {
        clip.call("duplicate_loop");
        var newLen = Number(unwrap(clip.get("length")) || 0);
        return {
            ok: true,
            message: "Doubled loop length and duplicated notes inside clip.",
            track_index: cloc.track,
            slot_index: cloc.slot,
            clip_name: String(unwrap(clip.get("name")) || ""),
            length: newLen
        };
    } catch (e) {
        return { ok: false, error: "duplicate_loop failed: " + String(e) };
    }
}

function palUndo() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("undo");
        return { ok: true, message: "Undid last action in Ableton Live" };
    } catch (e) {
        return { ok: false, error: "Undo failed: " + String(e) };
    }
}

function palRedo() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("redo");
        return { ok: true, message: "Redid last undone action in Ableton Live" };
    } catch (e) {
        return { ok: false, error: "Redo failed: " + String(e) };
    }
}

function palJumpToTime(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var t = Number(params.time != null ? params.time : (params.beat != null ? params.beat : 0));
    if (isNaN(t) || t < 0) return { ok: false, error: "Provide a valid beat time >= 0" };
    try {
        song.set("current_song_time", t);
        return { ok: true, message: "Arrangement playhead jumped to beat " + t, time: t };
    } catch (e) {
        return { ok: false, error: "jump_to_time failed: " + String(e) };
    }
}

function palSetOverdub(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var overdubGiven = params.overdub != null || params.arrangement_overdub != null;
    var arrOverdub = params.overdub != null ? !!params.overdub : (params.arrangement_overdub != null ? !!params.arrangement_overdub : null);
    var sessRecord = params.session_record != null ? !!params.session_record : null;
    if (!overdubGiven && sessRecord == null) {
        return { ok: false, error: "Provide overdub/arrangement_overdub and/or session_record" };
    }
    var notApplied = [];
    var messages = [];
    if (overdubGiven) {
        if (palSetChecked(song, "arrangement_overdub", arrOverdub ? 1 : 0)) messages.push("arrangement overdub=" + arrOverdub);
        else notApplied.push("arrangement_overdub");
    }
    if (sessRecord != null) {
        if (palSetChecked(song, "session_record", sessRecord ? 1 : 0)) messages.push("session_record=" + sessRecord);
        else notApplied.push("session_record");
    }
    var result = {
        ok: notApplied.length === 0,
        message: messages.length ? "Set " + messages.join(", ") : "No overdub changes applied",
        arrangement_overdub: overdubGiven ? arrOverdub : undefined,
        session_record: sessRecord != null ? sessRecord : undefined
    };
    if (notApplied.length) result.not_applied = notApplied;
    return result;
}

function palReadArrangementLength() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        var len = Number(unwrap(song.get("song_length")) || 0);
        return { ok: true, arrangement_length: len, message: "Arrangement length is " + len + " beats" };
    } catch (e) {
        return { ok: false, error: "Could not read song_length: " + String(e) };
    }
}

function palMoveArrangementClip(params) {
    var srcTrackIdx = Number(params.source_track_index != null ? params.source_track_index : (params.track_index != null ? params.track_index : 0));
    var srcClipIdx = Number(params.source_clip_index != null ? params.source_clip_index : (params.clip_index != null ? params.clip_index : 0));
    var targetTrackIdx = Number(params.target_track_index != null ? params.target_track_index : srcTrackIdx);
    var newStartTime = Number(params.new_start_time != null ? params.new_start_time : (params.start_time != null ? params.start_time : 0));

    var srcTrack = liveApi("live_set tracks " + srcTrackIdx);
    if (!srcTrack) return { ok: false, error: "Source track not found: " + palLiveNum(srcTrackIdx) };
    var clip = liveApi("live_set tracks " + srcTrackIdx + " arrangement_clips " + srcClipIdx);
    if (!clip) return { ok: false, error: "Arrangement clip " + palLiveNum(srcClipIdx) + " not found on track " + palLiveNum(srcTrackIdx) };

    var targetTrack = (targetTrackIdx === srcTrackIdx) ? srcTrack : liveApi("live_set tracks " + targetTrackIdx);
    if (!targetTrack) return { ok: false, error: "Target track not found: " + palLiveNum(targetTrackIdx) };

    // duplicate_clip_to_arrangement never throws on a type mismatch (M1) --
    // it just silently fails, which used to surface as the generic "did not
    // create a new clip" message below. Catch the actual reason up front.
    if (targetTrackIdx !== srcTrackIdx) {
        var clipIsMidi = !!unwrap(clip.get("is_midi_clip"));
        var targetHasMidi = !!unwrap(targetTrack.get("has_midi_input"));
        var targetHasAudio = !!unwrap(targetTrack.get("has_audio_input"));
        if (clipIsMidi && !targetHasMidi) {
            return { ok: false, error: "Cannot move a MIDI clip onto audio track " + palLiveNum(targetTrackIdx), source_track_index: srcTrackIdx, source_clip_index: srcClipIdx, target_track_index: targetTrackIdx };
        }
        if (!clipIsMidi && !targetHasAudio) {
            return { ok: false, error: "Cannot move an audio clip onto MIDI track " + palLiveNum(targetTrackIdx), source_track_index: srcTrackIdx, source_clip_index: srcClipIdx, target_track_index: targetTrackIdx };
        }
    }

    var clipName = String(unwrap(clip.get("name")) || "Clip");
    var clipId = extractId(clip.id);
    if (!clipId) return { ok: false, error: "Could not resolve source clip id" };

    // .call() never throws on an unsupported method (M1) -- a naive
    // try{duplicate; delete}catch{...} would report ok:true even if the
    // duplicate silently failed, and the delete below would then destroy
    // the only copy of the clip. Verify the duplicate landed (arrangement
    // clip count went up on the target track) BEFORE deleting the source.
    var beforeCount = 0;
    try { beforeCount = targetTrack.getcount("arrangement_clips"); } catch (eCnt) {}
    try { targetTrack.call("duplicate_clip_to_arrangement", "id", clipId, newStartTime); } catch (eDup) {}
    var afterCount = beforeCount;
    try { afterCount = targetTrack.getcount("arrangement_clips"); } catch (eCnt2) {}

    if (afterCount <= beforeCount) {
        return {
            ok: false,
            error: "duplicate_clip_to_arrangement did not create a new clip on the target track -- source clip left untouched",
            source_track_index: srcTrackIdx,
            source_clip_index: srcClipIdx,
            target_track_index: targetTrackIdx
        };
    }

    try { srcTrack.call("delete_clip", "id", clipId); } catch (eDel) {}

    return {
        ok: true,
        message: "Moved arrangement clip '" + clipName + "' to beat " + newStartTime + " on track " + palLiveNum(targetTrackIdx),
        source_track_index: srcTrackIdx,
        source_clip_index: srcClipIdx,
        target_track_index: targetTrackIdx,
        new_start_time: newStartTime
    };
}

function palReadArrangementNotes(params) {
    var trkIdx = Number(params.track_index != null ? params.track_index : 0);
    var clipIdx = Number(params.clip_index != null ? params.clip_index : 0);
    var clip = liveApi("live_set tracks " + trkIdx + " arrangement_clips " + clipIdx);
    if (!clip) return { ok: false, error: "Arrangement clip " + clipIdx + " not found on track " + trkIdx };
    var isMidi = !!unwrap(clip.get("is_midi_clip"));
    if (!isMidi) return { ok: false, error: "Clip on track " + trkIdx + ", arrangement index " + clipIdx + " is audio, not MIDI." };

    var noteData = palGetNotes(clip);
    return {
        ok: true,
        track_index: trkIdx,
        clip_index: clipIdx,
        clip_name: String(unwrap(clip.get("name")) || ""),
        start_time: Number(unwrap(clip.get("start_time")) || 0),
        length: Number(unwrap(clip.get("length")) || 0),
        total_notes: noteData.total,
        truncated: noteData.truncated,
        notes: noteData.notes
    };
}

function palWriteArrangementNotes(params) {
    var trkIdx = Number(params.track_index != null ? params.track_index : 0);
    var clipIdx = Number(params.clip_index != null ? params.clip_index : 0);
    var clip = liveApi("live_set tracks " + trkIdx + " arrangement_clips " + clipIdx);
    if (!clip) return { ok: false, error: "Arrangement clip " + clipIdx + " not found on track " + trkIdx };
    var isMidi = !!unwrap(clip.get("is_midi_clip"));
    if (!isMidi) return { ok: false, error: "Clip on track " + trkIdx + ", arrangement index " + clipIdx + " is audio, not MIDI." };

    var replace = params.replace !== false;
    var notes = params.notes;
    if (typeof notes === "string") {
        try { notes = JSON.parse(notes); } catch (e) {
            return { ok: false, error: "Failed to parse notes JSON: " + e };
        }
    }
    if (!notes || !notes.length) return { ok: false, error: "No valid notes array provided" };

    var normNotes = [];
    var i;
    for (i = 0; i < notes.length; i++) {
        var n = notes[i];
        var item = {
            pitch: n.pitch != null ? n.pitch : 60,
            startTime: n.start_time != null ? n.start_time : (n.startTime != null ? n.startTime : 0.0),
            duration: n.duration != null ? n.duration : 0.25,
            velocity: n.velocity != null ? n.velocity : 100,
            mute: !!n.mute
        };
        if (n.probability != null) item.probability = Math.max(0, Math.min(1, Number(n.probability)));
        if (n.velocity_deviation != null) item.velocity_deviation = Math.max(-127, Math.min(127, Number(n.velocity_deviation)));
        normNotes.push(item);
    }

    try {
        writeNotes(clip, normNotes, replace);
        return {
            ok: true,
            message: (replace ? "Replaced with " : "Added ") + normNotes.length + " notes in arrangement clip on track " + trkIdx,
            track_index: trkIdx,
            clip_index: clipIdx,
            notes_count: normNotes.length
        };
    } catch (e2) {
        return { ok: false, error: "Failed to write notes to arrangement clip: " + String(e2) };
    }
}

function palRemoveArrangementNotes(params) {
    var trkIdx = Number(params.track_index != null ? params.track_index : 0);
    var clipIdx = Number(params.clip_index != null ? params.clip_index : 0);
    var clip = liveApi("live_set tracks " + trkIdx + " arrangement_clips " + clipIdx);
    if (!clip) return { ok: false, error: "Arrangement clip " + clipIdx + " not found on track " + trkIdx };
    if (!unwrap(clip.get("is_midi_clip"))) {
        return { ok: false, error: "Clip on track " + trkIdx + ", arrangement index " + clipIdx + " is audio, not MIDI." };
    }

    var fromPitch = Number(params.from_pitch != null ? params.from_pitch : 0);
    var pitchSpan = Number(params.pitch_span != null ? params.pitch_span : 128);
    var fromTime = Number(params.from_time != null ? params.from_time : 0);
    var timeSpan = Number(params.time_span != null ? params.time_span : 100000);

    try {
        clip.call("remove_notes_extended", fromPitch, pitchSpan, fromTime, timeSpan);
        return {
            ok: true,
            message: "Removed notes in range (pitch " + fromPitch + ".." + (fromPitch + pitchSpan) + ", time " + fromTime + ".." + (fromTime + timeSpan) + ") from arrangement clip " + clipIdx,
            track_index: trkIdx,
            clip_index: clipIdx
        };
    } catch (e) {
        return { ok: false, error: "Failed to remove notes from arrangement clip: " + String(e) };
    }
}

function palReadTakeLanes(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found: " + loc.path };
    var n = 0;
    try { n = track.getcount("take_lanes"); } catch (e) { n = 0; }
    var lanes = [];
    var i;
    for (i = 0; i < n; i++) {
        var tl = liveApi(loc.path + " take_lanes " + i);
        if (tl) {
            lanes.push({
                index: i,
                name: String(unwrap(tl.get("name")) || ("Take " + (i + 1)))
            });
        }
    }
    return {
        ok: true,
        track_index: loc.index,
        track_name: String(unwrap(track.get("name")) || ""),
        take_lane_count: lanes.length,
        take_lanes: lanes
    };
}

function palUpdateTakeLane(params) {
    var loc = palTrackPath(params);
    var laneIdx = Number(params.take_lane_index != null ? params.take_lane_index : (params.lane_index != null ? params.lane_index : 0));
    var tl = liveApi(loc.path + " take_lanes " + laneIdx);
    if (!tl) return { ok: false, error: "Take lane " + laneIdx + " not found on track " + loc.index };
    if (!params.name) return { ok: false, error: "Provide 'name' to rename take lane." };
    try {
        tl.set("name", String(params.name));
        return {
            ok: true,
            message: "Renamed take lane " + laneIdx + " on track " + loc.index + " to '" + params.name + "'",
            track_index: loc.index,
            take_lane_index: laneIdx,
            name: String(params.name)
        };
    } catch (e) {
        return { ok: false, error: "Failed to rename take lane: " + String(e) };
    }
}

function palCreateTakeLaneClip(params) {
    var loc = palTrackPath(params);
    var track = liveApi(loc.path);
    if (!track) return { ok: false, error: "Track not found: " + loc.path };
    var laneIdx = Number(params.take_lane_index != null ? params.take_lane_index : (params.lane_index != null ? params.lane_index : 0));
    var tl = liveApi(loc.path + " take_lanes " + laneIdx);
    if (!tl) return { ok: false, error: "Take lane " + laneIdx + " not found on track " + loc.index };

    var startTime = Number(params.start_time != null ? params.start_time : 0.0);
    var length = Number(params.length != null ? params.length : 4.0);
    if (length <= 0) return { ok: false, error: "length must be > 0" };

    try {
        tl.call("create_midi_clip", startTime, length);
        return {
            ok: true,
            message: "Created MIDI clip on take lane " + laneIdx + " (track " + loc.index + ") at beat " + startTime + " (length " + length + " beats)",
            track_index: loc.index,
            take_lane_index: laneIdx,
            start_time: startTime,
            length: length
        };
    } catch (e) {
        return { ok: false, error: "Could not create clip on take lane: " + String(e) };
    }
}

function palBatchTracks(params, defaultAction) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var action = String((params && params.action) || defaultAction || "unarm_all").toLowerCase();
    var nTracks = 0;
    try { nTracks = song.getcount("tracks"); } catch (e) { nTracks = 0; }

    var modified = 0;
    var trkIdx = (params && params.track_index != null) ? Number(params.track_index) : -1;

    if (action === "unarm_all") {
        for (var i = 0; i < nTracks; i++) {
            var t = liveApi("live_set tracks " + i);
            if (t && unwrap(t.get("can_be_armed")) && unwrap(t.get("arm"))) {
                t.set("arm", 0);
                modified++;
            }
        }
        return { ok: true, message: "Unarmed " + modified + " track(s)", action: action, count: modified };
    }

    if (action === "unmute_all") {
        for (var j = 0; j < nTracks; j++) {
            var tm = liveApi("live_set tracks " + j);
            if (tm && unwrap(tm.get("mute"))) {
                tm.set("mute", 0);
                modified++;
            }
        }
        return { ok: true, message: "Unmuted " + modified + " track(s)", action: action, count: modified };
    }

    if (action === "unsolo_all") {
        for (var k = 0; k < nTracks; k++) {
            var ts = liveApi("live_set tracks " + k);
            if (ts && unwrap(ts.get("solo"))) {
                ts.set("solo", 0);
                modified++;
            }
        }
        return { ok: true, message: "Unsoloed " + modified + " track(s)", action: action, count: modified };
    }

    if (action === "solo_exclusive") {
        if (trkIdx < 0 || trkIdx >= nTracks) return { ok: false, error: "Provide a valid track_index (0.." + (nTracks - 1) + ") for solo_exclusive" };
        for (var m = 0; m < nTracks; m++) {
            var te = liveApi("live_set tracks " + m);
            if (te) {
                te.set("solo", m === trkIdx ? 1 : 0);
            }
        }
        return { ok: true, message: "Exclusively soloed track " + trkIdx, action: action, soloed_track: trkIdx };
    }

    return { ok: false, error: "Unknown batch action: " + action + ". Supported: unarm_all, unmute_all, unsolo_all, solo_exclusive" };
}

function palStopAllClips() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("stop_all_clips");
        return { ok: true, message: "Stopped all playing clips across the session." };
    } catch (e) {
        return { ok: false, error: "stop_all_clips failed: " + String(e) };
    }
}

function palTapTempo() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("tap_tempo");
        var tempo = Number(unwrap(song.get("tempo")) || 120);
        return { ok: true, message: "Tapped tempo. Current tempo: " + tempo.toFixed(1) + " BPM", tempo: tempo };
    } catch (e) {
        return { ok: false, error: "tap_tempo failed: " + String(e) };
    }
}

function palContinuePlaying() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    try {
        song.call("continue_playing");
        return { ok: true, message: "Resumed transport playback from current playhead position." };
    } catch (e) {
        return { ok: false, error: "continue_playing failed: " + String(e) };
    }
}

function palScrub(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var beats = Number(params && params.beats != null ? params.beats : ((params && params.delta != null) ? params.delta : 4.0));
    try {
        song.call("scrub_by", beats);
        var curTime = Number(unwrap(song.get("current_song_time")) || 0);
        return { ok: true, message: "Scrubbed playhead by " + beats + " beats (now at beat " + curTime + ")", current_time: curTime };
    } catch (e) {
        return { ok: false, error: "scrub_by failed: " + String(e) };
    }
}

function palJumpCue(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var dir = String((params && params.direction) || "next").toLowerCase();
    try {
        if (dir === "prev" || dir === "previous") {
            song.call("jump_to_prev_cue");
            return { ok: true, message: "Jumped to previous cue point/locator" };
        } else {
            song.call("jump_to_next_cue");
            return { ok: true, message: "Jumped to next cue point/locator" };
        }
    } catch (e) {
        return { ok: false, error: "jump cue failed: " + String(e) };
    }
}

function palSetPunch(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var changes = [];
    var notApplied = [];
    if (params && (params.punch_in != null || params.punchIn != null)) {
        var pi = (params.punch_in != null ? params.punch_in : params.punchIn) ? 1 : 0;
        if (palSetChecked(song, "punch_in", pi)) changes.push("punch_in=" + (pi ? "on" : "off"));
        else notApplied.push("punch_in");
    }
    if (params && (params.punch_out != null || params.punchOut != null)) {
        var po = (params.punch_out != null ? params.punch_out : params.punchOut) ? 1 : 0;
        if (palSetChecked(song, "punch_out", po)) changes.push("punch_out=" + (po ? "on" : "off"));
        else notApplied.push("punch_out");
    }
    var punchResult = { ok: notApplied.length === 0, message: "Punch settings: " + (changes.join(", ") || "unchanged") };
    if (notApplied.length) punchResult.not_applied = notApplied;
    return punchResult;
}

function palSetCueVolume(params) {
    var cueParam = liveApi("live_set master_track mixer_device cue_volume");
    if (!cueParam) return { ok: false, error: "Cue volume parameter not found" };
    var vol = Number(params && params.volume != null ? params.volume : ((params && params.cue_volume != null) ? params.cue_volume : 0.85));
    var pMin = Number(unwrap(cueParam.get("min")));
    var pMax = Number(unwrap(cueParam.get("max")));
    if (!isNaN(pMin) && !isNaN(pMax) && pMax > pMin) vol = Math.max(pMin, Math.min(pMax, vol));
    try {
        cueParam.set("value", vol);
        var readBack = Number(unwrap(cueParam.get("value")));
        return { ok: true, message: "Set cue volume to " + readBack, cue_volume: readBack };
    } catch (e) {
        return { ok: false, error: "Failed to set cue volume: " + String(e) };
    }
}

function palMoveDevice(params) {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Live API not ready" };
    var trkIdx = Number(params && params.track_index != null ? params.track_index : 0);
    var devIdx = Number(params && params.device_index != null ? params.device_index : 0);
    var newIdx = Number(params && params.new_device_index != null ? params.new_device_index : ((params && params.new_index != null) ? params.new_index : 0));
    if (params && params.direction) {
        var dir = String(params.direction).toLowerCase();
        if (dir === "left" || dir === "prev" || dir === "up") {
            newIdx = Math.max(0, devIdx - 1);
        } else if (dir === "right" || dir === "next" || dir === "down") {
            newIdx = devIdx + 1;
        }
    }

    var track = liveApi("live_set tracks " + trkIdx);
    if (!track) return { ok: false, error: "Track not found: " + trkIdx };
    var dev = liveApi("live_set tracks " + trkIdx + " devices " + devIdx);
    if (!dev) return { ok: false, error: "Device not found at track " + trkIdx + ", index " + devIdx };

    var devId = extractId(dev.id);
    var trkId = extractId(track.id);

    try {
        if (devId && trkId) {
            song.call("move_device", "id", devId, "id", trkId, newIdx);
        } else {
            song.call("move_device", dev, track, newIdx);
        }
        return {
            ok: true,
            message: "Moved device " + devIdx + " to position " + newIdx + " on track " + trkIdx,
            track_index: trkIdx,
            old_index: devIdx,
            new_index: newIdx
        };
    } catch (e) {
        return { ok: false, error: "move_device failed: " + String(e) };
    }
}

function palReadDrumPads(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide track_index + device_index" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found: " + loc.devicePath };
    if (!unwrap(device.get("can_have_drum_pads"))) {
        return { ok: false, error: "Device is not a Drum Rack" };
    }

    var pads = [];
    var nPads = 0;
    try { nPads = device.getcount("drum_pads"); } catch (e) { nPads = 0; }

    for (var i = 0; i < nPads; i++) {
        var pad = liveApi(loc.devicePath + " drum_pads " + i);
        if (pad) {
            var chainsCount = 0;
            try { chainsCount = pad.getcount("chains"); } catch (eC) {}
            if (chainsCount > 0 || (params && params.all)) {
                pads.push({
                    index: i,
                    note: Number(unwrap(pad.get("note")) || i),
                    name: String(unwrap(pad.get("name")) || ("Pad " + i)),
                    mute: !!unwrap(pad.get("mute")),
                    solo: !!unwrap(pad.get("solo")),
                    chains_count: chainsCount
                });
            }
        }
    }

    return {
        ok: true,
        track_index: loc.track,
        device_index: loc.device,
        device_name: String(unwrap(device.get("name")) || "Drum Rack"),
        total_active_pads: pads.length,
        drum_pads: pads
    };
}

function palUpdateDrumPad(params) {
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide track_index + device_index" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found: " + loc.devicePath };
    if (!unwrap(device.get("can_have_drum_pads"))) {
        return { ok: false, error: "Device is not a Drum Rack" };
    }

    var targetNote = params && params.pad_note != null ? params.pad_note : ((params && params.note != null) ? params.note : (params && params.pad_index));
    if (targetNote == null) return { ok: false, error: "Provide pad_note (e.g. 36 or 'C1')" };
    if (typeof targetNote === "string" && !/^\d+$/.test(targetNote)) {
        targetNote = palNoteToPitch(targetNote);
    }
    targetNote = Number(targetNote);

    var nPads = 0;
    try { nPads = device.getcount("drum_pads"); } catch (e) { nPads = 0; }

    var targetPad = null;
    for (var i = 0; i < nPads; i++) {
        var p = liveApi(loc.devicePath + " drum_pads " + i);
        if (p && Number(unwrap(p.get("note"))) === targetNote) {
            targetPad = p;
            break;
        }
    }

    if (!targetPad) return { ok: false, error: "Drum pad for note " + targetNote + " not found" };

    var changes = [];
    var padNotApplied = [];
    if (params.name != null) {
        if (palSetChecked(targetPad, "name", String(params.name))) changes.push("name='" + params.name + "'");
        else padNotApplied.push("name");
    }
    if (params.mute != null) {
        var m = params.mute ? 1 : 0;
        if (palSetChecked(targetPad, "mute", m)) changes.push("mute=" + (m ? "on" : "off"));
        else padNotApplied.push("mute");
    }
    if (params.solo != null) {
        var s = params.solo ? 1 : 0;
        if (palSetChecked(targetPad, "solo", s)) changes.push("solo=" + (s ? "on" : "off"));
        else padNotApplied.push("solo");
    }

    var padResult = {
        ok: padNotApplied.length === 0,
        message: "Updated drum pad (note " + targetNote + "): " + (changes.join(", ") || "no changes"),
        note: targetNote
    };
    if (padNotApplied.length) padResult.not_applied = padNotApplied;
    return padResult;
}

function palFocusView(params) {
    var appView = liveApi("live_app view");
    var songView = liveApi("live_set view");
    var view = String((params && params.view) || "").toLowerCase();
    var changes = [];
    var fvNotApplied = [];

    if (view && appView) {
        var viewNames = {
            "session": "Session",
            "arrangement": "Arranger",
            "arranger": "Arranger",
            "detail": "Detail",
            "clip": "Detail/Clip",
            "device": "Detail/DeviceChain"
        };
        var vTarget = viewNames[view] || view;
        try { appView.call("focus_view", vTarget); } catch (e) {}
        var visible = false;
        try { visible = !!unwrap(appView.call("is_view_visible", vTarget)); } catch (eVis) {}
        if (visible) {
            changes.push("focused " + vTarget);
        } else {
            try { appView.call("show_view", vTarget); } catch (e2) {}
            try { visible = !!unwrap(appView.call("is_view_visible", vTarget)); } catch (eVis2) {}
            if (visible) changes.push("showed " + vTarget);
            else fvNotApplied.push("view=" + vTarget);
        }
    }

    if (songView && params) {
        if (params.draw_mode != null || params.drawMode != null) {
            var dm = (params.draw_mode != null ? params.draw_mode : params.drawMode) ? 1 : 0;
            if (palSetChecked(songView, "draw_mode", dm)) changes.push("draw_mode=" + (dm ? "on" : "off"));
            else fvNotApplied.push("draw_mode");
        }
        if (params.follow_mode != null || params.followMode != null || params.follow_song != null) {
            var fm = (params.follow_mode != null ? params.follow_mode : (params.followMode != null ? params.followMode : params.follow_song)) ? 1 : 0;
            if (palSetChecked(songView, "follow_song", fm)) changes.push("follow_song=" + (fm ? "on" : "off"));
            else fvNotApplied.push("follow_song");
        }
    }

    var fvResult = { ok: fvNotApplied.length === 0, message: "View state: " + (changes.join(", ") || "no changes applied") };
    if (fvNotApplied.length) fvResult.not_applied = fvNotApplied;
    return fvResult;
}

// Ableton Link status has no confirmed property surface in the Max for Live
// LOM -- the property names below were guesses, never verified against a
// real Live session, and every guess that misses logs an error to the Max
// Console (LiveAPI.get() reports unknown properties there, not via a JS
// exception, so the try/catch around each guess doesn't prevent the spam).
// Report honestly unavailable instead of probing a dozen guessed names on
// every call (Low item).
function palReadLinkStatus() {
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };
    return {
        ok: true,
        available: false,
        message: "Ableton Link status is not exposed to the Max for Live Live Object Model -- check Link state in Live's own Link/Tempo/Time Signature panel instead."
    };
}

function palInspectPlugin(params) {
    var loc = palTrackPath(params);
    var devIdx = Number(params.device_index != null ? params.device_index : (params.index != null ? params.index : 0));
    var dev = liveApi(loc.path + " devices " + devIdx);
    if (!dev) return { ok: false, error: "Device " + devIdx + " not found on track " + loc.index };

    var name = String(unwrap(dev.get("name")) || "");
    var className = String(unwrap(dev.get("class_name")) || "");
    var classDisplayName = String(unwrap(dev.get("class_display_name")) || "");
    var devType = String(unwrap(dev.get("type")) || "");
    var isActive = !!unwrap(dev.get("is_active"));
    var canChains = !!unwrap(dev.get("can_have_chains"));
    var canDrum = !!unwrap(dev.get("can_have_drum_pads"));
    var paramCount = 0;
    try { paramCount = dev.getcount("parameters"); } catch (eCount) {}

    var presets = [];
    try {
        var rawPresets = dev.get("presets");
        if (rawPresets && rawPresets.length) {
            presets = Array.isArray(rawPresets) ? rawPresets : [rawPresets];
        }
    } catch (ePre) {}

    var isPlugin = (className === "PluginDevice" || devType === "plugin" || presets.length > 0);
    var isM4l = (className.indexOf("Max") >= 0 || className.indexOf("Mx") >= 0 || name.indexOf(".amxd") >= 0);

    return {
        ok: true,
        device_index: devIdx,
        track_index: loc.index,
        name: name,
        class_name: className,
        class_display_name: classDisplayName,
        type: devType || (isPlugin ? "plugin" : (isM4l ? "max_for_live" : "native")),
        is_plugin: isPlugin,
        is_max_for_live: isM4l,
        is_active: isActive,
        can_have_chains: canChains,
        can_have_drum_pads: canDrum,
        total_parameters: paramCount,
        presets: presets
    };
}

function palSessionSnapshot(params) {
    params = params || {};
    var song = liveApi("live_set");
    if (!song) return { ok: false, error: "Cannot access live_set" };

    var includeClips = params.include_clips !== false;
    var includeDevices = params.include_devices !== false;

    var totalTracks = song.getcount("tracks");
    var numTracks = Math.min(totalTracks, PAL_TRACKS_CAP);
    var tracksTruncated = totalTracks > PAL_TRACKS_CAP;
    var PAL_SNAPSHOT_SLOT_CAP = 64;
    var tracks = [];
    var i;
    for (i = 0; i < numTracks; i++) {
        var trk = liveApi("live_set tracks " + i);
        if (!trk) continue;

        var vol = liveApi("live_set tracks " + i + " mixer_device volume");
        var pan = liveApi("live_set tracks " + i + " mixer_device panning");

        var trkInfo = {
            index: i,
            name: String(unwrap(trk.get("name")) || "Track " + (i + 1)),
            color: unwrap(trk.get("color")),
            is_midi: !!unwrap(trk.get("has_midi_input")),
            is_audio: !!unwrap(trk.get("has_audio_input")),
            mute: !!unwrap(trk.get("mute")),
            solo: !!unwrap(trk.get("solo")),
            arm: !!unwrap(trk.get("arm")),
            volume: vol ? Number(unwrap(vol.get("value")) || 0) : 0,
            panning: pan ? Number(unwrap(pan.get("value")) || 0) : 0
        };

        if (includeClips) {
            var nSlots = Math.min(trk.getcount("clip_slots"), PAL_SNAPSHOT_SLOT_CAP);
            var clips = [];
            var si;
            for (si = 0; si < nSlots; si++) {
                var sl = liveApi("live_set tracks " + i + " clip_slots " + si);
                if (sl && unwrap(sl.get("has_clip"))) {
                    var cl = liveApi("live_set tracks " + i + " clip_slots " + si + " clip");
                    if (cl) {
                        clips.push({
                            slot: si,
                            name: String(unwrap(cl.get("name")) || ""),
                            length: Number(unwrap(cl.get("length")) || 0),
                            is_playing: !!unwrap(cl.get("is_playing"))
                        });
                    }
                }
            }
            trkInfo.clips = clips;
        }

        if (includeDevices) {
            var nDevs = trk.getcount("devices");
            var devs = [];
            var di;
            for (di = 0; di < nDevs; di++) {
                var d = liveApi("live_set tracks " + i + " devices " + di);
                if (d) {
                    devs.push({
                        index: di,
                        name: String(unwrap(d.get("name")) || ""),
                        class_name: String(unwrap(d.get("class_name")) || ""),
                        is_active: !!unwrap(d.get("is_active"))
                    });
                }
            }
            trkInfo.devices = devs;
        }

        tracks.push(trkInfo);
    }

    var snapResult = {
        ok: true,
        ts: Date.now(),
        tempo: Number(unwrap(song.get("tempo")) || 120),
        is_playing: !!unwrap(song.get("is_playing")),
        song_time: Number(unwrap(song.get("current_song_time")) || 0),
        signature_numerator: Number(unwrap(song.get("signature_numerator")) || 4),
        signature_denominator: Number(unwrap(song.get("signature_denominator")) || 4),
        total_tracks: totalTracks,
        tracks: tracks
    };
    if (tracksTruncated) snapResult.tracks_truncated = true;
    return snapResult;
}

function palGetSelected() {
    var view = liveApi("live_set view");
    if (!view) return { ok: false, error: "Cannot access live_set view" };
    var song = liveApi("live_set");
    var res = {
        ok: true,
        selected: {
            track: null,
            scene: null,
            device: null,
            clip: null
        }
    };

    // 1. Selected Track -- may be a regular track, a return track, or the
    // master track; search all three so index/kind resolve everywhere
    // instead of only ever matching a regular track.
    var selTrackKind = "";   // "", "return", or "master" -- feeds the device lookup below
    var selTrackIndex = -1;
    try {
        var selTrkId = unwrap(view.get("selected_track"));
        if (selTrkId) {
            var trk = liveApi("live_set view selected_track");
            if (trk) {
                var trkId = extractId(trk.id);
                var trkName = String(unwrap(trk.get("name")) || "");
                var trkColor = (typeof hexToLiveColor === "function") ? ("#" + ("000000" + Number(unwrap(trk.get("color"))).toString(16)).slice(-6)) : unwrap(trk.get("color"));
                var isMidi = !!unwrap(trk.get("has_midi_input"));
                var isAudio = !!unwrap(trk.get("has_audio_input"));
                var nTrks = song.getcount("tracks");
                var trkIdx = -1;
                for (var ti = 0; ti < nTrks; ti++) {
                    var checkTrk = liveApi("live_set tracks " + ti);
                    if (checkTrk && extractId(checkTrk.id) === trkId) {
                        trkIdx = ti;
                        break;
                    }
                }
                var trkKind = isMidi ? "midi" : (isAudio ? "audio" : "unknown");
                if (trkIdx < 0) {
                    var masterTrk = liveApi("live_set master_track");
                    if (masterTrk && extractId(masterTrk.id) === trkId) {
                        trkKind = "master";
                        selTrackKind = "master";
                    } else {
                        var nReturns = song.getcount("return_tracks");
                        for (var ri = 0; ri < nReturns; ri++) {
                            var checkReturn = liveApi("live_set return_tracks " + ri);
                            if (checkReturn && extractId(checkReturn.id) === trkId) {
                                trkIdx = ri;
                                trkKind = "return";
                                selTrackKind = "return";
                                break;
                            }
                        }
                    }
                }
                selTrackIndex = trkIdx;
                var safeBool = function (api, prop) {
                    try { return !!unwrap(api.get(prop)); } catch (eProp) { return false; }
                };
                res.selected.track = {
                    index: trkIdx,
                    id: trkId,
                    name: trkName,
                    kind: trkKind,
                    color: trkColor,
                    is_muted: safeBool(trk, "mute"),
                    is_soloed: safeBool(trk, "solo"),
                    is_armed: safeBool(trk, "arm")
                };
            }
        }
    } catch (eTrk) {}

    // 2. Selected Scene
    try {
        var selScnId = unwrap(view.get("selected_scene"));
        if (selScnId) {
            var scn = liveApi("live_set view selected_scene");
            if (scn) {
                var scnId = extractId(scn.id);
                var scnName = String(unwrap(scn.get("name")) || "");
                var nScns = song.getcount("scenes");
                var scnIdx = -1;
                for (var si = 0; si < nScns; si++) {
                    var checkScn = liveApi("live_set scenes " + si);
                    if (checkScn && extractId(checkScn.id) === scnId) {
                        scnIdx = si;
                        break;
                    }
                }
                res.selected.scene = {
                    index: scnIdx,
                    id: scnId,
                    name: scnName
                };
            }
        }
    } catch (eScn) {}

    // 3. Selected Device -- device selection lives on the TRACK's own view,
    // not Song.view (there is no Song.view.selected_device in the LOM;
    // that path previously resolved to a stale object from an unrelated
    // prior LiveAPI call instead of erroring, which is why this always
    // reported index -1 -- M2 in the v1.0.26 audit).
    try {
        var selDevTrackPath = selTrackKind === "master" ? "live_set master_track"
            : selTrackKind === "return" ? "live_set return_tracks " + selTrackIndex
            : selTrackIndex >= 0 ? "live_set tracks " + selTrackIndex
            : null;
        var selDev = selDevTrackPath ? liveApi(selDevTrackPath + " view selected_device") : null;
        if (selDev && extractId(selDev.id)) {
            var devId = extractId(selDev.id);
            var devName = String(unwrap(selDev.get("name")) || "");
            var devClass = String(unwrap(selDev.get("class_name")) || "");
            var devType = String(unwrap(selDev.get("type")) || "");
            var devIdx = -1;
            var selTrackApi = liveApi(selDevTrackPath);
            var nDevs = 0;
            try { nDevs = selTrackApi ? selTrackApi.getcount("devices") : 0; } catch (eDevCnt) { nDevs = 0; }
            for (var di = 0; di < nDevs; di++) {
                var checkDev = liveApi(selDevTrackPath + " devices " + di);
                if (checkDev && extractId(checkDev.id) === devId) {
                    devIdx = di;
                    break;
                }
            }
            res.selected.device = {
                index: devIdx,
                id: devId,
                name: devName,
                class_name: devClass,
                type: devType,
                is_active: !!unwrap(selDev.get("is_active"))
            };
        }
    } catch (eDev) {}

    // 4. Detail Clip
    try {
        var detailClip = liveApi("live_set view detail_clip");
        if (detailClip && extractId(detailClip.id)) {
            var clipId = extractId(detailClip.id);
            var clipName = String(unwrap(detailClip.get("name")) || "");
            var clipLen = Number(unwrap(detailClip.get("length")) || 0);
            var isMidiClip = !!unwrap(detailClip.get("is_midi_clip"));
            var isAudioClip = !!unwrap(detailClip.get("is_audio_clip"));
            res.selected.clip = {
                id: clipId,
                name: clipName,
                length: clipLen,
                is_midi: isMidiClip,
                is_audio: isAudioClip,
                is_playing: !!unwrap(detailClip.get("is_playing"))
            };
        }
    } catch (eClip) {}

    return res;
}

function palClearClipEnvelopes(params) {
    params = params || {};
    var trackIndex = params.track_index;
    if (trackIndex === undefined || trackIndex === null) {
        return { ok: false, error: "track_index is required" };
    }
    var clip = null;
    var locationDesc = "";

    if (params.arrangement_clip_index !== undefined || params.clip_index !== undefined) {
        var aIdx = params.arrangement_clip_index !== undefined ? params.arrangement_clip_index : params.clip_index;
        var trk = liveApi("live_set tracks " + trackIndex);
        if (!trk) return { ok: false, error: "Cannot access track " + trackIndex };
        var nArr = trk.getcount("arrangement_clips");
        if (aIdx < 0 || aIdx >= nArr) {
            return { ok: false, error: "Arrangement clip index " + aIdx + " out of range (0-" + (nArr - 1) + ")" };
        }
        clip = liveApi("live_set tracks " + trackIndex + " arrangement_clips " + aIdx);
        locationDesc = "arrangement clip " + aIdx + " on track " + trackIndex;
    } else {
        var slotIndex = params.slot_index;
        if (slotIndex === undefined || slotIndex === null) {
            return { ok: false, error: "slot_index (or arrangement_clip_index) is required" };
        }
        var slot = liveApi("live_set tracks " + trackIndex + " clip_slots " + slotIndex);
        if (!slot) return { ok: false, error: "Cannot access clip slot " + slotIndex + " on track " + trackIndex };
        if (!unwrap(slot.get("has_clip"))) {
            return { ok: false, error: "No clip in slot " + slotIndex + " on track " + trackIndex };
        }
        clip = liveApi("live_set tracks " + trackIndex + " clip_slots " + slotIndex + " clip");
        locationDesc = "session clip on track " + trackIndex + " slot " + slotIndex;
    }

    if (!clip) {
        return { ok: false, error: "Failed to access clip at " + locationDesc };
    }

    try {
        clip.call("clear_all_envelopes");
        var clipName = String(unwrap(clip.get("name")) || "");
        return {
            ok: true,
            message: "Successfully cleared all automation envelopes for " + locationDesc + (clipName ? " ('" + clipName + "')" : "") + "."
        };
    } catch (e) {
        return { ok: false, error: "Error clearing envelopes: " + e.message };
    }
}

function palMapRackMagnitude(params) {
    params = params || {};
    var loc = palFindDevice(params);
    if (!loc) return { ok: false, error: "Provide path (e.g. t0/d0) or track_index + device_index" };
    var device = liveApi(loc.devicePath);
    if (!device) return { ok: false, error: "Device not found at " + loc.devicePath };

    var canHaveChains = false;
    try { canHaveChains = !!unwrap(device.get("can_have_chains")); } catch (e) {}
    if (!canHaveChains) {
        return { ok: false, error: "Device '" + String(unwrap(device.get("name")) || "") + "' is not a Rack (can_have_chains is false)" };
    }

    var rackName = String(unwrap(device.get("name")) || "Rack");
    var macroName = params.macro_name || params.name || "Magnitude";
    var macroIdx = params.macro_index !== undefined && params.macro_index !== null ? Number(params.macro_index) : 0;
    if (isNaN(macroIdx) || macroIdx < 0) macroIdx = 0;

    // Ensure at least macroIdx + 1 macros are visible
    try {
        var visible = Number(unwrap(device.get("visible_macro_count")) || 0);
        if (visible <= macroIdx) {
            try { device.set("visible_macro_count", macroIdx + 1); } catch (eVis) {}
            try {
                if (Number(unwrap(device.get("visible_macro_count")) || 0) <= macroIdx && device.call) {
                    device.call("add_macro");
                }
            } catch (eAdd) {}
        }
    } catch (eMacroVis) {}

    // Locate the macro's parameter first so rename_macro can be verified by
    // re-reading its name -- device.call() never throws on an unsupported
    // method (M1/M4), so "it didn't throw" is not evidence it worked.
    var base = device.unquotedpath || device.path;
    var macroParam = null;
    try {
        var p = liveApi(base + " parameters " + (macroIdx + 1));
        if (p) macroParam = p;
    } catch (eP) {}

    var renamed = false;
    try {
        if (device.call) device.call("rename_macro", macroIdx, macroName);
    } catch (eRename) {}
    if (macroParam) {
        var nameAfterRename = "";
        try { nameAfterRename = String(unwrap(macroParam.get("name")) || ""); } catch (eNr) {}
        if (nameAfterRename === macroName) {
            renamed = true;
        } else if (palSetChecked(macroParam, "name", macroName)) {
            renamed = true;
        }
    }

    // Preferred blend parameter names
    var preferredNames = ["dry/wet", "dry wet", "mix", "amount", "blend", "wet"];
    if (params.blend_names && Array.isArray(params.blend_names)) {
        preferredNames = params.blend_names.map(function(s) { return String(s).toLowerCase(); });
    }

    // Traverse all chains and nested devices
    var chainCount = 0;
    try { chainCount = device.getcount("chains"); } catch (eCh) { chainCount = 0; }
    var mapped = [];
    var skipped = [];
    var macroMapSupported = false;

    for (var cIdx = 0; cIdx < chainCount; cIdx++) {
        var chainPath = loc.devicePath + " chains " + cIdx;
        var chain = liveApi(chainPath);
        if (!chain) continue;
        var chainName = String(unwrap(chain.get("name")) || ("Chain " + (cIdx + 1)));

        var devCount = 0;
        try { devCount = chain.getcount("devices"); } catch (eDc) { devCount = 0; }

        for (var dIdx = 0; dIdx < devCount; dIdx++) {
            var nestedPath = chainPath + " devices " + dIdx;
            var nested = liveApi(nestedPath);
            if (!nested) continue;
            var nestedName = String(unwrap(nested.get("name")) || ("Device " + dIdx));
            var nestedClass = String(unwrap(nested.get("class_name")) || "");

            // Scan parameters for blend control
            var paramCount = 0;
            try { paramCount = nested.getcount("parameters"); } catch (ePc) { paramCount = 0; }
            var blendParam = null;
            var blendParamName = "";
            var blendParamIdx = -1;

            for (var pIdx = 0; pIdx < paramCount; pIdx++) {
                var pNested = liveApi(nestedPath + " parameters " + pIdx);
                if (!pNested) continue;
                var pname = String(unwrap(pNested.get("name")) || "");
                var pnameLower = pname.toLowerCase();

                var isMatch = false;
                for (var mIdx = 0; mIdx < preferredNames.length; mIdx++) {
                    if (pnameLower === preferredNames[mIdx] || pnameLower.indexOf(preferredNames[mIdx]) !== -1) {
                        isMatch = true;
                        break;
                    }
                }

                if (isMatch) {
                    blendParam = pNested;
                    blendParamName = pname;
                    blendParamIdx = pIdx;
                    break;
                }
            }

            if (!blendParam) {
                skipped.push({
                    chain_index: cIdx,
                    chain_name: chainName,
                    device_index: dIdx,
                    device_name: nestedName,
                    device_class: nestedClass,
                    reason: "no Dry/Wet, Mix, or Amount parameter found"
                });
                continue;
            }

            var paramVal = Number(unwrap(blendParam.get("value")));
            var paramMin = Number(unwrap(blendParam.get("min")));
            var paramMax = Number(unwrap(blendParam.get("max")));
            var paramId = extractId(blendParam.id);

            // device.call() never throws on an unsupported method (M1/M4), so
            // "it didn't throw" only means the Rack API accepted the call --
            // it is not proof the mapping now exists, and this codebase has
            // no LOM read-back that can confirm a macro_map actually took.
            // macro_map_api_supported records that weak non-throw signal;
            // `mapped` stays honestly false unconditionally, and the value
            // writes below (set_directly) are the real, verifiable fallback
            // magnitude control actually relies on.
            try {
                if (device.call) {
                    device.call("macro_map", macroIdx, "id", paramId);
                    macroMapSupported = true;
                }
            } catch (eMap) {
                try {
                    device.call("macro_map", macroIdx, paramId);
                    macroMapSupported = true;
                } catch (eMap2) {}
            }

            mapped.push({
                chain_index: cIdx,
                chain_name: chainName,
                device_index: dIdx,
                device_name: nestedName,
                device_class: nestedClass,
                parameter_name: blendParamName,
                parameter_index: blendParamIdx,
                parameter_id: paramId,
                current_value: paramVal,
                min: paramMin,
                max: paramMax,
                mapped: false,
                set_directly: false
            });
        }
    }

    // Resolve the requested magnitude to a single 0..1 fraction so both the
    // macro (if renamed/visible) and every discovered blend parameter can be
    // driven directly -- this is what actually works regardless of whether
    // macro_map's silent-on-failure call above did anything real.
    var updatedValue = null;
    var norm = null;
    if (params.value_normalized !== undefined && params.value_normalized !== null) {
        norm = Math.max(0.0, Math.min(1.0, Number(params.value_normalized)));
    } else if (params.value !== undefined && params.value !== null && macroParam) {
        var minM0 = Number(unwrap(macroParam.get("min")));
        var maxM0 = Number(unwrap(macroParam.get("max")));
        if (!isNaN(minM0) && !isNaN(maxM0) && maxM0 > minM0) {
            norm = Math.max(0.0, Math.min(1.0, (Number(params.value) - minM0) / (maxM0 - minM0)));
        }
    }

    if (norm !== null && macroParam) {
        var minM = Number(unwrap(macroParam.get("min")));
        var maxM = Number(unwrap(macroParam.get("max")));
        macroParam.set("value", minM + norm * (maxM - minM));
        updatedValue = Number(unwrap(macroParam.get("value")));
    } else if (params.value !== undefined && params.value !== null && macroParam) {
        macroParam.set("value", Number(params.value));
        updatedValue = Number(unwrap(macroParam.get("value")));
    } else if (macroParam) {
        updatedValue = Number(unwrap(macroParam.get("value")));
    }

    if (norm !== null) {
        for (var k = 0; k < mapped.length; k++) {
            var item = mapped[k];
            var pTarget = liveApi(loc.devicePath + " chains " + item.chain_index + " devices " + item.device_index + " parameters " + item.parameter_index);
            if (pTarget) {
                try {
                    pTarget.set("value", item.min + norm * (item.max - item.min));
                    item.set_directly = true;
                } catch (eSetNorm) {}
            }
        }
    }

    return {
        ok: true,
        rack_name: rackName,
        rack_path: loc.devicePath,
        macro_index: macroIdx,
        macro_name: macroName,
        macro_renamed: renamed,
        macro_map_api_supported: macroMapSupported,
        chains_scanned: chainCount,
        mapped_count: 0,
        mapped: mapped,
        skipped_count: skipped.length,
        skipped: skipped,
        current_macro_value: updatedValue
    };
}

function palSetClipFollowAction(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    var faNames = {"none": 0, "stop": 1, "again": 2, "previous": 3, "prev": 3, "next": 4, "first": 5, "last": 6, "any": 7, "other": 8, "jump": 9};
    var notApplied = [];

    var hasAnyField = params.action_a != null || params.follow_action_a != null ||
        params.action_b != null || params.follow_action_b != null ||
        params.chance != null || params.follow_action_chance != null ||
        params.time != null || params.follow_action_time != null ||
        params.enabled != null || params.follow_action_enabled != null;
    if (!hasAnyField) {
        return { ok: false, error: "No follow-action fields provided (action_a, action_b, chance, time, or enabled)." };
    }

    if (params.action_a != null || params.follow_action_a != null) {
        var a = params.action_a != null ? params.action_a : params.follow_action_a;
        if (typeof a === "string" && faNames[a.toLowerCase()] != null) a = faNames[a.toLowerCase()];
        if (!palSetChecked(clip, "follow_action_a", Number(a))) notApplied.push("follow_action_a");
    }
    if (params.action_b != null || params.follow_action_b != null) {
        var b = params.action_b != null ? params.action_b : params.follow_action_b;
        if (typeof b === "string" && faNames[b.toLowerCase()] != null) b = faNames[b.toLowerCase()];
        if (!palSetChecked(clip, "follow_action_b", Number(b))) notApplied.push("follow_action_b");
    }
    if (params.chance != null || params.follow_action_chance != null) {
        var ch = params.chance != null ? params.chance : params.follow_action_chance;
        if (!palSetChecked(clip, "follow_action_chance", Math.max(0, Math.min(1, Number(ch))))) notApplied.push("follow_action_chance");
    }
    if (params.time != null || params.follow_action_time != null) {
        var t = params.time != null ? params.time : params.follow_action_time;
        if (!palSetChecked(clip, "follow_action_time", Number(t))) notApplied.push("follow_action_time");
    }
    if (params.enabled != null || params.follow_action_enabled != null) {
        var en = (params.enabled != null ? params.enabled : params.follow_action_enabled) ? 1 : 0;
        if (!palSetChecked(clip, "follow_action_enabled", en)) notApplied.push("follow_action_enabled");
    }

    var result = palGetClipFollowAction(params);
    if (notApplied.length) {
        result.not_applied = notApplied;
        result.ok = false;
    }
    return result;
}

function palGetClipFollowAction(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    var actionNames = ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"];
    var a = Number(unwrap(clip.get("follow_action_a")) || 0);
    var b = Number(unwrap(clip.get("follow_action_b")) || 0);
    var ch = Number(unwrap(clip.get("follow_action_chance")) || 0);
    var t = Number(unwrap(clip.get("follow_action_time")) || 0);
    var en = !!unwrap(clip.get("follow_action_enabled"));

    return {
        ok: true,
        track_index: loc.track,
        slot_index: loc.slot,
        follow_action_a: a,
        follow_action_a_name: (a >= 0 && a < actionNames.length) ? actionNames[a] : "unknown",
        follow_action_b: b,
        follow_action_b_name: (b >= 0 && b < actionNames.length) ? actionNames[b] : "unknown",
        follow_action_chance: ch,
        follow_action_time: t,
        follow_action_enabled: en
    };
}

function palSetClipLaunchMode(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    var lmMap = { "trigger": 0, "gate": 1, "toggle": 2, "repeat": 3 };
    var lqMap = { "global": 0, "none": 1, "8_bars": 2, "8 bars": 2, "4_bars": 3, "4 bars": 3, "2_bars": 4, "2 bars": 4, "1_bar": 5, "1 bar": 5, "1/2": 6, "1/2t": 7, "1/4": 8, "1/4t": 9, "1/8": 10, "1/8t": 11, "1/16": 12, "1/16t": 13, "1/32": 14 };

    var notAppliedLm = [];
    if (params.launch_mode != null || params.mode != null) {
        var lm = params.launch_mode != null ? params.launch_mode : params.mode;
        if (typeof lm === "string" && lmMap[lm.toLowerCase()] != null) lm = lmMap[lm.toLowerCase()];
        if (!palSetChecked(clip, "launch_mode", Number(lm))) notAppliedLm.push("launch_mode");
    }
    if (params.launch_quantization != null || params.quantization != null) {
        var lq = params.launch_quantization != null ? params.launch_quantization : params.quantization;
        if (typeof lq === "string" && lqMap[lq.toLowerCase()] != null) lq = lqMap[lq.toLowerCase()];
        if (!palSetChecked(clip, "launch_quantization", Number(lq))) notAppliedLm.push("launch_quantization");
    }
    if (params.legato != null) {
        if (!palSetChecked(clip, "legato", params.legato ? 1 : 0)) notAppliedLm.push("legato");
    }

    var lmNames = ["trigger", "gate", "toggle", "repeat"];
    var currentLm = Number(unwrap(clip.get("launch_mode")) || 0);
    var lmResult = {
        ok: true,
        track_index: loc.track,
        slot_index: loc.slot,
        launch_mode: currentLm,
        launch_mode_name: (currentLm >= 0 && currentLm < lmNames.length) ? lmNames[currentLm] : "unknown",
        launch_quantization: Number(unwrap(clip.get("launch_quantization")) || 0),
        legato: !!unwrap(clip.get("legato"))
    };
    if (notAppliedLm.length) {
        lmResult.not_applied = notAppliedLm;
        lmResult.ok = false;
    }
    return lmResult;
}

function palSetClipFades(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (!unwrap(clip.get("is_audio_clip"))) {
        return { ok: false, error: "Fades are only supported on audio clips." };
    }

    var notAppliedFades = [];
    if (params.fade_in_start != null && !palSetChecked(clip, "fade_in_start", Number(params.fade_in_start))) notAppliedFades.push("fade_in_start");
    if (params.fade_in_end != null && !palSetChecked(clip, "fade_in_end", Number(params.fade_in_end))) notAppliedFades.push("fade_in_end");
    if (params.fade_out_start != null && !palSetChecked(clip, "fade_out_start", Number(params.fade_out_start))) notAppliedFades.push("fade_out_start");
    if (params.fade_out_end != null && !palSetChecked(clip, "fade_out_end", Number(params.fade_out_end))) notAppliedFades.push("fade_out_end");

    var fadesResult = {
        ok: notAppliedFades.length === 0,
        message: "Updated fades for audio clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot),
        track_index: loc.track,
        slot_index: loc.slot,
        fade_in_start: Number(unwrap(clip.get("fade_in_start")) || 0),
        fade_in_end: Number(unwrap(clip.get("fade_in_end")) || 0),
        fade_out_start: Number(unwrap(clip.get("fade_out_start")) || 0),
        fade_out_end: Number(unwrap(clip.get("fade_out_end")) || 0)
    };
    if (notAppliedFades.length) fadesResult.not_applied = notAppliedFades;
    return fadesResult;
}

function palSetClipMarkers(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    if (params.start_marker != null) try { clip.set("start_marker", Number(params.start_marker)); } catch (eSm) {}
    if (params.end_marker != null) try { clip.set("end_marker", Number(params.end_marker)); } catch (eEm) {}
    var loopStart = params.loop_start != null ? params.loop_start : params.start_time;
    var loopEnd = params.loop_end != null ? params.loop_end : params.end_time;
    if (loopStart != null) try { clip.set("loop_start", Number(loopStart)); } catch (eLs) {}
    if (loopEnd != null) try { clip.set("loop_end", Number(loopEnd)); } catch (eLe) {}

    return {
        ok: true,
        message: "Updated markers for clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot),
        track_index: loc.track,
        slot_index: loc.slot,
        start_marker: Number(unwrap(clip.get("start_marker")) || 0),
        end_marker: Number(unwrap(clip.get("end_marker")) || 0),
        loop_start: Number(unwrap(clip.get("loop_start")) || 0),
        loop_end: Number(unwrap(clip.get("loop_end")) || 0)
    };
}

// Pure (no LiveAPI) half of the warp_markers get path: join a possibly-
// fragmented Max atom list back into one JSON string and parse it. Returns
// { handled: false } when rawWm is neither a string nor a string-atom
// array, so the caller falls back to the older flat id-pairs form (which
// does need liveApi and stays inline in palManageWarpMarkers).
function palJoinAndParseWarpMarkers(rawWm) {
    var joined = null;
    if (typeof rawWm === "string") {
        joined = rawWm;
    } else if (rawWm instanceof Array && rawWm.length && typeof rawWm[0] === "string") {
        joined = rawWm.join("");
    }
    if (joined === null) return { handled: false };
    try {
        var parsed = JSON.parse(joined);
        if (parsed && parsed.warp_markers) parsed = parsed.warp_markers;
        if (!(parsed instanceof Array)) return { handled: true, parseFailed: true };
        var markers = [];
        for (var j = 0; j < parsed.length; j++) {
            markers.push({
                beat_time: Number(parsed[j].beat_time || 0),
                sample_time: Number(parsed[j].sample_time || 0)
            });
        }
        return { handled: true, parseFailed: false, markers: markers };
    } catch (eParseWm) {
        return { handled: true, parseFailed: true };
    }
}

function palManageWarpMarkers(params) {
    params = params || {};
    var action = String(params.action || "get").toLowerCase();
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    if (!unwrap(clip.get("is_audio_clip"))) {
        return { ok: false, error: "Warp markers are only supported on audio clips." };
    }

    if (action === "add" || action === "insert") {
        if (params.beat_time == null) return { ok: false, error: "beat_time is required to add warp marker" };
        var bt = Number(params.beat_time);
        var markerDict = { beat_time: bt };
        if (params.sample_time != null) markerDict.sample_time = Number(params.sample_time);
        var countBefore = 0;
        try { countBefore = clip.getcount("warp_markers"); } catch (eCnt) {}
        try {
            var d = new Dict();
            d.parse(JSON.stringify(markerDict));
            clip.call("add_warp_marker", d);
            d.freepeer();
        } catch (eAdd) {
            return { ok: false, error: "Failed to add warp marker: " + (eAdd && eAdd.message ? eAdd.message : String(eAdd)) };
        }
        var countAfter = countBefore;
        try { countAfter = clip.getcount("warp_markers"); } catch (eCnt2) {}
        if (countAfter <= countBefore) {
            return { ok: false, error: "add_warp_marker did not insert a marker (count unchanged at " + countBefore + ")", track_index: loc.track, slot_index: loc.slot, beat_time: bt };
        }
        return { ok: true, message: "Added warp marker at beat " + bt, track_index: loc.track, slot_index: loc.slot, beat_time: bt, warp_marker_count: countAfter };
    }

    if (action === "delete" || action === "remove") {
        if (params.beat_time == null) return { ok: false, error: "beat_time is required to delete warp marker" };
        var btDel = Number(params.beat_time);
        try {
            clip.call("remove_warp_marker", btDel);
            return { ok: true, message: "Removed warp marker at beat " + btDel, track_index: loc.track, slot_index: loc.slot, beat_time: btDel };
        } catch (eDel) {
            return { ok: false, error: "Failed to remove warp marker: " + (eDel && eDel.message ? eDel.message : String(eDel)) };
        }
    }

    // clip.get("warp_markers") comes back in one of three shapes depending
    // on Live version/marker count: a single JSON string, a Max atom list
    // that IS that same JSON string split into word fragments (a long
    // get() result gets fragmented the same way OSC/textedit text does --
    // see unwrap()'s own comment), or the older flat [id, N, id, N, ...]
    // id-reference pairs. Taking unwrap()'s first-atom-only shortcut on the
    // fragmented-string case used to silently truncate the JSON before
    // JSON.parse ever saw it; join every atom first instead.
    var markers = [];
    var rawWm = null;
    var parseFailed = false;
    var raw_type = "";
    var raw_sample = "";
    try {
        rawWm = clip.get("warp_markers");
        raw_type = typeof rawWm;
        raw_sample = String(rawWm).slice(0, 200);
        var joinResult = palJoinAndParseWarpMarkers(rawWm);
        if (joinResult.handled) {
            if (joinResult.parseFailed) {
                parseFailed = true;
            } else {
                markers = joinResult.markers;
            }
        } else if (rawWm instanceof Array && rawWm.length) {
            // Older/atom form: flat [id, N, id, N, ...] id-reference pairs.
            for (var i = 0; i < rawWm.length; i += 2) {
                var wmId = rawWm[i + 1];
                var wmObj = liveApi("id " + wmId);
                if (wmObj) {
                    markers.push({
                        id: wmId,
                        beat_time: Number(unwrap(wmObj.get("beat_time")) || 0),
                        sample_time: Number(unwrap(wmObj.get("sample_time")) || 0)
                    });
                }
            }
        }
    } catch (eGet) {
        parseFailed = true;
    }

    if (parseFailed) {
        return {
            ok: false,
            error: "Could not parse warp_markers from Live",
            track_index: loc.track,
            slot_index: loc.slot,
            raw_type: raw_type,
            raw_sample: raw_sample
        };
    }

    return {
        ok: true,
        track_index: loc.track,
        slot_index: loc.slot,
        warp_markers_count: markers.length,
        warp_markers: markers
    };
}

function palSetClipAutomation(params) {
    params = params || {};
    var loc = palAutomationClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    var track = liveApi("live_set tracks " + loc.track);
    if (!track) return { ok: false, error: "Track not found: " + palLiveNum(loc.track) };

    var paramName = params.parameter_name || params.param_name || params.name;
    var targetParam = null;
    var paramOwner = "";

    if (paramName) {
        var pLower = String(paramName).toLowerCase();
        if (pLower === "volume") {
            targetParam = liveApi("live_set tracks " + loc.track + " mixer_device volume");
            paramOwner = "Track Mixer";
        } else if (pLower === "panning" || pLower === "pan") {
            targetParam = liveApi("live_set tracks " + loc.track + " mixer_device panning");
            paramOwner = "Track Mixer";
        }
    }

    if (!targetParam) {
        var devIdx = params.device_index != null ? Number(params.device_index) : 0;
        var dev = liveApi("live_set tracks " + loc.track + " devices " + devIdx);
        if (dev) {
            paramOwner = String(unwrap(dev.get("name")) || ("Device " + devIdx));
            if (params.parameter_index != null) {
                targetParam = liveApi("live_set tracks " + loc.track + " devices " + devIdx + " parameters " + Number(params.parameter_index));
            } else if (paramName) {
                var pCount = 0;
                try { pCount = dev.getcount("parameters"); } catch (ePc) {}
                for (var pi = 0; pi < pCount; pi++) {
                    var pCandidate = liveApi("live_set tracks " + loc.track + " devices " + devIdx + " parameters " + pi);
                    if (pCandidate) {
                        var cn = String(unwrap(pCandidate.get("name")) || "");
                        if (cn.toLowerCase() === String(paramName).toLowerCase()) {
                            targetParam = pCandidate;
                            break;
                        }
                    }
                }
            }
        }
    }

    if (!targetParam) {
        return { ok: false, error: "Could not find parameter '" + paramName + "' on track " + palLiveNum(loc.track) };
    }

    var envelopeData = params.envelope_data || params.points || [];
    if (typeof envelopeData === "string") {
        try { envelopeData = JSON.parse(envelopeData); } catch (eParse) {}
    }

    var clipLen = Number(unwrap(clip.get("length")) || 4.0);
    var paramId = extractId(targetParam.id);
    var paramMin = Number(unwrap(targetParam.get("min")));
    var paramMax = Number(unwrap(targetParam.get("max")));
    var hasRange = !isNaN(paramMin) && !isNaN(paramMax) && paramMax > paramMin;
    var inserted = 0;
    var envelope = null;
    var attempts = [];

    // ret comes back in one of several shapes depending on Live/M4L version:
    // ["id", N], the doubled ["id", "id", N], the bare string "id N", or a
    // bare number/numeric string N. Parsing down to just the trailing id
    // token (palParseEnvelopeIdToken) and resolving it through liveApiId()
    // (which correctly treats id 0 as a real, valid id) replaces the old
    // extractId()+liveApi("id "+x) path, which took extractId's `|| ""`
    // fallback on a literal id of 0 as "no id" and could double up an "id"
    // prefix into the literal path string "id id N" when ret was already
    // the plain string "id N".
    function resolveEnvelope(ret) {
        var idToken = palParseEnvelopeIdToken(ret);
        if (idToken === null) return null;
        var envObj = liveApiId(Number(idToken));
        return (envObj && envObj.info !== "No object") ? envObj : null;
    }

    try {
        var ret = paramId
            ? clip.call("create_automation_envelope", "id", paramId)
            : clip.call("create_automation_envelope", targetParam);
        attempts.push({ call: "create_automation_envelope", raw: String(ret), raw_type: typeof ret });
        envelope = resolveEnvelope(ret);
    } catch (eEnv) {
        attempts.push({ call: "create_automation_envelope", exception: String(eEnv && eEnv.message ? eEnv.message : eEnv) });
    }

    if (!envelope) {
        try {
            var ret2 = paramId
                ? clip.call("automation_envelope", "id", paramId)
                : clip.call("automation_envelope", targetParam);
            attempts.push({ call: "automation_envelope", raw: String(ret2), raw_type: typeof ret2 });
            envelope = resolveEnvelope(ret2);
        } catch (eEnv2) {
            attempts.push({ call: "automation_envelope", exception: String(eEnv2 && eEnv2.message ? eEnv2.message : eEnv2) });
        }
    }

    if (!envelope) {
        // Chat models have consistently failed to relay this attempts array
        // verbatim across three rounds of live testing (paraphrasing it down
        // to a bare count, or omitting it) -- post it to Max Console too so
        // the user can read it directly instead of depending on the model.
        post("live-actions-pal: automation envelope FAILED for '" + paramName + "' -- attempts: " + JSON.stringify(attempts) + "\n");
        return {
            ok: false,
            error: "Could not create or find an automation envelope for '" + paramName + "' on this Live/M4L version",
            parameter: paramName,
            owner: paramOwner,
            attempts: attempts
        };
    }

    try { envelope.call("clear_range", 0.0, clipLen); } catch (eClr) {}
    envelopeData.sort(function(a, b) { return Number(a.time || 0) - Number(b.time || 0); });
    var writtenPoints = [];
    for (var i = 0; i < envelopeData.length; i++) {
        var pt = envelopeData[i];
        var t = Number(pt.time != null ? pt.time : 0);
        var val = Number(pt.value != null ? pt.value : 0);
        if (hasRange) val = Math.max(paramMin, Math.min(paramMax, val));
        var nextT = (i + 1 < envelopeData.length) ? Number(envelopeData[i + 1].time) : clipLen;
        var dur = Math.max(0.03125, nextT - t);
        try {
            envelope.call("insert_step", t, dur, val);
            inserted++;
            writtenPoints.push({ time: t, value: val });
        } catch (eStep) {
            attempts.push({ call: "insert_step", time: t, exception: String(eStep && eStep.message ? eStep.message : eStep) });
        }
    }

    if (inserted === 0) {
        post("live-actions-pal: automation envelope created but no points inserted for '" + paramName + "' -- attempts: " + JSON.stringify(attempts) + "\n");
        return {
            ok: false,
            error: "Envelope created but no points could be inserted for '" + paramName + "'",
            parameter: paramName,
            owner: paramOwner,
            attempts: attempts
        };
    }

    // Verification (S1.3.3): insert_step succeeding is a Max call that
    // returned without throwing, not proof the value actually landed --
    // read each written point back via value_at_time and count how many
    // match within a tolerance that allows for range clamping and float
    // rounding, same spirit as palSetChecked's read-after-write elsewhere.
    var verified = 0;
    var tol = hasRange ? Math.max(1e-6, (paramMax - paramMin) * 0.01) : 1e-3;
    for (var vi = 0; vi < writtenPoints.length; vi++) {
        try {
            var readBack = Number(unwrap(envelope.call("value_at_time", writtenPoints[vi].time)));
            if (!isNaN(readBack) && Math.abs(readBack - writtenPoints[vi].value) <= tol) verified++;
        } catch (eVerify) {}
    }

    return {
        ok: true,
        message: "Wrote " + inserted + " automation points for " + (paramName || "parameter"),
        track_index: loc.track,
        slot_index: loc.slot,
        owner: paramOwner,
        points_added: inserted,
        points_verified: verified
    };
}

function palGetClipAutomation(params) {
    params = params || {};
    var loc = palAutomationClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };
    var hasEnv = !!unwrap(clip.get("has_envelopes"));
    return {
        ok: true,
        track_index: loc.track,
        slot_index: loc.slot,
        has_envelopes: hasEnv
    };
}

function palCommitGroove(params) {
    params = params || {};
    var loc = palClipFromParams(params);
    var clip = liveApi(loc.path);
    if (!clip) return { ok: false, error: "Clip not found at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot) };

    var grid = params.quantize_to != null ? Number(params.quantize_to) : (params.grid != null ? Number(params.grid) : 5);
    var amount = params.amount != null ? Number(params.amount) : 1.0;

    try {
        clip.call("quantize", grid, amount);
        return {
            ok: true,
            message: "Committed groove quantization to clip at track " + palLiveNum(loc.track) + ", slot " + palLiveNum(loc.slot),
            track_index: loc.track,
            slot_index: loc.slot,
            committed: true
        };
    } catch (e) {
        return { ok: false, error: "Failed to commit groove: " + (e && e.message ? e.message : String(e)) };
    }
}


