# AGENTS.md: working in NSDF-Data

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) and for human contributors. Read this before changing anything. `CLAUDE.md` points here.

## What this repo is

Analysis of SuperCDMS-type dark-matter detector data from the NSDF archive (Run 76). It holds:

- `python/`: a small shared pulse-analysis library (flat modules, no package). Start with `python/README.md`.
- `R76/analysis_notes/`: exploratory Jupyter notebooks (kernel `darkmatter_cli_env`).
- `docs/`: the GitHub Pages site (https://villano-lab.github.io/NSDF-Data/), plain hand-written HTML with no build step: `docs/index.html`, `docs/notes/note-NN-*.html`, `docs/notes/img/`, `docs/style.css`.
- `docs/students/`: the student guide PDFs, built from sources in `docs/students/src/`.
- `notes/src/` and `tools/build_notes.py`: student notes written in Markdown and published by a GitHub Action.
- `archives/`: HDF5 files of selected event ids (see `archives/README.md`).

The maintainer is Anthony Villano (@villaa).

## Before you change anything

1. `git status` and `git log --oneline -3`. Pull first. Confirm the tree is clean and in sync, and that you are on a `feature/*` branch made from an up-to-date `develop`.
2. Run the tests: `cd python && python -m pytest -q` (52 or more should pass).
3. Run `git status` again before any `checkout`, `reset` or `clean`. Two notebooks (`07221203_2025_dump1_bstd_time.ipynb`, `good_pulses_overlay.ipynb`) often show as modified after re-execution; check whether the source really changed before committing.

## Git rules

The repository uses **Git Flow** and **semantic versioning**. The full procedure is in `RELEASING.md` (a one-page summary with diagrams: `docs/developers/developer-workflow.pdf`); the rules an agent must follow are:

- **Branches:** `master` holds released code only (every commit is tagged `vX.Y.Z`). `develop` is the integration branch, **and the live site and guide PDFs are served from `develop`**, so a merged change there is live in about two minutes. Work happens on `feature/<name>` branches **from `develop`**, which open pull requests **into `develop`**. Releases use `release/X.Y.Z` and urgent fixes use `hotfix/X.Y.Z`; both target `master`.
- **Never commit directly to `master` or `develop`.** This applies to the maintainer too. Make a branch and open a pull request.
- **Reviews:** GitHub automatically requests the maintainer (@villaa) on PRs that other people open (`.github/CODEOWNERS`). Anyone else, such as Kitty Mickelson (@nuclearGoblin), is added by hand under **Reviewers** when their review is wanted. Contributors do not merge their own PR. The maintainer may merge their own PRs. Feature PRs into `develop` may also be merged by Kitty Mickelson after review by someone else; release and hotfix PRs into `master` are merged only by the maintainer. **An agent never merges a PR without the maintainer's explicit go-ahead**, even if every check is green.
- Use merge commits (not squash or rebase) to finish a branch.
- Never force-push. `master` is protected against deletion and non-fast-forward pushes. Delete only branches you created, and only after they are merged.
- **Add an entry under `[Unreleased]` in `CHANGELOG.md`** for any change a user or student would notice. Only a `release/*` or `hotfix/*` branch changes `VERSION` or renames `[Unreleased]`.
- Student notes (`notes/src/**`), `tools/build_notes.py` and the student-notes workflow always go through a PR into `develop`. A note goes live about two minutes after the maintainer gives it an S-number and merges it; nothing is published before that.
- Write commit messages that say what changed and why. If an AI assistant helped, add a `Co-Authored-By:` trailer naming it.
- Never commit raw data, credentials or tokens.

## If you change X, also update Y

| You change | Also do |
|---|---|
| A function in `python/` (add, rename, remove) | Add or update tests in `python/tests/`. Tag it `@status(DONE)` or `@status(UNDER_DEVELOPMENT, note=...)`. Note 1a (the library reference) is regenerated from the library, never hand-edited. A **breaking** change (rename/removal) means updating the notebooks that use it, or marking them deprecated (see "Notebooks and deprecation" on `docs/index.html`). Additive changes need no notebook edits. |
| A hand-written note page `docs/notes/note-NN-*.html` (live as soon as it is merged into `develop`; quick-sheets: `docs/developers/note-creation.pdf`, and `note-creation-ai.pdf` for an agent) | Keep exactly one row for it in `docs/index.html`, newest note number first. Notes marked **Complete** are left alone, apart from a minimal correction when a library rename makes them wrong. New or In-progress notes get an `id` on each `<h2>` and a `<nav class="outline">`. Pin notebooks and `python/` to the exact commit sha that produced the results. |
| A student guide (`docs/students/src/`) | Edit **only the sources**: `gen.py` for the setup and first-analysis guides (it writes the six per-OS `.md` files, so never edit those by hand), or the guide's own `.md` for the others. Rebuild (below), commit sources **and** the rebuilt PDFs together, and bump the version and date in the guide's header and its *Session Info*. |
| `requirements.txt`, package pins, or the Python version | Keep the setup guide's Step 5 commands, `.devcontainer/devcontainer.json` and `.github/workflows/check-instructions.yml` in step with each other. |
| `.github/workflows/*` | Test on a branch (a push runs the workflow). Keep it working on Windows, macOS and Linux if it checks the guides. |
| A student note (`notes/src/*.md`) | PR into `develop`. Leave `id: "TBD"`; the maintainer assigns the S-number. Run `python tools/build_notes.py check` before asking for review. It goes live once the maintainer merges it (about 2 to 3 minutes). To remove a note, delete its source in a PR; the build prunes the generated page. |
| Anything a user or student would notice | A line under `[Unreleased]` in `CHANGELOG.md`. |

## Building the student guides

```
sh docs/students/src/build.sh
```

Needs python, pandoc, and a LaTeX install with xelatex, tcolorbox and titlesec. On Windows, set the Mac-only fonts and the Python explicitly:

```
PYTHON=python MAINFONT=Arial MONOFONT=Consolas sh docs/students/src/build.sh
```

Rebuilt PDFs are never byte-identical (pandoc stamps a date), so restore the PDFs whose source did not change (`git checkout -- <pdf>`) before committing. Every guide has a "Where to get help" section naming the project lead. Check the rebuilt pages for text running past the margin and for `?`/replacement characters (the sources must be written as UTF-8).

## Data and environment

- Raw dump data lives **outside the repo**, in `~/idx`, and `/idx/` is git-ignored. `nsdf-cli download` writes an `idx` folder **in the current directory**, so always run it from the home folder, never from inside `NSDF-Data`.
- Pinned packages: Python 3.10, `nsdf-dark-matter==0.3.0`, `nsdf-dark-matter-cli==0.5.0` (version 0.3.1 of the CLI does not exist on PyPI), `numpy==2.2.6`, `matplotlib==3.10.7`, plus `h5py`, `pytest`, `ipykernel` and `jupyterlab`.
- `requirements.txt` lists these, but it cannot be used as-is: `conda create -f requirements.txt` fails (the NSDF packages are not on conda channels) and `pip install -r` fails on its `python==3.10` line. The guides use explicit `conda create` and `pip install` commands instead.
- Do **not** run `R76/analysis_notes/07221203_2025_dump1_noise.ipynb` without the maintainer's approval: it rewrites `archives/good_noise.h5`.
- The Pages site builds from `master` `/docs` in about 30 seconds. After a push to `docs/`, verify the live page (for example `curl -s -o /dev/null -w "%{http_code}"`, or compare a published PDF with `cmp`).

## Analysis pitfalls

- A trace's first ~10 samples can carry an electronics glitch of hundreds of counts. Skip `config.glitch_samples` (or use `pulse_operations.trim_glitch`) before any full-trace operation such as an FFT; `bstd` and `bline` already skip them.
- Event numbers restart in every dump, so they are not globally unique.
- A *segment* is a stretch of consecutive same-trigger-type events. A *run* is a whole data-taking period (for example Run 76). Do not mix the words up.
- The `randoms` / `real_triggers` cuts in `pulse_cuts.py` rest on an unconfirmed assumption that the `.csv` trigger labels are swapped. They are tagged under development for that reason.
- `nsdf-cli ls` reads a bundled, frozen manifest. Use a 1-byte ranged GET on a signed URL for a live existence check.

## Checks that run automatically

- **Student notes** (`.github/workflows/student-notes.yml`): validates `notes/src/**` on pull requests and builds the pages on push to `master`.
- **Check instructions** (`.github/workflows/check-instructions.yml`): repeats the guides' setup steps on Windows, macOS and Linux. It runs on pull requests, on pushes to `develop` and `master`, and weekly.
