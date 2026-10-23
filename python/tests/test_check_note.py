"""Tests for tools/check_note.py: one command that runs the structure, pinned-link and number checks on a student note
and shows only what concerns that note."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_note as cn  # noqa: E402

NAME = "my-note.md"
PINS_OK = "All 34 pinned links resolve.\n"
STRUCTURE_OK = "3 note(s) valid.\n"
NUMBERS_OK = ("== notes/src/my-note.md\n  notebook: data_analysis/x/nb.ipynb @ abc1234\n"
              "  12 numbers: 12 found in output, 0 only in code, 0 NOT FOUND\n")
NUMBERS_ADVICE = ("== notes/src/my-note.md\n  notebook: data_analysis/x/nb.ipynb @ abc1234\n"
                  "  12 numbers: 9 found in output, 1 only in code, 2 NOT FOUND\n"
                  "    code only  line   12  1.6          (cell 3 has 1.6 in its code, not in its output)\n"
                  "    NOT FOUND  line   40  152.6        The ADC bin is 152.6 uV\n"
                  "    NOT FOUND  line   58  17           We found 17 events\n")


def runner_for(structure=(0, STRUCTURE_OK), pins=(0, PINS_OK), numbers=(0, NUMBERS_OK)):
    answers = {"build_notes.py": structure, "check_note_pins.py": pins, "check_note_numbers.py": numbers}

    def run(args, root=None):
        return answers[Path(args[0]).name]
    return run


def test_structure_keeps_only_the_lines_of_the_named_note():
    out = ("my-note.md: header field 'title' is missing or empty\n"
           "other-note.md: picture not found: notes/src/img/x.png\n"
           "2 note(s) with problems; nothing was built.\n")
    assert cn.structure_problems(out, "my-note.md") == ["header field 'title' is missing or empty"]
    assert cn.structure_problems(out, "third.md") == []


def test_pin_problems_join_the_link_and_the_reason_and_ignore_other_notes():
    out = ("notes/src/my-note.md: https://github.com/villano-lab/NSDF-Data/blob/develop/python/pulse_cuts.py\n"
           "    not pinned to a commit hash ('develop'). Link to the commit that produced the result.\n"
           "notes\\src\\other.md: https://github.com/villano-lab/NSDF-Data/blob/abc1234/gone.py\n"
           "    the file does not exist at that commit\n")
    mine = cn.pin_problems(out, "my-note.md")
    assert len(mine) == 1 and "blob/develop/python/pulse_cuts.py" in mine[0] and "not pinned" in mine[0]
    assert "gone.py" in cn.pin_problems(out, "other.md")[0]


def test_number_report_counts_what_is_not_found_and_problems():
    lines, not_found, problems = cn.number_report(NUMBERS_ADVICE)
    assert not_found == 2 and problems == 0
    assert all(not line.startswith("==") for line in lines)
    _, nf, pr = cn.number_report("== n.md\n  PROBLEM: the note links to no notebook\n  0 numbers: 0 found in output, 0 only in code, 0 NOT FOUND\n")
    assert (nf, pr) == (0, 1)


def test_everything_fine_passes():
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner_for())
    assert {k: v["status"] for k, v in result.items()} == {"structure": "ok", "pins": "ok", "numbers": "ok"}
    assert cn.exit_status(result) == 0
    assert cn.verdict(result) == "Result: ready for review."


def test_a_structure_problem_in_this_note_fails():
    runner = runner_for(structure=(1, f"{NAME}: status must be one of ['In progress']\n1 note(s) with problems; nothing was built.\n"))
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner)
    assert result["structure"]["status"] == "fail" and "status must be" in result["structure"]["lines"][0]
    assert cn.exit_status(result) == 1
    assert "fix the problems" in cn.verdict(result)


def test_problems_of_other_notes_do_not_fail_this_one():
    structure = (1, "other.md: header field 'id' is missing or empty\n1 note(s) with problems; nothing was built.\n")
    pins = (1, "notes/src/other.md: https://github.com/villano-lab/NSDF-Data/blob/develop/x.py\n    not pinned\n")
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner_for(structure=structure, pins=pins))
    assert result["structure"]["status"] == "ok" and result["pins"]["status"] == "ok"
    assert cn.exit_status(result) == 0


def test_a_pin_problem_in_this_note_fails():
    pins = (1, f"notes/src/{NAME}: https://github.com/villano-lab/NSDF-Data/blob/master/x.py\n    not pinned to a commit hash ('master')\n")
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner_for(pins=pins))
    assert result["pins"]["status"] == "fail" and "master" in result["pins"]["lines"][0]
    assert cn.exit_status(result) == 1


def test_a_tool_that_crashes_fails_instead_of_passing_silently():
    result = cn.check_note(f"notes/src/{NAME}", ["structure"], runner_for(structure=(1, "Traceback (most recent call last):\nValueError: boom\n")))
    assert result["structure"]["status"] == "fail" and "boom" in " ".join(result["structure"]["lines"])
    result = cn.check_note(f"notes/src/{NAME}", ["pins"], runner_for(pins=(1, "fatal: not a git repository\n")))
    assert result["pins"]["status"] == "fail"


def test_numbers_are_advice_unless_strict():
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner_for(numbers=(1, NUMBERS_ADVICE)))
    assert result["numbers"]["status"] == "advice" and result["numbers"]["not_found"] == 2
    assert cn.exit_status(result) == 0
    assert cn.exit_status(result, strict=True) == 1
    assert "Look at the numbers" in cn.verdict(result)
    text = cn.render(f"notes/src/{NAME}", result)
    assert "2 NOT FOUND" in text and "advice" in text and "152.6" in text


def test_the_checks_can_be_chosen():
    result = cn.check_note(f"notes/src/{NAME}", ["pins"], runner_for())
    assert list(result) == ["pins"]


def test_github_output_has_a_warning_for_each_number_and_an_error_for_a_problem():
    result = cn.check_note(f"notes/src/{NAME}", cn.CHECKS, runner_for(numbers=(1, NUMBERS_ADVICE)))
    notes, summary = cn.github_output(f"notes/src/{NAME}", result)
    assert "::warning file=notes/src/my-note.md,line=40::number 152.6 is not in the notebook output" in notes
    assert not any(n.startswith("::error") for n in notes)
    assert any("line 58" in s for s in summary)
    bad = cn.check_note(f"notes/src/{NAME}", ["structure"], runner_for(structure=(1, f"{NAME}: picture not found: x\n1 note(s) with problems\n")))
    assert any(n.startswith("::error file=notes/src/my-note.md::structure: picture not found") for n in cn.github_output(f"notes/src/{NAME}", bad)[0])


def test_main_exit_status_and_summary_file(tmp_path, monkeypatch, capsys):
    note = tmp_path / NAME
    note.write_text("# note\n", encoding="utf-8")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert cn.main([str(note), "--github"], runner=runner_for()) == 0
    assert "Result: ready for review." in capsys.readouterr().out
    assert "my-note.md" in summary.read_text(encoding="utf-8")
    assert cn.main([str(note)], runner=runner_for(numbers=(1, NUMBERS_ADVICE))) == 0
    assert cn.main([str(note), "--strict"], runner=runner_for(numbers=(1, NUMBERS_ADVICE))) == 1
    failing = runner_for(pins=(1, f"notes/src/{NAME}: https://github.com/villano-lab/NSDF-Data/blob/master/x.py\n    not pinned\n"))
    assert cn.main([str(note)], runner=failing) == 1


def test_main_refuses_a_missing_note_and_an_empty_choice(tmp_path, capsys):
    assert cn.main([str(tmp_path / "nope.md")], runner=runner_for()) == 2
    assert "note not found" in capsys.readouterr().out
    note = tmp_path / NAME
    note.write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        cn.main([str(note), "--only", "pins", "--skip", "pins"], runner=runner_for())
    with pytest.raises(SystemExit):
        cn.main([], runner=runner_for())


def test_changed_with_nothing_changed_says_so(capsys):
    assert cn.main(["--changed", "HEAD"], runner=runner_for()) == 0
    assert "No student notes changed." in capsys.readouterr().out


def test_it_prints_characters_a_windows_console_cannot_encode(tmp_path, monkeypatch, capsys):
    """A note quotes arrows and Greek letters; printing them to a cp1252 stdout used to crash the check."""
    import io
    note = tmp_path / "notes" / "src"
    note.mkdir(parents=True)
    (note / NAME).write_text("---\ntitle: x\n---\n", encoding="utf-8")
    numbers = ("== notes/src/my-note.md\n  notebook: data_analysis/x/nb.ipynb @ abc1234\n"
               "  12 numbers: 11 found in output, 0 only in code, 1 NOT FOUND\n"
               "    NOT FOUND  line   40  7            from \u03bc to \u2192 7 events\n")
    monkeypatch.setattr(cn, "ROOT", tmp_path)
    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    monkeypatch.setattr(sys, "stdout", console)
    status = cn.main([str(note / NAME)], runner=runner_for(numbers=(0, numbers)))
    console.flush()
    assert status == 0
    assert "7 events" in raw.getvalue().decode("utf-8")      # printed as UTF-8, not crashed
