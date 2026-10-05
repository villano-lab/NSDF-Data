#!/bin/sh
# Rebuild every student guide PDF in docs/students/ from its source.
# Run from anywhere: the script works in its own folder.
#   1. gen.py writes the Markdown for the setup and first-analysis guides
#      (one per operating system), from the text in gen.py.
#   2. pandoc turns each Markdown file into a PDF, using boxes.lua (coloured
#      Tip / Careful / Checkpoint boxes) and style.tex (headings, colours).
# Needs: python3, pandoc, and a LaTeX install with xelatex, tcolorbox and titlesec.
set -e
cd "$(dirname "$0")"
OUT=..
python3 gen.py > /dev/null
for f in setup-windows setup-macos setup-linux first-analysis-windows first-analysis-macos first-analysis-linux writing-a-note publishing-a-note publishing-with-ai; do
  pandoc "$f.md" -o "$OUT/$f.pdf" --pdf-engine=xelatex --lua-filter=boxes.lua -H style.tex \
    -V geometry:margin=0.9in -V fontsize=11pt -V mainfont=Helvetica -V monofont=Menlo \
    -V colorlinks=true -V linkcolor=brand -V urlcolor=brand --highlight-style=tango
  echo "built $f.pdf"
done
