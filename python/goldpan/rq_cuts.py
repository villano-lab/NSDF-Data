"""Selections made from already-processed RQs, with no raw traces: the fast path (ported from `scdms-analysis-tools`).

The idea is the excursion ratio of `goldpan.quantities`, `|max| / std` per channel, computed from the RQs a reconstruction
has already stored, so that selecting clean random triggers needs no raw-file access::

    ratios = phonon_log_ratios(rqs, channels)                  # log10(|max| / std) of each channel
    clean = tight_randoms(ratios, low, pileup_thresholds, tight_ranges)

What this module does **not** contain is any analysis result: the per-channel thresholds, floors and ranges are derived
from one dataset's own distributions, so they are always passed in. The channel names are passed in too (a mapping's keys,
or `channels=`); `Z7_PHONON_CHANNELS` is the list of the Z7 phonon channels, for convenience.

Units of the RQ files this was written for (BatCommon's `BasicPulseCalc`): `P<ch>max` is stored in **microamps** and
`P<ch>std` in amps, so `channel_max_amps` converts before a ratio is taken (`MAX_RQ_UA_TO_A`). A channel with no data for an
event (absent from the mapping, or NaN) is skipped rather than failing the event. The total phonon channel `PT` has no
`max` or `std` RQ of its own: `pt_std_proxy` estimates its std from the other channels (uncorrelated noise assumed).
"""
import numpy as np

from .status import DONE, UNDER_DEVELOPMENT, status

Z7_PHONON_CHANNELS = ["PAS1", "PAS2", "PBS1", "PBS2", "PCS1", "PCS2",
                      "PDS1", "PDS2", "PES1", "PES2", "PFS1", "PFS2"]
"""The twelve phonon channels of Z7, in RQ naming."""

MAX_RQ_UA_TO_A = 1e-6
"""`P<ch>max` is stored in microamps (BatCommon `BasicPulseCalc.cxx`, `fMaximum = minMax.max*1e6`), `P<ch>std` in amps."""


@status(DONE)
def channel_max_amps(max_rq):
    """`P<ch>max` (stored in microamps) converted to amps, the unit of `P<ch>std`, before taking a ratio."""
    return np.asarray(max_rq) * MAX_RQ_UA_TO_A


@status(DONE)
def pt_std_proxy(std_rqs_by_channel, channels=None):
    """Estimate of the total channel's baseline std from the channels' own `std` RQs: `sqrt(sum(std_i ** 2))`.

    `std_rqs_by_channel`: a mapping channel -> array (one entry per event), or a list of such arrays. `channels` limits a
    mapping to those names (default: all of its keys). Assumes uncorrelated noise, so the variances add; it is an
    approximation, not an RQ of the processing. Built from whichever channels are present: not all of them are required.
    """
    if isinstance(std_rqs_by_channel, dict):
        names = list(std_rqs_by_channel) if channels is None else [c for c in channels if c in std_rqs_by_channel]
        arrays = [np.asarray(std_rqs_by_channel[c]) for c in names]
    else:
        arrays = [np.asarray(a) for a in std_rqs_by_channel]
    return np.sqrt(np.sum(np.stack(arrays, axis=0) ** 2, axis=0))


@status(DONE)
def excursion_ratio_rq(amp, std):
    """`|amp| / std`: the RQ-only stand-in for `goldpan.quantities.excursion_ratio`.

    `amp`: `channel_max_amps(P<ch>max)`, or `PTOFamps` for the total channel (no `PTmax` exists); `std`: `P<ch>std` or
    `pt_std_proxy(...)`. Same length, aligned to the same events.
    """
    return np.abs(np.asarray(amp)) / np.asarray(std)


@status(DONE)
def log_excursion_ratio_rq(amp, std):
    """`log10(excursion_ratio_rq(amp, std))`."""
    return np.log10(excursion_ratio_rq(amp, std))


@status(DONE)
def phonon_log_ratios(rqs, channels):
    """`log10(|P<ch>max| / P<ch>std)` for each of `channels` that has both RQs in `rqs` (a mapping of RQ name to array).

    Ready for `pileup_randoms`, `loose_randoms` and `tight_randoms`. A zero `std` gives infinity, not an error.
    """
    out = {}
    for ch in channels:
        if f"{ch}max" in rqs and f"{ch}std" in rqs:
            with np.errstate(divide="ignore", invalid="ignore"):
                out[ch] = log_excursion_ratio_rq(channel_max_amps(rqs[f"{ch}max"]), rqs[f"{ch}std"])
    return out


@status(DONE)
def excursion_band_rq(log_ratio, low, high):
    """True where `log_ratio` is in `[low, high)`. No default band: the bands differ from channel to channel."""
    log_ratio = np.asarray(log_ratio)
    return (log_ratio >= low) & (log_ratio < high)


def _n_events(log_ratios_by_channel):
    return len(next(iter(log_ratios_by_channel.values())))


