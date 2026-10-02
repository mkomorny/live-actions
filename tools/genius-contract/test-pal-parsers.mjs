// Regression harness for the C1 note-parsing fix in live-actions-pal.js:
// palUpdateClip/palCreateClip's "notes" param, and the bridge's write_notes
// action, must accept a real JS Array, a JSON-encoded array as *text*
// (what the five algorithmic generators used to send, stringified, before
// the v1.0.26 fix), and Pal-style shorthand text -- and all three must
// parse to the identical note list.
//
// Unlike bridge/live-actions-bridge.js (see tools/detect-key/test-detect-
// key.mjs's header), bridge/live-actions-pal.js has NO top-level Max
// globals (autowatch/inlets/outlets) or Max API calls at load time -- it
// is include()-d into bridge.js's scope and is just function declarations.
// So this loads the REAL shipped file via `new Function(source)` instead
// of a hand-synced copy: no drift risk between this test and what ships.
//
// Run: node tools/genius-contract/test-pal-parsers.mjs

"use strict";

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PAL_JS_PATH = path.join(__dirname, "..", "..", "bridge", "live-actions-pal.js");
const palSrc = readFileSync(PAL_JS_PATH, "utf8");

// unwrap() itself lives in bridge/live-actions-bridge.js, not pal.js -- pal.js
// normally gets it for free via include() into bridge.js's scope. Stubbed
// here verbatim (bridge.js:21) so palValueForDisplayString (which calls it)
// can be exercised without loading the whole Max-dependent bridge file.
const UNWRAP_STUB = `
function unwrap(v) {
    if (v === null || v === undefined) return v;
    if (typeof v === "object" && v.length !== undefined && typeof v !== "string") {
        return v.length ? v[0] : v;
    }
    return v;
}
`;

const loadPal = new Function(
    UNWRAP_STUB + palSrc +
    "\nreturn { palParseNotes, palNoteToPitch, palParseDuration, palBarBeatToBeats, " +
    "palLiveNum, palParseEnvelopeIdToken, palJoinAndParseWarpMarkers, palLeadingNumber, palValueForDisplayString };"
);
const {
    palParseNotes, palNoteToPitch, palParseDuration, palBarBeatToBeats,
    palLiveNum, palParseEnvelopeIdToken, palJoinAndParseWarpMarkers, palLeadingNumber, palValueForDisplayString,
} = loadPal();

let passed = 0;
let failed = 0;

function eq(actual, expected, label) {
    const a = JSON.stringify(actual);
    const e = JSON.stringify(expected);
    if (a === e) {
        passed++;
    } else {
        failed++;
        console.log("FAIL: " + label);
        console.log("  expected: " + e);
        console.log("  actual:   " + a);
    }
}

function ok(cond, label) {
    if (cond) {
        passed++;
    } else {
        failed++;
        console.log("FAIL: " + label);
    }
}

// ---------------------------------------------------------------------
// palNoteToPitch / palParseDuration / palBarBeatToBeats sanity
// ---------------------------------------------------------------------
eq(palNoteToPitch("C3"), 60, "palNoteToPitch('C3') === 60");
eq(palNoteToPitch("C#3"), 61, "palNoteToPitch('C#3') === 61");
eq(palNoteToPitch(36), 36, "palNoteToPitch(36) passes numbers through");
eq(palParseDuration("n/16", 4), 0.25, "palParseDuration('n/16') is meter-independent");
eq(palParseDuration("1bar", 3), 3, "palParseDuration('1bar') scales with beatsPerBar");
eq(palBarBeatToBeats("1|1", 4), 0, "palBarBeatToBeats('1|1') is beat 0");
eq(palBarBeatToBeats("2|1", 4), 4, "palBarBeatToBeats('2|1') is bar 2 in 4/4");

