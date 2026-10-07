# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/) (see `RELEASING.md`).

## [Unreleased]

### Added

- Small **Copy buttons on commands written inside a sentence** in the guides' web pages (the "type this" steps, the checkpoints and every item of the "You are done when" checklist), not only in code blocks. The source marks such a command with the class `cmd`; the PDF ignores it.
- The **ticks in the checklists are remembered** in the browser, per page, so they are still there after a reload (kept only in that browser, never sent anywhere).

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
