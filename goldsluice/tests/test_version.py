"""goldsluice has a version of its own (RELEASING.md, "goldsluice's own version"): the same number in the three places that state it, well formed."""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def versions():
    cargo = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))["package"]["version"]
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    init = re.search(r'^__version__ = "([^"]+)"', (ROOT / "python" / "goldsluice" / "__init__.py").read_text(encoding="utf-8"), re.M)
    assert init, "python/goldsluice/__init__.py has no __version__ = \"X.Y.Z\""
    return cargo, pyproject, init.group(1)


def test_the_three_places_that_state_the_version_agree_and_it_is_well_formed():
    cargo, pyproject, init = versions()
    assert cargo == pyproject == init, f"Cargo.toml says {cargo}, pyproject.toml {pyproject}, __init__.py {init}: change all three together"
    assert re.fullmatch(r"\d+\.\d+\.\d+", cargo), f"{cargo!r} is not X.Y.Z"
