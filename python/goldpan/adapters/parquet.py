"""The native format of goldpan and goldsluice: Parquet (specification, format version 1).

goldsluice writes it, goldpan reads it, and anything else can read it: the files use **plain Arrow types**, not extension
types, so Polars, DuckDB, pandas and pyarrow open them without goldpan. The design is in `GoldpanGoldsluice/2026-10-25`
and `2026-10-26` (log repository); this docstring is the specification.

**A dataset is a directory**::

    <dataset>/
        _goldpan.json                      the manifest
        <detector>/<series>_<dump>.parquet one file per series dump of a detector

The manifest is JSON: ``{"format": "goldpan-dataset", "format_version": 1, "streams": {<detector>: {"kind": "events",
"main_array": true, "detector": {...}, "files": [relative paths]}}}``. A stream is the table of one detector; only
streams of kind `events` exist so far (time series and ancillary streams are added later without changing this).
A single `.parquet` file is also a valid dataset for the reader.

**A file is the table of one detector's events**, one row per event, with these columns:

* `series` (string), `dump` (string), `event` (int64): the key that identifies an event (event numbers restart in every dump).
* `t_trigger` (float64, optional): the trigger time in seconds, on the clock named in the metadata key `clock`.
* `traces.<channel>.<segment>`: a fixed-size list column per channel and segment (the samples of one trace), any numeric
  dtype; `segment` is `main` for an ordinary trace. Channel and segment names contain no dot.
* every other column is a quantity (an RQ): a number, a string, a list of numbers (variable length is fine), or a struct of
  these (for example a struct per channel with `std` and `max`).

**File metadata** (Parquet key-value, all strings): `goldpan.format_version` (an integer; a reader refuses a newer one),
`goldpan.detector` (JSON: `name`, `channels` with `name`, `role`, `unit`, `input`, and `segments` with `name`, `n_samples`,
`pretrigger_samples`, `glitch_samples`, `sample_period_s`, `start_s`) and `goldpan.meta` (JSON: provenance, units of the
quantities, the clock). Compression is `zstd`; row groups hold a few hundred events, so that a reader can skip groups and read
only some columns.

**Versioning.** An addition that old readers can ignore (a new quantity, a new metadata key) keeps the version; a change they
cannot read raises `goldpan.format_version`. The sample dataset in `python/tests/data/sample_dataset/` is read by the tests of
goldpan and is the file that goldsluice's tests read too.
"""
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Iterator, Optional

import awkward as ak
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ..config import PulseConfig
from ..data import ChannelInfo, Detector, Events, Readout, Segment
from ..status import DONE, status

FORMAT_VERSION = 1
MANIFEST = "_goldpan.json"
TRACE_PREFIX = "traces."
_SAFE = re.compile(r"^[A-Za-z0-9._-]+$")


# ---- the detector as JSON -------------------------------------------------------------------------------------------

def _detector_to_json(detector: Detector) -> dict:
    return {
        "name": detector.name,
        "channels": [{"name": c.name, "role": c.role, "unit": c.unit, "input": c.input} for c in detector.channels],
        "segments": [{"name": s.name, "n_samples": s.n_samples, "pretrigger_samples": s.config.pretrigger_samples,
                      "glitch_samples": s.config.glitch_samples, "sample_period_s": s.config.sample_period_s,
                      "start_s": s.start_s} for s in detector.readout.segments],
    }


def _detector_from_json(d: dict) -> Detector:
    segments = tuple(Segment(s["name"], s["n_samples"],
                             PulseConfig(s["pretrigger_samples"], s["glitch_samples"], s["sample_period_s"]), s["start_s"])
                     for s in d["segments"])
    return Detector(d["name"], tuple(ChannelInfo(c["name"], c["role"], c["unit"], c["input"]) for c in d["channels"]),
                    Readout(segments))


def _safe_name(kind: str, value: str) -> str:
    if not isinstance(value, str) or not _SAFE.match(value):
        raise ValueError(f"{kind} {value!r} cannot be used in a file name: use letters, digits, '.', '_' and '-' only")
    return value


def _check_names(events: Events) -> None:
    for c in events.detector.channels:
        if "." in c.name:
            raise ValueError(f"channel name {c.name!r} contains a dot; the format uses dots to separate channel and segment")
    for s in events.detector.readout.segments:
        if "." in s.name:
            raise ValueError(f"segment name {s.name!r} contains a dot")
    for f in ak.fields(events.quantities):
        if f.startswith(TRACE_PREFIX):
            raise ValueError(f"quantity {f!r} starts with 'traces.', which is reserved for trace columns")


# ---- writing ----------------------------------------------------------------------------------------------------

def _table(events: Events, meta_json: str) -> pa.Table:
    columns = {f: events.quantities[f] for f in ak.fields(events.quantities)}
    for (channel, segment), arr in events.traces.items():
        columns[f"{TRACE_PREFIX}{channel}.{segment}"] = arr
    table = ak.to_arrow_table(ak.Array(columns), extensionarray=False)
    return table.replace_schema_metadata({
        "goldpan.format_version": str(FORMAT_VERSION),
        "goldpan.detector": json.dumps(_detector_to_json(events.detector)),
        "goldpan.meta": meta_json,
    })


