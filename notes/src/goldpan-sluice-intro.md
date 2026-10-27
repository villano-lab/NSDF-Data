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

Both links are pinned to commit `22f308d`: they show the notebooks as they were at that commit, which may be older than the latest versions, and the files may have moved since (see `data_analysis/README.md`).

## Data and setup

Say which series, dump, detector and channel you used, and define every quantity.

## The question

What are the packages `goldpan` and `goldsluice`? These are data analysis programs that are made to analyze processed data and to process pulse data respectively. `goldsluice` might take in some raw pulses and integrate them, saving the values of the integrals into a file. Those values are sometimes called Reduced Quantities (RQs) and they are in turn analyzed and/or manipulated with `goldpan` to get science results. Any generic function for fetching or manipulating data would go in these programs, rather than sitting in multiple people's analysis codes. The names were chosen with the help of AI because we want to discover something valuable in the data, one program takes a huge chunk of raw data and makes it manageable (`goldsluice`) and one sifts through very carefully for the key science (`goldpan`). 

## 