"""The in-memory container of one detector's events: traces, quantities, readout, provenance.

This is the middle of the design in `GoldpanGoldsluice/2026-10-25` (log repository): file formats live in adapters, the
functions of goldpan are pure, and what passes between them is an `Events`, **immutable**. The simplest version is
built first: one detector, and the traces of a channel are held in named *segments* (here only the default,
`"main"`), so that hybrid sampling later (a coarse and a fine segment) changes no signature and no file.

An `Events` has

* a `Detector`: its name, its channels (name, role, the readout unit and input they come through) and its `Readout`
  (the segments of a trace, each with a `PulseConfig`);
* `traces`: `{(channel, segment): array of shape (n_events, n_samples_of_the_segment)}`, read-only (use `ev.trace(channel)`);
* `quantities`: an Awkward Array, one record per event. Its first fields identify the event, `series`, `dump` and `event`
  (event numbers restart in every dump), and `t_trigger` (seconds on the clock named in `meta["clock"]`) may follow; the
  rest are the quantities (RQs). Flat numbers and variable-length lists are both fields.
* `meta`: provenance (source files, program versions, units of the quantities, the clock).

Nothing here opens a file. Build one by hand with `Events.from_arrays` (for a notebook or a test) or get one from an
adapter.
"""
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional

import awkward as ak
import numpy as np

from .config import PulseConfig

MAIN = "main"
"""The name of the default segment of a trace."""

KEY_COLUMNS = ("series", "dump", "event")
"""The fields that identify an event in `Events.quantities`; they cannot be replaced by `with_quantities`."""

TIME_COLUMN = "t_trigger"
"""The optional field with the trigger time in seconds, on the clock named in `Events.meta["clock"]`."""


@dataclass(frozen=True)
class ChannelInfo:
    name: str
    """The channel's name, unique inside its detector (for example `Side2pC`)."""

    role: Optional[str] = None
    """What the channel measures (`phonon`, `charge`, ...), so that a cut can be applied to every channel of a role."""

    unit: Optional[str] = None
    """The readout unit (a board) the channel comes through, if that matters."""

    input: Optional[str] = None
    """The input on that unit."""


@dataclass(frozen=True)
class Segment:
    name: str
    """The segment's name: `main` for an ordinary trace, `coarse` and `fine` for hybrid sampling."""

    n_samples: int
    """Samples per trace in this segment."""

    config: PulseConfig
    """The readout of this segment: its pretrigger window, glitch samples and sample period."""

    start_s: Optional[float]
    """Time of the first sample relative to the trigger, in seconds (negative before it); `None` if unknown."""

    @classmethod
    def main(cls, n_samples: int, config: PulseConfig) -> "Segment":
        """The ordinary single segment: the trigger is sample `config.pretrigger_samples`."""
        start = None if config.sample_period_s is None else -config.pretrigger_samples * config.sample_period_s
        return cls(MAIN, n_samples, config, start)


@dataclass(frozen=True)
class Readout:
    segments: tuple
    """The `Segment`s of a trace, with unique names."""

    def __post_init__(self):
        object.__setattr__(self, "segments", tuple(self.segments))
        names = [s.name for s in self.segments]
        if not names:
            raise ValueError("a Readout needs at least one segment")
        if len(set(names)) != len(names):
            raise ValueError(f"segment names must be unique, got {names}")

    @classmethod
    def single(cls, n_samples: int, config: PulseConfig) -> "Readout":
        """A readout with the one segment `main`."""
        return cls((Segment.main(n_samples, config),))

    def segment(self, name: str = MAIN) -> Segment:
        for s in self.segments:
            if s.name == name:
                return s
        raise KeyError(f"no segment {name!r}; this readout has {[s.name for s in self.segments]}")

    def config(self, name: str = MAIN) -> PulseConfig:
        """The `PulseConfig` to pass to the functions of goldpan for this segment."""
        return self.segment(name).config

    def time_axis(self, name: str = MAIN) -> np.ndarray:
        """Time of each sample of the segment in seconds relative to the trigger (needs the sample period and start)."""
        seg = self.segment(name)
        if seg.config.sample_period_s is None or seg.start_s is None:
            raise ValueError(f"segment {name!r} has no sample period or start time, so it has no time axis")
        return seg.start_s + np.arange(seg.n_samples) * seg.config.sample_period_s


@dataclass(frozen=True)
class Detector:
    name: str
    """The detector's name, unique inside a dataset."""

    channels: tuple
    """The `ChannelInfo`s of the detector, with unique names."""

    readout: Readout
    """How its traces are sampled."""

    def __post_init__(self):
        object.__setattr__(self, "channels", tuple(self.channels))
        names = [c.name for c in self.channels]
        if len(set(names)) != len(names):
            raise ValueError(f"channel names must be unique inside detector {self.name!r}, got {names}")

    def channel_names(self) -> list:
        """The names of the channels, in order."""
        return [c.name for c in self.channels]

    def channel(self, name: str) -> ChannelInfo:
        """The `ChannelInfo` called `name`."""
        for c in self.channels:
            if c.name == name:
                return c
        raise KeyError(f"detector {self.name!r} has no channel {name!r}; it has {self.channel_names()}")

    def channels_with_role(self, role: str) -> list:
        """The names of the channels whose role is `role`, in order."""
        return [c.name for c in self.channels if c.role == role]


