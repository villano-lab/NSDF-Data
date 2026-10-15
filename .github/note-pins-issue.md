This issue is kept open on purpose. Every Monday the *Note pins* workflow compares the files that the notes link to (each at an exact commit) with the files on `develop` today, and posts the report here **when the list of files that need a look has changed** since the last comment. You are assigned so that GitHub notifies you.

## What the report says

- **changed**: the file at the pinned commit is not the file today. A note marked Complete is left alone unless the change makes its result wrong (see `AGENTS.md`); a note in progress may need its numbers checked.
- **moved**: the file now lives somewhere else. The pinned link still works. Run `python tools/check_note_pins.py report --write-moves` and commit `docs/notes/pin-moves.json`, so the note page's `[latest]` link points to the new place.
- **removed**: the file is gone from the repository. The pinned link still shows it.
- **broken**: the commit or the file does not exist at the pinned link. This also fails the *Note pins* check; fix the link.

## Run it yourself, any time

The tool is a standalone Python script (`tools/check_note_pins.py`, standard library only), so you do not have to wait for Monday or for a pull request. From inside the `NSDF-Data` folder, with the full history (`git fetch origin` first, so that `develop` is current):

```
python tools/check_note_pins.py check
python tools/check_note_pins.py report --head origin/develop
```

- `check` prints `All N pinned links resolve.` or lists the links that do not (exit status 1).
- `report` prints the report above. `--head` is the commit or branch to compare with (default: the one you have checked out; `origin/develop` is what the live site is served from).
- `report --summary report.md` also appends the report to a file.
- `report --write-moves` writes `docs/notes/pin-moves.json`, the table the note pages use for moved files; `report --check-moves` only warns when that file is out of date.
- In a shallow clone (`git clone --depth 1`) the pinned commits are missing; run `git fetch --unshallow` first.

The same report is in the summary of every *Note pins* run in the Actions tab, and you can start the workflow by hand there (**Run workflow**), which also posts here if the list has changed.

Background: issue #51.
