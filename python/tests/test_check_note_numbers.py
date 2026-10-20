"""Tests for tools/check_note_numbers.py: the numbers in a student note must be found in the output of its notebook."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_note_numbers as cnn  # noqa: E402

URL = "https://github.com/villano-lab/NSDF-Data/blob/{sha}/data_analysis/R76/student/x/nb.ipynb"


def nb(stream="", result="", source="x = 1\n"):
    outputs = []
    if stream:
        outputs.append({"output_type": "stream", "name": "stdout", "text": stream})
    if result:
        outputs.append({"output_type": "execute_result", "data": {"text/plain": result}, "metadata": {}, "execution_count": 1})
    return {"cells": [{"cell_type": "code", "source": source, "outputs": outputs, "metadata": {}, "execution_count": 1}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5}


def num(text):
    return cnn.tokens(text)[0]


def find(note_text, all_small=False):
    return [(t.text, line) for line, t, _ in cnn.note_numbers(note_text, all_small)]


def test_tokens_read_decimals_separators_exponents_and_percent():
    assert num("1,517").value == 1517
    assert num("0.52").places == 2
    assert num("3.2e-3").value == cnn.Decimal("0.0032")
    assert num("45%").pct


def test_names_with_digits_are_not_numbers():
    assert cnn.tokens("series 07221203_2025, detector S104 and v1.2") == []


def test_rounding_to_the_digits_shown():
    assert cnn.matches(num("0.52"), num("0.5213"))
    assert not cnn.matches(num("0.53"), num("0.5213"))
    assert cnn.matches(num("179"), num("179"))
    assert cnn.matches(num("179"), num("179.4"))


def test_percent_and_significant_figures():
    assert cnn.matches(num("45%"), num("0.4512"))
    assert cnn.matches(num("5200"), num("5213.4"))
    assert not cnn.matches(num("5300"), num("5213.4"))


def test_note_text_skips_header_code_links_labels_dates_and_years():
    text = (
        "---\nid: \"TBD\"\ndate: \"2026-10-05\"\ndescription: \"has 999 in it\"\n---\n"
        "See [Note 2](https://x.org/note-02.html) and Figure 3 on 5 October 2026.\n"
        "```\nx = 12345\n```\n"
        "Use `pulses[1234]`. We kept 179 traces.\n"
        "1. A list item\n"
        "Skipped 4242 here. <!-- numbers-ok -->\n"
        "## References\n"
        "1. Someone, arXiv 1101.5205\n"
    )
    assert find(text) == [("179", 10)]


def test_small_whole_numbers_are_skipped_unless_asked():
    assert find("Channel 0 has 3 plots and 12 traces.") == [("12", 1)]
    assert ("3", 1) in find("Channel 0 has 3 plots and 12 traces.", all_small=True)


def test_captions_are_checked_but_image_paths_are_not():
    text = "![**Figure 1.** The 141 randoms](img/fig1-2026.png)\n"
    assert find(text) == [("141", 1)]


def test_notebook_numbers_split_output_from_code():
    outputs, code, has_output = cnn.notebook_numbers(nb(stream="n = 179\n", result="0.5213", source="cut = 1.25\n# 777\n"))
    assert has_output
    assert [t.text for _, t in outputs] == ["179", "0.5213"]
    assert [t.text for _, t in code] == ["1.25"]


@pytest.fixture
def repo(tmp_path):
    """A repository holding a notebook at a commit, and notes that link to it."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
    git("init", "-q")
    d = tmp_path / "data_analysis" / "R76" / "student" / "x"
    d.mkdir(parents=True)
    (d / "nb.ipynb").write_text(json.dumps(nb(stream="kept 179 traces, mean 0.5213, 45.1 percent\n", source="cut = 7.5\n")), encoding="utf-8")
    git("add", "-A")
    git("-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "-m", "nb")
    sha = git("rev-parse", "--short=7", "HEAD")
    (tmp_path / "notes" / "src").mkdir(parents=True)
    return tmp_path, sha


def write_note(repo, body):
    root, sha = repo
    p = root / "notes" / "src" / "my-note.md"
    p.write_text(f"---\nid: \"TBD\"\n---\n\n[nb]({URL.format(sha=sha)})\n\n{body}\n", encoding="utf-8")
    return p


def test_check_note_reports_found_code_only_and_missing(repo, capsys):
    p = write_note(repo, "We kept 179 traces with mean 0.52. The cut was 7.5 and we found 4321 events.")
    bad = cnn.check_note(repo[0], p)
    out = capsys.readouterr().out
    assert bad == 1
    assert "3 numbers" not in out and "4 numbers: 2 found in output, 1 only in code, 1 NOT FOUND" in out
    assert "NOT FOUND" in out and "4321" in out
    assert "code only" in out and "7.5" in out


def test_check_note_clean_note_returns_zero(repo, capsys):
    p = write_note(repo, "We kept 179 traces and the mean was 0.52.")
    assert cnn.check_note(repo[0], p) == 0
    assert "0 NOT FOUND" in capsys.readouterr().out


def test_note_without_a_notebook_link_is_a_problem(tmp_path, capsys):
    p = tmp_path / "n.md"
    p.write_text("---\nid: \"TBD\"\n---\nWe kept 179 traces.\n", encoding="utf-8")
    assert cnn.check_note(tmp_path, p) >= 1
    assert "links to no notebook" in capsys.readouterr().out


def test_explicit_notebook_overrides_the_links(tmp_path, capsys):
    path = tmp_path / "other.ipynb"
    path.write_text(json.dumps(nb(stream="179\n")), encoding="utf-8")
    p = tmp_path / "n.md"
    p.write_text("---\nid: \"TBD\"\n---\nWe kept 179 traces.\n", encoding="utf-8")
    assert cnn.check_note(tmp_path, p, explicit=[path]) == 0


def test_notebook_without_saved_output_is_flagged(tmp_path, capsys):
    path = tmp_path / "empty.ipynb"
    path.write_text(json.dumps(nb()), encoding="utf-8")
    p = tmp_path / "n.md"
    p.write_text("---\nid: \"TBD\"\n---\nWe kept 179 traces.\n", encoding="utf-8")
    cnn.check_note(tmp_path, p, explicit=[path])
    assert "NO SAVED OUTPUT" in capsys.readouterr().out


def test_main_exit_status(repo):
    p = write_note(repo, "We found 4321 events.")
    assert cnn.main([str(p), "--root", str(repo[0])]) == 1
    p = write_note(repo, "We kept 179 traces.")
    assert cnn.main([str(p), "--root", str(repo[0])]) == 0
