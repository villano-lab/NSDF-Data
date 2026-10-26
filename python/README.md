# python/

**goldpan**: a library of reusable pulse operations, cuts and derived quantities, factored out of the exploratory work
in `data_analysis/R76/notebooks/`. It is a Python package, `goldpan`, in the folder `python/goldpan/`.

**Install it** (it is part of the setup): `requirements.txt` installs this folder in place, so `pip install -r
requirements.txt`, run from the `NSDF-Data` folder as the setup and updating guides do (or only the library:
`python -m pip install -e ./python`), makes it importable from any folder, with no `sys.path` snippet. An edit to a
module takes effect at once. `check_environment.py` warns if it is not installed. The library has its own version, in
`python/pyproject.toml`.

```python
from goldpan import quantities as q
from goldpan import cuts, operations as op, io
from goldpan.config import DCRC_RUN76, Z7, PulseConfig

config = DCRC_RUN76                      # name the readout of your data (see below)
bstd = q.pretrigger_std(pulses, config)
quiet = cuts.quiet_baseline(pulses, config)
```

**The container.** `goldpan.data.Events` holds one detector's events and is **immutable**: its `detector` (name, channels
with roles, and the readout with its segments), its `traces` (read-only arrays, one per channel and segment, `ev.trace("A")`), its
`quantities` (an Awkward Array, one record per event; the first fields `series`, `dump`, `event` identify the event) and its `meta`
(provenance). `select`, `with_quantities` and `concatenate` return new objects. Nothing in it opens a file: adapters do (next paragraph). See the design notes of 2026-10-25 and 2026-10-26 (`GoldpanGoldsluice/` in the log repository).

```python
from goldpan.data import ChannelInfo, Detector, Events, Readout
detector = Detector("S104", (ChannelInfo("A", role="phonon"), ChannelInfo("B", role="phonon")), Readout.single(4096, DCRC_RUN76))
ev = Events.from_arrays(detector, {"A": traces_a, "B": traces_b}, series="07221203_2025", dump="F0001")
std = q.pretrigger_std(ev.trace("A"), ev.detector.readout.config())      # the readout comes from the detector
quiet = ev.select(cuts.quiet_baseline(ev.trace("A"), ev.detector.readout.config()))
```

**Adapters.** The only code that knows a file format. `goldpan.adapters.parquet` is the native format (reads and writes; its docstring is the
specification, format version 1: one Parquet file per series and dump, plain Arrow types, a `_goldpan.json` manifest), and `goldpan.adapters.idx` reads
a dump of the NSDF archive. `read` returns an `Events`; `iter_chunks` reads a big dataset a chunk at a time. Someone with another format (MIDAS, ROOT) writes
a small module with `read(path, **kw) -> Events` and checks it with `goldpan.testing.check_adapter`; `goldpan.adapters.register` makes it available
to `goldpan.adapters.read(path, format=...)`. A small synthetic dataset to test against is in `python/tests/data/sample_dataset/`.

```python
from goldpan.adapters import idx, parquet
from goldpan.channels import sensor_channels
channels = {c.name: (c.detector, c.channel) for c in sensor_channels()}
ev = idx.read('~/idx/07221203_2025_F0001', detector_name='NSDF', channels=channels, config=DCRC_RUN76)   # the readout is given, never assumed
parquet.write(ev, 'my_dataset')                      # needs the extra: pip install pyarrow (in requirements.txt)
for chunk in parquet.iter_chunks('my_dataset', chunk=256): ...   # or parquet.read('my_dataset', channels=['Side2pC'])
```

**Synthetic data in every format.** `python python/tests/synthetic_series.py OUTDIR` writes one small made-up series (two dumps, six Side-2
sensors plus the other DCRC inputs, 4096 samples at 0.8 us) as an idx dump, as SuperCDMS SNOLAB MIDAS files (`.mid.gz`, CDMS I/O library format version 8),
as RQs in Parquet and in ROOT (`rqDir/eventTree` and `rqDir/zip1`), and as a native goldpan dataset, all from the same events, so that every adapter and
every cross-format check has data to read. Nothing in it is detector data. `python/tests/test_synthetic_series.py` uses it.

