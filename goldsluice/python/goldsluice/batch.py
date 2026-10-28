"""Batch mode: run the processing of a dataset definition (`goldpan.dataset`) over all its raw files.

    python -m goldsluice run r76.dataset.toml            # process every raw file that is new or changed
    python -m goldsluice check r76.dataset.toml          # read the definition and list what would be done

or from Python, `goldsluice.batch.run("r76.dataset.toml")`. For every raw file the pulses are read in pieces by the source's
adapter (`goldpan.adapters`), every step is applied to the channels it names with the Rust kernels, and the quantities (one record
per channel, keyed by series, dump and event, **without** the pulses) are written into the output dataset of the definition, a
goldpan Parquet dataset that `goldpan.dataset.Dataset.processed()` reads (or, with `output_format = "root"`, RQ-style ROOT files
under our names, written by `goldpan.adapters.rq_root.write` and read with `rq_root.read`; needs `goldsluice[root]`). A ledger, `_goldsluice.json` in the output folder, records
for each raw file what was done, with what, and how long it took, so that a second run only does what changed: a file is skipped only
if its fingerprint (the definition), its stamp (the raw file) **and** the versions of `goldsluice` and `goldpan` that made the output are
unchanged (`force=True` redoes everything). Every output file also carries its provenance in its metadata (`goldsluice` key).

`goldpan` does the reading and the definition, so batch mode needs it (`pip install goldsluice[batch]`).

Processed data must not end up in a Git repository: `check` and `run` refuse an output folder that lies inside a Git working tree
and whose data files that tree does not ignore (`check_output_location`; `allow_output_in_repo=True`, or `--allow-output-in-repo`
on the command line, overrides it).
"""
import importlib.metadata
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import __version__
from .algorithms import ALGORITHMS, run as run_algorithm

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
    """The versions of the code that makes an output: the kernels (`goldsluice`) and the readers and definition (`goldpan`). Part of
    the test for skipping a file, so that a fixed kernel or reader is not hidden behind an output made by the old one. They change
    only at a release: between releases, `--force` redoes everything."""
    try:
        goldpan = importlib.metadata.version("goldpan")
    except importlib.metadata.PackageNotFoundError:
        goldpan = None
    return {"goldsluice": __version__, "goldpan": goldpan}


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

    @property
    def n_events(self) -> int:
        return sum(f.n_events for f in self.files if not f.skipped)

    def __str__(self) -> str:
        done = [f for f in self.files if not f.skipped]
        lines = [f"dataset {self.name}: {len(done)} file(s) processed, {len(self.files) - len(done)} unchanged, "
                 f"{self.n_events} events in {self.total_s:.2f} s"]
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
    if not allow_output_in_repo:
        check_output_location(spec.output, spec.output_format)
    return [(s.name, f) for s in spec.sources for f in s.files()]


def run(spec_path, *, chunk: int = 1000, force: bool = False, backend: str = "rust", allow_output_in_repo: bool = False,
        progress: Optional[Callable[[str], None]] = print) -> Report:
    """Process the dataset defined in `spec_path`; returns the `Report` (what was done and the timing). `chunk` is the number of
    events read at once (it bounds the memory used by the pulses); `backend="python"` runs the mirrors, for comparison."""
    ak, dataset, parquet, Events = _goldpan()
    todo = check(spec_path, allow_output_in_repo=allow_output_in_repo)
    spec = dataset.load(spec_path)
    out = spec.output
    out.mkdir(parents=True, exist_ok=True)
    ledger = _load_ledger(out)
    versions = _versions()
    report = Report(spec.name)
    say = progress or (lambda _msg: None)
    t_all = time.perf_counter()

    for source_name, path in todo:
        source = spec.source(source_name)
        fp = dataset.fingerprint(spec, source)
        key, stamp = f"{source.name}:{path}", _stamp(path)
        old = ledger["files"].get(key)
        if old and not force and old.get("fingerprint") == fp and old.get("stamp") == stamp:
            if old.get("versions") == versions:
                report.files.append(FileReport(str(path), skipped=True, n_events=old.get("n_events", 0)))
                say(f"unchanged  {path}")
                continue
            say(f"redoing    {path}: made with {old.get('versions') or 'versions not recorded'}, now {versions}")

        fr = FileReport(str(path))
        pieces = []
        t0 = time.perf_counter()
        for ev in dataset.read_raw(source, path, chunk=chunk):
            fr.read_s += time.perf_counter() - t0
            columns = {k: ev.quantities[k] for k in ("series", "dump", "event")}
            per_channel = {}
            for step in spec.steps:
                params = step.resolve(ev.detector.readout.segment("main").config)
                for ch in step.channel_names(ev.detector):
                    t1 = time.perf_counter()
                    result = run_algorithm(step.algorithm, ev.trace(ch), backend=backend, **params)
                    fr.compute_s[step.algorithm] = fr.compute_s.get(step.algorithm, 0.0) + time.perf_counter() - t1
                    record = per_channel.setdefault(ch, {})
                    for name, values in result.items():
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
        provenance = {"version": __version__, "versions": versions, "dataset": spec.name, "source": source.name, "raw": str(path),
                      "fingerprint": fp, "backend": backend,
                      "steps": [{"algorithm": s.algorithm, "channels": s.channels, "params": s.params} for s in spec.steps],
                      "timing_s": {"read": fr.read_s, **{f"compute.{k}": v for k, v in fr.compute_s.items()}}}
        events = Events(events.detector, {}, events.quantities, {"goldsluice": provenance})
        t2 = time.perf_counter()
        if spec.output_format == "root":
            from goldpan.adapters import rq_root          # needs uproot (goldpan[root])
            rq_root.write(events, out, detector=spec.root_detector)
        else:
            parquet.write(events, out)
        fr.write_s = time.perf_counter() - t2
        series_dumps = sorted({f"{s}_{d}" for s, d in zip(events.quantities["series"].to_list(),
                                                          events.quantities["dump"].to_list())})
        ledger["files"][key] = {"fingerprint": fp, "stamp": stamp, "n_events": fr.n_events, "version": __version__,
                                "versions": versions,
                                "series_dumps": series_dumps,
                                "seconds": {"read": fr.read_s, "write": fr.write_s, **fr.compute_s}}
        (out / LEDGER).write_text(json.dumps(ledger, indent=1, sort_keys=True), encoding="utf-8")
        report.files.append(fr)
        say(f"processed  {path}: {fr.n_events} events in {fr.read_s + sum(fr.compute_s.values()) + fr.write_s:.2f} s")

    report.total_s = time.perf_counter() - t_all
    return report
