"""The MIDAS adapter: raw SuperCDMS SNOLAB DAQ files (`.mid`, `.mid.gz`, `.mid.lz4`) into an `Events`. Read only.

A file is a sequence of MIDAS events. The first (id `0x8000`, begin of run) carries the ODB, the experiment's settings, as XML; the
last (id `0x8001`, end of run) carries it again; each event in between (id `1`) holds a bank `SCD0` with one trigger in the SNOLAB
data format (the CDMS I/O library, `CDMSIOLIB::pack_event`; this reader follows `unpack_event`, format versions 4 to 8) and
sometimes a veto bank `LDV0`. Polling-cycle events (trigger type 8) and events of other detectors carry no traces and are skipped.
The format is described at https://gitlab.com/supercdms/DAQ/IOLibrary (README, "Description of Data Structures").

Like the idx adapter, this one does not know your detector: you say which detector number and which channel numbers are the
named channels, and you name the readout, which is checked against the sample rate in the file::

    from goldpan.adapters import midas
    from goldpan.config import Z7
    ev = midas.read("24260424_145101_F0001.mid.lz4", detector_name="Z7", detector_id=7, config=Z7, max_events=100,
                    channels={"PAS1": 0, "PAS2": 1, "PBS1": 2})              # channel name -> channel number

* `channels` are **phonon** channels (`channel_type=1`; pass `channel_type=0` for charge). The traces keep the file's `uint16`.
* Only the channels you name are copied; the others are read past, so a 15 GB file costs a pass over it. Use `max_events=` to stop
  early, or `iter_chunks` to process a file in pieces.
* Event quantities: `series` and `dump` (from a file name like `<series>_F0003.mid.lz4`, or `series=`/`dump=`), `event` (the event
  number), `trigger_id`, `trigger_type` (as text: "Physics", "BeginOfRunRandom", ...), `readout_type` and `global_timestamp`.
* `meta`: `run` (run number, state, start and stop time from the ODB), `complete` (the end-of-run event was seen: a file cut short
  is not complete), `skipped_events`, `format_version`, `source`.
* Hybrid sampling (pre- or post-pulse samples at a coarser rate) is not read yet: such a file raises `NotImplementedError`.

`.mid.lz4` files need the `lz4` package (`pip install lz4`); `.mid.gz` and plain `.mid` need nothing.
"""
import gzip
import re
import struct
from collections import namedtuple
from pathlib import Path
from typing import Iterator, Mapping, Optional

import numpy as np

from ..config import PulseConfig
from ..data import ChannelInfo, Detector, Events, Readout
from ..status import DONE, status

EVENT_BEGIN_OF_RUN = 0x8000
EVENT_END_OF_RUN = 0x8001
EVENT_DATA = 1
PHONON, CHARGE = 1, 0

TRIGGER_TYPES = {1: "Physics", 2: "BeginOfRunRandom", 3: "InRunRandom", 4: "EndOfRunRandom", 5: "BaselineControlRandom",
                 6: "BeginOfRunTestSignal", 7: "EndOfRunTestSignal", 8: "PollingCycleMetadata", 9: "SaltingStub",
                 10: "SDUAccelerometerChannel0", 11: "SDUAccelerometerChannel1", 12: "SDUAccelerometerChannel2",
                 13: "SDUAccelerometerChannel3", 14: "SDULEMO", 15: "SDUAntenna", 16: "SDUSync", 17: "SDUPileUp"}

# head nibbles of the blocks of the SNOLAB data format (cdms_iolibrary.h)
_HEAD = dict(channel=0x0, channelBlock=0x1, detectorBlock=0x2, detectorHead=0x3, trigger=0x5, primBlock=0x6, primHead=0x7,
             trailer=0x8, overall=0x9, sduPrimHead=0xA, sduBlock=0xC, sduChannelHead=0xD, sduChannelBlock=0xE, sduHead=0xF)

RawEvent = namedtuple("RawEvent", "event_id mask serial timestamp data")


class MidasFormatError(ValueError):
    """The file does not follow the SNOLAB data format (the message says where)."""


# ---- the file --------------------------------------------------------------------------------------------------

