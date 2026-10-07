# Student guide sources

These files are the source of the PDFs in `docs/students/`. Edit here, then rebuild.

| File | What it is |
|---|---|
| `gen.py` | Holds the text of the setup and first-analysis guides. The `OS` dictionary has the per-operating-system parts (Windows, macOS, Linux); `SETUP` and `FIRST` are the shared templates. Running it writes the six `*-<os>.md` files. |
| `setup-*.md`, `first-analysis-*.md` | Output of `gen.py`. Do not edit by hand: change `gen.py` and rerun it. |
| `writing-a-note.md`, `publishing-a-note.md`, `publishing-with-ai.md`, `codespaces.md` | Sources of student guides 3, 4, 5 and 6, edited directly. |
| `note-cheatsheet.md`, `make_cheatsheet_figure.py` | Source of the one-page note cheat-sheet (summarises guides 3 and 4), and the script that draws its figure (`img/note-path.png`, needs matplotlib). |
| `guide-template.html`, `htmlfix.lua` | The pandoc template and filter that turn every source into a web page (`docs/students/*.html`, `docs/developers/*.html`). The page styles and the copy-button script are `docs/guide.css` and `docs/guide.js`. |
| `boxes.lua` | Pandoc filter that turns `::: tip`, `::: careful` and `::: checkpoint` blocks into coloured boxes. |
| `style.tex` | LaTeX header: heading colour and spacing. |
| `build.sh` | Regenerates the Markdown and rebuilds all ten guide PDFs and the cheat-sheet, and the matching HTML pages, into `docs/students/`. |

To change a guide: edit the source, run `sh build.sh`, check the PDFs, then commit the sources and the PDFs together. Guide version numbers and dates are in each file's header and in its *Session Info* section.
