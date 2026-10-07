# Branching, versions and releases

This repository uses **Git Flow** branching and **semantic versioning** (https://semver.org). One version number describes the whole repository: the `python/` library, the notebooks, the notes site, the student guides and the CI checks together. The guides also carry their own document versions (in their headers); those are separate and are not the repository version.

The current version is in the `VERSION` file, and its history is in `CHANGELOG.md`.

## Branches

| Branch | Purpose | Branches from | Merges into |
|---|---|---|---|
| `master` | Released code only. Every commit on it is a release, tagged `vX.Y.Z`. | | |
| `develop` | Integration branch: the next release, in progress. **GitHub Pages serves the notes site and the student guide PDFs from `develop` (`/docs`)**, so a change to them is live as soon as it is merged here. | | |
| `feature/<short-name>` | One piece of work (a function, a note, a guide change, a CI change). | `develop` | `develop` (pull request) |
| `release/X.Y.Z` | Prepares a release: version number, changelog and last fixes only. | `develop` | `master` (pull request), then back into `develop` |
| `hotfix/X.Y.Z` | An urgent fix to what is released (a broken guide step, a broken site page). | `master` | `master` (pull request), then back into `develop` |

Student branches (`student-<name>`, from the student guides) are feature branches: they branch from `develop` and open pull requests into `develop`.

## Rules

- **Never commit directly to `master` or `develop`.** Work on a branch and open a pull request, except for the merge commits that finish a release or hotfix.
- Use **merge commits** (not squash or rebase) when finishing a feature, release or hotfix, so the branch history stays visible.
- **Reviews and who merges:** GitHub automatically requests the maintainer (@villaa) as reviewer on pull requests that other people open (see `.github/CODEOWNERS`); other reviewers are added by hand under **Reviewers**. The maintainer may merge their own pull requests. Feature pull requests into `develop` may also be merged by Kitty Mickelson (@nuclearGoblin), after review by someone other than the author. Release and hotfix pull requests into `master` are merged **only by the maintainer**. An AI agent never merges any pull request without the maintainer's explicit go-ahead.
- Never force-push to `master` or `develop`. Delete a branch only after it is merged, and only if you created it.
- Open pull requests **against `develop`**, except `release/*` and `hotfix/*`, which target `master`.
- **The site and the guides do not wait for a release.** Fix a guide, add a note or correct a page with an ordinary feature PR into `develop`; it is live about two minutes after the merge. A release only marks a version (`vX.Y.Z`).

## Choosing the next version

The version is `MAJOR.MINOR.PATCH`. While the major version is 0, the library is still changing; a breaking change then raises the minor number instead.

| Bump | When | Examples |
|---|---|---|
| **MAJOR** (X) | A breaking change to the `python/` library (a function renamed or removed, or a changed signature) or to the repository layout that existing notebooks or guides rely on. Not used while the version is 0.x. | Renaming `bstd`; moving the library into a package. |
| **MINOR** (Y) | New backwards-compatible capability. | A new library function or module; a new student guide; a new CI check; a new notes feature. While 0.x: also a breaking change. |
| **PATCH** (Z) | Fixes and content changes with no new capability. | A corrected guide step; a new or revised note; a CI fix; a typo. |

If a release contains changes of several kinds, use the highest bump.

## Making a release

1. Make sure `develop` is green (CI passing) and every finished feature is merged.
2. `git switch develop && git pull`, then `git switch -c release/X.Y.Z`.
3. On that branch:
   - set the number in `VERSION`;
   - in `CHANGELOG.md`, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and start a new empty `[Unreleased]` section;
   - rebuild any student guide PDFs whose source changed (see `AGENTS.md`) and commit sources and PDFs together;
   - only small fixes. No new features.
4. Open a pull request from `release/X.Y.Z` into `master`. The maintainer merges it (a merge commit).
5. Tag the merge commit: `git tag -a vX.Y.Z -m "Release X.Y.Z"` and `git push origin vX.Y.Z`.
6. Merge `master` back into `develop` (a pull request or a merge commit) so `develop` has the release commit and the tag's history.
7. Delete the `release/X.Y.Z` branch. The live site is unaffected, because it is served from `develop`.

## Making a hotfix

A hotfix repairs **released code** (for example a broken library function in a tagged release). A broken guide or site page is *not* a hotfix: fix it with a feature PR into `develop`, and it is live on merge.

1. `git switch master && git pull`, then `git switch -c hotfix/X.Y.Z` (X.Y.Z is the next patch number).
2. Fix it, set `VERSION`, and add the entry to `CHANGELOG.md`. Rebuild any guide PDFs whose source changed.
3. Open a pull request into `master`. The maintainer merges it, then tags `vX.Y.Z` as above.
4. Merge `master` back into `develop`.

## Student notes

Student notes (`notes/src/*.md`) are feature work: a student branches from `develop`, writes the note with `id: "TBD"`, and opens a pull request into `develop`.

1. The pull request runs `tools/build_notes.py check`. Nothing is published yet, and nothing is visible on the site.
2. The maintainer reviews it, gives it an S-number (replacing `TBD`), and merges. **Nothing is published without this approval**: the build refuses a note whose id is still `TBD`.
3. The merge pushes to `develop`, which starts the student-notes workflow. It builds `docs/notes/student-<name>.html`, the images and the index row, and the bot commits them to `develop`.
4. GitHub Pages rebuilds from `develop`. The note is live about one to two minutes after the merge.

To **take a note off the site**, delete `notes/src/<name>.md` (and any picture only it used) in a pull request into `develop`. The next build removes the generated page and figures itself (`prune()` in `tools/build_notes.py`), and the front-page table is regenerated. It only ever removes files named `student-*`, and only when every remaining note validates.

The bot commits directly to `develop`, so a ruleset on `develop` must not require pull requests (deletion and force-push blocks are fine).

## One-time repository settings (maintainer)

- Make `develop` the default branch, so new pull requests and clones start there.
- Keep a ruleset on `master` against deletion and force-push, naming `refs/heads/master` explicitly: the existing `protect-master` ruleset targets the *default* branch, so it would move to `develop` when the default changes. Add the same protection for `develop`, but **no pull-request requirement**: the student-notes bot commits to it.
- **GitHub Pages: set the source to branch `develop`, folder `/docs`** (Settings → Pages). Do this together with making `develop` the default branch, and after the student-notes workflow change has been merged into `develop`.
