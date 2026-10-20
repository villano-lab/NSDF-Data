#!/usr/bin/env python3
"""One command for all the checks on a student note.

    python tools/check_note.py notes/src/my-note.md        check one note (or several)
    python tools/check_note.py --changed origin/develop     check the notes changed since a Git ref (used by CI)

It runs the three checks that already exist, one after the other, and shows only what concerns the note you name:

    structure   tools/build_notes.py check       the header, the status, the pictures, the pinned notebook links.
                                                 A problem here fails the check (exit status 1).
    pins        tools/check_note_pins.py check   every pinned link resolves: the commit and the file exist. A problem
                                                 here fails the check. It needs the repository's Git history.
    numbers     tools/check_note_numbers.py      the numbers in the text that are not in the notebook's saved output.
                                                 Advisory: it is a help, not a proof, so it does not fail the check
                                                 unless you ask (--strict).

Options
    --only structure|pins|numbers   run only this check (repeat the option for several)
    --skip structure|pins|numbers   leave this check out (repeat the option for several)
    --strict                        a number that is NOT FOUND also fails the check
    --verbose                       also print the full output of each tool
    --notebook PATH                 passed to the number checker: use this notebook instead of the ones the note links to
    --changed REF                   check the notes under notes/src changed between REF and HEAD
    --github                        for CI: write the result to $GITHUB_STEP_SUMMARY and print GitHub warnings and errors

Exit status: 0 if the structure and the pinned links are fine (and, with --strict, the numbers), 1 otherwise, 2 if a
note cannot be found. Only the Python standard library is used.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_MD = {"README.md", "_template.md"}
CHECKS = ("structure", "pins", "numbers")
LABEL = {
    "structure": "Structure (tools/build_notes.py check)",
    "pins": "Pinned links (tools/check_note_pins.py check)",
    "numbers": "Numbers (tools/check_note_numbers.py)",
}
PIN_BLOCK = re.compile(r"^(\S.*?\.(?:md|html)): ")
NUMBER_LINE = re.compile(r"^\s+NOT FOUND\s+line\s+(\d+)\s+(\S+)")
NUMBER_TOTAL = re.compile(r"(\d+) numbers: (\d+) found in output, (\d+) only in code, (\d+) NOT FOUND")


def run_tool(args, root=ROOT):
    """Run a tool of this repository. Returns (exit status, its output)."""
    r = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout + r.stderr


def structure_problems(output, name):
    """The messages `build_notes.py check` printed for the note called `name` (one line each)."""
    prefix = name + ": "
    return [line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)]


def pin_problems(output, name):
    """The messages `check_note_pins.py check` printed for the note called `name`: its link, then the reason."""
    blocks, current = [], None
    for line in output.splitlines():
        m = PIN_BLOCK.match(line)
        if m:
            current = [line] if Path(m.group(1).replace("\\", "/")).name == name else None
            if current is not None:
                blocks.append(current)
        elif line.startswith((" ", "\t")) and current is not None:
            current.append(line.strip())
        else:
            current = None
    out = []
    for block in blocks:
        link = block[0].split(": ", 1)[1]
        out.append(link + ("  ->  " + " ".join(block[1:]) if len(block) > 1 else ""))
    return out


def number_report(output):
    """From the number checker's output: (the lines to show, how many numbers are NOT FOUND, how many problems)."""
    lines = [line for line in output.splitlines() if line.strip() and not line.startswith("==")]
    not_found = sum(1 for line in lines if NUMBER_LINE.match(line))
    problems = sum(1 for line in lines if line.strip().startswith("PROBLEM:"))
    return lines, not_found, problems


def check_note(path, checks, runner=run_tool, notebooks=(), root=ROOT):
    """Run the chosen checks on one note. Returns {check: {"status": "ok"|"fail"|"advice", "lines": [...]}}."""
    name = Path(path).name
    result = {}
    if "structure" in checks:
        code, out = runner(["tools/build_notes.py", "check"], root)
        mine = structure_problems(out, name)
        broken = code != 0 and not mine and "with problems" not in out
        if mine or broken:
            result["structure"] = {"status": "fail", "lines": mine or out.strip().splitlines()[-5:]}
        else:
            result["structure"] = {"status": "ok", "lines": []}
    if "pins" in checks:
        code, out = runner(["tools/check_note_pins.py", "check"], root)
        mine = pin_problems(out, name)
        broken = code != 0 and not mine and not any(PIN_BLOCK.match(line) for line in out.splitlines())
        if mine or broken:
            result["pins"] = {"status": "fail", "lines": mine or out.strip().splitlines()[-5:]}
        else:
            result["pins"] = {"status": "ok", "lines": []}
    if "numbers" in checks:
        extra = [a for nb in notebooks for a in ("--notebook", str(nb))]
        code, out = runner(["tools/check_note_numbers.py", str(path), *extra], root)
        lines, not_found, problems = number_report(out)
        if code not in (0, 1) or not lines:
            result["numbers"] = {"status": "fail", "lines": out.strip().splitlines()[-5:] or ["the number checker printed nothing"]}
        elif not_found or problems:
            result["numbers"] = {"status": "advice", "lines": lines, "not_found": not_found, "problems": problems}
        else:
            result["numbers"] = {"status": "ok", "lines": lines, "not_found": 0, "problems": 0}
    return result


