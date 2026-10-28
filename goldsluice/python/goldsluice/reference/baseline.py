"""Python mirror of `src/baseline.rs`: the mean and the standard deviation of the pretrigger window of a trace.

For one trace `x` of `n` samples, with `w = x[glitch_samples:pretrigger_samples]` (the same window as `peak` uses for its baseline):

* `baseline_mean` = mean of `w`;
* `baseline_std`  = standard deviation of `w` (the population one, dividing by the number of samples, as `numpy.std`).

Both are in the units of the trace (ADC counts): there is no conversion to amps here, so no `amps_per_adc`.

This file is written in the *kernel subset* (see `PORTING.md`) so that it can be ported to Rust line by line. The deviations are
summed in a second pass over the window (not `E[x^2] - E[x]^2`), which stays accurate when the baseline is large compared with its scatter.
"""
import math

import numpy as np

NAME = "baseline"
OUTPUTS = ("baseline_mean", "baseline_std")


def goldpan_expected(traces, params):
    """The same numbers from `goldpan`'s own functions (the analysis side): `{output: array}`."""
    from goldpan.config import PulseConfig
    from goldpan.quantities import pretrigger_mean, pretrigger_std
    config = PulseConfig(pretrigger_samples=params["pretrigger_samples"], glitch_samples=params["glitch_samples"],
                         sample_period_s=None)
    return {"baseline_mean": pretrigger_mean(traces, config), "baseline_std": pretrigger_std(traces, config)}


def problem(n_samples, glitch_samples, pretrigger_samples):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
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
    return mean, math.sqrt(squares / n)


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(77)
    params = dict(glitch_samples=10, pretrigger_samples=500)
    pulses = rng.normal(3000.0, 1.5, size=(20, 4096))
    pulses[:, 500:900] += np.linspace(0, 3000, 400)              # a made-up pulse that starts where the window ends
    pulses[:, :5] += 800.0                                        # the electronics glitch: inside the skipped samples
    flat = np.full((3, 64), 7.0)                                  # nothing but baseline: the deviation is exactly 0
    ints = rng.integers(0, 4096, size=(5, 128)).astype(float)    # raw ADC counts
    large = rng.normal(1.0e9, 1.0, size=(4, 256))                # a baseline large against its scatter: the second pass matters
    one = rng.normal(100.0, 5.0, size=(3, 32))                   # the smallest legal window, one sample: the deviation is 0
    return [
        (pulses, params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64)),
        (large, dict(glitch_samples=0, pretrigger_samples=256)),
        (one, dict(glitch_samples=31, pretrigger_samples=32)),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    return [
        (traces, dict(glitch_samples=32, pretrigger_samples=32)),     # no baseline window
        (traces, dict(glitch_samples=0, pretrigger_samples=65)),      # window longer than the trace
    ]
