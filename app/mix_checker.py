"""Live Actions — Heuristic Session & Mix Health Checker.

Performs structural and mix-hygiene audits over a running Ableton Live set,
evaluating gain staging, low-end clashing, master chain protection, solo/mute
hygiene, and stereo balance.
"""

from __future__ import annotations

from typing import Any


def analyze_mix_heuristics(set_info: dict[str, Any]) -> dict[str, Any]:
    """Run structural mix health checks against a live set snapshot.

    Args:
        set_info: The dictionary returned by `palReadSet` or `live_read_set`
                  including tracks, mixer, and devices.
    """
    tracks = set_info.get("tracks") or []
    master = set_info.get("master") or {}

    critical: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    # 1. Master Bus Health & Limiter Check
    master_devices = master.get("devices") or []
    master_has_limiter = False
    for d in master_devices:
        dname = str(d.get("name") or "").lower()
        if any(w in dname for w in ("limiter", "maximizer", "brickwall", "ozone", "pro-l", "glue")):
            master_has_limiter = True
            break

    if not master_has_limiter:
        critical.append("Master track lacks a brickwall Limiter or safety compressor.")

    master_vol = (master.get("mixer") or {}).get("volume")
    if master_vol is not None and master_vol > 0.8505:
        critical.append(f"Master fader is boosted above unity gain 0 dB ({master_vol:.3f} > 0.850). Risk of clipping.")

    # 2. Track Gain Staging & Headroom
    hot_tracks: list[str] = []
    soloed_tracks: list[str] = []
    low_end_tracks: list[dict[str, Any]] = []

    for t in tracks:
        tname = str(t.get("name") or f"Track {t.get('index', '?')}")
        mixer = t.get("mixer") or {}
        vol = mixer.get("volume")
        muted = bool(t.get("mute", False))
        solo = bool(t.get("solo", False))
        pan = float(mixer.get("pan") or 0.0)

        if solo:
            soloed_tracks.append(tname)

        if not muted and vol is not None and vol > 0.90:
            hot_tracks.append(f"{tname} ({vol:.2f})")

        # Low-end identification
        low_keywords = ("kick", "bass", "sub", "808", "low", "boomy")
        is_low_end = any(kw in tname.lower() for kw in low_keywords)
        if is_low_end and not muted:
            # Check pan on low end
            if abs(pan) > 0.15:
                warnings.append(f"Low-end track '{tname}' is panned off-center ({pan:+.2f}). Bass should typically be centered.")
            low_end_tracks.append(t)

    if soloed_tracks:
        warnings.append(f"Tracks currently soloed: {', '.join(soloed_tracks)}. Other session tracks are silenced.")

    if hot_tracks:
        warnings.append(f"Tracks pushed hot near ceiling (>0.90): {', '.join(hot_tracks)}.")

    # 3. Low-End Frequency Contention (Sub-bass clash)
    if len(low_end_tracks) >= 3:
        track_names = [str(t.get("name")) for t in low_end_tracks]
        recommendations.append(
            f"Multiple active low-frequency tracks detected ({', '.join(track_names)}). "
            "Ensure only one sub source occupies 30-80 Hz, and high-pass or sidechain the others."
        )

    # 4. Empty Track / Organisation Check
    empty_unmuted: list[str] = []
    for t in tracks:
        tname = str(t.get("name") or "")
        has_any_clip = any(slot.get("has_clip") for slot in (t.get("clip_slots") or []))
        muted = bool(t.get("mute", False))
        if not has_any_clip and not muted and t.get("kind") in ("midi", "audio"):
            empty_unmuted.append(tname)

    if empty_unmuted:
        recommendations.append(f"Active tracks with 0 clips: {', '.join(empty_unmuted)}.")

    # 5. Overall Score / Headline
    if critical:
        headline = "CRITICAL: Mix has potential clipping or master protection issues."
        status = "danger"
    elif warnings:
        headline = "WARNING: Mix has gain-staging, solo, or panning imbalances."
        status = "warning"
    else:
        headline = "HEALTHY: Good gain staging, centered low end, and master bus protected."
        status = "ok"

    return {
        "ok": True,
        "status": status,
        "headline": headline,
        "critical_issues": critical,
        "warnings": warnings,
        "recommendations": recommendations,
        "checked_tracks_count": len(tracks),
    }
