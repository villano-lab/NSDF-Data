"""Python mirror of `src/lowpass.rs`: a zero-phase Butterworth low-pass filter of a trace (a transform: it returns a trace).

**This mirror is a *reference*, not in the kernel subset** (see "When the kernel cannot be written this way" in `PORTING.md`): the filter
is made with the FFT, so `kernel` uses numpy, and the Rust kernel uses the `rustfft` crate. The two agree to rounding, not bit for bit,
which is why `ATOL` is set.

The recipe is the one of `goldpan.algorithms.lowpass` (the two must give the same numbers; goldsluice never imports goldpan, so it is
written out here). For one trace `x` of `n` samples, with `dt = sample_period_s`:

* `pad = min(n - 1, 3 * round(1 / (cutoff_hz * dt)) + 1)`, where `round` is `floor(v + 0.5)` (half up). Python's own `round` rounds half
  to even and Rust's rounds half away from zero; the three agree except exactly at .5, which is not a realistic input, and this
  definition is the same in both languages;
* both ends are extended by `pad` samples with odd symmetry about the end points (`2 * x[0] - x[pad .. 1]` in front,
  `2 * x[n-1] - x[n-2 .. n-1-pad]` behind), so that the edges do not ring, giving `N = n + 2 * pad` samples;
* the spectrum of the extended trace is multiplied by `1 / (1 + (f / cutoff_hz) ** (2 * order))` (the magnitude response of a
  Butterworth filter, applied forwards and backwards, so there is no phase shift), `f` being the frequency of the bin;
* the result is the middle `n` samples of the inverse transform.

`cutoff_hz` (below the Nyquist frequency), `order` (1 or more) and `sample_period_s` are the filter's and the readout's and have no
default. `kernel` returns a list of `n` floats (`KIND = "trace"`).
"""
import math

import numpy as np

NAME = "lowpass"
KIND = "trace"
OUTPUTS = ("trace",)
REVISION = 1
# Raised by one when a change makes this algorithm give different numbers for the same input (a fixed kernel): `goldsluice run`
# redoes the outputs made with the old revision, and only those made with this algorithm (see PORTING.md).

ATOL = 1e-9
# rustfft and numpy's pocketfft round differently. On the standard inputs (traces of a few thousand counts, up to 4096 samples) the
# largest absolute difference measured between the Rust kernel and numpy was 5.5e-12 on `cases()` and 7.3e-12 on 500 traces of 4096
# samples (3000 counts of baseline, a 3000-count pulse); `ATOL` is more than 100 times that, and far below any digitiser count. A
# relative tolerance alone cannot do: a filtered sample near zero has no meaningful relative error.


def goldpan_expected(traces, params):
    """The same numbers from `goldpan`'s own function (the analysis side): `{output: array}`."""
    from goldpan.algorithms import lowpass
    from goldpan.config import PulseConfig
    config = PulseConfig(pretrigger_samples=1, glitch_samples=0, sample_period_s=params["sample_period_s"])
    return {"trace": lowpass(traces, params["cutoff_hz"], config, params["order"])}


def problem(n_samples, cutoff_hz, order, sample_period_s):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    if not cutoff_hz > 0:
        return "cutoff_hz must be positive"
    if not cutoff_hz < 0.5 / sample_period_s:
        return "cutoff_hz must be below the Nyquist frequency, half the sampling frequency"
    if order < 1:
        return "order must be at least 1"
    if n_samples < 2:
        return f"a trace needs at least 2 samples ({n_samples} given)"
    return None


def kernel(trace, cutoff_hz, order, sample_period_s):
    x = np.asarray(trace, dtype=np.float64)
    n = x.shape[0]
    pad = min(n - 1, 3 * math.floor(1.0 / (cutoff_hz * sample_period_s) + 0.5) + 1)
    left = 2.0 * x[0] - x[1:pad + 1][::-1]
    right = 2.0 * x[n - 1] - x[n - 1 - pad:n - 1][::-1]
    ext = np.concatenate([left, x, right])
    f = np.fft.rfftfreq(ext.shape[0], d=sample_period_s)
    response = 1.0 / (1.0 + (f / cutoff_hz) ** (2 * order))
    out = np.fft.irfft(np.fft.rfft(ext) * response, n=ext.shape[0])
    return out[pad:pad + n].tolist()


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(79)
    dt = 0.8e-6
    pulses = rng.normal(3000.0, 1.5, size=(12, 4096))
    pulses[:, 500:900] += np.linspace(0, 3000, 400) * np.exp(-np.arange(400) / 150.0)    # a made-up pulse
    pulses[:, :5] += 800.0                                                               # the electronics glitch at the start: the odd extension must cope
    flat = np.full((3, 256), 7.0)                                                        # nothing but baseline: stays 7
    short = rng.normal(100.0, 5.0, size=(4, 2))                                          # the shortest legal trace
    small = rng.normal(100.0, 5.0, size=(4, 64))                                         # pad is limited by the trace length
    ints = rng.integers(0, 4096, size=(5, 512)).astype(float)                            # raw ADC counts
    return [
        (pulses, dict(cutoff_hz=95e3, order=4, sample_period_s=dt)),
        (pulses[:4], dict(cutoff_hz=30e3, order=1, sample_period_s=dt)),
        (flat, dict(cutoff_hz=50e3, order=2, sample_period_s=dt)),
        (short, dict(cutoff_hz=95e3, order=4, sample_period_s=dt)),
        (small, dict(cutoff_hz=30e3, order=3, sample_period_s=dt)),
        (ints, dict(cutoff_hz=200e3, order=6, sample_period_s=dt)),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    ok = dict(cutoff_hz=100e3, order=4, sample_period_s=0.8e-6)
    return [
        (traces, {**ok, "sample_period_s": 0.0}),                  # not positive
        (traces, {**ok, "sample_period_s": float("nan")}),
        (traces, {**ok, "cutoff_hz": 0.0}),                        # not positive
        (traces, {**ok, "cutoff_hz": float("nan")}),
        (traces, {**ok, "cutoff_hz": 700e3}),                      # above the Nyquist frequency (625 kHz) of 0.8 us
        (traces, {**ok, "order": 0}),                              # no filter
        (np.zeros((2, 1)), ok),                                    # a trace of one sample
    ]
