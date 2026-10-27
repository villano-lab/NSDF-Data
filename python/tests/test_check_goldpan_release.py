"""Tests for tools/check_goldpan_release.py: the tag of a library release must agree with the code before it is published."""
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_goldpan_release as cgr  # noqa: E402

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- goldpan 0.3.0 will have something.

## [0.10.0] - 2026-11-01

- goldpan 0.2.0: the adapters.

## [0.9.0] - 2026-10-23
"""


def tree(tmp_path, version="0.2.0", changelog=CHANGELOG):
    (tmp_path / "python").mkdir(exist_ok=True)
    (tmp_path / "python" / "pyproject.toml").write_text(f'[project]\nname = "goldpan"\nversion = "{version}"\n', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return tmp_path


def test_version_of_accepts_only_library_tags():
    assert cgr.version_of("goldpan-v0.2.0") == "0.2.0" and cgr.version_of("goldpan-v10.20.30") == "10.20.30"
    for bad in ("v0.2.0", "goldpan-0.2.0", "goldpan-v0.2", "goldpan-v0.2.0rc1", "goldpan-v0.2.0-1", "xgoldpan-v0.2.0", ""):
        assert cgr.version_of(bad) is None, bad


def test_a_consistent_release_has_no_problems(tmp_path):
    assert cgr.problems("goldpan-v0.2.0", tree(tmp_path)) == []


def test_a_project_tag_is_refused_with_a_hint(tmp_path):
    (msg,) = cgr.problems("v0.10.0", tree(tmp_path))
    assert "goldpan-vX.Y.Z" in msg and "not published" in msg


def test_a_tag_that_disagrees_with_pyproject_is_refused(tmp_path):
    (msg,) = cgr.problems("goldpan-v0.2.0", tree(tmp_path, version="0.1.0"))
    assert "0.1.0" in msg and "0.2.0" in msg and "pyproject" in msg


def test_the_changelog_line_must_be_in_a_released_section(tmp_path):
    assert cgr.problems("goldpan-v0.3.0", tree(tmp_path, version="0.3.0"))                 # only under [Unreleased]
    assert cgr.problems("goldpan-v0.4.0", tree(tmp_path, version="0.4.0"))                 # nowhere
    assert cgr.problems("goldpan-v0.2.0", tree(tmp_path, changelog="## [1.0.0]\n\n- goldpan 0.20.0\n"))   # another version
    assert cgr.problems("goldpan-v0.2.0", tree(tmp_path, changelog="## [Unreleased]\n\n- goldpan 0.2.0\n"))


def test_the_line_may_have_the_name_in_backticks_as_the_changelog_writes_it(tmp_path):
    log = "## [Unreleased]\n\n## [0.10.0] - 2026-10-26\n\n`goldpan` 0.2.0: new modules.\n"
    assert cgr.problems("goldpan-v0.2.0", tree(tmp_path, changelog=log)) == []


def test_both_problems_are_reported_together(tmp_path):
    assert len(cgr.problems("goldpan-v0.9.9", tree(tmp_path))) == 2


def test_main_prints_and_returns_the_exit_code(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(cgr, "ROOT", tree(tmp_path))
    assert cgr.main(["x", "--version-only", "goldpan-v1.2.3"]) == 0 and capsys.readouterr().out.strip() == "1.2.3"
    assert cgr.main(["x", "--version-only", "v1.2.3"]) == 1
    assert cgr.main(["x", "goldpan-v0.2.0"]) == 0 and "ready to publish goldpan 0.2.0" in capsys.readouterr().out
    assert cgr.main(["x", "goldpan-v0.5.0"]) == 1 and "ERROR" in capsys.readouterr().out
    assert cgr.main(["x"]) == 2


def test_the_real_repository_is_consistent_with_its_own_tag_rule():
    """The version in pyproject is well formed, so a tag can be made from it (the changelog line comes with the release)."""
    version = tomllib.loads((ROOT / "python" / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert cgr.version_of(f"goldpan-v{version}") == version


def test_the_workflow_publishes_only_from_tags_with_a_trusted_publisher():
    text = (ROOT / ".github" / "workflows" / "publish-goldpan.yml").read_text(encoding="utf-8")
    assert 'tags: ["goldpan-v*"]' in text and "id-token: write" in text and "environment:" in text
    assert "if: github.ref_type == 'tag'" in text and "pypa/gh-action-pypi-publish" in text
    for forbidden in ("password:", "PYPI_TOKEN", "secrets."):
        assert forbidden not in text, f"the workflow must not use {forbidden}: PyPI trusts the workflow, no token is stored"
