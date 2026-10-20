#!/usr/bin/env python3
"""Check that the numbers in a student note appear in the output of the notebook behind it.

A note's numbers must come from its notebook. This tool lists, for each note in notes/src (or the notes you name),
the numbers in the text that it cannot find in the notebook's saved output. It is a checking aid for the author and
the reviewer, not a proof: read the list and decide.

    python tools/check_note_numbers.py                       every note in notes/src
    python tools/check_note_numbers.py notes/src/my-note.md  one note
    python tools/check_note_numbers.py my-note.md --notebook path/to/other.ipynb   use this notebook instead of the
                                                              ones the note links to (repeat the option for several)
    python tools/check_note_numbers.py my-note.md --verbose  also say where each number was found
    python tools/check_note_numbers.py my-note.md --all-small  also check the one-digit whole numbers (skipped by
                                                              default: "channel 0", "3 plots" are mostly words)

Which notebook: the notebooks the note links to at a pinned commit (https://github.com/villano-lab/NSDF-Data/blob/
<commit>/path/name.ipynb), read from Git at that commit, or from your working copy if Git does not have it.
The notebook must have been saved with its outputs (do not clear them before you commit).

What counts as a number in the note: digits in the text and captions, including decimals, thousands separators
(1,517), percentages and scientific notation. Not counted: the header, code (blocks and `inline`), links and
addresses, HTML tags, a References section, "Figure 1", "Note 2", "Step 3" and similar labels, list numbers, dates and years, names such as
07221203_2025 or S104. To leave a line out, end it with <!-- numbers-ok -->.

A number is found when the notebook's output has a number that rounds to it at the digits the note shows (0.52 matches
0.5213), as a percent of it (45% matches 0.4512), or, for a whole number ending in zeros, rounded to that many
significant digits (5200 matches 5213.4). Numbers that appear only in the notebook's code (a threshold you chose) are
listed separately: they are inputs, not results, so say so in the note. Everything else is NOT FOUND: a number typed by
hand, from a different run of the notebook, or from a plot (read the number off the plot only if you say so).

Exit status 1 if any number is NOT FOUND, otherwise 0. Only the Python standard library is used.
"""
import argparse
import json
import re
import subprocess
import sys
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_MD = {"README.md", "_template.md"}
NOTEBOOK_LINK = re.compile(r"https://github\.com/villano-lab/NSDF-Data/blob/([0-9a-f]{7,40})/([^\s\"'<>)#?]+\.ipynb)")
NUMBER = re.compile(
    r"(?<![\w.])"                         # not inside a name such as S104, 07221203_2025 or v1.2
    r"(\d{1,3}(?:,\d{3})+|\d+)"           # whole part, with or without thousands separators
    r"(?:\.(\d+))?"                       # decimals
    r"(?:[eE]([+-]?\d+))?"                # exponent
    r"(%)?"                               # percent sign
    r"(?![\w])"
)
LABEL = re.compile(
    r"\b(Run|Figure|Fig\.?|Table|Note|Step|Section|Appendix|Equation|Eq\.?|Guide|Dump|Series|Channel|Chan\.?|Detector|"
    r"Event|Events|Page|Chapter|Issue|PR|Part)\s+\d+[a-z]?\b",
    re.I,
)
IGNORE_MARK = "numbers-ok"


class Num:
    """A number as written: its value, the digits it shows after the point, and a percent flag."""
    def __init__(self, text, whole, frac, exp, pct):
        self.text = text
        self.pct = bool(pct)
        digits = whole.replace(",", "") + ("." + frac if frac else "")
        self.value = Decimal(digits) * (Decimal(10) ** int(exp)) if exp else Decimal(digits)
        self.places = (len(frac) if frac else 0) - (int(exp) if exp else 0)
        self.is_int = frac is None and exp is None
        self.zeros = len(whole.replace(",", "")) - len(whole.replace(",", "").rstrip("0")) if self.is_int else 0


def tokens(text):
    out = []
    for m in NUMBER.finditer(text):
        try:
            out.append(Num(m.group(0), m.group(1), m.group(2), m.group(3), m.group(4)))
        except (InvalidOperation, ValueError):
            pass
    return out


def clean_note_line(line):
    """The prose of one Markdown line, with everything that is not a result removed."""
    line = re.sub(r"<!--.*?-->", " ", line)
    line = re.sub(r"<[^>]+>", " ", line)                          # HTML tags
    line = re.sub(r"`[^`]*`", " ", line)                           # inline code
    line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r" \1 ", line)        # images: keep the caption, drop the path
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r" \1 ", line)         # links: keep the words, drop the address
    line = re.sub(r"https?://\S+", " ", line)
    line = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", line)             # ISO dates
    line = re.sub(r"^\s*\d+[.)]\s+", " ", line)                    # numbered list items
    line = re.sub(r"^#+\s*\d+(\.\d+)*\.?\s+", "## ", line)         # numbered headings
    line = LABEL.sub(" ", line)
    return line


def note_numbers(md_text, all_small=False):
    """[(line number, Num, line text)] for every number to check in a note's text."""
    lines = md_text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":                        # skip the header
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1
    found, fenced, refs = [], False, False
    for n in range(i, len(lines)):
        raw = lines[n]
        if raw.startswith("#"):                                    # a reference list holds citations, not results
            refs = bool(re.match(r"#+\s*(references|bibliography|further reading)\b", raw, re.I))
        if refs:
            continue
        if re.match(r"^\s*(```|~~~)", raw):
            fenced = not fenced
            continue
        if fenced or IGNORE_MARK in raw:
            continue
        for t in tokens(clean_note_line(raw)):
            if t.is_int and not t.pct:
                if 1900 <= t.value <= 2100:                        # a year
                    continue
                if not all_small and t.value < 10:
                    continue
            found.append((n + 1, t, raw.strip()))
    return found


