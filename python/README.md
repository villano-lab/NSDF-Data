# python/

A small library of reusable pulse operations, cuts, and derived quantities,
factored out of the exploratory work in `R76/analysis_notes/`. Flat modules
(no package/`__init__.py`), imported by adding this directory to `sys.path` --
same convention as `nrFanoII_paper2022`'s `python/ba_bknd_lines.py`.

```python
import sys
sys.path.insert(0, "/path/to/NSDF-Data/python")

import pulse_quantities as q
import pulse_cuts as cuts
import pulse_operations as op
import pulse_io as io
from pulse_config import PulseConfig
```

## Convention: samples on the last axis

Every function takes an array shaped `(..., n_samples)` -- a single pulse
`(n_samples,)` or a whole batch `(n_pulses, n_samples)` both work unchanged,
since all reductions run along `axis=-1`. There's no custom pulse-collection
class; a plain NumPy array *is* the pulse (or batch of pulses).

## The three categories

| Module | Signature | Returns |
|---|---|---|
| `pulse_quantities.py` | `(pulses, config, **params)` | one number (or spectrum) per pulse, shape `(...,)` or `(..., n_freq)` |
| `pulse_cuts.py` | `(pulses, config, **params)` | one bool per pulse, shape `(...,)` (`True` = keep) |
| `pulse_operations.py` | `(pulses, config, **params)` | new pulses, same pulse-shaped family as the input |

Quantities are the primitives; cuts are built by thresholding a quantity
(e.g. `ratio_band` thresholds `excursion_ratio`, `excursion_band` thresholds
`log_excursion_ratio`) and combine with plain `&`/`|`/`~`; operations are
independent transforms (baseline subtraction, glitch trimming) and never
mutate their input in place.

`pulse_cuts.excursion_band` (default `[0.5, 0.7)`) and `excursion_band_loose`
(`[0.5, 1.0)`) are the two named log10(ratio) cuts from the Branch 2
exploration in `07221203_2025_dump1_noise.ipynb` -- pass a `config` with the
pretrigger window you want (Branch 2 used 500 samples). `excursion_band_AI`
additionally removes traces `pulse_cuts.looks_like_pulse` flags as containing
a real pulse (a sustained, consecutive-sample excursion rather than a brief
noise fluctuation) -- an exploratory heuristic, not a validated cut; see its
docstring/status note before trusting it on a new dataset. `ratio_band` is the
older, fully generic linear-ratio band-threshold utility (any `low`/`high`,
no default), used e.g. by `07221203_2025_dump2_pulse.ipynb`'s `ratio > 9` cut.

`pulse_io.py` is the only module that knows about `nsdf_dark_matter`'s `cdms`
objects -- `load_channel_batch` turns a list of `detector_id`s into a plain
`(n_pulses, n_samples)` array for everything else to consume.

`pulse_archive.py` is a fifth, separate module: it persists a cut's *result*
(which `detector_id`s it selected, for a given series/detector/channel) to an
HDF5 file, rather than computing something from pulse data -- see its own
docstring and `archives/README.md` at the repo root. It's the only module
that needs `h5py`.

## `PulseConfig`

A frozen dataclass (`pretrigger_samples`, `glitch_samples`, `sample_period_s`)
passed explicitly to every function, instead of each notebook hardcoding its
own copy of these constants. Current defaults (`1000`, `10`, `1.6e-6`) match
`07221203_2025_dump1_noise.ipynb` / `07221203_2025_dump2_pulse.ipynb`.

## Function status: `done` vs. `under_development`

Every function in `pulse_quantities.py`/`pulse_cuts.py`/`pulse_operations.py`/
`pulse_io.py` is tagged with `@status(DONE)` or `@status(UNDER_DEVELOPMENT, note=...)`
from `pulse_status.py`. `under_development` functions still run, but emit a
`UserWarning` (with the note) on every call, so a notebook that depends on one
says so in its own output instead of silently looking as settled as everything
else.

```python
from pulse_status import status, DONE, UNDER_DEVELOPMENT, list_statuses

@status(DONE)
def pretrigger_mean(pulses, config=DEFAULT_CONFIG):
    ...

@status(UNDER_DEVELOPMENT, note="only checked against single-peak traces so far")
def rise_sample(pulses, config=DEFAULT_CONFIG, fraction=0.5):
    ...

list_statuses(pulse_quantities)  # {"pretrigger_mean": ("done", None), "rise_sample": ("under_development", "..."), ...}
```

As of today, `rise_sample` and `excursion_below_percentile` (known to be
biased toward contaminated traces when used *alone* -- see its docstring),
plus `excursion_duration`, `looks_like_pulse`, and `excursion_band_AI` (the
"is this actually a pulse" heuristic and the cut built on it), are
`under_development`; everything else is `done`.

## Tests

Synthetic-data unit tests (no real detector data or `nsdf_dark_matter`
dependency) live in `tests/`:

```
cd python && python -m pytest tests/ -v
```

They need `numpy` + `pytest` (present in the base conda env; `pytest` is
*not* currently in `darkmatter_cli_env`). The library modules themselves only
need `numpy`, so they work fine under either environment -- `pulse_io.py` is
the only file that additionally needs `nsdf_dark_matter` at import time (only
because it calls into a `cdms` object you already have), and `pulse_archive.py`
the only one that needs `h5py` (installed in both `darkmatter_cli_env` and the
base conda env as of 2026-09-23).
