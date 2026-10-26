"""The conformance test of an adapter, for the people who write one (see the guide "Writing an adapter" when it exists).

    from goldpan.testing import check_adapter
    passed = check_adapter(my_adapter_module, "sample/file", **read_kwargs)

It reads the sample with the adapter and checks the contract of `goldpan.data.Events`; that `iter_chunks` (if the adapter has
it) gives, joined, the same events as `read`; and, if the adapter can `write`, that a written and read-back copy loses nothing.
It raises `AssertionError` saying which check failed, and returns the list of the checks that passed.
"""
import tempfile
from pathlib import Path

import awkward as ak
import numpy as np

from .data import KEY_COLUMNS, Events
from .status import DONE, status


def _same(a: Events, b: Events, what: str) -> None:
    assert a.detector == b.detector, f"{what}: the detectors differ"
    assert sorted(a.traces) == sorted(b.traces), f"{what}: the traces differ: {sorted(a.traces)} against {sorted(b.traces)}"
    for key in a.traces:
        assert np.array_equal(a.traces[key], b.traces[key]), f"{what}: traces[{key}] differ"
    assert ak.fields(a.quantities) == ak.fields(b.quantities), f"{what}: the quantity fields differ"
    assert a.quantities.to_list() == b.quantities.to_list(), f"{what}: the quantities differ"


@status(DONE)
def check_adapter(module, sample_path, **read_kwargs) -> list:
    """Check `module` (an adapter) against the contract on `sample_path`; returns the checks passed, raises `AssertionError`."""
    passed = []
    ev = module.read(sample_path, **read_kwargs)
    assert isinstance(ev, Events), f"read() must return Events, got {type(ev).__name__}"
    assert ev.n_events > 0, "the sample has no events"
    passed.append("read() returns Events")

    assert all(k in ak.fields(ev.quantities) for k in KEY_COLUMNS), "the key fields are missing"
    assert ev.traces, "no traces were read"
    assert all(not a.flags.writeable for a in ev.traces.values()), "the traces must be read-only"
    for (channel, segment), a in ev.traces.items():
        assert a.shape == (ev.n_events, ev.detector.readout.segment(segment).n_samples), f"traces[{channel}, {segment}] has a wrong shape"
    passed.append("the invariants of Events hold")

    if hasattr(module, "iter_chunks"):
        chunks = list(module.iter_chunks(sample_path, chunk=max(1, ev.n_events // 3), **read_kwargs))
        assert len(chunks) >= 1 and all(isinstance(c, Events) for c in chunks), "iter_chunks must yield Events"
        assert all(len(c) <= max(1, ev.n_events // 3) for c in chunks), "a chunk is larger than asked"
        _same(ev, Events.concatenate(*chunks), "iter_chunks joined against read")
        passed.append("iter_chunks joined equals read")

    if hasattr(module, "write"):
        with tempfile.TemporaryDirectory() as tmp:
            module.write(ev, Path(tmp) / "roundtrip")
            back = module.read(Path(tmp) / "roundtrip")
        _same(ev, back, "write then read against the original")
        passed.append("a round trip loses nothing")
    return passed
