"""Python mirror of `src/subtract_line.rs`: a trace minus the straight line fitted to its pretrigger samples (a transform: it returns a trace).

For one trace `x` of `n` samples, with the window `i = glitch_samples .. fit_end_samples - 1`:

* the line `y = a + b * i` (`i` the sample index, 0 to `n - 1`) is the least-squares fit to `x[i]` over the window: `b` is
  `sum((i - ib) * (x[i] - xb)) / sum((i - ib)^2)` with `ib`, `xb` the means of the index and of the samples over the window, and `a` is such
  that the line passes through `(ib, xb)` (centring the index keeps the fit accurate for traces that sit far from zero);
* the result is `x[i] - (a + b * i)` for **every** sample `i` of the trace (the glitch and everything after the window included).

This is the "pretrigger line" baseline: a line, not a constant, so a slow drift of the baseline is removed too. `fit_end_samples` is
the first sample *not* in the window; a window that stops a little before the pulse starts (the exploration code stops 94 samples
before the end of the pretrigger window) keeps the start of the pulse out of the fit. Both parameters are the readout's and have no
default. The fit is in the units of the trace (ADC counts).

This file is written in the *kernel subset* (see `PORTING.md`) so that it can be ported to Rust line by line; the sums run front to back.
`kernel` returns a list of `n` floats, not a tuple of numbers (`KIND = "trace"`).
"""
import numpy as np

NAME = "subtract_line"
KIND = "trace"
OUTPUTS = ("trace",)
REVISION = 1
# Raised by one when a change makes this algorithm give different numbers for the same input (a fixed kernel): `goldsluice run`
# redoes the outputs made with the old revision, and only those made with this algorithm (see PORTING.md).

ATOL = 1e-9
# A residual near zero has no meaningful relative error, so the parity test also allows this absolute difference (ADC counts). The two
# versions do the same operations in the same order, so in practice they are bit for bit equal; the tolerance is only a margin.

NO_GOLDPAN = ("goldpan has no counterpart that the library may import: the exploration code (data_analysis/R76/notebooks/pulse-normalization/"
              "small_triggers.py, pretrigger_line) does the fit with numpy.polyfit, and a test in tests/test_subtract_line.py checks "
              "this algorithm against numpy.polyfit")


def problem(n_samples, glitch_samples, fit_end_samples):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if fit_end_samples < glitch_samples + 2:
        return f"fit_end_samples ({fit_end_samples}) must be at least two more than glitch_samples ({glitch_samples})"
    if fit_end_samples > n_samples:
        return f"fit_end_samples ({fit_end_samples}) is longer than the trace ({n_samples} samples)"
    return None


def kernel(trace, glitch_samples, fit_end_samples):
    m = fit_end_samples - glitch_samples
    total_i = 0.0
    total_x = 0.0
    for i in range(glitch_samples, fit_end_samples):
        total_i += i
        total_x += trace[i]
    ib = total_i / m
    xb = total_x / m
    sxy = 0.0
    sxx = 0.0
    for i in range(glitch_samples, fit_end_samples):
        di = i - ib
        sxy += di * (trace[i] - xb)
        sxx += di * di
    b = sxy / sxx
    a = xb - b * ib
    out = []
    for i in range(len(trace)):
        out.append(trace[i] - (a + b * i))
    return out


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(78)
    n = 4096
    t = np.arange(n)
    pulses = rng.normal(3000.0, 1.5, size=(20, n))
    pulses += rng.normal(0.0, 0.01, size=(20, 1)) * t                  # a different slow drift in every trace
    pulses[:, 500:900] += np.linspace(0, 3000, 400)                    # a made-up pulse that starts where the window ends
    pulses[:, :5] += 800.0                                              # the electronics glitch: before the window
    tiny = rng.normal(50.0, 3.0, size=(4, 16))                          # the smallest legal window, two samples: the line passes through both
    flat = np.full((3, 64), 7.0)                                        # nothing but baseline: the result is exactly 0
    ramp = np.tile(3.0 + 0.25 * np.arange(128), (2, 1))                 # exactly a line: the result is 0 everywhere
    trap = rng.normal(3000.0, 1.5, size=(6, 600))
    trap[:, :10] += 900.0                                               # a glitch that must stay out of the fit...
    trap[:, 500:] += 400.0                                              # ...and a pulse after the window that must stay out of it too
    return [
        (pulses, dict(glitch_samples=10, fit_end_samples=406)),         # 500 - 94: the window of the exploration code
        (tiny, dict(glitch_samples=3, fit_end_samples=5)),
        (flat, dict(glitch_samples=1, fit_end_samples=64)),
        (ramp, dict(glitch_samples=0, fit_end_samples=128)),
        (trap, dict(glitch_samples=10, fit_end_samples=406)),
    ]


def bad_cases():
    """Inputs both versions must refuse, with the same message: `[(traces, params), ...]`."""
    traces = np.zeros((2, 64))
    return [
        (traces, dict(glitch_samples=32, fit_end_samples=32)),          # no window
        (traces, dict(glitch_samples=31, fit_end_samples=32)),          # one sample: no line
        (traces, dict(glitch_samples=0, fit_end_samples=65)),           # window longer than the trace
    ]
