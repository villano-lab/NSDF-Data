"""Batch mode: run the processing of a dataset definition (`goldpan.dataset`) over all its raw files.

    python -m goldsluice run r76.dataset.toml            # process every raw file that is new or changed
    python -m goldsluice check r76.dataset.toml          # read the definition and list what would be done

or from Python, `goldsluice.batch.run("r76.dataset.toml")`. For every raw file the pulses are read in pieces by the source's
adapter (`goldpan.adapters`), every step is applied to the channels it names with the Rust kernels, and the quantities (one record
per channel, keyed by series, dump and event, plus what the adapter knows about each event such as `trigger_type`, **without** the pulses) are written into the output dataset of the definition, a
goldpan Parquet dataset that `goldpan.dataset.Dataset.processed()` reads (or, with `output_format = "root"`, RQ-style ROOT files
under our names, written by `goldpan.adapters.rq_root.write` and read with `rq_root.read`; needs `goldsluice[root]`). A ledger, `_goldsluice.json` in the output folder, records
for each raw file what was done, with what, and how long it took, so that a second run only does what changed: a file is skipped only
if its fingerprint (the definition), its stamp (the raw file) **and** the revisions of the algorithms and of the reader that made the output are
unchanged (`force=True` redoes everything). Every output file also carries its provenance in its metadata (`goldsluice` key).

Reading a dump dominates the time, and it is the same work for every dump, so `run(..., workers=N)` (`--workers N`) processes N raw files at
once, each in its own thread (the readers, the kernels and the writers let go of the interpreter lock while they work): each file is
read, reduced and written by one thread; only the small shared files (the manifest of a Parquet dataset, the ledger) are updated one at a time. Every file needs its dump in memory, about
a gigabyte for a dump of 3000 events, so choose N by the memory of the machine as well as by its cores.

On a hard disk the readers fight for the head and the decoding waits for the disk, so a thread of its own reads the next raw files
from the disk, one after the other, into the cache of the operating system a few files ahead of the workers (`readahead`, by default
two more files than there are workers; `readahead=0` turns it off). It reads only; the workers still decode and reduce.

`goldpan` does the reading and the definition, so batch mode needs it (`pip install goldsluice[batch]`).

A step may build on an earlier one (`name`, `input`, `suffix` in `goldpan.dataset`): a step whose algorithm gives a trace (`KIND = "trace"`, a
filter or a baseline subtraction) keeps its result for the channels it names, in memory for the chunk being processed, and a step with `input = "<name>"` reads that
trace instead of the raw one. The ledger fingerprint and the provenance include `name`, `input` and `suffix` only where they are written.

Processed data must not end up in a Git repository: `check` and `run` refuse an output folder that lies inside a Git working tree
and whose data files that tree does not ignore (`check_output_location`; `allow_output_in_repo=True`, or `--allow-output-in-repo`
on the command line, overrides it).
"""
import importlib.metadata
import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import __version__
from .algorithms import ALGORITHMS, TRACE, kind, run as run_algorithm

LEDGER = "_goldsluice.json"


def _goldpan():
    try:
        import awkward as ak
        from goldpan import dataset
        from goldpan.adapters import parquet
        from goldpan.data import Events
    except ImportError as e:
        raise ImportError(f"batch mode needs goldpan (and awkward, pyarrow): {e}. Install it with `pip install goldsluice[batch]` "
                          f"or, in the repository, `pip install -e ./python[parquet]`") from None
    return ak, dataset, parquet, Events


def _versions() -> dict:
    """The versions of the packages that make an output, recorded for the reader of the ledger. They do **not** decide whether a file is
    redone: that is `_revisions`, which looks only at what the definition uses."""
    try:
        goldpan = importlib.metadata.version("goldpan")
    except importlib.metadata.PackageNotFoundError:
        goldpan = None
    return {"goldsluice": __version__, "goldpan": goldpan}


def _revisions(spec, source, adapters) -> dict:
    """The revision of every algorithm that the steps of the definition use and of the reader of `source`: what must be unchanged for an
    output to be still current. A new algorithm, or the fix of one the definition does not use, changes nothing here."""
    algorithms = {name: ALGORITHMS[name].REVISION for name in sorted({s.algorithm for s in spec.steps})}
    return {"algorithms": algorithms, "reader": {source.format: adapters.revision(source.format)}}


def _what_changed(old: dict, new: dict) -> list:
    """The differences between the revisions an output was made with and the current ones, in words (empty if there are none)."""
    out = []
    for kind, label in (("algorithms", "algorithm"), ("reader", "reader")):
        for name, rev in new[kind].items():
            was = old.get(kind, {}).get(name)
            if was != rev:
                out.append(f"{label} {name} revision {was} -> {rev}")
    return out


