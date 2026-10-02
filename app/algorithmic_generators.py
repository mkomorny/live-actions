"""Live Actions — Algorithmic Music & Generative MIDI Engine.

Provides deterministic algorithmic MIDI generation and transformation:
1. Euclidean rhythm generation (Bjorklund algorithm).
2. Voiced chord progressions with smooth voice leading (Drop-2, rootless, shell).
3. Quarter-note jazz walking basslines with chromatic approach tones.
4. Classical motif transformations (inversion, retrograde, augmentation, diminution).
5. ASCII drum grid parser to MIDI note events.
"""

from __future__ import annotations

import math
import random
from typing import Any


# ── Note & Chord Definitions ──────────────────────────────────────────────────

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_SEMITONE = {
    "C": 0, "B#": 0,
    "C#": 1, "DB": 1,
    "D": 2,
    "D#": 3, "EB": 3,
    "E": 4, "FB": 4,
    "F": 5, "E#": 5,
    "F#": 6, "GB": 6,
    "G": 7,
    "G#": 8, "AB": 8,
    "A": 9,
    "A#": 10, "BB": 10,
    "B": 11, "CB": 11,
}


def _resolve_key_root(key_str: str) -> int:
    """Look up a key/root note letter, raising instead of silently defaulting to C."""
    root = key_str.upper().strip()
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(
            f"Unrecognized key '{key_str}'. Use a note name like C, F#, or Bb."
        )
    return NOTE_TO_SEMITONE[root]

