"""The Python mirror of every algorithm: one module per algorithm, listed in `ALL`.

A module defines `NAME`, `OUTPUTS`, `problem(n_samples, **params)`, `kernel(trace, **params)` (one trace as a plain list of floats, a
tuple of numbers back), `cases()` (the standard inputs of the parity test), `bad_cases()` (inputs both versions must refuse) and either
`goldpan_expected(traces, params)` (the same numbers from goldpan's own functions) or `NO_GOLDPAN`, a string that says why goldpan has none. The Rust function of the same `NAME` and keyword
arguments lives in `src/`; `PORTING.md` explains how to port one to the other.
"""
from . import baseline, excursion, integral, max_time, peak

ALL = [peak, max_time, baseline, integral, excursion]
