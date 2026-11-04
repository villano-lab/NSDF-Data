"""The RQs of a whole list of series at once, as numpy arrays, with an on-disk cache: the second read is fast.

The call is that of the collaboration's `rqdata`, so that an analysis can move over with its lines unchanged::

    from goldpan.rqdata import load

    RQS = ["EventType", "PTOFamps", "P*max", "P*std"]            # P* = all 12 phonon channels
    data = load("24260424_145101", RQS)                         # a series name, a list of them, or a CSV with a `series` column
    data["PTOFamps"]                                            # one numpy array over every event of every series
    data["series"]                                              # which series each row came from (also "dump" and "event")
    data.files                                                  # series -> the file that was read

Each branch comes back as one array with the rows of the files one after the other. A branch name is looked up in `eventTree`
first, then in `zip<N>`; a branch a file does not have is filled with NaN for that file; a name with `*`, `?` or `[` is a pattern
(see `goldpan.adapters.rq_root.read`, which does the reading), except `P*`, which is expanded first into the phonon channels
(`P*max` is `PAS1max`, `PAS2max`, ...). The channels are those of the Z7 detector unless you pass `phonon_channels=`.

**Where the files are is not in this library.** Say it once, in the environment, and the call above needs nothing more:

* `GOLDPAN_RQ_FILES` (or `files=` in the call): a pattern with `{series}` in it, for example
  `"/data/R*/Processed/Prompt/*/Submerged/*_{series}.root"`; of the files that match, the last in name order is read (a series
  with one file per dump, like Run 76, is `files="/data/{series}_F*.root"` with `all_files=True`: every match is read, in name order);
* `GOLDPAN_RQ_DETECTOR` (or `detector=`): the number `N` of the `zip<N>` tree.

**The cache.** `load` saves what it read in `$GOLDPAN_CACHE/rqdata` (default `~/.cache/goldpan/rqdata`, a folder of your own, never
inside a repository). A later `load` of the same files reuses any cached read that contains all the branches asked for, so asking
for fewer RQs than before costs nothing; `refresh=True` reads again and `cache=False` neither reads nor writes the cache. Unlike a
cache keyed on file names, this one is keyed on the *state* of the files (size and modification time) and on the version of
goldpan: a file that was rewritten is read again, never served from an old entry. Entries are written to a temporary file and
renamed, so a reader never sees half of one. `cache_info()` lists them and `cache_clear()` removes them.
"""
import csv
import hashlib
import importlib.metadata
import json
import os
import re
import time
from glob import glob
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

import numpy as np

from .status import DONE, status

ENV_CACHE = "GOLDPAN_CACHE"
ENV_FILES = "GOLDPAN_RQ_FILES"
ENV_DETECTOR = "GOLDPAN_RQ_DETECTOR"

SERIES_NAME = re.compile(r"^\d{8}_\d{4,6}$")
PHONON_CHANNELS = ["PAS1", "PAS2", "PBS1", "PBS2", "PCS1", "PCS2", "PDS1", "PDS2", "PES1", "PES2", "PFS1", "PFS2"]
"""The twelve phonon channels of Z7, in RQ naming: what `P*` stands for unless `phonon_channels=` is given."""
META_COLUMNS = ("series", "dump", "event")


class RQData(dict):
    """`dict` of branch name -> numpy array (plus `series`, `dump` and `event` per row), with `.skipped` (series with no file),
    `.files` (series -> the file that was read) and `.dataset` (what was asked for)."""
    skipped: tuple = ()
    files: dict = {}
    dataset = None


def _goldpan_version() -> str:
    try:
        return importlib.metadata.version("goldpan")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


@status(DONE)
def cache_dir() -> str:
    """The folder of the RQ cache: `$GOLDPAN_CACHE/rqdata`, by default `~/.cache/goldpan/rqdata`."""
    root = os.environ.get(ENV_CACHE) or os.path.join("~", ".cache", "goldpan")
    return os.path.join(os.path.expanduser(root), "rqdata")


def _read_csv(path) -> list:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


@status(DONE)
def series_list(dataset) -> list:
    """The series names of `dataset`: a series name (`"24260424_145101"`), a list of them, or the path of a CSV with a `series`
    column (lines starting with `#` are skipped)."""
    if isinstance(dataset, str) and SERIES_NAME.match(dataset):
        return [dataset]
    if isinstance(dataset, (str, Path)):
        path = Path(dataset).expanduser()
        if not path.is_file():
            raise ValueError(f"{dataset!r} is neither a series name (like 24260424_145101) nor a CSV file with a `series` column")
        rows = _read_csv(path)
        if not rows or "series" not in rows[0]:
            raise ValueError(f"{path} has no `series` column")
        return [r["series"].strip() for r in rows if r.get("series", "").strip()]
    series = [str(s) for s in dataset]
    bad = [s for s in series if not SERIES_NAME.match(s)]
    if bad:
        raise ValueError(f"not series names (like 24260424_145101): {bad[:5]}")
    return series


