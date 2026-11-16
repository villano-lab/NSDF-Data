---
title-meta: "Developer quick-sheet: writing an adapter"
author-meta: "NSDF-Data maintainers"
html-title: "Writing an adapter"
html-subtitle: "Developer quick-sheet · for anyone who wants goldpan to read another file format · version 2, 6 November 2026"
---

```{=latex}
\setlength{\parskip}{0.3em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.05}
\vspace*{-1.2em}
\begin{center}
{\LARGE\bfseries\color{brand} Writing an adapter}\\[0.2em]
{\small Developer quick-sheet \textperiodcentered{} for anyone who wants goldpan to read another file format \textperiodcentered{} version 2, 6 November 2026}
\end{center}
\vspace{0.2em}
\small
```

**The full guide is now part of the goldpan documentation: <https://villano-lab.github.io/goldpan/guides/writing-an-adapter.html>.** It has the rules, the functions, the tests and the steps to make an adapter available, with the code. This sheet is the overview.

An **adapter** is the only code that knows a file format. It turns one storage (a MIDAS file, an idx dump, a ROOT file, a format of your own) into the objects the rest of `goldpan` works on; everything else in the library sees arrays and never a file. A new one is a small Python module, and the guide starts from a complete, tested example of about 50 lines.

## What to know before you start

- **Two shapes.** An *events adapter* reads a file with waveforms into `goldpan.data.Events`; a *table adapter* reads processed quantities into a table that `goldpan.adapters.rq.attach` joins to an `Events`.
- **The user names the detector, the channels and the readout**, and the adapter checks them against what the file knows. A silent default would change every time and energy without an error.
- **The key of an event is `series`, `dump`, `event`**, because event numbers restart in every dump.
- **Skip and count, never invent**; raise a clear error for a feature you do not read yet.
- **Test it** with `goldpan.testing.check_adapter`, then register it (`goldpan.adapters.register`) for your own use, or add it to goldpan with a pull request.

## Where things are

| You want | Go to |
|---|---|
| the guide, step by step | <https://villano-lab.github.io/goldpan/guides/writing-an-adapter.html> |
| the example adapter | `tests/example_adapter.py` in <https://github.com/villano-lab/goldpan> |
| what the existing adapters offer | the reference of the goldpan documentation, <https://villano-lab.github.io/goldpan/reference/index.html> |
| how to contribute it | `CONTRIBUTING.md` in the goldpan repository |

A new dependency of an adapter is named as an extra in goldpan and, when students need it, pinned through the `goldpan[...]` line of `requirements.txt` of this repository, with a *Students, please:* line at the next release (`RELEASING.md`).

```{=latex}
\normalsize
```