def _open(path):
    name = str(path)
    if name.endswith(".lz4"):
        try:
            import lz4.frame
        except ImportError as e:
            raise ImportError("reading .mid.lz4 files needs the lz4 package: pip install lz4") from e
        return lz4.frame.open(name, "rb")
    if name.endswith(".gz"):
        return gzip.open(name, "rb")
    return open(name, "rb")


def _read_exactly(f, n):
    """`n` bytes, fewer only at the end of the file; a stream cut short in the middle counts as the end."""
    parts, have = [], 0
    try:
        while have < n:
            chunk = f.read(n - have)
            if not chunk:
                break
            parts.append(chunk)
            have += len(chunk)
    except (EOFError, RuntimeError, OSError):
        pass
    return b"".join(parts)


@status(DONE)
def iter_events(path) -> Iterator[RawEvent]:
    """The MIDAS events of a file one by one, as `RawEvent(event_id, mask, serial, timestamp, data)` with `data` the bytes
    after the 16-byte header. A file that stops in the middle of an event ends there without an error."""
    with _open(path) as f:
        while True:
            head = _read_exactly(f, 16)
            if len(head) < 16:
                return
            event_id, mask, serial, timestamp, size = struct.unpack("<HHIII", head)
            data = _read_exactly(f, size)
            if len(data) < size:
                return
            yield RawEvent(event_id, mask, serial, timestamp, data)


_ODB_KEYS = {"run_number": "Run number", "state": "State", "start_time": "Start time binary", "stop_time": "Stop time binary"}


@status(DONE)
def parse_odb(xml) -> dict:
    """The run information of an ODB (XML bytes of a begin- or end-of-run event), from its `/Runinfo` directory: `run_number`,
    `state` (as stored; the real begin- and end-of-run dumps show 1 and 3), `start_time` and `stop_time` (unix seconds; 0 while running).
    Keys that are not found are left out; the rest of the ODB (tens of megabytes) is not parsed."""
    text = xml.decode("latin-1") if isinstance(xml, (bytes, bytearray)) else xml
    m = re.search(r'<dir name="Runinfo"[^>]*>', text)
    if not m:
        return {}
    section = text[m.end():text.find("</dir>", m.end())]
    out = {}
    for field, key in _ODB_KEYS.items():
        k = re.search(r'<key name="' + re.escape(key) + r'" type="[A-Z0-9]+"[^>]*>(-?\d+)</key>', section)
        if k:
            out[field] = int(k.group(1))
    return out


# ---- one trigger ---------------------------------------------------------------------------------------------------

