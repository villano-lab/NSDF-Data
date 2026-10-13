# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/) (see `RELEASING.md`).

## [Unreleased]

### Added

- **Note 8: the Processing.xlsx-recorded raw and RQ locations for 3 UMN R76 series no longer exist.** Reads `Processing.xlsx` from `cdms3.spa.umn.edu:/project/chocula/k100/run076` and checks the raw (`midasraw`) and processed (`midasrq`) paths it records for series `07220812_1805`, `07220830_1829` and `07220923_1746`; none exist, and the owning user's whole directory is gone. Four other UMN users' `k100proc` copies were checked and none hold these series either. In progress: Run68 and the other ~230 Run76 series are not yet covered, and a broader filename search did not finish in time.

### Changed

- **Publishing a note (version 8): a short box that says what a pull request is.** At the top of Step 3: your branch is your own copy, nothing on it changes anyone else's work or the public site, a pull request is the button that means "please have a look", and if something looks wrong, stop and send `git status`. Written for students who are new to Git.

## [0.6.0] - 2026-10-13

The student guides gain *Updating your setup* and an environment check, the note guides now suggest VS Code and fully support Word and Google Docs (with a converter that carries the pictures), all notes share one table and one set of note numbers, and the library gets a channel-name module, a generated reference page and its own CI workflow.

### Added

- **A generated library reference page, `docs/library/index.html`.** `python tools/build_library_reference.py` reads every `python/pulse_*.py` module and writes one page with each module's docstring, its classes and fields, and a table of its public functions (signature, one-line summary, expandable details, and the `done` or `under development` tag with its note). It is separate from Note 1a, which keeps its history and prose and can be updated or superseded later. The front page links to it. `python/tests/test_library_reference.py` fails when the page no longer matches the code, and `test_library_conventions.py` now also requires a docstring on every public function (the library tests run when the generator or the page changes).
- **`python/pulse_channels.py`: which physical channel is a dump's (detector, channel)?** `channel_name(0, 2)` gives `'Side1pC'`, `channel_label` adds the DCRC board and tower input for plot labels, `find_channel` goes from a name back to `(detector, channel)`, and `all_channels()` lists all 12. The dump's three "detectors" are three readout boards (DCRC1, DCRC3, DCRC4) of one two-sided detector; the table comes from the Run 76 Setup table on the UMN wiki. Tagged `under_development`: that detector 0, 1, 2 are the boards in ascending order is inferred from a raw MIDAS file of another Run 76 series, and the channel order within a board is assumed. 11 new tests (73 in all).
- **Library tests run on their own in CI, and two rules of `AGENTS.md` are now tests.** The new workflow `.github/workflows/library-tests.yml` runs `python -m pytest` in `python/` on Windows, macOS and Linux for every pull request or push that touches `python/` or `requirements.txt`, so a broken function fails a check named after the library (the guide walkthrough in `check-instructions.yml` still runs the tests as Setup Step 6). `python/tests/test_library_conventions.py` fails when a public function in a `pulse_*.py` module has no `@status` tag, or when no test file mentions it (14 new tests, 87 in all).
- **Updating your setup (new student guide 7, for Windows, macOS and Linux), a Routine maintenance box, and an environment check.** Students had no way to find out that the guides moved to a new Python or new packages. `python/check_environment.py` (stdlib only; `check()` in a notebook or `python check_environment.py` in a terminal; warning only, `--strict` for CI) compares the Python version and the pins in `requirements.txt` with what is installed and points to the new guide. The guide covers the three cases: merge the newest changes into your branch, reinstall `requirements.txt` when packages changed, and make a new environment (save a list of the old packages, `conda env remove`, then `conda create`) when Python changed. A red **Routine maintenance** box says this is regular, not one-off: on the front page (with a new column in the guides table), at the end of the setup guide (version 18), in the first-analysis guide's *Before you start* (version 18), and at the top of the new guide. The first-analysis guide's Step 4 cell now runs the check. The library has 10 new tests (62 in all; the guides now say `62 passed`; Codespaces guide version 6). `RELEASING.md` says a release that changes the environment must start with a "Students, please:" line; CI runs the check in the environment the guide builds.

