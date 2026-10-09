"""Run the Python code blocks of the first-analysis student guide and check the numbers.

Usage (from data_analysis/R76/notebooks, with the environment active and the data downloaded):

    python ../../.github/scripts/run_guide_code.py ../../docs/students/src/first-analysis-linux.md

The code is taken from the guide's own Markdown, so this check cannot drift from what a
student is told to type. It expects the guide's two results: 1517 traces of 4096 samples,
and 179 quiet traces (Note 2).
"""
import pathlib
import re
import sys

guide = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)```", guide, flags=re.S)
if len(blocks) < 3:
    sys.exit(f"expected at least 3 python blocks in the guide, found {len(blocks)}")

namespace = {"__name__": "__guide__"}
for number, code in enumerate(blocks, start=1):
    print(f"--- guide code block {number} ---", flush=True)
    exec(compile(code, f"<guide block {number}>", "exec"), namespace)

shape = tuple(namespace["pulses"].shape)
quiet = int(namespace["quiet"].sum())
print(f"pulses.shape = {shape}, quiet traces = {quiet}")
if shape != (1517, 4096):
    sys.exit(f"FAIL: expected (1517, 4096), got {shape}")
if quiet != 179:
    sys.exit(f"FAIL: expected 179 quiet traces, got {quiet}")
print("OK: the guide's numbers reproduce.")