// ---------------------------------------------------------------------
// C1: Array / JSON-text / Pal-text must all parse identically.
//
// This is exactly the shape of the bug: the five generators
// (live_generate_euclidean, live_generate_chords, live_generate_
// walking_bass, live_transform_clip, live_write_drum_grid) used to send
// json.dumps(notes) -- a STRING -- into update_clip's "notes" param.
// palParseNotes only treated Arrays as note objects, so the JSON string
// fell through to the Pal text tokenizer and produced zero valid notes,
// silently wiping the clip via replace:true. The fix (C1) makes
// palParseNotes JSON.parse a string that looks like a JSON array before
// falling through to the tokenizer.
// ---------------------------------------------------------------------
const rawNotes = [
    { pitch: 60, start_time: 0, duration: 1, velocity: 100 },
    { pitch: 64, start_time: 1, duration: 0.5, velocity: 90, mute: true },
];
const expected = [
    { pitch: 60, startTime: 0, duration: 1, velocity: 100, mute: false },
    { pitch: 64, startTime: 1, duration: 0.5, velocity: 90, mute: true },
];

eq(palParseNotes(rawNotes, 4), expected, "real Array parses to note objects");
eq(palParseNotes(JSON.stringify(rawNotes), 4), expected, "JSON-encoded TEXT of the same array parses identically (C1)");

// startTime alias (some callers use camelCase, some snake_case)
const camelNotes = [{ pitch: 60, startTime: 2, duration: 1, velocity: 100 }];
eq(palParseNotes(camelNotes, 4)[0].startTime, 2, "startTime (camelCase) is honored directly");
eq(palParseNotes(JSON.stringify(camelNotes), 4)[0].startTime, 2, "startTime survives the JSON-text round trip too");

// Pal-style shorthand text -- a different note but same parser entry point,
// confirming the JSON-array short-circuit doesn't break the plain-text path.
const palText = palParseNotes("v100 n/4 C3 1|1", 4);
ok(palText.length === 1, "Pal text produces exactly one note");
eq(palText[0], { pitch: 60, startTime: 0, duration: 1, velocity: 100, mute: false }, "Pal text 'v100 n/4 C3 1|1' parses to C3 at beat 0");

// Malformed JSON-looking text must not throw -- it should fall through to
// the tokenizer (which will likely yield no notes for garbage, but must
// not crash palUpdateClip/write_notes).
ok(Array.isArray(palParseNotes("[not valid json", 4)), "malformed '[...' text falls through to the tokenizer instead of throwing");

// Empty / falsy input
eq(palParseNotes(null, 4), [], "null input returns []");
eq(palParseNotes("", 4), [], "empty string returns []");
eq(palParseNotes([], 4), [], "empty array returns []");

// ---------------------------------------------------------------------
// palLiveNum -- 0-based internal index -> 1-based Live-shown number (S1.1)
// ---------------------------------------------------------------------
eq(palLiveNum(0), 1, "palLiveNum(0) === 1 (Live's track 1)");
eq(palLiveNum(2), 3, "palLiveNum(2) === 3");
eq(palLiveNum(-1), -1, "palLiveNum(-1) passes through unchanged (sentinel 'none')");
eq(palLiveNum("Bass"), "Bass", "palLiveNum passes a non-number straight through");
eq(palLiveNum(null), null, "palLiveNum(null) passes through unchanged");

// ---------------------------------------------------------------------
// palParseEnvelopeIdToken -- S1.3.3: id 0 and the "id id N" double prefix
// ---------------------------------------------------------------------
eq(palParseEnvelopeIdToken(["id", 42]), 42, "['id', 42] -> 42");
eq(palParseEnvelopeIdToken(["id", "id", 42]), 42, "doubled ['id','id',42] -> 42 (last atom wins)");
eq(palParseEnvelopeIdToken("id 42"), "42", "string 'id 42' -> trailing token '42'");
eq(palParseEnvelopeIdToken(42), 42, "bare number 42 -> 42");
eq(palParseEnvelopeIdToken("42"), "42", "bare numeric string '42' -> '42'");
eq(palParseEnvelopeIdToken(["id", 0]), 0, "['id', 0] -> 0 (a literal id of 0 is valid, not 'missing')");
eq(palParseEnvelopeIdToken("id 0"), "0", "string 'id 0' -> '0'");
eq(palParseEnvelopeIdToken(null), null, "null -> null");
eq(palParseEnvelopeIdToken(undefined), null, "undefined -> null");
eq(palParseEnvelopeIdToken(""), null, "empty string -> null");
eq(palParseEnvelopeIdToken("id"), null, "'id' with no trailing number -> null (NaN token)");
eq(palParseEnvelopeIdToken([]), null, "empty array -> null");

