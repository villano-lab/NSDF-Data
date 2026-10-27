"""A dataset definition: which raw files, how to read them, and which processing to run on them. One TOML file, read by both
packages: `goldsluice` runs the processing in batch, `goldpan` reads the pulses and the processed quantities back.

The file (`r76.dataset.toml`)::

    [dataset]
    name = "r76-nai"
    output = "processed/r76-nai"            # the processed quantities: a goldpan Parquet dataset (directory), relative to this file

    [[sources]]                             # where the pulses come from; as many as you like
    name = "side2"
    format = "idx"                          # any adapter: idx, midas, parquet, or one you registered
    paths = ["~/idx/07221203_2025_F0001"]   # raw files or dump folders ...
    glob = "~/idx/07221203_2025_F*"         # ... and/or a pattern (sorted)
    detector = "NAI-S2"                     # the detector name (the adapter's detector_name)
    readout = "DCRC_RUN76"                  # a preset of goldpan.config, or { pretrigger_samples = 1000, glitch_samples = 10, sample_period_s = 0.8e-6 }
    [sources.read]                          # the other keyword arguments of the adapter's read(), verbatim
    channels = { Side2pA = [0, 0], Side2pB = [0, 1] }
    roles = { Side2pA = "phonon", Side2pB = "phonon" }

    [[processing]]                          # the steps, in order; each adds quantities to the channels it names
    algorithm = "peak"                      # a goldsluice algorithm
    channels = "role:phonon"                # "all", "role:<role>", or a list of channel names
    [processing.params]
    glitch_samples = "@readout.glitch_samples"        # "@readout.<field>": taken from the readout of the data
    pretrigger_samples = "@readout.pretrigger_samples"
    amps_per_adc = 1.5e-9

Nothing is assumed: the readout, the channels and every algorithm parameter are written down. `Dataset.open(path)` gives the same
file to both packages::

    ds = Dataset.open("r76.dataset.toml")
    ev = ds.read()                          # the pulses, with the processed quantities attached (one Events)
    q = ds.processed()                      # only the processed quantities, no pulses: small and fast
    ev.quantities["Side2pA"]["current_max"]

The processed quantities are stored one record per channel (`quantities["Side2pA"]["adc_max"]`), keyed by `series`, `dump`,
`event`. `python -m goldsluice run <file>` produces them; reading them before that raises an error that says so.
"""
import glob as _glob
import hashlib
import inspect
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Tuple

from . import config as _config
from .adapters import _adapter
from .adapters import parquet as _parquet
from .adapters import rq as _rq
from .config import PulseConfig
from .data import Events
from .status import DONE, status

FORMAT_VERSION = 1
"""The version of the dataset definition file; a reader refuses a newer one."""

_TOP = {"dataset", "sources", "processing"}
_DATASET = {"name", "output", "description", "format_version"}
_SOURCE = {"name", "format", "paths", "glob", "detector", "readout", "read"}
_STEP = {"algorithm", "channels", "params"}
_READOUT = {"pretrigger_samples", "glitch_samples", "sample_period_s"}


@dataclass(frozen=True)
class Source:
    name: str
    format: str
    patterns: Tuple[str, ...]
    """The `paths` and `glob` entries as written (with `~` and relative to the folder of the definition file when used)."""
    detector: str
    readout: Optional[PulseConfig]
    read: Mapping[str, Any]
    """Keyword arguments of the adapter's `read`, as written in the file."""
    base: Path
    """The folder of the definition file, for relative paths."""

    def files(self) -> list:
        """The raw files or dump folders of the source, in order. `ValueError` if a pattern or path matches nothing."""
        out = []
        for pattern in self.patterns:
            expanded = Path(pattern).expanduser()
            expanded = expanded if expanded.is_absolute() else self.base / expanded
            if any(ch in pattern for ch in "*?["):
                found = sorted(_glob.glob(str(expanded)))
            else:
                found = [str(expanded)] if expanded.exists() else []
            if not found:
                raise ValueError(f"source {self.name!r}: {pattern!r} matches nothing (looked in {self.base})")
            out.extend(Path(f) for f in found)
        return out


