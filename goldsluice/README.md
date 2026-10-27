# goldsluice

Fast pulse-reduction kernels in Rust, with a **Python mirror of every algorithm**. It is the reduction half of the pair that
`goldpan` (analysis, in `../python/`) belongs to. It is in its first steps: one algorithm, `peak`.

```python
from goldsluice import run, compare

traces = ...                  # float array, shape (n_events, n_samples): one channel
out = run("peak", traces, glitch_samples=10, pretrigger_samples=1000, amps_per_adc=1.5e-9)
out["adc_max"]                # largest raw ADC value of each trace
out["current_max"]            # largest current above the pretrigger baseline of each trace, in amps

run("peak", traces, backend="python", ...)     # the same through the Python mirror (slow; for development)
print(compare("peak", traces, ...))            # time both backends and the speedup
```

Nothing about the readout is assumed: `amps_per_adc`, `glitch_samples` and `pretrigger_samples` have no defaults.

## How it is laid out

| Where | What |
|---|---|
| `src/<algorithm>.rs` | the kernel in pure Rust: no Python types, unit tests next to it |
| `src/lib.rs` | the Python bindings (`goldsluice._core`): one function per algorithm, same name and keyword arguments as the mirror |
| `python/goldsluice/reference/<algorithm>.py` | the **Python mirror**: the readable definition, the place to develop and to define the standard inputs |
| `python/goldsluice/algorithms.py` | `run(name, traces, backend=..., **params)` |
| `python/goldsluice/profile.py` | `compare(...)`: the timing of both backends |
| `benches/kernels.rs` | `cargo bench`: the Rust kernels alone, with no Python |
| `tests/test_parity.py` | every algorithm has both versions, they agree on the standard inputs and refuse bad parameters alike |

## Build and test

You need Rust (<https://rustup.rs>; on Windows also the Visual Studio *Build Tools* with "Desktop development with C++") and Python
with `numpy`, `pytest` and `maturin`. From this folder, in your Python environment:

```
python -m pip install maturin pytest numpy
maturin develop --release
python -m pytest tests
cargo test
cargo bench
```

`maturin develop --release` builds the Rust and installs `goldsluice` in place. Always use `--release` when timing: a debug build is
slower by a factor of ten or more.

## Writing an algorithm

Write the Python mirror first, then port it to Rust, then register both: **`PORTING.md`** is the guide, with the rules the Python
must follow so that the port is mechanical, a table of the equivalent Python and Rust, and a checklist.

## Timing

Two levels, on purpose:

* `cargo bench` times the kernel alone (no Python, no copy). It is the number to optimise.
* `goldsluice.compare` times what a user sees: the call from Python, the conversion of the input, the output arrays, against the
  Python mirror (timed on a sample of the traces and scaled, because it is slow).

Rust kernels run over the traces in parallel (`rayon`); `RAYON_NUM_THREADS=1` gives the single-thread time.