@status(DONE)
def write(events: Events, path, *, row_group_size: int = 256) -> None:
    """Write `events` into the dataset directory `path` (created if needed), one file per (series, dump).

    A file of the same series dump is replaced; the manifest gets the stream of this detector. Events added to an existing
    stream must have the same detector (channels and readout). `events.meta` must be JSON-serializable."""
    _check_names(events)
    try:
        meta_json = json.dumps(dict(events.meta))
    except TypeError as e:
        raise TypeError(f"events.meta must be JSON-serializable to be written: {e}") from None
    root = Path(path)
    name = _safe_name("detector name", events.detector.name)
    detector_json = _detector_to_json(events.detector)

    manifest = {"format": "goldpan-dataset", "format_version": FORMAT_VERSION, "streams": {}}
    if (root / MANIFEST).exists():
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if manifest.get("format_version", 0) > FORMAT_VERSION:
            raise ValueError(f"{root} has format version {manifest['format_version']}, newer than this goldpan ({FORMAT_VERSION})")
    stream = manifest["streams"].setdefault(name, {"kind": "events", "main_array": True, "detector": detector_json, "files": []})
    if stream["detector"] != detector_json:
        raise ValueError(f"the stream {name!r} of {root} has a different detector (channels or readout); it cannot be extended")

    (root / name).mkdir(parents=True, exist_ok=True)
    series, dump = events.quantities["series"].to_list(), events.quantities["dump"].to_list()
    for s, d in sorted(set(zip(series, dump))):
        relative = f"{name}/{_safe_name('series', s)}_{_safe_name('dump', d)}.parquet"
        mask = np.array([a == s and b == d for a, b in zip(series, dump)])
        pq.write_table(_table(events.select(mask), meta_json), root / relative, compression="zstd", row_group_size=row_group_size)
        if relative not in stream["files"]:
            stream["files"].append(relative)
    stream["files"].sort()
    (root / MANIFEST).write_text(json.dumps(manifest, indent=1), encoding="utf-8")


# ---- reading ----------------------------------------------------------------------------------------------------

def _files(path, detector: Optional[str]):
    """The files of the stream, and the root they are relative to."""
    p = Path(path)
    if p.is_file():
        return [p]
    if not (p / MANIFEST).exists():
        raise FileNotFoundError(f"{p} has no {MANIFEST}: it is not a goldpan dataset (a single .parquet file also works)")
    manifest = json.loads((p / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("format_version", 0) > FORMAT_VERSION:
        raise ValueError(f"{p} has format version {manifest['format_version']}, newer than this goldpan ({FORMAT_VERSION})")
    streams = {k: v for k, v in manifest["streams"].items() if v.get("kind") == "events"}
    if detector is None:
        if len(streams) != 1:
            raise ValueError(f"{p} has several streams {sorted(streams)}: pass detector=<name>")
        detector = next(iter(streams))
    if detector not in streams:
        raise KeyError(f"{p} has no stream {detector!r}; it has {sorted(streams)}")
    return [p / f for f in streams[detector]["files"]]


def _open(file: Path):
    pf = pq.ParquetFile(file)
    md = pf.schema_arrow.metadata or {}
    version = int(md.get(b"goldpan.format_version", b"0"))
    if version < 1:
        raise ValueError(f"{file} is not a goldpan file (no goldpan.format_version)")
    if version > FORMAT_VERSION:
        raise ValueError(f"{file} has format version {version}, newer than this goldpan ({FORMAT_VERSION})")
    detector = _detector_from_json(json.loads(md[b"goldpan.detector"]))
    meta = json.loads(md.get(b"goldpan.meta", b"{}"))
    return pf, detector, meta


def _columns(pf, detector: Detector, channels) -> list:
    """The columns to read: every quantity column, and the trace columns of the channels asked for (all if None)."""
    if channels is not None:
        for c in channels:
            detector.channel(c)                                           # KeyError for an unknown channel
    wanted = None if channels is None else set(channels)
    out = []
    for name in pf.schema_arrow.names:
        if name.startswith(TRACE_PREFIX):
            if wanted is None or name.split(".", 2)[1] in wanted:
                out.append(name)
        else:
            out.append(name)
    return out


def _to_events(table: pa.Table, detector: Detector, meta: dict) -> Events:
    arr = ak.from_arrow(table)
    traces, quantities = {}, {}
    for name in ak.fields(arr):
        if name.startswith(TRACE_PREFIX):
            _, channel, segment = name.split(".", 2)
            traces[(channel, segment)] = ak.to_numpy(arr[name])
        else:
            quantities[name] = arr[name]
    return Events(detector, traces, ak.Array(quantities), meta)


@status(DONE)
def read(path, *, detector: Optional[str] = None, channels=None, events=None) -> Events:
    """Read the stream of one detector of a dataset (or a single file) into one `Events`.

    `detector` names the stream when the dataset has several; `channels` limits the trace columns that are read; `events` is a
    slice or a list of positions to keep (applied after reading: for a dataset larger than memory use `iter_chunks`)."""
    parts = []
    files = _files(path, detector)
    for file in files:
        pf, det, meta = _open(file)
        parts.append(_to_events(pf.read(columns=_columns(pf, det, channels)), det, meta))
    result = Events.concatenate(*parts)
    result = Events(result.detector, dict(result.traces), result.quantities,
                    {**dict(parts[0].meta), "source_files": [str(f) for f in files]})
    if events is not None:
        n = result.n_events
        result = result.select(np.arange(n)[events] if isinstance(events, slice) else np.asarray(events))
    return result


@status(DONE)
def iter_chunks(path, *, chunk: int = 256, detector: Optional[str] = None, channels=None) -> Iterator[Events]:
    """Yield the events of the stream as `Events` of at most `chunk` events, file by file, without reading a file at once.

    This is how a dataset larger than memory is processed; the functions of goldpan work on any chunk."""
    for file in _files(path, detector):
        pf, det, meta = _open(file)
        meta = {**meta, "source_file": str(file)}
        for batch in pf.iter_batches(batch_size=chunk, columns=_columns(pf, det, channels)):
            yield _to_events(pa.Table.from_batches([batch]), det, meta)
