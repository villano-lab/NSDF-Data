# data_analysis/

**All data analysis in this repository lives here, and nowhere else.** Notebooks, scripts that read the data, series lists, figures made from the data, and archives of analysis results all go under this folder. The rest of the repository holds the shared library (`python/`), the guides and notes (`docs/`, `notes/`) and the tools that build them.

A CI check fails a pull request that adds a Jupyter notebook outside `data_analysis/`.

This folder is expected to move to its own, separately versioned repository one day. It may use the library in `python/`, but nothing in the library may depend on it.

## Layout

| Folder | What goes in it |
|---|---|
| `R76/notebooks/` | The exploratory notebooks and scripts for Run 76, and the small files they write. Each one is named for the series it studies, for example `07221203_2025_dump1_noise.ipynb`. |
| `R76/series_lists/` | Run logs and lists of which series exist (`DataSeriesList.xlsx`, `nsdf_r76_series.csv`, ...). |
| `R76/student/` | Students' own work. **Each student has a folder of their own**, named with their name (for example `student/tony/`), holding their notebooks such as `first-analysis-yourname.ipynb` from the student guide. The guides tell students to make it with `mkdir`. |
| `archives/` | HDF5 files that record which events a cut kept. See `archives/README.md`. Do not run the notebook that rewrites `good_noise.h5` without the project lead's approval. |
| `legacy/` | Old notebooks and notes from before the library existed. Kept for reference. Not maintained. |

A new run gets its own folder next to `R76/`, with the same three sub-folders.

## Where did a file move to?

On 9 October 2026 the analysis files were moved here. Links in published notes still work, because they point at a fixed commit, but if you look for such a file in the current repository, use this table.

| Old path | New path |
|---|---|
| `R76/analysis_notes/` (notebooks, scripts, small csv files) | `data_analysis/R76/notebooks/` |
| `R76/DataSeriesList.xlsx`, `R76/Processing.xlsx`, `R76/am_lead_series.csv`, `R76/nsdf_r76_series.csv` | `data_analysis/R76/series_lists/` |
| `R76/george/` | `data_analysis/R76/student/george/` |
| `archives/` | `data_analysis/archives/` |
| `NSDF.ipynb`, `NSDF_noise.ipynb`, `R76Noise.ipynb`, `MLmodelImplementaion.ipynb`, `Fourier Transform Analysis.ipynb`, `Optimal Filter Reference.pdf`, `Project Notes.md` (top level) | `data_analysis/legacy/` |

A link to the old path at the latest version of the repository will not work. Replace the start of the path as in the table, or open the link at the commit it names.

## Rules

1. **Put new analysis here.** Pick the folder in the table, or ask your lead.
2. **Raw data never goes in the repository.** It lives in `~/idx` (outside the repo). Run `nsdf-cli download` from your home folder, never from inside this folder.
3. **Find the library by looking upward.** Start a notebook with the snippet in `python/README.md`. It works at any depth. Never count folders with `Path.cwd().parents[N]`.
4. **Run top to bottom before you commit,** and read `git diff` first: re-running a notebook often changes its metadata.
5. **Pin your results.** A published note links to the exact commit that produced its numbers.
6. Work on a branch and open a pull request into `develop`. See `AGENTS.md` and the student guides.
