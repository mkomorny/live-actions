"""Audio analysis and A/B comparison for Live Actions / Live Actions Genius.

Measures audio files objectively to provide acoustic feedback for closed-loop
mixing, sound design, and mastering. Calculates LUFS, True Peak (dBTP), RMS,
crest factor, 10-band spectral balance, spectral centroid (brightness),
rolloff, flatness, transient onset strength/rate, punch (band crest dB),
stereo width & correlation, and noise floor.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Optional


def _db(x: float | None) -> Optional[float]:
    if x is None or x <= 0:
        return None
    return round(20.0 * math.log10(x), 2)


_SPECTRUM_EDGES = [20, 40, 80, 160, 315, 630, 1250, 2500, 5000, 10000, 20000]
_LEGACY_BANDS = {
    "low_20_120": (20, 120),
    "lowmid_120_500": (120, 500),
    "mid_500_2k": (500, 2000),
    "high_2k_20k": (2000, 20000),
}
_HEAVY_CAP_SECONDS = 60.0


def _stft_mag(mono, sr: int, nperseg: int = 4096, hop: int = 1024):
    import numpy as np

    n = len(mono)
    win = np.hanning(nperseg)
    freqs = np.fft.rfftfreq(nperseg, 1.0 / sr)
    if n < nperseg:
        frame = np.zeros(nperseg)
        frame[:n] = mono
        return freqs, np.abs(np.fft.rfft(frame * win))[:, None]
    cols = []
    for s in range(0, n - nperseg + 1, hop):
        cols.append(np.abs(np.fft.rfft(mono[s : s + nperseg] * win)))
    return freqs, np.stack(cols, axis=1)


def _band_fraction(freqs, meanmag, lo: float, hi: float) -> float:
    import numpy as np

    total = float(np.sum(meanmag)) or 1.0
    mask = (freqs >= lo) & (freqs < hi)
    return float(np.sum(meanmag[mask])) / total


def _band_timeseries(sig, sr: int, lo: float, hi: float):
    import numpy as np

    n = len(sig)
    spec = np.fft.rfft(sig)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    spec = spec * ((freqs >= lo) & (freqs < hi))
    return np.fft.irfft(spec, n=n)


def _lufs_pyloudnorm(data, sr: int):
    import numpy as np
    import pyloudnorm as pyln

    meter = pyln.Meter(sr)
    try:
        integ = float(meter.integrated_loudness(data))
    except Exception:
        integ = None
    if integ is not None and not math.isfinite(integ):
        integ = None

    st_vals = []
    n = data.shape[0]
    wlen = int(3.0 * sr)
    hop = int(1.0 * sr)
    if n >= wlen:
        for s in range(0, n - wlen + 1, hop):
            try:
                v = float(meter.integrated_loudness(data[s : s + wlen]))
                if math.isfinite(v):
                    st_vals.append(v)
            except Exception:
                pass
    st_max = round(max(st_vals), 2) if st_vals else (round(integ, 2) if integ is not None else None)

    lra = None
    if len(st_vals) >= 3:
        arr = np.array([v for v in st_vals if v > -70.0])
        if arr.size >= 3:
            rel_gate = float(np.mean(arr)) - 20.0
            gated = arr[arr >= rel_gate]
            if gated.size >= 2:
                lra = round(float(np.percentile(gated, 95) - np.percentile(gated, 10)), 2)

    return (round(integ, 2) if integ is not None else None), st_max, lra, "pyloudnorm"


def _kweight_response(freqs, fs: int):
    import numpy as np

    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / fs)
    Vh = 10 ** (G / 20.0)
    Vb = Vh**0.4996667741545416
    a0 = 1 + K / Q + K * K
    b1 = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0]
    a1 = [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]

    f0b, Qb = 38.13547087602444, 0.5003270373238773
    Kb = math.tan(math.pi * f0b / fs)
    a0b = 1 + Kb / Qb + Kb * Kb
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, 2 * (Kb * Kb - 1) / a0b, (1 - Kb / Qb + Kb * Kb) / a0b]

    w = 2 * np.pi * np.asarray(freqs) / fs
    z1, z2 = np.exp(-1j * w), np.exp(-2j * w)
    H1 = (b1[0] + b1[1] * z1 + b1[2] * z2) / (a1[0] + a1[1] * z1 + a1[2] * z2)
    H2 = (b2[0] + b2[1] * z1 + b2[2] * z2) / (a2[0] + a2[1] * z1 + a2[2] * z2)
    return np.abs(H1 * H2)


def _lufs_numpy(data, sr: int):
    import numpy as np

    chans = data.shape[1]
    z = 0.0
    for c in range(chans):
        x = data[:, c]
        n = len(x)
        if n == 0:
            continue
        X = np.fft.rfft(x)
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        H = _kweight_response(freqs, sr)
        Y = np.abs(X) * H
        sq = Y**2
        if n % 2 == 0:
            energy = sq[0] + 2 * np.sum(sq[1:-1]) + sq[-1]
        else:
            energy = sq[0] + 2 * np.sum(sq[1:])
        z += float(energy / (n * n))
    if z <= 0:
        return None, None, None, "numpy-fft-approx"
    integ = round(-0.691 + 10.0 * math.log10(z), 2)
    return integ, integ, None, "numpy-fft-approx"


def _true_peak_dbtp(data):
    import numpy as np

    try:
        from scipy.signal import resample_poly

        up = resample_poly(data, 4, 1, axis=0)
        return _db(float(np.max(np.abs(up)))), "4x-oversample"
    except Exception:
        return _db(float(np.max(np.abs(data)))) if data.size else None, "sample-peak"


def analyze_audio(wav_path: str, max_seconds: float = 600.0) -> dict[str, Any]:
    """Measure an audio file and return a structured dictionary of acoustic features."""
    try:
        import numpy as np
        import soundfile as sf
    except ImportError as e:
        raise RuntimeError("Audio analysis requires numpy + soundfile: %s" % e)

    path = os.path.expanduser(wav_path)
    if not os.path.exists(path):
        raise FileNotFoundError("Audio file not found: %s" % path)

    data, sr = sf.read(path, always_2d=True)
    if data.shape[0] > int(max_seconds * sr):
        data = data[: int(max_seconds * sr)]
    frames, channels = data.shape
    duration = frames / float(sr) if sr else 0.0

    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(data))) if frames else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if frames else 0.0
    crest = _db(peak) - _db(rms) if (peak > 0 and rms > 0) else None

    # 4-band coarse spectral balance
    spectral = {}
    if frames > 1:
        win = mono[: 1 << int(math.floor(math.log2(min(frames, 1 << 18))))] if frames >= 2 else mono
        spectrum = np.abs(np.fft.rfft(win * np.hanning(len(win))))
        freqs0 = np.fft.rfftfreq(len(win), 1.0 / sr)
        total = float(np.sum(spectrum)) or 1.0
        for label, (lo, hi) in _LEGACY_BANDS.items():
            mask = (freqs0 >= lo) & (freqs0 < hi)
            spectral[label] = round(float(np.sum(spectrum[mask])) / total, 4)

    # 10-band spectrum and shape
    spectrum_bands: dict[str, float] = {}
    spectrum_bands_db: dict[str, float | None] = {}
    centroid = rolloff = flatness = None
    onset_strength = onset_rate = None
    if frames > 1:
        freqs, S = _stft_mag(mono, sr)
        meanmag = S.mean(axis=1)
        for i in range(len(_SPECTRUM_EDGES) - 1):
            lo, hi = _SPECTRUM_EDGES[i], _SPECTRUM_EDGES[i + 1]
            label = "%d_%d" % (lo, hi)
            frac = _band_fraction(freqs, meanmag, lo, hi)
            spectrum_bands[label] = round(frac, 4)
            spectrum_bands_db[label] = _db(frac) if frac > 0 else None

        psum = float(np.sum(meanmag)) or 1.0
        centroid = round(float(np.sum(freqs * meanmag) / psum), 1)
        cumulative = np.cumsum(meanmag)
        roll_idx = int(np.searchsorted(cumulative, 0.85 * cumulative[-1]))
        roll_idx = min(roll_idx, len(freqs) - 1)
        rolloff = round(float(freqs[roll_idx]), 1)
        pos = meanmag[meanmag > 0]
        if pos.size:
            gmean = math.exp(float(np.mean(np.log(pos))))
            amean = float(np.mean(meanmag))
            flatness = round(gmean / amean, 4) if amean > 0 else None

        if S.shape[1] >= 2:
            diff = np.diff(S, axis=1)
            flux = np.sum(np.maximum(diff, 0.0), axis=0)
            fe = np.sum(S[:, 1:], axis=0) + 1e-12
            nf = flux / fe
            onset_strength = round(float(np.mean(nf)), 4)
            if nf.size and float(np.std(nf)) > 0:
                thresh = float(np.mean(nf) + np.std(nf))
                peaks = int(np.sum((nf[1:-1] > nf[:-2]) & (nf[1:-1] >= nf[2:]) & (nf[1:-1] > thresh)))
                onset_rate = round(peaks / duration, 2) if duration > 0 else None

    cap = int(min(frames, _HEAVY_CAP_SECONDS * sr)) if frames else 0
    band_crest_db: dict[str, float | None] = {}
    band_stereo_width: dict[str, float | None] = {}
    if cap > 1:
        mono_c = mono[:cap]
        left_c = data[:cap, 0]
        right_c = data[:cap, 1] if channels >= 2 else None
        for label, (lo, hi) in _LEGACY_BANDS.items():
            b = _band_timeseries(mono_c, sr, lo, hi)
            bpeak = float(np.max(np.abs(b))) if b.size else 0.0
            brms = float(np.sqrt(np.mean(np.square(b)))) if b.size else 0.0
            band_crest_db[label] = round(_db(bpeak) - _db(brms), 2) if (bpeak > 0 and brms > 0) else None
            if right_c is not None:
                bl = _band_timeseries(left_c, sr, lo, hi)
                br = _band_timeseries(right_c, sr, lo, hi)
                mid = (bl + br) / 2.0
                side = (bl - br) / 2.0
                mrms = float(np.sqrt(np.mean(mid**2)))
                srms = float(np.sqrt(np.mean(side**2)))
                band_stereo_width[label] = round(srms / (mrms + srms + 1e-12), 4)

    correlation = None
    stereo_width = None
    if channels >= 2:
        l, r = data[:, 0], data[:, 1]
        if np.std(l) > 1e-9 and np.std(r) > 1e-9:
            correlation = round(float(np.corrcoef(l, r)[0, 1]), 4)
        mid = (l + r) / 2.0
        side = (l - r) / 2.0
        mrms = float(np.sqrt(np.mean(mid**2)))
        srms = float(np.sqrt(np.mean(side**2)))
        stereo_width = round(srms / (mrms + srms + 1e-12), 4)

    dc_offset = round(float(np.mean(mono)), 6) if frames else 0.0

    noise_floor = None
    if frames:
        fl = max(1, int(0.05 * sr))
        nfrm = frames // fl
        if nfrm >= 4:
            trimmed = mono[: nfrm * fl].reshape(nfrm, fl)
            frame_rms = np.sqrt(np.mean(trimmed**2, axis=1))
            noise_floor = _db(float(np.percentile(frame_rms[frame_rms > 0], 10))) if np.any(frame_rms > 0) else None

    thresh = 10 ** (-60 / 20.0)
    loud = np.abs(mono) > thresh
    if loud.any():
        idx = np.where(loud)[0]
        lead = round(idx[0] / float(sr), 3)
        trail = round((frames - 1 - idx[-1]) / float(sr), 3)
    else:
        lead = trail = round(duration, 3)

    try:
        lufs_i, lufs_st, lra, loud_method = _lufs_pyloudnorm(data, sr)
    except Exception:
        lufs_i, lufs_st, lra, loud_method = _lufs_numpy(data, sr)
    true_peak, tp_method = _true_peak_dbtp(data)

    return {
        "path": path,
        "sample_rate": sr,
        "channels": channels,
        "duration_sec": round(duration, 3),
        "peak_dbfs": _db(peak),
        "rms_dbfs": _db(rms),
        "crest_factor_db": round(crest, 2) if crest is not None else None,
        "clipping": bool(peak >= 0.999),
        "lufs_integrated": lufs_i,
        "lufs_short_term_max": lufs_st,
        "lufs_range_lra": lra,
        "true_peak_dbtp": true_peak,
        "loudness_method": loud_method,
        "true_peak_method": tp_method,
        "spectral_balance": spectral,
        "spectrum_bands": spectrum_bands,
        "spectrum_bands_db": spectrum_bands_db,
        "spectral_centroid_hz": centroid,
        "spectral_rolloff_hz": rolloff,
        "spectral_flatness": flatness,
        "onset_strength": onset_strength,
        "onset_rate_per_sec": onset_rate,
        "band_crest_db": band_crest_db,
        "stereo_correlation": correlation,
        "stereo_is_mono": (correlation is not None and correlation > 0.999),
        "stereo_width": stereo_width,
        "band_stereo_width": band_stereo_width,
        "dc_offset": dc_offset,
        "noise_floor_dbfs": noise_floor,
        "lead_silence_sec": lead,
        "trail_silence_sec": trail,
    }


_FLOOR_LU = 0.5
_FLOOR_BAND_DB = 0.7
_FLOOR_CENTROID = 75.0
_FLOOR_WIDTH = 0.03
_FLOOR_CREST = 0.7


def _delta(a: float | None, b: float | None) -> Optional[float]:
    if a is None or b is None:
        return None
    return round(b - a, 2)


def compare_analyses(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Diff two analyze_audio dictionaries (b relative to a) into human-readable deltas."""
    out: dict[str, Any] = {
        "loudness": {},
        "spectrum": {},
        "tone": {},
        "punch": {},
        "width": {},
        "dynamics": {},
    }
    verdicts = []

    d = _delta(a.get("lufs_integrated"), b.get("lufs_integrated"))
    if d is not None:
        out["loudness"]["lufs_integrated_delta"] = d
        if abs(d) >= _FLOOR_LU:
            verdicts.append("%+.1f LU %s" % (d, "louder" if d > 0 else "quieter"))
    tp_a, tp_b = a.get("true_peak_dbtp"), b.get("true_peak_dbtp")
    out["loudness"]["true_peak_dbtp_delta"] = _delta(tp_a, tp_b)
    if tp_b is not None and tp_b > -0.3:
        out["loudness"]["headroom_warning"] = "true peak %.1f dBTP — at/over ceiling" % tp_b

    sa, sb = a.get("spectrum_bands_db") or {}, b.get("spectrum_bands_db") or {}
    band_deltas = {}
    movers = []
    for k in sb:
        d = _delta(sa.get(k), sb.get(k))
        if d is not None:
            band_deltas[k] = d
    out["spectrum"]["band_db_delta"] = band_deltas
    for k, d in sorted(band_deltas.items(), key=lambda kv: -abs(kv[1])):
        if abs(d) >= _FLOOR_BAND_DB:
            movers.append("%s Hz %+.1f dB" % (k.replace("_", "-"), d))
    if movers:
        out["spectrum"]["summary"] = "; ".join(movers[:3])
        verdicts.append(movers[0])

    d = _delta(a.get("spectral_centroid_hz"), b.get("spectral_centroid_hz"))
    if d is not None:
        out["tone"]["spectral_centroid_hz_delta"] = d
        if abs(d) >= _FLOOR_CENTROID:
            verdicts.append("%s (%+d Hz centroid)" % ("brighter" if d > 0 else "darker", int(d)))

    ca, cb = a.get("band_crest_db") or {}, b.get("band_crest_db") or {}
    d = _delta(ca.get("low_20_120"), cb.get("low_20_120"))
    if d is not None:
        out["punch"]["low_band_crest_delta"] = d
        if abs(d) >= _FLOOR_CREST:
            verdicts.append("kick %s (low-crest %+.1f dB)" % ("punchier" if d > 0 else "more compressed", d))

    d = _delta(a.get("stereo_width"), b.get("stereo_width"))
    if d is not None:
        out["width"]["stereo_width_delta"] = d
        if abs(d) >= _FLOOR_WIDTH:
            verdicts.append("%s (width %+.2f)" % ("wider" if d > 0 else "narrower", d))
    lw = (b.get("band_stereo_width") or {}).get("low_20_120")
    if lw is not None and lw > 0.15:
        out["width"]["low_band_warning"] = "bass width %.2f — check mono compatibility" % lw

    out["dynamics"]["crest_factor_db_delta"] = _delta(a.get("crest_factor_db"), b.get("crest_factor_db"))
    out["dynamics"]["lra_delta"] = _delta(a.get("lufs_range_lra"), b.get("lufs_range_lra"))

    out["headline"] = "; ".join(verdicts) if verdicts else "no perceptible change above the noise floor"
    return out


def compare_audio(path_a: str, path_b: str, max_seconds: float = 600.0) -> dict[str, Any]:
    """Analyze two audio files and return their individual metrics plus delta comparison."""
    a = analyze_audio(path_a, max_seconds=max_seconds)
    b = analyze_audio(path_b, max_seconds=max_seconds)
    return {"a": a, "b": b, "delta": compare_analyses(a, b)}
