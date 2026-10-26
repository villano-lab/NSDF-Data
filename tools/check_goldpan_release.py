"""Check the tag of a library release before it is published to PyPI (used by .github/workflows/publish-goldpan.yml).

    python tools/check_goldpan_release.py goldpan-v0.2.0

The library `goldpan` (python/) has a version of its own (RELEASING.md, "The library's own version"), so its tags are
`goldpan-vX.Y.Z`, not the project's `vX.Y.Z`. Before anything is uploaded the tag must agree with the code:

* it has the form `goldpan-vX.Y.Z`;
* `python/pyproject.toml` has version `X.Y.Z`;
* CHANGELOG.md says `goldpan X.Y.Z` in a released section (not under `[Unreleased]`), as RELEASING.md asks for every release
  that changes the library.

Prints the problems and exits 1 if there are any; prints the version and exits 0 if not. `--version-only TAG` prints just the
version of a well-formed tag.
"""
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = re.compile(r"^goldpan-v(\d+\.\d+\.\d+)$")


def version_of(tag: str):
    """The version in a `goldpan-vX.Y.Z` tag, or None if the tag does not have that form."""
    m = TAG.match(tag)
    return m.group(1) if m else None


def released_changelog(text: str) -> str:
    """CHANGELOG.md without its `[Unreleased]` section."""
    parts = re.split(r"(?m)^## \[", text)
    return "## [".join(p for p in parts if not p.startswith("Unreleased]"))


def problems(tag: str, root: Path = None) -> list:
    root = root or ROOT
    version = version_of(tag)
    if version is None:
        return [f"{tag!r} is not a library tag: use goldpan-vX.Y.Z (the project's own tags, vX.Y.Z, are not published to PyPI)"]
    found = []
    declared = tomllib.loads((root / "python" / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if declared != version:
        found.append(f"python/pyproject.toml says version {declared}, the tag says {version}")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"\bgoldpan {re.escape(version)}\b", released_changelog(changelog)):
        found.append(f"CHANGELOG.md has no line 'goldpan {version}' in a released section (RELEASING.md, \"The library's own version\")")
    return found


def main(argv) -> int:
    args = argv[1:]
    if len(args) == 2 and args[0] == "--version-only":
        version = version_of(args[1])
        if version is None:
            print(problems(args[1])[0], file=sys.stderr)
            return 1
        print(version)
        return 0
    if len(args) != 1:
        print(__doc__)
        return 2
    found = problems(args[0])
    for line in found:
        print(f"ERROR: {line}")
    if not found:
        print(f"{args[0]}: ready to publish goldpan {version_of(args[0])}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
