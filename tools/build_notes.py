"""Build student notes from notes/src/*.md into the GitHub Pages site.

    python tools/build_notes.py check    # validate only; exit 1 on any problem
    python tools/build_notes.py build    # validate, then write docs/ (HTML, images, index rows)
    python tools/build_notes.py next     # print the next free note number

Each note is one Markdown file with a YAML header. The header fields are
listed in REQUIRED. The output is docs/notes/student-<slug>.html, its figures
in docs/notes/img/student-<slug>/, and one row per note in the Analysis Notes
table of docs/index.html, marked class="generated" and placed by note number
among the hand-written rows (one continuous set of numbers: 1, 1a, 2, ... 8, ...).
Hand-written notes are never touched.
A build also removes generated pages and figures whose note is gone (see prune()), so
deleting notes/src/<name>.md is enough to take a note off the site.
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
NOTE_ID = re.compile(r"(\d+)([a-z]?)")                   # a note number: 8, or 8a for a follow-up
GENERATED_ROW = re.compile(r'[ \t]*<tr class="generated">.*?</tr>[ \t]*\n(?:[ \t]*\n)?', re.S)
HAND_ROW = re.compile(r'[ \t]*<tr>\s*<td class="num">([^<]+)</td>.*?</tr>', re.S)

REQUIRED = ["id", "title", "author", "date", "status", "keywords", "description"]
STATUSES = {"In progress": "in-progress", "Complete": "complete", "Superseded (reference/link)": "superseded"}
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
            problems.append("id is still TBD: the reviewer assigns the note number before merging")
    elif nid and not NOTE_ID.fullmatch(nid):
        problems.append(f"id must be a note number such as 8 (or 8a for a follow-up), or TBD, not {nid!r}")
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
        if not re.fullmatch(r"img/[^/]+", src):
            problems.append(f"picture {src!r} must be directly in notes/src/img/, not in a subfolder, "
                            "and linked as img/name.png (student guide 4)")
        elif not (SRC / src).is_file():
            problems.append(f"picture not found: notes/src/{src}")
    if "COMMIT" in body:
        problems.append("placeholder COMMIT is still in the note: replace it with the commit hash")
    return problems


STATUS_LINE = re.compile(r'^status:\s*"(.*)"\s*$', re.M)
REVISED_MARK = re.compile(r":::\s*callout\s*\n\s*\*\*(Revised|Revision|Correction|Update)", re.I)


def _git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def completion_dates(rel_path, root=ROOT):
    """The dates a note became Complete on the branch that is checked out: (first, revised).

    `first` is the date of the first commit on the branch (following first parents, so a merged pull request counts as
    the day of its merge) in which the note's status is Complete after it was something else. `revised` is the date of the
    last such commit if the note went back to another status and became Complete again, otherwise None. Both are None
    if the note is not Complete now, or if the history is not there (a shallow clone, or no Git)."""
    shallow = _git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None or shallow.strip() != "false":
        return None, None
    log = _git(root, "log", "--first-parent", "--reverse", "--format=%H %cs", "--", rel_path)
    if not log:
        return None, None
    dates, complete = [], False
    for line in log.splitlines():
        sha, day = line.split()
        text = _git(root, "show", f"{sha}:{rel_path}") or ""
        m = STATUS_LINE.search(text)
        now = bool(m) and m.group(1) == "Complete"
        if now and not complete:
            dates.append(day)
        complete = now
    if not complete or not dates:
        return None, None
    return dates[0], (dates[-1] if len(dates) > 1 else None)


def status_text(header):
    """The status as shown: Complete (first date), and ", revised (date)" if it was reopened and completed again."""
    text = header["status"]
    first, revised = header.get("_first"), header.get("_revised")
    if text == "Complete" and first:
        text += f" ({first})" + (f", revised ({revised})" if revised else "")
    return text


def revised_box(header, body):
    """A red box for the top of a note that was reopened and completed again, unless the author already
    put a box that starts with Revised, Revision, Correction or Update at the top of the note's text."""
    first, revised = header.get("_first"), header.get("_revised")
    if not revised or REVISED_MARK.search(body):
        return ""
    history = f"https://github.com/villano-lab/NSDF-Data/commits/develop/{header.get('_src', 'notes/src')}"
    return (f'<div class="revised-box"><strong>Revised {revised}.</strong> This note was first marked Complete on {first}, '
            f'reopened, and marked Complete again on {revised}. The author has not said what changed, in a box at the top of the '
            f'note; <a href="{history}">the history of the note\'s source file</a> shows every change.</div>')


def slug_of(path):
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def to_html(body):
    out = subprocess.run(["pandoc", "-f", "markdown", "-t", "html5", "--no-highlight", "--mathml"],
                         input=body, capture_output=True, text=True, encoding="utf-8", check=True)
    # a box that starts with Revised, Correction, Warning ... is the red box (as the automatic Revised box)
    return re.sub(r'<div class="callout">(\s*<p><strong>(?:Revised|Revision|Correction|Update|Warning|Caution))',
                  r'<div class="callout revised-box">\1', out.stdout, flags=re.I)


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
<title>Note {html.escape(header['id'])}: {html.escape(header['title'])}</title>
<link rel="stylesheet" href="../style.css">
<script src="../notes-pins.js" defer></script>
<script src="../notes-extras.js" defer></script>
</head>
<body>
<div class="wrap note">

<header class="site"><nav><a href="../index.html">&larr; All notes</a></nav></header>

<h1>{html.escape(header['title'])}</h1>
<p class="meta"><strong>Note {html.escape(header['id'])}</strong> &middot; Author(s): {html.escape(header['author'])} &middot; {html.escape(header['date'])} &middot; Status: <span class="status {status_class}">{html.escape(status_text(header))}</span></p>
{header.get('_revised_box', '')}
{outline_block}

