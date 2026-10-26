"""The synthetic series (python/tests/synthetic_series.py): every format holds the same events, and the readers agree."""
import gzip
import re
import warnings

import numpy as np
import pyarrow.parquet as pq
import pytest

import synthetic_series as ss
from goldpan.adapters import idx, parquet
from goldpan.quantities import pretrigger_std
from goldpan.rq_cuts import loose_randoms, phonon_log_ratios, pileup_randoms

NAMES = [n for n, _, _ in ss.sensors()]


@pytest.fixture(scope="module")
def dumps():
    return ss.all_dumps()


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    folder = tmp_path_factory.mktemp("synthetic")
    formats = ["midas", "rq_parquet", "goldpan"]
    for mod, fmt in (("OpenVisus", "idx"), ("uproot", "rq_root")):
        try:
            __import__(mod)
            formats.append(fmt)
        except ImportError:
            pass
    return ss.write_all(folder, formats=formats)


def test_the_truth_is_deterministic_and_shaped_like_the_series(dumps):
    again = ss.all_dumps()
    for a, b in zip(dumps, again):
        np.testing.assert_array_equal(a.traces, b.traces)
    d = dumps[0]
    assert d.traces.shape == (14, 3, 4, 4096) and d.traces.dtype == np.uint16
    assert [d.dump for d in dumps] == ["F0001", "F0002"] and dumps[1].n_events == 10
    assert sorted(set(d.trigger_type)) == [1, 2, 3] and d.pileup.sum() == 1
    assert NAMES == ["Side2pC", "Side2pF", "Side2pE", "Side2pB", "Side2pA", "Side2pD"]


# ---- MIDAS ------------------------------------------------------------------------------------------------------

def test_midas_file_structure(out):
    raw = gzip.open(out["midas"] / "07221203_2025_F0001.mid.gz").read()
    import struct
    event_id, mask, serial, ts, size = struct.unpack_from("<HHIII", raw, 0)
    assert (event_id, mask) == (0x8000, ss.BOR_MASK)                                      # begin of run: the ODB
    assert (mask, serial) == (ss.BOR_MASK, ss.RUN_NUMBER)
    pos, ids, banks = 16 + size, [], []
    while pos < len(raw):
        event_id, mask, serial, ts, size = struct.unpack_from("<HHIII", raw, pos)
        ids.append((event_id, serial))
        if event_id == 1:
            banks.append(struct.unpack_from("<4s", raw, pos + 16 + 8)[0])
            assert (size - 20) % 8 == 0 and struct.unpack_from("<I", raw, pos + 16 + 12)[0] == 6      # TID_DWORD
        pos += 16 + size
    assert pos == len(raw)
    assert ids[:-1] == [(1, s) for s in range(16)] and ids[-1] == (0x8001, ss.RUN_NUMBER)      # veto, 14 triggers, 1 polling, end of run
    assert banks[0] == b"LDV0" and banks.count(b"SCD0") == 15


def test_midas_round_trips_every_trace_and_header(out, dumps):
    for dump in dumps:
        got = ss.read_midas(out["midas"] / f"{dump.series}_{dump.dump}.mid.gz")
        assert got["vetoes"] == 1 and got["odb_end"] is not None
        events = [ev for ev in got["events"] if ev["trigger_type"] != ss.POLLING]
        assert len(events) == dump.n_events and len(got["events"]) == dump.n_events + 1
        for e, ev in enumerate(events):
            assert ev["event_number"] == dump.event[e] and ev["trigger_type"] == dump.trigger_type[e]
            assert ev["trigger_id"] == e + 1 and ev["timestamp"] == dump.timestamp[e]
            assert [d["detector_id"] for d in ev["detectors"]] == [1, 2, 3]
            for b, det in enumerate(ev["detectors"]):
                assert det["detector_type"] == ss.DETECTOR_TYPE
                for i, ch in enumerate(det["channels"]):
                    assert (ch["channel_num"], ch["channel_type"], ch["pretrigger"]) == (i, 1, ss.CONFIG.pretrigger_samples)
                    assert ch["sample_rate_khz"] == 1250 and ch["downsampling"] == 1
                    np.testing.assert_array_equal(ch["data"], dump.traces[e, b, i])


def test_midas_odb_carries_the_readout(out):
    odb = ss.read_midas(out["midas"] / "07221203_2025_F0001.mid.gz")["odb"].decode("latin-1")
    assert odb.startswith("<?xml") and odb.count('<dir name="Det0') == 3
    assert re.search(r'Phonon on-pulse length \(samp\)" type="INT" handle="1">4096<', odb)
    assert re.search(r'Phonon sampling rate \(Hz\)" type="FLOAT" handle="1">1250000', odb)


def test_midas_files_are_reproducible(dumps, tmp_path):
    a = ss.write_midas(dumps[1], tmp_path / "a")
    b = ss.write_midas(dumps[1], tmp_path / "b")
    assert a.read_bytes() == b.read_bytes()


# ---- idx --------------------------------------------------------------------------------------------------------

