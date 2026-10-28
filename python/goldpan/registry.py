"""A registry of the facts about an experiment that analysis needs and the library must not contain: the readouts (how a
pretrigger window, a glitch and a sample period are set), and the detectors (their number, type, readout and where each
named channel is wired in a given file format).

**This module is the mechanism only.** No detector of any experiment is written in `goldpan`; the records are data and live
outside the package, in folders of TOML files (for the Run 76 detector of this project, the `registry/` folder of the
repository, which is laid out so it can become a repository of its own). The readout presets `DCRC_RUN76` and `Z7` of
`goldpan.config` are older and stay where they are; a registry may define readouts too, and a name is looked up in the registry
first and then among those presets. A registry is built from *sources*; a folder
of TOML files is the first kind, and anything with a `load()` method that yields `(origin, tables)` pairs can take its place
later (a Git repository, a database) without a change anywhere else::

    from goldpan import registry

    reg = registry.load("~/NSDF-Data/registry")        # one or more folders; the environment variable GOLDPAN_REGISTRY is added
    reg.readout_config("DCRC_RUN76")                   # a goldpan.config.PulseConfig (a preset, or the registry's own readout)
    reg.detector("NAI-S2").number                      # 1
    reg.detector("NAI-S2").read_defaults("idx")        # {'channels': {...}, 'roles': {...}}: the defaults of [sources.read]

A dataset definition file names the folders in `[dataset] registry = [...]` (see `goldpan.dataset`), and a source whose
`detector` is a name in the registry takes its readout, its channels and its roles from there. Anything written in the
definition file itself wins over the registry, key by key.

**The files.** Any file `*.toml` of a folder (sorted by name); every file holds the tables `readouts` and `detectors`, and the
integer `format_version` (1)::

    format_version = 1

    [readouts.DCRC_RUN76]
    pretrigger_samples = 1000
    glitch_samples = 10
    sample_period_s = 0.8e-6
    status = "inferred"                                # "confirmed" or "inferred": required
    evidence = "where the numbers come from"           # required: what a reader needs to judge the entry

    [detectors."NAI-S2"]
    number = 1                                         # the N of zip<N> in RQ files, the detector number of the MIDAS ODB
    readout = "DCRC_RUN76"
    status = "inferred"
    evidence = "..."
    [detectors."NAI-S2".idx]                           # defaults for [sources.read] of a source of this format
    channels = { Side2pC = [0, 0] }

Readouts take `pretrigger_samples`, `glitch_samples`, `sample_period_s` (all three: nothing is assumed), `status`, `evidence`,
`description` and `series`; detectors take `number`, `type_code`, `tower`, `plane`, `odb_name`, `readout`, `status`,
`evidence`, `description` and `series`, plus one table per file format. Unknown keys are errors, as in the dataset definition
file, and a name defined twice (in two files or two sources) is an error, so two folders can never disagree silently.
"""
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Tuple

from .status import DONE, status

FORMAT_VERSION = 1
"""The version of the registry files; a reader refuses a newer one."""

ENV_VAR = "GOLDPAN_REGISTRY"
"""Folders to add to every registry opened with `load`, separated like `PATH` (`os.pathsep`)."""

STATUSES = ("confirmed", "inferred")

_TOP = {"format_version", "readouts", "detectors"}
_READOUT_NUMBERS = ("pretrigger_samples", "glitch_samples", "sample_period_s")
_COMMON = {"status", "evidence", "description", "series"}
_READOUT = set(_READOUT_NUMBERS) | _COMMON
_DETECTOR = {"number", "type_code", "tower", "plane", "odb_name", "readout"} | _COMMON


@dataclass(frozen=True)
class ReadoutRecord:
    """A readout: the three numbers of a `goldpan.config.PulseConfig`, and where they come from."""
    name: str
    config: Any
    """The `PulseConfig`."""
    status: str
    """`"confirmed"` or `"inferred"`."""
    evidence: str
    description: str = ""
    series: Tuple[str, ...] = ()
    """The series (or patterns) the readout applies to, as written."""
    origin: str = ""
    """The file the record was read from."""


