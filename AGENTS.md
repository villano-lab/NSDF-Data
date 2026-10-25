# AGENTS.md: working in NSDF-Data

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) and for human contributors. Read this before changing anything. `CLAUDE.md` points here.

## What this repo is

Analysis of SuperCDMS-type dark-matter detector data from the NSDF archive (Run 76). It holds:

- `python/`: a small shared pulse-analysis library (flat modules, no package). Start with `python/README.md`.
- `data_analysis/`: **all data analysis lives here, and nowhere else** (notebooks, series lists, figures, archives, student work). `data_analysis/R76/notebooks/` holds the exploratory notebooks (kernel `darkmatter_cli_env`), `R76/student/` the students' notebooks (one folder per student, for example `student/tony/`), `R76/series_lists/` the run logs, `archives/` the HDF5 files, `legacy/` old work. See `data_analysis/README.md`. Expect this folder to move to its own repository later, so it may use the library in `python/` but nothing in the library may depend on it.
- `docs/`: the GitHub Pages site (https://villano-lab.github.io/NSDF-Data/), plain hand-written HTML with no build step: `docs/index.html`, `docs/notes/note-NN-*.html`, `docs/notes/img/`, `docs/style.css`.
- `docs/students/`: the student guide PDFs, built from sources in `docs/students/src/`.
- `notes/src/`, `tools/build_notes.py` and `tools/word_to_note.py`: student notes written in Markdown and published by a GitHub Action (`word_to_note.py` turns a Word or Google Docs `.docx` into a note and its pictures; pictures live directly in `notes/src/img/`, named `<note>-figN.png`).

The maintainer is Anthony Villano (@villaa).

## Before you change anything

1. `git status` and `git log --oneline -3`. Pull first. Confirm the tree is clean and in sync, and that you are on a `feature/*` branch made from an up-to-date `develop`.
2. Run the tests: `cd python && python -m pytest -q` (62 or more should pass).
3. Run `git status` again before any `checkout`, `reset` or `clean`. Two notebooks (`07221203_2025_dump1_bstd_time.ipynb`, `good_pulses_overlay.ipynb`) often show as modified after re-execution; check whether the source really changed before committing.
4. **One working copy per session.** More than one session (or person) can be working on this project at the same time, often in the same folder. Two of them editing one working copy overwrite each other: a rebuild such as `build.sh` or `gen.py` rewrites many files, `git add -A` commits the other's half-finished edits, and a `git switch` changes the files under them. So: if `git status` shows changes you did not make, or another session may be using this folder, stop and do not touch them. Do your work in your own Git worktree instead, `git worktree add ../NSDF-Data-<task> -b feature/<name> origin/develop` (it is a second working copy of the same repository, on its own branch), and remove it when you are done (`git worktree remove ../NSDF-Data-<task>`). Commit only the files you changed.

## Git rules

The repository uses **Git Flow** and **semantic versioning**. The full procedure is in `RELEASING.md` (a one-page summary with diagrams: `docs/developers/developer-workflow.pdf`); the rules an agent must follow are:

- **Branches:** `master` holds released code only (every commit is tagged `vX.Y.Z`). `develop` is the integration branch, **and the live site and guide PDFs are served from `develop`**, so a merged change there is live in about two minutes. Work happens on `feature/<name>` branches **from `develop`**, which open pull requests **into `develop`**. A student's own branch, `student-<name>` (made from `develop` in the setup guide), counts as a feature branch: students open their note PRs from it into `develop`. It lives long and carries many notes, so merge `develop` into it from time to time (ask first before touching a student's branch). Releases use `release/X.Y.Z` and urgent fixes use `hotfix/X.Y.Z`; both target `master`.
- **Never commit directly to `master` or `develop`.** This applies to the maintainer too. Make a branch and open a pull request.
- **Reviews:** how to review a PR, step by step: `docs/developers/reviewing-a-pr.pdf`. GitHub automatically requests the maintainer (@villaa) on PRs that other people open (`.github/CODEOWNERS`). Anyone else, such as Kitty Mickelson (@nuclearGoblin), is added by hand under **Reviewers** when their review is wanted. Contributors do not merge their own PR. The maintainer may merge their own PRs. Feature PRs into `develop` may also be merged by Kitty Mickelson after review by someone else; release and hotfix PRs into `master` are merged only by the maintainer. **An agent never merges a PR without the maintainer's explicit go-ahead**, even if every check is green.
- Use merge commits (not squash or rebase) to finish a branch.
- Never force-push. `master` is protected against deletion and non-fast-forward pushes. Delete only branches you created, and only after they are merged.
- **Add an entry under `[Unreleased]` in `CHANGELOG.md`** for any change a user or student would notice. Only a `release/*` or `hotfix/*` branch changes `VERSION`, the library's own version in `python/pyproject.toml` (independent of `VERSION`; rules in `RELEASING.md`, "The library's own version"), or renames `[Unreleased]`.
- Student notes (`notes/src/**`), `tools/build_notes.py`, `tools/word_to_note.py` and the student-notes workflow always go through a PR into `develop`. A note goes live about two minutes after the maintainer gives it a note number and merges it; nothing is published before that.
- Write commit messages that say what changed and why. If an AI assistant helped, add a `Co-Authored-By:` trailer naming it.
- Never commit raw data, credentials or tokens.

