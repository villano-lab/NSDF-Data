"""The ROOT RQ adapter: the processed quantities (RQs) of the collaboration's reconstruction, read with uproot. Read only.

The RQs of a series are in a ROOT file with a directory `rqDir` holding `eventTree` (event-level quantities) and `zip<N>` (the
quantities of detector number `N`), row-aligned. This adapter returns them as a **table of quantities**: an Awkward Array with one
record per event whose first fields are the event key (`series`, `dump`, `event`, as in `goldpan.data.KEY_COLUMNS`) followed by the
RQs, so that `goldpan.adapters.rq.attach` can add them to an `Events` of the same events::

    from goldpan.adapters import rq_root, rq
    table = rq_root.read("24260424_145101.root", detector=7, branches=["EventType", "PTOFamps", "P*max", "P*std"])
    events = rq.attach(events, table)

* The detector number is never assumed: pass `detector=`.
* `branches` limits what is read; names may use `*` and `?` (`"P*max"`). `None` reads everything. A branch that the file does
  not have is **filled with NaN** (a series without a channel's RQs is not an error), listed in `meta`-less form by `missing()`.
* The key comes from the file: `DumpNumber` becomes the label `F<dump:04d>` (`3` is `"F0003"`), `EventNumber` is `event`, and
  `series` is `series=` or, by default, the series name found in the file name (`\\d{8}_\\d{4,6}`).
* Values are returned as stored (including a fill value such as -999999 where a detector was not read out).
* `path` may be one file, a list of files or a folder of `.root` files; their events follow one after another.

Needs `uproot` (`pip install uproot`, in `requirements.txt`).
"""
import fnmatch
import re
from pathlib import Path
from typing import Iterator, Optional

import awkward as ak
import numpy as np

from ..status import DONE, status

DIRECTORY = "rqDir"
EVENT_TREE = "eventTree"
SERIES_NAME = re.compile(r"\d{8}_\d{4,6}")
KEY_BRANCHES = ("DumpNumber", "EventNumber")


def _uproot():
    try:
        import uproot
    except ImportError as e:
        raise ImportError("goldpan.adapters.rq_root needs uproot: pip install uproot") from e
    return uproot


def _files(path) -> list:
    if isinstance(path, (list, tuple)):
        files = [Path(p) for p in path]
    else:
        p = Path(path)
        files = sorted(p.glob("*.root")) if p.is_dir() else [p]
    if not files:
        raise FileNotFoundError(f"no .root files in {path}")
    return files


def _trees(f, detector: int):
    try:
        return f[f"{DIRECTORY}/{EVENT_TREE}"], f[f"{DIRECTORY}/zip{detector}"]
    except KeyError as e:
        raise KeyError(f"{f.file_path} has no {DIRECTORY}/{EVENT_TREE} and {DIRECTORY}/zip{detector}: {e}") from None


def _branch_names(tree) -> list:
    return list(tree.keys())


def _wanted(branches, event_names, zip_names):
    """(names in eventTree, names in zip tree, names in neither) for the requested branches."""
    if branches is None:
        return list(event_names), [n for n in zip_names if n not in event_names], []
    from_event, from_zip, missing = [], [], []
    for pattern in branches:
        if any(c in pattern for c in "*?["):
            hits = [n for n in event_names if fnmatch.fnmatchcase(n, pattern)] + \
                   [n for n in zip_names if fnmatch.fnmatchcase(n, pattern) and n not in event_names]
            if not hits:
                missing.append(pattern)
            for n in hits:
                (from_event if n in event_names else from_zip).append(n)
        elif pattern in event_names:
            from_event.append(pattern)
        elif pattern in zip_names:
            from_zip.append(pattern)
        else:
            missing.append(pattern)
    return from_event, from_zip, missing


def _series_of(file: Path, series: Optional[str]) -> str:
    if series is not None:
        return series
    m = SERIES_NAME.search(file.name)
    if not m:
        raise ValueError(f"cannot find a series name (like 24260424_145101) in {file.name}; pass series=")
    return m.group(0)


def _read_file(file: Path, detector: int, branches, series, start=None, stop=None) -> ak.Array:
    uproot = _uproot()
    with uproot.open(file) as f:
        event_tree, zip_tree = _trees(f, detector)
        n_total = event_tree.num_entries
        lo = 0 if start is None else start
        hi = n_total if stop is None else min(stop, n_total)
        from_event, from_zip, missing = _wanted(branches, _branch_names(event_tree), _branch_names(zip_tree))
        keys = event_tree.arrays(list(KEY_BRANCHES), entry_start=lo, entry_stop=hi, library="np")
        n = hi - lo
        columns = {"series": np.full(n, _series_of(file, series)),
                   "dump": np.array([f"F{int(d):04d}" for d in keys["DumpNumber"]], dtype=object),
                   "event": keys["EventNumber"].astype(np.int64)}
        for tree, names in ((event_tree, from_event), (zip_tree, from_zip)):
            if names:
                data = tree.arrays(names, entry_start=lo, entry_stop=hi, library="np")
                for name in names:
                    if name not in columns:
                        columns[name] = data[name]
        for name in missing:
            if not any(c in name for c in "*?["):
                columns[name] = np.full(n, np.nan)
    return ak.Array({k: (ak.Array(v.tolist()) if v.dtype == object else v) for k, v in columns.items()})


@status(DONE)
def read(path, *, detector: int, branches=None, series: Optional[str] = None) -> ak.Array:
    """The RQs of `path` (a file, a list of files or a folder of `.root` files) as a table of quantities, one record per event.

    `detector` is the number of the `zip<N>` tree to read (required). `branches`: names (with `*`/`?` wildcards) to read, `None`
    for all; a name that no tree has is filled with NaN. The first fields are `series`, `dump`, `event`."""
    parts = [_read_file(f, detector, branches, series) for f in _files(path)]
    return parts[0] if len(parts) == 1 else ak.concatenate(parts)


@status(DONE)
def iter_chunks(path, *, chunk: int = 256, detector: int, branches=None, series: Optional[str] = None) -> Iterator[ak.Array]:
    """Yield the table of `read` in pieces of at most `chunk` events, file by file, without reading a file at once."""
    uproot = _uproot()
    for file in _files(path):
        with uproot.open(file) as f:
            n = _trees(f, detector)[0].num_entries
        for start in range(0, n, chunk):
            yield _read_file(file, detector, branches, series, start, start + chunk)


@status(DONE)
def branches(path, *, detector: int) -> dict:
    """The branch names of the first file of `path`: `{"eventTree": [...], "zip<N>": [...]}`."""
    uproot = _uproot()
    with uproot.open(_files(path)[0]) as f:
        event_tree, zip_tree = _trees(f, detector)
        return {EVENT_TREE: _branch_names(event_tree), f"zip{detector}": _branch_names(zip_tree)}


@status(DONE)
def missing(path, *, detector: int, branches) -> list:
    """The requested `branches` (wildcards included) that the first file of `path` does not have, and that `read` fills with NaN."""
    uproot = _uproot()
    with uproot.open(_files(path)[0]) as f:
        event_tree, zip_tree = _trees(f, detector)
        return _wanted(branches, _branch_names(event_tree), _branch_names(zip_tree))[2]
