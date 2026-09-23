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


def test_excursion_band_bounds():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(1)
    pulses = rng.normal(size=(20, 25))

    ratio = q.excursion_ratio(pulses, config)
    lo, hi = np.percentile(ratio, [25, 75])

    mask = cuts.excursion_band(pulses, config, low=lo, high=hi)
    expected = (ratio >= lo) & (ratio < hi)
    np.testing.assert_array_equal(mask, expected)


def test_excursion_band_precomputed_ratio_matches_recomputed():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(5)
    pulses = rng.normal(size=(10, 25))
    ratio = q.excursion_ratio(pulses, config)

    from_precomputed = cuts.excursion_band(pulses, config, low=2, high=5, ratio=ratio)
    from_scratch = cuts.excursion_band(pulses, config, low=2, high=5)
    np.testing.assert_array_equal(from_precomputed, from_scratch)


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
