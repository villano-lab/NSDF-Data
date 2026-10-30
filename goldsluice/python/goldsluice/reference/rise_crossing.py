"""Python mirror of `src/rise_crossing.rs`: the time at which the rising edge of the largest pulse of a trace crosses `fraction` of its height (s).

For one trace `x` of `n` samples:

* `baseline` = mean of `x[glitch_samples:pretrigger_samples]`, and `y[i] = x[i] - baseline`;
* the peak is the first largest `y` over **all** `n` samples (the glitch and the window included), at index `peak` with height `amp`;
* `level` = `fraction * amp`, and `i` = the last index `i <= peak` with `y[i] < level`, or -1 if there is none;
* the crossing lies between samples `i` and `i + 1`, and is found by linear interpolation:
  `crossing_time_s` = `(i + (level - y[i]) / (y[i + 1] - y[i])) * sample_period_s`, from the start of the trace (as `max_time_s`);
* the result is `nan` unless `amp > 0` and `i` was found (a trace with no positive peak, or that never lies below the level before its peak).

This is the same last-crossing rule as `rise_time`, for one level, with the sample fraction kept (a rise time of a few samples is
too coarse to tell where on the face an event is). It is computed on the trace as it is: no filter is applied, so it is noisier than
a time taken from a filtered pulse. `fraction` has no default: 0.2 gives the 20 % time that the collaboration's position quantities
(`xdel`, `ydel`, the delays between channels) are made of. A step of a definition file writes it. This file is written in the *kernel
subset* (see `PORTING.md`) so that it can be ported to Rust line by line.
"""
import numpy as np

NAME = "rise_crossing"
OUTPUTS = ("crossing_time_s",)
REVISION = 1
# Raised by one when a change makes this algorithm give different numbers for the same input (a fixed kernel): `goldsluice run`
# redoes the outputs made with the old revision, and only those made with this algorithm (see PORTING.md).

NO_GOLDPAN = ("goldpan has no counterpart: its rise_time is the difference of two sample indices and keeps no time of its own, "
              "and no goldpan function interpolates between samples")


def problem(n_samples, glitch_samples, pretrigger_samples, sample_period_s, fraction):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    if not (0 <= fraction and fraction <= 1):
        return "fraction must satisfy 0 <= fraction <= 1"
    return None


def kernel(trace, glitch_samples, pretrigger_samples, sample_period_s, fraction):
    total = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        total += trace[i]
    baseline = total / (pretrigger_samples - glitch_samples)
    peak = 0
    amp = trace[0] - baseline
    for i in range(1, len(trace)):
        y = trace[i] - baseline
        if y > amp:
            amp = y
            peak = i
    level = fraction * amp
    last = -1
    for i in range(peak + 1):
        y = trace[i] - baseline
        if y < level:
            last = i
    if amp > 0.0 and last >= 0:
        y0 = trace[last] - baseline
        y1 = trace[last + 1] - baseline
        return ((last + (level - y0) / (y1 - y0)) * sample_period_s,)
    return (float("nan"),)


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(81)
    params = dict(glitch_samples=10, pretrigger_samples=500, sample_period_s=0.8e-6, fraction=0.2)
    t = np.arange(4096)
    pulses = rng.normal(3000.0, 1.5, size=(20, 4096))
    for k in range(20):                                                       # a rise of a different length for each trace
        start, rise = 500 + k, 4 + k
        shape = np.where(t < start, 0.0, np.where(t < start + rise, (t - start) / rise, np.exp(-(t - start - rise) / 300.0)))
        pulses[k] += (800.0 + 100.0 * k) * shape
    pulses[:, :5] += 80.0                                                     # a glitch smaller than the pulse: the peak is the pulse
    noise = rng.normal(3000.0, 1.5, size=(5, 4096))                          # no pulse: the largest noise excursion is the peak
    glitch = rng.normal(3000.0, 1.5, size=(3, 4096))
    glitch[:, :5] += 800.0                                                    # a glitch at the very start: the peak is sample 0, no rise
    glitch[:, 600:700] += 300.0
    flat = np.full((2, 64), 7.0)                                              # amp is 0: nan
    ints = rng.integers(0, 4096, size=(6, 128)).astype(float)                # raw ADC counts: many ties and exact thresholds
    ramp = np.zeros((2, 40))
    ramp[:, 10:20] = np.arange(10) * 10.0                                     # a ramp 0, 10, ..., 90 then back to 0: the 20 % level is exactly on sample 12
    ramp[:, 20] = 100.0
    other = dict(glitch_samples=0, pretrigger_samples=10, sample_period_s=2.0, fraction=0.25)
    return [
        (pulses, params),
        (noise, params),
        (glitch, params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32, sample_period_s=1.0, fraction=0.2)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64, sample_period_s=2.5e-6, fraction=0.75)),
        (ramp, other),
        (ramp, dict(other, fraction=0.0)),                                    # the level is the baseline itself
        (ramp, dict(other, fraction=1.0)),                                    # the level is the peak
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    ok = dict(glitch_samples=0, pretrigger_samples=32, sample_period_s=1.0, fraction=0.2)
    return [
        (traces, {**ok, "glitch_samples": 32}),                      # no baseline window
        (traces, {**ok, "pretrigger_samples": 65}),                  # window longer than the trace
        (traces, {**ok, "sample_period_s": 0.0}),                    # no sample period
        (traces, {**ok, "sample_period_s": float("nan")}),
        (traces, {**ok, "fraction": -0.1}),                          # a negative level
        (traces, {**ok, "fraction": 1.5}),                           # a level above the peak
        (traces, {**ok, "fraction": float("nan")}),
    ]
