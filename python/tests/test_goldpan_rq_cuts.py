"""Tests of goldpan.rq_cuts (RQ-only selections), ported from the tests of scdms-analysis-tools."""
import numpy as np
import pytest

from goldpan.rq_cuts import (
    MAX_RQ_UA_TO_A,
    Z7_PHONON_CHANNELS,
    calibration_line,
    channel_max_amps,
    excursion_band_rq,
    excursion_ratio_rq,
    log_excursion_ratio_rq,
    loose_randoms,
    phonon_log_ratios,
    pileup_randoms,
    pt_std_proxy,
    tight_randoms,
    triggered_physics,
)

# toy thresholds and ranges, deliberately not real values: the functions must work for any analysis's parameters
THRESHOLDS = {"PAS1": 2.0, "PBS1": 2.0}
TIGHT_RANGES = {"PAS1": (0.0, 1.0), "PBS1": (0.0, 1.0)}


def test_max_is_converted_from_microamps_to_amps():
    assert channel_max_amps(1.0) == pytest.approx(MAX_RQ_UA_TO_A)
    np.testing.assert_allclose(channel_max_amps(np.array([1e6, 2e6])), [1.0, 2.0])


def test_excursion_ratio_and_its_log():
    amp, std = np.array([1.0, -10.0]), np.array([1.0, 1.0])
    np.testing.assert_allclose(excursion_ratio_rq(amp, std), [1.0, 10.0])
    np.testing.assert_allclose(log_excursion_ratio_rq(amp, std), [0.0, 1.0])


def test_pt_std_proxy_adds_variances_and_takes_a_mapping_a_subset_or_a_list():
    assert pt_std_proxy({"A": np.array([3.0]), "B": np.array([4.0])}) == pytest.approx(5.0)
    assert pt_std_proxy({"A": np.array([3.0]), "B": np.array([4.0]), "C": np.array([99.0])}, channels=["A", "B"]) == pytest.approx(5.0)
    assert pt_std_proxy([np.array([3.0]), np.array([4.0])]) == pytest.approx(5.0)


def test_excursion_band_is_half_open():
    np.testing.assert_array_equal(excursion_band_rq(np.array([0.0, 0.5, 1.0, 1.5]), 0.5, 1.5), [False, True, True, False])


def test_phonon_log_ratios_uses_the_channels_given_that_have_both_rqs():
    rqs = {"PAS1max": np.array([1e6]), "PAS1std": np.array([1.0]),
           "PBS1max": np.array([1e7]), "PBS1std": np.array([1.0]),
           "PCS1max": np.array([1e6])}                               # no PCS1std
    out = phonon_log_ratios(rqs, Z7_PHONON_CHANNELS)
    assert set(out) == {"PAS1", "PBS1"}
    np.testing.assert_allclose(out["PAS1"], [0.0])
    np.testing.assert_allclose(out["PBS1"], [1.0])
    assert set(phonon_log_ratios(rqs, ["PAS1"])) == {"PAS1"}


def test_phonon_log_ratios_does_not_raise_on_a_zero_std():
    out = phonon_log_ratios({"PAS1max": np.array([1e6]), "PAS1std": np.array([0.0])}, ["PAS1"])
    assert np.isinf(out["PAS1"][0])


def test_z7_has_twelve_distinct_phonon_channels():
    assert len(Z7_PHONON_CHANNELS) == len(set(Z7_PHONON_CHANNELS)) == 12


def test_pileup_randoms_flags_any_channel_over_its_threshold():
    ratios = {"PAS1": np.array([0.0, 3.0, np.nan]), "PBS1": np.array([3.0, 0.0, 0.0])}
    np.testing.assert_array_equal(pileup_randoms(ratios, THRESHOLDS), [True, True, False])


def test_pileup_randoms_ignores_channels_without_a_threshold():
    assert pileup_randoms({"PAS1": np.array([3.0]), "PFS2": np.array([999.0])}, THRESHOLDS)[0]
    assert not pileup_randoms({"PFS2": np.array([999.0])}, THRESHOLDS)[0]


def test_loose_randoms_needs_every_channel_above_low_and_no_pileup():
    ratios = {"PAS1": np.array([0.5, 0.5, 3.0]), "PBS1": np.array([0.5, -1.0, 0.5])}
    np.testing.assert_array_equal(loose_randoms(ratios, 0.4, THRESHOLDS), [True, False, False])


def test_tight_randoms_is_a_subset_of_loose_randoms():
    rng = np.random.default_rng(0)
    ratios = {ch: rng.normal(0.5, 1.0, 500) for ch in ["PAS1", "PBS1"]}
    loose = loose_randoms(ratios, 0.4, THRESHOLDS)
    tight = tight_randoms(ratios, 0.4, THRESHOLDS, TIGHT_RANGES)
    assert np.all(~tight | loose) and tight.sum() < loose.sum()


def test_a_channel_with_a_range_but_no_data_is_skipped_not_failed():
    ratios = {"PAS1": np.array([0.5]), "PBS1": np.array([0.5])}
    assert tight_randoms(ratios, 0.4, THRESHOLDS, {**TIGHT_RANGES, "PFS2": (0.0, 1.0)})[0]


def test_a_nan_for_one_event_is_skipped_for_that_event_only():
    ratios = {"PAS1": np.array([np.nan, 0.5]), "PBS1": np.array([0.5, 0.5])}
    np.testing.assert_array_equal(tight_randoms(ratios, 0.4, THRESHOLDS, TIGHT_RANGES), [True, True])


# ---- the calibration line (from line_cuts) -------------------------------------------------------------------------------

def line_rqs():
    return {"series": np.array(["s1", "s1", "s1", "s1", "s2"]),
            "EventType": np.array([1, 1, 2, 1, 1]), "TriggerDetectorNum": np.array([7, 7, 7, 3, 7]),
            "PTOFamps": np.array([10.0, 10.0, 10.0, 10.0, 10.0]), "PTOFdelay": np.array([0.0, 5.0, 0.0, 0.0, 0.0])}


WINDOWS = {"s1": dict(amp=(9.0, 11.0), delay=[(-1.0, 1.0)]), "s2": dict(amp=(20.0, 30.0), delay=[(-1.0, 1.0)])}


def test_triggered_physics_needs_the_event_type_and_the_trigger_detector():
    np.testing.assert_array_equal(triggered_physics(line_rqs(), 7), [True, True, False, False, True])
    np.testing.assert_array_equal(triggered_physics(line_rqs(), 3), [False, False, False, True, False])


def test_calibration_line_applies_each_series_window_and_the_trigger():
    # event 1: delay out of window; 2: not physics; 3: other detector; 4: amplitude outside series s2's window
    np.testing.assert_array_equal(calibration_line(line_rqs(), WINDOWS, detector=7), [True, False, False, False, False])


def test_calibration_line_names_a_series_without_a_window():
    with pytest.raises(ValueError, match="s2 \\(1 events\\)"):
        calibration_line(line_rqs(), {"s1": WINDOWS["s1"]}, detector=7)
    out = calibration_line(line_rqs(), {"s1": WINDOWS["s1"]}, detector=7, allow_missing=True)
    np.testing.assert_array_equal(out, [True, False, False, False, False])
