#!/usr/bin/env python3
"""Suggest the note number on a pull request that adds a student note with id "TBD".

A student leaves `id: "TBD"` in the header of a new note; the reviewer replaces it with the next free note number
before merging (the build refuses a note that still says TBD). This tool, run by the Student notes workflow on a pull
request, writes the number on the pull request so that the reviewer needs no checkout:

    python tools/suggest_note_number.py --repo OWNER/REPO --pr 96 --head <sha of the PR head> --base origin/develop

For every note the pull request changes whose header still says `id: "TBD"`, it posts a review comment on that line
with a suggestion block: `id: "9"`, where 9 is `build_notes.py next` on the pull request merged into develop. GitHub
shows a **Commit suggestion** button on it. The reviewer presses it (the commit is theirs, so the checks run again),
then merges. The decision stays with the reviewer: nothing is pushed to the student's branch by this tool.

- Running it again (a new push, a re-run of the check) updates the comment if the number changed, and does nothing
  if it did not. A hidden marker in the comment, one per note, says which comment is ours.
- If GitHub refuses the comment on that line (the line is not part of the pull request's changes), it posts an
  ordinary comment with the same instruction instead.
- When the id is no longer TBD there is nothing to suggest.
- Two note pull requests open at once are both offered the same number. After the first is merged, re-run the check
  of the second to refresh its suggestion.

--dry-run prints what it would post. It needs `git` and the GitHub CLI `gh` (with GH_TOKEN in CI, and
`pull-requests: write` on the token). Only the Python standard library is used.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_notes as bn  # noqa: E402

SKIP_MD = {"README.md", "_template.md"}
ID_TBD = re.compile(r'^id:\s*"TBD"\s*$')


class GhError(Exception):
    pass


def marker(path):
    return f"<!-- note-number-suggestion:{path} -->"


def tbd_line(text):
    """The 1-based line of `id: "TBD"` in the header of a note, or None if the id is a number (or there is no header)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return None
        if ID_TBD.match(line):
            return number
    return None


def suggestion_body(path, number):
    return (f"**Next free note number: {number}.** To give this note its number, press **Commit suggestion** below, "
            f"then merge. The number is what `python tools/build_notes.py next` prints for this pull request merged "
            f"into `develop` at the time of the last check; if another note is merged first, re-run the check to "
            f"refresh it.\n\n```suggestion\nid: \"{number}\"\n```\n{marker(path)}")


def fallback_body(path, number):
    return (f"**Next free note number: {number}.** In `{path}`, change `id: \"TBD\"` in the header to "
            f"`id: \"{number}\"` (on GitHub: **Files changed**, the **...** menu of the file, **Edit file**), then merge. "
            f"The number is what `python tools/build_notes.py next` prints for this pull request merged into "
            f"`develop` at the time of the last check.\n{marker(path)}")


def find_ours(path, comments):
    """The existing comment (review or ordinary) that carries the marker of this note, or None."""
    tag = marker(path)
    return next((c for c in comments if tag in (c.get("body") or "")), None)


def plan(notes, number, comments):
    """What to do for each note: [(action, path, ...)]. `notes` is {path: text of the note on the PR head}."""
    actions = []
    for path in sorted(notes):
        line = tbd_line(notes[path])
        if line is None:
            continue
        body = suggestion_body(path, number)
        ours = find_ours(path, comments)
        if ours is None:
            actions.append(("create", path, line, body))
        elif ours["body"].strip() != body.strip() and ours["body"].strip() != fallback_body(path, number).strip():
            actions.append(("update", path, ours, body))
    return actions


def execute(actions, number, post_review, post_issue, patch_comment, head):
    """Carry out the plan with the given functions. Returns a list of lines saying what was done."""
    done = []
    for act in actions:
        if act[0] == "create":
            _, path, line, body = act
            try:
                post_review(body, head, path, line)
                done.append(f"{path}: suggested id \"{number}\" on line {line}")
            except GhError as e:
                post_issue(fallback_body(path, number))
                done.append(f"{path}: posted an ordinary comment (GitHub refused the line comment: {e})")
        else:
            _, path, ours, body = act
            body = fallback_body(path, number) if ours.get("kind") == "issue" else body
            patch_comment(ours, body)
            done.append(f"{path}: updated the suggestion to id \"{number}\"")
    return done


# ---- the GitHub side (not used by the tests)

def gh(args, fields=None):
    cmd = ["gh", "api", *args]
    for key, value in (fields or {}).items():
        cmd += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise GhError((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else "gh failed")
    return json.loads(r.stdout) if r.stdout.strip() else None


def list_comments(repo, pr):
    """Every review comment and ordinary comment of the pull request, as {"id", "body", "kind"}."""
    out = []
    for kind, path in (("review", f"repos/{repo}/pulls/{pr}/comments"), ("issue", f"repos/{repo}/issues/{pr}/comments")):
        r = subprocess.run(["gh", "api", "--paginate", path, "--jq", ".[] | {id: .id, body: .body}"],
                           capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise GhError(r.stderr.strip() or "gh failed")
        for line in r.stdout.splitlines():
            if line.strip():
                c = json.loads(line)
                out.append({"id": c["id"], "body": c.get("body"), "kind": kind})
    return out


def changed_notes(base, root=ROOT):
    r = subprocess.run(["git", "diff", "--name-only", "--diff-filter=d", f"{base}...HEAD", "--", "notes/src"], cwd=root,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"git diff against {base} failed: {r.stderr.strip()}")
    return [p for p in r.stdout.split() if p.endswith(".md") and Path(p).name not in SKIP_MD]


def read_at(head, path, root=ROOT):
    r = subprocess.run(["git", "show", f"{head}:{path}"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0:
        return r.stdout
    return (Path(root) / path).read_text(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Suggest the note number on a pull request.")
    ap.add_argument("--repo", required=True, help="OWNER/REPO")
    ap.add_argument("--pr", required=True, type=int, help="the pull request number")
    ap.add_argument("--head", required=True, help="the commit at the head of the pull request")
    ap.add_argument("--base", default="origin/develop", help="the Git ref the pull request is compared with")
    ap.add_argument("--dry-run", action="store_true", help="print what would be posted")
    args = ap.parse_args(argv)
    notes = {p: read_at(args.head, p) for p in changed_notes(args.base)}
    if not any(tbd_line(t) for t in notes.values()):
        print("No changed note has id \"TBD\": nothing to suggest.")
        return 0
    number = bn.next_number()
    comments = [] if args.dry_run else list_comments(args.repo, args.pr)
    actions = plan(notes, number, comments)
    if not actions:
        print(f"The suggestion of number {number} is already on the pull request.")
        return 0
    if args.dry_run:
        for act in actions:
            print(f"would {act[0]}: {act[1]}\n{act[-1]}\n")
        return 0

    def post_review(body, head, path, line):
        gh([f"repos/{args.repo}/pulls/{args.pr}/comments", "-X", "POST"],
           {"body": body, "commit_id": head, "path": path, "line": line, "side": "RIGHT"})

    def post_issue(body):
        gh([f"repos/{args.repo}/issues/{args.pr}/comments", "-X", "POST"], {"body": body})

    def patch_comment(ours, body):
        kind = "pulls" if ours["kind"] == "review" else "issues"
        gh([f"repos/{args.repo}/{kind}/comments/{ours['id']}", "-X", "PATCH"], {"body": body})

    for line in execute(actions, number, post_review, post_issue, patch_comment, args.head):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
