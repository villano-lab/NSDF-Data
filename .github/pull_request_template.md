## What and why

<!-- One or two sentences: what this changes, and why. Link an issue if there is one. -->

## What changed

- [ ] Library code (`python/`)
- [ ] Notebooks (`R76/analysis_notes/`)
- [ ] Notes site or hand-written notes (`docs/`)
- [ ] Student guides (`docs/students/src/`)
- [ ] Student note (`notes/src/`)
- [ ] CI or build files (`.github/`, `tools/`)

## Checklist

Tick what applies, and say "n/a" for the rest. See `AGENTS.md` for the details of each.

- [ ] Tests pass: `cd python && python -m pytest -q`
- [ ] New or changed library functions have tests and a `@status` tag
- [ ] A new or renamed note has its row in `docs/index.html` (newest first)
- [ ] Guides: edited the **sources** (`gen.py` or the guide's `.md`), rebuilt, and committed sources **and** PDFs together
- [ ] Guides: bumped the version and date in the header and *Session Info*
- [ ] Changed package pins? Updated the guide's Step 5, `requirements.txt` and `.devcontainer/` together
- [ ] Student note: left `id: "TBD"` and ran `python tools/build_notes.py check`
- [ ] No raw data, credentials or tokens committed
- [ ] If an AI assistant helped: a `Co-Authored-By:` trailer is in the commit messages

## How I tested it

<!-- Commands you ran, the operating system, and what you saw. For guides, say which steps you followed. -->
