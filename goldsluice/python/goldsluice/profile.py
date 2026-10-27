"""Time an algorithm on both backends:  `print(compare("peak", traces, glitch_samples=10, ...))`."""
import time
from dataclasses import dataclass

from .algorithms import _traces, run


@dataclass(frozen=True)
class Timing:
    name: str
    n_events: int
    n_samples: int
    rust_s: float               # best of `repeat` runs over all `n_events` traces, seconds
    python_s: float             # the Python mirror on its first `python_events` traces, scaled to `n_events`, seconds
    python_events: int

    @property
    def speedup(self):
        return self.python_s / self.rust_s

    def __str__(self):
        us = 1e6 / self.n_events
        return (f"{self.name}: {self.n_events} traces x {self.n_samples} samples\n"
                f"  rust    {self.rust_s * 1e3:10.3f} ms  ({self.rust_s * us:8.3f} us per trace)\n"
                f"  python  {self.python_s * 1e3:10.3f} ms  ({self.python_s * us:8.3f} us per trace, "
                f"from the first {self.python_events} traces)\n"
                f"  speedup {self.speedup:10.1f} x")


def _best(f, repeat):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        f()
        best = min(best, time.perf_counter() - t0)
    return best


def compare(name, traces, *, repeat=5, python_events=200, **params):
    """Best-of-`repeat` wall time of the Rust kernel over all traces, and of the Python mirror over the first `python_events`
    (it is slow), scaled up. The Rust time includes the call, the contiguity check and the output arrays, not the first-call import."""
    traces = _traces(traces)
    n_events, n_samples = traces.shape
    python_events = min(python_events, n_events)
    run(name, traces[:1], **params)                                       # import and warm up
    rust_s = _best(lambda: run(name, traces, **params), repeat)
    sub = traces[:python_events]
    python_s = _best(lambda: run(name, sub, backend="python", **params), max(1, repeat // 2)) * n_events / python_events
    return Timing(name, n_events, n_samples, rust_s, python_s, python_events)
