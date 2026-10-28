"""Python mirror of `src/integral.rs`: the integral of the baseline-subtracted trace over the whole trace.

For one trace `x` of `n` samples:

* `baseline` = mean of `x[glitch_samples:pretrigger_samples]` (the window `peak` and `baseline` use);
* `integral` = sum over all `n` samples of `(x[i] - baseline)`, times `sample_period_s`: the unit of the trace times seconds.

The sum runs over the whole trace, the baseline window and the glitch samples included, as `goldpan.algorithms.integral` does.
`sample_period_s` has no default: it belongs to the readout.

This file is written in the *kernel subset* (see `PORTING.md`) so that it can be ported to Rust line by line.
"""
import numpy as np

NAME = "integral"
OUTPUTS = ("integral",)


def goldpan_expected(traces, params):
    """The same numbers from `goldpan.algorithms.integral`: `{output: array}`."""
    from goldpan.algorithms import integral
    from goldpan.config import PulseConfig
    config = PulseConfig(pretrigger_samples=params["pretrigger_samples"], glitch_samples=params["glitch_samples"],
                         sample_period_s=params["sample_period_s"])
    return {"integral": integral(traces, config)}


def problem(n_samples, glitch_samples, pretrigger_samples, sample_period_s):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    return None


def kernel(trace, glitch_samples, pretrigger_samples, sample_period_s):
    total = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        total += trace[i]
    baseline = total / (pretrigger_samples - glitch_samples)
    area = 0.0
    for i in range(len(trace)):
        area += trace[i] - baseline
    return (area * sample_period_s,)


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(78)
    params = dict(glitch_samples=10, pretrigger_samples=500, sample_period_s=0.8e-6)
    pulses = rng.normal(3000.0, 1.5, size=(20, 4096))
    pulses[:, 500:900] += 3000.0 * np.exp(-np.arange(400) / 80.0)    # a made-up pulse that starts where the window ends
    pulses[:, :5] += 800.0                                            # the electronics glitch: skipped by the baseline, not by the sum
    flat = np.full((3, 64), 7.0)                                      # nothing but baseline: the integral is exactly 0
    ints = rng.integers(0, 4096, size=(5, 128)).astype(float)        # raw ADC counts
    step = np.full((2, 40), 100.0)
    step[:, 20:] += 50.0                                              # a step after the window: 20 samples of 50
    return [
        (pulses, params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32, sample_period_s=1.0)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64, sample_period_s=2.5e-6)),
        (step, dict(glitch_samples=0, pretrigger_samples=20, sample_period_s=0.5)),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    return [
        (traces, dict(glitch_samples=32, pretrigger_samples=32, sample_period_s=1.0)),                  # no baseline window
        (traces, dict(glitch_samples=0, pretrigger_samples=65, sample_period_s=1.0)),                   # window longer than the trace
        (traces, dict(glitch_samples=0, pretrigger_samples=32, sample_period_s=0.0)),                   # no sample period
        (traces, dict(glitch_samples=0, pretrigger_samples=32, sample_period_s=float("nan"))),
    ]
