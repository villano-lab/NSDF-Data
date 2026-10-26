"""Adapters: the only code that knows a file format. Each turns one storage into an `Events` (and back, where we can write).

* `goldpan.adapters.parquet`: the native format (reads and writes); its docstring is the specification.
* `goldpan.adapters.idx`: a dump of the NSDF archive (reads).
* `goldpan.adapters.rq_root`: the RQs of the collaboration's reconstruction, ROOT files read with uproot (reads a *table of quantities*, not
  traces; `goldpan.adapters.rq.attach` adds it to an `Events`).

Anyone can add one: a module with `read(path, **kw) -> Events`, optionally `iter_chunks(path, *, chunk, **kw)` and `write(events, path)`;
`goldpan.testing.check_adapter` checks it against the contract. `register` makes it available to `read(path, format=...)`.
"""
import importlib

_BUILTIN = {"parquet": "goldpan.adapters.parquet", "idx": "goldpan.adapters.idx",
            "rq_root": "goldpan.adapters.rq_root"}
_registered = {}


def register(name: str, module) -> None:
    """Make `module` (an adapter) available as `read(path, format=name)`."""
    if not hasattr(module, "read"):
        raise TypeError(f"{module!r} has no read(): it is not an adapter")
    _registered[name] = module


def available() -> list:
    """The names of the adapters that `read` knows."""
    return sorted(set(_BUILTIN) | set(_registered))


def _adapter(name: str):
    if name in _registered:
        return _registered[name]
    if name in _BUILTIN:
        return importlib.import_module(_BUILTIN[name])
    raise KeyError(f"no adapter {name!r}; available: {available()}")


def read(path, format=None, **kwargs):
    """Read `path` with the adapter `format`; `None` guesses: a directory with `_goldpan.json` or a `.parquet` file is `parquet`; a `.root` file or a folder of them is `rq_root`."""
    if format is None:
        from pathlib import Path
        p = Path(path)
        if (p / "_goldpan.json").exists() or p.suffix == ".parquet":
            format = "parquet"
        elif p.suffix == ".root" or (p.is_dir() and any(p.glob("*.root"))):
            format = "rq_root"
        else:
            raise ValueError(f"cannot tell the format of {path}; pass format= one of {available()}")
    return _adapter(format).read(path, **kwargs)
