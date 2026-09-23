"""Cuts: pulses in, one boolean per pulse out (True = keep).

Every function takes an array shaped ``(..., n_samples)`` and returns a boolean
array of shape ``(...,)``. Cuts are plain functions of the quantities in
`pulse_quantities.py` -- combine them with ordinary `&`/`|`/`~` rather than a
special combinator API.

Percentile-based cuts (`quiet_baseline`, `excursion_below_percentile`) compute
the percentile from the batch passed in, i.e. "quiet relative to this
population" -- pass the same batch you're about to select from, not some other
reference set, unless that's actually what you want.
"""
import numpy as np

from pulse_config import PulseConfig, DEFAULT_CONFIG
from pulse_quantities import pretrigger_std, excursion_ratio
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
def excursion_band(pulses, config: PulseConfig = DEFAULT_CONFIG, low=None, high=None,
                    ratio=None):
    """True where `excursion_ratio` is in `[low, high)` (either bound optional).

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
