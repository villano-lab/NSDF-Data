# Branching, versions and releases

This repository uses **Git Flow** branching and **semantic versioning** (https://semver.org). One version number describes the whole repository: the `python/` library, the notebooks, the notes site, the student guides and the CI checks together. The guides also carry their own document versions (in their headers); those are separate and are not the repository version.

The current version is in the `VERSION` file, and its history is in `CHANGELOG.md`. A one-page summary with diagrams is on the notes site: `docs/developers/developer-workflow.pdf` (source in `docs/developers/src/`, rebuilt with `sh docs/developers/src/build.sh`).

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

## The library's own version

The library in `python/` (the `goldpan` distribution, see issue 71) has a version of its own, in `python/pyproject.toml`. It is **independent of `VERSION`**: `VERSION` marks the project as a whole (guides, notes, tooling and library together), and most of its releases do not touch the library, so the two numbers differ and that is intended. The library's version also stays meaningful if it is ever split into its own repository.

- **Semantic versioning,** starting at 0.1.0 and staying 0.x until the public functions and `PulseConfig` settle. While 0.x, raise the **minor** number (0.2.0) for anything that changes results, signatures or names, or adds a function; raise the **patch** number (0.1.1) for a fix that changes none of those. A change in a default that changes results counts as a minor change (the sample-period fix of October 2026 is the example).
- **Bump it on the `release/*` or `hotfix/*` branch, not in a feature pull request.** Every bump makes each student's `python check_environment.py` warn ("goldpan is 0.1.0, but requirements.txt wants 0.2.0") until they re-run `python -m pip install -r requirements.txt`, so batching bumps into releases keeps that to once per release. In between, the version in the file may lag behind the code.
- **Say it in the release notes.** In that release's `CHANGELOG.md` section, add the line `goldpan X.Y.Z` (state what changed in the library, as for any change) and start the section with **Students, please:** to re-run *Updating your setup* (student guide 7), Step 3, as for any environment change.
- **What counts as the library:** the modules listed in `python/pyproject.toml`. Tools, tests, `check_environment.py` and the guides are not versioned by it.
- `python/tests/test_library_install.py` checks that the version is well formed and that the list of modules matches the files.

## Making a release

1. Make sure `develop` is green (CI passing) and every finished feature is merged.
2. `git switch develop && git pull`, then `git switch -c release/X.Y.Z`.
3. On that branch:
   - set the number in `VERSION`, and, if the library changed since the last release, its own version in `python/pyproject.toml` (see "The library's own version");
   - in `CHANGELOG.md`, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and start a new empty `[Unreleased]` section;
   - rebuild any student guide PDFs whose source changed (see `AGENTS.md`) and commit sources and PDFs together;
   - **if the release changes the environment** (the Python version, a package pin in `requirements.txt`, or the library's own version in `python/pyproject.toml`), start that release's `CHANGELOG.md` section with a line beginning **Students, please:** that says what to do and points to *Updating your setup* (student guide 7), and tell the students when the release is out. Students learn about it from `python check_environment.py` (it warns when the environment differs from `requirements.txt` and the guides) and from that line;
   - only small fixes. No new features.
4. Open a pull request from `release/X.Y.Z` into `master`. The maintainer merges it (a merge commit).
5. Tag the merge commit: `git tag -a vX.Y.Z -m "Release X.Y.Z"` and `git push origin vX.Y.Z`.
6. Merge `master` back into `develop` (a pull request or a merge commit) so `develop` has the release commit and the tag's history.
7. Delete the `release/X.Y.Z` branch. The live site is unaffected, because it is served from `develop`.

## Publishing the library to PyPI

The library is published as **`goldpan`** (https://pypi.org/project/goldpan/) by the workflow `.github/workflows/publish-goldpan.yml`. It runs when a tag `goldpan-vX.Y.Z` is pushed, builds the package, installs the wheel in a clean environment and imports every module, and then uploads it. **No token is stored anywhere**: PyPI trusts the workflow (a "trusted publisher"), and the upload waits for the maintainer to approve the `pypi` environment. Run by hand (Actions, *Publish goldpan*, *Run workflow*) it is a dry run: it builds and tests and never uploads.

**One-time setup (maintainer, on the two websites):**

1. GitHub, *Settings*, *Environments*, *New environment*: name it `pypi`; under *Required reviewers* add yourself, so that every upload needs your click; under *Deployment branches and tags* allow only tags matching `goldpan-v*`.
2. PyPI, project `goldpan`, *Manage*, *Publishing*, *Add a new publisher*, GitHub: owner `villano-lab`, repository `NSDF-Data`, workflow `publish-goldpan.yml`, environment `pypi`.
3. Run the dry run once and read its log.

**Each library release.** Make the release as above, with the library's version in `python/pyproject.toml` and the line `goldpan X.Y.Z` in that release's `CHANGELOG.md` section. After the release pull request is merged into `master`:

1. Tag the merge commit with the *library* tag, which is not the project's tag `vX.Y.Z` (the two may point at the same commit): `git tag -a goldpan-vX.Y.Z -m "goldpan X.Y.Z"` and `git push origin goldpan-vX.Y.Z`.
2. The workflow's first job checks that the tag, `python/pyproject.toml` and the changelog agree (`python tools/check_goldpan_release.py goldpan-vX.Y.Z` does the same on your computer) and that the tag is on `master`.
3. Approve the *Upload to PyPI* job when GitHub asks. Check https://pypi.org/project/goldpan/ and, in a throwaway environment, `python -m pip install goldpan==X.Y.Z`.

A version on PyPI can never be replaced or reused: a bad upload can only be yanked, and fixed by a new patch version, so run the dry run first. **An AI agent never pushes a `goldpan-v*` tag.** If the library moves to its own repository, register the trusted publisher again for the new repository.

## Making a hotfix

A hotfix repairs **released code** (for example a broken library function in a tagged release). A broken guide or site page is *not* a hotfix: fix it with a feature PR into `develop`, and it is live on merge.

1. `git switch master && git pull`, then `git switch -c hotfix/X.Y.Z` (X.Y.Z is the next patch number).
2. Fix it, set `VERSION` (and the library's own version in `python/pyproject.toml` if the fix changes the library), and add the entry to `CHANGELOG.md`. Rebuild any guide PDFs whose source changed.
3. Open a pull request into `master`. The maintainer merges it, then tags `vX.Y.Z` as above.
4. Merge `master` back into `develop`.

## When the NSDF software updates

`nsdf-cli` and the `nsdf_dark_matter` library (formerly NSDF-SLAC, now **Nexus-DM**, https://github.com/nsdf-fabric/nexus-dm) are developed actively by another team, and this project depends heavily on them. We therefore **pin exact versions** in `requirements.txt` and never let a student upgrade them alone. Three numberings exist and are not the same: the CLI package version on PyPI (0.6.0), the library package version on PyPI (0.3.1), and the repository's release tags (v0.7.0). Their documentation is at https://nsdf-fabric.github.io/nexus-dm/ and their release notes at https://github.com/nsdf-fabric/nexus-dm/releases.

1. **Notice.** Run `python tools/check_upstream.py` (read-only; `--strict` exits 1 when a pinned package has a newer release). Look at it when the Nexus-DM team announces something and before each release.
2. **Read what changed.** The release notes, and the code: compare the tags on GitHub (`compare/<old>...<new>`) and note which files changed under `nsdf_dark_matter/` (the library) and `nsdf_dark_matter_cli/`. Check their open issues for anything we filed (for example the trigger-label and missing-data bugs).
3. **Test in a throwaway environment, never in yours.** `conda create -n nexus_test python=3.12 pip -y`, then `python -m pip install -r` a copy of `requirements.txt` with the new pins. Run the commands with a temporary home folder (set `USERPROFILE` and `HOME`), because the CLI now writes `~/.nexus-dm/config.json` the first time any command runs. Check: `nsdf-cli version`, `config` (and `config --output-global`, `--reset`), `ls --limit 3`, `download 07221203_2025_F0001` from a different folder, the same files and sizes as an existing download, `download ... -o`, `prune -f`, then the guide's numbers (shape (1517, 4096), 179 quiet traces, 141 randoms), `python python/check_environment.py` (it should warn about the pin you changed) and `python -m pytest -q`. Then `conda env remove -n nexus_test -y`.
4. **Bump the pins** in `requirements.txt` only, then change what quotes them: the "NSDF Dark Matter CLI: X" line of the setup guide and the Codespaces guide (a test fails until they match), the pinned-packages line of `AGENTS.md`, and any new options the guides should teach. Rebuild the guides and open a pull request: the CI check "Guide steps" repeats the setup and first analysis on Windows, macOS and Linux with the new pins.
5. **Release it** with a changelog line beginning **Students, please:** that points to *Updating your setup* (student guide 7, Step 3), as for any change of environment. Students are warned by `check_environment.py` until they reinstall.
6. **Tell the Nexus-DM team** about anything wrong that you found (an issue on their repository), and keep our own notes about their behaviour (for example the unconfirmed trigger-label assumption in `pulse_cuts.py`) in step with their answers.

## Student notes

Student notes (`notes/src/*.md`) are feature work: a student branches from `develop`, writes the note with `id: "TBD"`, and opens a pull request into `develop`.

1. The pull request runs `tools/build_notes.py check`. Nothing is published yet, and nothing is visible on the site.
2. The maintainer reviews it, gives it a note number (replacing `TBD`), and merges. **Nothing is published without a note number**: the build refuses a note whose id is still `TBD`. For a note that needs a quick release, the maintainer may allow a student to do step 2 themselves: they press **Commit suggestion** on the number the bot posted, merge their own pull request, and tell the maintainer or Kitty, who read the note afterwards. Only notes: a guide, the library or CI always waits for review.
3. The merge pushes to `develop`, which starts the student-notes workflow. It builds `docs/notes/student-<name>.html`, the images and the index row, and the bot commits them to `develop`.
4. GitHub Pages rebuilds from `develop`. The note is live about one to two minutes after the merge.

To **take a note off the site**, delete `notes/src/<name>.md` (and any picture only it used) in a pull request into `develop`. The next build removes the generated page and figures itself (`prune()` in `tools/build_notes.py`), and the front-page table is regenerated. It only ever removes files named `student-*`, and only when every remaining note validates.

### The notes bot and the pull-request rule

The rulesets `protect-develop` and `protect-master` block deletion and force-push and **require a pull request** (0 approvals, merge commits only). The bot of the *Student notes* workflow commits the generated pages straight to `develop` (or `master`), so it needs a way past that rule. GitHub does not offer GitHub Actions as a bypass actor on this repository, so the bot pushes with a **deploy key**:

1. On a computer with `ssh-keygen`, in an empty folder outside the repository: `ssh-keygen -t ed25519 -N "" -C "notes-bot" -f notes-bot`. It writes `notes-bot` (private) and `notes-bot.pub` (public).
2. Add the public key as a deploy key **with write access**: `gh repo deploy-key add notes-bot.pub --allow-write --title notes-bot` (or Settings, Deploy keys).
3. Store the private key as the Actions secret `NOTES_DEPLOY_KEY`: `gh secret set NOTES_DEPLOY_KEY < notes-bot`.
4. **Delete both files** (`notes-bot` and `notes-bot.pub`). The key lives only in GitHub.
5. In both rulesets, Bypass list, Add bypass, tick **Deploy keys** (mode Always).

The *Documentation* workflow (`.github/workflows/docs.yml`) uses the same deploy key to commit the generated Sphinx pages in `docs/api/` ("Publish the documentation") on pushes to `develop` and `master`; no other key or secret is needed.

To check it, merge a student note (or a change to `tools/build_notes.py`) and see that the *Student notes* run on `develop` ends with "Publish student notes". If the run fails with "The push was rejected", the secret or the bypass is missing. To revoke the bot's access, delete the deploy key in Settings. A lost private key cannot be recovered: repeat the steps with a new pair.

## One-time repository settings (maintainer)

- Make `develop` the default branch, so new pull requests and clones start there.
- Keep a ruleset on `master` against deletion and force-push, naming `refs/heads/master` explicitly: the existing `protect-master` ruleset targets the *default* branch, so it would move to `develop` when the default changes. Add the same protection for `develop`, but **no pull-request requirement**: the student-notes bot commits to it.
- **GitHub Pages: set the source to branch `develop`, folder `/docs`** (Settings → Pages). Do this together with making `develop` the default branch, and after the student-notes workflow change has been merged into `develop`.
