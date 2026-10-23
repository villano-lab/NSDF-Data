"""Drawing of an event over the detector channel layout (series 07221203_2025, detector S104, Side-2 readout).

Exploration code for the pulse-normalization notebooks: not part of the library in `python/`.

The readout of this series is Side 2 (see `python/pulse_channels.py`): six sensors, all on Side 2, one for every
region of that face. The face is drawn as in the Note 9 channel figure and the wiki (Run 76 summary, 7.4):
A = outer ring, B = second ring, C / D / E = three 120-degree sectors of the middle region (E on the right, C upper
left, D lower left), F = centre disc, as seen after flipping the detector over; the x axis of the wiki figure points
to the left. Side 1 of the detector is not read out in this series and is not drawn.

A channel is identified by the letter of its region, for example "C" for Side2pC.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.patches import Wedge, Patch
from matplotlib.lines import Line2D

import pulse_channels as pch

REGIONS = {   # letter -> (inner radius, outer radius, start angle, end angle) in degrees, radius 1 = the face
    "A": (0.90, 1.00, 0, 360), "B": (0.80, 0.90, 0, 360),
    "C": (0.25, 0.80, 60, 180), "D": (0.25, 0.80, 180, 300), "E": (0.25, 0.80, -60, 60),
    "F": (0.00, 0.25, 0, 360),
}
BOARD_COLOUR = {"DCRC1": "#1f77b4", "DCRC3": "#d95f02"}      # frames of the trace panels: one colour per readout board
AXES_COLOUR = "#c44e00"
CHANNELS = {c.letter: c for c in pch.sensor_channels()}      # letter -> Channel record of the six sensors

# where the trace of each channel goes: (column, row) of the six slots around the face (column 0 left of the
# face, 1 right; row 0 bottom, 1 middle, 2 top), and the point of the region the leader line starts from
# (radius as a fraction of the face, angle in degrees)
SLOT = {"C": (0, 2), "D": (0, 0), "E": (1, 1), "A": (1, 2), "B": (0, 1), "F": (1, 0)}
ANCHOR = {"C": (0.78, 140), "D": (0.78, 220), "E": (0.75, 0), "A": (0.95, 50), "B": (0.85, 180), "F": (0.12, -50)}

# the page, in inches (the map axes use inches as data units, so circles stay round)
PAGE_W, PAGE_H = 10.8, 12.5
RADIUS = 1.6
CENTRE = (5.4, 6.4)
SLOT_X = (1.95, 8.85)
SLOT_Y = (2.9, 6.4, 9.9)
CALL_W, CALL_H = 3.0, 2.3


def _polar(radius, angle_deg):
    a = np.deg2rad(angle_deg)
    return radius * np.cos(a), radius * np.sin(a)


def sector_centroid(letter):
    """Centroid of a region as a fraction of the face radius (rings and the centre disc: the centre)."""
    r_in, r_out, a0, a1 = REGIONS[letter]
    if a1 - a0 >= 360:
        return 0.0, 0.0
    half = np.deg2rad(a1 - a0) / 2
    r_c = (2 / 3) * (r_out ** 3 - r_in ** 3) / (r_out ** 2 - r_in ** 2) * np.sin(half) / half
    return _polar(r_c, (a0 + a1) / 2)


def weighted_centre(heights):
    """Height-weighted mean of the region centroids of the face, or None.
    A rough guide to where on the face the event is, not a position reconstruction (the ring channels sit at the centre)."""
    w = np.array([max(h, 0.0) for h in heights.values()])
    if not len(w) or w.sum() <= 0:
        return None
    pts = np.array([sector_centroid(letter) for letter in heights])
    return tuple((w[:, None] * pts).sum(axis=0) / w.sum())


def _text_colour(rgba):
    lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
    return "black" if lum > 0.55 else "white"


def draw_face(ax, centre, radius, heights, cmap, norm, numbers=True, fontsize=10, star=True):
    """Draw the face on `ax` (data units), each region coloured by its rise height (a region with no height is hatched grey).
    `heights` maps letter -> height. Returns the weighted centre (fraction of the radius) or None."""
    cx, cy = centre
    for letter, (r_in, r_out, a0, a1) in REGIONS.items():
        ok = letter in heights
        face = cmap(norm(heights[letter])) if ok else "0.88"
        ax.add_patch(Wedge((cx, cy), r_out * radius, a0, a1, width=(r_out - r_in) * radius, facecolor=face,
                           edgecolor="k", linewidth=1.0, hatch=None if ok else "//", zorder=2))
        if letter in "CDE" and numbers:
            x, y = _polar((r_in + r_out) / 2 * radius + 0.03 * radius, (a0 + a1) / 2)
            text = f"{letter}\n{heights[letter]:.0f}" if ok else f"{letter}\n-"
            ax.text(cx + x, cy + y, text, ha="center", va="center", fontsize=fontsize, zorder=3,
                    fontweight="bold" if ok else "normal", color=_text_colour(face) if ok else "0.35")
    wc = weighted_centre(heights) if star else None
    if wc is not None:
        ax.plot([cx + wc[0] * radius], [cy + wc[1] * radius], marker="*", markersize=fontsize * 1.8, markerfacecolor="white",
                markeredgecolor="k", markeredgewidth=1.0, linestyle="none", zorder=4)
    return wc


def _legend_handles(star=True):
    handles = [Patch(facecolor="white", edgecolor=BOARD_COLOUR["DCRC1"], linewidth=2, label="trace frame: DCRC1"),
               Patch(facecolor="white", edgecolor=BOARD_COLOUR["DCRC3"], linewidth=2, label="trace frame: DCRC3")]
    if star:
        handles.append(Line2D([0], [0], marker="*", linestyle="none", markerfacecolor="white", markeredgecolor="k",
                              markersize=14, label="height-weighted centre (a rough guide only)"))
    return handles


def draw_event_layout(event_label, t_us, flats, heights, t_fit, ylim, cmap="viridis", subtitle=""):
    """One event over the detector layout: the face (Side 2) with its six regions coloured by rise height, and
    the whole trace of every channel (baseline subtracted, on one vertical scale `ylim`) in a panel next to its
    region, joined to it by a leader line.

    flats:   letter -> trace with the baseline subtracted (n_samples)
    heights: letter -> rise height in counts
    t_fit:   (start, end) of the baseline fit, or a list of such spans, microseconds from the trigger
    """
    spans = [t_fit] if np.ndim(t_fit) == 1 else list(t_fit)      # one fit span, or several (before the pulse and the late tail)
    top = max(heights.values())
    norm = colors.Normalize(vmin=0, vmax=top)
    cmap = plt.get_cmap(cmap)
    fig = plt.figure(figsize=(PAGE_W, PAGE_H))
    amap = fig.add_axes([0, 0, 1, 1], zorder=0)
    amap.set_xlim(0, PAGE_W); amap.set_ylim(0, PAGE_H); amap.set_aspect("equal"); amap.axis("off")

    cx, cy = CENTRE
    draw_face(amap, CENTRE, RADIUS, heights, cmap, norm)
    amap.text(cx, cy + RADIUS + 0.35, "Side 2 (seen after flipping the detector over)", ha="center", fontsize=13)
    # the x / y axes of the wiki figure: +x to the left on this face, +y up
    ox, oy = cx - 0.4, 4.15
    amap.annotate("", xy=(ox - 0.5, oy), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", color=AXES_COLOUR, lw=1.8))
    amap.annotate("", xy=(ox, oy + 0.5), xytext=(ox, oy), arrowprops=dict(arrowstyle="->", color=AXES_COLOUR, lw=1.8))
    amap.text(ox - 0.68, oy, "x", color=AXES_COLOUR, ha="center", va="center", fontsize=12)
    amap.text(ox, oy + 0.68, "y", color=AXES_COLOUR, ha="center", va="center", fontsize=12)

    for letter in REGIONS:
        col, row = SLOT[letter]
        sx, sy = SLOT_X[col], SLOT_Y[row]
        r, ang = ANCHOR[letter]
        ax_, ay_ = _polar(r * RADIUS, ang)
        edge_x = sx + (CALL_W / 2 if col == 0 else -CALL_W / 2)
        ch = CHANNELS[letter]
        colour = BOARD_COLOUR[ch.dcrc]
        amap.plot([cx + ax_, edge_x], [cy + ay_, sy], color=colour, lw=1.0, alpha=0.9, zorder=1)
        amap.plot([cx + ax_], [cy + ay_], marker="o", markersize=3.5, color="k", zorder=4)
        ax = fig.add_axes([(sx - CALL_W / 2) / PAGE_W, (sy - CALL_H / 2) / PAGE_H, CALL_W / PAGE_W, CALL_H / PAGE_H], zorder=2)
        for span in spans:
            ax.axvspan(*span, color="0.88", zorder=0)
        ax.axvline(0, color="0.5", linestyle="--", linewidth=0.8)
        ax.plot(t_us, flats[letter], linewidth=0.7, color=colour)
        ax.set_ylim(*ylim)
        ax.set_xlim(t_us[0], t_us[-1])
        ax.set_title(f"{ch.name} ({ch.dcrc} {ch.board_input}): {heights[letter]:.0f} counts", fontsize=9)
        ax.tick_params(labelsize=7, length=2)
        for spine in ax.spines.values():
            spine.set_edgecolor(colour); spine.set_linewidth(2.0)
        if row == 0:
            ax.set_xlabel("time from trigger (us)", fontsize=8)
        if col == 0:
            ax.set_ylabel("counts", fontsize=8)

    cax = fig.add_axes([0.30, 0.085, 0.40, 0.012])
    cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_label("rise height (counts); all traces share one vertical scale", fontsize=10)
    fig.legend(handles=_legend_handles(), loc="lower center", ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"{event_label}{subtitle}", fontsize=13, y=0.975)
    return fig


def draw_contact_sheet(events, cmap="viridis", ncols_events=4, title=""):
    """A small map of each event: the face with its regions coloured by rise height (and printed in the three
    big regions), and the height-weighted centre. Colours are normalised to the largest height of each
    event, which is printed. `events` is a list of dicts with keys 'label', 'heights' (letter -> counts)
    and 'top' (the text for the title, e.g. the channel with the largest height)."""
    cmap = plt.get_cmap(cmap)
    n = len(events)
    nrows = int(np.ceil(n / ncols_events))
    fig, axes = plt.subplots(nrows, ncols_events, figsize=(3.6 * ncols_events, 3.9 * nrows), squeeze=False)
    for k, ax in enumerate(axes.flat):
        if k >= n:
            ax.axis("off")
            continue
        ev = events[k]
        norm = colors.Normalize(vmin=0, vmax=max(ev["heights"].values()))
        draw_face(ax, (0, 0), 1.0, ev["heights"], cmap, norm, fontsize=9)
        small = "   ".join(f"{letter} {ev['heights'][letter]:.0f}" for letter in "ABF" if letter in ev["heights"])
        if small:                      # the ring and the centre disc are too small to print their height in
            ax.text(0, -1.12, small + "  (rings, disc)", ha="center", va="top", fontsize=8, color="0.3")
        ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.3, 1.15); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(ev["label"], fontsize=10, fontweight="bold", loc="left", pad=16)
        ax.text(0.0, 1.03, ev["top"], transform=ax.transAxes, fontsize=8, ha="left", color="0.3")
    fig.legend(handles=_legend_handles()[2:], loc="lower center", ncol=1, fontsize=9, frameon=False)
    fig.suptitle(title, fontsize=12, y=1.0)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.07, hspace=0.45, wspace=0.05)
    return fig