@status(DONE)
def find_file(series: str, files: Union[str, Callable, None] = None) -> Optional[str]:
    """The file of `series`: `files` is a pattern with `{series}` in it (default: `$GOLDPAN_RQ_FILES`), or a function of the series
    name that returns a path or `None`. Of several matches the last in name order is taken. `None` if there is no file."""
    if callable(files):
        found = files(series)
        return None if found is None else str(found)
    pattern = files or os.environ.get(ENV_FILES)
    if not pattern:
        raise ValueError(f"say where the RQ files are: files=\"<pattern with {{series}}>\" or the environment variable {ENV_FILES}")
    if "{series}" not in pattern:
        raise ValueError(f"the pattern for the RQ files must contain {{series}}, got {pattern!r}")
    hits = sorted(glob(os.path.expanduser(pattern.replace("{series}", series))))
    return hits[-1] if hits else None


@status(DONE)
def find_files(series: str, files: Union[str, Callable, None] = None) -> list:
    """Every file of `series`, in name order: the matches of the pattern `files` (default: `$GOLDPAN_RQ_FILES`), or what the function
    `files(series)` returns (a path, a list of paths or `None`). The empty list if there is none. For a series that is stored as
    many files, such as the dumps of Run 76."""
    if callable(files):
        found = files(series)
        return [] if found is None else ([str(f) for f in found] if isinstance(found, (list, tuple)) else [str(found)])
    pattern = files or os.environ.get(ENV_FILES)
    if not pattern:
        raise ValueError(f"say where the RQ files are: files=\"<pattern with {{series}}>\" or the environment variable {ENV_FILES}")
    if "{series}" not in pattern:
        raise ValueError(f"the pattern for the RQ files must contain {{series}}, got {pattern!r}")
    return sorted(glob(os.path.expanduser(pattern.replace("{series}", series))))


@status(DONE)
def expand_branches(rqs: Sequence[str], phonon_channels: Optional[Sequence[str]] = None) -> list:
    """`rqs` with every `P*` replaced by the phonon channels (`P*max` -> `PAS1max`, ...), each name once, in order."""
    channels = list(phonon_channels) if phonon_channels is not None else PHONON_CHANNELS
    out = []
    for name in rqs:
        names = [name.replace("P*", ch, 1) for ch in channels] if "P*" in name else [name]
        out += [n for n in names if n not in out]
    return out


def _detector(detector) -> int:
    if detector is None:
        detector = os.environ.get(ENV_DETECTOR)
    if detector is None or str(detector).strip() == "":
        raise ValueError(f"say which zip<N> tree to read: detector=N or the environment variable {ENV_DETECTOR}")
    try:
        return int(detector)
    except ValueError:
        raise ValueError(f"the detector must be the whole number N of the zip<N> tree, got {detector!r}") from None


def _stamp(path: str) -> list:
    st = os.stat(path)
    return [os.path.abspath(path), st.st_size, st.st_mtime_ns]


def _fileset_key(dataset, files: dict, detector: int) -> str:                  # files: series -> the stamp(s) of its file(s)
    h = hashlib.sha1(json.dumps([detector, sorted(files.items()), _goldpan_version()]).encode()).hexdigest()[:10]
    named = isinstance(dataset, str) and SERIES_NAME.match(dataset)
    name = dataset if named else (Path(dataset).stem if isinstance(dataset, (str, Path)) else "custom")
    return f"{re.sub(r'[^A-Za-z0-9_.+-]', '_', name)}_zip{detector}_{h}"


def _cache_lookup(prefix: str, requested: list) -> Optional[str]:
    for p in sorted(glob(os.path.join(cache_dir(), prefix + "_*.npz"))):
        try:
            with np.load(p) as z:
                if set(requested) <= set(z["__requested__"].tolist()):
                    return p
        except (OSError, ValueError, KeyError):
            continue                                                  # a damaged entry is ignored (and replaced by the next write)
    return None


