"""Tests for tools/check_goldsluice_release.py: the tag of a goldsluice release must agree with the code before it is published."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import check_goldsluice_release as cgr  # noqa: E402

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- goldsluice 0.3.0 will have something.

## [0.11.0] - 2026-11-05

- goldsluice 0.1.0: the first release.

## [0.10.0] - 2026-11-01
"""


def tree(tmp_path, cargo="0.1.0", pyproject="0.1.0", init="0.1.0", changelog=CHANGELOG):
    pkg = tmp_path / "goldsluice" / "python" / "goldsluice"
    pkg.mkdir(parents=True, exist_ok=True)
    (tmp_path / "goldsluice" / "Cargo.toml").write_text(f'[package]\nname = "goldsluice"\nversion = "{cargo}"\n', encoding="utf-8")
    (tmp_path / "goldsluice" / "pyproject.toml").write_text(f'[project]\nname = "goldsluice"\nversion = "{pyproject}"\n', encoding="utf-8")
    (pkg / "__init__.py").write_text(f'"""goldsluice."""\n__version__ = "{init}"\n', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return tmp_path


def test_version_of_accepts_only_goldsluice_tags():
    assert cgr.version_of("goldsluice-v0.1.0") == "0.1.0" and cgr.version_of("goldsluice-v10.20.30") == "10.20.30"
    for bad in ("v0.1.0", "goldpan-v0.1.0", "goldsluice-0.1.0", "goldsluice-v0.1", "goldsluice-v0.1.0rc1", "xgoldsluice-v0.1.0", ""):
        assert cgr.version_of(bad) is None, bad


def test_a_consistent_release_has_no_problems(tmp_path):
    assert cgr.problems("goldsluice-v0.1.0", tree(tmp_path)) == []


def test_other_tags_are_refused_with_a_hint(tmp_path):
    (msg,) = cgr.problems("goldpan-v0.3.0", tree(tmp_path))
    assert "goldsluice-vX.Y.Z" in msg


def test_each_of_the_three_places_must_agree_with_the_tag(tmp_path):
    for place in ("cargo", "pyproject", "init"):
        (msg,) = cgr.problems("goldsluice-v0.1.0", tree(tmp_path, **{place: "0.0.9"}))
        assert "0.0.9" in msg and "0.1.0" in msg


def test_the_changelog_line_must_be_in_a_released_section(tmp_path):
    assert cgr.problems("goldsluice-v0.3.0", tree(tmp_path, cargo="0.3.0", pyproject="0.3.0", init="0.3.0"))     # only under [Unreleased]
    assert cgr.problems("goldsluice-v0.1.0", tree(tmp_path, changelog="## [1.0.0]\n\n- goldsluice 0.10.0\n"))   # another version


def test_the_line_may_have_the_name_in_backticks(tmp_path):
    log = "## [Unreleased]\n\n## [0.11.0] - 2026-11-05\n\n`goldsluice` 0.1.0: the kernels.\n"
    assert cgr.problems("goldsluice-v0.1.0", tree(tmp_path, changelog=log)) == []


def test_main_prints_and_returns_the_exit_code(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(cgr, "ROOT", tree(tmp_path))
    assert cgr.main(["x", "--version-only", "goldsluice-v1.2.3"]) == 0 and capsys.readouterr().out.strip() == "1.2.3"
    assert cgr.main(["x", "--version-only", "v1.2.3"]) == 1
    assert cgr.main(["x", "goldsluice-v0.1.0"]) == 0 and "ready to publish goldsluice 0.1.0" in capsys.readouterr().out
    assert cgr.main(["x", "goldsluice-v0.5.0"]) == 1 and "ERROR" in capsys.readouterr().out
    assert cgr.main(["x"]) == 2


def test_the_real_repository_has_one_well_formed_version():
    versions = set(cgr.declared_versions(ROOT).values())
    assert len(versions) == 1 and cgr.version_of(f"goldsluice-v{versions.pop()}")


def test_the_workflow_publishes_only_from_tags_with_a_trusted_publisher():
    text = (ROOT / ".github" / "workflows" / "publish-goldsluice.yml").read_text(encoding="utf-8")
    assert 'tags: ["goldsluice-v*"]' in text and "id-token: write" in text and "environment:" in text
    assert "if: github.ref_type == 'tag'" in text and "pypa/gh-action-pypi-publish" in text
    for forbidden in ("password:", "PYPI_TOKEN", "secrets."):
        assert forbidden not in text, f"the workflow must not use {forbidden}: PyPI trusts the workflow, no token is stored"