@status(DONE)
def pileup_randoms(log_ratios_by_channel, thresholds):
    """True where a random trigger is pileup-contaminated: ANY channel's `log10(ratio)` is above its entry in `thresholds`.

    In every phonon channel the pooled `log10(ratio)` of random triggers has a main noise peak, a gap, then a sparse pileup
    cluster; a channel's threshold is, for example, the start of that gap. The numbers are an analysis result and are
    passed in. `log_ratios_by_channel`: channel -> array (from `phonon_log_ratios`); `thresholds`: channel -> value. A
    channel absent from the first, or NaN for an event, is skipped.
    """
    mask = np.zeros(_n_events(log_ratios_by_channel), dtype=bool)
    for ch, threshold in thresholds.items():
        if ch not in log_ratios_by_channel:
            continue
        x = np.asarray(log_ratios_by_channel[ch], dtype=float)
        with np.errstate(invalid="ignore"):
            mask |= np.isfinite(x) & (x > threshold)
    return mask


def _all_channels_in(log_ratios_by_channel, low_by_channel, high_by_channel):
    """True where every channel that has data (and a range) is in [low, high)."""
    ok = np.ones(_n_events(log_ratios_by_channel), dtype=bool)
    for ch, x in log_ratios_by_channel.items():
        if ch not in low_by_channel:
            continue
        x = np.asarray(x, dtype=float)
        with np.errstate(invalid="ignore"):
            inside = (x >= low_by_channel[ch]) & (x < high_by_channel[ch])
        ok &= ~np.isfinite(x) | inside
    return ok


@status(DONE)
def loose_randoms(log_ratios_by_channel, low, pileup_thresholds):
    """True for a clean-enough random trigger: every channel with data has `log10(ratio) >= low`, and it is not `pileup_randoms`.

    `low` is one sanity floor for every channel; each channel's upper limit is its pileup threshold. Only the channels named in
    `pileup_thresholds` take part (a channel with no threshold is not judged).
    """
    low_by_channel = {ch: low for ch in pileup_thresholds}
    high = {ch: np.inf for ch in pileup_thresholds}
    return (_all_channels_in(log_ratios_by_channel, low_by_channel, high)
            & ~pileup_randoms(log_ratios_by_channel, pileup_thresholds))


@status(DONE)
def tight_randoms(log_ratios_by_channel, low, pileup_thresholds, tight_ranges):
    """True for a clean random trigger: `loose_randoms`, and every channel with data inside its `tight_ranges` entry.

    `tight_ranges`: channel -> `(low, high)`, the "broad peak" of that channel's smoothed `log10(ratio)` histogram with
    pileup removed (an analysis result, passed in). A subset of `loose_randoms`.
    """
    lo = {ch: l for ch, (l, h) in tight_ranges.items()}
    hi = {ch: h for ch, (l, h) in tight_ranges.items()}
    return (loose_randoms(log_ratios_by_channel, low, pileup_thresholds)
            & _all_channels_in(log_ratios_by_channel, lo, hi))


@status(UNDER_DEVELOPMENT, note="ported from scdms-analysis-tools line_cuts, written for one Z7 calibration line; the RQ names "
                                 "are those of that reconstruction")
def triggered_physics(rqs, detector, physics_event_type=1):
    """Physics triggers (`EventType == physics_event_type`) that were fired by `detector` (`TriggerDetectorNum`)."""
    return (np.asarray(rqs["EventType"]) == physics_event_type) & (np.asarray(rqs["TriggerDetectorNum"]) == detector)


@status(UNDER_DEVELOPMENT, note="ported from scdms-analysis-tools line_cuts (ten_kev_line); the per-series windows are an analysis "
                                 "result set by eye, and the RQ names are those of the Z7 reconstruction")
def calibration_line(rqs, windows, detector, allow_missing=False):
    """True for triggered physics events inside their series' line window: `PTOFamps` in `amp` and `PTOFdelay` in a `delay` window.

    `rqs` needs `series`, `EventType`, `TriggerDetectorNum`, `PTOFamps` and `PTOFdelay`. `windows`: series ->
    `dict(amp=(lo, hi), delay=[(lo, hi), ...])`, passed in (they are an analysis result). `detector`: the trigger detector
    number, required. A series of `rqs` with no window raises `ValueError` naming it, rather than quietly returning False
    (which would look like a series with no line events); `allow_missing=True` gives False for those series instead.
    """
    series = np.asarray(rqs["series"])
    names, counts = np.unique(series, return_counts=True)
    missing = [(str(s), int(n)) for s, n in zip(names, counts) if str(s) not in windows]
    if missing and not allow_missing:
        listed = ", ".join(f"{s} ({n} events)" for s, n in missing[:10])
        more = f", and {len(missing) - 10} more" if len(missing) > 10 else ""
        raise ValueError(f"no line window for {len(missing)} series: {listed}{more}. "
                         f"Windows exist only for {sorted(windows)}; pass allow_missing=True to get False for these.")
    amp, delay = np.asarray(rqs["PTOFamps"]), np.asarray(rqs["PTOFdelay"])
    ok = np.zeros(len(series), dtype=bool)
    for s, w in windows.items():
        in_delay = np.zeros(len(series), dtype=bool)
        for lo, hi in w["delay"]:
            in_delay |= (delay > lo) & (delay < hi)
        ok |= (series == s) & (amp > w["amp"][0]) & (amp < w["amp"][1]) & in_delay
    return ok & triggered_physics(rqs, detector)