def exit_status(result, strict=False):
    bad = any(r["status"] == "fail" for r in result.values())
    if strict and result.get("numbers", {}).get("status") == "advice":
        bad = True
    return 1 if bad else 0


def render(path, result, strict=False, verbose=False):
    """The text printed for one note."""
    out = [f"== {path}"]
    for check in CHECKS:
        if check not in result:
            continue
        r = result[check]
        if r["status"] == "ok":
            tail = "OK"
        elif r["status"] == "fail":
            tail = "PROBLEM"
        else:
            tail = f"{r['not_found']} NOT FOUND" + (f", {r['problems']} problem(s)" if r["problems"] else "") + (
                "" if strict else "  (advice, does not fail the check)")
        out.append(f"{LABEL[check]}: {tail}")
        show = r["lines"] if (r["status"] != "ok" or verbose) else []
        if check == "numbers" and not verbose:
            show = [line for line in show if "NOT FOUND" in line or "code only" in line or "PROBLEM" in line or "numbers:" in line]
        out += [f"    {line.strip()}" for line in show]
    return "\n".join(out)


def verdict(result, strict=False):
    if exit_status(result, strict):
        return "Result: fix the problems above, then run this again."
    advice = result.get("numbers", {}).get("status") == "advice"
    return "Result: ready for review. Look at the numbers listed above." if advice else "Result: ready for review."


def github_output(path, result, strict=False):
    """Lines for the GitHub Actions log and the job summary."""
    notes, summary = [], [f"### {path}", ""]
    for check in CHECKS:
        if check not in result:
            continue
        r = result[check]
        mark = {"ok": "OK", "fail": "PROBLEM", "advice": "to look at"}[r["status"]]
        summary.append(f"- **{LABEL[check]}**: {mark}")
        if r["status"] == "fail":
            for line in r["lines"]:
                notes.append(f"::error file={path}::{check}: {line}")
                summary.append(f"    - {line}")
        elif r["status"] == "advice":
            for line in r["lines"]:
                m = NUMBER_LINE.match(line)
                if m:
                    notes.append(f"::warning file={path},line={m.group(1)}::number {m.group(2)} is not in the notebook output")
                    summary.append(f"    - line {m.group(1)}: {m.group(2)} is not in the notebook output")
                elif "PROBLEM:" in line:
                    notes.append(f"::warning file={path}::{line.strip()}")
                    summary.append(f"    - {line.strip()}")
    summary.append("")
    return notes, summary


def changed_notes(ref, root=ROOT):
    r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=d", f"{ref}...HEAD", "--", "notes/src"], cwd=root,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"git diff against {ref} failed: {r.stderr.strip()}")
    return [Path(p) for p in r.stdout.split() if p.endswith(".md") and Path(p).name not in SKIP_MD]


def find_note(arg, root=ROOT):
    p = Path(arg)
    for candidate in (p, root / p, root / "notes" / "src" / p.name):
        if candidate.is_file():
            return candidate
    return None


def main(argv=None, runner=run_tool):
    ap = argparse.ArgumentParser(description="Run every check on a student note.")
    ap.add_argument("notes", nargs="*", help="note files, for example notes/src/my-note.md")
    ap.add_argument("--changed", metavar="REF", help="check the notes under notes/src changed between REF and HEAD")
    ap.add_argument("--only", action="append", choices=CHECKS, default=[])
    ap.add_argument("--skip", action="append", choices=CHECKS, default=[])
    ap.add_argument("--strict", action="store_true", help="a number that is NOT FOUND also fails the check")
    ap.add_argument("--verbose", action="store_true", help="also print the full output of each tool")
    ap.add_argument("--notebook", action="append", default=[], help="use this notebook for the number check")
    ap.add_argument("--github", action="store_true", help="write the result for GitHub Actions")
    args = ap.parse_args(argv)
    checks = [c for c in (args.only or CHECKS) if c not in args.skip]
    if not checks:
        ap.error("nothing to check: --only and --skip leave no check")
    notes = list(args.notes)
    if args.changed:
        notes += [str(p) for p in changed_notes(args.changed)]
        if not notes:
            print("No student notes changed.")
            return 0
    if not notes:
        ap.error("name a note, for example notes/src/my-note.md, or use --changed REF")
    status, summary_lines = 0, []
    for arg in notes:
        found = find_note(arg)
        if found is None:
            print(f"note not found: {arg}")
            return 2
        rel = found.resolve().relative_to(ROOT).as_posix() if ROOT in found.resolve().parents else str(found)
        result = check_note(rel, checks, runner, args.notebook)
        print(render(rel, result, args.strict, args.verbose))
        print(verdict(result, args.strict))
        print()
        status = max(status, exit_status(result, args.strict))
        if args.github:
            notes_out, summary = github_output(rel, result, args.strict)
            for line in notes_out:
                print(line)
            summary_lines += summary
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github and target:
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n".join(summary_lines) + "\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