def _recorded_revisions(entry: dict, formats):
    """The revisions a ledger entry was made with. An entry written by the version-based ledger (it has `versions` and no `revisions`) was
    made by code whose revisions were all 1, so it counts as that; one with neither is unknown (`None`) and is redone."""
    if "revisions" in entry:
        return entry["revisions"]
    if "versions" in entry:
        return {"algorithms": {name: 1 for name in ALGORITHMS}, "reader": {name: 1 for name in formats}}
    return None


def _prefetch(paths, ahead: int, stop: threading.Event, slots: threading.Semaphore, ready=None) -> None:
    """Read every file under each of `paths`, in order, into the cache of the operating system, never more than `ahead` raw files before the
    ones the workers have finished (`slots` has `ahead` places, and a worker gives one back when it finishes a file), and set `ready[i]` when
    the files of `paths[i]` have been read (a worker waits for it, so that the disk is read in order, by one reader, and not by every worker
    at once). Runs in a thread of its own; it reads and forgets, so the memory it holds is one block. A file that cannot be read is left to
    the worker, which will say why; whatever happens, every `ready` is set at the end, so that no worker waits for ever."""
    try:
        for i, path in enumerate(paths):
            while not slots.acquire(timeout=0.2):
                if stop.is_set():
                    return
            if stop.is_set():
                return
            try:
                files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
                for f in files:
                    with open(f, "rb", buffering=0) as fh:
                        while fh.read(8 << 20) and not stop.is_set():
                            pass
            except OSError:
                pass
            if ready is not None:
                ready[i].set()
    finally:
        for event in ready or ():
            event.set()


def _stamp(path: Path) -> dict:
    """What identifies the state of a raw file or folder: the sizes and the latest modification time of its files."""
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    return {"n_files": len(files), "bytes": sum(f.stat().st_size for f in files),
            "mtime_ns": max((f.stat().st_mtime_ns for f in files), default=0)}


@dataclass
class FileReport:
    path: str
    skipped: bool = False
    n_events: int = 0
    read_s: float = 0.0
    compute_s: dict = field(default_factory=dict)       # {algorithm: seconds}: the call, with the conversion of the traces
    write_s: float = 0.0


@dataclass
class Report:
    name: str
    files: list = field(default_factory=list)
    total_s: float = 0.0
    workers: int = 1

    @property
    def n_events(self) -> int:
        return sum(f.n_events for f in self.files if not f.skipped)

    def __str__(self) -> str:
        done = [f for f in self.files if not f.skipped]
        lines = [f"dataset {self.name}: {len(done)} file(s) processed, {len(self.files) - len(done)} unchanged, "
                 f"{self.n_events} events in {self.total_s:.2f} s" + (f" ({self.workers} workers: the times below are summed over files)" if self.workers > 1 else "")]
        if done:
            lines.append(f"  read    {sum(f.read_s for f in done):9.3f} s   (the adapters)")
            compute = {}
            for f in done:
                for k, v in f.compute_s.items():
                    compute[k] = compute.get(k, 0.0) + v
            for k, v in compute.items():
                lines.append(f"  compute {v:9.3f} s   ({k})")
            lines.append(f"  write   {sum(f.write_s for f in done):9.3f} s")
            if self.total_s > 0:
                lines.append(f"  {self.n_events / self.total_s:9.0f} events/s overall")
        return "\n".join(lines)


def _load_ledger(out: Path) -> dict:
    p = out / LEDGER
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"format_version": 1, "files": {}}


def _git_root(path: Path) -> Optional[Path]:
    """The top of the Git working tree that contains `path` (which need not exist yet), or None."""
    here = path.resolve()
    for folder in (here, *here.parents):
        if (folder / ".git").exists():
            return folder
    return None


def check_output_location(out: Path, output_format: str = "parquet") -> None:
    """Raise `ValueError` if the output folder `out` is inside a Git working tree that does not ignore the data files written there
    (`_probe.parquet`, or `_probe.root` for ROOT output): results must not be committed by accident. An output outside any
    repository, or inside one that ignores it (the `processed/` rule of this repository's `.gitignore`), passes. When Git cannot
    answer (it is not installed, or it fails on that folder) nothing is refused."""
    root = _git_root(out)
    if root is None:
        return
    probe = out.resolve() / ("_probe.root" if output_format == "root" else "_probe.parquet")
    try:
        answer = subprocess.run(["git", "check-ignore", "-q", "--", str(probe)], cwd=root, capture_output=True)
    except OSError:
        return
    if answer.returncode == 1:                                  # 0 = ignored, 1 = not ignored, anything else = Git cannot tell
        raise ValueError(f"the output folder {out} is inside the Git working tree {root} and is not ignored by it: processed data "
                         f"must not be committed. Write it elsewhere (output = \"~/goldsluice-output/<name>\" in the definition), "
                         f"or add the folder to .gitignore, or, if you really mean it, pass allow_output_in_repo=True "
                         f"(--allow-output-in-repo)")