@dataclass(frozen=True)
class Step:
    algorithm: str
    channels: Any
    """``"all"``, ``"role:<role>"`` or a tuple of channel names."""
    params: Mapping[str, Any]

    def channel_names(self, detector) -> list:
        """The channels of `detector` this step applies to."""
        if self.channels == "all":
            return detector.channel_names()
        if isinstance(self.channels, str):
            names = detector.channels_with_role(self.channels[len("role:"):])
            if not names:
                raise ValueError(f"step {self.algorithm!r}: the detector {detector.name!r} has no channel with role "
                                 f"{self.channels[len('role:'):]!r} (roles: {sorted({c.role for c in detector.channels})})")
            return names
        for name in self.channels:
            detector.channel(name)                                     # KeyError for an unknown channel
        return list(self.channels)

    def resolve(self, config: PulseConfig) -> dict:
        """The parameters with every `"@readout.<field>"` replaced by that field of `config`."""
        out = {}
        for key, value in self.params.items():
            if isinstance(value, str) and value.startswith("@readout."):
                field = value[len("@readout."):]
                if field not in _READOUT:
                    raise ValueError(f"step {self.algorithm!r}, parameter {key!r}: {value!r}: the readout has {sorted(_READOUT)}")
                value = getattr(config, field)
                if value is None:
                    raise ValueError(f"step {self.algorithm!r}, parameter {key!r}: the readout does not give {field}")
            out[key] = value
        return out


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    output: Path
    sources: Tuple[Source, ...]
    steps: Tuple[Step, ...]
    path: Path
    """The definition file."""
    raw: Mapping[str, Any]
    """The parsed TOML, kept for provenance."""

    def source(self, name: Optional[str] = None) -> Source:
        if name is None:
            if len(self.sources) != 1:
                raise ValueError(f"the dataset has several sources {[s.name for s in self.sources]}: name one")
            return self.sources[0]
        for s in self.sources:
            if s.name == name:
                return s
        raise KeyError(f"no source {name!r}; the dataset has {[s.name for s in self.sources]}")


def _unknown(where: str, table: Mapping, allowed: set) -> None:
    extra = sorted(set(table) - allowed)
    if extra:
        raise ValueError(f"{where}: unknown key(s) {extra}; allowed: {sorted(allowed)}")


def _readout(value, where: str) -> Optional[PulseConfig]:
    if value is None:
        return None
    if isinstance(value, str):
        preset = getattr(_config, value, None)
        if not isinstance(preset, PulseConfig):
            presets = sorted(n for n, v in vars(_config).items() if isinstance(v, PulseConfig))
            raise ValueError(f"{where}: readout {value!r} is not a preset of goldpan.config (presets: {presets})")
        return preset
    if isinstance(value, Mapping):
        _unknown(f"{where}: readout", value, _READOUT)
        missing = sorted(_READOUT - set(value))
        if missing:
            raise ValueError(f"{where}: readout needs {missing} (there are no defaults); write the three numbers or name a preset")
        return PulseConfig(**value)
    raise ValueError(f"{where}: readout must be a preset name or a table, not {type(value).__name__}")


@status(DONE)
def load(path) -> DatasetSpec:
    """Read and check a dataset definition file. Nothing is opened: the raw files need not exist yet."""
    path = Path(path).expanduser().resolve()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{path}: not valid TOML: {e}") from None
    _unknown(str(path), raw, _TOP)
    d = raw.get("dataset")
    if d is None:
        raise ValueError(f"{path}: needs a [dataset] table with name and output")
    _unknown(f"{path}: [dataset]", d, _DATASET)
    if d.get("format_version", FORMAT_VERSION) > FORMAT_VERSION:
        raise ValueError(f"{path} has format_version {d['format_version']}, newer than this goldpan ({FORMAT_VERSION})")
    for key in ("name", "output"):
        if key not in d:
            raise ValueError(f"{path}: [dataset] needs {key!r}")
    base = path.parent
    output = Path(d["output"]).expanduser()
    output = output if output.is_absolute() else base / output

    sources = []
    for i, s in enumerate(raw.get("sources", [])):
        where = f"{path}: sources[{i}]"
        _unknown(where, s, _SOURCE)
        for key in ("format", "detector"):
            if key not in s:
                raise ValueError(f"{where} needs {key!r}")
        patterns = tuple(list(s.get("paths", [])) + ([s["glob"]] if "glob" in s else []))
        if not patterns:
            raise ValueError(f"{where} needs paths and/or glob")
        sources.append(Source(s.get("name", f"source{i}"), s["format"], patterns, s["detector"],
                              _readout(s.get("readout"), where), dict(s.get("read", {})), base))
    if not sources:
        raise ValueError(f"{path}: needs at least one [[sources]]")
    if len({s.name for s in sources}) != len(sources):
        raise ValueError(f"{path}: source names must be unique, got {[s.name for s in sources]}")

    steps = []
    for i, st in enumerate(raw.get("processing", [])):
        where = f"{path}: processing[{i}]"
        _unknown(where, st, _STEP)
        for key in ("algorithm", "channels"):
            if key not in st:
                raise ValueError(f"{where} needs {key!r}")
        channels = st["channels"]
        if isinstance(channels, list):
            channels = tuple(channels)
        elif not (channels == "all" or (isinstance(channels, str) and channels.startswith("role:") and len(channels) > 5)):
            raise ValueError(f"{where}: channels must be \"all\", \"role:<role>\" or a list of names, not {channels!r}")
        steps.append(Step(st["algorithm"], channels, dict(st.get("params", {}))))
    return DatasetSpec(d["name"], output, tuple(sources), tuple(steps), path, raw)