## If you change X, also update Y

| You change | Also do |
|---|---|
| A function in `python/` (add, rename, remove) | Add or update tests in `python/tests/`. Tag it `@status(DONE)` or `@status(UNDER_DEVELOPMENT, note=...)`. The library reference page `docs/library/index.html` is generated, never hand-edited: after adding, renaming, removing or re-documenting a function run `python tools/build_library_reference.py` and commit the page (a test fails if it is stale). Note 1a is a hand-written note and is not regenerated. A **breaking** change (rename/removal) means updating the notebooks that use it, or marking them deprecated (see "Notebooks and deprecation" on `docs/index.html`). Additive changes need no notebook edits. |
| A hand-written note page `docs/notes/note-NN-*.html` (live as soon as it is merged into `develop`; quick-sheets: `docs/developers/note-creation.pdf`, and `note-creation-ai.pdf` for an agent) | Keep exactly one row for it in `docs/index.html`, newest note number first. Notes marked **Complete** are left alone, apart from a minimal correction when a library rename makes them wrong. New or In-progress notes get an `id` on each `<h2>` and a `<nav class="outline">`. Pin notebooks and `python/` to the exact commit sha that produced the results; every pinned link must resolve (`python tools/check_note_pins.py check`). Every note page loads `../notes-pins.js` (it adds the small "latest" link after each pinned link): a page without that line is missing it, and it is the only mechanical edit allowed on a Complete note. |
| A student guide (`docs/students/src/`) | Edit **only the sources**: `gen.py` for the setup, first-analysis, updating and Git-in-VS-Code guides (it writes the twelve per-OS `.md` files, so never edit those by hand), or the guide's own `.md` for the others. Never edit the generated `.html` pages or PDFs. Rebuild (below), commit sources **and** the rebuilt HTML pages and PDFs together, and bump the version and date in the guide's header and its *Session Info*. The front page links only to the HTML pages; each page links to its PDF. |
| A file or folder that a note links to (moving, renaming or removing it) | Notes link to files at exact commits, so the pinned links keep working. After the change, run `python tools/check_note_pins.py report --write-moves` and commit `docs/notes/pin-moves.json`: the note pages use it to point their small "latest" link at the file's new place. CI ("Note pins") warns when it is out of date. `python tools/check_note_pins.py report` lists which pinned files have changed since each note, which is the list to review before a note marked Complete is left as it is. |
| `requirements.txt`, package pins, or the Python version | For the NSDF packages (`nsdf-dark-matter`, `nsdf-dark-matter-cli`) follow **RELEASING.md, "When the NSDF software updates"**: run `python tools/check_upstream.py`, test the new version in a throwaway environment first, and change the version quoted by the setup and Codespaces guides (a test checks them against `requirements.txt`). Setup Step 5, `.devcontainer/devcontainer.json` and the CI step "Setup Step 5" all install with `pip install -r requirements.txt`, so change versions only in `requirements.txt`. The Python version (3.12) is written in the `conda create` lines of the setup guide and of *Updating your setup* (`gen.py`), in `.devcontainer/devcontainer.json` (image tag), in the CI workflow, and as `EXPECTED_PYTHON` in `python/check_environment.py` (a test checks that one against `gen.py`); keep those in step. A release that changes the environment also needs the "Students, please:" line described in `RELEASING.md`. |
| `.github/workflows/*` | Test on a branch (a push runs the workflow). Keep it working on Windows, macOS and Linux if it checks the guides. |
| A student note (`notes/src/*.md`) | PR into `develop`. Leave `id: "TBD"`; the maintainer assigns the note number (one continuous set with the hand-written notes; `python tools/build_notes.py next` prints the next free one). On the pull request the *Student notes* workflow posts a review comment on the `id: "TBD"` line with the next free number as a suggestion (`tools/suggest_note_number.py`): the reviewer presses **Commit suggestion** and merges, with no checkout. Run `python tools/check_note.py notes/src/<note>.md` before asking for review. It runs the structure check (`build_notes.py check`), the pinned-link check (`check_note_pins.py check`) and the number check (`check_note_numbers.py`, which lists the numbers in the text that are not in the notebook's saved output) and shows only what concerns that note. The first two fail it; the number check is an aid for the author and reviewer, not a gate, unless you pass `--strict`. When you add a check for notes, add it to `check_note.py` so students and CI get it without changing the guides. It goes live once the maintainer merges it (about 2 to 3 minutes). To remove a note, delete its source in a PR; the build prunes the generated page. |
| Anything a user or student would notice | A line under `[Unreleased]` in `CHANGELOG.md`. |

## Building the student guides and quick-sheets

Every guide and quick-sheet is built from one Markdown source into **two** files: a web page (`.html`, with a Copy button on every command, styled by `docs/guide.css` and `docs/guide.js`) and a PDF backup. `sh docs/students/src/build.sh` builds the student ones and `sh docs/developers/src/build.sh` the developer ones. The HTML needs only pandoc; the PDF also needs LaTeX. Commands are meant to be copied from the web page, so keep each command on its own line in a plain code block.

```
sh docs/students/src/build.sh
```

Needs python, pandoc, and a LaTeX install with xelatex, tcolorbox and titlesec. On Windows, set the Mac-only fonts and the Python explicitly. **Never use Consolas**: its hyphen copies out of the PDF as a look-alike character (U+2010), so a command pasted from a guide fails (the CI check "PDFs copy as plain text" catches this):

```
PYTHON=python MAINFONT=Arial MONOFONT="Latin Modern Mono" sh docs/students/src/build.sh
```

The setup, first-analysis, updating and Git-in-VS-Code guides are one web page each, with a Windows / macOS / Linux switch (`setup.html`, `first-analysis.html`, `update.html`, `git-in-vscode.html`; `docs/students/src/build_os_pages.py` assembles them, and the old per-system addresses are small forwarding pages), but still one PDF per computer.

Rebuilt PDFs are never byte-identical (pandoc stamps a date), so restore the PDFs whose source did not change (`git checkout -- <pdf>`) before committing. Every guide has a "Where to get help" section naming the project lead. Check the rebuilt pages for text running past the margin and for `?`/replacement characters (the sources must be written as UTF-8).

## Data and environment

- Raw dump data lives **outside the repo**, in `~/idx`, and any folder named `idx/` is git-ignored. `nsdf-cli download` writes an `idx` folder **in the current directory**, so always run it from the home folder, never from inside `NSDF-Data`.
- Pinned packages: Python 3.12, `nsdf-dark-matter==0.3.1`, `nsdf-dark-matter-cli==0.6.0` (the CLI and the library have different version numbers: the CLI has no 0.3.1, and the repository tags of Nexus-DM, such as v0.7.0, are a third numbering), `numpy==2.2.6`, `matplotlib==3.10.7`, plus `h5py`, `pytest`, `ipykernel` and `jupyterlab`.
- `requirements.txt` is the single list of pip packages and versions; setup Step 5 does `conda create -n darkmatter_cli_env python=3.12 pip` and then `python -m pip install -r requirements.txt`. It has no `python==` line (pip cannot install one). Do **not** use `conda create -f requirements.txt`: the NSDF packages are not on conda channels.
- Do **not** run `data_analysis/R76/notebooks/07221203_2025_dump1_noise.ipynb` without the maintainer's approval: it rewrites `data_analysis/archives/good_noise.h5`.
- The Pages site builds from `master` `/docs` in about 30 seconds. After a push to `docs/`, verify the live page (for example `curl -s -o /dev/null -w "%{http_code}"`, or compare a published PDF with `cmp`).

## Analysis pitfalls

- Notebooks and scripts must find the `python/` library by looking upward for `python/pulse_io.py` (the snippet in `python/README.md`), never with `Path.cwd().parents[N]`. A fixed depth breaks as soon as a notebook is moved. Since phase 1 of issue 71 `requirements.txt` also installs the library in place (`-e ./python[archive]`), so in an environment built from it a plain `import pulse_quantities` works anywhere and `python python/check_environment.py` warns when it is not installed. Guide 2 and the exploratory notebooks now use the plain import; keep the walk-up snippet only in a script that must run without the library installed (or that needs the repository folder for other paths, like `nsdf_r76_availability.py`).
- The phonon sample period is **0.8 us (1.25 MHz)**, so a 4096-sample trace is 3.2768 ms; it is the default of `PulseConfig`. Our code and notes used 1.6 us until 2026-10-22, which was wrong (evidence: *The sample period* in `python/README.md`). Never write `sample_period_s=1.6e-6`: `PulseConfig` warns about it.
- The channel names depend on the readout. This series is **Side-2 readout**: six sensors, all on Side 2 (`Side2pA` to `Side2pF`), DCRC4 pA (dump channel (2, 0)) is the NaI trigger input, and the other inputs are not connected. `python/pulse_channels.py` has the map (`sensor_channels()`); never hard-code names from the table's *DCRC (2-sided)* column, and never assume a `Side1p...` channel exists in this series. Our code and notes had it wrong until 2026-10-22.
- A trace's first ~10 samples can carry an electronics glitch of hundreds of counts. Skip `config.glitch_samples` (or use `pulse_operations.trim_glitch`) before any full-trace operation such as an FFT; `bstd` and `bline` already skip them.
- Event numbers restart in every dump, so they are not globally unique.
- A *segment* is a stretch of consecutive same-trigger-type events. A *run* is a whole data-taking period (for example Run 76). Do not mix the words up.
- The `randoms` / `real_triggers` cuts in `pulse_cuts.py` rest on an unconfirmed assumption that the `.csv` trigger labels are swapped. They are tagged under development for that reason.
- `nsdf-cli ls` reads a bundled, frozen manifest. Use a 1-byte ranged GET on a signed URL for a live existence check.

## Checks that run automatically

- **Student notes** (`.github/workflows/student-notes.yml`): validates `notes/src/**` on pull requests (`build_notes.py check`), writes the number check (`tools/check_note.py --only numbers`) for the notes the pull request changed to the job summary and as warnings (advice only: it never fails the pull request), and builds the pages on push to `develop` and `master`, committing them with a deploy key that bypasses the pull-request rule (`RELEASING.md`, "The notes bot and the pull-request rule").
- **Library tests** (`.github/workflows/library-tests.yml`): runs `python -m pytest` in `python/` on Windows, macOS and Linux for pull requests and pushes that touch `python/` or `requirements.txt`. It includes `test_library_conventions.py`, which fails when a public library function has no `@status` tag or is not mentioned in any test.
- **Note pins** (`.github/workflows/note-pins.yml`): on every pull request and push, and every Monday. Fails if a pinned link in a note does not resolve (the commit or the file is missing, or the link is not pinned to a commit hash); also writes a report of which pinned files have changed, moved or been removed since (in the run's summary), and warns when `docs/notes/pin-moves.json` is out of date. Every Monday it also posts the report as a comment on the standing issue "Pinned links in the notes: report" (assigned to the maintainer), but only when the list of files that need a look has changed (judged by `check_note_pins.py signature`, which ignores the notes' own status labels). The tool is a standalone script: `python tools/check_note_pins.py check` and `report` can be run at any time (the issue explains how).
- **Dev container** (`.github/workflows/devcontainer.yml`): builds the Codespaces dev container (`.devcontainer/devcontainer.json`) and checks inside it that the library imports, the environment check is OK, `nsdf-cli` runs, the kernel is registered and the library tests pass. It runs on pull requests and pushes that touch `.devcontainer/`, `requirements.txt` or `python/`, and every Monday (the base image moves).
- **Check instructions** (`.github/workflows/check-instructions.yml`): repeats the guides' setup steps on Windows, macOS and Linux. It runs on pull requests, on pushes to `develop` and `master`, and weekly.