@dataclass(frozen=True, eq=False)
class Events:
    detector: Detector
    """The detector these events were recorded by."""

    traces: Mapping[tuple, np.ndarray]
    """`{(channel, segment): (n_events, n_samples)}`, read-only views."""

    quantities: ak.Array
    """One record per event: the key fields, the optional `t_trigger`, then the quantities."""

    meta: Mapping[str, Any] = field(default_factory=dict)
    """Provenance and units; a read-only copy."""

    def __post_init__(self):
        q = self.quantities if isinstance(self.quantities, ak.Array) else ak.Array(self.quantities)
        fields = ak.fields(q)
        missing = [k for k in KEY_COLUMNS if k not in fields]
        if missing:
            raise ValueError(f"quantities must have the key fields {list(KEY_COLUMNS)}; missing {missing}")
        n = len(q)
        views = {}
        for key, arr in dict(self.traces).items():
            if not (isinstance(key, tuple) and len(key) == 2):
                raise ValueError(f"traces are keyed by (channel, segment), got {key!r}")
            channel, segment = key
            self.detector.channel(channel)                       # raises KeyError for an unknown channel
            seg = self.detector.readout.segment(segment)         # and for an unknown segment
            arr = np.asarray(arr)
            if arr.ndim != 2 or arr.shape != (n, seg.n_samples):
                raise ValueError(f"traces[{key}] has shape {arr.shape}, expected ({n}, {seg.n_samples})")
            view = arr.view()
            view.flags.writeable = False
            views[key] = view
        object.__setattr__(self, "quantities", q)
        object.__setattr__(self, "traces", MappingProxyType(views))
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))

    @classmethod
    def from_arrays(cls, detector: Detector, traces: Mapping[str, Any], *, series="", dump="", event=None,
                    quantities: Optional[Mapping[str, Any]] = None, meta: Optional[Mapping[str, Any]] = None) -> "Events":
        """Build `Events` by hand: `traces` is `{channel: (n_events, n_samples)}` (segment `main`).

        `series` and `dump` are one value for every event or one per event; `event` defaults to 0, 1, 2, ...
        `quantities` adds more columns."""
        arrays = {c: np.asarray(a) for c, a in traces.items()}
        if not arrays:
            raise ValueError("traces is empty")
        n = len(next(iter(arrays.values())))
        event = np.arange(n) if event is None else np.asarray(event)
        columns = {
            "series": np.broadcast_to(np.asarray(series), (n,)),
            "dump": np.broadcast_to(np.asarray(dump), (n,)),
            "event": event,
        }
        for name, values in (quantities or {}).items():
            if name in KEY_COLUMNS:
                raise ValueError(f"{name!r} is a key field and is given by its own argument")
            columns[name] = values
        return cls(detector, {(c, MAIN): a for c, a in arrays.items()}, ak.Array(columns), dict(meta or {}))

    @property
    def n_events(self) -> int:
        return len(self.quantities)

    def __len__(self) -> int:
        return self.n_events

    def __repr__(self) -> str:
        return (f"Events(detector={self.detector.name!r}, n_events={self.n_events}, "
                f"traces={sorted(self.traces)}, quantities={ak.fields(self.quantities)})")

    def trace(self, channel: str, segment: str = MAIN) -> np.ndarray:
        """The read-only array `(n_events, n_samples)` of a channel's segment."""
        try:
            return self.traces[(channel, segment)]
        except KeyError:
            raise KeyError(f"no traces for channel {channel!r}, segment {segment!r}; have {sorted(self.traces)}") from None

    def time_axis(self, segment: str = MAIN) -> np.ndarray:
        """Time of each sample of `segment`, seconds relative to the trigger, from this detector's own readout."""
        return self.detector.readout.time_axis(segment)

    def select(self, where) -> "Events":
        """The events where `where` is True (a boolean array of length `n_events`) or at the given integer positions."""
        where = np.asarray(where)
        if where.dtype == bool and where.shape != (self.n_events,):
            raise ValueError(f"a mask must have shape ({self.n_events},), got {where.shape}")
        idx = np.flatnonzero(where) if where.dtype == bool else where
        return Events(self.detector, {k: a[idx] for k, a in self.traces.items()}, self.quantities[idx], dict(self.meta))

    def with_quantities(self, **columns) -> "Events":
        """A new `Events` with columns added or replaced; each value has one entry per event. Key fields cannot be replaced."""
        q = self.quantities
        for name, values in columns.items():
            if name in KEY_COLUMNS:
                raise ValueError(f"{name!r} identifies the events and cannot be replaced")
            values = ak.Array(values) if not isinstance(values, ak.Array) else values
            if len(values) != self.n_events:
                raise ValueError(f"column {name!r} has {len(values)} entries for {self.n_events} events")
            q = ak.with_field(q, values, name)
        return Events(self.detector, dict(self.traces), q, dict(self.meta))

    @staticmethod
    def concatenate(*events: "Events") -> "Events":
        """The events of several `Events` of the same detector, one after another (meta of the first is kept)."""
        if not events:
            raise ValueError("nothing to concatenate")
        first = events[0]
        for other in events[1:]:
            if other.detector != first.detector:
                raise ValueError("cannot concatenate events of different detectors or readouts")
            if sorted(other.traces) != sorted(first.traces):
                raise ValueError("cannot concatenate events with different traces")
            if sorted(ak.fields(other.quantities)) != sorted(ak.fields(first.quantities)):
                raise ValueError("cannot concatenate events with different quantities")
        traces = {k: np.concatenate([e.traces[k] for e in events], axis=0) for k in first.traces}
        return Events(first.detector, traces, ak.concatenate([e.quantities for e in events]), dict(first.meta))
