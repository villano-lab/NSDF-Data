"""Cuts: pulses in, one boolean per pulse out (True = keep).

Every function takes an array shaped ``(..., n_samples)`` and returns a boolean
array of shape ``(...,)``. Cuts are plain functions of the quantities in
`pulse_quantities.py` -- combine them with ordinary `&`/`|`/`~` rather than a
special combinator API.

`randoms` and `real_triggers` are the exception: they take an array of trigger-type
labels (see `pulse_io.trigger_types`), not pulses, since that is per-event metadata.

Percentile-based cuts (`quiet_baseline`, `excursion_below_percentile`) compute
the percentile from the batch passed in, i.e. "quiet relative to this
population" -- pass the same batch you're about to select from, not some other
reference set, unless that's actually what you want.
"""
import numpy as np

from pulse_config import PulseConfig, DEFAULT_CONFIG
from pulse_quantities import (
    pretrigger_std, excursion_ratio, log_excursion_ratio, excursion_duration,
)
from pulse_status import status, DONE, UNDER_DEVELOPMENT


@status(DONE)
def dead_channel(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """True where the pretrigger std is exactly zero -- channel not read out for
    this pulse, not merely a quiet channel. See the Detector 0/Channel 2 finding
    in 07221203_2025_dump1_noise.ipynb (100% dead in that dump)."""
    return pretrigger_std(pulses, config) == 0


@status(DONE)
def active(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """`~dead_channel`, as its own name for readability at call sites."""
    return ~dead_channel(pulses, config)


@status(DONE)
def quiet_baseline(pulses, config: PulseConfig = DEFAULT_CONFIG, percentile: float = 75,
                    bstd=None):
    """True where `pretrigger_std` is below its own `percentile`-th value across the
    *active* pulses in this batch. Dead channels are always excluded (never True).

    Pass a precomputed `bstd` (e.g. `pulse_quantities.pretrigger_std(pulses, config)`)
    to avoid recomputing it when combining with other cuts on the same batch.
    """
    if bstd is None:
        bstd = pretrigger_std(pulses, config)
    is_active = bstd > 0
    if not np.any(is_active):
        return np.zeros_like(is_active)
    cap = np.percentile(bstd[is_active], percentile)
    return is_active & (bstd < cap)


@status(DONE)
def ratio_band(pulses, config: PulseConfig = DEFAULT_CONFIG, low=None, high=None,
                ratio=None):
    """True where `excursion_ratio` (linear, not log) is in `[low, high)` (either
    bound optional). The generic band-threshold utility -- see `excursion_band`
    for the specific log10(ratio) cut used by the Branch 2 exploration.

    Pass a precomputed `ratio` (e.g. `pulse_quantities.excursion_ratio(pulses, config)`)
    to avoid recomputing it when combining with other cuts on the same batch.
    """
    if ratio is None:
        ratio = excursion_ratio(pulses, config)
    mask = np.ones(ratio.shape, dtype=bool)
    if low is not None:
        mask &= ratio >= low
    if high is not None:
        mask &= ratio < high
    return mask


@status(DONE)
def excursion_band(pulses, config: PulseConfig = DEFAULT_CONFIG, low=0.5, high=0.7,
                    log_ratio=None):
    """True where `log_excursion_ratio` is in `[low, high)` -- default `[0.5, 0.7)`,
    the "tight" Branch 2 cut from 07221203_2025_dump1_noise.ipynb (cleanest
    slice found there, though even it keeps 13 of its 192 traces that look like
    real pulses -- see `excursion_band_AI`). Pass a
    `config` with the pretrigger window you want (Branch 2 used 500 samples, not
    the library default of 1000).

    Pass a precomputed `log_ratio` (e.g.
    `pulse_quantities.log_excursion_ratio(pulses, config)`) to avoid recomputing
    it when combining with other cuts on the same batch.
    """
    if log_ratio is None:
        log_ratio = log_excursion_ratio(pulses, config)
    return (log_ratio >= low) & (log_ratio < high)


@status(DONE)
def excursion_band_loose(pulses, config: PulseConfig = DEFAULT_CONFIG, log_ratio=None):
    """`excursion_band` widened to `[0.5, 1.0)` -- the "loose" Branch 2 cut from
    07221203_2025_dump1_noise.ipynb (more traces retained, somewhat more
    contamination than the tight `[0.5, 0.7)` default)."""
    return excursion_band(pulses, config, low=0.5, high=1.0, log_ratio=log_ratio)


@status(UNDER_DEVELOPMENT, note="matches the original dump1_noise 'good noise' cut, "
        "which the same notebook's widened-Cut-A investigation found is biased "
        "toward contaminated-baseline traces rather than quiet ones when used alone "
        "-- combine with quiet_baseline (already the notebook's practice) rather "
        "than relying on this in isolation")
def excursion_below_percentile(pulses, config: PulseConfig = DEFAULT_CONFIG,
                                percentile: float = 25, ratio=None):
    """True where `excursion_ratio` is below its own `percentile`-th value across the
    active pulses in this batch. Convenience wrapper matching the original
    dump1_noise notebook's "good noise" ratio cut -- see its module docstring
    for why a *low* ratio is not automatically "quieter."""
    if ratio is None:
        ratio = excursion_ratio(pulses, config)
    finite = np.isfinite(ratio)
    if not np.any(finite):
        return np.zeros_like(finite)
    thresh = np.percentile(ratio[finite], percentile)
    return finite & (ratio < thresh)


@status(UNDER_DEVELOPMENT, note="'looks like a pulse' is a judgment call, not a "
        "validated physical criterion. Flags traces whose excursion stays near "
        "its own peak for a long *consecutive* run (excursion_duration >= "
        "min_duration), which a real detector pulse's rise-then-decay does and "
        "ordinary noise usually doesn't. default min_duration=50 was picked by "
        "eye from a real gap in the data (07221203_2025_F0001, Detector0/Channel0, "
        "500-sample window): within the tight excursion_band, 179/192 traces "
        "had duration <= 25 and the other 13 had duration >= 168 -- nothing in "
        "between -- and those 13 are visually unambiguous real pulses/drifts, the "
        "other 179 visually flat noise. Devised for excursion_band_AI -- treat as a "
        "first guess to be checked against the traces it flags on any new dataset, "
        "not ground truth.")
def looks_like_pulse(pulses, config: PulseConfig = DEFAULT_CONFIG, min_duration: int = 50,
                      duration=None):
    """True where `excursion_duration` is at or above `min_duration` samples."""
    if duration is None:
        duration = excursion_duration(pulses, config)
    return duration >= min_duration


@status(UNDER_DEVELOPMENT, note="excursion_band ([0.5, 0.7) by default) with "
        "looks_like_pulse traces removed -- i.e. 'whatever Claude judged to be a "
        "real pulse, taken out.' Both the band and the pulse-shape veto are "
        "judgment calls; treat this as an exploratory variant of excursion_band, "
        "not an independently validated cut, and check what it removes before "
        "trusting it on a new dataset.")
def excursion_band_AI(pulses, config: PulseConfig = DEFAULT_CONFIG, low=0.5, high=0.7,
                       log_ratio=None, min_duration: int = 50, duration=None):
    """`excursion_band(low, high)` with `looks_like_pulse` traces removed."""
    band = excursion_band(pulses, config, low=low, high=high, log_ratio=log_ratio)
    pulse_like = looks_like_pulse(pulses, config, min_duration=min_duration, duration=duration)
    return band & ~pulse_like


RANDOM_TRIGGER_LABEL = "Physics"
REAL_TRIGGER_LABEL = "Unknown"


@status(UNDER_DEVELOPMENT, note="assumes the dump's trigger_type labels are swapped "
        "relative to their names: events recorded as 'Physics' are taken to be "
        "randoms (fixed-count random triggers) and 'Unknown' to be real triggers. "
        "That mapping is a working assumption from 07221203_2025_F0001 (see Note 2a), "
        "not confirmed against the DAQ configuration or the nsdf library")
def randoms(trigger_types, label: str = RANDOM_TRIGGER_LABEL):
    """True where the recorded trigger type equals `label` (default `"Physics"`), taken
    to be random triggers. Takes the trigger-type array from `pulse_io.trigger_types`
    rather than pulses."""
    return np.asarray(trigger_types) == label


@status(UNDER_DEVELOPMENT, note="the other half of the randoms assumption: events "
        "recorded as 'Unknown' are taken to be real (pulse-triggered) events. Not "
        "confirmed; see `randoms`")
def real_triggers(trigger_types, label: str = REAL_TRIGGER_LABEL):
    """True where the recorded trigger type equals `label` (default `"Unknown"`), taken
    to be real triggers. Takes the trigger-type array from `pulse_io.trigger_types`
    rather than pulses."""
    return np.asarray(trigger_types) == label