**Algorithms from the collaboration library.** `goldpan.rq_cuts` selects clean random triggers and calibration lines from already-processed RQs
(`phonon_log_ratios`, `pileup_randoms`, `loose_randoms`, `tight_randoms`, `calibration_line`): the thresholds and windows are analysis results and are
always passed in, never defaults. `goldpan.algorithms` has the trace filters (`lowpass`, zero-phase Butterworth, numpy only; `downsample`) and per-trace
quantities (`pulse_max`, `max_time`, `integral`, `rise_time`), and `compute` adds them to an `Events` as one record per channel. Both are ports of
`scdms-analysis-tools`, with the readout taken from a `config` instead of being fixed to Z7.

**The readout is never assumed.** In the package, every function that needs the pretrigger window, the glitch samples
or the sample period takes a `config` and has **no default** for it: the numbers belong to a *readout*, not to the library,
and a silent wrong default (the library once assumed 1.6 us for a readout that samples every 0.8 us) changes every time,
frequency and energy without any error. Use a preset (`goldpan.config.DCRC_RUN76`: the Run 76 phonon channels, 0.8 us;
`goldpan.config.Z7`: the Z7 readout, 1.6 us) or give the numbers.

**The old flat names still work.** The first versions were eight flat modules (`pulse_quantities`, `pulse_cuts`,
`pulse_operations`, `pulse_io`, `pulse_config`, `pulse_archive`, `pulse_channels`, `pulse_status`), and the existing
notebooks, notes and guides import them. They are now thin aliases of the package modules (`goldpan.legacy`) with one
difference: the functions that take a `config` default to the Run 76 readout, and `pulse_config.PulseConfig` has the
Run 76 values as defaults. So `import pulse_cuts as pc; pc.quiet_baseline(pulses)` is the same as `goldpan.cuts.quiet_baseline(pulses,
DCRC_RUN76)`. New code uses `goldpan.*`; the flat names will be removed in a later release.

If the library is not installed (a checkout used without `pip install`), the fallback is to put the folder on `sys.path`:

```python
import sys
from pathlib import Path

_here = Path.cwd().resolve()
REPO = next((p for p in [_here, *_here.parents] if (p / "python" / "pulse_io.py").exists()), None)
assert REPO, "Start Jupyter from inside the NSDF-Data folder."
sys.path.insert(0, str(REPO / "python"))
```

## Convention: samples on the last axis

Every function takes an array shaped `(..., n_samples)` -- a single pulse
`(n_samples,)` or a whole batch `(n_pulses, n_samples)` both work unchanged,
since all reductions run along `axis=-1`. There's no custom pulse-collection
class; a plain NumPy array *is* the pulse (or batch of pulses).

## The three categories

| Module | Signature | Returns |
|---|---|---|
| `goldpan.quantities` | `(pulses, config, **params)` | one number (or spectrum) per pulse, shape `(...,)` or `(..., n_freq)` |
| `goldpan.cuts` | `(pulses, config, **params)` | one bool per pulse, shape `(...,)` (`True` = keep) |
| `goldpan.operations` | `(pulses, config, **params)` | new pulses, same pulse-shaped family as the input |

Quantities are the primitives; cuts are built by thresholding a quantity
(e.g. `ratio_band` thresholds `excursion_ratio`, `excursion_band` thresholds
`log_excursion_ratio`) and combine with plain `&`/`|`/`~`; operations are
independent transforms (baseline subtraction, glitch trimming) and never
mutate their input in place.

