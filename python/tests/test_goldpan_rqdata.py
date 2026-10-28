"""goldpan.rqdata: `load(dataset, rqs)` with the call of the collaboration's `rqdata`, and its on-disk cache. The RQ files are the ones
of the synthetic series (`synthetic_series.write_rq_root`), written under the names of two real-looking series."""
import os
import time

import numpy as np
import pytest

pytest.importorskip("uproot")

import synthetic_series as ss
from goldpan import rqdata
from goldpan.rqdata import RQData, load

SERIES = ("24260424_145101", "24260618_202553")
NAMES = [n for n, _, _ in ss.sensors()]
RQS = ["EventType", "PTOFamps", "P*max", "P*std"]
CHANNELS = NAMES[:3]                                       # what P* stands for in these files


def write_file(folder, series, dump, scale=1.0):
    """`<folder>/<series>.root` with the RQs of one synthetic dump; `scale` multiplies PTOFamps."""
    import uproot
    folder.mkdir(parents=True, exist_ok=True)
    r = ss.rqs(dump)
    r["PTOFamps"] = r["PTOFamps"] * scale
    path = folder / f"{series}.root"
    with uproot.recreate(path) as f:
        f["rqDir/eventTree"] = {k: r[k] for k in ss.EVENT_LEVEL_RQS}
        f["rqDir/zip1"] = {k: v for k, v in r.items() if k not in ss.EVENT_LEVEL_RQS}
    return path


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Two series on disk, the cache in the temporary folder, and the environment that lets `load(series, RQS)` be called bare."""
    dumps = ss.all_dumps()
    root = tmp_path / "rq"
    for series, dump in zip(SERIES, dumps):
        write_file(root, series, dump)
    monkeypatch.setenv(rqdata.ENV_CACHE, str(tmp_path / "cache"))
    monkeypatch.setenv(rqdata.ENV_FILES, str(root / "{series}.root"))
    monkeypatch.setenv(rqdata.ENV_DETECTOR, "1")
    return tmp_path, root, dumps


def load_(dataset, rqs=RQS, **kw):
    return load(dataset, rqs, phonon_channels=CHANNELS, **kw)


# ---- the call -------------------------------------------------------------------------------------------------------

def test_load_of_a_series_gives_numpy_arrays_one_row_per_event_and_expands_p_star(env, capsys):
    tmp, root, dumps = env
    data = load_(SERIES[0])
    ref = ss.rqs(dumps[0])
    assert isinstance(data, RQData) and data.dataset == SERIES[0] and data.skipped == ()
    assert data.files == {SERIES[0]: str(root / f"{SERIES[0]}.root")}
    np.testing.assert_allclose(data["PTOFamps"], ref["PTOFamps"])
    for ch in CHANNELS:
        np.testing.assert_allclose(data[f"{ch}max"], ref[f"{ch}max"])
        np.testing.assert_allclose(data[f"{ch}std"], ref[f"{ch}std"])
    assert f"{NAMES[3]}max" not in data                                        # P* is the phonon channels given, no more
    assert list(data["series"]) == [SERIES[0]] * dumps[0].n_events and data["event"].tolist() == list(dumps[0].event)
    assert "from the RQ files" in capsys.readouterr().out


def test_a_list_of_series_and_a_csv_are_concatenated_in_order(env, tmp_path):
    tmp, root, dumps = env
    both = load_(list(SERIES))
    ref = np.concatenate([ss.rqs(d)["PTOFamps"] for d in dumps[:2]])
    np.testing.assert_allclose(both["PTOFamps"], ref)
    assert both["series"].tolist() == [SERIES[0]] * dumps[0].n_events + [SERIES[1]] * dumps[1].n_events
    csv = tmp_path / "ds.csv"
    csv.write_text("# a dataset\nseries,fridge_run\n" + "\n".join(f"{s},4" for s in SERIES) + "\n", encoding="utf-8")
    np.testing.assert_allclose(load_(str(csv))["PTOFamps"], ref)


def test_a_series_with_no_file_is_skipped_and_listed(env):
    data = load_([SERIES[0], "24260101_000000"], verbose=False)
    assert data.skipped == ("24260101_000000",) and list(data.files) == [SERIES[0]]
    empty = load_("24260101_000000", verbose=False)
    assert len(empty["series"]) == 0 and empty.skipped == ("24260101_000000",)


def test_a_branch_the_file_does_not_have_is_nan(env):
    data = load_(SERIES[0], ["PTOFamps", "PFS2std"], verbose=False)
    assert np.isnan(data["PFS2std"]).all() and len(data["PFS2std"]) == len(data["PTOFamps"])


# ---- the cache ------------------------------------------------------------------------------------------------------

def test_the_second_load_comes_from_the_cache_and_equals_the_first(env, capsys):
    tmp, root, dumps = env
    first = load_(SERIES[0])
    assert "from the RQ files" in capsys.readouterr().out and len(os.listdir(rqdata.cache_dir())) == 1
    second = load_(SERIES[0])
    assert "from cache" in capsys.readouterr().out
    assert set(first) == set(second)
    for k in first:
        np.testing.assert_array_equal(first[k], second[k])
    assert not [f for f in os.listdir(rqdata.cache_dir()) if f.endswith(".tmp")]


def test_a_read_with_fewer_branches_is_served_by_a_cached_read_with_more(env, capsys):
    load_(SERIES[0], ["EventType", "PTOFamps", "P*max"], verbose=False)
    fewer = load_(SERIES[0], ["PTOFamps"])
    assert "from cache" in capsys.readouterr().out and "PTOFamps" in fewer
    more = load_(SERIES[0], ["PTOFamps", "P*std"])                              # a branch not cached: read again
    assert "from the RQ files" in capsys.readouterr().out and f"{CHANNELS[0]}std" in more


def test_a_rewritten_file_is_read_again_not_served_from_an_old_entry(env, capsys):
    tmp, root, dumps = env
    old = load_(SERIES[0], verbose=False)
    path = write_file(root, SERIES[0], dumps[0], scale=2.0)
    os.utime(path, ns=(time.time_ns(), time.time_ns() + 5_000_000_000))        # a different modification time, whatever the clock says
    new = load_(SERIES[0])
    assert "from the RQ files" in capsys.readouterr().out
    np.testing.assert_allclose(new["PTOFamps"], old["PTOFamps"] * 2.0)


def test_refresh_reads_again_and_cache_false_neither_reads_nor_writes_the_cache(env, capsys):
    tmp, root, dumps = env
    load_(SERIES[0], verbose=False)
    load_(SERIES[0], refresh=True)
    assert "from the RQ files" in capsys.readouterr().out
    rqdata.cache_clear()
    load_(SERIES[0], cache=False, verbose=False)
    assert not os.path.exists(rqdata.cache_dir()) or not os.listdir(rqdata.cache_dir())


def test_the_cache_is_in_goldpan_cache_and_never_in_the_working_folder(env, monkeypatch):
    tmp, root, dumps = env
    assert rqdata.cache_dir() == os.path.join(str(tmp / "cache"), "rqdata")
    monkeypatch.delenv(rqdata.ENV_CACHE)
    assert rqdata.cache_dir() == os.path.join(os.path.expanduser("~"), ".cache", "goldpan", "rqdata")


def test_cache_info_lists_the_entries_and_cache_clear_removes_them(env, capsys):
    load_(SERIES[0], verbose=False)
    load_(list(SERIES), verbose=False)
    rows = rqdata.cache_info()
    assert len(rows) == 2 and all(r["file"].endswith(".npz") and r["bytes"] > 0 for r in rows)
    assert "2 entries" in capsys.readouterr().out
    assert rqdata.cache_clear() == 2 and rqdata.cache_info(verbose=False) == []


def test_a_damaged_entry_is_ignored_and_replaced(env, capsys):
    load_(SERIES[0], verbose=False)
    entry = os.path.join(rqdata.cache_dir(), os.listdir(rqdata.cache_dir())[0])
    with open(entry, "wb") as f:
        f.write(b"not an npz")
    data = load_(SERIES[0])
    assert "from the RQ files" in capsys.readouterr().out and len(data["series"]) > 0
    assert "from cache" in (load_(SERIES[0]) and capsys.readouterr().out)


# ---- where the files are, and what is refused -----------------------------------------------------------------------

def test_files_and_detector_can_be_given_in_the_call_instead_of_the_environment(env, monkeypatch):
    tmp, root, dumps = env
    monkeypatch.delenv(rqdata.ENV_FILES)
    monkeypatch.delenv(rqdata.ENV_DETECTOR)
    with pytest.raises(ValueError, match="GOLDPAN_RQ_DETECTOR"):
        load_(SERIES[0])
    monkeypatch.setenv(rqdata.ENV_DETECTOR, "1")
    with pytest.raises(ValueError, match="GOLDPAN_RQ_FILES"):
        load_(SERIES[0])
    data = load_(SERIES[0], detector=1, files=str(root / "{series}.root"), verbose=False)
    assert len(data["PTOFamps"]) == dumps[0].n_events
    by_function = load_(SERIES[0], detector="1", files=lambda s: root / f"{s}.root", cache=False, verbose=False)
    np.testing.assert_array_equal(by_function["PTOFamps"], data["PTOFamps"])


def test_find_file_takes_the_last_match_and_wants_series_in_the_pattern(env):
    tmp, root, dumps = env
    (root / "a").mkdir()
    (root / "a" / f"R1_{SERIES[0]}.root").write_bytes(b"")
    (root / "a" / f"R2_{SERIES[0]}.root").write_bytes(b"")
    assert rqdata.find_file(SERIES[0], str(root / "a" / "*_{series}.root")).endswith(f"R2_{SERIES[0]}.root")
    assert rqdata.find_file("24260101_000000", str(root / "{series}.root")) is None
    with pytest.raises(ValueError, match=r"must contain \{series\}"):
        rqdata.find_file(SERIES[0], str(root / "x.root"))


def test_a_bad_dataset_or_detector_is_refused(env):
    with pytest.raises(ValueError, match="neither a series name"):
        load_("not-a-series")
    with pytest.raises(ValueError, match="not series names"):
        load_(["24260424_145101", "bogus"])
    with pytest.raises(ValueError, match="whole number"):
        load_(SERIES[0], detector="seven")


def test_expand_branches_replaces_p_star_once_per_name_and_keeps_the_order():
    assert rqdata.expand_branches(["EventType", "P*max", "EventType"], ["PA", "PB"]) == ["EventType", "PAmax", "PBmax"]
    assert rqdata.expand_branches(["P*"], ["PA"]) == ["PA"]
    assert rqdata.expand_branches(["P*max"])[0] == "PAS1max" and len(rqdata.expand_branches(["P*max"])) == 12


def test_series_list_accepts_a_name_a_list_or_a_csv(tmp_path):
    assert rqdata.series_list("24260424_145101") == ["24260424_145101"]
    assert rqdata.series_list(("24260424_145101", "24260618_202553")) == list(SERIES)
    csv = tmp_path / "s.csv"
    csv.write_text("series\n24260424_145101\n\n# skipped\n24260618_202553\n", encoding="utf-8")
    assert rqdata.series_list(csv) == list(SERIES)
    csv.write_text("run\n4\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no `series` column"):
        rqdata.series_list(str(csv))
