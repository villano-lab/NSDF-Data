"""Tests of goldpan.adapters.midas on the MIDAS files of the synthetic series, and (when the paths are given) on real DAQ files.

The real-file tests need two samples from S3DF, which are data and so not in the repository: `GOLDPAN_MIDAS_SAMPLE` is the path of
the first 30 MB of a `.mid.lz4` file and `GOLDPAN_MIDAS_TAIL` the path of a gzip of the last 45 MB of its decompressed stream
(`lz4 -dc FILE | tail -c 45000000 | gzip`, on S3DF); without them those tests are skipped.
"""
import gzip
import os
import re
import struct

import awkward as ak
import numpy as np
import pytest

import synthetic_series as ss
from goldpan.adapters import midas
from goldpan.config import PulseConfig
from goldpan.testing import check_adapter

CHANNELS = {"Side2pC": 0, "Side2pF": 1, "Side2pE": 3}          # detector 1 (board 0): the inputs of the first three sensors
KW = dict(detector_name="NSDF", detector_id=1, channels=CHANNELS, config=ss.CONFIG)


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    out = tmp_path_factory.mktemp("midas")
    dumps = ss.all_dumps()
    for d in dumps:
        ss.write_midas(d, out)
    return out


@pytest.fixture(scope="module")
def dump():
    return ss.all_dumps()[0]


@pytest.fixture(scope="module")
def path(folder):
    return folder / "07221203_2025_F0001.mid.gz"


def test_read_gives_the_traces_and_the_event_quantities(path, dump):
    ev = midas.read(path, **KW)
    assert len(ev) == dump.n_events and ev.detector.channel_names() == list(CHANNELS)
    for name, inp in CHANNELS.items():
        assert ev.trace(name).dtype == np.uint16 and ev.trace(name).shape == (14, 4096)
        np.testing.assert_array_equal(ev.trace(name), dump.traces[:, 0, inp, :])
    q = ev.quantities
    assert q["series"].to_list() == ["07221203_2025"] * 14 and q["dump"].to_list() == ["F0001"] * 14
    assert q["event"].to_list() == list(dump.event) and q["trigger_id"].to_list() == list(range(1, 15))
    assert q["trigger_type"].to_list() == [ss.TRIGGER_TYPES[t] for t in dump.trigger_type]
    assert q["global_timestamp"].to_list() == list(dump.timestamp)
    assert ev.detector.readout.config() == ss.CONFIG and ev.detector.channel("Side2pF").input == "1"


def test_meta_has_the_run_the_completeness_and_what_was_skipped(path):
    meta = midas.read(path, **KW).meta
    assert meta["run"] == dict(run_number=ss.RUN_NUMBER, state=3, start_time=ss.START_TIME, stop_time=ss.START_TIME + 7200)
    assert meta["complete"] is True and meta["skipped_events"] == 2           # the veto-only event and the polling-cycle event
    assert meta["format_version"] == 8 and meta["adapter"] == "midas" and meta["source"].endswith(".mid.gz")


def test_other_dumps_take_series_and_dump_from_the_file_name(folder):
    ev = midas.read(folder / "07221203_2025_F0002.mid.gz", **KW)
    assert set(ev.quantities["dump"].to_list()) == {"F0002"} and len(ev) == 10
    other = midas.read(folder / "07221203_2025_F0002.mid.gz", series="X", dump="D", **KW)
    assert other.quantities["series"].to_list()[0] == "X" and other.quantities["dump"].to_list()[0] == "D"


def test_max_events_stops_early_and_says_the_file_is_not_complete(path):
    ev = midas.read(path, max_events=3, **KW)
    assert len(ev) == 3 and ev.meta["complete"] is False