@status(DONE)
def unpack_scd0(data: bytes, want: Optional[Mapping] = None, channel_type: int = PHONON) -> dict:
    """The trigger in the `SCD0` bank of a MIDAS data event.

    Returns `dict(format_version, trigger_id, event_number, trigger_type, readout_type, global_timestamp, detectors)` where
    `detectors` maps a detector number to `{channel_number: dict(rate_khz, downsampling, pretrigger, pre, on, post, data)}`.
    `want` (`{detector: {channel numbers}}`) keeps the waveforms of those channels of type `channel_type` only (the others are read
    past); `None` keeps every channel. Returns `None` for an event without an `SCD0` bank."""
    banks, pos = {}, 8
    while pos + 12 <= len(data):
        name, _, size = struct.unpack_from("<4sII", data, pos)
        banks[name.decode("latin-1")] = (pos + 12, size)
        pos += 12 + size
    if "SCD0" not in banks:
        return None
    start, size = banks["SCD0"]
    d = np.frombuffer(data, dtype="<u4", count=size // 4, offset=start)
    state = {"p": 0}

    def take():
        state["p"] += 1
        return int(d[state["p"] - 1])

    def head(kind):
        v = take()
        if v >> 28 != _HEAD[kind]:
            raise MidasFormatError(f"expected a {kind} head (nibble {_HEAD[kind]:#x}), found {v >> 28:#x} at word {state['p'] - 1}")
        return v & 0x0FFFFFFF

    v = take()
    if v >> 28 != _HEAD["overall"]:
        raise MidasFormatError("the SCD0 bank does not start with the overall header")
    version = (v >> 12) & 0xFFFF
    if not 4 <= version <= 8:
        raise MidasFormatError(f"format version {version} is not supported (4 to 8)")
    head("trigger")
    ev = dict(format_version=version, trigger_id=take(), event_number=take())
    v = take()
    ev["readout_type"], ev["trigger_type"] = v >> 8, v & 0xFF
    lo, hi = take(), take()
    ev["global_timestamp"] = (hi << 32) | lo
    take(), take()                                                                # polling cycle end time and fraction
    n_prims = head("primHead")
    take()
    for _ in range(n_prims):
        head("primBlock")
        for _ in range(6 if version >= 3 else 5):
            take()
    detectors = {}
    for _ in range(head("detectorHead")):
        v = take()
        if v >> 28 != _HEAD["detectorBlock"]:
            raise MidasFormatError("expected a detector block")
        det_id = (v >> 2) & 0xFF
        for _ in range(6):               # serials and versions, readout status and series time, fraction, waveform read times (3)
            take()
        keep = None if want is None else want.get(det_id, ())
        chans = {}
        for _ in range(head("channel")):
            v = take()
            if v >> 28 != _HEAD["channelBlock"]:
                raise MidasFormatError("expected a channel block")
            c_num, c_type = (v >> 2) & 0xF, v & 1
            pretrigger = (v >> 6) & 0x3FFFFF
            pre, on, post, rate = take(), take(), take(), take()
            n = pre + on + post
            rows = (n + 1) // 2
            if c_type == channel_type and (want is None or c_num in keep):
                chans[c_num] = dict(rate_khz=rate >> 16, downsampling=rate & 0xFFFF, pretrigger=pretrigger, pre=pre, on=on,
                                    post=post, data=d[state["p"]:state["p"] + rows].view("<u2")[:n].copy())
            state["p"] += rows
        detectors[det_id] = chans
    ev["detectors"] = detectors
    n_sdu_prims = head("sduPrimHead")
    take()
    for _ in range(n_sdu_prims):
        for _ in range(7):
            take()
    for _ in range(head("sduHead")):     # the SDU (accelerometers, antenna, LEMO): present, skipped
        take()
        for _ in range(4):
            take()
        for _ in range(head("sduChannelHead")):
            take()
            n = take()
            take()
            state["p"] += (n + 1) // 2
    head("trailer")
    return ev


# ---- reading -----------------------------------------------------------------------------------------------------------

_NAME = re.compile(r"(?P<series>\d{8}_\d{4,6})_F(?P<dump>\d+)")


def _series_and_dump(path, series, dump):
    m = _NAME.search(Path(path).name)
    if series is None:
        if not m:
            raise ValueError(f"cannot find a series name (like 24260424_145101_F0001) in {Path(path).name}; pass series= and dump=")
        series = m.group("series")
    if dump is None:
        dump = f"F{int(m.group('dump')):04d}" if m else "F0000"
    return series, dump


def _check_rate(chan, number, config: PulseConfig):
    """The sample rate in the file against the readout the user named: the library never assumes one."""
    if config.sample_period_s is None:
        return
    in_file = 1.0 / (chan["rate_khz"] * 1e3)
    if abs(in_file - config.sample_period_s) > 0.01 * config.sample_period_s:
        raise ValueError(f"channel {number}: the file samples every {in_file * 1e6:g} us ({chan['rate_khz']} kHz) but the readout "
                         f"you gave says {config.sample_period_s * 1e6:g} us; use the config of this data (goldpan.config)")


def _scan(path, *, detector_id, channels, channel_type, config, series, dump, max_events):
    """Yield `("odb", info)`, `("event", dict)` and `("end", info)` for the events of a file that hold the requested channels."""
    series, dump = _series_and_dump(path, series, dump)
    want = {detector_id: set(channels.values())}
    skipped = taken = 0
    for raw in iter_events(path):
        if raw.event_id == EVENT_BEGIN_OF_RUN:
            yield "odb", parse_odb(raw.data)
        elif raw.event_id == EVENT_END_OF_RUN:
            yield "end", dict(parse_odb(raw.data), skipped_events=skipped, complete=True)
            return
        elif raw.event_id == EVENT_DATA:
            ev = unpack_scd0(raw.data, want, channel_type)
            chans = None if ev is None else ev["detectors"].get(detector_id)
            if not chans:
                skipped += 1
                continue
            missing = sorted(set(channels.values()) - set(chans))
            if missing:
                raise ValueError(f"event {ev['event_number']} has no channels {missing} of detector {detector_id} "
                                 f"(type {channel_type}); it has {sorted(chans)}")
            for number, c in chans.items():
                if c["pre"] or c["post"]:
                    raise NotImplementedError("pre- or post-pulse samples (hybrid sampling) are not read yet")
                _check_rate(c, number, config)
            ev["traces"] = {name: chans[number]["data"] for name, number in channels.items()}
            ev["series"], ev["dump"] = series, dump
            yield "event", ev
            taken += 1
            if max_events is not None and taken >= max_events:
                yield "end", dict(skipped_events=skipped, complete=False)
                return
    yield "end", dict(skipped_events=skipped, complete=False)


def _build(rows, detector_name, channels, config, roles, meta) -> Events:
    roles = roles or {}
    n_samples = len(next(iter(rows[0]["traces"].values())))
    detector = Detector(detector_name, tuple(ChannelInfo(n, role=roles.get(n), input=str(num)) for n, num in channels.items()),
                        Readout.single(n_samples, config))
    traces = {n: np.stack([r["traces"][n] for r in rows]) for n in channels}
    quantities = {"trigger_id": [r["trigger_id"] for r in rows],
                  "trigger_type": [TRIGGER_TYPES.get(r["trigger_type"], "Unknown") for r in rows],
                  "readout_type": [r["readout_type"] for r in rows],
                  "global_timestamp": np.array([r["global_timestamp"] for r in rows], dtype=np.int64)}
    return Events.from_arrays(detector, traces, series=rows[0]["series"], dump=rows[0]["dump"],
                              event=[r["event_number"] for r in rows], quantities=quantities,
                              meta={**meta, "format_version": rows[0]["format_version"]})


def _run_meta(odb, end):
    return {**odb, **{k: v for k, v in end.items() if k in _ODB_KEYS}}


@status(DONE)
def read(path, *, detector_name: str, detector_id: int, channels: Mapping[str, int], config: PulseConfig, roles=None,
         channel_type: int = PHONON, series: Optional[str] = None, dump: Optional[str] = None,
         max_events: Optional[int] = None) -> Events:
    """The events of a MIDAS file in which `detector_id` has the `channels` (name -> channel number), as `Events`.

    `config` is the readout of the data; its sample period is checked against the file. `max_events` stops after that many events
    (a whole file can be 15 GB). `meta["complete"]` is True only if the end-of-run event was reached."""
    rows, odb, end = [], {}, {}
    for kind, item in _scan(path, detector_id=detector_id, channels=channels, channel_type=channel_type, config=config,
                            series=series, dump=dump, max_events=max_events):
        if kind == "odb":
            odb = item
        elif kind == "event":
            rows.append(item)
        else:
            end = item
    if not rows:
        raise ValueError(f"{path} has no events with channels {list(channels.values())} of detector {detector_id}")
    meta = {"adapter": "midas", "source": str(path), "run": _run_meta(odb, end),
            "complete": bool(end.get("complete", False)),
            "skipped_events": end.get("skipped_events", 0)}
    return _build(rows, detector_name, channels, config, roles, meta)


@status(DONE)
def iter_chunks(path, *, chunk: int = 256, detector_name: str, detector_id: int, channels: Mapping[str, int],
                config: PulseConfig, roles=None, channel_type: int = PHONON, series: Optional[str] = None,
                dump: Optional[str] = None, max_events: Optional[int] = None) -> Iterator[Events]:
    """Yield the events of `read` in pieces of at most `chunk` events, reading the file once from the start. Every chunk's
    `meta["run"]` has the begin-of-run information; whether the file is complete is only known to `read`."""
    rows, odb, count = [], {}, 0
    meta = {"adapter": "midas", "source": str(path)}
    for kind, item in _scan(path, detector_id=detector_id, channels=channels, channel_type=channel_type, config=config,
                            series=series, dump=dump, max_events=max_events):
        if kind == "odb":
            odb = item
        elif kind == "event":
            rows.append(item)
            if len(rows) >= chunk:
                yield _build(rows, detector_name, channels, config, roles, {**meta, "run": odb})
                rows = []
    if rows:
        yield _build(rows, detector_name, channels, config, roles, {**meta, "run": odb})
