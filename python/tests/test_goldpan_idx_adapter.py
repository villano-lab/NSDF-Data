"""Tests of the idx adapter with a fake `cdms` object (no data needed): board and input to named channel, series and dump,
dropped events, trigger types."""
import numpy as np
import pytest

from goldpan.adapters import idx
from goldpan.config import DCRC_RUN76

N_SAMPLES = 40


class Meta:
    def __init__(self, trigger_type):
        self.trigger_type = trigger_type


class FakeCdms:
    """Ids look like '<event>_<board>_Phonon_<n>'; a board's traces are (4, n_samples), indexed by input."""

    def __init__(self, events=(10000, 10001, 10002), boards=(0, 1, 2), missing=(), trigger_types=True, n_samples=N_SAMPLES):
        self.ids = [f"{e}_{b}_Phonon_{b}" for e in events for b in boards if (e, b) not in missing]
        self.n_samples = n_samples
        self.trigger_types = trigger_types

    def get_detector_ids(self):
        return list(self.ids)

    def get_detector_channels(self, det_id):
        event, board = int(det_id.split("_")[0]), int(det_id.split("_")[1])
        base = event * 100 + board * 10
        return np.array([np.full(self.n_samples, base + k, dtype=np.int32) for k in range(4)])

    def get_event_metadata(self, event):
        if not self.trigger_types:
            raise KeyError(event)
        return Meta("Physics" if int(event) % 2 == 0 else "Unknown")


CHANNELS = {"Side2pC": (0, 0), "Side2pF": (0, 1), "Side2pA": (1, 1)}


def read(cdms=None, **kw):
    return idx.read(cdms or FakeCdms(), detector_name="S104", channels=CHANNELS, config=DCRC_RUN76,
                    series="07221203_2025", dump="F0001", **kw)


def test_named_channels_come_from_their_board_and_input():
    ev = read()
    assert ev.detector.name == "S104" and ev.detector.channel_names() == ["Side2pC", "Side2pF", "Side2pA"]
    assert ev.n_events == 3
    # (board 0, input 0) of event 10000 holds 10000*100 + 0*10 + 0; (board 1, input 1) holds ... + 10 + 1
    np.testing.assert_array_equal(ev.trace("Side2pC")[:, 0], [1000000, 1000100, 1000200])
    np.testing.assert_array_equal(ev.trace("Side2pF")[:, 0], [1000001, 1000101, 1000201])
    np.testing.assert_array_equal(ev.trace("Side2pA")[:, 0], [1000011, 1000111, 1000211])
    assert ev.trace("Side2pC").dtype == np.float64 and ev.trace("Side2pC").shape == (3, N_SAMPLES)


def test_the_readout_is_the_one_given_and_the_events_are_keyed():
    ev = read()
    assert ev.detector.readout.config() is DCRC_RUN76 and ev.detector.readout.segment().n_samples == N_SAMPLES
    assert ev.quantities["series"].to_list() == ["07221203_2025"] * 3
    assert ev.quantities["dump"].to_list() == ["F0001"] * 3
    assert ev.quantities["event"].to_list() == [10000, 10001, 10002]
    assert ev.detector.channel("Side2pA").unit == "board1" and ev.detector.channel("Side2pA").input == "1"
    assert ev.meta["adapter"] == "idx" and ev.meta["dropped_events"] == 0


def test_trigger_types_are_a_quantity_when_the_dump_has_them():
    assert read().quantities["trigger_type"].to_list() == ["Physics", "Unknown", "Physics"]
    assert "trigger_type" not in read(FakeCdms(trigger_types=False)).quantities.fields


def test_roles_are_attached_by_channel_name():
    ev = read(roles={"Side2pC": "phonon"})
    assert ev.detector.channel("Side2pC").role == "phonon" and ev.detector.channel("Side2pF").role is None
    assert ev.detector.channels_with_role("phonon") == ["Side2pC"]


def test_events_missing_a_requested_board_are_dropped_and_counted():
    ev = read(FakeCdms(missing={(10001, 1)}))
    assert ev.quantities["event"].to_list() == [10000, 10002]
    assert ev.meta["dropped_events"] == 1


def test_events_come_in_numeric_order():
    ev = read(FakeCdms(events=(9999, 10001, 10000)))
    assert ev.quantities["event"].to_list() == [9999, 10000, 10001]


def test_no_common_events_and_inconsistent_samples_are_errors():
    with pytest.raises(ValueError, match="no event"):
        read(FakeCdms(boards=(2,)))
    cdms = FakeCdms()
    original = cdms.get_detector_channels

    def uneven(det_id):
        a = original(det_id)
        return a[:, :-1] if det_id.startswith("10001_1") else a

    cdms.get_detector_channels = uneven
    with pytest.raises(ValueError, match="same shape"):
        read(cdms)


def test_a_loaded_object_needs_series_and_dump():
    with pytest.raises(ValueError, match="series= and dump="):
        idx.read(FakeCdms(), detector_name="S104", channels=CHANNELS, config=DCRC_RUN76)


def test_the_series_and_the_dump_come_from_the_folder_name():
    from pathlib import Path
    assert idx._series_and_dump(Path("/x/07221203_2025_F0001")) == ("07221203_2025", "F0001")
    with pytest.raises(ValueError, match="folder name"):
        idx._series_and_dump(Path("/x/dump1"))


class TableCdms(FakeCdms):
    """Like the real `nsdf_dark_matter.idx.CDMS`: every trace of the dump in one array `channels`, and for each detector id the bounds
    `[lo, hi)` of its rows in `detector_to_bounds`."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        rows, self.detector_to_bounds = [], {}
        for det_id in self.ids:
            self.detector_to_bounds[det_id] = [len(rows), len(rows) + 4]
            rows.extend(super().get_detector_channels(det_id))
        self.channels = np.array(rows, dtype=np.int32)          # the real table is uint16; the fake values here exceed 65535

    def get_detector_channels(self, det_id):                   # as the real one: a slice of `channels`
        lo, hi = self.detector_to_bounds[det_id]
        return self.channels[lo:hi]


def test_a_cdms_with_one_table_of_traces_is_gathered_at_once_and_gives_the_same_events():
    from_table, plain = read(TableCdms(missing={(10001, 1)})), read(FakeCdms(missing={(10001, 1)}))
    assert from_table.detector.channel_names() == plain.detector.channel_names()
    for name in CHANNELS:
        np.testing.assert_array_equal(from_table.trace(name), plain.trace(name))
        assert from_table.trace(name).dtype == np.float64
    assert from_table.quantities["event"].to_list() == plain.quantities["event"].to_list() == [10000, 10002]
    calls = []
    cdms = TableCdms()
    original = cdms.get_detector_channels
    cdms.get_detector_channels = lambda d: calls.append(d) or original(d)
    read(cdms)
    assert calls == []                                          # the gather does not ask for the traces one detector at a time


def test_an_input_the_table_does_not_have_is_refused_as_before():
    cdms = TableCdms()
    with pytest.raises(IndexError):
        idx.read(cdms, detector_name="S104", channels={"X": (0, 7)}, config=DCRC_RUN76, series="07221203_2025", dump="F0001")
