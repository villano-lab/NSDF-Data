"""Tests of the adapter layer: the native Parquet format, the registry and the conformance test (design step 2)."""
import json
from pathlib import Path

import awkward as ak
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import goldpan.adapters as adapters
from goldpan.adapters import parquet
from goldpan.config import PulseConfig
from goldpan.data import ChannelInfo, Detector, Events, Readout
from goldpan.testing import check_adapter

SAMPLE = Path(__file__).resolve().parent / "data" / "sample_dataset"
N = 64


def detector(name="S1", n_samples=N):
    return Detector(name, (ChannelInfo("A", role="phonon", unit="b0", input="0"), ChannelInfo("B", role="phonon")),
                    Readout.single(n_samples, PulseConfig(16, 2, 1e-6)))


def events(n=6, series="SER", dump="F0001", first=0, **kw):
    rng = np.random.default_rng(first + n)
    traces = {c: rng.normal(0, 1, (n, N)).astype(np.float32) for c in ("A", "B")}
    return Events.from_arrays(detector(), traces, series=series, dump=dump, event=np.arange(n) + first, **kw)


# ---- the sample dataset and the conformance test ----------------------------------------------------------------------

def test_the_sample_dataset_passes_the_conformance_test():
    passed = check_adapter(parquet, SAMPLE)
    assert passed == ["read() returns Events", "the invariants of Events hold", "iter_chunks joined equals read",
                      "a round trip loses nothing"]


def test_the_sample_dataset_has_the_documented_content():
    ev = parquet.read(SAMPLE)
    assert len(ev) == 24 and ev.detector.name == "SAMPLE"
    assert ak.fields(ev.quantities)[:3] == ["series", "dump", "event"]
    assert set(ak.fields(ev.quantities)) >= {"t_trigger", "trigger_type", "A", "pulse_times"}
    assert sorted(ev.traces) == [("A", "main"), ("B", "main")]
    assert ev.trace("A").dtype == np.float32
    assert ak.num(ev.quantities["pulse_times"]).to_list()[:6] == [0, 1, 2, 0, 1, 2]       # variable length survives
    assert sorted(set(ev.quantities["dump"].to_list())) == ["F0001", "F0002"]
    assert ev.meta["clock"] == "sample-daq" and len(ev.meta["source_files"]) == 2


def test_the_manifest_lists_the_stream_and_its_files():
    m = json.loads((SAMPLE / "_goldpan.json").read_text(encoding="utf-8"))
    assert m["format"] == "goldpan-dataset" and m["format_version"] == parquet.FORMAT_VERSION
    stream = m["streams"]["SAMPLE"]
    assert stream["kind"] == "events" and stream["main_array"] is True
    assert stream["files"] == ["SAMPLE/SERIES1_F0001.parquet", "SAMPLE/SERIES1_F0002.parquet"]
    assert [c["name"] for c in stream["detector"]["channels"]] == ["A", "B"]


def test_the_files_use_plain_arrow_types_that_other_tools_read():
    schema = pq.read_schema(SAMPLE / "SAMPLE" / "SERIES1_F0001.parquet")
    assert not any(isinstance(f.type, pa.ExtensionType) for f in schema)
    assert pa.types.is_fixed_size_list(schema.field("traces.A.main").type)
    assert schema.metadata[b"goldpan.format_version"] == b"1"


# ---- round trips -------------------------------------------------------------------------------------------------

def test_round_trip_keeps_traces_dtypes_quantities_and_meta(tmp_path):
    ev = events(5, quantities={"amp": np.arange(5.0), "label": np.array(list("abcde")),
                               "lst": [[1.0], [], [2.0, 3.0], [4.0], []], "rec": {"std": np.arange(5.0), "max": np.arange(5) * 2.0}},
                meta={"clock": "daq", "units": {"amp": "counts"}})
    parquet.write(ev, tmp_path / "ds")
    back = parquet.read(tmp_path / "ds")
    assert back.detector == ev.detector
    for key in ev.traces:
        assert back.traces[key].dtype == np.float32 and np.array_equal(back.traces[key], ev.traces[key])
    assert back.quantities.to_list() == ev.quantities.to_list()
    assert back.meta["units"] == {"amp": "counts"} and back.meta["clock"] == "daq"
    assert not back.trace("A").flags.writeable


def test_two_series_dumps_make_two_files_and_read_back_in_order(tmp_path):
    ev = Events.concatenate(events(3, dump="F0002", first=100), events(4, dump="F0001", first=0))
    parquet.write(ev, tmp_path / "ds")
    manifest = json.loads((tmp_path / "ds" / "_goldpan.json").read_text(encoding="utf-8"))
    assert manifest["streams"]["S1"]["files"] == ["S1/SER_F0001.parquet", "S1/SER_F0002.parquet"]
    back = parquet.read(tmp_path / "ds")
    assert back.quantities["event"].to_list() == [0, 1, 2, 3, 100, 101, 102]
    assert back.quantities["dump"].to_list() == ["F0001"] * 4 + ["F0002"] * 3


