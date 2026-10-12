# notes/src

Student notes are written here as Markdown (`.md`) files, one note per file, and are published automatically to the notes site.

- Start from `_template.md`. Copy it to `your-note-name.md` and fill in the header.
- Pictures go directly in `img/` (no subfolders), next to the notes, and are referred to as `img/file.png`. All notes share that folder, so start each file name with your note's name (`your-note-name-fig1.png`).
- Wrote the note in Word or Google Docs? `python tools/word_to_note.py my-note.docx your-note-name` turns it into a note and saves its pictures (student guide 4, Step 1).
- Read the guide *Writing a note* (student guide 3) on the notes site before you start.
- The publishing check runs on every pull request. Fix anything it reports before asking for review.
- Leave `id: "TBD"` in your header. A reviewer gives the note its number (the next free one, for example 8) before merging. Notes have one continuous set of numbers; `python tools/build_notes.py next` prints the next free one.
