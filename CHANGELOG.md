# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/) (see `RELEASING.md`).

## [Unreleased]

### Changed

- **Each student works in a folder of their own** inside `data_analysis/R76/student/` (for example `student/tony/`). The first-analysis guide (version 16) now has students run `mkdir yourname` and `cd yourname` before `jupyter lab` and use the longer path in `git add`; the Codespaces guide (version 4), the writing-a-note guide (version 8), the note template and `data_analysis/README.md` say the same.
- **All analysis files moved into `data_analysis/`** (the top-level notebooks, `R76/` and `archives/`), with a README saying this is where analysis always goes. Notebooks are in `data_analysis/R76/notebooks/`, series lists in `R76/series_lists/`, students' notebooks in `R76/student/` (George's folder is `student/george/`), the archive in `data_analysis/archives/`, and the old top-level notebooks in `legacy/`. The setup guides (version 13) and the first-analysis guide (version 15), the Codespaces guide, the note guides, the note template, CI and `AGENTS.md` use the new paths, and a CI check fails a pull request that adds a notebook outside `data_analysis/`. Published notes still link to the old paths, pinned to a commit, so those links keep working; the notes index and the note template now say that such links show the file as of that commit, and `data_analysis/README.md` has a table from old paths to new ones. If you had notebooks open, run `git pull` and re-open them from their new folder.
- **First-analysis guide (version 14):** Steps 5 and 6 now say to use the empty cell that Jupyter adds under a cell you have just run (and **+** only if there is none). Steps 4 and 6 link to a new appendix, "the code, line by line", with a plain-language explanation of each line of the Step 4 and Step 6 code. Step 7 now starts with `git branch --show-current` and `git status`, with a checkpoint, so students get used to looking at the branch and the status when they enter a repository.
- **First-analysis guide (version 13), Step 3:** naming the notebook now says to right-click its tab (`Untitled.ipynb`), choose **Rename Notebook**, replace `Untitled` with `first-analysis-yourname`, keep `.ipynb`, and click **Rename**. The old text ("click the name at the top") describes the older Jupyter Notebook; JupyterLab has no clickable title.
- **First-analysis guide (version 12), Step 2:** the green tip now says how to check whether the data is already there: `dir %USERPROFILE%\idx` on Windows, `ls ~/idx` on macOS and Linux, which should list a folder named `07221203_2025_F0001`; an error message means there is no `idx` folder yet.
- **Setup guides (version 12), Step 8: students sign in to GitHub with `gh auth login`** (the helper `gh` is installed from conda-forge; browser sign-in over HTTPS) before they push, and a new checklist item runs `gh auth status`. Until now the guides never explained how to sign in, so the first `git push` could fail with `Password authentication is not supported` or `Invalid username or token`. Cloning stays over HTTPS, because an SSH key adds about ten beginner steps. Refs #5.
- **Setup guides (version 11), Step 5: the environment is installed from `requirements.txt`** (one command, `python -m pip install -r requirements.txt`) instead of three separate `pip install` lines, so a version changes in one place. `requirements.txt` no longer starts with a `python==3.10` line, which made `pip install -r` fail; the Python version is in the guide's `conda create` line. The dev container and the CI use the same file. Closes #4.

### Added

