"""Build student notes from notes/src/*.md into the GitHub Pages site.

    python tools/build_notes.py check    # validate only; exit 1 on any problem
    python tools/build_notes.py build    # validate, then write docs/ (HTML, images, index block)

Each note is one Markdown file with a YAML header. The header fields are
listed in REQUIRED. The output is docs/notes/student-<slug>.html, its figures
in docs/notes/img/student-<slug>/, and a table of student notes between the
markers in docs/index.html. Hand-written notes are never touched.
Run by .github/workflows/student-notes.yml.
"""
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "notes" / "src"
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"
START, END = "<!-- student-notes:start -->", "<!-- student-notes:end -->"

REQUIRED = ["id", "title", "author", "date", "status", "keywords", "description"]
STATUSES = {"In progress": "in-progress", "Complete": "complete", "Outdated": "outdated"}
FORBIDDEN_HTML = re.compile(r"<(u|sup|sub|span|font)\b", re.I)
PIN = re.compile(r"github\.com/villano-lab/NSDF-Data/(?:blob|tree)/([^/\s)]+)/")


def read_note(path):
    """Split a note into (header dict, body text). Only simple `key: "value"` lines are supported."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError("missing header block: the file must start with a line '---'")
    header = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^(\w+):\s*"(.*)"\s*$', line)
        if not km:
            raise ValueError(f"header line not in the form key: \"value\": {line!r}")
        header[km.group(1)] = km.group(2)
    return header, m.group(2)


def check_note(path, header, body, taken_ids, strict):
    problems = []
    for key in REQUIRED:
        if not header.get(key):
            problems.append(f"header field '{key}' is missing or empty")
    if header.get("status") and header["status"] not in STATUSES:
        problems.append(f"status must be one of {list(STATUSES)}, not {header['status']!r}")
    nid = header.get("id", "")
    if nid == "TBD":
        if strict:
            problems.append("id is still TBD: the reviewer assigns the S-number before merging")
    elif nid and not re.fullmatch(r"S\d+", nid):
        problems.append(f"id must look like S1, S2, or TBD, not {nid!r}")
    elif nid in taken_ids:
        problems.append(f"id {nid} is already used by another note")
    for tag in FORBIDDEN_HTML.findall(body):
        problems.append(f"raw HTML tag <{tag}> in the text: remove the formatting (see student guide 3)")
    for ref in PIN.findall(body):
        if ref == "master" or not re.fullmatch(r"[0-9a-f]{7,40}", ref):
            problems.append(f"notebook link pinned to {ref!r}, not a commit hash")
    for src in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body):
        if src.startswith("http"):
            continue
        if not (SRC / src).is_file():
            problems.append(f"picture not found: notes/src/{src}")
    if "COMMIT" in body:
        problems.append("placeholder COMMIT is still in the note: replace it with the commit hash")
    return problems


def slug_of(path):
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def to_html(body):
    out = subprocess.run(["pandoc", "-f", "markdown", "-t", "html5", "--no-highlight"],
                         input=body, capture_output=True, text=True, encoding="utf-8", check=True)
    return out.stdout


def page(header, slug, body_html):
    h2 = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html, re.S)
    outline = "\n".join(f'  <li><a href="#{i}">{t}</a></li>' for i, t in h2)
    outline_block = f"""<nav class="outline" aria-label="Outline">
<strong>Outline</strong>
<ol>
{outline}
</ol>
</nav>""" if h2 else ""
    status_class = STATUSES[header["status"]]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(header['id'])}: {html.escape(header['title'])}</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="wrap note">

<header class="site"><nav><a href="../index.html">&larr; All notes</a></nav></header>

<h1>{html.escape(header['title'])}</h1>
<p class="meta"><strong>{html.escape(header['id'])}</strong> &middot; Author(s): {html.escape(header['author'])} &middot; {html.escape(header['date'])} &middot; Status: <span class="status {status_class}">{html.escape(header['status'])}</span></p>

{outline_block}

{body_html}

<footer><a href="../index.html">&larr; All notes</a> &middot; <a href="https://github.com/villano-lab/NSDF-Data">NSDF-Data on GitHub</a></footer>

</div>
</body>
</html>
"""


def index_block(notes):
    rows = []  # one row per published note, in S-number order
    for slug, h in sorted(notes, key=lambda x: x[1]["id"]):
        rows.append(f"""    <tr>
      <td class="num">{html.escape(h['id'])}</td>
      <td class="link"><a href="notes/student-{slug}.html">Open note &rarr;</a></td>
      <td class="date">{html.escape(h['date'])}</td>
      <td>{html.escape(h['author'])}</td>
      <td>{html.escape(h['title'])}</td>
      <td class="desc">{html.escape(h['description'])}</td>
      <td class="kw">{html.escape(h['keywords'])}</td>
      <td><span class="status {STATUSES[h['status']]}">{html.escape(h['status'])}</span></td>
      <td></td>
    </tr>""")
    body = "\n".join(rows) if rows else "    <tr><td colspan=\"9\">No student notes yet.</td></tr>"
    return f"""{START}
<h2>Student notes</h2>
<p>Notes written by students, published from <code>notes/src/</code>. Each has been reviewed before it appears here.</p>
<div class="table-scroll"><table class="notes">
  <thead><tr><th>Note #</th><th>Link</th><th>Date</th><th>Author</th><th>Title</th><th>Description</th><th>Keywords</th><th>Status</th><th>Presentation</th></tr></thead>
  <tbody>
{body}
  </tbody>
</table></div>
{END}"""


def load_all(strict):
    notes, problems = [], {}
    files = sorted(p for p in SRC.glob("*.md") if not p.name.startswith("_") and p.name != "README.md")
    parsed = {}
    for p in files:
        try:
            parsed[p] = read_note(p)
        except ValueError as e:
            problems[p.name] = [str(e)]
    ids = [h.get("id") for h, _ in parsed.values() if h.get("id") not in (None, "", "TBD")]
    for p, (h, body) in parsed.items():
        others = [i for i in ids if i != h.get("id")]
        taken = set(others) | {i for i in ids if ids.count(i) > 1}
        found = check_note(p, h, body, taken, strict)
        if found:
            problems.setdefault(p.name, []).extend(found)
        if not any(e for e in problems.get(p.name, [])):
            notes.append((slug_of(p), h, body))
    return notes, problems


def build(notes):
    out_dir = DOCS / "notes"
    for slug, h, body in notes:
        body_html = to_html(body.replace("](img/", f"](img/student-{slug}/"))
        (out_dir / f"student-{slug}.html").write_text(page(h, slug, body_html), encoding="utf-8")
        img_dst = out_dir / "img" / f"student-{slug}"
        img_src = SRC / "img"
        if img_src.is_dir():
            img_dst.mkdir(parents=True, exist_ok=True)
            for f in img_src.iterdir():
                if f.is_file():
                    shutil.copy2(f, img_dst / f.name)
    text = INDEX.read_text(encoding="utf-8")
    block = index_block([(s, h) for s, h, _ in notes])
    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        text = text.replace("<footer>", block + "\n\n<footer>", 1)
    INDEX.write_text(text, encoding="utf-8")


def main(mode):
    notes, problems = load_all(strict=(mode == "build"))
    if problems:
        for name, items in problems.items():
            for item in items:
                print(f"{name}: {item}")
        print(f"{len(problems)} note(s) with problems; nothing was built.")
        return 1
    print(f"{len(notes)} note(s) valid.")
    if mode == "build":
        build(notes)
        print("docs/ updated.")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode not in ("check", "build"):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(mode))