def check(spec_path, *, allow_output_in_repo: bool = False) -> list:
    """Read the definition and return what `run` would look at, as `[(source name, path), ...]`; raises on any problem (an unknown
    algorithm, a pattern that matches nothing, a bad readout, an output folder inside a Git working tree that does not ignore it)."""
    _, dataset, _, _ = _goldpan()
    spec = dataset.load(spec_path)
    if not spec.steps:
        raise ValueError(f"{spec.path}: no [[processing]] steps: nothing to run")
    for step in spec.steps:
        if step.algorithm not in ALGORITHMS:
            raise ValueError(f"unknown algorithm {step.algorithm!r}; goldsluice has {sorted(ALGORITHMS)}")
        if kind(step.algorithm) == TRACE and step.name is None:
            raise ValueError(f"{spec.path}: the step with algorithm {step.algorithm!r} gives a trace, not quantities: give it a name "
                             f"(name = \"...\") so that later steps can read it with input = \"...\"")
        if step.input is not None:
            producer = next(x for x in spec.steps if x.name == step.input)            # load() guarantees an earlier step of that name
            if kind(producer.algorithm) != TRACE:
                raise ValueError(f"{spec.path}: the step with algorithm {step.algorithm!r} reads input {step.input!r}, but that step "
                                 f"({producer.algorithm!r}) gives quantities, not a trace; an input must be a filter or a baseline subtraction")
    if not allow_output_in_repo:
        check_output_location(spec.output, spec.output_format)
    return [(s.name, f) for s in spec.sources for f in s.files()]