{body_html}

<footer><a href="../index.html">&larr; All notes</a> &middot; <a href="https://github.com/villano-lab/NSDF-Data">NSDF-Data on GitHub</a></footer>

</div>
</body>
</html>
"""


def id_key(nid):
    """Sort key of a note number: 8 -> (8, ""), 2a -> (2, "a")."""
    m = NOTE_ID.fullmatch(nid)
    return (int(m.group(1)), m.group(2))


def hand_written_ids():
    """The note numbers already in the front-page table that this script did not write."""
    text = GENERATED_ROW.sub("", INDEX.read_text(encoding="utf-8"))
    return {m.group(1) for m in HAND_ROW.finditer(text)}


def index_rows(notes):
    """One table row per published note (class="generated" marks it as ours)."""
    rows = []
    for slug, h in notes:
        rows.append((h["id"], f"""    <tr class="generated">
      <td class="num">{html.escape(h['id'])}</td>
      <td class="link"><a href="notes/student-{slug}.html">Open note &rarr;</a></td>
      <td class="date">{html.escape(h['date'])}</td>
      <td>{html.escape(h['author'])}</td>
      <td>{html.escape(h['title'])}</td>
      <td class="desc">{html.escape(h['description'])}</td>
      <td class="kw">{html.escape(h['keywords'])}</td>
      <td><span class="status {STATUSES[h['status']]}">{html.escape(status_text(h))}</span></td>
    </tr>"""))
    return rows


def merge_rows(text, notes):
    """Put the generated rows into the Analysis Notes table, newest number first, among the
    hand-written rows (which keep their text). Rows from an earlier build are replaced."""
    text = GENERATED_ROW.sub("", text)
    t = text.index('<table class="notes">')
    start = text.index("<tbody>", t) + len("<tbody>")
    end = text.index("</tbody>", start)
    body = text[start:end]
    items = [(id_key(m.group(1)), m.group(0).rstrip()) for m in HAND_ROW.finditer(body)]
    items += [(id_key(nid), row) for nid, row in index_rows(notes)]
    items.sort(key=lambda it: it[0], reverse=True)
    new_body = "\n\n" + "\n\n".join(r for _, r in items) + "\n\n  " if items else "\n  "
    return text[:start] + new_body + text[end:]


def notes_src_ids():
    """The note numbers already written in notes/src, valid note or not."""
    ids = set()
    for p in SRC.glob("*.md"):
        if p.name.startswith("_") or p.name == "README.md":
            continue
        try:
            h, _ = read_note(p)
        except ValueError:
            continue
        if NOTE_ID.fullmatch(h.get("id", "")):
            ids.add(h["id"])
    return ids


def next_number():
    """The next free note number: one more than the highest in the table and in notes/src."""
    used = hand_written_ids() | notes_src_ids()
    return max(id_key(i)[0] for i in used) + 1 if used else 1


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
        taken = set(others) | {i for i in ids if ids.count(i) > 1} | hand_written_ids()
        found = check_note(p, h, body, taken, strict)
        if found:
            problems.setdefault(p.name, []).extend(found)
        if not any(e for e in problems.get(p.name, [])):
            h["_src"] = f"notes/src/{p.name}"
            notes.append((slug_of(p), h, body))
    return notes, problems


def prune(notes):
    """Delete generated student pages and figures that no longer have a note.

    Only names starting with "student-" are ever touched (hand-written notes are
    "note-NN-..."), and prune runs only after every note has validated, so one broken
    note cannot remove the others. Returns the paths removed, relative to the repo.
    """
    out_dir = DOCS / "notes"
    keep = {slug for slug, _, _ in notes}
    src_images = {f.name for f in (SRC / "img").iterdir() if f.is_file()} if (SRC / "img").is_dir() else set()
    removed = []
    for page_path in sorted(out_dir.glob("student-*.html")):
        if page_path.stem[len("student-"):] not in keep:
            page_path.unlink()
            removed.append(page_path)
    img_root = out_dir / "img"
    if img_root.is_dir():
        for folder in sorted(p for p in img_root.glob("student-*") if p.is_dir()):
            if folder.name[len("student-"):] not in keep:
                shutil.rmtree(folder)
                removed.append(folder)
            else:
                for f in sorted(folder.iterdir()):
                    if f.is_file() and f.name not in src_images:
                        f.unlink()
                        removed.append(f)
    return [p.relative_to(ROOT).as_posix() for p in removed]


def build(notes):
    out_dir = DOCS / "notes"
    for slug, h, body in notes:
        if h["status"] == "Complete":
            h["_first"], h["_revised"] = completion_dates(h["_src"])
            h["_revised_box"] = revised_box(h, body)
        body_html = to_html(body.replace("](img/", f"](img/student-{slug}/"))
        (out_dir / f"student-{slug}.html").write_text(page(h, slug, body_html), encoding="utf-8")
        img_dst = out_dir / "img" / f"student-{slug}"
        img_src = SRC / "img"
        if img_src.is_dir():
            img_dst.mkdir(parents=True, exist_ok=True)
            for f in img_src.iterdir():
                if f.is_file():
                    shutil.copy2(f, img_dst / f.name)
    text = merge_rows(INDEX.read_text(encoding="utf-8"), [(s_, h) for s_, h, _ in notes])
    INDEX.write_text(text, encoding="utf-8")
    for path in prune(notes):
        print(f"removed stale file: {path}")


def main(mode):
    if mode == "next":
        print(next_number())
        return 0
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
    if mode not in ("check", "build", "next"):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(mode))