def test_writing_again_replaces_the_file_and_extends_the_stream(tmp_path):
    parquet.write(events(3, dump="F0001"), tmp_path / "ds")
    parquet.write(events(5, dump="F0001"), tmp_path / "ds")                       # replaces F0001
    parquet.write(events(2, dump="F0002", first=50), tmp_path / "ds")             # adds F0002
    back = parquet.read(tmp_path / "ds")
    assert len(back) == 7
    assert len(json.loads((tmp_path / "ds" / "_goldpan.json").read_text(encoding="utf-8"))["streams"]["S1"]["files"]) == 2


def test_a_stream_cannot_be_extended_with_a_different_detector(tmp_path):
    parquet.write(events(3), tmp_path / "ds")
    other = Events.from_arrays(Detector("S1", (ChannelInfo("A"),), Readout.single(N, PulseConfig(16, 2, 2e-6))),
                               {"A": np.zeros((2, N))}, series="X", dump="F9")
    with pytest.raises(ValueError, match="different detector"):
        parquet.write(other, tmp_path / "ds")


def test_two_detectors_are_two_streams_and_need_a_name(tmp_path):
    a = events(3)
    b = Events.from_arrays(detector("S2"), {"A": np.ones((2, N)), "B": np.ones((2, N))}, series="SER", dump="F0001")
    parquet.write(a, tmp_path / "ds")
    parquet.write(b, tmp_path / "ds")
    with pytest.raises(ValueError, match="several streams"):
        parquet.read(tmp_path / "ds")
    assert len(parquet.read(tmp_path / "ds", detector="S2")) == 2
    assert len(parquet.read(tmp_path / "ds", detector="S1")) == 3
    with pytest.raises(KeyError, match="no stream"):
        parquet.read(tmp_path / "ds", detector="S3")


# ---- partial reads ----------------------------------------------------------------------------------------------

def test_channels_limits_the_trace_columns_read(tmp_path):
    parquet.write(events(4), tmp_path / "ds")
    ev = parquet.read(tmp_path / "ds", channels=["B"])
    assert sorted(ev.traces) == [("B", "main")]
    assert ev.detector.channel_names() == ["A", "B"]
    with pytest.raises(KeyError, match="no channel"):
        parquet.read(tmp_path / "ds", channels=["Z"])


def test_events_slice_or_positions(tmp_path):
    parquet.write(events(8), tmp_path / "ds")
    assert parquet.read(tmp_path / "ds", events=slice(2, 5)).quantities["event"].to_list() == [2, 3, 4]
    assert parquet.read(tmp_path / "ds", events=[7, 0]).quantities["event"].to_list() == [7, 0]


def test_a_single_file_is_a_dataset_too():
    ev = parquet.read(SAMPLE / "SAMPLE" / "SERIES1_F0002.parquet")
    assert len(ev) == 10 and set(ev.quantities["dump"].to_list()) == {"F0002"}


def test_iter_chunks_yields_bounded_chunks_that_join_to_the_whole(tmp_path):
    parquet.write(events(10), tmp_path / "ds", row_group_size=4)
    chunks = list(parquet.iter_chunks(tmp_path / "ds", chunk=3))
    assert all(len(c) <= 3 for c in chunks) and sum(len(c) for c in chunks) == 10
    joined = Events.concatenate(*chunks)
    assert joined.quantities["event"].to_list() == list(range(10))
    assert chunks[0].meta["source_file"].endswith("SER_F0001.parquet")
    assert [len(c) for c in parquet.iter_chunks(tmp_path / "ds", chunk=100)] == [10]       # one file, one chunk


# ---- refusals ---------------------------------------------------------------------------------------------------

def test_a_directory_without_a_manifest_is_not_a_dataset(tmp_path):
    with pytest.raises(FileNotFoundError, match="not a goldpan dataset"):
        parquet.read(tmp_path)


def test_a_newer_format_version_is_refused(tmp_path):
    parquet.write(events(3), tmp_path / "ds")
    manifest = tmp_path / "ds" / "_goldpan.json"
    m = json.loads(manifest.read_text(encoding="utf-8"))
    m["format_version"] = 99
    manifest.write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ValueError, match="newer"):
        parquet.read(tmp_path / "ds")
    with pytest.raises(ValueError, match="newer"):
        parquet.write(events(3), tmp_path / "ds")


def test_a_file_of_a_newer_version_or_not_ours_is_refused(tmp_path):
    table = pa.table({"x": [1, 2]})
    pq.write_table(table, tmp_path / "plain.parquet")
    with pytest.raises(ValueError, match="not a goldpan file"):
        parquet.read(tmp_path / "plain.parquet")
    pq.write_table(table.replace_schema_metadata({"goldpan.format_version": "99"}), tmp_path / "new.parquet")
    with pytest.raises(ValueError, match="newer"):
        parquet.read(tmp_path / "new.parquet")