@status(DONE)
def fingerprint(spec: DatasetSpec, source: Source) -> str:
    """A short hash of what determines the processed quantities of `source`: how it is read and the processing steps. The
    batch run stores it in every output file and skips a file whose fingerprint has not changed."""
    payload = {"source": {"format": source.format, "detector": source.detector,
                          "readout": None if source.readout is None else asdict(source.readout),
                          "read": source.read},
               "steps": [{"algorithm": s.algorithm, "channels": s.channels, "params": s.params} for s in spec.steps]}
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _read_kwargs(module, source: Source) -> dict:
    accepted = set(inspect.signature(module.read).parameters)
    kwargs = dict(source.read)
    if "detector_name" in accepted:
        kwargs["detector_name"] = source.detector
    elif "detector" in accepted:
        kwargs["detector"] = source.detector
    if "config" in accepted:
        if source.readout is None:
            raise ValueError(f"source {source.name!r}: the {source.format!r} adapter needs a readout (a preset name or three numbers)")
        kwargs["config"] = source.readout
    unknown = sorted(set(kwargs) - accepted)
    if unknown:
        raise ValueError(f"source {source.name!r}: the {source.format!r} adapter's read() has no argument {unknown}; it has {sorted(accepted)}")
    return kwargs


@status(DONE)
def read_raw(source: Source, path, *, chunk: Optional[int] = None) -> Iterator[Events]:
    """The pulses of one raw file of `source` as `Events` read by its adapter: one `Events`, or with `chunk` pieces of at most
    that many events when the adapter can (`iter_chunks`; otherwise the whole file is one piece)."""
    module = _adapter(source.format)
    kwargs = _read_kwargs(module, source)
    if chunk and hasattr(module, "iter_chunks"):
        yield from module.iter_chunks(path, chunk=chunk, **kwargs)
    else:
        yield module.read(path, **kwargs)


class Dataset:
    """A dataset definition opened for reading: the pulses from its sources and the quantities processed from them."""

    def __init__(self, spec: DatasetSpec):
        self.spec = spec

    @classmethod
    def open(cls, path) -> "Dataset":
        return cls(load(path))

    def __repr__(self) -> str:
        return f"Dataset({self.spec.name!r}, sources={[s.name for s in self.spec.sources]}, output={str(self.spec.output)!r})"

    def processed(self, *, detector: Optional[str] = None) -> Events:
        """The processed quantities of a detector, without pulses (an `Events` with no traces): one record per event."""
        out = self.spec.output
        if not (out / _parquet.MANIFEST).exists():
            raise FileNotFoundError(f"nothing processed yet in {out}: run `python -m goldsluice run {self.spec.path}`")
        return _parquet.read(out, detector=detector if detector is not None else self._detector())

    def _detector(self) -> Optional[str]:
        names = {s.detector for s in self.spec.sources}
        return next(iter(names)) if len(names) == 1 else None

    def iter_events(self, source: Optional[str] = None, *, processed: bool = True) -> Iterator[Events]:
        """One `Events` per raw file of `source`: its pulses, with the processed quantities attached unless `processed=False`."""
        src = self.spec.source(source)
        table = self.processed(detector=src.detector) if processed else None
        for path in src.files():
            for ev in read_raw(src, path):
                if table is not None:
                    try:
                        ev = _rq.attach(ev, table.quantities)
                    except ValueError as e:
                        raise ValueError(f"{path}: {e}; has the batch run covered this file? "
                                         f"`python -m goldsluice run {self.spec.path}`") from None
                yield ev

    @status(DONE)
    def read(self, source: Optional[str] = None, *, processed: bool = True) -> Events:
        """All the events of `source` as one `Events` (pulses, and the processed quantities unless `processed=False`)."""
        return Events.concatenate(*self.iter_events(source, processed=processed))
