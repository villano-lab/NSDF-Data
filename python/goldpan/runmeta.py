"""Run metadata (high voltage, trigger setting, ...) per event, from a table keyed by series.

Metadata applies to whole series, but an analysis needs it per event: a cut, a histogram, a colour. This joins the two in
one pass over the events. `numpy.unique(series, return_inverse=True)` finds the few distinct series and the inverse index
picks the table row of each event, so there is no string comparison per event and no pandas merge::

    from goldpan import runmeta

    meta = runmeta.read_table("series.csv")                    # a CSV with a `series` column and any others
    cols = runmeta.per_event(q["series"], meta)                # {"hv_v": array, "trigger_value": array, ...}, one value per event
    sel = (cols["hv_v"] == -34.0) & (cols["trigger_value"] == 2)

    for key, idx in runmeta.groups(q["series"], meta, by=("hv_v", "trigger_value")):
        print(key, len(idx))                                   # idx: the indices of the events of that chunk

**The table is data and is not in this library.** Where it lives (a file next to the outputs, or the detector registry) is
not decided here: every function takes the table as an argument. Numeric columns come back as float arrays (an empty cell
is NaN), the others as text. The `series` column is always text.
"""
import csv
import hashlib
import json

import numpy as np

from .status import DONE, status


@status(DONE)
def read_table(path):
    """Read a CSV with a `series` column into ``{column: numpy array}``.

    A column whose every cell is a number becomes a float array (an empty cell is NaN), any other column stays text.
    `series` always stays text: names such as ``07221121_2214`` are numbers to ``float`` (it accepts underscores).
    A series listed twice is an error.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "series" not in rows[0]:
        raise ValueError(f"{path}: needs a 'series' column")
    table = {}
    for name in rows[0]:
        values = [r[name] for r in rows]
        if name != "series":
            try:
                table[name] = np.array([float(v) if v != "" else np.nan for v in values])
                continue
            except ValueError:
                pass
        table[name] = np.array(values)
    if len(set(table["series"])) != len(rows):
        raise ValueError(f"{path}: a series is listed twice")
    return table


@status(DONE)
def per_event(series, table, columns=None):
    """One value per event for each metadata column, as ``{column: array}`` in the order of `series`.

    `series` is the ``series`` column of the events. A series that is not in `table` is an error that names it.
    `columns` picks which table columns to return (default: all but ``series``).
    """
    names, inverse = np.unique(np.asarray(series), return_inverse=True)
    lookup = {str(s): i for i, s in enumerate(table["series"])}
    missing = [str(s) for s in names if str(s) not in lookup]
    if missing:
        raise KeyError(f"series not in the metadata table: {', '.join(missing)}")
    rows = np.array([lookup[str(s)] for s in names], dtype=int)
    if columns is None:
        columns = [c for c in table if c != "series"]
    return {c: table[c][rows][inverse] for c in columns}


@status(DONE)
def groups(series, table, by=("hv_v", "trigger_value")):
    """Yield ``(key, event_indices)`` for each distinct combination of the `by` columns, sorted by key.

    The combinations are found on the small table first, so the cost is one pass over the events.
    """
    names, inverse = np.unique(np.asarray(series), return_inverse=True)
    meta = per_event(names, table, columns=by)
    keys = list(zip(*(meta[c] for c in by)))
    for key in sorted(set(keys)):
        in_group = np.array([k == key for k in keys])
        yield key, np.flatnonzero(in_group[inverse])


@status(DONE)
def rows(table, series):
    """The metadata of the given series as plain Python values, ``{series: {column: value}}``, for provenance (a number is a float,
    NaN is ``None``, so that it is valid JSON). A series that is not in `table` is an error that names it."""
    lookup = {str(s): i for i, s in enumerate(table["series"])}
    names = sorted({str(s) for s in series})
    missing = [s for s in names if s not in lookup]
    if missing:
        raise KeyError(f"series not in the metadata table: {', '.join(missing)}")
    out = {}
    for name in names:
        record = {}
        for column, values in table.items():
            if column == "series":
                continue
            value = values[lookup[name]]
            if isinstance(value, np.floating):
                value = None if np.isnan(value) else float(value)
            record[column] = value if value is None or isinstance(value, float) else str(value)
        out[name] = record
    return out


@status(DONE)
def digest(table, series):
    """A short hash of the metadata of the given series (the rows of `rows`, the order of the series does not matter): it changes when
    a value of one of those series changes and does not when another series is added or changed. A batch run stores it for each raw
    file, to redo only the files whose metadata changed."""
    blob = json.dumps(rows(table, series), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