@dataclass(frozen=True)
class DetectorRecord:
    """A detector: its identity, its readout, and per file format the defaults of `[sources.read]`."""
    name: str
    number: Optional[int]
    """The N of `zip<N>` in RQ files and the detector number of the MIDAS ODB (`Det07` is 7)."""
    type_code: Optional[int]
    """The ODB `DetectorType` (710 and 711 are Ge and Si HV, 700 and 701 iZIP)."""
    tower: Optional[int]
    plane: Optional[int]
    odb_name: Optional[str]
    """The `DetectorName` of the ODB (for example `G149`), when the name here is a different one."""
    readout: Optional[str]
    """The name of the readout, to be found in the same registry."""
    status: str
    evidence: str
    description: str = ""
    series: Tuple[str, ...] = ()
    read: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    """Per file format, the keyword arguments of that adapter's `read` that this detector sets."""
    origin: str = ""

    def read_defaults(self, format: str) -> dict:
        """The defaults for `[sources.read]` of a source of file format `format` (empty if the record has none)."""
        return {k: v for k, v in self.read.get(format, {}).items()}


class FolderSource:
    """The registry files of one folder (`*.toml`, in name order). Anything with this `load` method is a source."""

    def __init__(self, folder):
        self.folder = Path(folder).expanduser()

    def __repr__(self) -> str:
        return f"FolderSource({str(self.folder)!r})"

    def load(self) -> Iterable[Tuple[str, Mapping]]:
        """`(origin, tables)` for each file: the parsed TOML. `ValueError` if the folder is missing or a file is not TOML."""
        if not self.folder.is_dir():
            raise ValueError(f"registry folder {str(self.folder)!r} does not exist")
        for path in sorted(self.folder.glob("*.toml")):
            try:
                yield str(path), tomllib.loads(path.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as e:
                raise ValueError(f"{path}: not valid TOML: {e}") from None


def _unknown(where: str, table: Mapping, allowed: set) -> None:
    extra = sorted(set(table) - allowed)
    if extra:
        raise ValueError(f"{where}: unknown key(s) {extra}; allowed: {sorted(allowed)}")


def _common(where: str, t: Mapping) -> Tuple[str, str, str, Tuple[str, ...]]:
    for key in ("status", "evidence"):
        if key not in t:
            raise ValueError(f"{where}: needs {key!r} (status is one of {list(STATUSES)}; evidence says where the entry comes from)")
    if t["status"] not in STATUSES:
        raise ValueError(f"{where}: status must be one of {list(STATUSES)}, not {t['status']!r}")
    if not isinstance(t["evidence"], str) or not t["evidence"].strip():
        raise ValueError(f"{where}: evidence must say where the entry comes from")
    series = t.get("series", [])
    if not (isinstance(series, list) and all(isinstance(s, str) for s in series)):
        raise ValueError(f"{where}: series must be a list of strings")
    return t["status"], t["evidence"], str(t.get("description", "")), tuple(series)


def _int(where: str, t: Mapping, key: str) -> Optional[int]:
    if key not in t:
        return None
    v = t[key]
    if not isinstance(v, int) or isinstance(v, bool) or v < 0:
        raise ValueError(f"{where}: {key} must be a whole number of at least 0, not {v!r}")
    return v


def _readout(name: str, t: Mapping, origin: str) -> ReadoutRecord:
    from .config import PulseConfig
    where = f"{origin}: readouts.{name}"
    _unknown(where, t, _READOUT)
    missing = [k for k in _READOUT_NUMBERS if k not in t]
    if missing:
        raise ValueError(f"{where}: needs {missing} (there are no defaults)")
    st, ev, desc, series = _common(where, t)
    return ReadoutRecord(name, PulseConfig(**{k: t[k] for k in _READOUT_NUMBERS}), st, ev, desc, series, origin)


def _detector(name: str, t: Mapping, origin: str) -> DetectorRecord:
    where = f"{origin}: detectors.{name}"
    scalar = {k: v for k, v in t.items() if not isinstance(v, Mapping)}
    formats = {k: v for k, v in t.items() if isinstance(v, Mapping)}
    _unknown(where, scalar, _DETECTOR)
    st, ev, desc, series = _common(where, scalar)
    odb_name, readout = scalar.get("odb_name"), scalar.get("readout")
    for key, v in (("odb_name", odb_name), ("readout", readout)):
        if v is not None and not isinstance(v, str):
            raise ValueError(f"{where}: {key} must be a string")
    return DetectorRecord(name, _int(where, scalar, "number"), _int(where, scalar, "type_code"), _int(where, scalar, "tower"),
                          _int(where, scalar, "plane"), odb_name, readout, st, ev, desc, series,
                          {fmt: dict(v) for fmt, v in formats.items()}, origin)


class Registry:
    """The records of one or more sources, read and checked when it is made."""

    def __init__(self, sources: Iterable = ()):
        self.sources = tuple(sources)
        self._readouts: dict = {}
        self._detectors: dict = {}
        for source in self.sources:
            for origin, tables in source.load():
                self._add(origin, tables)

    def _add(self, origin: str, tables: Mapping) -> None:
        _unknown(origin, tables, _TOP)
        if tables.get("format_version", FORMAT_VERSION) > FORMAT_VERSION:
            raise ValueError(f"{origin} has format_version {tables['format_version']}, newer than this goldpan ({FORMAT_VERSION})")
        for kind, make, into in (("readouts", _readout, self._readouts), ("detectors", _detector, self._detectors)):
            for name, t in tables.get(kind, {}).items():
                if not isinstance(t, Mapping):
                    raise ValueError(f"{origin}: {kind}.{name} must be a table")
                if name in into:
                    raise ValueError(f"{origin}: {kind}.{name} is already defined in {into[name].origin}; "
                                     "a name may be defined once")
                into[name] = make(name, t, origin)

    def __repr__(self) -> str:
        return f"Registry({len(self._readouts)} readouts, {len(self._detectors)} detectors, sources={list(self.sources)})"

    def readouts(self) -> dict:
        """All the readout records by name."""
        return dict(self._readouts)

    def detectors(self) -> dict:
        """All the detector records by name."""
        return dict(self._detectors)

    def has_readout(self, name: str) -> bool:
        return name in self._readouts

    def has_detector(self, name: str) -> bool:
        return name in self._detectors

    def readout(self, name: str) -> ReadoutRecord:
        """The readout record `name`; `KeyError` that lists the names there are."""
        try:
            return self._readouts[name]
        except KeyError:
            raise KeyError(f"no readout {name!r} in the registry (readouts: {sorted(self._readouts)}; sources: {list(self.sources)})") from None

    def readout_config(self, name: str):
        """The `PulseConfig` of the readout `name`: the registry's own record if it has one, otherwise the preset of that name in
        `goldpan.config` (`DCRC_RUN76`, `Z7`). `KeyError` that lists both."""
        if name in self._readouts:
            return self._readouts[name].config
        from . import config
        preset = getattr(config, name, None)
        if isinstance(preset, config.PulseConfig):
            return preset
        presets = sorted(n for n, v in vars(config).items() if isinstance(v, config.PulseConfig))
        raise KeyError(f"no readout {name!r}: not in the registry (readouts: {sorted(self._readouts)}) and not a preset of "
                       f"goldpan.config (presets: {presets})")

    def detector(self, name: str) -> DetectorRecord:
        """The detector record `name`; `KeyError` that lists the names there are."""
        try:
            return self._detectors[name]
        except KeyError:
            raise KeyError(f"no detector {name!r} in the registry (detectors: {sorted(self._detectors)}; sources: {list(self.sources)})") from None


@status(DONE)
def load(*folders, use_environment: bool = True) -> Registry:
    """A `Registry` of the TOML files in `folders` (and of the folders of the environment variable `GOLDPAN_REGISTRY`, unless
    `use_environment` is false). An empty registry if there are none. `ValueError` for a folder that does not exist, a file that
    is not valid, or a name that two files define."""
    sources = [FolderSource(f) for f in folders]
    env = os.environ.get(ENV_VAR, "") if use_environment else ""
    sources += [FolderSource(p) for p in env.split(os.pathsep) if p.strip()]
    return Registry(sources)


@status(DONE)
def compare(record: DetectorRecord, found: Any) -> list:
    """What a detector record and another description of the same detector disagree on, as messages (empty if they agree). `found`
    is anything with the attributes `number`, `type_code`, `tower`, `plane` and `name`, such as the `OdbDetector` of
    `goldpan.adapters.midas.detectors`; only what the record states is compared (`name` against `odb_name`, else the record's name)."""
    out = []
    for attr in ("number", "type_code", "tower", "plane"):
        want, got = getattr(record, attr), getattr(found, attr, None)
        if want is not None and got is not None and want != got:
            out.append(f"detector {record.name!r}: the registry has {attr} {want}, the file has {got}")
    want_name = record.odb_name if record.odb_name is not None else record.name
    got_name = getattr(found, "name", None)
    if record.odb_name is not None and got_name is not None and want_name != got_name:
        out.append(f"detector {record.name!r}: the registry has odb_name {want_name!r}, the file has {got_name!r}")
    return out