# Intervals from root for common chord qualities
CHORD_QUALITIES: dict[str, list[int]] = {
    "maj": [0, 4, 7],
    "major": [0, 4, 7],
    "": [0, 4, 7],
    "min": [0, 3, 7],
    "m": [0, 3, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "7": [0, 4, 7, 10],            # Dominant 7
    "dom7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
    "min7": [0, 3, 7, 10],
    "m7b5": [0, 3, 6, 10],         # Half-diminished
    "dim7": [0, 3, 6, 9],
    "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "m9": [0, 3, 7, 10, 14],
    "add9": [0, 4, 7, 14],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
}

ROMAN_TO_DEGREE: dict[str, tuple[int, str]] = {
    "i": (0, "min"), "I": (0, "maj"),
    "i7": (0, "m7"), "I7": (0, "maj7"), "Imaj7": (0, "maj7"),
    "ii": (2, "min"), "II": (2, "maj"),
    "ii7": (2, "m7"), "II7": (2, "7"), "iim7": (2, "m7"), "ii7b5": (2, "m7b5"),
    "iii": (4, "min"), "III": (4, "maj"),
    "iii7": (4, "m7"), "III7": (4, "7"),
    "iv": (5, "min"), "IV": (5, "maj"),
    "iv7": (5, "m7"), "IV7": (5, "maj7"), "IVmaj7": (5, "maj7"),
    "v": (7, "min"), "V": (7, "maj"),
    "v7": (7, "m7"), "V7": (7, "7"),
    "vi": (9, "min"), "VI": (9, "maj"),
    "vi7": (9, "m7"), "VI7": (9, "7"),
    "vii": (11, "dim"), "VII": (11, "maj"),
    "vii7": (11, "m7b5"), "vii0": (11, "dim"), "vii07": (11, "dim7"),
    "bII": (1, "maj"), "bII7": (1, "7"),     # Neapolitan / tritone sub
    "bVI": (8, "maj"), "bVI7": (8, "maj7"),
    "bVII": (10, "maj"), "bVII7": (10, "7"),
}

ROMAN_DEGREES_MAJOR: dict[str, tuple[int, str]] = {
    "I": (0, "maj"), "II": (2, "min"), "III": (4, "min"), "IV": (5, "maj"),
    "V": (7, "maj"), "VI": (9, "min"), "VII": (11, "dim")
}

ROMAN_DEGREES_MINOR: dict[str, tuple[int, str]] = {
    "I": (0, "min"), "II": (2, "dim"), "III": (3, "maj"), "IV": (5, "min"),
    "V": (7, "min"), "VI": (8, "maj"), "VII": (10, "maj")
}

STANDARD_DRUM_MAP: dict[str, int] = {
    "k": 36, "kick": 36, "bd": 36,
    "s": 38, "snare": 38, "sd": 38,
    "rim": 37, "sidestick": 37,
    "cp": 39, "clap": 39,
    "ch": 42, "hat": 42, "hh": 42, "closedhat": 42,
    "oh": 46, "openhat": 46,
    "ph": 44, "pedalhat": 44,
    "lt": 43, "lowtom": 43,
    "mt": 47, "midtom": 47,
    "ht": 50, "hightom": 50,
    "cy": 49, "crash": 49,
    "rd": 51, "ride": 51,
    "cb": 56, "cowbell": 56,
    "perc": 54, "tamb": 54,
}


# ── 1. Euclidean Rhythm Generator ─────────────────────────────────────────────

def bjorklund(pulses: int, steps: int) -> list[int]:
    """Bjorklund's algorithm for Euclidean rhythm distribution."""
    if pulses <= 0:
        return [0] * steps
    if pulses >= steps:
        return [1] * steps

    return [1 if (i * pulses) % steps < pulses else 0 for i in range(steps)]


def generate_euclidean_rhythm(
    pulses: int,
    steps: int = 16,
    rotate: int = 0,
    pitch: int = 36,
    velocity: int = 100,
    step_duration: float = 0.25,
    bars: int = 1,
    humanize: float = 0.0,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Generate MIDI notes according to a Euclidean rhythm.

    Args:
        pulses: Number of active hits.
        steps: Total steps in one measure/cycle (default 16 for 16th notes).
        rotate: Shift pattern forward by steps.
        pitch: MIDI pitch for hits (e.g. 36 for kick).
        velocity: Base velocity (1-127).
        step_duration: Duration of one step in beats (0.25 = 16th note).
        bars: How many repetitions of the pattern to generate.
        humanize: Degree of velocity and timing jitter (0.0 to 1.0).
        seed: Random seed for repeatability.
    """
    if seed is not None:
        random.seed(seed)

    pattern = bjorklund(pulses, steps)
    if rotate:
        rot = rotate % steps
        pattern = pattern[-rot:] + pattern[:-rot]

    notes: list[dict[str, Any]] = []
    for b in range(bars):
        bar_offset = b * (steps * step_duration)
        for i, hit in enumerate(pattern):
            if hit:
                t = bar_offset + (i * step_duration)
                v = velocity
                dur = step_duration * 0.85

                if humanize > 0:
                    time_jitter = (random.random() - 0.5) * 0.04 * humanize
                    t = max(0.0, t + time_jitter)
                    vel_jitter = int((random.random() - 0.5) * 20 * humanize)
                    v = max(1, min(127, v + vel_jitter))

                notes.append({
                    "pitch": int(pitch),
                    "start_time": round(float(t), 4),
                    "duration": round(float(dur), 4),
                    "velocity": int(v),
                    "mute": False,
                })
    return notes


# ── 2. Voiced Chord Progression Generator ─────────────────────────────────────

def _parse_chord_token(token: str, key_root: int = 0) -> tuple[int, list[int], str]:
    """Parse Roman numeral or chord symbol into root semitone and pitch intervals."""
    token = token.strip()
    if not token:
        return (0, [0, 4, 7], "C")

    # Check Roman numeral first
    for r_str, (deg, quality) in ROMAN_TO_DEGREE.items():
        if token == r_str:
            root = (key_root + deg) % 12
            intervals = CHORD_QUALITIES.get(quality, [0, 4, 7])
            name = NOTE_NAMES[root] + quality
            return (root, intervals, name)

    # Chord symbol parsing (e.g., Dm7, F#maj7, Bb, G7)
    match_root = ""
    upper = token.upper()
    for n in ["C#", "D#", "F#", "G#", "A#", "DB", "EB", "GB", "AB", "BB", "C", "D", "E", "F", "G", "A", "B"]:
        if upper.startswith(n):
            match_root = n
            break

    if not match_root:
        return (key_root, [0, 4, 7], token)

    root = NOTE_TO_SEMITONE[match_root]
    quality_str = token[len(match_root):].strip().lower()
    intervals = CHORD_QUALITIES.get(quality_str, [0, 4, 7])
    return (root, intervals, token)


def _voice_chord(
    root: int,
    intervals: list[int],
    style: str = "drop2",
    center_pitch: int = 60,
    prev_pitches: list[int] | None = None,
) -> list[int]:
    """Construct voiced pitch list adhering to style and smooth voice leading."""
    # Base octave for root near center_pitch
    octave = 12 * (center_pitch // 12)
    base_pitches = [octave + root + iv for iv in intervals]

    # Style transformations
    if style == "shell":
        # Root in bass + 3rd and 7th in middle register
        root_pitch = (octave - 12) + root
        if len(intervals) >= 4:
            # 3rd is intervals[1], 7th is intervals[3] (or intervals[-1])
            shells = [octave + root + intervals[1], octave + root + intervals[-1]]
            return sorted([root_pitch] + shells)
        elif len(intervals) >= 3:
            return sorted([root_pitch, octave + root + intervals[1], octave + root + intervals[2]])
        return sorted([root_pitch] + base_pitches)

    elif style == "drop2" and len(base_pitches) >= 4:
        # Sort ascending, take second note from top and drop down one octave
        sorted_p = sorted(base_pitches)
        second_from_top = sorted_p[-2] - 12
        other_notes = [sorted_p[0], sorted_p[1], sorted_p[3]]
        return sorted([second_from_top] + other_notes)

    elif style == "rootless" and len(intervals) >= 4:
        # Drop root, add 9th (root + 14)
        third_up = [octave + root + iv for iv in intervals[1:]]
        ninth = octave + root + 14
        return sorted(third_up + [ninth])

    elif style == "open":
        # Spread pitches across octaves
        sorted_p = sorted(base_pitches)
        res = []
        for idx, p in enumerate(sorted_p):
            res.append(p + (12 if idx % 2 == 1 else 0))
        return sorted(res)

    # Voice leading optimization if previous pitches exist
    if prev_pitches and len(prev_pitches) == len(base_pitches):
        best_pitches = base_pitches
        min_dist = float("inf")
        # Test octave transpositions (+/- 12) to minimize total movement
        for shift in [-12, 0, 12]:
            shifted = [p + shift for p in base_pitches]
            dist = sum(abs(s - p) for s, p in zip(sorted(shifted), sorted(prev_pitches)))
            if dist < min_dist:
                min_dist = dist
                best_pitches = shifted
        return sorted(best_pitches)

    return sorted(base_pitches)


def generate_voiced_progression(
    progression: str | list[str],
    key: str = "C",
    beats_per_chord: float = 4.0,
    style: str = "drop2",
    center_pitch: int = 60,
    velocity: int = 85,
    strum: float = 0.0,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build a voiced chord progression into a list of MIDI note dicts."""
    key_root = _resolve_key_root(key)

    if isinstance(progression, str):
        # Split by dashes, commas, or spaces
        tokens = [t.strip() for t in progression.replace("-", " ").replace(",", " ").split() if t.strip()]
    else:
        tokens = [str(t).strip() for t in progression if str(t).strip()]

    if not tokens:
        tokens = ["I", "vi", "IV", "V"]

    notes: list[dict[str, Any]] = []
    chord_names: list[str] = []
    prev_pitches: list[int] | None = None

    for i, tok in enumerate(tokens):
        root, intervals, cname = _parse_chord_token(tok, key_root)
        chord_names.append(cname)
        chord_pitches = _voice_chord(root, intervals, style=style, center_pitch=center_pitch, prev_pitches=prev_pitches)
        prev_pitches = chord_pitches

        start_time = i * beats_per_chord
        dur = beats_per_chord * 0.95

        for n_idx, p in enumerate(chord_pitches):
            offset = n_idx * strum
            notes.append({
                "pitch": int(p),
                "start_time": round(float(start_time + offset), 4),
                "duration": round(float(max(0.1, dur - offset)), 4),
                "velocity": int(max(1, min(127, velocity + (n_idx * 2)))),
                "mute": False,
            })

    return notes, chord_names


# ── 3. Walking Bassline Generator ─────────────────────────────────────────────

def generate_walking_bass(
    progression: str | list[str],
    key: str = "C",
    beats_per_chord: float = 4.0,
    octave: int = 1,
    ghost: bool = True,
    velocity: int = 95,
) -> list[dict[str, Any]]:
    """Generate a jazz/blues quarter-note walking bassline.

    Structure per 4-beat bar:
      Beat 1: Chord Root
      Beat 2: Chord 3rd or 5th
      Beat 3: Diatonic scale approach or 7th
      Beat 4: Chromatic leading tone approaching next chord root
    """
    key_root = _resolve_key_root(key)
    base_octave = 12 * (octave + 1)  # octave 1 -> C1 is 24, octave 2 -> C2 is 36

    if isinstance(progression, str):
        tokens = [t.strip() for t in progression.replace("-", " ").replace(",", " ").split() if t.strip()]
    else:
        tokens = [str(t).strip() for t in progression if str(t).strip()]

    if not tokens:
        tokens = ["ii", "V", "I", "I"]

    chord_data = [_parse_chord_token(t, key_root) for t in tokens]
    notes: list[dict[str, Any]] = []

    for i, (root, intervals, _cname) in enumerate(chord_data):
        bar_start = i * beats_per_chord
        next_i = (i + 1) % len(chord_data)
        next_root = chord_data[next_i][0]

        root_pitch = base_octave + root
        third_pitch = base_octave + root + intervals[min(1, len(intervals) - 1)]
        fifth_pitch = base_octave + root + intervals[min(2, len(intervals) - 1)]

        next_target = base_octave + next_root
        # Chromatic approach: 1 semitone above or below next target
        chromatic_approach = next_target + (1 if random.random() > 0.5 else -1)

        # 4 quarter-note beats
        pattern = [
            root_pitch,
            third_pitch if (i % 2 == 0) else fifth_pitch,
            fifth_pitch if (i % 2 == 0) else third_pitch,
            chromatic_approach,
        ]

        for step, p in enumerate(pattern):
            t = bar_start + step
            notes.append({
                "pitch": int(max(12, min(60, p))),
                "start_time": round(float(t), 4),
                "duration": 0.85,
                "velocity": int(velocity if step == 0 else max(1, velocity - 10)),
                "mute": False,
            })

            # Optional ghost note on swing 8th
            if ghost and step in (1, 3) and random.random() > 0.6:
                notes.append({
                    "pitch": int(max(12, min(60, p))),
                    "start_time": round(float(t + 0.66), 4),
                    "duration": 0.2,
                    "velocity": max(30, velocity - 45),
                    "mute": False,
                })

    return notes


# ── 4. Classical Motif Transformations ────────────────────────────────────────

def transform_clip_notes(
    notes: list[dict[str, Any]],
    op: str = "invert",
    amount: float = 0.0,
    axis: int | None = None,
) -> list[dict[str, Any]]:
    """Apply classical transformations to a MIDI note list.

    Operations:
      - 'invert': Pitch inversion around an axis (default median pitch).
      - 'retrograde': Reverse note timing from end to start.
      - 'retrograde_invert': Both retrograde and inversion.
      - 'augment': Stretch timing and duration by a factor (default 2.0).
      - 'diminish': Compress timing and duration by a factor (default 0.5).
      - 'transpose': Shift pitch by `amount` semitones.
      - 'humanize': Apply random velocity and timing jitter.
    """
    if not notes:
        return []

    op = op.lower().strip()
    result: list[dict[str, Any]] = []

    pitches = [n["pitch"] for n in notes]
    center_axis = axis if axis is not None else (int(sum(pitches) / len(pitches)) if pitches else 60)

    max_end = max(n["start_time"] + n["duration"] for n in notes)

    for n in notes:
        new_p = n["pitch"]
        new_t = n["start_time"]
        new_d = n["duration"]
        new_v = n["velocity"]

        if op in ("invert", "inversion"):
            new_p = 2 * center_axis - new_p

        elif op in ("retrograde", "reverse"):
            new_t = max_end - (n["start_time"] + n["duration"])

        elif op in ("retrograde_invert", "retrograde_inversion"):
            new_p = 2 * center_axis - new_p
            new_t = max_end - (n["start_time"] + n["duration"])

        elif op in ("augment", "augmentation", "stretch"):
            factor = float(amount) if amount > 0 else 2.0
            new_t = n["start_time"] * factor
            new_d = n["duration"] * factor

        elif op in ("diminish", "diminution", "compress"):
            factor = float(amount) if amount > 0 else 0.5
            new_t = n["start_time"] * factor
            new_d = n["duration"] * factor

        elif op in ("transpose", "transposition"):
            shift = int(amount)
            new_p += shift

        elif op == "humanize":
            jit_amt = float(amount) if amount > 0 else 0.5
            new_t += (random.random() - 0.5) * 0.05 * jit_amt
            new_v = int(new_v + (random.random() - 0.5) * 24 * jit_amt)

        result.append({
            "pitch": int(max(0, min(127, new_p))),
            "start_time": round(float(max(0.0, new_t)), 4),
            "duration": round(float(max(0.05, new_d)), 4),
            "velocity": int(max(1, min(127, new_v))),
            "mute": bool(n.get("mute", False)),
        })

    # Sort chronological
    result.sort(key=lambda x: (x["start_time"], x["pitch"]))
    return result


# ── 5. ASCII Drum Grid Parser ─────────────────────────────────────────────────

def parse_drum_grid(
    grid_text: str,
    step_beats: float = 0.25,
    swing: float = 0.0,
) -> list[dict[str, Any]]:
    """Parse multi-line ASCII drum grid into MIDI note events.

    Example format:
      K:  x...x...x...x...
      S:  ....x.......x...
      CH: x.x.x.x.x.x.x.x.
    """
    notes: list[dict[str, Any]] = []

    lines = [ln.strip() for ln in grid_text.splitlines() if ln.strip()]
    for line in lines:
        if ":" not in line:
            continue
        header, steps_str = line.split(":", 1)
        header = header.strip().lower()
        steps_clean = steps_str.replace(" ", "").replace("|", "").strip()

        pitch = STANDARD_DRUM_MAP.get(header)
        if pitch is None:
            # Fallback if header is numeric pitch
            try:
                pitch = int(header)
            except ValueError:
                continue

        for i, ch in enumerate(steps_clean):
            if ch in (".", "-"):
                continue

            # Velocity mapping
            if ch in ("x", "X"):
                vel = 100
            elif ch in ("^", "!"):
                vel = 125
            elif ch in ("o", "O"):
                vel = 65
            elif ch in ("g", "G"):
                vel = 45
            else:
                vel = 90

            t = i * step_beats
            # Apply swing to odd 16ths
            if swing > 0 and (i % 2 == 1):
                t += swing * (step_beats * 0.33)

            dur = step_beats * 0.8

            notes.append({
                "pitch": int(pitch),
                "start_time": round(float(t), 4),
                "duration": round(float(dur), 4),
                "velocity": int(vel),
                "mute": False,
            })

    notes.sort(key=lambda x: (x["start_time"], x["pitch"]))
    return notes


# ── 6. High-Level Drum Pattern Generator ─────────────────────────────────────

def create_drum_pattern_notes(
    pattern: dict[str | int, str],
    default_velocity: int = 100,
    beats_per_bar: float = 4.0,
    length_beats: float | None = None,
) -> tuple[list[dict[str, Any]], float]:
    """Parse step strings into MIDI notes supporting velocity scaling ('2'-'9') and polyrhythms.

    Args:
        pattern: Dict mapping voice names ('kick', 'snare', etc.), note names ('C1'),
                 or MIDI pitch ints to step strings ('x...x...x...x...').
        default_velocity: Velocity for hits marked 'x' or '1' (default 100).
        beats_per_bar: Duration of one measure in beats (default 4.0).
        length_beats: Total clip length. If omitted, calculated from the longest voice row.

    Returns:
        tuple of (notes list, total clip length in beats)
    """
    notes: list[dict[str, Any]] = []
    if not pattern:
        return ([], length_beats or beats_per_bar)

    voice_map = dict(STANDARD_DRUM_MAP)
    voice_map.update({
        "snare_side": 37,
        "sidestick": 37,
        "closed_hat": 42,
        "pedal_hat": 44,
        "open_hat": 46,
        "tom_low": 41,
        "tom_mid": 45,
        "tom_high": 48,
        "ride_bell": 53,
        "tambourine": 54,
        "splash": 55,
        "shaker": 70,
    })

    calc_length = 0.0
    for voice, row in pattern.items():
        row_str = str(row).replace("|", "").replace(" ", "")
        n_steps = len(row_str)
        if n_steps > 0:
            row_beats = length_beats if length_beats is not None else max(beats_per_bar, n_steps * 0.25)
            if row_beats > calc_length:
                calc_length = row_beats

    total_beats = length_beats if length_beats is not None else (calc_length or beats_per_bar)

    for voice, row in pattern.items():
        pitch: int | None = None
        v_key = str(voice).strip().lower()
        if v_key in voice_map:
            pitch = voice_map[v_key]
        else:
            import re
            m = re.match(r"^([A-Ga-g][#b]?)(-?\d+)$", str(voice).strip())
            if m:
                p_name = m.group(1).upper()
                octave = int(m.group(2))
                semi = NOTE_TO_SEMITONE.get(p_name)
                if semi is not None:
                    pitch = (octave + 1) * 12 + semi
            if pitch is None:
                try:
                    pitch = int(voice)
                except ValueError:
                    continue

        if pitch is None or pitch < 0 or pitch > 127:
            continue

        row_str = str(row).replace("|", "").replace(" ", "")
        n_steps = len(row_str)
        if n_steps == 0:
            continue

        step_beats = total_beats / n_steps

        for i, ch in enumerate(row_str):
            if ch in (".", "-", "_", "0", " "):
                continue

            vel = default_velocity
            if ch in ("x", "X", "1"):
                vel = default_velocity
            elif ch in "23456789":
                vel = int(28 + (int(ch) - 2) * (127 - 28) / 7)

            start_t = i * step_beats
            dur = max(0.05, step_beats * 0.8)

            notes.append({
                "pitch": int(pitch),
                "start_time": round(float(start_t), 4),
                "duration": round(float(dur), 4),
                "velocity": int(max(1, min(127, vel))),
                "mute": False,
            })

    notes.sort(key=lambda x: (x["start_time"], x["pitch"]))
    return (notes, round(float(total_beats), 4))


# ── 7. High-Level Roman Numeral & Chord Progression Engine ───────────────────

def _parse_chord_token_advanced(
    token: str,
    key_root: int = 0,
    is_minor_key: bool = False,
    default_voicing: str = "triad",
) -> tuple[int, list[int], str]:
    """Parse Roman numeral token or absolute chord symbol."""
    import re
    token = token.strip()
    if not token:
        return (key_root, [0, 4, 7], "C")

    # Match Roman numeral pattern: optional accidental (b, #), roman digits (I, V, etc.), suffix
    m = re.match(r"^([b#]?)([ivIV]+)([°0\+ø]?)(maj7|maj9|m7|min7|dim7|7|9|sus2|sus4|6|m6)?$", token)
    if m:
        acc, roman, dim_sym, suffix = m.groups()
        roman_upper = roman.upper()
        is_lower = roman.islower()

        scale_map = ROMAN_DEGREES_MINOR if is_minor_key else ROMAN_DEGREES_MAJOR
        deg_info = scale_map.get(roman_upper, (0, "min" if is_lower else "maj"))
        base_deg = deg_info[0]

        offset = 0
        if acc == "b":
            offset = -1
        elif acc == "#":
            offset = 1

        root_semi = (key_root + base_deg + offset) % 12

        if dim_sym in ("°", "0", "ø"):
            quality = "dim7" if suffix == "7" else "dim"
        elif suffix == "7":
            quality = "m7" if is_lower else "7"
        elif suffix:
            quality = suffix
        elif is_lower:
            quality = "min"
        else:
            quality = "maj"

        if default_voicing == "seventh" and "7" not in quality and quality in ("maj", "min", "dim"):
            if quality == "maj":
                quality = "maj7" if roman_upper in ("I", "IV") else "7"
            elif quality == "min":
                quality = "m7"
            elif quality == "dim":
                quality = "m7b5"

        intervals = CHORD_QUALITIES.get(quality, [0, 4, 7])
        root_name = NOTE_NAMES[root_semi]
        return (root_semi, intervals, f"{root_name}{quality}")

    return _parse_chord_token(token, key_root)


def create_chord_progression_notes(
    chords: list[str] | str,
    key: str = "C",
    voicing: str = "triad",
    beats_per_chord: float | list[float] = 4.0,
    length_beats: float | None = None,
    base_octave: int = 3,
    velocity: int = 85,
) -> tuple[list[dict[str, Any]], float]:
    """Generate chord progression notes from Roman numeral tokens or chord names.

    Args:
        chords: List of tokens (e.g. ['I', 'vi', 'IV', 'V'] or ['ii', 'V7', 'I']) or space-separated string.
        key: Key root (e.g. 'C', 'Am', 'F#', 'Eb').
        voicing: 'triad', 'seventh', or 'power'.
        beats_per_chord: Float duration per chord or list of durations per chord.
        length_beats: Total clip length (optional).
        base_octave: Center octave register (default 3 = C3/MIDI 60).
        velocity: Base velocity (default 85).

    Returns:
        tuple of (notes list, total clip length in beats)
    """
    import re
    if isinstance(chords, str):
        chord_list = [c.strip() for c in re.split(r"[,\s\-]+", chords) if c.strip()]
    else:
        chord_list = [str(c).strip() for c in chords if str(c).strip()]

    if not chord_list:
        return ([], length_beats or 4.0)

    clean_key = key.strip()
    is_minor_key = clean_key.endswith("m") or clean_key.lower().endswith("min") or clean_key.lower().endswith("minor")
    root_str = re.sub(r"(?i)(minor|min|m)$", "", clean_key).strip().upper()
    key_root = _resolve_key_root(root_str)

    durations: list[float] = []
    if isinstance(beats_per_chord, list):
        for i in range(len(chord_list)):
            durations.append(float(beats_per_chord[i % len(beats_per_chord)]))
    else:
        durations = [float(beats_per_chord)] * len(chord_list)

    total_beats = length_beats if length_beats is not None else sum(durations)

    notes: list[dict[str, Any]] = []
    curr_time = 0.0
    center_midi = (base_octave + 1) * 12

    for i, token in enumerate(chord_list):
        chord_dur = durations[i]
        root_semi, intervals, chord_name = _parse_chord_token_advanced(token, key_root, is_minor_key, voicing)

        base_pitch = center_midi + root_semi
        while base_pitch < center_midi - 6:
            base_pitch += 12
        while base_pitch > center_midi + 6:
            base_pitch -= 12

        if voicing == "power":
            chord_pitches = [base_pitch, base_pitch + 7, base_pitch + 12]
        else:
            chord_pitches = [base_pitch + interval for interval in intervals]

        note_dur = max(0.1, chord_dur * 0.95)

        for p in chord_pitches:
            notes.append({
                "pitch": int(max(0, min(127, p))),
                "start_time": round(float(curr_time), 4),
                "duration": round(float(note_dur), 4),
                "velocity": int(max(1, min(127, velocity))),
                "mute": False,
            })

        curr_time += chord_dur

    notes.sort(key=lambda x: (x["start_time"], x["pitch"]))
    return (notes, round(float(total_beats), 4))


def generate_shaped_automation(
    shape: str = "sine",
    cycles: float = 1.0,
    min_value: float = 0.0,
    max_value: float = 1.0,
    points: int = 33,
    length: float = 4.0,
) -> list[dict[str, float]]:
    """Draw a repeating waveform envelope as a list of {"time": float, "value": float} points.

    Supports:
    - sine: smooth trigonometric wave starting at center
    - triangle: linear ramp up and down
    - saw: linear ramp from 0 to 1
    - square: high on first half of cycle, low on second half
    - random: deterministic hash-based sample-and-hold curve
    """
    low, high = min(min_value, max_value), max(min_value, max_value)
    val_range = high - low
    point_count = max(2, int(points))
    shape_lower = (shape or "sine").strip().lower()

    def unit_sine(phase: float) -> float:
        return 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)

    def sample_shape(phase: float) -> float:
        p = phase % 1.0
        if shape_lower == "triangle":
            return 1.0 - abs(2.0 * p - 1.0)
        elif shape_lower == "saw":
            return p
        elif shape_lower == "square":
            return 1.0 if p < 0.5 else 0.0
        elif shape_lower == "random":
            scrambled = int(p * 997.0) * 131 + 7
            return (scrambled % 100) / 99.0
        return unit_sine(p)

    envelope: list[dict[str, float]] = []
    total_len = float(length if length > 0 else 4.0)

    for i in range(point_count):
        t = total_len * i / (point_count - 1)
        phase = (float(cycles) * i / (point_count - 1)) % 1.0
        val = low + val_range * sample_shape(phase)
        envelope.append({
            "time": round(float(t), 4),
            "value": round(float(val), 4),
        })

    return envelope


