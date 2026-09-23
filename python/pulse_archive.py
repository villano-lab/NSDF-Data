"""Persistent archive of "good event" selections, keyed by series/detector/channel.

Every cut in `pulse_cuts.py` is cheap to recompute from raw data, so this isn't
a cache -- it's a durable record of *which* detector_ids a particular cut (run
with particular parameters, on a particular dump) actually selected, so a
later notebook or a re-run with different library code can compare against
what was kept before, without re-deriving it from scratch or re-reading
notebook output by hand.

One HDF5 file, one group per `(series, detector, channel)`::

    /<series>/detector<N>/channel<C>
        dataset "detector_ids"   -- variable-length UTF-8 strings
        attrs: cut_name, cut_status, cut_params (JSON string), n_total,
               n_kept, dump, pretrigger_samples, glitch_samples,
               sample_period_s, source_notebook, created (ISO 8601, UTC)

Saving a group overwrites it -- the archive holds the *current* good-event
list per series/detector/channel, not a history of every past run. Only this
module knows about `h5py`; everything else in `python/` stays free of that
dependency.
"""
import json
from datetime import datetime, timezone

import h5py
import numpy as np

from pulse_status import status, DONE


def _group_path(series: str, detector: int, channel: int) -> str:
    return f"{series}/detector{detector}/channel{channel}"


@status(DONE)
def save_good_events(path, series: str, detector: int, channel: int, detector_ids,
                      cut_name: str, *, cut_status: str = None, cut_params: dict = None,
                      n_total: int = None, dump: str = None, config=None,
                      source_notebook: str = None):
    """Write (or overwrite) the good-event list for one `(series, detector,
    channel)` group. `detector_ids` is any iterable of id strings (e.g. from
    `pulse_io.load_channel_batch`, indexed by a cut's boolean mask).

    Pass `cut_status` (e.g. `pulse_cuts.excursion_band_AI.status`) so a reader
    can tell at a glance whether the archived selection came from a `done` or
    `under_development` cut, without re-importing the library. `cut_params`
    (e.g. `{"low": 0.5, "high": 0.7, "min_duration": 50}`) and `config`
    (a `PulseConfig`) are stored as a record of exactly how the cut was run.
    """
    detector_ids = list(detector_ids)
    with h5py.File(path, "a") as f:
        group_path = _group_path(series, detector, channel)
        if group_path in f:
            del f[group_path]
        grp = f.create_group(group_path)
        grp.create_dataset("detector_ids", data=np.array(detector_ids, dtype=object),
                            dtype=h5py.string_dtype(encoding="utf-8"))
        grp.attrs["cut_name"] = cut_name
        grp.attrs["cut_status"] = cut_status or ""
        grp.attrs["cut_params"] = json.dumps(cut_params or {})
        grp.attrs["n_total"] = -1 if n_total is None else int(n_total)
        grp.attrs["n_kept"] = len(detector_ids)
        grp.attrs["dump"] = dump or ""
        grp.attrs["source_notebook"] = source_notebook or ""
        if config is not None:
            grp.attrs["pretrigger_samples"] = config.pretrigger_samples
            grp.attrs["glitch_samples"] = config.glitch_samples
            grp.attrs["sample_period_s"] = (
                config.sample_period_s if config.sample_period_s is not None else -1.0
            )
        grp.attrs["created"] = datetime.now(timezone.utc).isoformat()


@status(DONE)
def load_good_events(path, series: str, detector: int, channel: int) -> dict:
    """Read back one `(series, detector, channel)` group.

    Returns a dict with `detector_ids` (a plain `np.ndarray` of strings) plus
    every attribute `save_good_events` wrote (`cut_params` is decoded back
    into a dict).
    """
    with h5py.File(path, "r") as f:
        group_path = _group_path(series, detector, channel)
        if group_path not in f:
            raise KeyError(f"no archived good-event list at {group_path!r} in {path}")
        grp = f[group_path]
        out = {"detector_ids": grp["detector_ids"][()].astype(str)}
        for key, value in grp.attrs.items():
            out[key] = json.loads(value) if key == "cut_params" else value
        return out


@status(DONE)
def list_archive(path) -> dict:
    """Return `{series: {detector: {channel: n_kept}}}` for every group in the
    archive -- a quick overview of what's been saved so far. Returns `{}` if
    `path` doesn't exist yet."""
    import os
    if not os.path.exists(path):
        return {}

    out = {}
    with h5py.File(path, "r") as f:
        for series in f:
            out[series] = {}
            for detector_key in f[series]:
                detector = int(detector_key.removeprefix("detector"))
                out[series][detector] = {}
                for channel_key in f[series][detector_key]:
                    channel = int(channel_key.removeprefix("channel"))
                    grp = f[series][detector_key][channel_key]
                    out[series][detector][channel] = int(grp.attrs["n_kept"])
    return out
