"""Tests for tools/suggest_note_number.py: a pull request that adds a student note with id "TBD" gets the next free
note number as a suggestion the reviewer can commit with one click."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import suggest_note_number as sn  # noqa: E402

NOTE = 'notes/src/my-note.md'
TBD_TEXT = '---\nid: "TBD"\ntitle: "A question?"\nauthor: "A"\n---\n\nBody with id: "TBD" in the text.\n'
NUMBERED = TBD_TEXT.replace('id: "TBD"', 'id: "9"', 1)


def test_the_line_of_the_tbd_id_is_found_in_the_header_only():
    assert sn.tbd_line(TBD_TEXT) == 2
    assert sn.tbd_line("---\ntitle: \"x\"\nid: \"TBD\"\n---\n") == 3
    assert sn.tbd_line(NUMBERED) is None
    assert sn.tbd_line("---\nid: \"9\"\n---\nid: \"TBD\"\n") is None       # a TBD in the body does not count
    assert sn.tbd_line("no header\nid: \"TBD\"\n") is None
    assert sn.tbd_line("") is None


def test_the_suggestion_body_has_the_number_a_suggestion_block_and_the_marker():
    body = sn.suggestion_body(NOTE, 9)
    assert "Next free note number: 9" in body
    assert '```suggestion\nid: "9"\n```' in body
    assert "Commit suggestion" in body
    assert sn.marker(NOTE) in body
    assert sn.marker("notes/src/other.md") not in body


def test_plan_creates_a_suggestion_for_a_tbd_note_and_ignores_numbered_ones():
    notes = {NOTE: TBD_TEXT, "notes/src/done.md": NUMBERED}
    actions = sn.plan(notes, 9, comments=[])
    assert len(actions) == 1
    act = actions[0]
    assert act[:3] == ("create", NOTE, 2) and '```suggestion\nid: "9"' in act[3]


def test_plan_does_nothing_when_the_same_suggestion_is_already_there():
    body = sn.suggestion_body(NOTE, 9)
    assert sn.plan({NOTE: TBD_TEXT}, 9, [{"id": 1, "body": body, "kind": "review"}]) == []
    fallback = sn.fallback_body(NOTE, 9)
    assert sn.plan({NOTE: TBD_TEXT}, 9, [{"id": 2, "body": fallback, "kind": "issue"}]) == []


def test_plan_updates_the_comment_when_the_number_changed():
    old = sn.suggestion_body(NOTE, 9)
    actions = sn.plan({NOTE: TBD_TEXT}, 10, [{"id": 7, "body": old, "kind": "review"}])
    assert len(actions) == 1 and actions[0][0] == "update" and actions[0][2]["id"] == 7
    assert 'id: "10"' in actions[0][3]


def test_plan_finds_the_comment_of_each_note_by_its_marker():
    other = sn.suggestion_body("notes/src/other.md", 9)
    actions = sn.plan({NOTE: TBD_TEXT}, 9, [{"id": 3, "body": other, "kind": "review"}])
    assert actions[0][0] == "create"          # the existing comment belongs to another note


def test_execute_posts_a_review_comment_on_the_line_with_the_head_commit():
    calls = []
    actions = sn.plan({NOTE: TBD_TEXT}, 9, [])
    done = sn.execute(actions, 9, lambda *a: calls.append(("review",) + a), lambda b: calls.append(("issue", b)),
                      lambda c, b: calls.append(("patch", c, b)), head="abc1234")
    assert len(calls) == 1 and calls[0][0] == "review"
    assert calls[0][2:5] == ("abc1234", NOTE, 2)          # (body, head commit, path, line) of the review comment
    assert "suggested" in done[0] and NOTE in done[0]


def test_execute_falls_back_to_an_ordinary_comment_when_github_refuses_the_line():
    issues = []

    def refuse(*args):
        raise sn.GhError("line must be part of the diff")

    actions = sn.plan({NOTE: TBD_TEXT}, 9, [])
    done = sn.execute(actions, 9, refuse, lambda b: issues.append(b), lambda c, b: None, head="abc1234")
    assert len(issues) == 1 and 'change `id: "TBD"`' in issues[0] and sn.marker(NOTE) in issues[0]
    assert "ordinary comment" in done[0]


def test_execute_updates_a_review_comment_and_an_ordinary_one():
    patched = []
    review = {"id": 1, "body": sn.suggestion_body(NOTE, 9), "kind": "review", "path": NOTE}
    issue = {"id": 2, "body": sn.fallback_body(NOTE, 9), "kind": "issue"}
    for comment in (review, issue):
        patched.clear()
        actions = sn.plan({NOTE: TBD_TEXT}, 10, [comment])
        sn.execute(actions, 10, None, None, lambda c, b: patched.append((c["id"], b)), head="abc1234")
        assert patched[0][0] == comment["id"]
        assert ('```suggestion' in patched[0][1]) == (comment["kind"] == "review")


def test_the_next_number_is_the_one_the_build_uses():
    import build_notes
    assert isinstance(build_notes.next_number(), int)
