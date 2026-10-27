"""The Python mirror of every algorithm: one module per algorithm, listed in `ALL`.

A module defines `NAME`, `OUTPUTS`, `problem(n_samples, **params)`, `kernel(trace, **params)` (one trace as a plain list of floats, a
tuple of numbers back) and `cases()` (the standard inputs of the parity test). The Rust function of the same `NAME` and keyword
arguments lives in `src/`; `PORTING.md` explains how to port one to the other.
"""
from . import peak

ALL = [peak]
