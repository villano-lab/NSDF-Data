#!/usr/bin/env python3
"""Make one web page for a guide that has a version per computer, plus small forwarding pages.

    python build_os_pages.py <base> <folder with the three .frag files> <output folder>

For a guide whose sources are <base>-windows.md, <base>-macos.md and <base>-linux.md, build.sh first turns
each into an HTML fragment (<base>-<os>.frag, with every id prefixed by the system's name so the three
versions can share a page). This script puts the three fragments into guide-os-template.html, which has the
Windows / macOS / Linux switch (docs/guide.js picks the visitor's system and remembers the choice), and writes
<output>/<base>.html. It also writes <output>/<base>-<os>.html: a tiny page that forwards the old address
(for example setup-windows.html) to <base>.html?os=<os>, so old links and bookmarks keep working.
The PDFs stay one per computer, built by build.sh from the same sources; the page links to the one for the
selected system.
"""
import re
import sys
from pathlib import Path

SYSTEMS = (("windows", "Windows"), ("macos", "macOS"), ("linux", "Linux"))
HERE = Path(__file__).resolve().parent


def main(base, frag_dir, out_dir):
    frag_dir, out_dir = Path(frag_dir), Path(out_dir)
    frags = {key: (frag_dir / f"{base}-{key}.frag").read_text(encoding="utf-8") for key, _ in SYSTEMS}

    first = frags["windows"]
    h1 = re.search(r"<h1>(.*?)</h1>", first, re.S).group(1).strip()
    meta = re.search(r'<p class="meta">(.*?)</p>', first, re.S).group(1)
    number = re.search(r"student guide (\d+)", meta).group(1)
    title = f"{h1} (NSDF-Data student guide {number})"

    page = (HERE / "guide-os-template.html").read_text(encoding="utf-8")
    page = (page.replace("@TITLE@", title)
                .replace("@BASE@", base)
                .replace("@VARIANTS@", "\n".join(frags[key] for key, _ in SYSTEMS)))
    (out_dir / f"{base}.html").write_text(page, encoding="utf-8", newline="\n")

    for key, name in SYSTEMS:
        stub = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h1} ({name} edition)</title>
<meta http-equiv="refresh" content="0; url={base}.html?os={key}">
<link rel="canonical" href="{base}.html">
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="../guide.css">
<script src="../guide.js" defer></script>
</head>
<body>
<div class="wrap note guide">
<p>This guide now has one page for all computers. <a href="{base}.html?os={key}">Open the {name} version</a>, or the <a href="{base}-{key}.pdf">PDF for {name}</a>. <a href="../index.html">&larr; All notes and guides</a></p>
</div>
</body>
</html>
"""
        (out_dir / f"{base}-{key}.html").write_text(stub, encoding="utf-8", newline="\n")
    print(f"built {base}.html (and forwarding pages for {', '.join(k for k, _ in SYSTEMS)})")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
