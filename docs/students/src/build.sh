#!/bin/sh
# Rebuild every student guide PDF in docs/students/ from its source.
# Run from anywhere: the script works in its own folder.
#   1. gen.py writes the Markdown for the setup and first-analysis guides
#      (one per operating system), from the text in gen.py.
#   2. pandoc turns each Markdown file into a PDF, using boxes.lua (coloured
#      Tip / Careful / Checkpoint boxes) and style.tex (headings, colours).
# Needs: python3, pandoc, and a LaTeX install with xelatex, tcolorbox and titlesec.
# Optional overrides (e.g. on Windows): PYTHON=python MAINFONT=Arial MONOFONT="Latin Modern Mono" sh build.sh
# Do not use Consolas: its hyphen copies out of the PDF as U+2010, so a pasted command fails.
set -e
cd "$(dirname "$0")"
OUT=..
"${PYTHON:-python3}" gen.py > /dev/null
for f in setup-windows setup-macos setup-linux first-analysis-windows first-analysis-macos first-analysis-linux writing-a-note publishing-a-note publishing-with-ai codespaces; do
  pandoc "$f.md" -o "$OUT/$f.pdf" --pdf-engine=xelatex --lua-filter=boxes.lua -H style.tex \
    -V geometry:margin=0.9in -V fontsize=11pt -V mainfont="${MAINFONT:-Helvetica}" -V monofont="${MONOFONT:-Menlo}" \
    -V colorlinks=true -V linkcolor=brand -V urlcolor=brand --highlight-style=tango
  echo "built $f.pdf"
done
# The one-page note cheat-sheet: its figure is drawn by make_cheatsheet_figure.py (needs matplotlib),
# and it uses tighter margins than the guides.
"${PYTHON:-python3}" make_cheatsheet_figure.py
pandoc note-cheatsheet.md -o "$OUT/note-cheatsheet.pdf" --pdf-engine=xelatex -H style.tex \
  -V geometry:margin=0.6in -V fontsize=11pt -V mainfont="${MAINFONT:-Helvetica}" -V monofont="${MONOFONT:-Menlo}" \
  -V colorlinks=true -V linkcolor=brand -V urlcolor=brand --highlight-style=tango
echo "built note-cheatsheet.pdf"

# The same sources, as web pages with copy buttons. The PDF stays as a backup, linked from inside
# each page. The pages use docs/style.css, docs/guide.css and docs/guide.js; they need only pandoc.
HTML_COMMON="-s -f markdown -t html5 --template=guide-template.html --lua-filter=boxes.lua --lua-filter=htmlfix.lua --no-highlight -V root=.."
for f in setup-windows setup-macos setup-linux first-analysis-windows first-analysis-macos first-analysis-linux writing-a-note publishing-a-note publishing-with-ai codespaces; do
  pandoc "$f.md" -o "$OUT/$f.html" $HTML_COMMON --toc --toc-depth=2 -V pdf="$f.pdf"
  echo "built $f.html"
done
pandoc note-cheatsheet.md -o "$OUT/note-cheatsheet.html" $HTML_COMMON -V pdf="note-cheatsheet.pdf"
echo "built note-cheatsheet.html"
