"""Python mirror of `src/max_time.rs`: the time of the largest sample of each trace, from the start of the trace (s).

The first sample wins a tie, as in `numpy.argmax`. `sample_period_s` has no default: it belongs to the readout.
"""
import numpy as np

NAME = "max_time"
OUTPUTS = ("max_time_s",)


def goldpan_expected(traces, params):
    """The same numbers from `goldpan.algorithms.max_time`: `{output: array}`."""
    from goldpan.algorithms import max_time
    from goldpan.config import PulseConfig
    config = PulseConfig(pretrigger_samples=0, glitch_samples=0, sample_period_s=params["sample_period_s"])
    return {"max_time_s": max_time(traces, config)}


def problem(n_samples, sample_period_s):
    if not sample_period_s > 0:
        return "sample_period_s must be positive"
    return None


def kernel(trace, sample_period_s):
    best = 0
    for i in range(1, len(trace)):
        if trace[i] > trace[best]:
            best = i
    return (best * sample_period_s,)


def cases():
    rng = np.random.default_rng(7)
    pulses = rng.normal(2000.0, 5.0, size=(10, 512))
    pulses[:, 300] += 4000.0
    ties = np.zeros((2, 16))
    ties[:, 3] = ties[:, 9] = 5.0                       # the first of two equal maxima
    return [(pulses, dict(sample_period_s=0.8e-6)), (ties, dict(sample_period_s=1.0))]


def bad_cases():
    return [(np.zeros((2, 8)), dict(sample_period_s=0.0)), (np.zeros((2, 8)), dict(sample_period_s=-1e-6)),
            (np.zeros((2, 8)), dict(sample_period_s=float("nan")))]
