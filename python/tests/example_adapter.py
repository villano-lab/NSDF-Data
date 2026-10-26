"""The complete example adapter of the guide "Writing an adapter" (docs/developers/writing-an-adapter.pdf).

The format is invented and as small as can be: a NumPy `.npz` file with one array `(n_events, n_samples)` per channel, an optional
`event` array and an optional `period_s` (seconds per sample). Everything an adapter has to do is here, in one page:

* the user names the detector and the readout (`config`); the adapter never assumes them;
* the one thing the file knows (its sample period) is checked against the readout the user named;
* the traces become an `Events`, whose constructor checks the shapes and the key fields and makes the traces read-only;
* `iter_chunks` gives the same events in pieces, `write` makes a file that `read` reads back.
"""
from pathlib import Path
from typing import Iterator, Optional

import numpy as np

from goldpan.config import PulseConfig
from goldpan.data import ChannelInfo, Detector, Events, Readout

NOT_CHANNELS = ("event", "period_s")


def read(path, *, detector_name: str, config: PulseConfig, channels: Optional[list] = None, series: str = "",
         dump: str = "F0000") -> Events:
    """The events of an `.npz` file; `channels` names the arrays to read (default: all that are not `event` or `period_s`)."""
    with np.load(path) as f:
        names = list(channels) if channels else [k for k in f.files if k not in NOT_CHANNELS]
        missing = [n for n in names if n not in f.files]
        if missing:
            raise KeyError(f"{path} has no arrays {missing}; it has {f.files}")
        if "period_s" in f.files and config.sample_period_s is not None:
            in_file = float(f["period_s"])
            if abs(in_file - config.sample_period_s) > 0.01 * config.sample_period_s:
                raise ValueError(f"the file samples every {in_file * 1e6:g} us but the readout you gave says "
                                 f"{config.sample_period_s * 1e6:g} us")
        traces = {n: f[n] for n in names}
        event = f["event"] if "event" in f.files else None
    n_samples = next(iter(traces.values())).shape[1]
    detector = Detector(detector_name, tuple(ChannelInfo(n, role="phonon") for n in names), Readout.single(n_samples, config))
    return Events.from_arrays(detector, traces, series=series, dump=dump, event=event,
                              meta={"adapter": "npz", "source": str(Path(path))})


def iter_chunks(path, *, chunk: int = 256, **kwargs) -> Iterator[Events]:
    """The same events, at most `chunk` at a time (a real adapter reads the file in pieces; this one is small)."""
    events = read(path, **kwargs)
    for start in range(0, len(events), chunk):
        yield events.select(np.arange(start, min(start + chunk, len(events))))


def write(events: Events, path) -> None:
    """A file that `read` reads back: one array per channel, the event numbers and the sample period."""
    config = events.detector.readout.config()
    arrays = {n: events.trace(n) for n in events.detector.channel_names()}
    with open(path, "wb") as f:                      # a file object: np.savez would add ".npz" to a path
        np.savez(f, event=np.asarray(events.quantities["event"].to_list()), period_s=config.sample_period_s, **arrays)
