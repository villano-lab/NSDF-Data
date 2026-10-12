"""Draw the data-structure figure of student guide 2 (img/data-structure.png): how a series is
split into dumps, events, detectors, channels and samples, and which of them the Step 4 code picks.

    python make_structure_figure.py

Needs matplotlib. Run by build.sh. Blue = the part the guide follows (detector 0, channel 0), grey = the rest.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

OUT = Path(__file__).resolve().parent / "img"
OUT.mkdir(exist_ok=True)

PICK = dict(fc="#E6F1FB", ec="#185FA5", tc="#0C447C")
REST = dict(fc="#F1EFE8", ec="#B4B2A9", tc="#5F5E5A")
CODE = "#0C447C"
NOTE = "#5F5E5A"
ZOOM = "#E6F1FB"

# Each level: name, labels of its cells, index of the one we follow, plain note, code that picks it.
LEVELS = [
    ("Series", ["07221203_2025"], 0, "07 = test facility (UMN), 221203 = date, 2025 = start time", ""),
    ("Dump", ["F0001", "F0002", "F0003", "..."], 0, "one file set from the series",
     'load_all_data(".../07221203_2025_F0001")'),
    ("Event", ["...", "11108", "..."], 1, "event 11108 is row 1095 of the 1517 rows", "pulses[1095]"),
    ("Detector", ["0", "1", "2"], 0, "three readout units, all on the same physical detector",
     "filter_by_detector(..., 0)"),
    ("Channel", ["0", "1", "2", "3"], 0, "four channels per readout unit", "load_channel_batch(..., 0)"),
    ("Trace", ["0", "1", "2", "...", "4095"], None, "4096 samples; each is one number in ADC counts (1.6 \u00b5s)",
     "pulses[row, sample]"),
]

X0, W = 13.0, 46.0          # left edge and width of the cell rows
H, STEP = 3.2, 7.0          # cell height, distance between rows


def main():
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    n = len(LEVELS)
    top = n * STEP
    ax.set_xlim(0, 100)
    ax.set_ylim(1.5, top + 1)
    ax.axis("off")

    prev = None  # (x, width) of the cell picked in the row above
    for i, (name, cells, pick, note, code) in enumerate(LEVELS):
        y = top - (i + 1) * STEP + 2
        gap = 0.6
        cw = (W - gap * (len(cells) - 1)) / len(cells)
        if prev is not None:
            px, pw = prev
            ax.add_patch(Polygon([(px, y + H + STEP - H), (px + pw, y + H + STEP - H), (X0 + W, y + H), (X0, y + H)],
                                 closed=True, fc=ZOOM, ec="none", alpha=0.55, zorder=0))
        for j, label in enumerate(cells):
            x = X0 + j * (cw + gap)
            c = PICK if j == pick else REST
            if label in ("...",):
                c = dict(fc="white", ec="white", tc=NOTE)
            ax.add_patch(FancyBboxPatch((x, y), cw, H, boxstyle="round,pad=0,rounding_size=0.4",
                                        fc=c["fc"], ec=c["ec"], lw=1.1 if j == pick else 0.8, zorder=2))
            ax.text(x + cw / 2, y + H / 2, label, ha="center", va="center", fontsize=7.2,
                    fontweight="bold" if j == pick else "normal", color=c["tc"], zorder=3)
            if j == pick:
                prev = (x, cw)
        ax.text(X0 - 1.2, y + H / 2, name, ha="right", va="center", fontsize=8, fontweight="bold",
                color="#2C2C2A")
        if code:
            ax.text(X0 + W + 2.0, y + H / 2 + 0.9, note, ha="left", va="center", fontsize=6.6, color=NOTE)
            ax.text(X0 + W + 2.0, y + H / 2 - 0.9, code, ha="left", va="center", fontsize=6.6,
                    family="monospace", color=CODE)
        else:
            ax.text(X0 + W + 2.0, y + H / 2, note, ha="left", va="center", fontsize=6.6, color=NOTE)

    fig.savefig(OUT / "data-structure.png", dpi=230, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    print("wrote data-structure.png")


if __name__ == "__main__":
    main()
