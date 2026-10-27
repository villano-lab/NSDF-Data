"""Tests of goldpan.adapters.rq_root and goldpan.adapters.rq, on the ROOT RQ files of the synthetic series."""
import awkward as ak
import numpy as np
import pytest

pytest.importorskip("uproot")

import synthetic_series as ss
from goldpan import adapters
from goldpan.adapters import parquet, rq, rq_root

NAMES = [n for n, _, _ in ss.sensors()]


@pytest.fixture(scope="module")
def folder(tmp_path_factory):
    out = tmp_path_factory.mktemp("rq")
    dumps = ss.all_dumps()
    for d in dumps:
        ss.write_rq_root(d, out / "root")
    ss.write_goldpan(dumps[0], out / "goldpan")
    return out


@pytest.fixture(scope="module")
def dump():
    return ss.all_dumps()[0]


def test_read_a_file_gives_one_record_per_event_with_the_key_first(folder, dump):
    t = rq_root.read(folder / "root" / "07221203_2025_F0001.root", detector=1)
    assert len(t) == dump.n_events and ak.fields(t)[:3] == ["series", "dump", "event"]
    assert t["series"].to_list() == ["07221203_2025"] * 14 and t["dump"].to_list() == ["F0001"] * 14
    assert t["event"].to_list() == list(dump.event)
    ref = ss.rqs(dump)
    for name in ("EventType", "PTOFamps", "Side2pAstd", "Side2pCmax", "Side2pFmaxbin"):
        np.testing.assert_allclose(ak.to_numpy(t[name]), ref[name])


def test_branches_can_be_named_and_use_wildcards(folder):
    f = folder / "root" / "07221203_2025_F0002.root"
    t = rq_root.read(f, detector=1, branches=["EventType", "Side2p*max"])
    got = set(ak.fields(t))
    assert got == {"series", "dump", "event", "EventType"} | {f"{n}max" for n in NAMES}


def test_a_branch_the_file_does_not_have_is_nan_and_listed(folder):
    f = folder / "root" / "07221203_2025_F0001.root"
    t = rq_root.read(f, detector=1, branches=["PTOFamps", "PFS2std"])
    assert np.isnan(ak.to_numpy(t["PFS2std"])).all() and len(t) == 14
    assert rq_root.missing(f, detector=1, branches=["PTOFamps", "PFS2std", "Nope*"]) == ["PFS2std", "Nope*"]
    assert "PFS2std" not in rq_root.branches(f, detector=1)["zip1"]


def test_branches_lists_both_trees(folder):
    b = rq_root.branches(folder / "root" / "07221203_2025_F0001.root", detector=1)
    assert set(b) == {"eventTree", "zip1"} and "EventNumber" in b["eventTree"] and "Side2pCstd" in b["zip1"]


def test_the_detector_is_required_and_must_exist(folder):
    f = folder / "root" / "07221203_2025_F0001.root"
    with pytest.raises(TypeError):
        rq_root.read(f)
    with pytest.raises(KeyError, match="zip7"):
        rq_root.read(f, detector=7)


def test_a_folder_or_a_list_of_files_concatenates_in_order(folder, dump):
    t = rq_root.read(folder / "root", detector=1, branches=["EventType"])
    assert len(t) == 24 and t["dump"].to_list() == ["F0001"] * 14 + ["F0002"] * 10
    u = rq_root.read(sorted((folder / "root").glob("*.root")), detector=1, branches=["EventType"])
    assert u["event"].to_list() == t["event"].to_list()


def test_series_comes_from_the_file_name_unless_given(folder, tmp_path):
    f = folder / "root" / "07221203_2025_F0001.root"
    assert rq_root.read(f, detector=1, branches=["EventType"], series="X1")["series"].to_list()[0] == "X1"
    other = tmp_path / "rq.root"
    other.write_bytes(f.read_bytes())
    with pytest.raises(ValueError, match="series"):
        rq_root.read(other, detector=1)


