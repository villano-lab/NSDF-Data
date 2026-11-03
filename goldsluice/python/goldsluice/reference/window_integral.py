"""Python mirror of `src/window_integral.rs`: the integral of the baseline-subtracted trace between two samples.

For one trace `x` of `n` samples:

* `baseline` = mean of `x[glitch_samples:pretrigger_samples]` (the window `peak` and `baseline` use);
* `window_integral` = sum of `(x[i] - baseline)` for `i` from `start_sample` to `stop_sample - 1`, times `sample_period_s`: the unit
  of the trace times seconds.

`stop_sample` is not included, as in a slice: `start_sample = 0, stop_sample = n` gives the `integral` of the whole trace, and
`stop_sample - start_sample` is the number of samples summed. The limits are free of the baseline window: they may overlap it or lie
before it. None of the parameters has a default (`integral` is the whole-trace version); `sample_period_s` belongs to the readout.

This file is written in the *kernel subset* (see `PORTING.md`) so that it can be ported to Rust line by line.
"""
import numpy as np

NAME = "window_integral"
OUTPUTS = ("window_integral",)
REVISION = 1
# Raised by one when a change makes this algorithm give different numbers for the same input (a fixed kernel): `goldsluice run`
# redoes the outputs made with the old revision, and only those made with this algorithm (see PORTING.md).


def goldpan_expected(traces, params):
    """The same numbers from goldpan's baseline (`goldpan.quantities.pretrigger_mean`), summed over the slice: `{output: array}`."""
    from goldpan.config import PulseConfig
    from goldpan.quantities import pretrigger_mean
    config = PulseConfig(pretrigger_samples=params["pretrigger_samples"], glitch_samples=params["glitch_samples"],
                         sample_period_s=params["sample_period_s"])
    traces = np.asarray(traces, dtype=float)
    part = traces[:, params["start_sample"]:params["stop_sample"]] - pretrigger_mean(traces, config)[:, np.newaxis]
    return {"window_integral": part.sum(axis=-1) * config.sample_period_s}


def problem(n_samples, glitch_samples, pretrigger_samples, sample_period_s, start_sample, stop_sample):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    if start_sample >= stop_sample:
        return f"start_sample ({start_sample}) must be smaller than stop_sample ({stop_sample})"
    if stop_sample > n_samples:
        return f"stop_sample ({stop_sample}) is past the end of the trace ({n_samples} samples)"
    return None


def kernel(trace, glitch_samples, pretrigger_samples, sample_period_s, start_sample, stop_sample):
    total = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        total += trace[i]
    baseline = total / (pretrigger_samples - glitch_samples)
    area = 0.0
    for i in range(start_sample, stop_sample):
        area += trace[i] - baseline
    return (area * sample_period_s,)


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(79)
    pulses = rng.normal(3000.0, 1.5, size=(20, 4096))
    pulses[:, 500:900] += 3000.0 * np.exp(-np.arange(400) / 80.0)    # a made-up pulse that starts where the window ends
    pulses[:, :5] += 800.0                                            # the electronics glitch: left out of the baseline, inside a window from 0
    flat = np.full((3, 64), 7.0)                                      # nothing but baseline: the integral is exactly 0
    ints = rng.integers(0, 4096, size=(5, 128)).astype(float)        # raw ADC counts
    step = np.full((2, 40), 100.0)
    step[:, 20:] += 50.0                                              # a step after the window: 50 per sample from sample 20
    run76 = dict(glitch_samples=10, pretrigger_samples=500, sample_period_s=0.8e-6)
    return [
        (pulses, dict(run76, start_sample=500, stop_sample=1000)),   # the pulse alone
        (pulses, dict(run76, start_sample=0, stop_sample=4096)),     # the whole trace: the same as `integral`
        (pulses, dict(run76, start_sample=0, stop_sample=10)),       # the glitch, before the baseline window
        (flat, dict(glitch_samples=1, pretrigger_samples=32, sample_period_s=1.0, start_sample=40, stop_sample=41)),    # one sample
        (ints, dict(glitch_samples=0, pretrigger_samples=64, sample_period_s=2.5e-6, start_sample=32, stop_sample=128)),  # over the window's end
        (step, dict(glitch_samples=0, pretrigger_samples=20, sample_period_s=0.5, start_sample=25, stop_sample=35)),    # 10 samples of 50
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    ok = dict(glitch_samples=0, pretrigger_samples=32, sample_period_s=1.0, start_sample=0, stop_sample=64)
    return [
        (traces, dict(ok, glitch_samples=32)),                       # no baseline window
        (traces, dict(ok, pretrigger_samples=65)),                   # window longer than the trace
        (traces, dict(ok, sample_period_s=0.0)),                     # no sample period
        (traces, dict(ok, sample_period_s=float("nan"))),
        (traces, dict(ok, start_sample=40, stop_sample=40)),         # nothing to sum
        (traces, dict(ok, start_sample=50, stop_sample=40)),         # the limits the wrong way round
        (traces, dict(ok, stop_sample=65)),                          # past the end
    ]
