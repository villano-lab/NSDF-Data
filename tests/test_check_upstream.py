"""Tests for tools/check_upstream.py (offline parts) and for the places that quote the pinned NSDF versions."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_upstream as cu  # noqa: E402


def test_parse_pins_reads_equals_lines_only():
    text = "nsdf-dark-matter==0.3.0\nNSDF_Dark_Matter_CLI==0.6.0  # comment\nh5py\n# numpy==1\n"
    assert cu.parse_pins(text) == {"nsdf-dark-matter": "0.3.0", "nsdf-dark-matter-cli": "0.6.0"}


def test_versions_compare_as_numbers_not_text():
    assert cu.is_newer("0.10.0", "0.9.0")
    assert cu.is_newer("0.6.0", "0.5.0")
    assert not cu.is_newer("0.5.0", "0.5.0")
    assert not cu.is_newer("0.4.9", "0.5.0")


def test_a_release_candidate_is_older_than_its_release():
    assert cu.is_newer("0.6.0", "0.6.0rc1")


def test_guides_quote_the_pinned_cli_version():
    """The setup and Codespaces guides show `NSDF Dark Matter CLI: X`; X must be the version in requirements.txt."""
    pins = cu.parse_pins((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    cli = pins["nsdf-dark-matter-cli"]
    for rel in ("docs/students/src/gen.py", "docs/students/src/codespaces.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        shown = re.findall(r"NSDF Dark Matter CLI: (\d+\.\d+\.\d+)", text)
        assert shown, f"{rel} no longer shows the CLI version"
        assert set(shown) == {cli}, f"{rel} shows {sorted(set(shown))}, requirements.txt pins {cli}"


def test_codespaces_fallback_installs_from_the_list_not_from_a_copy_of_it():
    """The Codespaces guide must not repeat package versions by hand: they would drift from requirements.txt."""
    text = (ROOT / "docs/students/src/codespaces.md").read_text(encoding="utf-8")
    assert "python -m pip install -r requirements.txt" in text
    assert not re.search(r"pip install [^\n]*==", text), "codespaces.md lists versions by hand: say `pip install -r requirements.txt`"
