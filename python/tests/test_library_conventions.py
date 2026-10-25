"""Rules from AGENTS.md that apply to every module of the `goldpan` package, checked automatically.

* every public function is tagged `@status(DONE)` or `@status(UNDER_DEVELOPMENT, ...)`;
* every public function has a docstring (the library reference page is built from them);
* every public function is named in at least one test file, so a new function cannot arrive
  without a test (this checks that a test mentions it, not that the test is any good).
"""
import importlib
import inspect
import re
from pathlib import Path

import pytest

PYTHON_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
# Library modules: the files of the package `goldpan`. `status` is the decorator itself, `legacy` builds the old flat
# names (the flat `pulse_*.py` files are one-line aliases of the package), and helpers such as check_environment.py
# are not part of the library proper.
MODULES = sorted("goldpan." + p.stem for p in (PYTHON_DIR / "goldpan").glob("*.py")
                 if p.stem not in {"__init__", "status", "legacy"})


def _public_functions(module):
    return [
        (name, obj) for name, obj in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == module.__name__
    ]


@pytest.mark.parametrize("modname", MODULES)
def test_every_public_function_has_a_status_tag(modname):
    module = importlib.import_module(modname)
    untagged = [name for name, f in _public_functions(module) if getattr(f, "status", None) is None]
    assert not untagged, f"{modname}: tag with @status(DONE) or @status(UNDER_DEVELOPMENT, note=...): {untagged}"


@pytest.mark.parametrize("modname", MODULES)
def test_every_public_function_has_a_docstring(modname):
    module = importlib.import_module(modname)
    bare = [name for name, f in _public_functions(module) if not (f.__doc__ or "").strip()]
    assert not bare, f"{modname}: add a docstring (first line = one-sentence summary): {bare}"


@pytest.mark.parametrize("modname", MODULES)
def test_every_public_function_is_mentioned_in_a_test(modname):
    module = importlib.import_module(modname)
    test_text = "\n".join(p.read_text(encoding="utf-8") for p in TESTS_DIR.glob("test_*.py")
                          if p.name != Path(__file__).name)
    missing = [name for name, _ in _public_functions(module)
               if not re.search(rf"\b{re.escape(name)}\b", test_text)]
    assert not missing, f"{modname}: no test mentions these functions: {missing}"
