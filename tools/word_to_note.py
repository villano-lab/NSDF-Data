#!/usr/bin/env python3
"""Turn a Word or Google Docs file (.docx) into a student note, pictures included.

    python tools/word_to_note.py my-note.docx your-note-name

What it does
  1. Converts the .docx to Markdown with pandoc (needs pandoc on the PATH).
  2. Saves every picture in the document as notes/src/img/<your-note-name>-fig1.png,
     -fig2.png, ... (numbered in the order they appear), and points the Markdown at them.
     Pictures from all notes share one folder, so the note's name is part of each file name.
  3. Writes notes/src/<your-note-name>.md. If that file already exists (you are updating a
     published note), its header block is kept as it is, so the number (id: "S3"), the date
     and the status survive; only the text and the pictures are replaced. A new note gets the
     header from notes/src/_template.md, which you then fill in.
  4. Lists formatting that did not convert (<u>, <sup>, <sub>, <span>), which the check rejects.

Run it again after every change to the Word file; it is safe to repeat.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEFTOVER = re.compile(r"<(u|sup|sub|span|font)\b", re.I)
MD_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)(\{[^}]*\})?")
HTML_IMG = re.compile(r"<img\b[^>]*>", re.I)
FIGURE = re.compile(r"<figure>\s*(!\[[^\]]*\]\([^)]*\))\s*"
                    r"(?:<figcaption[^>]*>\s*(?:<p>)?(.*?)(?:</p>)?\s*</figcaption>)?\s*</figure>", re.S)


def split_header(text):
    """Return (header block including both '---' lines, rest) or ('', text) if there is none."""
    m = re.match(r"(---\r?\n.*?\r?\n---\r?\n)(.*)", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def convert(docx, workdir):
    """pandoc .docx -> Markdown inside workdir; pictures land in workdir/media."""
    out = workdir / "out.md"
    subprocess.run(["pandoc", str(docx), "-f", "docx", "-t", "gfm", "--wrap=none",
                    "--extract-media=media", "-o", out.name],
                   cwd=workdir, check=True, capture_output=True, text=True, encoding="utf-8")
    return out.read_text(encoding="utf-8")


def relink_pictures(md, workdir, name, img_dir):
    """Copy each picture to img_dir under a unique name and rewrite the links. Returns (md, names)."""
    order = {}

    def new_name(src):
        if src not in order:
            ext = Path(src).suffix.lower() or ".png"
            order[src] = f"{name}-fig{len(order) + 1}{ext}"
        return order[src]

    def md_sub(m):
        src = m.group(2)
        if src.startswith(("http://", "https://")):
            return m.group(0)
        return f"![{m.group(1)}](img/{new_name(src)})"

    def html_sub(m):
        src = re.search(r'src="([^"]+)"', m.group(0))
        if not src or src.group(1).startswith(("http://", "https://")):
            return m.group(0)
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        return f"![{alt.group(1) if alt else ''}](img/{new_name(src.group(1))})"

    md = MD_IMG.sub(md_sub, md)
    md = HTML_IMG.sub(html_sub, md)
    # pandoc wraps a captioned picture in raw <figure> HTML, inside which Markdown is not rendered:
    # keep the picture as plain Markdown and the caption as an italic line under it
    md = FIGURE.sub(lambda m: m.group(1) + (f"\n\n*{m.group(2).strip()}*" if m.group(2) and m.group(2).strip() else ""), md)

    img_dir.mkdir(parents=True, exist_ok=True)
    for src, dst in order.items():
        shutil.copy2(workdir / src, img_dir / dst)
    for old in img_dir.glob(f"{name}-fig*"):          # pictures of an earlier version that are gone now
        if old.name not in order.values():
            old.unlink()
    return md, list(order.values())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Turn a .docx into a student note (see the module docstring).")
    ap.add_argument("docx", type=Path, help="the Word or Google Docs file, saved as .docx")
    ap.add_argument("name", help="the note's file name without .md, for example my-baseline-note")
    ap.add_argument("--notes-dir", type=Path, default=ROOT / "notes" / "src", help="default: notes/src")
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.name):
        sys.exit("The name must be lowercase letters, digits and hyphens only, for example my-baseline-note.")
    if not args.docx.is_file() or args.docx.suffix.lower() != ".docx":
        sys.exit(f"{args.docx} is not a .docx file. In Word: File, Save As, Word Document (.docx). "
                 "In Google Docs: File, Download, Microsoft Word (.docx).")
    if shutil.which("pandoc") is None:
        sys.exit("pandoc is not installed. Install it first (publishing guide, Step 1).")

    notes_dir = args.notes_dir
    note = notes_dir / f"{args.name}.md"
    if note.exists():
        header, _ = split_header(note.read_text(encoding="utf-8"))
        kept = bool(header)
    else:
        header, _ = split_header((notes_dir / "_template.md").read_text(encoding="utf-8"))
        kept = False
    if not header:
        sys.exit(f"Could not find a header block in {note if note.exists() else notes_dir / '_template.md'}.")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        md = convert(args.docx.resolve(), work)
        md, pictures = relink_pictures(md, work, args.name, notes_dir / "img")

    body = md.strip() + "\n"
    note.write_text(header.rstrip("\r\n") + "\n\n" + body, encoding="utf-8", newline="\n")

    print(f"Wrote {note.relative_to(ROOT) if note.is_relative_to(ROOT) else note}")
    print(f"  header: {'kept from the existing note' if kept else 'new, from _template.md: fill it in (title, author, date, keywords, description)'}")
    print(f"  pictures: {len(pictures)}" + (f" ({', '.join(pictures)})" if pictures else ""))
    left = sorted({m.group(1).lower() for m in LEFTOVER.finditer(body)})
    if left:
        print("  formatting that did not convert: " + ", ".join(f"<{t}>" for t in left) +
              ". Delete the tags and keep the words, or the check will reject the note.")
    print("Next: python tools/build_notes.py check")


if __name__ == "__main__":
    main()
