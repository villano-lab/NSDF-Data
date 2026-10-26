"""Trace algorithms: filters and per-trace quantities (ported from `pulsedata.algorithms` of `scdms-analysis-tools`).

Like the rest of the package they work on arrays shaped `(..., n_samples)` and take the readout as a `config`; the baseline is the
pretrigger window of that `config` (the collaboration version used a fixed 10 ms, which is the window of the Z7 preset). Units
follow the trace (amps for Z7 traces) and seconds::

    clean = lowpass(pulses, 50e3, config)                      # a filtered copy
    peak = pulse_max(pulses, config)                           # one number per trace
    ev2 = compute(ev, {"max": pulse_max, "tmax": max_time}, channels=["A"])      # as quantities of an Events

A *quantity* is any function `f(pulses, config)` returning one number per trace; `compute` adds the results to an `Events` as one
record per channel (`ev2.quantities["A"]["max"]`). The baseline mean, std and subtraction already exist as
`quantities.pretrigger_mean`, `quantities.pretrigger_std` and `operations.baseline_subtract`.
"""
from dataclasses import replace

import numpy as np

from .config import PulseConfig
from .quantities import pretrigger_mean
from .status import DONE, status


@status(DONE)
def lowpass(pulses, cutoff_hz: float, config: PulseConfig, order: int = 4):
    """Zero-phase Butterworth low-pass filter of every pulse: no shift in time.

    The same magnitude response as `scipy.signal.sosfiltfilt` (`1 / (1 + (f / cutoff) ** (2 * order))`), applied with the FFT
    after odd extension of both ends so that the edges do not ring; numpy only. It agrees with scipy away from the edges (see
    the test).
    """
    pulses = np.asarray(pulses, dtype=float)
    n = pulses.shape[-1]
    pad = min(n - 1, 3 * int(round(1.0 / (cutoff_hz * config.sample_period_s))) + 1)
    left = 2 * pulses[..., :1] - pulses[..., pad:0:-1]
    right = 2 * pulses[..., -1:] - pulses[..., -2:-pad - 2:-1]
    ext = np.concatenate([left, pulses, right], axis=-1)
    f = np.fft.rfftfreq(ext.shape[-1], d=config.sample_period_s)
    response = 1.0 / (1.0 + (f / cutoff_hz) ** (2 * order))
    out = np.fft.irfft(np.fft.rfft(ext, axis=-1) * response, n=ext.shape[-1], axis=-1)
    return out[..., pad:pad + n]


@status(DONE)
def downsample(pulses, k: int):
    """Average blocks of `k` samples (a leftover tail shorter than `k` is dropped); see `downsampled_config` for the readout."""
    pulses = np.asarray(pulses)
    n = pulses.shape[-1] // k * k
    return pulses[..., :n].reshape(*pulses.shape[:-1], n // k, k).mean(axis=-1)


@status(DONE)
def downsampled_config(config: PulseConfig, k: int) -> PulseConfig:
    """The readout of `downsample(pulses, k)`: the sample period times `k`, the sample counts divided by `k`."""
    period = None if config.sample_period_s is None else config.sample_period_s * k
    return replace(config, pretrigger_samples=config.pretrigger_samples // k, glitch_samples=config.glitch_samples // k,
                   sample_period_s=period)


@status(DONE)
def pulse_max(pulses, config: PulseConfig):
    """Maximum of each trace above its pretrigger mean (units of the trace)."""
    pulses = np.asarray(pulses)
    return pulses.max(axis=-1) - pretrigger_mean(pulses, config)


@status(DONE)
def max_time(pulses, config: PulseConfig):
    """Time of the maximum from the start of the trace (s)."""
    return np.argmax(np.asarray(pulses), axis=-1) * config.sample_period_s


@status(DONE)
def integral(pulses, config: PulseConfig):
    """Integral of the baseline-subtracted trace over the whole trace (trace unit times s)."""
    pulses = np.asarray(pulses)
    return (pulses - pretrigger_mean(pulses, config)[..., np.newaxis]).sum(axis=-1) * config.sample_period_s


@status(DONE)
def rise_time(pulses, config: PulseConfig, lo: float = 0.1, hi: float = 0.9):
    """10-90% rise time of the largest pulse of each trace (s), from the last crossings of `lo` and `hi` of its height before the peak.

    NaN where the trace has no positive peak or never lies below the `lo` level before it.
    """
    pulses = np.asarray(pulses, dtype=float)
    y = pulses - pretrigger_mean(pulses, config)[..., np.newaxis]
    peak = y.argmax(axis=-1)
    amp = np.take_along_axis(y, peak[..., np.newaxis], axis=-1)[..., 0]
    index = np.arange(y.shape[-1])
    before = index <= peak[..., np.newaxis]

    def last_below(fraction):
        below = (y < fraction * amp[..., np.newaxis]) & before
        return np.where(below.any(axis=-1), np.where(below, index, -1).max(axis=-1), -1)

    i_lo, i_hi = last_below(lo), last_below(hi)
    out = (i_hi - i_lo) * config.sample_period_s
    return np.where((amp > 0) & (i_lo >= 0) & (i_hi >= 0), out, np.nan)


@status(DONE)
def compute(events, quantities, channels, config: PulseConfig = None):
    """`events` (an `Events`) with, for each of `channels`, a record of the `quantities` (name -> `f(pulses, config)`) added.

    `ev.quantities["A"]["max"]` is then one number per event. `config` defaults to the readout of the detector's main segment.
    """
    config = config or events.detector.readout.config()
    columns = {ch: {name: f(events.trace(ch), config) for name, f in quantities.items()} for ch in channels}
    return events.with_quantities(**columns)
