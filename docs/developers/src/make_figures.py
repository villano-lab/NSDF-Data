"""Draw the two figures of the developer workflow PDF (img/loop.png, img/branches.png).

    python make_figures.py

Needs matplotlib. Run by build.sh. Colours: blue = on your computer, teal = on GitHub.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch
from matplotlib.path import Path as MPath

OUT = Path(__file__).resolve().parent / "img"
OUT.mkdir(exist_ok=True)

BLUE = dict(fc="#E6F1FB", ec="#185FA5", tc="#0C447C")
TEAL = dict(fc="#E1F5EE", ec="#0F6E56", tc="#085041")
GRAY = dict(fc="#F1EFE8", ec="#5F5E5A", tc="#2C2C2A")
LINE = "#888780"


def box(ax, x, y, w, h, title, sub, colors, number=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.5",
                                fc=colors["fc"], ec=colors["ec"], lw=1.1))
    if number is not None:
        ax.text(x + 0.8, y + h - 0.55, str(number), ha="left", va="top", fontsize=6.0, color=colors["ec"])
    ax.text(x + w / 2, y + h * 0.50, title, ha="center", va="center", fontsize=6.9,
            fontweight="bold", color=colors["tc"])
    ax.text(x + w / 2, y + h * 0.20, sub, ha="center", va="center", fontsize=6.2, color=colors["tc"])


def arrow(ax, p, q, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, lw=1.1, color=LINE,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def loop():
    fig, ax = plt.subplots(figsize=(7.3, 2.0))
    ax.set_xlim(0, 73)
    ax.set_ylim(0, 20)
    ax.axis("off")
    w, h, gap = 12.6, 6.4, 2.5
    xs = [i * (w + gap) for i in range(5)]
    row1 = [("Update develop", "git pull", BLUE), ("Make a branch", "feature/name", BLUE),
            ("Work, commit", "small commits", BLUE), ("Push", "git push -u origin", BLUE),
            ("Open a PR", "base: develop", TEAL)]
    row2 = [("Checks run", "automatic (CI)", TEAL), ("Review", "optional, by hand", TEAL),
            ("Merge", "merge commit", TEAL), ("Live", "about 2 minutes", TEAL),
            ("Clean up", "delete branch, pull", BLUE)]
    y1, y2 = 13.2, 2.4
    for n, (x, (t, s, c)) in enumerate(zip(xs, row1), start=1):
        box(ax, x, y1, w, h, t, s, c, number=n)
    for n, (x, (t, s, c)) in enumerate(zip(xs, row2), start=6):
        box(ax, x, y2, w, h, t, s, c, number=n)
    for r_y in (y1, y2):
        for i in range(4):
            arrow(ax, (xs[i] + w, r_y + h / 2), (xs[i + 1], r_y + h / 2))
    ax.plot([xs[4] + w / 2, xs[4] + w / 2, xs[0] + w / 2], [y1, 10.9, 10.9], color=LINE, lw=1.1)
    arrow(ax, (xs[0] + w / 2, 10.9), (xs[0] + w / 2, y2 + h))
    fig.savefig(OUT / "loop.png", dpi=230, bbox_inches="tight", pad_inches=0.03, transparent=False,
                facecolor="white")
    plt.close(fig)


def bez(ax, pts, **kw):
    ax.add_patch(PathPatch(MPath(pts, [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4]),
                           fc="none", **kw))


def branches():
    fig, ax = plt.subplots(figsize=(7.3, 1.75))
    ax.set_xlim(0, 73)
    ax.set_ylim(0, 17.3)
    ax.axis("off")
    ym, yd, yf = 14.2, 8.0, 2.6
    for y in (ym, yd):
        ax.plot([2, 71], [y, y], color=LINE, lw=1.6, solid_capstyle="round")
    ax.text(2, ym + 1.7, "master", fontsize=8.2, fontweight="bold", va="center", color=GRAY["tc"])
    ax.text(10.2, ym + 1.7, "released and tagged only", fontsize=6.9, va="center", color="#5F5E5A")
    ax.text(2, yd + 1.7, "develop", fontsize=8.2, fontweight="bold", va="center", color=GRAY["tc"])
    ax.text(10.8, yd + 1.7, "integration, and the live site is served from here", fontsize=6.9,
            va="center", color="#5F5E5A")
    bez(ax, [(12, yd), (14.2, yd), (14.2, yf), (17.5, yf)], ec=LINE, lw=1.6)
    ax.plot([17.5, 29.5], [yf, yf], color=LINE, lw=1.6)
    bez(ax, [(29.5, yf), (32.8, yf), (33.3, yd), (35, yd)], ec=LINE, lw=1.6)
    for x in (6, 12, 35, 47, 64):
        ax.plot(x, yd, "o", ms=6, mfc=BLUE["fc"], mec=BLUE["ec"], mew=1.4)
    for x in (20.5, 26.5):
        ax.plot(x, yf, "o", ms=6, mfc=GRAY["fc"], mec=GRAY["ec"], mew=1.4)
    ax.plot(57, ym, "o", ms=8, mfc=TEAL["fc"], mec=TEAL["ec"], mew=1.6)
    ax.text(57, ym - 1.9, "v0.1.0", fontsize=7.6, fontweight="bold", ha="center", color=TEAL["tc"])
    ax.text(23.5, 0.35, "feature/name", fontsize=6.9, ha="center", va="center", color="#5F5E5A")
    ax.text(16.6, 5.6, "branch off", fontsize=6.9, va="center", color="#5F5E5A")
    ax.text(36.4, 5.6, "PR merged into develop", fontsize=6.9, va="center", color="#5F5E5A")
    ax.add_patch(FancyArrowPatch((47, yd + 0.4), (56.1, ym - 0.1), arrowstyle="-|>", mutation_scale=8,
                                 lw=1.1, color=LINE, connectionstyle="arc3,rad=-0.28"))
    ax.text(45.6, 11.2, "release PR", fontsize=6.9, ha="right", va="center", color="#5F5E5A")
    ax.add_patch(FancyArrowPatch((58.1, ym - 0.1), (64, yd + 0.5), arrowstyle="-|>", mutation_scale=8,
                                 lw=1.1, color=LINE, connectionstyle="arc3,rad=-0.28"))
    ax.text(64, 5.6, "merge master back", fontsize=6.9, ha="center", va="center", color="#5F5E5A")
    fig.savefig(OUT / "branches.png", dpi=230, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    loop()
    branches()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))
