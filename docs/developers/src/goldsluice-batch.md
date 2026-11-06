---
title-meta: "Developer quick-sheet: batch mode"
author-meta: "NSDF-Data maintainers"
html-title: "Batch mode: define a dataset, process it, read it back"
html-subtitle: "Developer quick-sheet · goldsluice and goldpan share one dataset file · version 2, 6 November 2026"
---

```{=latex}
\setlength{\parskip}{0.3em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.05}
\vspace*{-1.2em}
\begin{center}
{\LARGE\bfseries\color{brand} Batch mode: define a dataset, process it, read it back}\\[0.2em]
{\small Developer quick-sheet \textperiodcentered{} goldsluice and goldpan share one dataset file \textperiodcentered{} version 2, 6 November 2026}
\end{center}
\vspace{0.2em}
\small
```

**The full guide is now part of the goldsluice documentation: <https://villano-lab.github.io/goldsluice/guides/batch.html>.** It has the whole definition file, every option, the messages and what to do about them. This sheet is the overview.

A **dataset definition** is one small text file that says *which raw files*, *how to read them* and *which processing to run*. `goldsluice` runs it over every raw file in one command and writes the results next to it; `goldpan` opens the same file and gives you the pulses together with the processed quantities. Nothing is assumed: the readout, the channels and every parameter are written in the file.

## The loop

1. Write `<name>.dataset.toml`: the `[dataset]` name and output folder, one or more `[[sources]]` (format, files, detector, readout) and the `[[processing]]` steps in order.
2. Check and run it:

```
python -m goldsluice algorithms
python -m goldsluice check r76.dataset.toml
python -m goldsluice run r76.dataset.toml
```

3. Read it back in a notebook:

```python
from goldpan.dataset import Dataset

ds = Dataset.open("r76.dataset.toml")
ev = ds.read()         # the pulses with the processed quantities
q = ds.processed()     # only the quantities: small and fast
```

## What to remember

- **Results do not belong in the repository.** Write them outside it (`~/goldsluice-output/`, or set `GOLDSLUICE_OUTPUT`); `check` and `run` refuse a folder that Git would track.
- **Unknown keys are errors**, so a typo fails at once.
- A raw file is processed again only when it, its reading, its readout or its steps change.
- Steps can build on each other (a filter, then `peak` on its result), several sources can share one file, run metadata (high voltage, trigger setting) is joined when the data are read, and the quantities can be written as ROOT files.

## Where things are

| You want | Go to |
|---|---|
| the guide | <https://villano-lab.github.io/goldsluice/guides/batch.html> |
| the file format, as a specification | the docstring of `goldpan.dataset`, <https://villano-lab.github.io/goldpan/reference/generated/goldpan.dataset.html> |
| example definitions | `examples/` in <https://github.com/villano-lab/goldsluice> |
| a new algorithm to name in a step | the sheet *Running goldsluice and developing an algorithm* |

```{=latex}
\normalsize
```
