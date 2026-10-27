#!/usr/bin/env python
"""Build the Sphinx documentation of goldpan and goldsluice (sources in sphinx/) into docs/api/.

    python tools/build_docs.py              # build, replacing docs/api/ only if the build succeeded
    python tools/build_docs.py --strict     # the same, but a warning (a broken reference, a bad docstring) fails the build
    python tools/build_docs.py --check      # build into a temporary folder and write nothing (what pull requests run; strict)

Needs the packages of sphinx/requirements.txt, and the dependencies of the modules it documents (numpy, awkward, pyarrow, h5py,
uproot, lz4: `pip install -e "./python[archive,parquet,root,midas]"`). The Rust extension of goldsluice is not needed.
The pages in docs/api/ are generated: never edit them by hand. On pushes to develop and master the workflow
.github/workflows/docs.yml rebuilds and commits them.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sphinx"
OUT = ROOT / "docs" / "api"


def build(target: Path, *, strict: bool) -> int:
    with tempfile.TemporaryDirectory() as doctrees:
        cmd = [sys.executable, "-m", "sphinx", "-b", "html", "-d", doctrees, "-q", str(SOURCE), str(target)]
        if strict:
            cmd[3:3] = ["-W", "--keep-going"]
        return subprocess.call(cmd)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--strict", action="store_true", help="a warning fails the build")
    p.add_argument("--check", action="store_true", help="build in a temporary folder, write nothing (implies --strict)")
    args = p.parse_args(argv)
    strict = args.strict or args.check
    with tempfile.TemporaryDirectory() as tmp:
        built = Path(tmp) / "html"
        code = build(built, strict=strict)
        if code != 0:
            print(f"error: the documentation did not build (exit {code}); {OUT.relative_to(ROOT)} is unchanged", file=sys.stderr)
            return code
        if args.check:
            print("documentation builds")
            return 0
        (built / ".buildinfo").unlink(missing_ok=True)
        if OUT.exists():
            shutil.rmtree(OUT)
        shutil.copytree(built, OUT)
        (OUT / ".nojekyll").write_text("", encoding="utf-8")        # GitHub Pages must not process the underscore folders
    print(f"wrote {OUT.relative_to(ROOT)} ({sum(1 for _ in OUT.rglob('*.html'))} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
