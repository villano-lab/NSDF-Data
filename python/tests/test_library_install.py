"""Tests for the installable library (phase 1 of issue 71): python/pyproject.toml must list every library module, and
requirements.txt must install it, so that `import pulse_quantities` works from any folder."""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / "python"
NOT_LIBRARY = set()   # every *.py in python/ is a module of the library


def project():
    return tomllib.loads((PY / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_lists_every_library_module_and_nothing_else():
    on_disk = {p.stem for p in PY.glob("*.py")} - NOT_LIBRARY
    listed = set(project()["tool"]["setuptools"]["py-modules"])
    assert listed == on_disk, f"missing from pyproject: {sorted(on_disk - listed)}; not on disk: {sorted(listed - on_disk)}"


def test_library_has_a_semantic_version_and_numpy_dependency():
    meta = project()["project"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", meta["version"])
    assert "numpy" in meta["dependencies"]
    assert "h5py" in meta["optional-dependencies"]["archive"]


def test_requirements_installs_the_library_in_place():
    lines = [l.split("#")[0].strip() for l in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    assert any(l.startswith("-e ./python") for l in lines), "requirements.txt must contain a line `-e ./python[archive]`"


def test_every_module_is_imported_by_its_plain_name():
    """The flat names stay: notebooks and notes use `import pulse_cuts`, not a package path."""
    for name in project()["tool"]["setuptools"]["py-modules"]:
        assert "." not in name
        assert (PY / f"{name}.py").exists()


def test_the_environment_check_sees_the_library_that_requirements_installs():
    """requirements.txt installs the library whose name and version pyproject.toml gives, and check_environment pins it."""
    import check_environment as ce
    meta = project()["project"]
    assert meta["name"] == "goldpan"
    assert ce.library_pins(ROOT / "requirements.txt") == {"goldpan": meta["version"]}
