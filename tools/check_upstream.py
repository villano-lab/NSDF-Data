#!/usr/bin/env python3
"""Compare the NSDF packages pinned in requirements.txt with what the Nexus-DM team has published.

    python tools/check_upstream.py            # print a table; always exits 0
    python tools/check_upstream.py --strict   # exit 1 if a pinned NSDF package has a newer release

The NSDF software (the `nsdf-cli` command and the `nsdf_dark_matter` library, formerly NSDF-SLAC, now
Nexus-DM at https://github.com/nsdf-fabric/nexus-dm) is developed actively and this project depends heavily
on it, so we pin exact versions. This script is the first step of the procedure in RELEASING.md,
"When the NSDF software updates". It only reads: PyPI and the public GitHub releases. Standard library only;
needs an internet connection.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ("nsdf-dark-matter", "nsdf-dark-matter-cli")
UPSTREAM_REPO = "nsdf-fabric/nexus-dm"


def parse_pins(text):
    """{name: version} for the `name==version` lines of a requirements file."""
    pins = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*==\s*([^\s#]+)", line)
        if m:
            pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def version_key(version):
    """Sort key of a version such as 0.6.0 (numbers only; a suffix like rc1 sorts as lower)."""
    m = re.match(r"\d+(?:\.\d+)*", version.strip().lstrip("v"))
    nums = [int(n) for n in m.group(0).split(".")] if m else [0]
    rest = version.strip().lstrip("v")[m.end():] if m else version
    return tuple(nums + [0] * (4 - len(nums))) + (0 if re.search(r"[A-Za-z]", rest) else 1,)


def is_newer(latest, pinned):
    return version_key(latest) > version_key(pinned)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NSDF-Data check_upstream", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def pypi_latest(package):
    """(latest version, upload date) of a package on PyPI."""
    data = fetch_json(f"https://pypi.org/pypi/{package}/json")
    version = data["info"]["version"]
    files = data["releases"].get(version) or []
    date = max((f["upload_time"][:10] for f in files), default="?")
    return version, date


def github_releases(repo, count=3):
    """[(tag, date)] of the newest releases of a public GitHub repository."""
    data = fetch_json(f"https://api.github.com/repos/{repo}/releases?per_page={count}")
    return [(r["tag_name"], (r.get("published_at") or "")[:10]) for r in data]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if a pinned NSDF package has a newer release")
    args = ap.parse_args(argv)

    pins = parse_pins((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    newer = False
    print(f"{'package':<24}{'pinned':<10}{'latest on PyPI':<22}")
    for pkg in PACKAGES:
        pinned = pins.get(pkg, "(not pinned)")
        try:
            latest, date = pypi_latest(pkg)
        except Exception as e:                      # offline, or PyPI unreachable
            print(f"{pkg:<24}{pinned:<10}could not reach PyPI: {e}")
            continue
        flag = ""
        if pkg in pins and is_newer(latest, pinned):
            flag, newer = "   <- newer release", True
        print(f"{pkg:<24}{pinned:<10}{latest} ({date}){flag}")

    print(f"\nNewest GitHub releases of {UPSTREAM_REPO} (the repository tag is not the package version):")
    try:
        for tag, date in github_releases(UPSTREAM_REPO):
            print(f"  {tag:<10}{date}")
    except Exception as e:
        print(f"  could not reach GitHub: {e}")
    print(f"  Release notes: https://github.com/{UPSTREAM_REPO}/releases")
    if newer:
        print("\nA pinned package has a newer release. Follow RELEASING.md, 'When the NSDF software updates'.")
    return 1 if (args.strict and newer) else 0


if __name__ == "__main__":
    sys.exit(main())
