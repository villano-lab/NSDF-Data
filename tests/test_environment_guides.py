"""The environment check and the student guides must name the same Python."""
import re
from pathlib import Path

import check_environment as ce

ROOT = Path(__file__).resolve().parents[1]


def test_expected_python_matches_the_setup_guide():
    """The number in check_environment must be the one the guides create the environment with."""
    gen = ROOT / "docs" / "students" / "src" / "gen.py"
    found = re.findall(r"conda create -n darkmatter_cli_env python=(\d+)\.(\d+)", gen.read_text(encoding="utf-8"))
    assert found, "gen.py has no conda create line"
    assert all((int(a), int(b)) == ce.EXPECTED_PYTHON for a, b in found)  # the setup guide and the updating guide