- **Logos on the AI agents page and an "AI Agents" collage button.** The front-page link is now a row of overlapping icons (Claude, Gemini, Perplexity, Cursor, GitHub Copilot, GitHub) with the words "AI Agents"; each assistant, coding agent and the Codespaces button on `agents.html` has its icon. Icons are vendored in `docs/img/agents/` (Simple Icons, CC0; the brands belong to their owners) and drawn as masks, so they follow dark mode. Where the open icon set has no logo (ChatGPT, Codex, Microsoft Copilot) a plain symbol stands in. The page also explains that Claude (and possibly others) show a caution notice before running a message from a link, and what to do if the text is lost at sign-in or a page will not load.
- **A page for working with an AI agent** (`docs/agents.html`, linked top right on the front page). Step 1 copies a short brief (`docs/agent-brief.txt`) that states what the project is and the rules an agent must follow (never commit to `develop` or `master`, never merge, never invent a number). Step 2 opens ChatGPT, Claude, Copilot or Perplexity with a first message that points at the brief (Gemini opens empty; paste the brief), gives the commands to start Claude Code, Codex CLI, Gemini CLI, Cursor or VS Code with Copilot in the cloned folder, and has an "Open in Codespaces" button (the Codespaces route is still being tested). Also `docs/llms.txt` (an index for agents that browse), `GEMINI.md` (points Gemini CLI at `AGENTS.md`), a README pointer, and a CI step that checks the page, the brief, their links, and that the six sites behind the buttons still answer.
- **Notebooks find the library at any depth.** The code at the top of the notebooks, the first-analysis guide (version 11), `make_trace_figure.py` and `nsdf_r76_availability.py` now look upward from where they run for `python/pulse_io.py`, instead of assuming the notebook is exactly two folders below the project root. If you start Jupyter outside the project, the first cell stops with "Start Jupyter from inside the NSDF-Data folder." This prepares moving the analysis files into `data_analysis/`.
- Small **Copy buttons on commands written inside a sentence** in the guides' web pages (the "type this" steps, the checkpoints and every item of the "You are done when" checklist), not only in code blocks. The source marks such a command with the class `cmd`; the PDF ignores it.
- The **ticks in the checklists are remembered** in the browser, per page, so they are still there after a reload (kept only in that browser, never sent anywhere).
- **First-analysis guide (version 9):** Step 7 now says to open a second terminal for the Git commands (the first is busy running Jupyter) and moves into the project folder; "Before you start" says no folder is needed yet. The "Words you will meet" table explains series length, event, sample and ADC counts better, and has a figure of a quiet trace next to one with a pulse. A new appendix, "what an event looks like", shows how one detector's four channels are organised. Step 5 points to row 1095 for a pulse. A note explains that in Run 76 one physical detector (S104) is read by three legacy electronics units of four channels each, which the data calls detectors 0, 1 and 2. The figures come from `docs/students/src/make_trace_figure.py`.
- **First-analysis guide (version 10), Step 2:** a short yellow "Navigation" box shows how to print the current folder (`cd` on Windows, `pwd` on macOS and Linux) and list its contents (`dir` / `ls`). It is a new box type, available to every guide (`::: navigate`).

### Fixed

- **Setup guides, "You are done when": two items gave no way to check them.** "Your Jupyter kernel is installed" and "You have a student- branch" now say how: `jupyter kernelspec list` lists `darkmatter_cli_env`, and `git branch` shows `* student-yourname`. The folder item now has a command too (`dir %USERPROFILE%\Research` on Windows, `ls ~/Research` on macOS and Linux). Setup guides are version 10.

## [0.3.0] - 2026-10-07

Commands in the guides can now be copied reliably (web pages with Copy buttons, and PDFs that copy clean), plus a corrected setup checkpoint.

### Added

- **Every student guide and developer sheet is now a web page with Copy buttons, and the PDF is the backup.** The 14 documents (ten guides, the student cheat-sheet and three developer sheets) are built from the same Markdown into `docs/students/*.html` and `docs/developers/*.html`, using `docs/guide.css` and `docs/guide.js`. Every command line has a Copy button, a block with several commands also has Copy all (a trailing `# comment` is left out, because Windows `cmd` does not treat `#` as a comment), a Python cell has one Copy button for the whole cell, and the AI briefs have Copy. Each page links to its PDF at the top and the bottom, and the front page links only to the pages. Works on a phone. A new check in "Check instructions" verifies that every page has its PDF, its images and no look-alike characters, and that the front page links only to existing pages.

### Fixed

- **Setup guides, Step 4: the checkpoint contradicted its commands.** The last command is `cd` into `NSDF-Data`, so a student is already inside the folder, but the checkpoint said that `dir` (or `ls`) would show `NSDF-Data` in the list. It now says the list shows the project's own folders and files (`python`, `R76`, `docs`, `README.md`). Setup guides are version 9. Reported by the maintainer while following the Windows guide; every other checkpoint in the guides was checked against its commands and is consistent.
- Guide 5 (publishing a note with an AI assistant): the numbered steps of the starting brief ran together as one paragraph; they are now a list.
- **Commands pasted from the guides failed on Windows.** The PDFs built on a Windows PC with Consolas copied `-` out as the look-alike character U+2010, so `git clone https://github.com/villano-lab/NSDF-Data.git` (and every other command with a hyphen) was not found when pasted. All guide, cheat-sheet and developer PDFs are rebuilt with Latin Modern Mono, and the "Check instructions" workflow now fails if any PDF contains such a character.

## [0.2.0] - 2026-10-07

Developer and student quick-sheets, a safer note-publishing pipeline, and guidance for updating notes.

