import numpy as np

import pulse_quantities as q
from pulse_config import PulseConfig


def test_pretrigger_mean_std_match_manual_slice():
    config = PulseConfig(pretrigger_samples=20, glitch_samples=3, sample_period_s=None)
    rng = np.random.default_rng(0)
    pulses = rng.normal(loc=5.0, scale=2.0, size=(6, 60))

    expected_mean = pulses[:, 3:20].mean(axis=-1)
    expected_std = pulses[:, 3:20].std(axis=-1)

    np.testing.assert_allclose(q.pretrigger_mean(pulses, config), expected_mean)
    np.testing.assert_allclose(q.pretrigger_std(pulses, config), expected_std)


def test_bstd_defaults_to_500_samples_and_bstd_1000_to_1000():
    config = PulseConfig(pretrigger_samples=2000, glitch_samples=10, sample_period_s=None)
    rng = np.random.default_rng(10)
    pulses = rng.normal(loc=5.0, scale=2.0, size=(4, 1500))
    pulses[:, 700:] *= 3.0   # baseline scatter differs between the 500- and 1000-sample windows

    np.testing.assert_allclose(q.bstd(pulses, config), pulses[:, 10:500].std(axis=-1))
    np.testing.assert_allclose(q.bstd_1000(pulses, config), pulses[:, 10:1000].std(axis=-1))
    assert not np.allclose(q.bstd(pulses, config), q.bstd_1000(pulses, config))


def test_bstd_ignores_pretrigger_samples_and_honors_glitch_samples_and_n_samples():
    rng = np.random.default_rng(11)
    pulses = rng.normal(size=(3, 1200))
    a = PulseConfig(pretrigger_samples=100, glitch_samples=10, sample_period_s=None)
    b = PulseConfig(pretrigger_samples=1100, glitch_samples=10, sample_period_s=None)
    np.testing.assert_array_equal(q.bstd(pulses, a), q.bstd(pulses, b))   # window is not config.pretrigger_samples

    pulses[:, :5] = 1000.0   # leading glitch
    skip = PulseConfig(glitch_samples=10, sample_period_s=None)
    keep = PulseConfig(glitch_samples=0, sample_period_s=None)
    assert np.all(q.bstd(pulses, skip) < 2.0)          # glitch skipped: ordinary noise scatter
    assert np.all(q.bstd(pulses, keep) > 50.0)         # glitch kept: scatter is huge
    np.testing.assert_allclose(q.bstd(pulses, skip, n_samples=300), pulses[:, 10:300].std(axis=-1))


def test_bstd_matches_pretrigger_std_when_the_window_matches():
    rng = np.random.default_rng(12)
    pulses = rng.normal(size=(5, 1500))
    c500 = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=None)
    c1000 = PulseConfig(pretrigger_samples=1000, glitch_samples=10, sample_period_s=None)
    np.testing.assert_allclose(q.bstd(pulses, c500), q.pretrigger_std(pulses, c500))
    np.testing.assert_allclose(q.bstd_1000(pulses, c1000), q.pretrigger_std(pulses, c1000))


def test_bline_defaults_to_500_samples_and_bline_1000_to_1000():
    config = PulseConfig(pretrigger_samples=2000, glitch_samples=10, sample_period_s=None)
    rng = np.random.default_rng(13)
    pulses = rng.normal(loc=5.0, scale=2.0, size=(4, 1500))
    pulses[:, 700:] += 20.0   # baseline level differs between the 500- and 1000-sample windows

    np.testing.assert_allclose(q.bline(pulses, config), pulses[:, 10:500].mean(axis=-1))
    np.testing.assert_allclose(q.bline_1000(pulses, config), pulses[:, 10:1000].mean(axis=-1))
    assert not np.allclose(q.bline(pulses, config), q.bline_1000(pulses, config))


def test_bline_ignores_pretrigger_samples_and_honors_glitch_samples_and_n_samples():
    rng = np.random.default_rng(14)
    pulses = rng.normal(size=(3, 1200))
    a = PulseConfig(pretrigger_samples=100, glitch_samples=10, sample_period_s=None)
    b = PulseConfig(pretrigger_samples=1100, glitch_samples=10, sample_period_s=None)
    np.testing.assert_array_equal(q.bline(pulses, a), q.bline(pulses, b))   # window is not config.pretrigger_samples

    pulses[:, :5] = 1000.0   # leading glitch
    skip = PulseConfig(glitch_samples=10, sample_period_s=None)
    keep = PulseConfig(glitch_samples=0, sample_period_s=None)
    assert np.all(np.abs(q.bline(pulses, skip)) < 1.0)   # glitch skipped: baseline near zero
    assert np.all(q.bline(pulses, keep) > 5.0)           # glitch kept: 5 samples of 1000 in 500 -> +10
    np.testing.assert_allclose(q.bline(pulses, skip, n_samples=300), pulses[:, 10:300].mean(axis=-1))


