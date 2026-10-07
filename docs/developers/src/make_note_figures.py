"""Draw the figures of the two note-creation quick-sheets.

    python make_note_figures.py      # writes img/note-steps.png and img/note-ai-steps.png

Needs matplotlib. Run by build.sh. Blue = you, purple = the AI agent, teal = GitHub.
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
PURPLE = dict(fc="#EEEDFE", ec="#534AB7", tc="#3C3489")
LINE = "#888780"


def row(steps, name):
    fig, ax = plt.subplots(figsize=(7.3, 1.05))
    ax.set_xlim(0, 74)
    ax.set_ylim(0, 8)
    ax.axis("off")
    n = len(steps)
    gap = 1.6
    w = (74 - gap * (n - 1)) / n
    for i, (title, sub, c) in enumerate(steps):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.8), w, 6.2, boxstyle="round,pad=0,rounding_size=0.5",
                                    fc=c["fc"], ec=c["ec"], lw=1.1))
        ax.text(x + 0.8, 0.8 + 6.2 - 0.5, str(i + 1), ha="left", va="top", fontsize=6.0, color=c["ec"])
        ax.text(x + w / 2, 0.8 + 6.2 * 0.52, title, ha="center", va="center", fontsize=6.9,
                fontweight="bold", color=c["tc"])
        ax.text(x + w / 2, 0.8 + 6.2 * 0.22, sub, ha="center", va="center", fontsize=5.8, color=c["tc"])
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((x + w, 0.8 + 3.1), (x + w + gap, 0.8 + 3.1), arrowstyle="-|>",
                                         mutation_scale=7, lw=1.1, color=LINE, shrinkA=0, shrinkB=0))
    fig.savefig(OUT / name, dpi=230, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)


def main():
    row([("Notebook", "commit, note hash", BLUE),
         ("Figures", "to docs/notes/img", BLUE),
         ("Page", "copy newest note", BLUE),
         ("Index row", "newest note first", BLUE),
         ("Check", "pins, links, log", BLUE),
         ("PR, merge", "live in about 2 min", TEAL)], "note-steps.png")
    row([("Brief", "notebook, hash", BLUE),
         ("Draft", "page, figures", PURPLE),
         ("Verify", "you check numbers", BLUE),
         ("Wire up", "index, changelog", PURPLE),
         ("Read diff", "expected files", BLUE),
         ("PR, merge", "you merge", TEAL)], "note-ai-steps.png")
    print("wrote note-steps.png, note-ai-steps.png")


if __name__ == "__main__":
    main()