### Added

- `docs/developers/note-creation.pdf` and `docs/developers/note-creation-ai.pdf`: two one-page developer quick-sheets, for creating a hand-written note (notebook, figures, page, index row, pinned links, PR) and for doing it with an AI agent (a starting brief, what the agent may and must never do, the checks you still do yourself). Both also cover reviewing a student note. Linked from the front page under "Developer guides". Sources and the figure script are in `docs/developers/src/`.
- `docs/students/note-cheatsheet.pdf`: a one-page student cheat-sheet, "From note to live page", that summarises and links to guides 3 and 4 (the commands, a checklist, what the PR check's messages mean). Linked from the front page. Source in `docs/students/src/`.
- `docs/developers/developer-workflow.pdf`: a one-page developer workflow (the daily pull request loop, how branches relate, releases), linked from the front page under "Developer guides". Source and figure script in `docs/developers/src/`.
- `tools/build_notes.py` removes generated student pages and figures whose note has been deleted (and figures no longer in `notes/src/img`), so deleting a note's source is enough to take it off the site. Found while removing the pipeline test note, which needed its generated files deleted by hand.

### Fixed

- Updating a published student note: guide 4 and the student cheat-sheet now say to run `git pull origin develop` first and to keep the note's S-number. A student's old branch still said `id: "TBD"`; the PR check accepts that, but the build refuses it, so the note's update could not be published and the maintainer had to catch it before merging. The developer quick-sheet "Creating a note" now covers updating a note, and warns reviewers to check for `TBD`.
- `tools/build_notes.py` now passes text to pandoc as UTF-8. On Windows it used the system code page, which garbled non-ASCII characters (an em dash, `µ`) in a note when it was built locally. The Linux build that publishes notes was not affected.

### Changed

- The "Check instructions" workflow also runs on pushes to `develop`, so every merge into the branch the site is served from is checked.

## [0.1.0] - 2026-10-07

First release. It gathers the state of the repository when semantic versioning and Git Flow began.

### Added

- `python/`: the shared pulse-analysis library (`pulse_quantities`, `pulse_cuts`, `pulse_operations`, `pulse_io`, `pulse_archive`), with `@status` tagging and a synthetic-data test suite (52 tests).
- `R76/analysis_notes/`: exploratory notebooks for series `07221203_2025` (Run 76), and `archives/` for selected event ids.
- The notes site on GitHub Pages: notes 1, 1a, 2, 2a and 3 to 7, with the index, a status legend and notebook-deprecation policy.
- Student guides (PDFs in `docs/students/`, built from `docs/students/src/`): setup and first analysis for Windows, macOS and Linux; writing a note; publishing a note; publishing with an AI assistant; working in the browser with GitHub Codespaces. A dev container for Codespaces.
- Student-notes publishing: Markdown sources in `notes/src/`, the validator and builder `tools/build_notes.py`, and a GitHub Action that checks pull requests and builds the pages.
- A "Check instructions" workflow that repeats the setup and first-analysis steps on Windows, macOS and Linux.
- `AGENTS.md` and `CLAUDE.md` (project rules for contributors and AI agents), a pull request template, `.github/CODEOWNERS`, `RELEASING.md`, and this changelog.
- `requirements.txt`, listing the pinned package versions.

### Changed

- Student guides are at setup version 8 and first-analysis version 6: direct Miniforge download links, installer options spelled out, plain-language explanations of each command, Command Prompt before the Miniforge Prompt on Windows, `jupyterlab` installed, and the data downloaded from the home folder.
- The notes site and student guides are served by GitHub Pages from `develop` (`/docs`), so guide fixes and notes are live on merge and do not wait for a release. The student-notes workflow builds on pushes to `develop` as well as `master`. Guides 1, 3, 4, 5 and 6 now say `develop` where they named `master`.
- Pull request reviews: GitHub requests only the maintainer automatically (`.github/CODEOWNERS`); other reviewers are added by hand. The maintainer may merge their own pull requests.

### Removed

- `environment.yml` (replaced by `requirements.txt`; the guides use explicit install commands).

### Fixed

- The pinned `nsdf-dark-matter-cli` version: 0.3.1 does not exist on PyPI; 0.5.0 is the working version.

[Unreleased]: https://github.com/villano-lab/NSDF-Data/compare/v0.3.0...develop
[0.3.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/villano-lab/NSDF-Data/releases/tag/v0.1.0
