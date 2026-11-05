"""Tests for the installable library (phase 1 of issue 71): python/pyproject.toml must list every library module, and
requirements.txt must install it, so that `import pulse_quantities` works from any folder."""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "python"
NOT_LIBRARY = set()   # every *.py in python/ is a module of the library
ORIGINAL_MODULES = {"archive", "channels", "config", "cuts", "io", "operations", "quantities", "status"}


def project():
    return tomllib.loads((PY / "pyproject.toml").read_text(encoding="utf-8"))


def test_pyproject_lists_every_library_module_and_nothing_else():
    on_disk = {p.stem for p in PY.glob("*.py")} - NOT_LIBRARY
    listed = set(project()["tool"]["setuptools"]["py-modules"])
    assert listed == on_disk, f"missing from pyproject: {sorted(on_disk - listed)}; not on disk: {sorted(listed - on_disk)}"


def test_pyproject_installs_the_goldpan_package_with_every_module_of_it():
    """The code is the package `goldpan`; the flat `pulse_*.py` files are one-line aliases, listed as py-modules."""
    assert project()["tool"]["setuptools"]["packages"] == ["goldpan", "goldpan.adapters"]
    assert (PY / "goldpan" / "__init__.py").exists() and (PY / "goldpan" / "adapters" / "__init__.py").exists()
    flat = {m for m in project()["tool"]["setuptools"]["py-modules"] if m.startswith("pulse_")}
    # the flat aliases exist only for the eight modules of the first versions; new modules of the package (data, ...) have none
    assert {m[len("pulse_"):] for m in flat} == ORIGINAL_MODULES
    assert ORIGINAL_MODULES <= {p.stem for p in (PY / "goldpan").glob("*.py")}


def test_library_has_a_semantic_version_and_numpy_dependency():
    meta = project()["project"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", meta["version"])
    assert "numpy" in meta["dependencies"]
    assert "h5py" in meta["optional-dependencies"]["archive"]


def test_requirements_pins_goldpan_from_pypi_with_every_extra_the_guides_promise():
    """goldpan comes from PyPI (its home is github.com/villano-lab/goldpan); the extras bring h5py, pyarrow, uproot and lz4."""
    lines = [l.split("#")[0].strip() for l in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()]
    found = [re.fullmatch(r"goldpan\[([a-z,]+)\]==(\d+\.\d+\.\d+)", l) for l in lines if l.startswith("goldpan")]
    assert len(found) == 1 and found[0], "requirements.txt must have one line `goldpan[archive,parquet,root,midas]==X.Y.Z`"
    assert set(found[0].group(1).split(",")) == {"archive", "parquet", "root", "midas"}
    assert not any(l.startswith("-e") for l in lines), "the library is no longer installed in place from this repository"


def test_every_module_is_imported_by_its_plain_name():
    """The flat names stay: notebooks and notes use `import pulse_cuts`, not a package path."""
    for name in project()["tool"]["setuptools"]["py-modules"]:
        assert "." not in name
        assert (PY / f"{name}.py").exists()


def test_the_environment_check_reads_the_goldpan_pin_of_requirements():
    """check_environment pins goldpan like any other package: it reads `goldpan[extras]==X.Y.Z` by the plain name."""
    import check_environment as ce
    pins = ce.parse_requirements((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d+\.\d+\.\d+", pins.get("goldpan", ""))
