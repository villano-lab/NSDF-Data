"""Pulse height helpers for the pulse-normalization notebooks (series 07221203_2025).

Shared by `small-physics-triggers-07221203_2025.ipynb` (which holds its own copy of the same two
functions, from the first version of the study) and `detector-layout-small-triggers-07221203_2025.ipynb`.
Exploration code: not part of the library in `python/`.

The drift-robust rise height: fit a straight line to the pretrigger samples (after the glitch, ending 75 us
before the trigger because the pulses start to rise up to ~40 us before it), extend it over the first 200
samples after the trigger, subtract it, smooth with an 8-sample moving average, and take the largest value.
A drift continues along the line and gives no excess; a pulse rises at the trigger and does.
"""
import numpy as np

WINDOW = 200          # samples after the trigger in which the rise height is measured
SMOOTH = 8            # moving-average length (samples)
FIT_GAP = 94          # the line is fitted up to this many samples before the trigger (94 samples = 75 us)
TAIL_FROM_US = 1500.0 # the two-sided baseline is also fitted to the trace from this time after the trigger on
BASELINE_ORDER = 2    # order of that polynomial (3 is no better than 2 on these events)
QUIET_PRE_MAX = 1.75  # quiet pretrigger: the worst channel's pretrigger residual RMS is below this times the randoms' median


def fit_end(config):
    """Index at which the pretrigger line fit stops."""
    return config.pretrigger_samples - FIT_GAP


def pretrigger_line(traces, config):
    """The straight line fitted to the pretrigger samples of each trace, evaluated at every sample: (..., n_samples)."""
    traces = np.asarray(traces, dtype=float)
    g, end = config.glitch_samples, fit_end(config)
    x = np.arange(traces.shape[-1])
    slope, intercept = np.polyfit(x[g:end], traces[..., g:end].T, 1)
    return slope[..., None] * x + intercept[..., None]


def subtract_pretrigger_line(traces, config):
    """Traces with their pretrigger line subtracted over the whole trace."""
    traces = np.asarray(traces, dtype=float)
    return traces - pretrigger_line(traces, config)


def rise_height(pulses, config, window=WINDOW, smooth=SMOOTH):
    """Drift-robust pulse height (counts): the largest smoothed excess above the extended pretrigger line
    in the first `window` samples after the trigger. `pulses` is (n_pulses, n_samples)."""
    pulses = np.asarray(pulses, dtype=float)
    start = config.pretrigger_samples
    g, end = config.glitch_samples, fit_end(config)
    slope, intercept = np.polyfit(np.arange(g, end), pulses[:, g:end].T, 1)
    x_win = np.arange(start, start + window + smooth - 1)
    resid = pulses[:, x_win] - (slope[:, None] * x_win + intercept[:, None])
    csum = np.cumsum(np.pad(resid, ((0, 0), (1, 0))), axis=1)
    smoothed = (csum[:, smooth:] - csum[:, :-smooth]) / smooth
    return smoothed.max(axis=1)


# ---- a baseline fitted on both sides of the pulse -------------------------------------------------------------
def _time_us(n_samples, config):
    return (np.arange(n_samples) - config.pretrigger_samples) * config.sample_period_s * 1e6


def two_sided_baseline(traces, config, order=BASELINE_ORDER, tail_from_us=TAIL_FROM_US):
    """Polynomial baseline fitted to the pretrigger samples (after the glitch, up to `fit_end`) **and** to the late
    tail (from `tail_from_us` after the trigger to the end of the trace), leaving the pulse out. Interpolating across the
    pulse is more stable than extending a pretrigger line over the whole trace. Returns (..., n_samples)."""
    traces = np.asarray(traces, dtype=float)
    n = traces.shape[-1]
    t = _time_us(n, config)
    use = np.zeros(n, dtype=bool)
    use[config.glitch_samples:fit_end(config)] = True
    use |= t >= tail_from_us
    x = t / (t[-1] - t[0]) * 2.0            # roughly -0.3 .. 2 for conditioning
    coef = np.polyfit(x[use], traces[..., use].T, order)
    return np.polyval(coef, x[(slice(None),) + (None,) * (coef.ndim - 1)]).T


def window(config, n_samples, start_us, stop_us):
    """Boolean mask of the samples between two times (microseconds from the trigger)."""
    t = _time_us(n_samples, config)
    return (t >= start_us) & (t < stop_us)


def subtract_baseline(traces, config, order=BASELINE_ORDER, tail_from_us=TAIL_FROM_US):
    """Traces with the two-sided baseline subtracted over the whole trace."""
    traces = np.asarray(traces, dtype=float)
    return traces - two_sided_baseline(traces, config, order=order, tail_from_us=tail_from_us)


def pretrigger_residual_rms(traces, config):
    """RMS (counts) of the residual about the fitted pretrigger line, over the samples the line is fitted to
    (after the glitch, up to `fit_end`). Large when a pulse, a step or a strong curvature sits in the pretrigger window.
    `traces` is (n_traces, n_samples)."""
    traces = np.asarray(traces, dtype=float)
    g, end = config.glitch_samples, fit_end(config)
    resid = traces[:, g:end] - pretrigger_line(traces, config)[:, g:end]
    return np.sqrt((resid ** 2).mean(axis=1))


def quiet_pretrigger(pre_rms, reference, limit=QUIET_PRE_MAX):
    """The quiet-pretrigger cut. `pre_rms` maps channel -> `pretrigger_residual_rms` of every event; `reference` is a boolean
    mask of the events that set each channel's normal level (the randoms: the median of their pretrigger RMS is the unit).
    Returns (ratio, quiet): for every event the largest over the channels of pre_rms / unit, and ratio < limit.
    A pulse that starts in the pretrigger window (a pile-up), a step, or strong curvature makes the ratio large."""
    ratio = np.max([pre_rms[k] / np.median(pre_rms[k][reference]) for k in pre_rms], axis=0)
    return ratio, ratio < limit