def test_names_that_the_format_cannot_carry_are_refused(tmp_path):
    bad_channel = Events.from_arrays(Detector("S1", (ChannelInfo("A.1"),), Readout.single(N, PulseConfig(16, 2, 1e-6))),
                                     {"A.1": np.zeros((2, N))})
    with pytest.raises(ValueError, match="dot"):
        parquet.write(bad_channel, tmp_path / "a")
    with pytest.raises(ValueError, match="file name"):
        parquet.write(events(2, series="a/b"), tmp_path / "b")
    with pytest.raises(ValueError, match="reserved"):
        parquet.write(events(2).with_quantities(**{"traces.X.main": np.zeros(2)}), tmp_path / "c")


def test_meta_that_is_not_json_is_refused_with_a_clear_message(tmp_path):
    with pytest.raises(TypeError, match="JSON"):
        parquet.write(events(2, meta={"bad": object()}), tmp_path / "ds")


# ---- the registry and the conformance test itself ---------------------------------------------------------------------

def test_registry_reads_a_dataset_by_guessing_and_by_name():
    assert len(adapters.read(SAMPLE)) == 24
    assert len(adapters.read(SAMPLE, format="parquet", channels=["A"])) == 24
    assert {"parquet", "idx"} <= set(adapters.available())
    with pytest.raises(ValueError, match="cannot tell"):
        adapters.read(SAMPLE.parent)
    with pytest.raises(KeyError, match="no adapter"):
        adapters.read(SAMPLE, format="nosuchformat")


def test_a_third_party_adapter_can_register_and_is_checked_by_the_same_test():
    class Mine:
        @staticmethod
        def read(path, **kw):
            return parquet.read(path, **kw)

    adapters.register("mine", Mine)
    assert len(adapters.read(SAMPLE, format="mine")) == 24
    assert check_adapter(Mine, SAMPLE) == ["read() returns Events", "the invariants of Events hold"]
    with pytest.raises(TypeError, match="not an adapter"):
        adapters.register("broken", object())


def test_check_adapter_catches_an_adapter_that_returns_writable_traces():
    class Bad:
        @staticmethod
        def read(path, **kw):
            ev = parquet.read(path)
            object.__setattr__(ev, "traces", {k: np.array(v) for k, v in ev.traces.items()})   # writable copies
            return ev

    with pytest.raises(AssertionError, match="read-only"):
        check_adapter(Bad, SAMPLE)


def test_check_adapter_catches_chunks_that_do_not_add_up():
    class Lossy:
        @staticmethod
        def read(path, **kw):
            return parquet.read(path, **kw)

        @staticmethod
        def iter_chunks(path, *, chunk, **kw):
            yield from list(parquet.iter_chunks(path, chunk=chunk, **kw))[:-1]

    with pytest.raises(AssertionError, match="iter_chunks"):
        check_adapter(Lossy, SAMPLE)


def test_every_built_in_adapter_has_a_revision_and_an_adapter_without_one_has_revision_1():
    """`REVISION` is what `goldsluice run` compares to decide whether an output was made by the reader as it is now."""
    from types import SimpleNamespace
    for name in ("idx", "parquet", "rq_root", "midas"):
        module = adapters._adapter(name)
        assert isinstance(module.REVISION, int) and module.REVISION >= 1
        assert adapters.revision(name) == module.REVISION
    adapters.register("revision-test", SimpleNamespace(read=lambda path: None))
    try:
        assert adapters.revision("revision-test") == 1
    finally:
        adapters._registered.pop("revision-test")
    with pytest.raises(KeyError, match="no adapter"):
        adapters.revision("nope")


def test_threads_writing_different_dumps_into_one_dataset_all_reach_the_manifest(tmp_path):
    """`goldsluice run --workers N`: the data files are written outside the lock, the manifest under it, so no dump is lost."""
    from concurrent.futures import ThreadPoolExecutor
    dumps = [f"F{k:04d}" for k in range(1, 25)]

    def write_dump(dump):
        ev = Events.from_arrays(detector(), {"A": np.full((3, N), 1.0), "B": np.full((3, N), 2.0)}, series="S1", dump=dump)
        parquet.write(ev, tmp_path / "ds")
        return dump

    for _ in range(3):                                         # a race is a matter of luck: try several times, with fresh datasets
        target = tmp_path / "ds"
        if target.exists():
            import shutil
            shutil.rmtree(target)
        with ThreadPoolExecutor(8) as pool:
            assert sorted(pool.map(write_dump, dumps)) == dumps
        manifest = json.loads((target / "_goldpan.json").read_text(encoding="utf-8"))
        assert manifest["streams"]["S1"]["files"] == sorted(f"S1/S1_{d}.parquet" for d in dumps)
        assert parquet.read(target).n_events == 3 * len(dumps)
