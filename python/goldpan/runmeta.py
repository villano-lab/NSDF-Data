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
is NaN), the others as text. The `series` column is always text. `write_table` writes such a table (a program that makes the
file, such as a form in a browser, builds the columns and calls it); `read_table` of the file gives the same table back.
"""
import csv
import math
from numbers import Real
from pathlib import Path

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


def _cells(name, values):
    """The cells of one column as text, such that `read_table` gives the column back as it is (numbers or text). `None` is an empty cell."""
    values = [v.item() if isinstance(v, np.generic) else v for v in values]
    present = [v for v in values if v is not None]
    if any(isinstance(v, bool) for v in present):
        raise ValueError(f"column {name!r}: true/false are not run metadata; write numbers or text")
    numbers = [isinstance(v, Real) for v in present]
    if present and all(numbers):
        return [("" if v is None or (isinstance(v, float) and math.isnan(v)) else repr(v)) for v in values]
    if any(numbers) or not all(isinstance(v, str) for v in present):
        raise ValueError(f"column {name!r} mixes numbers and text (or has values that are neither): a column is all numbers or all text")
    cells = ["" if v is None else v for v in values]
    for c in cells:
        try:
            float(c) if c != "" else None
        except ValueError:
            return cells                                                    # one cell that is not a number: read_table keeps the column as text
    raise ValueError(f"column {name!r} is text, but every cell is a number or empty, so a reader would take it for numbers: write numbers, "
                     "or make at least one cell text")


@status(DONE)
def write_table(path, table):
    """Write a table (``{column: sequence}``, as `read_table` gives it) to the CSV file `path` and return what `read_table` gives for that file.

    `table` needs a ``series`` column (text, every series once), written first; the other columns follow in the order of the mapping and have
    as many values as `series`. A column is all numbers (`None` or NaN is an empty cell) or all text (`None` is an empty cell), so the
    file reads back the same: a text column whose every cell looks like a number, or that mixes the two, is an error that names the column,
    and so are true/false values and a table without rows. Nothing is written when the table is refused."""
    if "series" not in table:
        raise ValueError("the table needs a 'series' column")
    columns = {name: list(values) for name, values in table.items()}
    n = len(columns["series"])
    if n == 0:
        raise ValueError("the table has no rows")
    for name, values in columns.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"a column name must be non-empty text, not {name!r}")
        if len(values) != n:
            raise ValueError(f"column {name!r} has {len(values)} values, 'series' has {n}")
    series = [v.item() if isinstance(v, np.generic) else v for v in columns["series"]]
    if not all(isinstance(v, str) and v for v in series):
        raise ValueError("every series must be non-empty text, such as '07221121_2214'")
    if len(set(series)) != n:
        raise ValueError("a series is listed twice")
    cells = {"series": series}
    for name, values in columns.items():
        if name != "series":
            cells[name] = _cells(name, values)
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cells)
        w.writerows(zip(*cells.values()))
    return read_table(path)


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