`goldpan.cuts.excursion_band` (default `[0.5, 0.7)`) and `excursion_band_loose`
(`[0.5, 1.0)`) are the two named log10(ratio) cuts from the Branch 2
exploration in `07221203_2025_dump1_noise.ipynb` -- pass a `config` with the
pretrigger window you want (Branch 2 used 500 samples). `excursion_band_AI`
additionally removes traces `goldpan.cuts.looks_like_pulse` flags as containing
a real pulse (a sustained, consecutive-sample excursion rather than a brief
noise fluctuation) -- an exploratory heuristic, not a validated cut; see its
docstring/status note before trusting it on a new dataset. `ratio_band` is the
older, fully generic linear-ratio band-threshold utility (any `low`/`high`,
no default), used e.g. by `07221203_2025_dump2_pulse.ipynb`'s `ratio > 9` cut.

`goldpan.io` is the only module that knows about `nsdf_dark_matter`'s `cdms`
objects -- `load_channel_batch` turns a list of `detector_id`s into a plain
`(n_pulses, n_samples)` array for everything else to consume.

`goldpan.channels` says which physical channel a dump's `(detector, channel)`
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

`goldpan.archive` is a fifth, separate module: it persists a cut's *result*
(which `detector_id`s it selected, for a given series/detector/channel) to an
HDF5 file, rather than computing something from pulse data -- see its own
docstring and `data_analysis/archives/README.md`. It's the only module
that needs `h5py`.

## `PulseConfig` and the readout

A frozen dataclass (`pretrigger_samples`, `glitch_samples`, `sample_period_s`) passed explicitly to every function, instead
of each notebook hardcoding its own copy of these constants. **In `goldpan.config` it has no defaults** (pass
`sample_period_s=None` if the period is unknown: functions that need it then raise). The presets are
`DCRC_RUN76 = PulseConfig(1000, 10, 0.8e-6)` and `Z7 = PulseConfig(6250, 10, 1.6e-6)`. In the flat alias
`pulse_config`, `PulseConfig()` has the Run 76 values as defaults (see above).

### The sample period (changed on 2026-10-22)

**The phonon channels of the DCRC readout of Run 76 sample every 0.8 us (1.25 MHz), so a trace of 4096
samples is 3.2768 ms.** (The Z7 readout samples every 1.6 us, 625 kHz: the value is a property of the readout.) The library, the notebooks and the notes used 1.6 us (625 kHz) until
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
samples or counts (cuts, selections, pulse heights) is unaffected. The flat alias `pulse_config.PulseConfig(sample_period_s=1.6e-6)`
emits a `UserWarning` saying so (it is the Run 76 readout), and `pulse_archive.load_good_events` warns for an archive written with
1.6 us; remove the explicit value from your notebook so the default is used, and re-run it.

## Function status: `done` vs. `under_development`

Every function in `goldpan.quantities`/`goldpan.cuts`/`goldpan.operations`/`goldpan.io` is tagged with
`@status(DONE)` or `@status(UNDER_DEVELOPMENT, note=...)` from `goldpan.status`. `under_development` functions still run, but emit a
`UserWarning` (with the note) on every call, so a notebook that depends on one
says so in its own output instead of silently looking as settled as everything
else.

```python
from goldpan.status import status, DONE, UNDER_DEVELOPMENT, list_statuses

@status(DONE)
def pretrigger_mean(pulses, config):
    ...

@status(UNDER_DEVELOPMENT, note="only checked against single-peak traces so far")
def rise_sample(pulses, config, fraction=0.5):
    ...

list_statuses(quantities)  # {"pretrigger_mean": ("done", None), "rise_sample": ("under_development", "..."), ...}
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
need `numpy`, so they work fine under either environment -- `goldpan.io` is
the only file that additionally needs `nsdf_dark_matter` at import time (only
because it calls into a `cdms` object you already have), and `goldpan.archive`
the only one that needs `h5py` (installed in both `darkmatter_cli_env` and the
base conda env as of 2026-09-23).
