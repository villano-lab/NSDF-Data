"""Tests for tools/check_note_pins.py: the pinned links in the notes must resolve, and the report must say when the
pinned files have changed, moved or been removed (issue 51)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_note_pins as cnp  # noqa: E402

URL = "https://github.com/villano-lab/NSDF-Data/"


def run(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", check=True)
    return r.stdout.strip()


def commit(repo, message):
    run(repo, "add", "-A")
    run(repo, "-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "-m", message)
    return run(repo, "rev-parse", "--short=7", "HEAD")


@pytest.fixture
def repo(tmp_path):
    """A small repository with a history: a file that changes, a file that moves, a file that is removed."""
    run(tmp_path, "init", "-q")
    (tmp_path / "lib").mkdir()
    big = "".join(f"line {i} of a reasonably long file, so that Git can tell it was moved\n" for i in range(40))
    (tmp_path / "lib" / "keep.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "lib" / "edit.py").write_text("b = 1\n", encoding="utf-8")
    (tmp_path / "old_dir").mkdir()
    (tmp_path / "old_dir" / "mover.py").write_text(big, encoding="utf-8")
    (tmp_path / "gone.csv").write_text("x\n1\n", encoding="utf-8")
    first = commit(tmp_path, "first")
    (tmp_path / "lib" / "edit.py").write_text("b = 2\n", encoding="utf-8")
    commit(tmp_path, "edit")
    (tmp_path / "data_analysis").mkdir()
    run(tmp_path, "mv", "old_dir/mover.py", "data_analysis/mover.py")
    commit(tmp_path, "move")
    # edit the moved file so much that comparing only the two ends cannot see the rename
    (tmp_path / "data_analysis" / "mover.py").write_text("completely different\n" * 30, encoding="utf-8")
    commit(tmp_path, "edit moved file")
    run(tmp_path, "rm", "-q", "gone.csv")
    commit(tmp_path, "remove")
    (tmp_path / "docs" / "notes").mkdir(parents=True)
    (tmp_path / "notes" / "src").mkdir(parents=True)
    return tmp_path, first


def note(repo, links, name="note-01-test.html"):
    body = "".join(f'<li><a href="{URL}{kind}/{ref}/{path}">{path}</a></li>' for kind, ref, path in links)
    (repo / "docs" / "notes" / name).write_text(f"<html><body><ul>{body}</ul></body></html>", encoding="utf-8")


def test_scan_finds_pinned_links_in_html_and_markdown_and_ignores_other_pages(repo):
    r, first = repo
    note(r, [("blob", first, "lib/keep.py"), ("tree", first, "lib")])
    (r / "notes" / "src" / "student-note.md").write_text(
        f"See [the notebook]({URL}blob/{first}/lib/edit.py#L3) and [elsewhere](https://github.com/other/repo/blob/{first}/x).\n",
        encoding="utf-8")
    (r / "notes" / "src" / "README.md").write_text(f"{URL}blob/{first}/ignored.py\n", encoding="utf-8")
    links = cnp.scan(r)
    got = sorted((l["note"], l["kind"], l["path"]) for l in links)
    assert got == [("docs/notes/note-01-test.html", "blob", "lib/keep.py"),
                   ("docs/notes/note-01-test.html", "tree", "lib"),
                   ("notes/src/student-note.md", "blob", "lib/edit.py")]


def test_a_generated_page_is_not_counted_twice(repo):
    r, first = repo
    (r / "notes" / "src" / "my-first-note.md").write_text(f"[x]({URL}blob/{first}/lib/keep.py)\n", encoding="utf-8")
    note(r, [("blob", first, "lib/keep.py")], name="note-09-my-first-note.html")
    assert [l["note"] for l in cnp.scan(r)] == ["notes/src/my-first-note.md"]


def test_check_passes_when_every_pin_resolves_including_an_old_path(repo):
    r, first = repo
    # old_dir/mover.py and gone.csv no longer exist today, but they exist at the pinned commit
    note(r, [("blob", first, "lib/keep.py"), ("blob", first, "old_dir/mover.py"), ("blob", first, "gone.csv"), ("tree", first, "old_dir")])
    assert cnp.check(r) == []


def test_check_reports_a_missing_commit_a_missing_path_and_an_unpinned_link(repo):
    r, first = repo
    note(r, [("blob", "deadbee", "lib/keep.py"), ("blob", first, "lib/typo.py"), ("blob", "master", "lib/keep.py")])
    problems = "\n".join(cnp.check(r))
    assert "deadbee does not exist" in problems
    assert "lib/typo.py does not exist at commit" in problems
    assert "not pinned to a commit hash ('master')" in problems
    assert len(cnp.check(r)) == 3


def test_report_says_current_changed_moved_and_removed(repo):
    r, first = repo
    note(r, [("blob", first, "lib/keep.py"), ("blob", first, "lib/edit.py"), ("blob", first, "old_dir/mover.py"),
             ("blob", first, "gone.csv"), ("tree", first, "old_dir")])
    rows, text = cnp.build_report(r, "HEAD")
    state = {x["path"]: x for x in rows}
    assert state["lib/keep.py"]["state"] == "current"
    assert state["lib/edit.py"]["state"] == "changed" and state["lib/edit.py"]["commits"] == "1"
    assert state["old_dir/mover.py"]["state"] == "moved" and state["old_dir/mover.py"]["target"] == "data_analysis/mover.py"
    assert state["gone.csv"]["state"] == "removed"
    assert state["old_dir"]["state"] == "removed"  # the folder is gone and its only file is followed on its own
    assert "## Needs a look" in text and "gone.csv" in text


def test_a_folder_that_moved_is_found_from_its_files(repo):
    r, first = repo
    run(r, "mv", "lib", "library")
    commit(r, "rename the folder")
    note(r, [("tree", first, "lib")])
    rows, _ = cnp.build_report(r, "HEAD")
    assert rows[0]["state"] == "moved" and rows[0]["target"] == "library"


def test_moves_file_lists_only_moved_and_removed_links(repo):
    r, first = repo
    note(r, [("blob", first, "lib/keep.py"), ("blob", first, "old_dir/mover.py"), ("blob", first, "gone.csv")])
    rows, _ = cnp.build_report(r, "HEAD")
    assert json.loads(cnp.moves_json(rows)) == {f"{first}/gone.csv": None,
                                                f"{first}/old_dir/mover.py": "data_analysis/mover.py"}


def test_command_line_exit_status(repo, capsys):
    r, first = repo
    note(r, [("blob", first, "lib/keep.py")])
    assert cnp.main(["--root", str(r), "check"]) == 0
    note(r, [("blob", first, "lib/typo.py")])
    assert cnp.main(["--root", str(r), "check"]) == 1
    assert "do not resolve" in capsys.readouterr().out


def test_the_real_notes_resolve():
    """Every pinned link in this repository's notes must resolve (needs the full history; skipped in a shallow clone)."""
    shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, capture_output=True, text=True)
    if shallow.stdout.strip() != "false":
        pytest.skip("shallow clone: the pinned commits are not available")
    assert cnp.check(ROOT) == []