### Changed

- **The SLAC documentation link was dead; `idx/` is ignored at any depth; one sentence in Updating your setup was too strong** (from Kitty Mickelson's review). `https://nsdf-fabric.github.io/nsdf-slac/` returns 404 because the project is now Nexus-DM; `README.md`, the front page and `docs/llms.txt` point to `https://nsdf-fabric.github.io/nexus-dm/`. `.gitignore` had `/idx/`, which covers only the repository root, so data downloaded from inside a subfolder (`python/idx`) would not have been ignored; it is now `idx/`. *Updating your setup* (version 4) no longer says Python "cannot be safely changed" in an existing environment: conda can, but pip-installed packages are not rebuilt, so a new environment is more reliable.
- **One table and one set of note numbers for all notes.** Student notes no longer have their own table and `S1`, `S2` numbers: `tools/build_notes.py` writes their rows into the Analysis Notes table, placed by note number among the hand-written rows (newest first), and the numbers continue the same sequence (the next note is 8). A note's `id` is now a number such as `8` (or `8a` for a follow-up), the check rejects a number a hand-written note already uses, `python tools/build_notes.py next` prints the next free number, and a generated page is titled "Note 8: ..." like the hand-written ones. Generated pages keep their `student-<name>.html` file names. Writing a note (version 14), Publishing a note (version 7), the cheat-sheet (version 4), the developer sheets, `AGENTS.md`, `RELEASING.md` and `notes/src/README.md` follow.
- **Writing a note (version 13): the pinned-link example fits the page.** In *Pinning your code* the example URL ran past the margin of the PDF; it is now `.../blob/a1b2c3d/PATH` with the notebook's path given separately.
- **Writing a note (version 12): how to make a coloured box.** The guide told students to put a correction in "a clearly labelled box" without saying how. It now shows the `::: callout` block (the site already styles it), says the VS Code preview shows the `:::` lines as plain text and the box appears only on the published page, and says a Word or Google Docs note uses a bold label instead.
- **Writing a note (version 11): the VS Code preview shortcut.** The guide said `Ctrl+Shift+V`, which replaces the text with the preview in the same tab; it now gives `Ctrl+K` then `V` (`Cmd+K` then `V` on macOS), which opens the preview in its own tab beside the text.
- **Note guides: VS Code suggested, Word and Google Docs fully supported, updating both ways.** Writing a note (version 10) now suggests writing Markdown in VS Code inside the project (with the folder layout and picture names), says plainly that Word and Google Docs are fine, and leaves the conversion to Publishing a note (version 6), which gets one path per way of writing and a *Changing a note later* with two ways. The new `tools/word_to_note.py` converts a `.docx` to a note, saves its pictures as `notes/src/img/<note>-figN.png` with the links fixed, and on a repeat run keeps the existing header (so the S-number survives). Guide 5 (version 4) uses it.
- **Note check: pictures must be directly in `notes/src/img/`.** A picture in a subfolder (for example `img/media/image1.png`, which is where `pandoc --extract-media=img` puts them) passed the check but was not copied to the site, so the note published with a broken picture. The check now rejects it with a message that says where to put the file.
- **Note guides: how to supersede a note.** Writing a note (version 9) and Publishing a note (version 5) say what to do when a note replaces another: a `Supersedes:` line in the new note, a line in the pull request description, and the older note's status and link changing in the same pull request.
- **The note status "Outdated" is now "Superseded (reference/link)".** It says what it means: a newer note has taken the place of this one, and this one stays up for reference with a link to the newer note. `tools/build_notes.py`, the status legend on the front page, the badge colour in `style.css` and the note guides (writing a note, publishing a note, the cheat-sheet and the developer note-creation sheet) use the new name; no existing note had the old one, so there is no alias. A student note whose header still says `Outdated` now fails `build_notes.py check`.
- **Updating your setup, version 3.** The merge in Step 2 is now `git merge --no-edit origin/develop`, so git no longer opens a text editor (Vim on Windows) that a student may not know how to leave; a troubleshooting row says how to leave it anyway. In Step 4 the list of old packages is saved with a full path into the home folder (`%USERPROFILE%\old-environment.txt`, or `~/old-environment.txt`), so it cannot land inside the repository and show up as a new file in `git status`; `/old-environment.txt` is also in `.gitignore`.

## [0.5.0] - 2026-10-12

The guides and CI move from Python 3.10 (end of life this month) to Python 3.12, and the setup and first-analysis guides get clearer wording, a data-structure figure and a series-name explanation.

### Changed

- **Python 3.12 instead of 3.10** (closes #43). Python 3.10 reaches end of life this month, and Anaconda stops building new 3.10 packages on its main channel after 31 October 2026. The setup guides (version 17) now create the environment with `python=3.12`; the dev container uses `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm` (Debian 12 instead of the end-of-support Debian 11); CI creates the same environment and its check now looks for `python=3.12`; the Codespaces guide (version 5), the agent brief and the AI-agents page say 3.12; `AGENTS.md` and the default path in `nsdf_r76_availability.py` are updated. The pinned packages are unchanged: tested on Windows with Python 3.12.15, `pip install -r requirements.txt` works, the 52 library tests pass, and the guide's Steps 4 to 6 give 1517 and 179. Python 3.13 is not possible yet: the pinned `openvisusnogui==2.2.138` has no 3.13 wheel for Linux. Anyone with an existing `darkmatter_cli_env` on 3.10 can keep using it, or recreate it with `conda create -n darkmatter_cli_env python=3.12 pip -y` and `python -m pip install -r requirements.txt`.
- **Front page:** the note cheat-sheet is no longer listed among student guides 3 to 6; it has its own "Quick reference" line under them.
- **Setup guides (version 16) and first-analysis guide (version 17):** the downloaded files are now described as "external data, not part of our data analysis code in the NSDF-Data repository" instead of "not part of the project".
- **First-analysis guide (version 17):** the words table explains the series name (`07` = test facility, UMN; then the start date and time), says a sample is one reading of a voltage or current and that ADC counts are the units of a sample, and splits the confusing detector/channel entry into a **Detector** row (a readout unit, all three on the same physical detector, S104) and a **Channel** row, pointing to a new **Figure 2**, a diagram of how the data is organised (series, dump, event, detector, channel, samples) and which indices the Step 4 code picks. Figures are now numbered, with bold labels. Step 1 now asks students to read Notes 2 and 2a, which use the same dump as the guide, instead of Notes 1, 1a and 2. The diagram is drawn by `make_structure_figure.py`, run by `build.sh`. The appendix "the code, line by line" now shows each line of code in its own block with a Copy button, and next to it, in red with an arrow, what it does (below it on a phone and in the PDF); `boxes.lua` and `docs/guide.css` handle the new `::: explain` block. The Windows edition's Step 7 has a tip about the `LF will be replaced by CRLF` warning that `git add` can print, saying why it appears and that it is harmless.
- **Setup guides (version 15):** in *You are done when*, the `python -m pytest -q` item now says to activate the environment (`conda activate darkmatter_cli_env`) and go to the repository's `python` folder first, as in Step 6.
- **Setup guides (version 14):** Step 4 and Step 6 now say plainly that the lines in the box are commands to run, one at a time: type (or paste) each line, press Enter, and wait for the prompt before the next. The Windows guide no longer says the 150 MB Miniforge download "can take a few minutes"; it takes less than a minute on most connections.

## [0.4.0] - 2026-10-09

Analysis files now live in one folder, `data_analysis/`, each student works in a folder of their own, and the student guides gain a line-by-line code appendix, a GitHub sign-in step and an AI-agents page.

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

[Unreleased]: https://github.com/villano-lab/NSDF-Data/compare/v0.5.0...develop
[0.5.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/villano-lab/NSDF-Data/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/villano-lab/NSDF-Data/releases/tag/v0.1.0
