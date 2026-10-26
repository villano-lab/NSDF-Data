"""Quantity tables from any RQ source, and how they join an `Events`.

The RQ adapters (`goldpan.adapters.rq_root`, and any you add) return a *table of quantities*: an Awkward Array with one record per
event whose first fields are the event key (`series`, `dump`, `event`). `attach` adds such a table to an `Events` of the same
events, matching on the key, so the RQs of the reconstruction can be compared with, or cut on together with, what the library
computes from the traces::

    ev = rq.attach(ev, rq_root.read(path, detector=7, branches=["PTOFamps", "P*std"]))
    ev.quantities["PTOFamps"]
"""
from typing import Sequence

import awkward as ak
import numpy as np

from ..data import KEY_COLUMNS, Events
from ..status import DONE, status


def _keys(table, on) -> list:
    return list(zip(*[np.asarray(ak.to_list(table[k])).tolist() for k in on]))


@status(DONE)
def attach(events: Events, table, *, on: Sequence[str] = KEY_COLUMNS, prefix: str = "") -> Events:
    """`events` with the columns of `table` added, each event matched to the row of `table` with the same `on` fields.

    Every event must have exactly one row in `table` (extra rows are ignored); otherwise `ValueError` names the first events
    without. The fields of `table` that are in the key (`series`, `dump`, `event`) are not copied, and a field with the name of
    an existing quantity is refused unless `prefix` is given (it is put before the names of the new columns). `on` lets you
    match on fewer fields, for example `("dump", "event")` when the two sources name the series differently."""
    on = tuple(on)
    for k in on:
        if k not in ak.fields(table):
            raise ValueError(f"the table has no field {k!r} to match on; it has {ak.fields(table)[:6]}...")
    table_keys = _keys(table, on)
    index = {}
    for i, key in enumerate(table_keys):
        if key in index:
            raise ValueError(f"the table has two rows with {dict(zip(on, key))}: cannot match on {list(on)}")
        index[key] = i
    event_keys = _keys(events.quantities, on)
    rows = [index.get(key) for key in event_keys]
    absent = [event_keys[i] for i, r in enumerate(rows) if r is None]
    if absent:
        raise ValueError(f"{len(absent)} of {len(rows)} events have no row in the table on {list(on)}; "
                         f"first: {dict(zip(on, absent[0]))}")
    take = np.asarray(rows)
    new = [f for f in ak.fields(table) if f not in KEY_COLUMNS]
    clash = [prefix + f for f in new if prefix + f in ak.fields(events.quantities)]
    if clash:
        raise ValueError(f"the events already have {clash}; pass prefix= to keep both")
    return events.with_quantities(**{prefix + f: table[f][take] for f in new})