def test_plain_gzip_and_lz4_files_are_the_same_events(tmp_path, path):
    raw = gzip.open(path).read()
    (tmp_path / "07221203_2025_F0001.mid").write_bytes(raw)
    a = midas.read(tmp_path / "07221203_2025_F0001.mid", **KW)
    b = midas.read(path, **KW)
    assert a.quantities.to_list() == b.quantities.to_list() and np.array_equal(a.trace("Side2pC"), b.trace("Side2pC"))
    lz4 = pytest.importorskip("lz4.frame")
    (tmp_path / "x" / "07221203_2025_F0001.mid.lz4").parent.mkdir()
    (tmp_path / "x" / "07221203_2025_F0001.mid.lz4").write_bytes(lz4.compress(raw))
    c = midas.read(tmp_path / "x" / "07221203_2025_F0001.mid.lz4", **KW)
    assert c.quantities.to_list() == b.quantities.to_list() and np.array_equal(c.trace("Side2pE"), b.trace("Side2pE"))


def test_a_file_that_stops_in_the_middle_gives_the_events_before_it(tmp_path, path):
    raw = gzip.open(path).read()
    cut = tmp_path / "07221203_2025_F0001.mid"
    cut.write_bytes(raw[:len(raw) // 2])
    ev = midas.read(cut, **KW)
    assert 3 < len(ev) < 14 and ev.meta["complete"] is False
    np.testing.assert_array_equal(ev.trace("Side2pC"), midas.read(path, **KW).trace("Side2pC")[:len(ev)])


def test_the_readout_you_name_is_checked_against_the_file(path):
    with pytest.raises(ValueError, match="1.6 us.*1250 kHz|0.8 us"):
        midas.read(path, **{**KW, "config": PulseConfig(1000, 10, 1.6e-6)})
    unknown = midas.read(path, **{**KW, "config": PulseConfig(1000, 10, None)})
    assert len(unknown) == 14                                                  # a config without a period is not checked


def test_missing_channels_and_detectors_are_errors(path):
    with pytest.raises(ValueError, match="no events"):
        midas.read(path, **{**KW, "channels": {"x": 9}})
    with pytest.raises(ValueError, match=r"has no channels \[9\]"):
        midas.read(path, **{**KW, "channels": {"a": 0, "x": 9}})
    with pytest.raises(ValueError, match="no events"):
        midas.read(path, **{**KW, "detector_id": 99})
    with pytest.raises(ValueError, match="no events"):
        midas.read(path, **{**KW, "channel_type": midas.CHARGE})
    with pytest.raises(ValueError, match="series"):
        midas.read(_renamed(path, "weird.mid.gz"), **KW)


def _renamed(path, name):
    target = path.parent / name
    target.write_bytes(path.read_bytes())
    return target


def test_iter_chunks_joins_to_read_and_passes_the_conformance_test(path):
    chunks = list(midas.iter_chunks(path, chunk=5, **KW))
    assert [len(c) for c in chunks] == [5, 5, 4]
    assert ak.concatenate([c.quantities for c in chunks]).to_list() == midas.read(path, **KW).quantities.to_list()
    assert chunks[0].meta["run"]["run_number"] == ss.RUN_NUMBER
    assert check_adapter(midas, path, **KW) == ["read() returns Events", "the invariants of Events hold",
                                                "iter_chunks joined equals read"]


def test_unpack_scd0_returns_the_blocks_of_each_kind_of_event(path):
    raw = list(midas.iter_events(path))
    assert raw[0].event_id == midas.EVENT_BEGIN_OF_RUN and raw[-1].event_id == midas.EVENT_END_OF_RUN
    assert (raw[0].serial, raw[0].mask) == (ss.RUN_NUMBER, ss.BOR_MASK)
    assert midas.unpack_scd0(raw[1].data) is None                                # the veto-only event
    full = midas.unpack_scd0(raw[2].data)                                        # every channel of every detector
    assert sorted(full["detectors"]) == [1, 2, 3] and sorted(full["detectors"][1]) == [0, 1, 2, 3]
    assert full["detectors"][1][0]["rate_khz"] == 1250 and full["detectors"][1][0]["pretrigger"] == ss.CONFIG.pretrigger_samples
    only = midas.unpack_scd0(raw[2].data, {2: {1}})
    assert list(only["detectors"][2]) == [1] and only["detectors"][1] == {}
    polling = midas.unpack_scd0(raw[5].data)
    assert polling["trigger_type"] == ss.POLLING and polling["detectors"] == {}


def test_a_bank_that_is_not_the_format_is_refused_with_a_message(path):
    raw = list(midas.iter_events(path))[2]
    data = bytearray(raw.data)
    struct.pack_into("<I", data, 20, (0x9 << 28) | (3 << 12) | 1)                # format version 3
    with pytest.raises(midas.MidasFormatError, match="version 3"):
        midas.unpack_scd0(bytes(data))
    data = bytearray(raw.data)
    struct.pack_into("<I", data, 24, 0x10000000)                                 # the trigger head replaced by a channel block
    with pytest.raises(midas.MidasFormatError, match="trigger head"):
        midas.unpack_scd0(bytes(data))


def test_parse_odb_reads_the_runinfo_directory_only(folder):
    xml = ss.read_midas(folder / "07221203_2025_F0001.mid.gz")["odb"]
    assert midas.parse_odb(xml) == dict(run_number=ss.RUN_NUMBER, state=1, start_time=ss.START_TIME, stop_time=0)
    assert midas.parse_odb(b"<odb></odb>") == {}
    decoy = b'<odb><dir name="Other"><key name="Run number" type="INT">5</key></dir></odb>'
    assert midas.parse_odb(decoy) == {}


# ---- real files (optional) --------------------------------------------------------------------------------------------

SAMPLE = os.environ.get("GOLDPAN_MIDAS_SAMPLE")
TAIL = os.environ.get("GOLDPAN_MIDAS_TAIL")
Z7 = PulseConfig(pretrigger_samples=6250, glitch_samples=10, sample_period_s=1.6e-6)


@pytest.mark.skipif(not SAMPLE or not os.path.exists(SAMPLE or ""), reason="GOLDPAN_MIDAS_SAMPLE not set")
def test_real_file_head_reads_with_the_z7_readout():
    pytest.importorskip("lz4.frame")
    kw = dict(detector_name="Z7", detector_id=7, config=Z7, channels={"PAS1": 0, "PAS2": 1, "PBS1": 2}, series="24260424_145101",
              dump="F0001")
    ev = midas.read(SAMPLE, **kw)
    assert len(ev) > 10 and ev.trace("PAS1").shape[1] == 32768 and ev.trace("PAS1").dtype == np.uint16
    assert ev.meta["run"]["run_number"] == 2626 and ev.meta["run"]["start_time"] == 1777056661
    assert ev.meta["complete"] is False and ev.meta["skipped_events"] > 0 and ev.meta["format_version"] == 8
    std = ev.trace("PAS1")[:, 100:6000].astype(float).std(axis=1)
    assert np.all((std > 5) & (std < 500))
    with pytest.raises(ValueError, match="1.6 us"):
        midas.read(SAMPLE, **{**kw, "config": PulseConfig(1000, 10, 0.8e-6)})
    assert [len(c) for c in midas.iter_chunks(SAMPLE, chunk=6, **kw)][0] == 6


@pytest.mark.skipif(not TAIL or not os.path.exists(TAIL or ""), reason="GOLDPAN_MIDAS_TAIL not set")
def test_real_end_of_run_odb_has_the_run_information():
    raw = gzip.open(TAIL).read()
    for m in re.finditer(re.escape(struct.pack("<HH", midas.EVENT_END_OF_RUN, 0x494D)), raw):
        event_id, mask, serial, ts, size = struct.unpack_from("<HHIII", raw, m.start())
        if m.start() + 16 + size == len(raw):
            info = midas.parse_odb(raw[m.start() + 16:])
            assert info["run_number"] == serial == 2626 and info["start_time"] == 1777056661
            assert info["stop_time"] == 1777063870 and info["stop_time"] > info["start_time"]
            return
    pytest.fail("no end-of-run event at the end of the tail")
