"""Every dataset definition of this repository is read and written back by goldpan as the same definition.

This test lived in goldpan until 2026-11-05. It belongs here: it scans this repository's own definitions (`data_analysis/`, and the
examples of goldsluice while they are here), and goldpan, from PyPI, is the code under test.
"""
import tomllib
from pathlib import Path

import pytest

dataset = pytest.importorskip("goldpan.dataset")

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = sorted((ROOT / "goldsluice" / "examples").glob("*.dataset.toml")) + sorted((ROOT / "data_analysis").rglob("*.dataset.toml"))


def test_the_repository_has_definitions_to_check():
    assert DEFINITIONS, "no *.dataset.toml found under data_analysis/ (or goldsluice/examples/): did the folders move?"


@pytest.mark.parametrize("path", DEFINITIONS, ids=lambda p: p.name)
def test_every_definition_in_the_repository_is_written_back_as_the_same_definition(path):
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    assert tomllib.loads(dataset.dumps(raw, base=path.parent)) == raw