def test_idx_dump_reads_with_the_nsdf_loader(out, dumps):
    pytest.importorskip("OpenVisus")
    from nsdf_dark_matter import idx as nsdf
    d = dumps[0]
    cdms = nsdf.load_all_data(str(out["idx"] / "07221203_2025_F0001"))
    assert len(cdms.get_event_ids()) == d.n_events and len(cdms.get_detector_ids()) == d.n_events * 3
    for e in (0, 4, 13):
        block = cdms.get_detector_channels(f"{d.event[e]}_1_Phonon_4096")
        np.testing.assert_array_equal(block, d.traces[e, 1])
        assert cdms.get_event_metadata(str(d.event[e])).trigger_type == ss.TRIGGER_TYPES[d.trigger_type[e]]


def test_the_idx_adapter_reads_the_sensors_and_agrees_with_the_goldpan_dataset(out, dumps):
    pytest.importorskip("OpenVisus")
    channels = {n: (b, i) for n, b, i in ss.sensors()}
    for dump in dumps:
        ev = idx.read(out["idx"] / f"{dump.series}_{dump.dump}", detector_name="NSDF", channels=channels, config=ss.CONFIG,
                      roles={n: "phonon" for n in channels})
        assert ev.n_events == dump.n_events and ev.quantities["dump"].to_list() == [dump.dump] * dump.n_events
        assert ev.quantities["trigger_type"].to_list() == [ss.TRIGGER_TYPES[t] for t in dump.trigger_type]
        for n, b, i in ss.sensors():
            np.testing.assert_array_equal(ev.trace(n), dump.traces[:, b, i, :].astype(float))
    native = parquet.read(out["goldpan"])
    assert len(native) == 24 and native.detector.channel_names() == NAMES
    first = native.select(np.asarray(native.quantities["dump"].to_list()) == "F0001")
    np.testing.assert_array_equal(first.trace("Side2pC"), dumps[0].traces[:, 0, 0, :])


def test_the_goldpan_dataset_keeps_the_events_and_the_readout(out, dumps):
    ev = parquet.read(out["goldpan"])
    assert ev.detector.readout.config() == ss.CONFIG
    assert ev.quantities["event"].to_list() == list(dumps[0].event) + list(dumps[1].event)
    assert ev.trace("Side2pA").dtype == np.uint16


# ---- RQs --------------------------------------------------------------------------------------------------------

def test_rq_parquet_holds_the_rqs_of_every_event(out, dumps):
    for dump in dumps:
        table = pq.read_table(out["rq_parquet"] / f"{dump.series}_{dump.dump}.parquet")
        ref = ss.rqs(dump)
        assert table.column_names[:2] == ["series", "dump"] and table.num_rows == dump.n_events
        for k, v in ref.items():
            np.testing.assert_allclose(table.column(k).to_numpy(), v)
        assert set(table.column_names) >= {f"{n}{s}" for n in NAMES for s in ("std", "max", "maxbin")}


def test_rq_root_has_the_event_tree_and_the_zip_tree_row_aligned(out, dumps):
    uproot = pytest.importorskip("uproot")
    for dump in dumps:
        with uproot.open(out["rq_root"] / f"{dump.series}_{dump.dump}.root") as f:
            tree, zipt = f["rqDir/eventTree"], f["rqDir/zip1"]
            assert set(tree.keys()) == set(ss.EVENT_LEVEL_RQS)
            assert tree.num_entries == zipt.num_entries == dump.n_events
            ref = ss.rqs(dump)
            np.testing.assert_array_equal(tree["EventNumber"].array(library="np"), dump.event)
            for k in ("Side2pAstd", "Side2pCmax", "Side2pFmaxbin"):
                np.testing.assert_allclose(zipt[k].array(library="np"), ref[k])


def test_rqs_agree_with_goldpans_own_quantities_from_the_traces(dumps):
    d = dumps[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for n, b, i in ss.sensors():
            std = pretrigger_std(d.traces[:, b, i, :].astype(float), ss.CONFIG)
            np.testing.assert_allclose(ss.rqs(d)[f"{n}std"], std * ss.AMPS_PER_COUNT)


def test_rq_cuts_find_the_planted_events_in_the_synthetic_rqs(out, dumps):
    d = dumps[0]
    r = {k: pq.read_table(out["rq_parquet"] / "07221203_2025_F0001.parquet").column(k).to_numpy() for k in
         ss.rqs(d)}
    ratios = phonon_log_ratios(r, NAMES)
    assert sorted(ratios) == sorted(NAMES)
    random = r["EventType"] == 2
    thresholds = {n: 1.0 for n in NAMES}                  # noise sits near log10(ratio) ~ 0.4; any pulse is far above
    assert list(np.flatnonzero(pileup_randoms(ratios, thresholds) & ~(d.trigger_type == 1))) == [4]
    clean = loose_randoms(ratios, -1.0, thresholds)
    assert not clean[d.trigger_type == 1].any() and not clean[4] and clean[random & ~d.pileup].all()
