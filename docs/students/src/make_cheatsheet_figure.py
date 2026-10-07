"""Draw the figure of the student note cheat-sheet (img/note-path.png).

    python make_cheatsheet_figure.py

Needs matplotlib. Run by build.sh. Blue = you, teal = GitHub (automatic), amber = your lead.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent / "img"
OUT.mkdir(exist_ok=True)

BLUE = dict(fc="#E6F1FB", ec="#185FA5", tc="#0C447C")
TEAL = dict(fc="#E1F5EE", ec="#0F6E56", tc="#085041")
AMBER = dict(fc="#FAEEDA", ec="#854F0B", tc="#633806")
LINE = "#888780"

STEPS = [
    ("Write", "a .md file", BLUE),
    ("Commit, push", "student-yourname", BLUE),
    ("Open a PR", "base: develop", BLUE),
    ("Check runs", "under a minute", TEAL),
    ("Lead reviews", "gives an S-number", AMBER),
    ("Live", "about 2 minutes", TEAL),
]


def main():
    fig, ax = plt.subplots(figsize=(7.1, 1.05))
    ax.set_xlim(0, 74)
    ax.set_ylim(0, 8)
    ax.axis("off")
    w, h, gap = 11.0, 6.2, 1.6
    for i, (title, sub, c) in enumerate(STEPS):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.8), w, h, boxstyle="round,pad=0,rounding_size=0.5",
                                    fc=c["fc"], ec=c["ec"], lw=1.1))
        ax.text(x + 0.8, 0.8 + h - 0.5, str(i + 1), ha="left", va="top", fontsize=6.0, color=c["ec"])
        ax.text(x + w / 2, 0.8 + h * 0.52, title, ha="center", va="center", fontsize=6.9,
                fontweight="bold", color=c["tc"])
        ax.text(x + w / 2, 0.8 + h * 0.22, sub, ha="center", va="center", fontsize=5.9, color=c["tc"])
        if i < len(STEPS) - 1:
            ax.add_patch(FancyArrowPatch((x + w, 0.8 + h / 2), (x + w + gap, 0.8 + h / 2),
                                         arrowstyle="-|>", mutation_scale=7, lw=1.1, color=LINE,
                                         shrinkA=0, shrinkB=0))
    fig.savefig(OUT / "note-path.png", dpi=230, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    print("wrote note-path.png")


if __name__ == "__main__":
    main()
