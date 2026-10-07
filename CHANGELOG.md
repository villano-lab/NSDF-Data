# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [semantic versioning](https://semver.org/) (see `RELEASING.md`).

## [Unreleased]

First release (0.1.0). It gathers the state of the repository when semantic versioning and Git Flow began, on 2026-10-07.

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

- Student guides are at setup version 7 and first-analysis version 6: direct Miniforge download links, installer options spelled out, plain-language explanations of each command, Command Prompt before the Miniforge Prompt on Windows, `jupyterlab` installed, and the data downloaded from the home folder.

### Removed

- `environment.yml` (replaced by `requirements.txt`; the guides use explicit install commands).

### Fixed

- The pinned `nsdf-dark-matter-cli` version: 0.3.1 does not exist on PyPI; 0.5.0 is the working version.
