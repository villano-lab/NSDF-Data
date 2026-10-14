# Student guide sources

These files are the source of the PDFs in `docs/students/`. Edit here, then rebuild.

| File | What it is |
|---|---|
| `gen.py` | Holds the text of the setup and first-analysis guides. The `OS` dictionary has the per-operating-system parts (Windows, macOS, Linux); `SETUP`, `FIRST` and `UPDATE` are the shared templates. Running it writes the six `*-<os>.md` files. |
| `setup-*.md`, `first-analysis-*.md`, `update-*.md` | Output of `gen.py` (the setup guide, the first-analysis guide and *Updating your setup*, student guide 7). Do not edit by hand: change `gen.py` and rerun it. |
| `writing-a-note.md`, `publishing-a-note.md`, `publishing-with-ai.md`, `codespaces.md`, `git-in-five-minutes.md` | Sources of student guides 3, 4, 5, 6 and 8, edited directly. |
| `note-cheatsheet.md`, `make_cheatsheet_figure.py` | Source of the one-page note cheat-sheet (summarises guides 3 and 4), and the script that draws its figure (`img/note-path.png`, needs matplotlib). |
| `make_structure_figure.py` | Draws Figure 2 of the first-analysis guide (`img/data-structure.png`: series, dumps, events, detectors, channels, samples). Needs matplotlib; run by `build.sh`. |
| `guide-template.html`, `htmlfix.lua` | The pandoc template and filter that turn every source into a web page (`docs/students/*.html`, `docs/developers/*.html`). The page styles and the copy-button script are `docs/guide.css` and `docs/guide.js`. |
| `boxes.lua` | Pandoc filter that turns `::: tip`, `::: careful`, `::: checkpoint`, `::: navigate` and `::: maintenance` (the red "Routine maintenance" box) blocks into coloured boxes. |
| `style.tex` | LaTeX header: heading colour and spacing. |
| `build_os_pages.py`, `guide-variant-template.html`, `guide-os-template.html` | The setup, first-analysis and updating guides are one web page each (`setup.html`, `first-analysis.html`, `update.html`) with a Windows / macOS / Linux switch. `build.sh` builds each system's version as a fragment (ids prefixed by the system's name), and `build_os_pages.py` puts the three into one page and writes small forwarding pages for the old addresses (`setup-windows.html` and so on). The switch is in `docs/guide.js` and `docs/guide.css`. The PDFs stay one per computer. |
| `build.sh` | Regenerates the Markdown and rebuilds all ten guide PDFs and the cheat-sheet, and the matching HTML pages, into `docs/students/`. |

To change a guide: edit the source, run `sh build.sh`, check the PDFs, then commit the sources and the PDFs together. Guide version numbers and dates are in each file's header and in its *Session Info* section.
