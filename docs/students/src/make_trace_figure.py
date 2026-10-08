"""Draw the two figures of student guide 2: img/trace-pulse.png (a quiet trace and a trace with a pulse) and
img/channels.png (how one event is organised: detectors and channels).

Run it from R76/analysis_notes with the data downloaded as in the guide (needs the dump
07221203_2025_F0001 in ~/idx, nsdf_dark_matter and matplotlib):

    cd R76/analysis_notes
    python ../../docs/students/src/make_trace_figure.py

It is NOT run by build.sh, because it needs the data; the picture is committed. It prints the row
numbers of the two traces, which guide 2 (Step 5) quotes.
"""
import sys
from pathlib import Path

ROOT = Path.cwd().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from nsdf_dark_matter.idx import load_all_data

import pulse_io as pio

QUIET_EVENT = 10001
PULSE_EVENT = 11108

cdms = load_all_data(str(Path.home() / "idx" / "07221203_2025_F0001"))
ids, pulses = pio.load_channel_batch(cdms, pio.filter_by_detector(cdms.get_detector_ids(), 0), 0)
events = np.array([int(pio.event_id(i)) for i in ids])
row = {e: int(np.where(events == e)[0][0]) for e in (QUIET_EVENT, PULSE_EVENT)}
print("rows in the guide's pulses array:", row)

BLUE, GRAY, RED = "#185FA5", "#5F5E5A", "#B3261E"
SPAN = 460  # the same vertical span in both panels, so the pulse can be compared with the noise
fig, axes = plt.subplots(2, 1, figsize=(7.3, 5.4), sharex=True)

for ax, event, title in (
    (axes[0], QUIET_EVENT, f"A trace with no pulse (event {QUIET_EVENT})"),
    (axes[1], PULSE_EVENT, f"A trace with a pulse (event {PULSE_EVENT})"),
):
    y = pulses[row[event]].astype(float)
    base = float(np.mean(y[10:500]))
    ax.plot(np.arange(len(y)), y, color=BLUE, lw=0.9)
    ax.axhline(base, color=GRAY, lw=0.8, ls="--")
    ax.axvspan(0, 500, color="#E1F5EE", alpha=0.7, lw=0)
    ax.set_ylim(base - 40, base + SPAN - 40)
    ax.set_xlim(0, 4096)
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
    ax.set_ylabel("ADC counts")
    ax.text(250, base + SPAN - 70, "pretrigger\nwindow\n(samples\n0 to 500)", ha="center", va="top",
            fontsize=7, color="#085041")
    ax.text(4070, base + 8, "baseline", ha="right", va="bottom", fontsize=8, color=GRAY)

quiet_base = float(np.mean(pulses[row[QUIET_EVENT]][10:500]))
axes[0].text(2300, quiet_base + 120, "noise only: a flat line with a little jitter", ha="center", fontsize=9, color=BLUE)

yp = pulses[row[PULSE_EVENT]].astype(float)
bp = float(np.mean(yp[10:500]))
axes[1].annotate("the pulse starts here\n(about sample 505)", xy=(505, bp + 20), xytext=(1150, bp + 90),
                 arrowprops=dict(arrowstyle="->", color=RED), fontsize=9, color=RED, va="center")
axes[1].annotate("then it slowly falls back", xy=(2500, float(yp[2500])), xytext=(2650, float(yp[2500]) + 120),
                 arrowprops=dict(arrowstyle="->", color=RED), fontsize=9, color=RED, va="center")

axes[1].set_xlabel("sample number (one sample is 1.6 microseconds; the whole trace is 4096 samples)")
fig.text(0.01, 0.005, "Series 07221203_2025, dump F0001, Detector 0, Channel 0. Both panels show the same height in counts.",
         fontsize=7.5, color=GRAY)
fig.tight_layout(rect=(0, 0.02, 1, 1))
out = ROOT / "docs" / "students" / "src" / "img" / "trace-pulse.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=200, facecolor="white")
print("wrote", out)


# ---- second figure: how one event is organised (detectors x channels), computed from the data ----
all_ids = cdms.get_detector_ids()
detectors = sorted({pio.detector_index(i) for i in all_ids})
N_CHANNELS = 4
has_signal = {}
for d in detectors:
    ids_d = pio.filter_by_detector(all_ids, d)
    for ch in range(N_CHANNELS):
        _, p = pio.load_channel_batch(cdms, ids_d, ch)
        has_signal[(d, ch)] = bool(np.any(p != 0))
n_signal = sum(has_signal.values())
print("slots with a signal:", n_signal, "of", len(has_signal), "|", {k: v for k, v in has_signal.items()})

from matplotlib.patches import Wedge, Circle

fig2, ax = plt.subplots(figsize=(7.3, 4.0))
ax.set_aspect("equal")
ax.axis("off")
ax.set_xlim(-2.6, 2.6)
ax.set_ylim(-1.55, 1.55)
TEAL_FC, TEAL_EC, GRAY_FC, GRAY_EC = "#E1F5EE", "#0F6E56", "#F1EFE8", "#B4B2A9"
R = 1.35
# four equal sectors, drawn like the top face of a round detector crystal; which sensor sits where
# on a real detector is not shown here, the sectors only stand for the four channel numbers
for ch in range(N_CHANNELS):
    a0 = 90 - 90 * ch
    sig = has_signal[(0, ch)]
    ax.add_patch(Wedge((0, 0), R, a0 - 90, a0, fc=TEAL_FC if sig else GRAY_FC, ec=TEAL_EC if sig else GRAY_EC, lw=1.4))
    mid = np.deg2rad(a0 - 45)
    ax.text(0.62 * R * np.cos(mid), 0.62 * R * np.sin(mid) + 0.07, f"channel {ch}", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#085041" if sig else GRAY)
    ax.text(0.62 * R * np.cos(mid), 0.62 * R * np.sin(mid) - 0.14, "a trace" if sig else "all zeros",
            ha="center", va="center", fontsize=8, color="#085041" if sig else GRAY)
ax.add_patch(Circle((0, 0), R, fc="none", ec=GRAY, lw=2.2))
# channel 0 is the first sector (upper right): outline it in red
ax.add_patch(Wedge((0, 0), R, 0, 90, fc="none", ec=RED, lw=3))
ax.text(1.75, 0.75, "the one this guide uses:\ndetector 0, channel 0", ha="left", va="center", fontsize=9, color=RED)
ax.annotate("", xy=(0.95, 0.62), xytext=(1.72, 0.75), arrowprops=dict(arrowstyle="->", color=RED))
ax.text(-1.75, 0.2, "detector 0", ha="right", va="center", fontsize=10, fontweight="bold", color=GRAY)
ax.text(-1.75, -0.15, "in Run 76 this is one\nelectronics unit with\nfour channels", ha="right", va="center", fontsize=8, color=GRAY)
n_det = len(detectors)
fig2.text(0.01, 0.02,
          f"One event. The data has {n_det} units of {N_CHANNELS} channels ({n_det * N_CHANNELS} slots); in Run 76 all {n_det} read the same physical detector.\n"
          f"{n_signal} slots hold a trace of 4096 samples, the rest read zero. A schematic, not a real channel map.",
          fontsize=7.2, color=GRAY)
fig2.tight_layout(rect=(0, 0.09, 1, 1))
out2 = ROOT / "docs" / "students" / "src" / "img" / "channels.png"
fig2.savefig(out2, dpi=200, facecolor="white")
print("wrote", out2)
