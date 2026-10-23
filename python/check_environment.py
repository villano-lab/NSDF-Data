"""Check that this Python environment is the one the NSDF-Data guides expect.

It compares the Python version and the packages listed in `requirements.txt` (at the top of the repository)
with what is installed (including the pulse library in `python/`, which `requirements.txt` installs in place),
and says what differs and where to read how to fix it. It only ever **warns**: it
never raises and never stops a notebook, so a student on an older setup can still finish their work.

In a notebook (after the library folder is on `sys.path`, as in the first-analysis guide)::

    import check_environment
    check_environment.check()

From a terminal, in the repository's `python` folder::

    python check_environment.py            # prints OK or the warnings; always exits 0
    python check_environment.py --strict   # exits 1 if anything differs (used by CI)

Only the standard library is used, so it works in any environment, including an old one.
"""
import re
import sys
from importlib import metadata
from pathlib import Path

from pulse_status import status, DONE

# The Python version the guides create the environment with. Keep it in step with the guides' `conda create`
# line (docs/students/src/gen.py), `.devcontainer/devcontainer.json` and the CI workflow: see AGENTS.md. CI checks that
# this number matches the guides.
EXPECTED_PYTHON = (3, 12)

GUIDE_URL = "https://villano-lab.github.io/NSDF-Data/#maintenance"
REQUIREMENTS = Path(__file__).resolve().parent.parent / "requirements.txt"


@status(DONE)
def parse_requirements(text: str) -> dict:
    """`{package name: pinned version or None}` from the text of a requirements file.

    A line `numpy==2.2.6` gives `{"numpy": "2.2.6"}`; a bare name such as `pytest` gives `{"pytest": None}`.
    Blank lines, `#` comments and option lines (such as `-e ./python`) are ignored.
    """
    pins = {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):    # blank, or an option such as `-e ./python`
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            pins[name.strip()] = version.strip()
        else:
            pins[line] = None
    return pins


@status(DONE)
def library_pins(requirements=REQUIREMENTS) -> dict:
    """`{name: version}` of the library that `requirements.txt` installs in place (a line like `-e ./python[archive]`).

    The name and version are read from that folder's `pyproject.toml`, so `check` can say when the pulse library is not
    installed, or is an older version than the checkout. Returns `{}` if there is no such line or the file is unreadable.
    Plain text matching is used (no `tomllib`) so that this works in an old environment too.
    """
    base = Path(requirements).resolve().parent
    try:
        lines = Path(requirements).read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    pins = {}
    for line in lines:
        m = re.match(r"-e\s+(\S+?)(\[[^\]]*\])?$", line.split("#")[0].strip())
        if not m:
            continue
        try:
            text = (base / m.group(1) / "pyproject.toml").read_text(encoding="utf-8")
        except OSError:
            continue
        name = re.search(r'(?m)^name\s*=\s*"([^"]+)"', text)
        version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
        if name and version:
            pins[name.group(1)] = version.group(1)
    return pins


@status(DONE)
def installed_version(name: str):
    """The installed version of a package, or `None` if it is not installed."""
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


@status(DONE)
def find_problems(pins: dict, python_version=None, expected_python=EXPECTED_PYTHON, lookup=installed_version) -> list:
    """What differs from what the guides expect, as a list of plain sentences (empty if nothing).

    `python_version` is a `(major, minor)` pair (default: the running Python); `lookup(name)` returns an installed
    version or `None` (default: `installed_version`). Both can be replaced, which is how the tests use it.
    """
    if python_version is None:
        python_version = tuple(sys.version_info[:2])
    problems = []
    if tuple(python_version[:2]) != tuple(expected_python):
        problems.append("Python is %d.%d, but the guides now use Python %d.%d." % (
            python_version[0], python_version[1], expected_python[0], expected_python[1]))
    for name, wanted in pins.items():
        have = lookup(name)
        if have is None:
            problems.append("%s is not installed%s." % (name, " (requirements.txt wants %s)" % wanted if wanted else ""))
        elif wanted is not None and have != wanted:
            problems.append("%s is %s, but requirements.txt wants %s." % (name, have, wanted))
    return problems


@status(DONE)
def check(requirements=REQUIREMENTS, stream=None) -> list:
    """Print whether this environment matches the guides, and return the list of problems (empty if it does).

    Warning only: this never raises. If `requirements.txt` cannot be found, only the Python version is checked,
    and it says so.
    """
    out = stream if stream is not None else sys.stdout
    pins, note = {}, None
    try:
        pins = parse_requirements(Path(requirements).read_text(encoding="utf-8"))
    except OSError:
        note = "requirements.txt was not found, so only the Python version was checked."
    pins.update(library_pins(requirements))   # the pulse library in python/, installed in place
    problems = find_problems(pins)
    version = "%d.%d.%d" % tuple(sys.version_info[:3])
    if not problems:
        print("Environment OK: Python %s%s." % (
            version, ", and the %d packages in requirements.txt match" % len(pins) if pins else ""), file=out)
    else:
        print("WARNING: your setup is out of date (Python %s)." % version, file=out)
        for p in problems:
            print("  - " + p, file=out)
        print("  This is only a warning, and you can keep working. To fix it, follow 'Updating your setup': " + GUIDE_URL,
              file=out)
    if note:
        print("  Note: " + note, file=out)
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    problems = check()
    return 1 if (problems and "--strict" in argv) else 0


if __name__ == "__main__":
    sys.exit(main())
