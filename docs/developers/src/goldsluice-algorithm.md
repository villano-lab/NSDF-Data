---
title-meta: "Developer quick-sheet: running goldsluice and developing an algorithm"
author-meta: "NSDF-Data maintainers"
html-title: "Running goldsluice and developing an algorithm"
html-subtitle: "Developer quick-sheet · from a Python idea to a fast Rust kernel · version 2, 6 November 2026"
---

```{=latex}
\setlength{\parskip}{0.3em}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.05}
\vspace*{-1.2em}
\begin{center}
{\LARGE\bfseries\color{brand} Running goldsluice and developing an algorithm}\\[0.2em]
{\small Developer quick-sheet \textperiodcentered{} from a Python idea to a fast Rust kernel \textperiodcentered{} version 2, 6 November 2026}
\end{center}
\vspace{0.2em}
\small
```

**The full guide is now part of the goldsluice documentation: <https://villano-lab.github.io/goldsluice/guides/algorithm.html>.** It has the setup, the worked example `max_time` with its Python and Rust code, and the traps. This sheet is the overview.

`goldsluice` is the fast half of the project: pulse-reduction kernels in **Rust**, each with a **Python mirror** that is the readable definition. You develop in Python on ordinary arrays, then port the same computation to Rust; a test makes sure the two never disagree.

## The path of an algorithm

1. **Set up once:** Rust (<https://rustup.rs>; on Windows also the Visual Studio Build Tools), then `maturin develop --release` in a clone of the goldsluice repository.
2. **Write the mirror** in Python, in the *kernel subset* (one trace in, plain loops), with its standard inputs and the inputs it must refuse. Check it in Python alone, where a mistake is cheap.
3. **Port it to Rust** line by line (`PORTING.md` of the repository has the table of equivalents) and register it.
4. **Test:** `python -m pytest tests`, `cargo test`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt`. The parity test finds the new algorithm by itself and checks that both versions agree to a relative `1e-12`, refuse the same inputs with the same message and agree with goldpan.
5. **Time it** with `goldsluice.compare` (what a user sees) and `cargo bench` (the kernel alone), and put both in the pull request with a line in the changelog.

## What to remember

- **No parameter has a default**: the readout's numbers are given by the user.
- **Always `--release`** when you time anything.
- A fix that changes what an algorithm returns raises its `REVISION` by one, so batch mode redoes only the outputs made with it.
- After a change in `src/`, run `maturin develop --release` again; a change in the mirror takes effect at once.

## Where things are

| You want | Go to |
|---|---|
| the guide with the worked example | <https://villano-lab.github.io/goldsluice/guides/algorithm.html> |
| the rules of the port | `PORTING.md` in <https://github.com/villano-lab/goldsluice> |
| running a whole dataset | the sheet *Batch mode*, or <https://villano-lab.github.io/goldsluice/guides/batch.html> |
| contributing | `CONTRIBUTING.md` and `AGENTS.md` in the goldsluice repository |

```{=latex}
\normalsize
```
