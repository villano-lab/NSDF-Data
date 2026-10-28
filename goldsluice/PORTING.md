# From a Python mirror to Rust

Every algorithm exists twice: the Python **mirror** is the readable definition, where it is developed and tested on the standard
inputs, and the Rust **kernel** is the same computation made fast. The two must give the same numbers (`tests/test_parity.py`
enforces it for every registered algorithm). This page is how to get from one to the other.

There is no automatic translator. The mirror is written in a small subset of Python, the *kernel subset*, in which a port is a
line-by-line rewrite, and the parity test tells you at once if the port is wrong. If a handful of algorithms later show the
subset is regular enough, a translator for it is a small project; until then the rules and the table below are the tool.

## 1. Write the mirror in the kernel subset

A mirror module `python/goldsluice/reference/<name>.py` defines:

| Name | What |
|---|---|
| `NAME` | the algorithm's name, the same as the Rust function |
| `REVISION` | a whole number, **1** for a new algorithm. Raise it by one, **in the pull request that does it**, whenever a change makes the algorithm give different numbers for the same input (a fixed kernel). `goldsluice run` records the revision of each algorithm that a definition uses and redoes the outputs made with another one: only those, so adding an algorithm, or fixing one that a definition does not use, redoes nothing. Not raised for speed, messages or documentation |
| `OUTPUTS` | the names of the numbers it returns for one trace, in order, for example `("adc_max", "current_max")` |
| `problem(n_samples, **params)` | why the parameters do not fit a trace of `n_samples` (a message), or `None` |
| `kernel(trace, **params)` | **one trace** in, a tuple of numbers out |
| `cases()` | the standard inputs: `[(traces, params), ...]`, an array of shape `(n_events, n_samples)` and the keyword arguments |
| `bad_cases()` | inputs that both versions must refuse with the same message, in the same form |
| `goldpan_expected(traces, params)` **or** `NO_GOLDPAN` | the same numbers from `goldpan`'s own functions (`{output: array}`), or a string saying why goldpan has no counterpart; the parity test requires one of the two, so a quantity is never defined twice with different numbers |

Rules for `kernel`, so that it ports mechanically:

1. **One trace, scalar results.** `trace` is a plain Python list of floats; the result is a tuple of floats. The loop over traces
   is `run`'s job (in Rust, it is `rayon`'s).
2. **Loops, not array expressions.** No numpy inside `kernel`: no `trace.max()`, no `trace[a:b].mean()`, no broadcasting. Write
   the `for` loop. (Slow in Python, and that is fine: it is the specification, and a slow reference is what makes the speedup
   worth measuring.)
3. **Plain arithmetic and comparisons**, `math.sqrt`/`math.exp`, `abs`, `min`, `max` of two numbers. Nothing else from the library.
4. **Sum in the same order** as Rust will (front to back). Floating-point sums depend on order; the parity test allows a
   relative difference of `1e-12`, which is rounding, not a different formula.
5. **Every parameter is an explicit keyword with no default**, and `problem` rejects what does not fit. The readout is never assumed.
6. **Indices are `int`, samples are `float`.** Do not rely on Python's negative indices or slicing past the end.
7. **No state between traces** and no randomness.
8. **No floats in error messages.** Python writes `0.0` and `1e-06`, Rust writes `0` and `0.000001`, so the two messages would differ and the parity test fails. Name the parameter and the rule (`sample_period_s must be positive`); integers are safe.

`cases()` is part of the specification. Include an ordinary case, an edge case (a flat trace, the smallest legal window) and one
with the glitch or other trap the algorithm has to survive. Keep them small enough to run in a second.

## 2. Port it to Rust

Create `src/<name>.rs` (pure Rust, no Python types) and copy the structure of `src/peak.rs`:

