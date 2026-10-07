# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/) (see `RELEASING.md`).

## [Unreleased]

### Added

- `docs/developers/developer-workflow.pdf`: a one-page developer workflow (the daily pull request loop, how branches relate, releases), linked from the front page under "Developer guides". Source and figure script in `docs/developers/src/`.
- `tools/build_notes.py` removes generated student pages and figures whose note has been deleted (and figures no longer in `notes/src/img`), so deleting a note's source is enough to take it off the site. Found while removing the pipeline test note, which needed its generated files deleted by hand.

### Fixed

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

[Unreleased]: https://github.com/villano-lab/NSDF-Data/compare/v0.1.0...develop
[0.1.0]: https://github.com/villano-lab/NSDF-Data/releases/tag/v0.1.0
