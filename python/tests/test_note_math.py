"""Formulas in a student note: pandoc draws them as MathML on the published page, and the number checker does not
look inside them."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import build_notes  # noqa: E402
import check_note_numbers as cnn  # noqa: E402

NOTE = '---\nid: "TBD"\n---\n'


def numbers(text):
    return [(line, tok.text) for line, tok, _ in cnn.note_numbers(NOTE + text)]


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is not installed")
def test_inline_and_display_formulas_become_mathml():
    html = build_notes.to_html("Time $\\Delta t = 1.6$ here.\n\n$$\nS = \\frac{a}{b}\n$$\n")
    assert html.count("<math") == 2
    assert 'display="block"' in html
    assert "\\(" not in html and "\\[" not in html             # no raw TeX is left for the reader to see


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc is not installed")
def test_a_note_without_formulas_is_unchanged_by_the_option():
    html = build_notes.to_html("A plain sentence with 3 numbers, and $5 and $7 in it.\n")
    assert "<math" not in html and "$5 and $7" in html


def test_numbers_inside_formulas_are_not_checked():
    assert numbers("A formula $10^{-6}$ and $x = 2.5$ in a line with 12 events.\n") == [(4, "12")]


def test_a_display_formula_over_several_lines_is_skipped_and_line_numbers_still_match():
    text = "Before 11.\n\n$$\nS = 44.5 \\cdot\n  77.7\n$$\n\nAfter 22.\n"
    assert numbers(text) == [(4, "11"), (11, "22")]


def test_dollar_amounts_are_not_formulas():
    assert numbers("It costs $50 and $70 in total, 33 times.\n") == [(4, "50"), (4, "70"), (4, "33")]
