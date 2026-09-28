import sys
from pathlib import Path

# python/ holds flat modules (pulse_quantities.py etc.), imported directly --
# not a package -- matching the sys.path-insertion convention used elsewhere
# (e.g. nrFanoII_paper2022's python/ba_bknd_lines.py). Make that importable
# for the tests regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