// ---------------------------------------------------------------------
// palJoinAndParseWarpMarkers -- fragmented-string atom unwrapping (S1.3.2)
// ---------------------------------------------------------------------
const wmJson = JSON.stringify([{ beat_time: 0, sample_time: 0 }, { beat_time: 4, sample_time: 88200 }]);
const wmExpected = [{ beat_time: 0, sample_time: 0 }, { beat_time: 4, sample_time: 88200 }];

eq(palJoinAndParseWarpMarkers(wmJson), { handled: true, parseFailed: false, markers: wmExpected },
    "a single JSON string parses directly");

// The bug this exists for: a long get() result split into multiple word
// atoms -- unwrap()'s first-atom-only shortcut used to silently truncate
// this before JSON.parse ever ran. Splitting the same JSON text into
// several string fragments and re-joining must recover the identical result.
const fragments = [];
for (let i = 0; i < wmJson.length; i += 7) fragments.push(wmJson.slice(i, i + 7));
ok(fragments.length > 1, "the JSON text actually got split into more than one fragment for this test to mean anything");
eq(palJoinAndParseWarpMarkers(fragments), { handled: true, parseFailed: false, markers: wmExpected },
    "a fragmented atom-list JSON string rejoins to the identical parsed result");

eq(palJoinAndParseWarpMarkers("not valid json"), { handled: true, parseFailed: true },
    "unparseable text reports parseFailed instead of silently returning an empty list");
eq(palJoinAndParseWarpMarkers({ warp_markers: [{ beat_time: 1, sample_time: 2 }] }), { handled: false },
    "a plain object (not string/string-array) is not handled here -- caller falls back to the id-pairs path");
eq(palJoinAndParseWarpMarkers([1, 101, 2, 102]), { handled: false },
    "the older flat [id, N, id, N, ...] numeric-atom form is not handled here -- caller falls back to liveApi id lookups");

// ---------------------------------------------------------------------
// palValueForDisplayString -- band midpoint, not a naive bisection edge (S1.3.4/H8)
// ---------------------------------------------------------------------
// Simulates a Delay Feedback-style parameter: min=0, max=100, and str_for_value
// rounds to the nearest whole percent, so many raw values share one display
// band (e.g. everything in [39.5, 40.5) reads "40 %"). A naive bisection can
// land right at 39.5 or 40.49 -- right on the edge -- and a later read can
// round the OTHER way. The band-midpoint fix must land near 40.0, not an edge.
function makePercentParam() {
    return {
        call: function (method, v) {
            if (method !== "str_for_value") throw new Error("unexpected call: " + method);
            return Math.round(v) + " %";
        },
    };
}
const p = makePercentParam();
const resolved = palValueForDisplayString(p, "40 %", 0, 100);
ok(resolved !== null, "palValueForDisplayString resolves a value for '40 %'");
ok(Math.abs(resolved - 40) < 0.5, "resolved value is close to 40 (name: " + resolved + ")");
// The real regression: the resolved value must itself redisplay as "40 %",
// not round to a neighboring band on read-back (the literal H8 bug).
eq(Math.round(resolved), 40, "resolved value redisplays as exactly 40, not 38 or 41");

eq(palLeadingNumber("-6 dB"), -6, "palLeadingNumber('-6 dB') === -6");
eq(palLeadingNumber("40 %"), 40, "palLeadingNumber('40 %') === 40");
ok(Number.isNaN(palLeadingNumber("no number here")), "palLeadingNumber with no digits is NaN");

// ---------------------------------------------------------------------
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
