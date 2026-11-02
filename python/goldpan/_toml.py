"""Writing TOML values, for the files goldpan writes (`goldpan.dataset.dump`, `goldpan.registry.add_record`). `tomllib` only reads. Private: the
functions are for the modules of the package; nothing here is part of the library's interface."""
import json
import re
from typing import Mapping

_BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def _key(key) -> str:
    """A TOML key: bare when it can be, a quoted string otherwise. `ValueError` for anything that is not a non-empty string."""
    if not isinstance(key, str) or not key:
        raise ValueError(f"a key must be a non-empty string, not {key!r}")
    return key if _BARE_KEY.match(key) else _value(key)


def _value(value) -> str:
    """One TOML value; tables inside a value are written inline. `ValueError` for anything TOML has no value for (`None`, a `Path`, ...)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:
            return "nan"
        return ("inf" if value > 0 else "-inf") if value in (float("inf"), float("-inf")) else repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_value(v) for v in value) + "]"
    if isinstance(value, Mapping):
        return "{ " + ", ".join(f"{_key(k)} = {_value(v)}" for k, v in value.items()) + " }" if value else "{}"
    raise ValueError(f"cannot write {value!r} ({type(value).__name__}) in a TOML file: use text, numbers, true/false, lists and tables")
