"""Python mirror of `src/rise_time.rs`: the 10-90 % rise time of the largest pulse of a trace (s), as `goldpan.algorithms.rise_time`.

For one trace `x` of `n` samples:

* `baseline` = mean of `x[glitch_samples:pretrigger_samples]`, and `y[i] = x[i] - baseline`;
* the peak is the first largest `y` over **all** `n` samples (the glitch and the window included), at index `peak` with height `amp`;
* `i_lo` (`i_hi`) = the last index `i <= peak` with `y[i] < lo * amp` (`hi * amp`), or -1 if there is none;
* `rise_time_s` = `(i_hi - i_lo) * sample_period_s`, and `nan` unless `amp > 0` and both indices were found (a trace with no positive
  peak, or that never lies below the `lo` level before its peak).

`lo` and `hi` have no defaults here (the collaboration's 10 and 90 % are `lo = 0.1`, `hi = 0.9`): they are part of the definition of
the quantity, so a definition file writes them. This file is written in the *kernel subset* (see `PORTING.md`) so that it can be
ported to Rust line by line.
"""
import numpy as np

NAME = "rise_time"
OUTPUTS = ("rise_time_s",)


def goldpan_expected(traces, params):
    """The same numbers from `goldpan.algorithms.rise_time`: `{output: array}`."""
    from goldpan.algorithms import rise_time
    from goldpan.config import PulseConfig
    config = PulseConfig(pretrigger_samples=params["pretrigger_samples"], glitch_samples=params["glitch_samples"],
                         sample_period_s=params["sample_period_s"])
    return {"rise_time_s": rise_time(traces, config, lo=params["lo"], hi=params["hi"])}


def problem(n_samples, glitch_samples, pretrigger_samples, sample_period_s, lo, hi):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    if not (0 <= lo and lo < hi and hi <= 1):
        return "lo and hi must satisfy 0 <= lo < hi <= 1"
    return None


def kernel(trace, glitch_samples, pretrigger_samples, sample_period_s, lo, hi):
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
    i_lo = -1
    i_hi = -1
    for i in range(peak + 1):
        y = trace[i] - baseline
        if y < lo * amp:
            i_lo = i
        if y < hi * amp:
            i_hi = i
    if amp > 0.0 and i_lo >= 0 and i_hi >= 0:
        return ((i_hi - i_lo) * sample_period_s,)
    return (float("nan"),)


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(80)
    params = dict(glitch_samples=10, pretrigger_samples=500, sample_period_s=0.8e-6, lo=0.1, hi=0.9)
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
    ramp[:, 10:20] = np.arange(10) * 10.0                                     # a ramp 0, 10, ..., 90 then back to 0: exact 10 % and 90 % levels
    ramp[:, 20] = 100.0
    other = dict(glitch_samples=0, pretrigger_samples=10, sample_period_s=2.0, lo=0.2, hi=0.8)
    return [
        (pulses, params),
        (noise, params),
        (glitch, params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32, sample_period_s=1.0, lo=0.1, hi=0.9)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64, sample_period_s=2.5e-6, lo=0.25, hi=0.75)),
        (ramp, other),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    ok = dict(glitch_samples=0, pretrigger_samples=32, sample_period_s=1.0, lo=0.1, hi=0.9)
    return [
        (traces, {**ok, "glitch_samples": 32}),                      # no baseline window
        (traces, {**ok, "pretrigger_samples": 65}),                  # window longer than the trace
        (traces, {**ok, "sample_period_s": 0.0}),                    # no sample period
        (traces, {**ok, "sample_period_s": float("nan")}),
        (traces, {**ok, "lo": 0.9, "hi": 0.1}),                      # lo not below hi
        (traces, {**ok, "lo": -0.1}),                                # a negative level
        (traces, {**ok, "hi": 1.5}),                                 # a level above the peak
        (traces, {**ok, "lo": float("nan")}),
    ]
