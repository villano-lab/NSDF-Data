"""Tests of goldpan.data: the immutable container of one detector's events (the simplest version of the design in
`GoldpanGoldsluice/2026-10-25` and `2026-10-26`)."""
import awkward as ak
import numpy as np
import pytest

from goldpan import quantities as gq
from goldpan.config import PulseConfig, Z7
from goldpan.data import (KEY_COLUMNS, MAIN, ChannelInfo, Detector, Events, Readout, Segment)

N_SAMPLES = 1200
READOUT = PulseConfig(pretrigger_samples=1000, glitch_samples=10, sample_period_s=0.8e-6)     # a 1000-sample window, 0.8 us: what these tests were written for


def detector(config=READOUT, n_samples=N_SAMPLES, name="S104"):
    return Detector(
        name,
        (ChannelInfo("A", role="phonon", unit="DCRC1", input="pA"),
         ChannelInfo("B", role="phonon", unit="DCRC1", input="pB"),
         ChannelInfo("Q", role="charge")),
        Readout.single(n_samples, config),
    )


def traces(n=5, seed=0):
    rng = np.random.default_rng(seed)
    return {c: rng.normal(0, 2.0, (n, N_SAMPLES)) for c in ("A", "B")}


def events(n=5, **kw):
    return Events.from_arrays(detector(), traces(n), series="07221203_2025", dump="F0001", **kw)


# ---- the pieces -----------------------------------------------------------------------------------------------

def test_readout_single_has_the_main_segment_and_its_config():
    r = Readout.single(N_SAMPLES, READOUT)
    assert [s.name for s in r.segments] == [MAIN]
    assert r.config() is READOUT
    assert r.segment().n_samples == N_SAMPLES


def test_time_axis_is_seconds_relative_to_the_trigger():
    r = Readout.single(N_SAMPLES, READOUT)
    t = r.time_axis()
    assert t[0] == pytest.approx(-1000 * 0.8e-6)
    assert t[1000] == pytest.approx(0.0, abs=1e-12)
    assert t[-1] == pytest.approx((N_SAMPLES - 1 - 1000) * 0.8e-6)
    z = Readout.single(N_SAMPLES, Z7).time_axis()
    assert z[0] == pytest.approx(-6250 * 1.6e-6)


def test_time_axis_needs_the_sample_period():
    r = Readout.single(N_SAMPLES, PulseConfig(1000, 10, None))
    with pytest.raises(ValueError, match="time axis"):
        r.time_axis()


def test_readout_rejects_no_segments_duplicates_and_unknown_names():
    with pytest.raises(ValueError):
        Readout(())
    seg = Segment.main(10, READOUT)
    with pytest.raises(ValueError, match="unique"):
        Readout((seg, seg))
    with pytest.raises(KeyError, match="no segment"):
        Readout.single(10, READOUT).segment("fine")


def test_hybrid_readout_has_two_segments_with_their_own_periods():
    coarse = Segment("coarse", 100, PulseConfig(80, 10, 8e-6), -80 * 8e-6)
    fine = Segment("fine", 400, PulseConfig(0, 0, 0.8e-6), 0.0)
    r = Readout((coarse, fine))
    assert r.config("fine").sample_period_s == 0.8e-6
    assert r.time_axis("coarse")[0] == pytest.approx(-80 * 8e-6)
    assert r.time_axis("fine")[1] == pytest.approx(0.8e-6)


def test_detector_channels_and_roles():
    d = detector()
    assert d.channel_names() == ["A", "B", "Q"]
    assert d.channels_with_role("phonon") == ["A", "B"]
    assert d.channel("A").unit == "DCRC1"
    with pytest.raises(KeyError, match="no channel"):
        d.channel("Z")


def test_detector_rejects_duplicate_channel_names():
    with pytest.raises(ValueError, match="unique"):
        Detector("X", (ChannelInfo("A"), ChannelInfo("A")), Readout.single(10, READOUT))


# ---- Events ----------------------------------------------------------------------------------------------------

def test_from_arrays_builds_key_columns_and_read_only_traces():
    ev = events(4)
    assert len(ev) == ev.n_events == 4
    assert ak.fields(ev.quantities)[:3] == list(KEY_COLUMNS)
    assert ev.quantities["series"].to_list() == ["07221203_2025"] * 4
    assert ev.quantities["event"].to_list() == [0, 1, 2, 3]
    assert not ev.trace("A").flags.writeable
    with pytest.raises(ValueError):
        ev.trace("A")[0, 0] = 1.0


def test_traces_and_meta_are_immutable_mappings():
    ev = events(3, meta={"source": "x"})
    with pytest.raises(TypeError):
        ev.traces[("A", MAIN)] = np.zeros((3, N_SAMPLES))
    with pytest.raises(TypeError):
        ev.meta["source"] = "y"
    with pytest.raises(Exception):
        ev.detector = detector(name="other")      # a frozen dataclass


def test_the_functions_of_goldpan_work_on_a_trace_with_the_readout_of_the_detector():
    ev = events(5)
    config = ev.detector.readout.config()
    std = gq.pretrigger_std(ev.trace("A"), config)
    assert std.shape == (5,)
    np.testing.assert_allclose(std, ev.trace("A")[:, 10:1000].std(axis=-1))


