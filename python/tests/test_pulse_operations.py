import numpy as np

import pulse_operations as op
from pulse_config import PulseConfig


def test_baseline_subtract_zeros_pretrigger_mean():
    config = PulseConfig(pretrigger_samples=10, glitch_samples=0, sample_period_s=None)
    rng = np.random.default_rng(0)
    pulses = rng.normal(loc=50.0, size=(4, 30))

    subtracted = op.baseline_subtract(pulses, config)
    np.testing.assert_allclose(subtracted[:, :10].mean(axis=-1), 0.0, atol=1e-10)


def test_baseline_subtract_does_not_mutate_input():
    config = PulseConfig(pretrigger_samples=5, glitch_samples=0, sample_period_s=None)
    pulses = np.full((2, 20), 5.0)
    original = pulses.copy()

    op.baseline_subtract(pulses, config)
    np.testing.assert_array_equal(pulses, original)


def test_trim_glitch_drops_leading_samples():
    config = PulseConfig(glitch_samples=4, sample_period_s=None)
    pulses = np.arange(20).reshape(2, 10)

    trimmed = op.trim_glitch(pulses, config)
    assert trimmed.shape == (2, 6)
    np.testing.assert_array_equal(trimmed[0], pulses[0, 4:])


def test_clip():
    data = np.array([-5, 0, 5, 10])
    np.testing.assert_array_equal(op.clip(data, low=0, high=8), [0, 0, 5, 8])