* a `Params` struct with the same fields as the keyword arguments;
* `problem(n_samples, &Params) -> Option<String>` with **exactly the same messages** as the mirror (the parity test compares them);
* `<name>_one(trace: &[f64], p: &Params) -> (f64, f64)`: the kernel;
* `<name>_many(traces, n_samples, p, out...)`: the loop over traces with `par_chunks` (rayon);
* unit tests in the same file (a hand-computed case at least).

Then in `src/lib.rs` add `pub mod <name>;`, a `#[pyfunction]` named `<name>` that copies `peak_py` (same keyword-only
signature, `problem` first, `py.detach` around the loop), and one `wrap_pyfunction!` line in the module. Add the kernel to
`benches/kernels.rs`.

| Python (kernel subset) | Rust |
|---|---|
| `trace` (list of floats) | `trace: &[f64]` |
| `len(trace)` | `trace.len()` |
| `for i in range(a, b):` | `for i in a..b {` |
| `for i in range(1, len(trace)):` | `for &v in &trace[1..] {` (or `for i in 1..trace.len()`) |
| `x = 0.0` then `x += v` | `let mut x = 0.0;` then `x += v;` |
| `if a > b:` | `if a > b {` |
| `return a, b` | `(a, b)` |
| `total / n` with `n` an int | `total / n as f64` |
| `int` parameter (a sample count) | `usize` (never negative: reject a negative number in `problem` or the binding) |
| `float` parameter | `f64` |
| `math.sqrt(x)` / `abs(x)` | `x.sqrt()` / `x.abs()` |
| `max(a, b)` of two floats | `a.max(b)` (a NaN is ignored by `f64::max`; Python's `max` is not: decide, and test it) |
| `float("nan")`, `float("inf")` | `f64::NAN`, `f64::INFINITY` |
| `if not x > 0:` (also true for NaN) | `if x.is_nan() \|\| x <= 0.0 {` (clippy refuses `!(x > 0.0)`) |
| `return None` / message from `problem` | `Option<String>` |
| `raise ValueError(msg)` | `Err(PyValueError::new_err(msg))` in the binding |

Integer division and rounding differ (`//` and `round` in Python round half to even and floor toward minus infinity): write
the arithmetic as `f64` or check the cases by hand.

## 3. Register it

1. Add `from . import <name>` and the module to `ALL` in `python/goldsluice/reference/__init__.py`.
2. Make sure `src/lib.rs` exposes the function with the same name.
3. `maturin develop --release`, then `python -m pytest tests` and `cargo test`. The parity test checks that the algorithm has both
   versions, that they agree on `cases()` and that they refuse bad parameters with the same message.
4. `cargo bench`, and `goldsluice.compare("<name>", traces, ...)` on a realistic block, and put the numbers in the pull request.
5. A line under `[Unreleased]` in `CHANGELOG.md`.

## Checklist

- [ ] the mirror follows the kernel subset (no numpy in `kernel`)
- [ ] `REVISION = 1` (a new algorithm) or raised by one (a fix that changes its results)
- [ ] `problem` messages are identical in Python and Rust
- [ ] a hand-computed test in Rust and in Python
- [ ] `cases()` has an ordinary, an edge and a trap case; `bad_cases()` has one input for each way `problem` refuses
- [ ] `goldpan_expected` (or `NO_GOLDPAN` with the reason): if goldpan already has the quantity, the two agree on `cases()`
- [ ] registered in `reference/__init__.py`, exposed in `lib.rs`, added to `benches/kernels.rs`
- [ ] parity test, `cargo test` and `cargo clippy -- -D warnings` pass
- [ ] timing in the pull request (`cargo bench` and `compare`), built with `--release`

## When the kernel cannot be written this way

Some algorithms are naturally array-shaped (an FFT, a filter, a fit). Do the port in two steps: write the mirror with numpy
(it is then a *reference*, not in the kernel subset), say so at the top of the file, port to Rust using a crate (for example
`rustfft`) and keep the parity test at a tolerance that fits the algorithm (`cases()` can return it). Ask before choosing this: it
makes the port a judgment, not a rewrite.
