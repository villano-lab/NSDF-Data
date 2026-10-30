"""goldpan.runmeta: run metadata joined to events by series."""
import numpy as np
import pytest

from goldpan import runmeta

TABLE = (
    "series,hv_v,trigger,trigger_value,duration_min\n"
    "07221121_2214,0.0,DCRC1pA 2,2.0,779\n"
    "07221124_2022,-34.0,DCRC1pA 2,2.0,97\n"
    "07221124_2331,-34.0,DCRC1pA 100,100.0,\n"
)


@pytest.fixture
def table(tmp_path):
    path = tmp_path / "series.csv"
    path.write_text(TABLE, encoding="utf-8")
    return runmeta.read_table(path)


def test_read_table_keeps_series_as_text_and_makes_numbers_floats(table):
    # float("07221121_2214") is a number in Python (underscores are allowed): the names must stay text
    assert list(table["series"]) == ["07221121_2214", "07221124_2022", "07221124_2331"]
    assert table["hv_v"].dtype == float and list(table["hv_v"]) == [0.0, -34.0, -34.0]
    assert table["trigger"].dtype.kind == "U"
    assert np.isnan(table["duration_min"][2])


def test_read_table_refuses_a_file_without_a_series_column_or_with_a_series_twice(tmp_path):
    (tmp_path / "a.csv").write_text("name,hv_v\nx,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="series"):
        runmeta.read_table(tmp_path / "a.csv")
    (tmp_path / "b.csv").write_text("series,hv_v\ns1,1\ns1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="twice"):
        runmeta.read_table(tmp_path / "b.csv")


def test_per_event_gives_one_value_per_event_in_the_order_of_the_events(table):
    s = np.array(["07221124_2022", "07221121_2214", "07221124_2331", "07221124_2022", "07221124_2331"])
    cols = runmeta.per_event(s, table, ["hv_v", "trigger_value"])
    assert list(cols["hv_v"]) == [-34.0, 0.0, -34.0, -34.0, -34.0]
    assert list(cols["trigger_value"]) == [2.0, 2.0, 100.0, 2.0, 100.0]
    assert set(runmeta.per_event(s, table)) == {"hv_v", "trigger", "trigger_value", "duration_min"}


def test_per_event_names_a_series_that_is_not_in_the_table(table):
    with pytest.raises(KeyError, match="nope"):
        runmeta.per_event(["07221121_2214", "nope"], table)


def test_groups_split_the_events_by_the_chosen_columns(table):
    s = np.array(["07221124_2022", "07221121_2214", "07221124_2331", "07221124_2022", "07221124_2331"])
    got = {key: list(idx) for key, idx in runmeta.groups(s, table)}
    assert got == {(-34.0, 2.0): [0, 3], (-34.0, 100.0): [2, 4], (0.0, 2.0): [1]}
    only_hv = {key: list(idx) for key, idx in runmeta.groups(s, table, by=("hv_v",))}
    assert only_hv == {(-34.0,): [0, 2, 3, 4], (0.0,): [1]}


def test_rows_are_plain_json_values_and_name_a_missing_series(table):
    got = runmeta.rows(table, ["07221124_2331", "07221124_2331", "07221121_2214"])
    assert got == {"07221121_2214": {"hv_v": 0.0, "trigger": "DCRC1pA 2", "trigger_value": 2.0, "duration_min": 779.0},
                   "07221124_2331": {"hv_v": -34.0, "trigger": "DCRC1pA 100", "trigger_value": 100.0, "duration_min": None}}
    with pytest.raises(KeyError, match="nope"):
        runmeta.rows(table, ["nope"])


def test_the_digest_follows_the_values_of_the_series_asked_for_and_nothing_else(table):
    a = runmeta.digest(table, ["07221124_2022"])
    assert a == runmeta.digest(table, ["07221124_2022", "07221124_2022"])
    other = dict(table, hv_v=table["hv_v"].copy())
    other["hv_v"][0] = 5.0                                                  # another series changed
    assert runmeta.digest(other, ["07221124_2022"]) == a
    other["hv_v"][1] = -35.0                                                # this one changed
    assert runmeta.digest(other, ["07221124_2022"]) != a
