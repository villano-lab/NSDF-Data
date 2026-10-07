#!/bin/sh
# Rebuild the developer PDFs in docs/developers/ from their sources.
# Run from anywhere: the script works in its own folder.
#   1. make_figures.py draws the two figures into img/ (needs matplotlib).
#   2. pandoc turns developer-workflow.md into a one-page PDF, using the student guides'
#      style.tex (heading colour, tcolorbox) so the guides look alike.
# Needs: python3 with matplotlib, pandoc, and a LaTeX install with xelatex.
# Optional overrides (e.g. on Windows): PYTHON=python MAINFONT=Arial MONOFONT="Latin Modern Mono" sh build.sh
# Do not use Consolas: its hyphen copies out of the PDF as U+2010, so a pasted command fails.
set -e
cd "$(dirname "$0")"
OUT=..
"${PYTHON:-python3}" make_figures.py
"${PYTHON:-python3}" make_note_figures.py
for f in developer-workflow note-creation note-creation-ai; do
  SIZE=11pt
  pandoc "$f.md" -o "$OUT/$f.pdf" --pdf-engine=xelatex --lua-filter=../../students/src/boxes.lua -H ../../students/src/style.tex \
    -V geometry:margin=0.6in -V fontsize=$SIZE -V mainfont="${MAINFONT:-Helvetica}" -V monofont="${MONOFONT:-Menlo}" \
    -V colorlinks=true -V linkcolor=brand -V urlcolor=brand --highlight-style=tango
  echo "built $f.pdf"
done

# The same sources, as web pages with copy buttons (the PDF is linked from inside each page).
# The template, filters and styles are shared with the student guides.
S=../../students/src
for f in developer-workflow note-creation note-creation-ai; do
  pandoc "$f.md" -o "$OUT/$f.html" -s -f markdown -t html5 --template=$S/guide-template.html \
    --lua-filter=$S/boxes.lua --lua-filter=$S/htmlfix.lua --no-highlight -V root=.. -V pdf="$f.pdf"
  echo "built $f.html"
done