def test_bline_matches_pretrigger_mean_when_the_window_matches_and_does_not_mutate_config():
    rng = np.random.default_rng(15)
    pulses = rng.normal(loc=3.0, size=(5, 1500))
    c500 = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=None)
    c1000 = PulseConfig(pretrigger_samples=1000, glitch_samples=10, sample_period_s=None)
    np.testing.assert_allclose(q.bline(pulses, c500), q.pretrigger_mean(pulses, c500))
    np.testing.assert_allclose(q.bline_1000(pulses, c1000), q.pretrigger_mean(pulses, c1000))
    assert c500.pretrigger_samples == 500 and c1000.pretrigger_samples == 1000   # frozen config left as it was


def test_single_pulse_matches_corresponding_batch_row():
    config = PulseConfig(pretrigger_samples=20, glitch_samples=3, sample_period_s=None)
    rng = np.random.default_rng(1)
    pulses = rng.normal(size=(4, 60))

    batch_result = q.pretrigger_mean(pulses, config)
    for i in range(pulses.shape[0]):
        assert np.isclose(q.pretrigger_mean(pulses[i], config), batch_result[i])


def test_max_deviation_known_spike():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulse = np.zeros(30)
    pulse[15] = 100.0  # spike well after the pretrigger window

    assert q.max_deviation(pulse, config) == 100.0  # bmean == 0


def test_max_deviation_reflects_pretrigger_contamination_not_just_the_real_pulse():
    """A spike confined to the pretrigger window doesn't get excluded from `dev`
    by construction -- it drags `bmean` off, so it inflates `dev` indirectly by
    making every *flat* post-trigger sample look far from that skewed baseline.
    This is exactly the contamination pathology found in
    07221203_2025_dump1_noise.ipynb, reproduced here as a regression check
    rather than something this function is expected to "fix"."""
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulse = np.zeros(30)
    pulse[3] = 1000.0   # inside pretrigger -- drags bmean far from the real baseline
    pulse[20] = 5.0      # the actual post-pretrigger signal

    bmean = pulse[:10].mean()  # 100.0
    # every flat post-trigger zero is |0 - 100| = 100 from bmean, which exceeds
    # the real signal's |5 - 100| = 95 -- so contamination, not the real pulse,
    # sets `dev` here.
    assert q.max_deviation(pulse, config) == abs(0.0 - bmean)


def test_excursion_ratio_matches_dev_over_std():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(2)
    pulses = rng.normal(size=(5, 40))

    expected = q.max_deviation(pulses, config) / q.pretrigger_std(pulses, config)
    np.testing.assert_allclose(q.excursion_ratio(pulses, config), expected)


def test_log_excursion_ratio_matches_log10_of_ratio():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(9)
    pulses = rng.normal(size=(5, 40))

    expected = np.log10(q.excursion_ratio(pulses, config))
    np.testing.assert_allclose(q.log_excursion_ratio(pulses, config), expected)


def test_excursion_duration_counts_samples_above_half_max():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulses = np.zeros((2, 30))
    pulses[0, 15] = 10.0        # dev=10, half-max=5 -- only 1 sample at/above it
    pulses[1, 15:25] = 10.0     # 10 samples at/above half-max

    np.testing.assert_array_equal(
        q.excursion_duration(pulses, config, fraction=0.5), [1, 10]
    )


def test_rise_sample_half_max_crossing():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulse = np.zeros(30)
    pulse[10:15] = 5.0   # below half-max
    pulse[15:] = 20.0    # full amplitude (dev = 20, half-max = 10)

    assert q.rise_sample(pulse, config, fraction=0.5) == 15


def test_rise_sample_batch_shape():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    pulses = np.zeros((3, 30))
    pulses[0, 12:] = 10.0
    pulses[1, 20:] = 10.0
    pulses[2, 29:] = 10.0

    rs = q.rise_sample(pulses, config, fraction=0.5)
    np.testing.assert_array_equal(rs, [12, 20, 29])


def test_power_spectrum_matches_manual_fft():
    config = PulseConfig(sample_period_s=1.0)
    rng = np.random.default_rng(3)
    pulses = rng.normal(size=(3, 16))

    spec = np.fft.rfft(pulses, axis=-1)
    expected = (spec * np.conj(spec)).real
    np.testing.assert_allclose(q.power_spectrum(pulses, config), expected)


def test_power_spectrum_is_real_nonnegative():
    config = PulseConfig(sample_period_s=1.0)
    rng = np.random.default_rng(4)
    pulses = rng.normal(size=(5, 32))

    ps = q.power_spectrum(pulses, config)
    assert np.all(ps >= -1e-9)  # nonnegative up to float noise


def test_frequencies_hz_matches_rfftfreq():
    config = PulseConfig(sample_period_s=2.0)
    np.testing.assert_allclose(q.frequencies_hz(10, config), np.fft.rfftfreq(10, d=2.0))


def test_sample_rate_hz_raises_without_sample_period():
    config = PulseConfig(sample_period_s=None)
    try:
        _ = config.sample_rate_hz
        assert False, "expected ValueError"
    except ValueError:
        pass
