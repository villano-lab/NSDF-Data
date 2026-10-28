---
id: "TBD"
title: "What are the packages `goldpan` and `goldsluice`?"
author: "Anthony Villano"
date: "2026-10-26"
status: "In progress"
keywords: "libraries, data analysis, pip, PyPI"
description: "In doing some early data analysis--for example Notes 2, 7, and 9--it was useful to make some library functions. Those originally sat in `python/` at the top level of the `NSDF-Data` repository. As the tools have grown it seems like putting them into their own Python package makes sense. I am starting that work and there will be two resulting packages `goldpan` and `goldsluice` that are explained a bit in this note."
---

<!-- The clickable outline at the top of the published page is built from the ## headings below: do not write one. -->

## Code repository

- [`rq-histogram-goldpan.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/22f308d7590971578a25c9051da242d9a7b8057d/data_analysis/R76/notebooks/goldpan-goldsluice/rq-histogram-goldpan.ipynb) — reads the RQs of a series from ROOT files with `goldpan`, histograms one of them, then loads the traces of the same events and plots the RQs over the pulses. It runs on the small synthetic files saved next to it (`synthetic-rq/`, `synthetic-goldpan/`), so it works on a fresh clone with no raw data.
- [`goldsluice-processed-plots.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/22f308d7590971578a25c9051da242d9a7b8057d/data_analysis/R76/notebooks/goldpan-goldsluice/goldsluice-processed-plots.ipynb) — reads back the Parquet dataset that `goldsluice` wrote for Run 76 series `07221203_2025` (30 dumps, 81,992 events, six phonon channels, the quantities `adc_max` and `current_max`) and plots the distributions, the correlations between channels and the trend from dump to dump. The processed files are the output of `python -m goldsluice run r76.dataset.toml` in `goldsluice/examples/` and are not in the repository.
- [`goldsluice-root-rqs.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/6000af9835e48009074a238c383f9dff0be43feb/data_analysis/R76/notebooks/goldpan-goldsluice/goldsluice-root-rqs.ipynb) — opens the RQs of a `goldsluice` run written as ROOT files (`rqDir/eventTree`, `rqDir/zip1`, `infoDir/goldsluice`) with `goldpan`, prints and draws the structure of the files, and plots the quantities `adc_max`, `current_max` and `max_time_s` of the six phonon channels. The ROOT files are in `~/goldsluice-output/`, written by `goldsluice`, and are not in the repository.

The first two links are pinned to commit `22f308d` and the third to commit `6000af9`: they show the notebooks as they were at those commits, which may be older than the latest versions, and the files may have moved since (see `data_analysis/README.md`).

## Data and setup

Say which series, dump, detector and channel you used, and define every quantity.

## The question

What are the packages `goldpan` and `goldsluice`? These are data analysis programs that are made to analyze processed data and to process pulse data respectively. `goldsluice` might take in some raw pulses and integrate them, saving the values of the integrals into a file. Those values are sometimes called Reduced Quantities (RQs) and they are in turn analyzed and/or manipulated with `goldpan` to get science results. Any generic function for fetching or manipulating data would go in these programs, rather than sitting in multiple people's analysis codes. The names were chosen with the help of AI because we want to discover something valuable in the data, one program takes a huge chunk of raw data and makes it manageable (`goldsluice`) and one sifts through very carefully for the key science (`goldpan`). 

## Reading data and doing a simple analysis with `goldpan`

A *dataset definition file* tells `goldpan` where the data are and how to read them: the source (the raw files, their format and the detector they came from), and, through the detector registry, the readout of that detector (sample period, trigger position, channel names). Nothing about the electronics is assumed in the code. `Dataset.open` reads the file; no data are read until we ask for them.

The file used here is `goldsluice/examples/r76-registry.dataset.toml`. A copy as of this note, to copy into a file of your own (the `registry` and `glob` paths and the output folder are the ones to change):

```toml
# The same dataset as r76.dataset.toml, with the detector described in the registry (../../registry) instead of in this file:
# the readout, the channel map and the roles come from the record of "NAI-S2", and root_detector from its `number`.
# Everything written here wins over the registry, key by key. `python -m goldsluice check r76-registry.dataset.toml` lists the files.

[dataset]
name = "r76-07221203"
output = "~/goldsluice-output/r76-07221203"
registry = ["../../registry"]                  # folders of detector records, relative to this file (goldpan.registry); also GOLDPAN_REGISTRY
# output_format = "root"                       # for ROOT output the zip<N> number is the record's `number`: no root_detector needed

[[sources]]
name = "side2"
format = "idx"
glob = "~/idx/07221203_2025_F*"
detector = "NAI-S2"                            # in the registry: it supplies readout = "DCRC_RUN76" and the idx channels and roles

[[processing]]
algorithm = "peak"
channels = "role:phonon"
[processing.params]
glitch_samples = "@readout.glitch_samples"
pretrigger_samples = "@readout.pretrigger_samples"
amps_per_adc = 1.0                             # PLACEHOLDER: current_max is in ADC counts until the ADC-to-amps scale is known

[[processing]]
algorithm = "max_time"
channels = "role:phonon"
[processing.params]
sample_period_s = "@readout.sample_period_s"
```

```python
from goldpan.dataset import Dataset

ds = Dataset.open("goldsluice/examples/r76-registry.dataset.toml")
ev = next(ds.iter_events(processed=False))     # the pulses of the first raw dump, as one Events
```

For the Run 76 series `07221203_2025` this is the first of 30 raw files, 1,517 events and six phonon channels (`Side2pA` to `Side2pF`). `ev.trace("Side2pC")` is an array with one row per event and one column per sample (4096 samples of 0.8 us). A simple analysis of it: subtract each event's baseline (the mean of the samples before the trigger, skipping the first ten, which can carry a glitch), take the largest value above it, and histogram that over the events or overlay the largest pulses against `ev.time_axis()`.

```python
cfg = ev.detector.readout.segments[0].config
trace = ev.trace("Side2pC")
baseline = trace[:, cfg.glitch_samples:cfg.pretrigger_samples].mean(axis=1)
peak = (trace - baseline[:, None])[:, cfg.glitch_samples:].max(axis=1)
```

In the first dump the median peak of `Side2pC` is 6 ADC counts and the largest is 411. **Reading the traces is the slow part, and it is not cached.** `iter_events` reads the raw dump from disk every time you call it: about 3 seconds for this one dump, and `ds.read()` would do the same for all 30 dumps (82,000 events) and hold six 4096-sample traces for each event in memory. Only the processed quantities are cached (see below). So read the traces of one dump, or of a few events, to look at pulses, and leave the pass over all the data to `goldsluice`.

## Processing the downloaded data with `goldsluice` and reading it back in `goldpan`

`goldsluice` reads the same dataset definition file, runs its `[[processing]]` steps over every raw dump and writes the results outside the repository (`~/goldsluice-output/`). Here the steps are `peak` (the largest value above the baseline, `current_max`, and the largest ADC value, `adc_max`) and `max_time` (the time of that maximum, `max_time_s`), on the six phonon channels. It is run from a terminal, in `goldsluice/examples/`; reading the raw dumps takes a couple of minutes and is most of the time.

```
python -m goldsluice check r76-registry.dataset.toml    # lists the raw files and the steps, reads nothing
python -m goldsluice run r76-registry.dataset.toml      # processes every dump
```

The output is a `goldpan` Parquet dataset, one file per dump (`output_format = "root"` in the definition gives ROOT files in the layout of the collaboration's RQ files instead). Reading it back needs no raw data:

```python
q = ds.processed()                          # the processed quantities of all dumps, no pulses: small and fast
q.quantities["Side2pC"]["current_max"]      # a record per channel, a field per quantity
```

This is 81,992 events with three quantities for each of the six channels. `current_max` is still in ADC counts because the conversion to amps (`amps_per_adc`) is a placeholder equal to 1 until the scale is known. For the RQ-file layout, `goldpan.rqdata.load` reads the quantities as numpy arrays and keeps what it read in a cache (`~/.cache/goldpan/rqdata`), so the second read of the same files takes a tenth of a second instead of four.

## Cached reading of the quantities (under development)

There is a second way to read the quantities, `goldpan.rqdata.load`, which reads RQ files (the format of the collaboration's processed files) as numpy arrays and keeps what it read in a cache, `~/.cache/goldpan/rqdata`. `goldsluice` can write its quantities as such files (`output_format = "root"` in the definition), or `goldpan.adapters.rq_root.write` can write the Parquet quantities of the previous section as RQ files, one per dump with a branch `<channel>_<quantity>` for each. The quantities are chosen with patterns, where `P*` stands for the six sensors:

```python
from goldpan import rqdata

RQS = ["P*_adc_max", "P*_current_max", "P*_max_time_s"]
where = dict(detector=N, files=str(RQ_DIR / "{series}_F*.root"), phonon_channels=sensors, all_files=True)

data = rqdata.load("07221203_2025", RQS, **where)     # first time: reads the 30 files
data = rqdata.load("07221203_2025", RQS, **where)     # second time: from the cache
data["Side2pA_current_max"]                           # a numpy array, one number per event
```

For the 30 files (81,992 events, 18 branches) the first read took 4.0 seconds and the second 0.1 seconds. Asking for fewer quantities than a cached read has (`["P*_current_max"]`) is also served from the cache, and a file that is rewritten is read again, never served stale. `rqdata.cache_info()` lists the entries (here 2 entries, 37 MB) and `rqdata.cache_clear()` removes them.

This is not the same reader as `Dataset` and `ds.processed()`: it returns flat arrays and not an `Events`, it takes patterns for the quantities, which the other reader does not, and it reads ROOT files only. Whether there should be two ways of reading, and where the cache belongs, is an open question for the development ([issue 177](https://github.com/villano-lab/NSDF-Data/issues/177)). The raw traces are not cached by either.

