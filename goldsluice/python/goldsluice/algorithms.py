"""Run an algorithm by name on either backend: the compiled Rust kernel or its Python mirror.

    from goldsluice import run
    out = run("peak", traces, glitch_samples=10, pretrigger_samples=1000, amps_per_adc=1.5e-9)
    out["adc_max"], out["current_max"]                   # one value per trace
    run("peak", traces, backend="python", ...)           # the mirror: slow, for development and checking

`traces` is an array of shape `(n_events, n_samples)` (one channel); it is converted to C-contiguous float64. Every parameter is
keyword-only and has no default.

Most algorithms reduce a trace to numbers (`KIND = "quantities"`: one value per trace for each name in `OUTPUTS`). A few **transform** a
trace into another trace (`KIND = "trace"`, `OUTPUTS = ("trace",)`): a filter, a baseline subtraction. Their result is an array of
the shape of `traces`, and a batch run can hand it to the steps that name it as their `input` (`goldpan.dataset`).
"""
import numpy as np

from . import reference

ALGORITHMS = {m.NAME: m for m in reference.ALL}

QUANTITIES, TRACE = "quantities", "trace"


def kind(name) -> str:
    """`"quantities"` (the algorithm reduces a trace to numbers) or `"trace"` (it returns a trace of the same length)."""
    try:
        return getattr(ALGORITHMS[name], "KIND", QUANTITIES)
    except KeyError:
        raise ValueError(f"no algorithm {name!r}; known: {sorted(ALGORITHMS)}") from None


def _traces(traces):
    traces = np.ascontiguousarray(traces, dtype=np.float64)
    if traces.ndim != 2:
        raise ValueError(f"traces must have shape (n_events, n_samples), not {traces.shape}")
    return traces


def run(name, traces, *, backend="rust", **params):
    """`{output name: array of one value per trace}` of algorithm `name`; `backend` is `"rust"` or `"python"`."""
    try:
        algorithm = ALGORITHMS[name]
    except KeyError:
        raise ValueError(f"no algorithm {name!r}; known: {sorted(ALGORITHMS)}") from None
    traces = _traces(traces)
    if backend == "rust":
        from . import _core
        result = getattr(_core, name)(traces, **params)
    elif backend == "python":
        why = algorithm.problem(traces.shape[1], **params)
        if why:
            raise ValueError(why)
        rows = [algorithm.kernel(row, **params) for row in traces.tolist()]
        if kind(name) == TRACE:
            result = (np.array(rows, dtype=np.float64).reshape(traces.shape),)
        elif rows:
            result = tuple(np.array(column, dtype=np.float64) for column in zip(*rows))
        else:
            result = tuple(np.empty(0) for _ in algorithm.OUTPUTS)
    else:
        raise ValueError(f"backend must be 'rust' or 'python', not {backend!r}")
    return dict(zip(algorithm.OUTPUTS, result))
