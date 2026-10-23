# python/

A small library of reusable pulse operations, cuts, and derived quantities,
factored out of the exploratory work in `data_analysis/R76/notebooks/`. Flat modules
(no package/`__init__.py`), imported by adding this directory to `sys.path` --
same convention as `nrFanoII_paper2022`'s `python/ba_bknd_lines.py`.

From a notebook anywhere inside the project, find the library by looking upward,
so the code does not depend on how deep the notebook is:

```python
import sys
from pathlib import Path

_here = Path.cwd().resolve()
REPO = next((p for p in [_here, *_here.parents] if (p / "python" / "pulse_io.py").exists()), None)
assert REPO, "Start Jupyter from inside the NSDF-Data folder."
sys.path.insert(0, str(REPO / "python"))
```

From anywhere else, add the folder by hand:

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

`pulse_channels.py` says which physical channel a dump's `(detector, channel)`
pair is, from the Run 76 Setup table, for **Side-2 readout** (the December 2022 series;
`readout=1` gives the Side-1 map): `channel_name(0, 0)` is `'Side2pC'`,
`channel_label(0, 0)` is `'Side2pC (DCRC1 pA, HV2 pA)'`, `find_channel('Side2pC')`
is `(0, 0)`, `all_channels()` lists the 12 inputs and `sensor_channels()` the 6 that
are QET channels (the other six: DCRC4 pA is the NaI trigger input, five inputs are
not connected). It needs no data and no extra package. It is tagged
`under_development`: the dump's detectors 0, 1, 2 are inferred to be the boards DCRC1,
DCRC3, DCRC4, and the channels 0 to 3 are assumed to be the board inputs pA to pD.
The module docstring explains which columns of the table are used. **Until 2026-10-22
it used the wrong column** (*DCRC (2-sided)*) and named twelve sensors on two sides;
for Side-2 readout there are six, all on Side 2. What changed, by dump channel `(detector, channel)`:
(0, 3) was `Side1pF` and is `Side2pE`; (1, 0) was `Side1pE`, now `Side2pB`; (1, 1) was `Side1pB`, now
`Side2pA`; (1, 3) was `Side2pE`, now `Side2pD`; (2, 0) was `Side2pB`, now the NaI trigger input;
(0, 0) `Side2pC` and (0, 1) `Side2pF` are as before; the other inputs are not sensors.

`pulse_archive.py` is a fifth, separate module: it persists a cut's *result*
(which `detector_id`s it selected, for a given series/detector/channel) to an
HDF5 file, rather than computing something from pulse data -- see its own
docstring and `data_analysis/archives/README.md`. It's the only module
that needs `h5py`.

## `PulseConfig`

A frozen dataclass (`pretrigger_samples`, `glitch_samples`, `sample_period_s`)
passed explicitly to every function, instead of each notebook hardcoding its
own copy of these constants. Current defaults: `1000`, `10`, `0.8e-6` (see below for
the sample period; the first two match `07221203_2025_dump1_noise.ipynb` /
`07221203_2025_dump2_pulse.ipynb`).

### The sample period (changed on 2026-10-22)

**The phonon channels of the DCRC readout sample every 0.8 us (1.25 MHz), so a trace of 4096
samples is 3.2768 ms.** The library, the notebooks and the notes used 1.6 us (625 kHz) until
2026-10-22; that value was wrong and has no known source. The evidence for 0.8 us:

- The UMN run diaries of April and May 2022 (Run 76) count pulses "in 125 3.2768-ms traces" (4096 x 0.8 us),
  and the diary of 2022-04-01 says "the DCRC sampling rate of 800 ns".
- The ODB of series 07220916_2200 has `PhononWaveFormLength` = 8192 (bytes, 2 per sample, so 4096 samples)
  and `PhononPrepulseSamples` = 500, our trace length and trigger sample.
- The wiki's analysis settings: `P_SAMPLERATE` = 1.25e6 (Run 68 bats file) and `secPERsample = 8e-7` (Run 76).
- The NaI trigger pulse in DCRC4 pA, in the pyRawIO plot of the paper notebook (N-MISC-23-001, page 24) on a
  sample axis and in the BatViewer and wiki plots on a microsecond axis: 99 samples are 75 to 78 us,
  the pulse rises at sample 500 = 402 us, and the traces end at 3270 to 3277 us.

**What this means for older results.** Anything made with 1.6 us has times and energies twice too large,
frequencies twice too small, PSDs twice too large and ASDs 1.41 times too large. Everything counted in
samples or counts (cuts, selections, pulse heights) is unaffected. `PulseConfig(sample_period_s=1.6e-6)`
now emits a `UserWarning` saying so, and `pulse_archive.load_good_events` warns for an archive written with
1.6 us; remove the explicit value from your notebook so the default is used, and re-run it.

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
