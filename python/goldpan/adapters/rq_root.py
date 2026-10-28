"""The ROOT RQ adapter: the processed quantities (RQs) of the collaboration's reconstruction, read with uproot; and `write`, which
puts our own processed quantities into the same layout.

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

Writing (`write`) keeps **our names**: a channel's quantities become branches `<channel>_<quantity>` (`Side2pC_adc_max`) in `zip<N>`,
not the collaboration's `P<letter>S<side><quantity>`. Only the container is theirs: `rqDir/eventTree` with `SeriesNumber`,
`DumpNumber`, `EventNumber`, `rqDir/zip<N>` row-aligned with it, every branch a `double`. `read` reads the files back.
"""
import fnmatch
import json
import re
from pathlib import Path
from typing import Iterator, Optional

import awkward as ak
import numpy as np

from ..data import KEY_COLUMNS, Events
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


# ---- writing: our quantities in the layout of the RQ files, under our own names

_BRANCH_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DUMP_LABEL = re.compile(r"^F(\d+)$")


def _series_number(series: str) -> float:
    digits = str(series).replace("_", "")
    if not digits.isdigit():
        raise ValueError(f"cannot make a series number of {series!r}: expected digits and underscores, like 24260424_145101")
    return float(int(digits))


def _dump_number(dump: str) -> float:
    m = _DUMP_LABEL.match(str(dump))
    if not m:
        raise ValueError(f"cannot make a dump number of {dump!r}: expected a label like F0001")
    return float(int(m.group(1)))


def _flat_quantities(quantities: ak.Array) -> dict:
    """`{branch name: float64 array}`: a record field `Side2pC: {adc_max}` becomes `Side2pC_adc_max`, a plain field keeps its name."""
    columns = {}
    for name in ak.fields(quantities):
        if name in KEY_COLUMNS:
            continue
        field = quantities[name]
        inner = ak.fields(field)
        for branch, values in ([(f"{name}_{k}", field[k]) for k in inner] if inner else [(name, field)]):
            if not _BRANCH_NAME.match(branch):
                raise ValueError(f"{branch!r} is not a usable branch name: letters, digits and underscores, not starting with a digit")
            columns[branch] = np.asarray(ak.to_numpy(values), dtype=np.float64)
    return columns


@status(DONE)
def write(events: Events, path, *, detector: int) -> list:
    """Write the quantities of `events` (their pulses are not written) as RQ-style ROOT files in the folder `path`; returns the
    files. One file per series and dump, `<series>_<dump>.root`, which `read` accepts (a folder of them is one dataset).

    Each file has `rqDir/eventTree` (`SeriesNumber`, `DumpNumber`, `EventNumber`) and `rqDir/zip<detector>` (one branch
    `<channel>_<quantity>` for each quantity of each channel, our names), row-aligned, every branch a `double`. A
    `goldsluice` entry in `events.meta` (the provenance of a batch run) is stored as the string `infoDir/goldsluice`.
    `detector` is the number of the `zip<N>` tree: it is never assumed. An existing file of the same name is replaced."""
    uproot = _uproot()
    columns = _flat_quantities(events.quantities)
    if not columns:
        raise ValueError("the events have no quantities to write (only the keys)")
    series = np.array(events.quantities["series"].to_list(), dtype=object)
    dump = np.array(events.quantities["dump"].to_list(), dtype=object)
    event = np.asarray(ak.to_numpy(events.quantities["event"]), dtype=np.float64)
    folder = Path(path)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for pair in sorted({(a, b) for a, b in zip(series, dump)}):
        take = (series == pair[0]) & (dump == pair[1])
        n = int(take.sum())
        file = folder / f"{pair[0]}_{pair[1]}.root"
        with uproot.recreate(file) as f:
            f[f"{DIRECTORY}/{EVENT_TREE}"] = {"SeriesNumber": np.full(n, _series_number(pair[0])),
                                              "DumpNumber": np.full(n, _dump_number(pair[1])),
                                              "EventNumber": event[take]}
            f[f"{DIRECTORY}/zip{int(detector)}"] = {name: values[take] for name, values in columns.items()}
            if "goldsluice" in events.meta:
                f["infoDir/goldsluice"] = json.dumps(dict(events.meta["goldsluice"]), sort_keys=True, default=str)
        written.append(file)
    return written