def test_iter_chunks_joins_to_read(folder):
    f = folder / "root" / "07221203_2025_F0001.root"
    chunks = list(rq_root.iter_chunks(f, chunk=5, detector=1, branches=["EventType", "Side2pAstd"]))
    assert [len(c) for c in chunks] == [5, 5, 4]
    whole = rq_root.read(f, detector=1, branches=["EventType", "Side2pAstd"])
    assert ak.concatenate(chunks).to_list() == whole.to_list()


def test_the_registry_guesses_root_files_and_folders(folder):
    assert len(adapters.read(folder / "root" / "07221203_2025_F0001.root", detector=1, branches=["EventType"])) == 14
    assert len(adapters.read(folder / "root", detector=1, branches=["EventType"])) == 24
    assert "rq_root" in adapters.available()


# ---- attach ------------------------------------------------------------------------------------------------------

def test_attach_adds_the_rqs_to_events_by_key(folder, dump):
    ev = parquet.read(folder / "goldpan")
    table = rq_root.read(folder / "root", detector=1, branches=["EventType", "PTOFamps", "Side2pCstd"])
    out = rq.attach(ev, table)
    assert out.n_events == 14 and out.quantities["event"].to_list() == ev.quantities["event"].to_list()
    np.testing.assert_allclose(ak.to_numpy(out.quantities["PTOFamps"]), ss.rqs(dump)["PTOFamps"])
    assert "PTOFamps" not in ev.quantities.fields                               # the original is unchanged
    out2 = rq.attach(ev, table, prefix="rq_")
    assert "rq_EventType" in out2.quantities.fields and "trigger_type" in out2.quantities.fields


def test_attach_refuses_missing_events_duplicates_and_name_clashes(folder):
    ev = parquet.read(folder / "goldpan")
    table = rq_root.read(folder / "root", detector=1, branches=["EventType"])
    with pytest.raises(ValueError, match="no row in the table"):
        rq.attach(ev, table[:5])
    with pytest.raises(ValueError, match="two rows"):
        rq.attach(ev, table, on=("event",))                                    # event numbers restart in every dump
    once = rq.attach(ev, table)
    with pytest.raises(ValueError, match="already have"):
        rq.attach(once, table)
    with pytest.raises(ValueError, match="no field"):
        rq.attach(ev, table, on=("dump", "nope"))


def test_attach_can_match_on_fewer_fields(folder):
    ev = parquet.read(folder / "goldpan")
    table = rq_root.read(folder / "root" / "07221203_2025_F0001.root", detector=1, branches=["EventType"], series="OTHER")
    with pytest.raises(ValueError, match="no row"):
        rq.attach(ev, table)                                                    # the series names differ
    assert rq.attach(ev, table, on=("dump", "event")).quantities["EventType"].to_list()[:3] == [1, 2, 2]


# ---- write: our quantities in the RQ layout, under our names

def _quantities(series="24260424_145101", dump="F0001", n=3, base=0.0):
    from goldpan.config import DCRC_RUN76
    from goldpan.data import ChannelInfo, Detector, Events, Readout
    det = Detector("TOY", (ChannelInfo("A", role="phonon"),), Readout.single(1500, DCRC_RUN76))
    q = ak.Array({"series": [series] * n, "dump": [dump] * n, "event": list(range(10000, 10000 + n)),
                  "A": ak.zip({"adc_max": [base + i for i in range(n)], "max_time_s": [1e-4 * (i + 1) for i in range(n)]},
                              depth_limit=1),
                  "B": ak.zip({"adc_max": [base + 10.0 + i for i in range(n)]}, depth_limit=1)})
    return Events(det, {}, q, {"goldsluice": {"version": "x", "steps": [1]}})