def matches(note, m):
    """Does the output number m (a Num) show the same value as the note's number at the note's precision?"""
    target, value = note.value, m.value
    if note.pct:
        values = [value * 100, value]                              # "45%" for 0.45, or for a printed 45.1
    else:
        values = [value]
    for v in values:
        for rounding in (ROUND_HALF_UP, ROUND_HALF_EVEN):
            try:
                if v.quantize(Decimal(1).scaleb(-note.places), rounding=rounding) == target:
                    return True
                if note.zeros and v.quantize(Decimal(1).scaleb(note.zeros), rounding=rounding) == target:
                    return True                                    # 5200 for 5213.4
            except InvalidOperation:
                pass
    return False


def output_text(cell):
    """The text of one code cell's saved output."""
    parts = []
    for o in cell.get("outputs", []):
        kind = o.get("output_type")
        if kind == "stream":
            parts.append("".join(o.get("text", [])))
        elif kind in ("execute_result", "display_data"):
            data = o.get("data", {})
            if "text/plain" in data:
                parts.append("".join(data["text/plain"]))
            elif "text/html" in data:
                parts.append(re.sub(r"<[^>]+>", " ", "".join(data["text/html"])))
    return "\n".join(parts)


def notebook_numbers(nb):
    """(outputs, code): lists of (cell number, Num) from the saved outputs and from the code cells' source."""
    outputs, code, has_output = [], [], False
    for k, cell in enumerate(nb.get("cells", []), 1):
        if cell.get("cell_type") != "code":
            continue
        text = output_text(cell)
        has_output = has_output or bool(text.strip())
        outputs += [(k, t) for t in tokens(text)]
        src = "".join(cell.get("source", []))
        src = re.sub(r"(?m)^\s*#.*$", "", src)                     # comment lines
        code += [(k, t) for t in tokens(src)]
    return outputs, code, has_output


def git_show(root, sha, path):
    r = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def load_notebooks(root, md_text, explicit):
    """[(label, notebook dict)] and a list of problems."""
    root = Path(root)
    result, problems = [], []
    if explicit:
        for p in explicit:
            try:
                result.append((str(p), json.loads(Path(p).read_text(encoding="utf-8"))))
            except (OSError, ValueError) as e:
                problems.append(f"cannot read notebook {p}: {e}")
        return result, problems
    seen = set()
    for sha, path in NOTEBOOK_LINK.findall(md_text):
        if (sha, path) in seen:
            continue
        seen.add((sha, path))
        text = git_show(root, sha, path)
        label = f"{path} @ {sha}"
        if text is None and (root / path).exists():
            text, label = (root / path).read_text(encoding="utf-8"), f"{path} (working copy; commit {sha} not found)"
        if text is None:
            problems.append(f"notebook not found: {path} at {sha}")
            continue
        try:
            result.append((label, json.loads(text)))
        except ValueError as e:
            problems.append(f"{path} is not a notebook: {e}")
    if not result and not problems:
        problems.append("the note links to no notebook (https://github.com/villano-lab/NSDF-Data/blob/<commit>/....ipynb)")
    return result, problems


def check_note(root, path, explicit=(), all_small=False, verbose=False, out=print):
    """Check one note. Returns the number of numbers NOT FOUND."""
    text = Path(path).read_text(encoding="utf-8")
    notebooks, problems = load_notebooks(root, text, explicit)
    out(f"== {path}")
    for pr in problems:
        out(f"  PROBLEM: {pr}")
    outputs, code = [], []
    for label, nb in notebooks:
        o, c, has_output = notebook_numbers(nb)
        out(f"  notebook: {label}" + ("" if has_output else "  (NO SAVED OUTPUT: run it and save it with its outputs)"))
        outputs += [(label, k, t) for k, t in o]
        code += [(label, k, t) for k, t in c]
    numbers = note_numbers(text, all_small)
    ok, code_only, missing = [], [], []
    for line, t, raw in numbers:
        hit = next((x for x in outputs if matches(t, x[2])), None)
        if hit:
            ok.append((line, t, hit))
            continue
        hit = next((x for x in code if matches(t, x[2])), None)
        (code_only if hit else missing).append((line, t, raw, hit))
    out(f"  {len(numbers)} numbers: {len(ok)} found in output, {len(code_only)} only in code, {len(missing)} NOT FOUND")
    if verbose:
        for line, t, (label, k, x) in ok:
            out(f"    found      line {line:>4}  {t.text:<12} = {x.text} in output of cell {k}")
    for line, t, raw, (label, k, x) in code_only:
        out(f"    code only  line {line:>4}  {t.text:<12} (cell {k} has {x.text} in its code, not in its output)")
    for line, t, raw, _ in missing:
        out(f"    NOT FOUND  line {line:>4}  {t.text:<12} {raw[:100]}")
    return len(missing) + (1 if problems else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description="List the numbers in a note that are not in its notebook's output.")
    ap.add_argument("notes", nargs="*", help="note files (default: every note in notes/src)")
    ap.add_argument("--notebook", action="append", default=[], help="use this notebook instead of the note's links")
    ap.add_argument("--all-small", action="store_true", help="also check whole numbers below 10")
    ap.add_argument("--verbose", action="store_true", help="also list the numbers that were found")
    ap.add_argument("--root", default=str(ROOT), help="the repository (default: this one)")
    args = ap.parse_args(argv)
    notes = [Path(n) for n in args.notes] or sorted(
        p for p in (Path(args.root) / "notes" / "src").glob("*.md") if p.name not in SKIP_MD
    )
    if not notes:
        print("no notes to check")
        return 0
    bad = sum(check_note(args.root, n, args.notebook, args.all_small, args.verbose) for n in notes)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
