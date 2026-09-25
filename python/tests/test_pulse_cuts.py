import numpy as np

import pulse_cuts as cuts
import pulse_quantities as q
from pulse_config import PulseConfig


def test_dead_channel_flags_zero_std():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    pulses = np.array([
        [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],   # constant pretrigger -> std 0 -> dead
        [1, 2, 1, 2, 1, 5, 5, 5, 5, 5],   # varying pretrigger -> not dead
    ], dtype=float)

    np.testing.assert_array_equal(cuts.dead_channel(pulses, config), [True, False])
    np.testing.assert_array_equal(cuts.active(pulses, config), [False, True])


def test_quiet_baseline_excludes_dead_and_high_std():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(0)
    quiet = rng.normal(scale=0.1, size=(3, 5))
    noisy = rng.normal(scale=100.0, size=(3, 5))
    dead = np.zeros((2, 5))
    pretrig = np.vstack([quiet, noisy, dead])
    post = rng.normal(size=(8, 10))
    pulses = np.hstack([pretrig, post])

    mask = cuts.quiet_baseline(pulses, config, percentile=50)
    assert mask[:3].all(), "quiet traces should be kept"
    assert not mask[3:6].any(), "noisy traces should be excluded"
    assert not mask[6:8].any(), "dead traces should never be included"


def test_quiet_baseline_all_dead_returns_all_false():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    pulses = np.zeros((4, 15))
    mask = cuts.quiet_baseline(pulses, config)
    np.testing.assert_array_equal(mask, [False, False, False, False])


def test_ratio_band_bounds():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(1)
    pulses = rng.normal(size=(20, 25))

    ratio = q.excursion_ratio(pulses, config)
    lo, hi = np.percentile(ratio, [25, 75])

    mask = cuts.ratio_band(pulses, config, low=lo, high=hi)
    expected = (ratio >= lo) & (ratio < hi)
    np.testing.assert_array_equal(mask, expected)


def test_ratio_band_precomputed_ratio_matches_recomputed():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(5)
    pulses = rng.normal(size=(10, 25))
    ratio = q.excursion_ratio(pulses, config)

    from_precomputed = cuts.ratio_band(pulses, config, low=2, high=5, ratio=ratio)
    from_scratch = cuts.ratio_band(pulses, config, low=2, high=5)
    np.testing.assert_array_equal(from_precomputed, from_scratch)


def test_excursion_band_default_matches_tightened_log_ratio_cut():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(6)
    pulses = rng.normal(size=(30, 25))

    log_ratio = q.log_excursion_ratio(pulses, config)
    expected = (log_ratio >= 0.5) & (log_ratio < 0.7)
    np.testing.assert_array_equal(cuts.excursion_band(pulses, config), expected)


def test_excursion_band_loose_matches_wider_log_ratio_cut():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(7)
    pulses = rng.normal(size=(30, 25))

    log_ratio = q.log_excursion_ratio(pulses, config)
    expected = (log_ratio >= 0.5) & (log_ratio < 1.0)
    np.testing.assert_array_equal(cuts.excursion_band_loose(pulses, config), expected)


def test_looks_like_pulse_flags_sustained_excursion_not_single_spike():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulses = np.zeros((2, 30))
    pulses[0, 15] = 10.0          # single-sample noise spike
    pulses[1, 15:25] = 10.0       # sustained plateau, like a real pulse's decay

    np.testing.assert_array_equal(
        cuts.looks_like_pulse(pulses, config, min_duration=3), [False, True]
    )


def test_excursion_band_AI_removes_pulse_like_traces_from_the_band():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(8)
    pretrig = rng.normal(scale=1.0, size=(2, 10))
    pulses = np.hstack([pretrig, np.zeros((2, 20))])
    pulses[0, 15] = 5.0        # brief spike -> noise-like
    pulses[1, 15:25] = 5.0     # sustained -> pulse-like

    band = cuts.excursion_band(pulses, config, low=-10, high=10)
    assert band.all(), "both traces should land in a wide-open band"

    ai = cuts.excursion_band_AI(pulses, config, low=-10, high=10, min_duration=3)
    np.testing.assert_array_equal(ai, [True, False])


def test_excursion_below_percentile():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(2)
    pulses = rng.normal(size=(30, 25))

    ratio = q.excursion_ratio(pulses, config)
    thresh = np.percentile(ratio, 30)
    expected = ratio < thresh

    np.testing.assert_array_equal(
        cuts.excursion_below_percentile(pulses, config, percentile=30), expected
    )


def test_randoms_and_real_triggers_split_on_the_trigger_label():
    triggers = np.array(["Physics", "Unknown", "Physics", "Unknown", "Other"])

    np.testing.assert_array_equal(cuts.randoms(triggers), [True, False, True, False, False])
    np.testing.assert_array_equal(cuts.real_triggers(triggers), [False, True, False, True, False])
    # "Other" is in neither, so the two cuts are not complements
    assert not np.any(cuts.randoms(triggers) & cuts.real_triggers(triggers))


def test_randoms_label_can_be_overridden_and_accepts_a_list():
    np.testing.assert_array_equal(cuts.randoms(["a", "b"], label="b"), [False, True])
    np.testing.assert_array_equal(cuts.real_triggers(["a", "b"], label="a"), [True, False])