def test_write_uses_the_rq_container_and_our_names(tmp_path):
    import uproot
    files = rq_root.write(_quantities(), tmp_path, detector=7)
    assert [f.name for f in files] == ["24260424_145101_F0001.root"]
    with uproot.open(files[0]) as f:
        assert {"rqDir/eventTree", "rqDir/zip7", "infoDir/goldsluice"} <= set(f.keys(cycle=False))
        assert sorted(f["rqDir/eventTree"].keys()) == ["DumpNumber", "EventNumber", "SeriesNumber"]
        assert sorted(f["rqDir/zip7"].keys()) == ["A_adc_max", "A_max_time_s", "B_adc_max"]      # ours, not P<letter>S<side>...
        assert {str(b.typename) for b in f["rqDir/zip7"].values()} == {"double"}
        assert f["rqDir/eventTree"]["SeriesNumber"].array(library="np")[0] == 24260424145101
        assert f["rqDir/eventTree"]["DumpNumber"].array(library="np").tolist() == [1.0, 1.0, 1.0]
        assert '"version": "x"' in str(f["infoDir/goldsluice"])


def test_what_write_wrote_read_gives_back(tmp_path):
    rq_root.write(_quantities(), tmp_path, detector=7)
    t = rq_root.read(tmp_path, detector=7)
    assert (t["series"].to_list(), t["dump"].to_list(), t["event"].to_list()) == (["24260424_145101"] * 3, ["F0001"] * 3, [10000, 10001, 10002])
    assert t["A_adc_max"].to_list() == [0.0, 1.0, 2.0] and t["B_adc_max"].to_list() == [10.0, 11.0, 12.0]
    np.testing.assert_allclose(t["A_max_time_s"].to_list(), [1e-4, 2e-4, 3e-4])
    assert rq_root.branches(tmp_path, detector=7)["zip7"] == ["A_adc_max", "A_max_time_s", "B_adc_max"]


def test_write_makes_one_file_per_series_and_dump_and_a_folder_of_them_reads_as_one_dataset(tmp_path):
    from goldpan.data import Events
    a, b = _quantities(dump="F0001", n=2), _quantities(dump="F0002", n=3, base=100.0)
    files = rq_root.write(Events.concatenate(a, b), tmp_path, detector=1)
    assert [f.name for f in files] == ["24260424_145101_F0001.root", "24260424_145101_F0002.root"]
    t = rq_root.read(tmp_path, detector=1)
    assert t["dump"].to_list() == ["F0001"] * 2 + ["F0002"] * 3
    assert t["A_adc_max"].to_list() == [0.0, 1.0, 100.0, 101.0, 102.0]
    assert [len(c) for c in rq_root.iter_chunks(tmp_path, chunk=4, detector=1)] == [2, 3]             # file by file


def test_write_replaces_a_file_of_the_same_name_and_never_assumes_the_detector(tmp_path):
    rq_root.write(_quantities(base=0.0), tmp_path, detector=7)
    rq_root.write(_quantities(base=50.0), tmp_path, detector=7)
    assert rq_root.read(tmp_path, detector=7)["A_adc_max"].to_list() == [50.0, 51.0, 52.0]
    with pytest.raises(TypeError):
        rq_root.write(_quantities(), tmp_path)                                  # detector is required


def test_write_refuses_what_it_cannot_name_or_number(tmp_path):
    from goldpan.data import Events
    with pytest.raises(ValueError, match="dump number"):
        rq_root.write(_quantities(dump="first"), tmp_path, detector=7)
    with pytest.raises(ValueError, match="series number"):
        rq_root.write(_quantities(series="S1"), tmp_path, detector=7)
    ev = _quantities()
    keys = {k: ev.quantities[k] for k in ("series", "dump", "event")}
    bad = ak.Array({**keys, "A": ak.zip({"max-time": [1.0, 2.0, 3.0]}, depth_limit=1)})
    with pytest.raises(ValueError, match="usable branch name"):
        rq_root.write(Events(ev.detector, {}, bad, {}), tmp_path, detector=7)
    with pytest.raises(ValueError, match="no quantities"):
        rq_root.write(Events(ev.detector, {}, ak.Array(keys), {}), tmp_path, detector=7)
