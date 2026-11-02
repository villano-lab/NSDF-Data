"""The -82 V DCRC1pB series of relcal: reading the processed quantities, the 20 % delays, and the two high-activity spots.

Shared by `positions-82v-dcrc1pb.ipynb` (where the spots are found and drawn) and `spots-82v-energy.ipynb` (their energy
distributions), so that both use the same selection. The definitions are those of `positions-from-delays.ipynb`.

The spots are circles in the plane of the delays (`xdel`, `ydel`, microseconds). Their centres are the peaks of the event density
of all eight series, found on a 0.1 us grid; their widths are about 0.45 us (standard deviation in x and in y within 1 us of the
centre), and the density falls to the level around them by about 2.5 us. The radius of 1.5 us keeps the core and leaves out most
of the surroundings; it is a choice, not a fit.
"""
import csv
import warnings
from pathlib import Path

import numpy as np

from goldpan.adapters import parquet

OUT = Path.home() / "goldsluice-output" / "r76-82v-dcrc1pb"     # the output of r76-82v-dcrc1pb.dataset.toml
LETTERS = "ABCDEF"

THRESH = 2.0                       # ADC counts x s, as in integral-on-the-face.ipynb
WINDOW = 60.0                      # microseconds: delays of the same pulse are a few microseconds, of different pulses hundreds
OFFSET_X, OFFSET_Y = -1.0, 9.0     # the empirical offsets of Fritts's code

SPOTS = {                          # name -> (xdel, ydel, radius), microseconds
    "C": (4.45, 4.80, 1.5),        # the spot over the sector C
    "F": (1.60, 0.70, 1.5),        # the spot over the centre disc F
}


def load(out=OUT):
    """The quantities of the output as a dict of numpy arrays, with the delays and the selection of positions-from-delays.ipynb.

    Keys: series, dump, event, trigger, t (dict letter -> 20 % time, us), integral (events x 6, ADC counts x s, in LETTERS order),
    S (integral minus its median within the series), total (sum of the positive S), xdel, ydel, afdel, phidel (degrees), use
    (real trigger, total > THRESH, six times, all six within WINDOW of their median)."""
    q = parquet.read(out, detector="NAI-S2").quantities
    d = {k: np.asarray(q[k]).astype(str) for k in ("series", "dump")}
    d["event"] = np.asarray(q["event"])
    d["trigger"] = np.asarray(q["trigger_type"]).astype(str)
    t = {k: np.asarray(q[f"Side2p{k}"]["crossing_time_s"], dtype=float) * 1e6 for k in LETTERS}
    integral = np.column_stack([np.asarray(q[f"Side2p{k}"]["integral"], dtype=float) for k in LETTERS])
    S = integral.copy()
    for s in np.unique(d["series"]):
        m = d["series"] == s
        S[m] -= np.median(integral[m], axis=0)
    total = np.clip(S, 0, None).sum(axis=1)

    T = np.column_stack([t[k] for k in LETTERS])
    xdel = t["E"] - 0.5 * (t["C"] + t["D"]) + OFFSET_X
    ydel = 0.866 * (t["D"] - t["C"]) + OFFSET_Y
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)         # an event with no time at all has an all-nan median
        one_pulse = (np.abs(T - np.nanmedian(T, axis=1, keepdims=True)) < WINDOW).all(axis=1)
    use = (d["trigger"] == "Unknown") & (total > THRESH) & np.isfinite(T).all(axis=1) & one_pulse
    d.update(t=t, integral=integral, S=S, total=total, xdel=xdel, ydel=ydel, afdel=t["F"] - t["A"],
             phidel=np.degrees(np.arctan2(ydel, xdel)), use=use)
    return d


def in_spot(xdel, ydel, name, scale=1.0):
    """True for the events within `scale` times the radius of the spot `name`."""
    x0, y0, r = SPOTS[name]
    return np.hypot(xdel - x0, ydel - y0) < scale * r


def ring(xdel, ydel, name, inner=1.5, outer=2.2):
    """True for the events in the ring between `inner` and `outer` times the radius of the spot: its surroundings, for comparison.
    The two spots are 5.0 us apart, so with the defaults (2.25 to 3.3 us) the ring of one does not reach the other's circle."""
    x0, y0, r = SPOTS[name]
    d = np.hypot(xdel - x0, ydel - y0)
    return (d >= inner * r) & (d < outer * r)


def series_csv():
    """The rows of series_lists/nsdf_r76_series.csv by series name (HV, trigger, ...)."""
    here = Path(__file__).resolve()
    path = next(p / "data_analysis" / "R76" / "series_lists" / "nsdf_r76_series.csv" for p in here.parents
                if (p / "data_analysis" / "R76" / "series_lists").is_dir())
    with open(path, newline="") as fh:
        return {r["series"]: r for r in csv.DictReader(fh)}
