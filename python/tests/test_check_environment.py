import io
import re
from pathlib import Path

import pytest

import check_environment as ce


def test_parse_requirements_pins_names_and_comments():
    text = "nsdf-dark-matter==0.3.0\n\n# a comment\nnumpy==2.2.6  # pinned\npytest\n"
    assert ce.parse_requirements(text) == {"nsdf-dark-matter": "0.3.0", "numpy": "2.2.6", "pytest": None}


def test_no_problems_when_everything_matches():
    pins = {"numpy": "2.2.6", "pytest": None}
    lookup = {"numpy": "2.2.6", "pytest": "9.1.1"}.get
    assert ce.find_problems(pins, python_version=(3, 12), lookup=lookup) == []


def test_old_python_is_reported_with_both_versions():
    problems = ce.find_problems({}, python_version=(3, 10), expected_python=(3, 12))
    assert len(problems) == 1
    assert "3.10" in problems[0] and "3.12" in problems[0]


def test_patch_version_of_python_is_ignored():
    assert ce.find_problems({}, python_version=(3, 12, 15), expected_python=(3, 12)) == []


def test_wrong_version_and_missing_package_are_reported():
    pins = {"numpy": "2.2.6", "h5py": None, "matplotlib": "3.10.7"}
    lookup = {"numpy": "1.26.4", "matplotlib": "3.10.7"}.get
    problems = ce.find_problems(pins, python_version=(3, 12), lookup=lookup)
    assert any("numpy is 1.26.4" in p and "2.2.6" in p for p in problems)
    assert any("h5py is not installed" in p for p in problems)
    assert not any("matplotlib" in p for p in problems)


def test_check_prints_ok_and_returns_no_problems(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("pytest\n", encoding="utf-8")  # pytest is installed: we are running under it
    out = io.StringIO()
    problems = ce.check(requirements=req, stream=out)
    if tuple(__import__("sys").version_info[:2]) == ce.EXPECTED_PYTHON:
        assert problems == []
        assert out.getvalue().startswith("Environment OK")
    else:  # an older Python still warns, never raises
        assert problems and out.getvalue().startswith("WARNING")


def test_check_warns_and_never_raises_on_a_mismatch(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("pytest==0.0.1\nnot-a-real-package-xyz\n", encoding="utf-8")
    out = io.StringIO()
    problems = ce.check(requirements=req, stream=out)
    text = out.getvalue()
    assert text.startswith("WARNING")
    assert any("pytest is" in p for p in problems)
    assert any("not-a-real-package-xyz is not installed" in p for p in problems)
    assert ce.GUIDE_URL in text and "only a warning" in text


def test_check_without_requirements_file_says_so_and_still_checks_python(tmp_path):
    out = io.StringIO()
    ce.check(requirements=tmp_path / "missing.txt", stream=out)
    assert "requirements.txt was not found" in out.getvalue()


def test_main_exits_zero_unless_strict(tmp_path, monkeypatch):
    monkeypatch.setattr(ce, "REQUIREMENTS", tmp_path / "missing.txt")
    monkeypatch.setattr(ce, "check", lambda: ["something differs"])
    assert ce.main([]) == 0
    assert ce.main(["--strict"]) == 1
    monkeypatch.setattr(ce, "check", lambda: [])
    assert ce.main(["--strict"]) == 0


def test_expected_python_matches_the_setup_guide():
    """The number in this module must be the one the guides create the environment with."""
    gen = Path(__file__).resolve().parents[2] / "docs" / "students" / "src" / "gen.py"
    found = re.findall(r"conda create -n darkmatter_cli_env python=(\d+)\.(\d+)", gen.read_text(encoding="utf-8"))
    assert found, "gen.py has no conda create line"
    assert all((int(a), int(b)) == ce.EXPECTED_PYTHON for a, b in found)  # the setup guide and the updating guide