def test_events_checks_shapes_keys_channels_and_segments():
    d = detector()
    q = ak.Array({"series": ["s"] * 3, "dump": ["d"] * 3, "event": [0, 1, 2]})
    good = {("A", MAIN): np.zeros((3, N_SAMPLES))}
    Events(d, good, q)
    with pytest.raises(ValueError, match="shape"):
        Events(d, {("A", MAIN): np.zeros((2, N_SAMPLES))}, q)
    with pytest.raises(ValueError, match="shape"):
        Events(d, {("A", MAIN): np.zeros((3, N_SAMPLES + 1))}, q)
    with pytest.raises(ValueError, match="shape"):
        Events(d, {("A", MAIN): np.zeros(3)}, q)
    with pytest.raises(KeyError, match="no channel"):
        Events(d, {("Z", MAIN): np.zeros((3, N_SAMPLES))}, q)
    with pytest.raises(KeyError, match="no segment"):
        Events(d, {("A", "fine"): np.zeros((3, N_SAMPLES))}, q)
    with pytest.raises(ValueError, match="keyed by"):
        Events(d, {"A": np.zeros((3, N_SAMPLES))}, q)
    with pytest.raises(ValueError, match="key fields"):
        Events(d, good, ak.Array({"series": ["s"] * 3, "event": [0, 1, 2]}))


def test_trace_of_a_missing_channel_names_what_there_is():
    with pytest.raises(KeyError, match="have"):
        events(2).trace("Q")


def test_select_by_mask_and_by_positions_keeps_everything_aligned():
    ev = events(6, quantities={"amp": np.arange(6.0)})
    mask = np.array([True, False, True, False, False, True])
    sub = ev.select(mask)
    assert len(sub) == 3
    assert sub.quantities["event"].to_list() == [0, 2, 5]
    assert sub.quantities["amp"].to_list() == [0.0, 2.0, 5.0]
    np.testing.assert_array_equal(sub.trace("A"), ev.trace("A")[[0, 2, 5]])
    by_position = ev.select([5, 1])
    assert by_position.quantities["event"].to_list() == [5, 1]
    assert len(ev) == 6                                  # the original is untouched
    with pytest.raises(ValueError, match="mask"):
        ev.select(np.array([True, False]))


def test_with_quantities_adds_replaces_and_never_touches_the_keys():
    ev = events(4, quantities={"amp": np.arange(4.0)})
    ev2 = ev.with_quantities(amp=np.ones(4), width=np.arange(4) * 2)
    assert ev2.quantities["amp"].to_list() == [1.0] * 4
    assert ev2.quantities["width"].to_list() == [0, 2, 4, 6]
    assert ev.quantities["amp"].to_list() == [0.0, 1.0, 2.0, 3.0]    # the original is untouched
    with pytest.raises(ValueError, match="identifies"):
        ev.with_quantities(event=np.arange(4))
    with pytest.raises(ValueError, match="entries"):
        ev.with_quantities(amp=np.ones(3))


def test_a_quantity_can_be_a_variable_length_list_per_event():
    ev = events(3).with_quantities(pulse_times=[[1.0, 2.0], [], [3.0]])
    assert ev.quantities["pulse_times"].to_list() == [[1.0, 2.0], [], [3.0]]
    assert ak.num(ev.quantities["pulse_times"]).to_list() == [2, 0, 1]
    assert len(ev.select([2, 0]).quantities["pulse_times"].to_list()) == 2


def test_concatenate_joins_events_of_one_detector():
    a, b = events(3, quantities={"amp": [1.0, 2.0, 3.0]}), events(2, quantities={"amp": [4.0, 5.0]}, event=[10, 11])
    c = Events.concatenate(a, b)
    assert len(c) == 5
    assert c.quantities["event"].to_list() == [0, 1, 2, 10, 11]
    assert c.quantities["amp"].to_list() == [1.0, 2.0, 3.0, 4.0, 5.0]
    np.testing.assert_array_equal(c.trace("B")[3:], b.trace("B"))


def test_concatenate_refuses_different_detectors_traces_or_quantities():
    a = events(2, quantities={"amp": [1.0, 2.0]})
    other_detector = Events.from_arrays(detector(Z7), traces(2), quantities={"amp": [1.0, 2.0]})
    with pytest.raises(ValueError, match="different detectors"):
        Events.concatenate(a, other_detector)
    with pytest.raises(ValueError, match="quantities"):
        Events.concatenate(a, events(2))
    only_a = Events.from_arrays(detector(), {"A": traces(2)["A"]}, quantities={"amp": [1.0, 2.0]})
    with pytest.raises(ValueError, match="traces"):
        Events.concatenate(a, only_a)
    with pytest.raises(ValueError):
        Events.concatenate()


def test_a_time_column_and_the_detector_time_axis():
    ev = events(3, quantities={"t_trigger": [10.0, 10.5, 11.0]}, meta={"clock": "daq"})
    assert ev.quantities["t_trigger"].to_list() == [10.0, 10.5, 11.0]
    assert ev.meta["clock"] == "daq"
    assert ev.time_axis()[0] == pytest.approx(-1000 * 0.8e-6)


def test_from_arrays_refuses_a_key_in_quantities_and_empty_traces():
    with pytest.raises(ValueError, match="key field"):
        Events.from_arrays(detector(), traces(2), quantities={"event": [0, 1]})
    with pytest.raises(ValueError, match="empty"):
        Events.from_arrays(detector(), {})


def test_repr_is_short_and_says_what_it_holds():
    text = repr(events(2))
    assert "n_events=2" in text and "S104" in text and len(text) < 300