def _read_files(files: dict, requested: list, detector: int) -> dict:
    from .adapters import rq_root                                      # needs uproot
    import awkward as ak
    parts = {}
    names = None
    for series, path in files.items():
        table = rq_root.read(path, detector=detector, branches=requested, series=series)             # path: a file or a list of files
        fields = ak.fields(table)
        names = fields if names is None else names + [f for f in fields if f not in names]
        n = len(table)
        part = {}
        for f in fields:
            col = ak.to_numpy(table[f]) if f not in ("series", "dump") else np.array(table[f].to_list(), dtype=str)
            part[f] = col
        parts[series] = (part, n)
    out = {}
    for f in names or []:
        pieces = []
        for series, (part, n) in parts.items():
            if f in part:
                pieces.append(part[f])
            else:                                                      # a branch a later file has and an earlier one lacks
                pieces.append(np.full(n, np.nan))
        out[f] = np.concatenate(pieces)
    return out


@status(DONE)
def load(dataset, rqs: Sequence[str], detector: Union[int, str, None] = None, cache: bool = True, refresh: bool = False,
         verbose: bool = True, files: Union[str, Callable, None] = None, phonon_channels: Optional[Sequence[str]] = None,
         all_files: bool = False) -> RQData:
    """All the requested RQs of every series of `dataset`, concatenated (see the module documentation).

    `dataset`: a series name, a list of series names, or the path of a CSV with a `series` column. `rqs`: branch names, patterns
    and `P*` names. `detector`: the number `N` of the `zip<N>` tree (default `$GOLDPAN_RQ_DETECTOR`). `files`: where the files
    are (default `$GOLDPAN_RQ_FILES`), see `find_file`. `cache=False` bypasses the cache and `refresh=True` reads again and
    replaces the entry. `all_files=True` reads every file that matches a series (its dumps, in name order) instead of the last one;
    `data.files` then maps each series to a list of files. Series with no file are skipped and listed in `data.skipped`."""
    t0 = time.time()
    requested = expand_branches(rqs, phonon_channels)
    detector = _detector(detector)
    found, skipped = {}, []
    for series in series_list(dataset):
        if all_files:
            path = find_files(series, files) or None
        else:
            path = find_file(series, files)
        (skipped.append(series) if path is None else found.__setitem__(series, path))
    stamps = {s: ([_stamp(f) for f in p] if isinstance(p, list) else _stamp(p)) for s, p in found.items()}
    prefix = _fileset_key(dataset, stamps, detector)

    out = RQData()
    hit = None if (refresh or not cache) else _cache_lookup(prefix, requested)
    if hit:
        with np.load(hit) as z:
            for name in z["__fields__"].tolist():
                out[name] = z[name]
    else:
        data = _read_files(found, requested, detector) if found else {}
        out.update(data)
        for name in META_COLUMNS:
            out.setdefault(name, np.array([], dtype=str if name != "event" else np.int64))
        if cache and found:
            os.makedirs(cache_dir(), exist_ok=True)
            key = hashlib.sha1(",".join(sorted(requested)).encode()).hexdigest()[:10]
            path = os.path.join(cache_dir(), f"{prefix}_{key}.npz")
            tmp = f"{path}.{os.getpid()}.tmp"                          # write, then rename: a reader never sees a partial file
            with open(tmp, "wb") as fh:
                np.savez(fh, __requested__=np.array(requested), __fields__=np.array(list(out)), **out)
            os.replace(tmp, path)
    out.skipped, out.files, out.dataset = tuple(skipped), dict(found), dataset
    if verbose:
        if not found:
            print(f"{dataset}: no RQ files found -- is the pattern {files or os.environ.get(ENV_FILES)!r} right and the disk visible?")
        else:
            n_ev = len(out["series"])
            src = f"cache {os.path.basename(hit)}" if hit else "the RQ files"
            n_files = sum(len(p) if isinstance(p, list) else 1 for p in found.values())
            print(f"{dataset}: {len(found)} series ({n_files} files), {n_ev} events, {len(requested)} branches from {src} in {time.time() - t0:.1f} s"
                  + (f"; {len(skipped)} series with no file skipped" if skipped else ""))
    return out


@status(DONE)
def cache_info(verbose: bool = True) -> list:
    """The entries of the RQ cache as a list of `{"file", "bytes", "modified"}` (newest first); prints a summary unless
    `verbose=False`."""
    rows = []
    for p in glob(os.path.join(cache_dir(), "*.npz")):
        st = os.stat(p)
        rows.append({"file": os.path.basename(p), "bytes": st.st_size, "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))})
    rows.sort(key=lambda r: r["modified"], reverse=True)
    if verbose:
        print(f"{cache_dir()}: {len(rows)} entries, {sum(r['bytes'] for r in rows) / 1e6:.1f} MB")
    return rows


@status(DONE)
def cache_clear() -> int:
    """Delete every entry of the RQ cache; returns how many there were."""
    n = 0
    for p in glob(os.path.join(cache_dir(), "*.npz")) + glob(os.path.join(cache_dir(), "*.tmp")):
        os.remove(p)
        n += 1
    return n