def run(spec_path, *, chunk: int = 1000, force: bool = False, backend: str = "rust", allow_output_in_repo: bool = False,
        workers: int = 1, readahead: Optional[int] = None, progress: Optional[Callable[[str], None]] = print) -> Report:
    """Process the dataset defined in `spec_path`; returns the `Report` (what was done and the timing). `chunk` is the number of
    events read at once (it bounds the memory used by the pulses); `backend="python"` runs the mirrors, for comparison. `workers` is the
    number of raw files processed at the same time (default 1, one after the other): the results are the same, only faster, and every
    file in flight holds its dump in memory (see the module documentation). `readahead` is how many raw files ahead of the workers a thread
    reads from the disk into the cache of the operating system (default `workers + 2`; 0 turns it off): it matters on a hard disk."""
    if not isinstance(workers, int) or isinstance(workers, bool) or workers < 1:
        raise ValueError("workers must be a whole number of at least 1")
    if readahead is not None and (not isinstance(readahead, int) or isinstance(readahead, bool) or readahead < 0):
        raise ValueError("readahead must be a whole number of at least 0")
    ak, dataset, parquet, Events = _goldpan()
    todo = check(spec_path, allow_output_in_repo=allow_output_in_repo)
    spec = dataset.load(spec_path)
    out = spec.output
    out.mkdir(parents=True, exist_ok=True)
    ledger = _load_ledger(out)
    versions = _versions()
    adapters = importlib.import_module("goldpan.adapters")
    report = Report(spec.name, workers=workers)
    say = progress or (lambda _msg: None)
    t_all = time.perf_counter()

    slots = [None] * len(todo)                                   # the FileReport of each file, in the order of `todo`
    jobs = []
    for index, (source_name, path) in enumerate(todo):
        source = spec.source(source_name)
        fp = dataset.fingerprint(spec, source)
        revisions = _revisions(spec, source, adapters)
        key, stamp = f"{source.name}:{path}", _stamp(path)
        old = ledger["files"].get(key)
        if old and not force and old.get("fingerprint") == fp and old.get("stamp") == stamp:
            recorded = _recorded_revisions(old, adapters.available())
            changed = ["revisions not recorded"] if recorded is None else _what_changed(recorded, revisions)
            if not changed:
                slots[index] = FileReport(str(path), skipped=True, n_events=old.get("n_events", 0))
                say(f"unchanged  {path}")
                continue
            say(f"redoing    {path}: {'; '.join(changed)}")
        jobs.append((index, source, path, fp, revisions, key, stamp))

    ahead = workers + 2 if readahead is None else readahead
    stop, places = threading.Event(), threading.Semaphore(max(ahead, 1))
    ready = {job[0]: threading.Event() for job in jobs}          # set when the read-ahead has read the raw file of that job
    prefetcher = threading.Thread(target=_prefetch, args=([job[2] for job in jobs], ahead, stop, places, [ready[job[0]] for job in jobs]),
                                  daemon=True) if ahead and jobs else None

    def process(job):
        """Read, reduce and write one raw file: runs in a worker thread. Returns what the main thread records."""
        try:
            if prefetcher:
                ready[job[0]].wait()                             # the disk is read in order by the read-ahead; the worker decodes from the cache
            return process_file(job)
        finally:
            places.release()                                     # the prefetcher may read one more file

    def process_file(job):
        index, source, path, fp, revisions, key, stamp = job
        fr = FileReport(str(path))
        pieces = []
        t0 = time.perf_counter()
        for ev in dataset.read_raw(source, path, chunk=chunk):
            fr.read_s += time.perf_counter() - t0
            keys = ("series", "dump", "event")                   # the key first, then what the adapter knows about each event (trigger_type, ...)
            columns = {k: ev.quantities[k] for k in keys + tuple(f for f in ak.fields(ev.quantities) if f not in keys)}
            per_channel = {}
            traces = {}                                          # (step name, channel) -> the trace a transform gave, for this chunk
            for step in spec.steps:
                params = step.resolve(ev.detector.readout.segment("main").config)
                for ch in step.channel_names(ev.detector):
                    if step.input is None:
                        data = ev.trace(ch)
                    elif (step.input, ch) in traces:
                        data = traces[(step.input, ch)]
                    else:
                        raise ValueError(f"{path}: the step with algorithm {step.algorithm!r} reads {step.input!r} for channel {ch!r}, "
                                         f"but that step does not give a trace for it (check the channels of both steps)")
                    t1 = time.perf_counter()
                    result = run_algorithm(step.algorithm, data, backend=backend, **params)
                    fr.compute_s[step.algorithm] = fr.compute_s.get(step.algorithm, 0.0) + time.perf_counter() - t1
                    if kind(step.algorithm) == TRACE:
                        traces[(step.name, ch)] = result["trace"]
                        continue
                    record = per_channel.setdefault(ch, {})
                    for name, values in result.items():
                        name = name + step.suffix
                        if name in record:
                            raise ValueError(f"{path}: channel {ch!r} gets {name!r} from two steps; "
                                             f"each quantity must come from one step")
                        record[name] = values
            for ch, record in per_channel.items():
                columns[ch] = ak.zip({k: ak.Array(v) for k, v in record.items()}, depth_limit=1)
            pieces.append(Events(ev.detector, {}, ak.Array(columns), {}))
            t0 = time.perf_counter()
        if not pieces:
            raise ValueError(f"{path}: the adapter returned no events")

        events = Events.concatenate(*pieces)
        fr.n_events = events.n_events
        provenance = {"version": __version__, "versions": versions, "revisions": revisions, "dataset": spec.name, "source": source.name, "raw": str(path),
                      "fingerprint": fp, "backend": backend,
                      "steps": [dataset.step_record(s) for s in spec.steps],
                      "timing_s": {"read": fr.read_s, **{f"compute.{k}": v for k, v in fr.compute_s.items()}}}
        events = Events(events.detector, {}, events.quantities, {"goldsluice": provenance})
        t2 = time.perf_counter()
        if spec.output_format == "root":
            from goldpan.adapters import rq_root              # needs uproot (goldpan[root])
            rq_root.write(events, out, detector=spec.root_detector)      # one file per dump: nothing shared
        else:
            parquet.write(events, out)                        # updates the manifest under its own lock
        fr.write_s = time.perf_counter() - t2
        series_dumps = sorted({f"{s}_{d}" for s, d in zip(events.quantities["series"].to_list(),
                                                          events.quantities["dump"].to_list())})
        entry = {"fingerprint": fp, "stamp": stamp, "n_events": fr.n_events, "version": __version__,
                 "versions": versions, "revisions": revisions, "series_dumps": series_dumps,
                 "seconds": {"read": fr.read_s, "write": fr.write_s, **fr.compute_s}}
        return job, fr, entry

    def record(job, fr, entry):
        """Note a finished file in the ledger and the report: only the main thread calls this."""
        ledger["files"][job[5]] = entry
        (out / LEDGER).write_text(json.dumps(ledger, indent=1, sort_keys=True), encoding="utf-8")
        slots[job[0]] = fr
        say(f"processed  {job[2]}: {fr.n_events} events in {fr.read_s + sum(fr.compute_s.values()) + fr.write_s:.2f} s")

    if prefetcher:
        prefetcher.start()
    try:
        if workers == 1 or len(jobs) <= 1:
            for job in jobs:
                record(*process(job))
        else:
            with ThreadPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
                futures = [pool.submit(process, job) for job in jobs]
                try:
                    for future in as_completed(futures):
                        record(*future.result())
                except BaseException:
                    for future in futures:
                        future.cancel()                          # the files not started are not started; the running ones finish
                    raise
    finally:
        stop.set()
        if prefetcher:
            prefetcher.join(timeout=5)

    report.files = [slot for slot in slots if slot is not None]
    report.total_s = time.perf_counter() - t_all
    return report
