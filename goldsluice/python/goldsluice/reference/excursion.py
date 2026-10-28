"""Python mirror of `src/excursion.rs`: how far a trace strays from its baseline after the pretrigger window, and relative to its noise.

For one trace `x` of `n` samples, with the baseline window `w = x[glitch_samples:pretrigger_samples]`, its mean `m` and its
standard deviation `s` (the population one, as `baseline` computes them):

* `max_deviation`   = the largest `abs(x[i] - m)` over the samples **after** the window, `i` from `pretrigger_samples` to `n - 1`
  (the "dev" of the noise-selection notebooks; measuring it over the whole trace would put the window itself in it);
* `excursion_ratio` = `max_deviation / s` (the "ratio"). A window with no scatter (`s` = 0) gives `inf` if the trace strays and
  `nan` if it does not, as the division does in numpy.

The trace must have at least one sample after the window. This file is written in the *kernel subset* (see `PORTING.md`) so that
it can be ported to Rust line by line.
"""
import math

import numpy as np

NAME = "excursion"
OUTPUTS = ("max_deviation", "excursion_ratio")


def goldpan_expected(traces, params):
    """The same numbers from `goldpan.quantities.max_deviation` and `excursion_ratio`: `{output: array}`."""
    from goldpan.config import PulseConfig
    from goldpan.quantities import excursion_ratio, max_deviation
    config = PulseConfig(pretrigger_samples=params["pretrigger_samples"], glitch_samples=params["glitch_samples"],
                         sample_period_s=None)
    with np.errstate(divide="ignore", invalid="ignore"):                      # a flat window divides by zero: inf or nan, on purpose
        return {"max_deviation": max_deviation(traces, config), "excursion_ratio": excursion_ratio(traces, config)}


def problem(n_samples, glitch_samples, pretrigger_samples):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    if pretrigger_samples == n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) leaves no samples after the window in a trace of {n_samples} samples"
    return None


def kernel(trace, glitch_samples, pretrigger_samples):
    n = pretrigger_samples - glitch_samples
    total = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        total += trace[i]
    mean = total / n
    squares = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        d = trace[i] - mean
        squares += d * d
    std = math.sqrt(squares / n)
    deviation = 0.0
    for i in range(pretrigger_samples, len(trace)):
        d = abs(trace[i] - mean)
        if d > deviation:
            deviation = d
    if std == 0.0:
        if deviation > 0.0:
            return deviation, float("inf")
        return deviation, float("nan")
    return deviation, deviation / std


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(79)
    params = dict(glitch_samples=10, pretrigger_samples=500)
    noise = rng.normal(3000.0, 1.5, size=(10, 4096))                          # no pulse: the ratio of pure noise
    pulses = rng.normal(3000.0, 1.5, size=(10, 4096))
    pulses[:, 500:900] += 3000.0 * np.exp(-np.arange(400) / 80.0)             # a made-up pulse that starts where the window ends
    pulses[:, :5] += 800.0                                                     # the glitch: skipped, and before the window
    pulses[5:, 1000] -= 4000.0                                                 # a negative excursion is a deviation too
    flat = np.full((2, 64), 7.0)                                               # no scatter, no excursion: nan
    stepped = np.full((2, 64), 7.0)
    stepped[:, 40] = 9.0                                                       # no scatter, an excursion: inf
    ints = rng.integers(0, 4096, size=(5, 128)).astype(float)                 # raw ADC counts
    last = rng.normal(100.0, 5.0, size=(3, 32))                                # a single sample after the window
    return [
        (np.vstack([noise, pulses]), params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32)),
        (stepped, dict(glitch_samples=1, pretrigger_samples=32)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64)),
        (last, dict(glitch_samples=0, pretrigger_samples=31)),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    return [
        (traces, dict(glitch_samples=32, pretrigger_samples=32)),     # no baseline window
        (traces, dict(glitch_samples=0, pretrigger_samples=65)),      # window longer than the trace
        (traces, dict(glitch_samples=0, pretrigger_samples=64)),      # nothing after the window to measure
    ]
