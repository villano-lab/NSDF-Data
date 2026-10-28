"""The idx adapter: a dump of the NSDF archive (NEXUS-DM `idx`) into an `Events`. Read only.

An idx dump numbers its traces by *readout board* and *input*, not by channel name: a trace is addressed by an id like
`<event>_<board>_Phonon_<n>` and a channel of it by a small integer. In Run 76 the three "detectors" of a dump are three
boards of one physical detector. This adapter hides that: you say which board and input each *named* channel comes from, and
you name the readout, because neither belongs to the library::

    from goldpan.adapters import idx
    from goldpan.config import DCRC_RUN76
    ev = idx.read("~/idx/07221203_2025_F0001", detector_name="S104", config=DCRC_RUN76,
                  channels={"Side2pC": (0, 0), "Side2pF": (0, 1)})          # channel name -> (board, input)

For Run 76 the map of every sensor is in `goldpan.channels` (`sensor_channels()`). Only this module and `goldpan.io` know
`nsdf_dark_matter`'s `cdms` object; it is imported when a path is given, so tests can pass any object with
`get_detector_ids()`, `get_detector_channels(id)` and `get_event_metadata(event)`.
"""
import re
from pathlib import Path
from typing import Mapping, Optional

import awkward as ak
import numpy as np

from ..config import PulseConfig
from ..data import ChannelInfo, Detector, Events, Readout
from ..status import DONE, status

REVISION = 1
"""Raised by one when a change of this reader changes what it returns for the same file (a fix), so that `goldsluice run` redoes the outputs
made with the old one (`goldpan.adapters.revision`). Not for a change that leaves the results alone."""

_DUMP_NAME = re.compile(r"^(?P<series>.+)_(?P<dump>F\d+)$")


def _series_and_dump(path: Path):
    m = _DUMP_NAME.match(path.name)
    if not m:
        raise ValueError(f"cannot tell the series and the dump from the folder name {path.name!r} (expected <series>_F<number>): "
                         "pass series= and dump=")
    return m["series"], m["dump"]


@status(DONE)
def read(source, *, detector_name: str, channels: Mapping[str, tuple], config: PulseConfig,
         roles: Optional[Mapping[str, str]] = None, series: Optional[str] = None, dump: Optional[str] = None) -> Events:
    """Read one idx dump into an `Events` of one detector.

    `source` is the dump folder (for example `~/idx/07221203_2025_F0001`) or an already loaded `cdms` object (then give `series`
    and `dump`). `channels` maps each channel name to its `(board, input)` in the dump; `config` is the readout of the data (there is
    no default); `roles` optionally gives a role per channel name. Events that lack any requested board are dropped, and how many
    is recorded in `meta["dropped_events"]`. The quantity `trigger_type` is the label of the dump's `.csv`, if the dump has one."""
    if isinstance(source, (str, Path)):
        path = Path(source).expanduser()
        series, dump = (series, dump) if series and dump else _series_and_dump(path)
        from nsdf_dark_matter.idx import load_all_data           # imported here: only this module needs the NSDF software
        cdms = load_all_data(str(path))
        origin = str(path)
    else:
        cdms, origin = source, "object"
        if not (series and dump):
            raise ValueError("pass series= and dump= when giving a loaded cdms object")

    by_event_board = {}
    for det_id in cdms.get_detector_ids():
        event, board = det_id.split("_")[0], int(det_id.split("_")[1])
        by_event_board[(event, board)] = det_id
    boards = sorted({board for board, _ in channels.values()})
    all_events = sorted({e for e, _ in by_event_board}, key=lambda e: (len(e), e))
    kept = [e for e in all_events if all((e, b) in by_event_board for b in boards)]
    if not kept:
        raise ValueError(f"no event of {origin} has all the boards {boards}")

    arrays = {}
    for name, (board, inp) in channels.items():
        arrays[name] = np.stack([np.asarray(cdms.get_detector_channels(by_event_board[(e, board)])[inp], dtype=np.float64)
                                 for e in kept])
    n_samples = {a.shape[1] for a in arrays.values()}
    if len(n_samples) != 1:
        raise ValueError(f"the channels of {origin} have different numbers of samples: {sorted(n_samples)}")

    detector = Detector(detector_name,
                        tuple(ChannelInfo(n, role=(roles or {}).get(n), unit=f"board{b}", input=str(i))
                              for n, (b, i) in channels.items()),
                        Readout.single(n_samples.pop(), config))
    quantities = {"series": np.full(len(kept), series), "dump": np.full(len(kept), dump),
                  "event": np.array([int(e) for e in kept], dtype=np.int64)}
    try:
        quantities["trigger_type"] = np.array([cdms.get_event_metadata(e).trigger_type for e in kept])
    except (AttributeError, KeyError):
        pass                                                     # a dump without a .csv has no trigger types
    meta = {"adapter": "idx", "source": origin, "dropped_events": len(all_events) - len(kept)}
    return Events(detector, {(n, "main"): a for n, a in arrays.items()}, ak.Array(quantities), meta)
