#!/usr/bin/env python3
"""Check and report on the commit-pinned links in the notes (issue 51).

Every note links to notebooks and library files at an exact commit, such as
https://github.com/villano-lab/NSDF-Data/blob/322b1b8/R76/nsdf_r76_series.csv, so the numbers in a note stay tied to
the code that produced them. This tool looks at those links in the hand-written notes (docs/notes/*.html) and in the
student notes (notes/src/*.md). It needs `git` and the repository's history (in CI, `fetch-depth: 0`).

    python tools/check_note_pins.py check
        Every pinned link must resolve: the commit exists, and the file or folder exists at that commit. A link that
        is not pinned to a commit (for example .../blob/master/...) is also an error. Exit status 1 if anything is wrong.
        This is the CI check.

    python tools/check_note_pins.py signature [--head REF]
        A short fingerprint of the files that need a look, without the notes' status labels. The weekly post on the
        standing issue is made only when it changes.

    python tools/check_note_pins.py report [--head REF] [--summary FILE] [--write-moves] [--check-moves]
        The report for the maintainer: for each pinned link, whether the file is unchanged since the pin, changed
        (how many commits, and when), moved or removed. --summary appends the report to FILE (use
        $GITHUB_STEP_SUMMARY in CI). --write-moves writes docs/notes/pin-moves.json, which the note pages use to
        point the "latest" link at a file's new location. --check-moves only warns when that file is out of date.

The pages show a small "latest" link after every pinned link (docs/notes-pins.js).
Only the Python standard library is used.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'https://github\.com/villano-lab/NSDF-Data/(blob|tree)/([^/\s"\'<>)#?]+)/([^\s"\'<>)#?]*)')
HEX = re.compile(r"[0-9a-f]{7,40}")
MOVES_FILE = "docs/notes/pin-moves.json"
SKIP_MD = {"README.md", "_template.md"}
ORDER = ["broken", "removed", "moved", "changed", "current"]


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")


def slug_of(stem):
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def scan(root):
    """The pinned links of every note: a list of dicts (note, kind, ref, path), one per distinct link per note."""
    root = Path(root)
    found = []
    md_files = sorted(p for p in (root / "notes" / "src").glob("*.md") if p.name not in SKIP_MD)
    slugs = {slug_of(p.stem) for p in md_files}
    html_files = sorted((root / "docs" / "notes").glob("*.html"))
    sources = []
    for p in html_files:
        # a page built from a student note is covered by its Markdown source
        if any(p.stem.endswith("-" + s) for s in slugs):
            continue
        sources.append((p, f"docs/notes/{p.name}"))
    sources += [(p, f"notes/src/{p.name}") for p in md_files]
    for path, label in sources:
        text = path.read_text(encoding="utf-8")
        seen = set()
        for kind, ref, rel in LINK.findall(text):
            rel = unquote(rel).rstrip("/")
            if (kind, ref, rel) in seen:
                continue
            seen.add((kind, ref, rel))
            found.append({"note": label, "kind": kind, "ref": ref, "path": rel})
    return found


def object_at(root, rev, path):
    """The object id of a file or folder at a commit, or None if it is not there."""
    spec = f"{rev}:{path}" if path else f"{rev}^{{tree}}"
    r = git(root, "rev-parse", "--verify", "-q", spec)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def commit_exists(root, rev):
    return git(root, "cat-file", "-e", f"{rev}^{{commit}}").returncode == 0


def check(root):
    """The problems, as a list of messages (empty when every pinned link resolves)."""
    problems = []
    cache = {}
    for link in scan(root):
        note, ref, path = link["note"], link["ref"], link["path"]
        where = f"{note}: .../{link['kind']}/{ref}/{path}"
        if not HEX.fullmatch(ref):
            problems.append(f"{where}\n    not pinned to a commit hash ({ref!r}). Link to the commit that produced the "
                            "result, so the note keeps showing that version of the file.")
            continue
        if ref not in cache:
            cache[ref] = commit_exists(root, ref)
        if not cache[ref]:
            problems.append(f"{where}\n    the commit {ref} does not exist. Check the hash, and that the commit has been pushed.")
        elif object_at(root, ref, path) is None:
            problems.append(f"{where}\n    {path or '(root)'} does not exist at commit {ref}. Check the path.")
    return problems


def renames(root, ref, head, cache):
    """{old path: new path or None} for the files that moved or were removed between two commits."""
    if ref not in cache:
        out = {}
        r = git(root, "diff", "-M", "--name-status", ref, head)
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if parts[0].startswith("R") and len(parts) == 3:
                out[parts[1]] = parts[2]
            elif parts[0] == "D" and len(parts) == 2:
                out[parts[1]] = None
        cache[ref] = out
    return cache[ref]


def follow(root, ref, head, path):
    """Follow a file through the renames between two commits, one commit at a time (this still finds a file that
    was moved and then edited a lot, which a single comparison of the two ends misses). New path, or None."""
    r = git(root, "log", "--reverse", "-M", "--name-status", "--format=@%H", f"{ref}..{head}")
    cur = path
    for line in r.stdout.splitlines():
        if not line or line.startswith("@"):
            continue
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3 and parts[1] == cur:
            cur = parts[2]
        elif parts[0] == "D" and len(parts) == 2 and parts[1] == cur:
            return None
    return cur if cur != path and object_at(root, head, cur) is not None else None


def new_location(path, moved):
    """Where a file or folder went, from the rename table; (found, new path or None)."""
    if path in moved:
        return True, moved[path]
    prefix = path + "/"
    targets = Counter()
    for old, new in moved.items():
        if old.startswith(prefix) and new:
            tail = old[len(path):]
            if new.endswith(tail):
                targets[new[: len(new) - len(tail)]] += 1
    if targets:
        return True, targets.most_common(1)[0][0]
    return False, None


def state_of(root, link, head, rename_cache):
    ref, path = link["ref"], link["path"]
    if not HEX.fullmatch(ref) or not commit_exists(root, ref):
        return {"state": "broken", "detail": "the commit does not exist"}
    old = object_at(root, ref, path)
    if old is None:
        return {"state": "broken", "detail": "the path does not exist at that commit"}
    new = object_at(root, head, path)
    if new is not None:
        if new == old:
            return {"state": "current", "detail": "unchanged since the pin"}
        n = git(root, "rev-list", "--count", f"{ref}..{head}", "--", path).stdout.strip() or "?"
        last = git(root, "log", "-1", "--format=%cs", head, "--", path).stdout.strip()
        return {"state": "changed", "detail": f"{n} commit(s) since; last change {last}", "commits": n, "last": last}
    target = follow(root, ref, head, path) if link["kind"] == "blob" else None
    found = target is not None
    if not found:
        found, target = new_location(path, renames(root, ref, head, rename_cache))
    if found and target:
        return {"state": "moved", "detail": f"now at {target}", "target": target}
    return {"state": "removed", "detail": "no longer in the repository", "target": None}


def note_statuses(root):
    """{note page name: status text} from the rows of the notes table in docs/index.html."""
    index = Path(root) / "docs" / "index.html"
    out = {}
    if not index.is_file():
        return out
    for row in re.findall(r"<tr[^>]*>.*?</tr>", index.read_text(encoding="utf-8"), re.S):
        m = re.search(r'href="notes/([^"]+\.html)"', row)
        s = re.search(r'class="status[^"]*">([^<]+)<', row)
        if m and s:
            out[m.group(1)] = s.group(1).strip()
    return out


def build_report(root, head):
    root = Path(root)
    head_sha = git(root, "rev-parse", "--short", head).stdout.strip() or head
    statuses = note_statuses(root)
    rcache = {}
    rows = []
    for link in scan(root):
        rows.append({**link, **state_of(root, link, head, rcache)})
    counts = Counter(r["state"] for r in rows)
    notes = {r["note"] for r in rows}
    lines = ["# Pinned links in the notes", "",
             f"Compared with `{head}` ({head_sha}): {len(rows)} pinned links in {len(notes)} notes.", "",
             "| State | Links |", "|---|---|"]
    lines += [f"| {s} | {counts[s]} |" for s in ORDER if counts[s]]
    attention = [r for r in rows if r["state"] != "current"]
    lines += ["", "## Needs a look", ""]
    if not attention:
        lines += ["Nothing: every pinned file is unchanged since its pin.", ""]
    else:
        lines += ["| Note | Note status | Pinned link | State | Detail |", "|---|---|---|---|---|"]
        for r in sorted(attention, key=lambda r: (ORDER.index(r["state"]), r["note"], r["path"])):
            page = r["note"].split("/")[-1].replace(".md", ".html")
            st = statuses.get(page, "")
            lines.append(f"| {r['note']} | {st} | `{r['ref']}` {r['path'] or '(root)'} | {r['state']} | {r['detail']} |")
        lines += ["", "A note marked Complete is left alone unless a changed file makes its result wrong "
                  "(see AGENTS.md). 'moved' and 'removed' links keep working at their pinned commit; the note page "
                  "adds a link to the new location when docs/notes/pin-moves.json is up to date.", ""]
    return rows, "\n".join(lines) + "\n"


def signature(rows):
    """A short fingerprint of what needs a look: which pinned links are not current, and why.
    It leaves out the notes' own status labels, so marking a note Superseded or Complete does not look like
    a change in the files. The weekly report is posted on the standing issue only when this changes."""
    parts = sorted(f"{r['note']}|{r['ref']}|{r['path']}|{r['state']}|{r['detail']}" for r in rows if r["state"] != "current")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def moves_json(rows):
    moves = {}
    for r in rows:
        if r["state"] in ("moved", "removed"):
            moves[f"{r['ref']}/{r['path']}"] = r.get("target")
    return json.dumps(dict(sorted(moves.items())), indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(ROOT), help="the repository to look at (default: this one)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="every pinned link must resolve (the CI check)")
    sg = sub.add_parser("signature", help="print a short fingerprint of the files that need a look (used by the weekly post)")
    sg.add_argument("--head", default="HEAD", help="compare with this commit or branch (default HEAD)")
    rp = sub.add_parser("report", help="which pinned files have changed since, for the maintainer")
    rp.add_argument("--head", default="HEAD", help="compare with this commit or branch (default HEAD)")
    rp.add_argument("--summary", help="append the report to this file (GITHUB_STEP_SUMMARY in CI)")
    rp.add_argument("--write-moves", action="store_true", help=f"write {MOVES_FILE}")
    rp.add_argument("--check-moves", action="store_true", help=f"warn if {MOVES_FILE} is out of date")
    a = ap.parse_args(argv)
    root = Path(a.root)

    if a.cmd == "check":
        if git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
            print("This is a shallow clone: the pinned commits may be missing. Fetch the full history first "
                  "(git fetch --unshallow; in CI, fetch-depth: 0).")
            return 2
        problems = check(root)
        n = len(scan(root))
        if problems:
            print(f"{len(problems)} of {n} pinned links do not resolve:\n")
            print("\n".join(problems))
            return 1
        print(f"All {n} pinned links resolve.")
        return 0

    if a.cmd == "signature":
        rows, _ = build_report(root, a.head)
        print(signature(rows))
        return 0

    rows, text = build_report(root, a.head)
    print(text)
    if a.summary:
        with open(a.summary, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    moves_path = root / MOVES_FILE
    wanted = moves_json(rows)
    if a.write_moves:
        moves_path.write_text(wanted, encoding="utf-8", newline="\n")
        print(f"wrote {MOVES_FILE}")
    elif a.check_moves:
        have = moves_path.read_text(encoding="utf-8").replace("\r\n", "\n") if moves_path.is_file() else "{}\n"
        if have != wanted:
            msg = (f"{MOVES_FILE} is out of date: a file that a note links to has moved or been removed. "
                   f"Run: python tools/check_note_pins.py report --write-moves, and commit the file.")
            print(f"::warning title=Note pins::{msg}")
            print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
