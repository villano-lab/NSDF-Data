"""The date a student note became Complete is taken from Git's history, and a note that was reopened and completed
again shows the date of the revision, with a red box at its top if its author did not say so."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_notes as bn  # noqa: E402

NOTE = "notes/src/demo.md"


def git(repo, *args, **env):
    subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args], cwd=repo, check=True,
                   capture_output=True, env={**os.environ, **env})


def commit(repo, status, day, message=None):
    body = message or f"{status} {day}"                      # a different body each time, so every commit changes the file
    (repo / NOTE).write_text(f'---\nid: "9"\nstatus: "{status}"\n---\n{body}\n', encoding="utf-8")
    git(repo, "add", "-A")
    stamp = f"{day}T12:00:00"
    git(repo, "commit", "-m", message or f"{status} {day}", GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "notes" / "src").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "develop")
    return tmp_path


def test_a_note_that_was_never_complete_has_no_date(repo):
    commit(repo, "In progress", "2026-09-10")
    assert bn.completion_dates(NOTE, repo) == (None, None)


def test_completed_once_shows_the_date_of_that_commit(repo):
    commit(repo, "In progress", "2026-09-10")
    commit(repo, "Complete", "2026-09-14")
    commit(repo, "Complete", "2026-09-20", "a later edit that leaves it Complete")
    assert bn.completion_dates(NOTE, repo) == ("2026-09-14", None)


def test_a_note_created_as_complete_counts_from_its_first_commit(repo):
    commit(repo, "Complete", "2026-09-14")
    assert bn.completion_dates(NOTE, repo) == ("2026-09-14", None)


def test_reopened_and_completed_again_gives_the_first_and_the_revision_date(repo):
    commit(repo, "Complete", "2026-09-14")
    commit(repo, "In progress", "2026-09-15")
    commit(repo, "Complete", "2026-10-01")
    assert bn.completion_dates(NOTE, repo) == ("2026-09-14", "2026-10-01")


def test_reopened_again_after_that_gives_the_latest_completion_as_the_revision(repo):
    for status, day in [("Complete", "2026-09-14"), ("In progress", "2026-09-15"), ("Complete", "2026-10-01"),
                        ("In progress", "2026-10-05"), ("Complete", "2026-10-09")]:
        commit(repo, status, day)
    assert bn.completion_dates(NOTE, repo) == ("2026-09-14", "2026-10-09")


def test_a_note_that_is_in_progress_now_has_no_date_even_if_it_was_complete(repo):
    commit(repo, "Complete", "2026-09-14")
    commit(repo, "In progress", "2026-09-15")
    assert bn.completion_dates(NOTE, repo) == (None, None)


def test_a_merged_pull_request_counts_as_the_day_of_its_merge(repo):
    commit(repo, "In progress", "2026-09-10")
    git(repo, "switch", "-q", "-c", "student-x")
    commit(repo, "Complete", "2026-10-01", "completed on the student branch")
    git(repo, "switch", "-q", "develop")
    (repo / "other.txt").write_text("x", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "something else", GIT_AUTHOR_DATE="2026-10-02T12:00:00", GIT_COMMITTER_DATE="2026-10-02T12:00:00")
    git(repo, "merge", "--no-ff", "-m", "Merge student-x", "student-x", GIT_AUTHOR_DATE="2026-10-05T12:00:00", GIT_COMMITTER_DATE="2026-10-05T12:00:00")
    assert bn.completion_dates(NOTE, repo) == ("2026-10-05", None)


def test_a_shallow_clone_gives_no_date_instead_of_a_wrong_one(repo, tmp_path_factory):
    commit(repo, "In progress", "2026-09-10")
    commit(repo, "Complete", "2026-09-14")
    commit(repo, "Complete", "2026-09-20", "an edit")
    shallow = tmp_path_factory.mktemp("shallow") / "clone"
    subprocess.run(["git", "clone", "-q", "--depth", "1", repo.as_uri(), str(shallow)], check=True, capture_output=True)
    assert bn.completion_dates(NOTE, shallow) == (None, None)


def test_a_folder_that_is_not_a_repository_gives_no_date(tmp_path):
    assert bn.completion_dates(NOTE, tmp_path) == (None, None)


def test_the_status_text():
    assert bn.status_text({"status": "In progress", "_first": "2026-09-14"}) == "In progress"
    assert bn.status_text({"status": "Complete"}) == "Complete"
    assert bn.status_text({"status": "Complete", "_first": "2026-09-14"}) == "Complete (2026-09-14)"
    assert bn.status_text({"status": "Complete", "_first": "2026-09-14", "_revised": "2026-10-01"}) == \
        "Complete (2026-09-14), revised (2026-10-01)"
    assert bn.status_text({"status": "Superseded (reference/link)"}) == "Superseded (reference/link)"


def test_the_index_row_shows_the_status_text():
    rows = bn.index_rows([("demo", {"id": "9", "date": "2026-10-05", "author": "A", "title": "T", "description": "D",
                                    "keywords": "k", "status": "Complete", "_first": "2026-09-14", "_revised": "2026-10-01"})])
    assert "Complete (2026-09-14),<br>revised (2026-10-01)" in rows[0][1]     # the revised date goes on its own line


def test_the_red_box_appears_for_a_revision_the_author_did_not_announce():
    h = {"_first": "2026-09-14", "_revised": "2026-10-01", "_src": "notes/src/demo.md"}
    box = bn.revised_box(h, "## The question\n\nText.\n")
    assert 'class="revised-box"' in box and "Revised 2026-10-01" in box and "2026-09-14" in box
    assert "commits/develop/notes/src/demo.md" in box


@pytest.mark.parametrize("label", ["Revised.", "Revision.", "Correction.", "Update."])
def test_the_red_box_is_left_out_when_the_author_put_a_box_of_their_own(label):
    h = {"_first": "2026-09-14", "_revised": "2026-10-01"}
    assert bn.revised_box(h, f"::: callout\n**{label}** What changed.\n:::\n") == ""


def test_no_red_box_for_a_note_that_was_not_revised():
    assert bn.revised_box({"_first": "2026-09-14"}, "text") == ""
    assert bn.revised_box({}, "text") == ""


def test_backticks_in_the_title_and_description_render_as_code():
    h = {"id": "9", "date": "2026-10-05", "author": "A", "title": "What are `goldpan` and `goldsluice`?",
         "description": "Moving `python/` into the package `goldpan` & more.", "keywords": "k", "status": "In progress"}
    row = bn.index_rows([("demo", h)])[0][1]
    assert "<td>What are <code>goldpan</code> and <code>goldsluice</code>?</td>" in row
    assert "Moving <code>python/</code> into the package <code>goldpan</code> &amp; more." in row
    assert "`" not in row
    assert bn.header_html("no <b>markup</b> here & `x<y`") == "no &lt;b&gt;markup&lt;/b&gt; here &amp; <code>x&lt;y</code>"
    assert bn.header_plain("the `goldpan` tab") == "the goldpan tab"
    assert bn.header_html("a lone ` backtick") == "a lone ` backtick"
