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

- [`your-notebook.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/COMMIT/data_analysis/R76/student/yourname/your-notebook.ipynb) — the notebook for everything below. Pinned to `COMMIT`: the link shows the notebook as it was at that commit, which may be older than the latest version, and the file may have moved since (see `data_analysis/README.md`).

## Data and setup

Say which series, dump, detector and channel you used, and define every quantity.

## The question

What are the packages `goldpan` and `goldsluice`? These are data analysis programs that are made to analyze processed data and to process pulse data respectivley. `goldsluice` might take in some raw pulses and integrate them, saving the values of the integrals into a file. Those values are sometimes called Reduced Quantities (RQs) and they are in turn analyzed and/or manipulated with `goldpan` got get science results. Any generic function for fetching or manipulating data would go in these programs, rather than siting in multiple peoples' analysis codes. The names were chosen with the help of AI because the we want to discover something valuable in the data, one program takes a huge chunk of raw data and makes it manageable (`goldsluice`) and one sifts through very carefully for the key science (`goldpan`). 

## 