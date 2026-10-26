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
