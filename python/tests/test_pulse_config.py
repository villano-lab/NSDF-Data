import warnings

import numpy as np
import pytest

import pulse_archive as archive
import pulse_quantities as q
from pulse_config import DEFAULT_CONFIG, PHONON_SAMPLE_PERIOD_S, PulseConfig


def test_default_sample_period_is_0p8_us():
    assert PHONON_SAMPLE_PERIOD_S == 0.8e-6
    assert DEFAULT_CONFIG.sample_period_s == 0.8e-6
    assert PulseConfig().sample_period_s == 0.8e-6
    assert DEFAULT_CONFIG.sample_rate_hz == pytest.approx(1.25e6)


def test_a_4096_sample_trace_is_3p2768_ms_and_nyquist_is_625_khz():
    config = PulseConfig()
    freqs = q.frequencies_hz(4096, config)
    assert 4096 * config.sample_period_s == pytest.approx(3.2768e-3)
    assert freqs[-1] == pytest.approx(625e3)


def test_the_retired_period_warns_with_the_reason():
    with pytest.warns(UserWarning, match="1.6 us.*wrong.*0.8 us"):
        PulseConfig(pretrigger_samples=500, sample_period_s=1.6e-6)


def test_other_periods_do_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        PulseConfig(sample_period_s=0.8e-6)
        PulseConfig(sample_period_s=2e-6)
        PulseConfig(sample_period_s=None)
        PulseConfig()


def test_loading_an_archive_made_with_the_retired_period_warns(tmp_path):
    path = tmp_path / "old.h5"
    with pytest.warns(UserWarning, match="PulseConfig"):
        old = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=1.6e-6)
    archive.save_good_events(path, series="s", detector=0, channel=0, detector_ids=["1_0_Phonon_4096"],
                             cut_name="c", config=old)
    with pytest.warns(UserWarning, match="archive.*1.6 us"):
        result = archive.load_good_events(path, "s", 0, 0)
    assert result["sample_period_s"] == 1.6e-6


def test_loading_an_archive_made_with_the_right_period_does_not_warn(tmp_path):
    path = tmp_path / "new.h5"
    new = PulseConfig(pretrigger_samples=500, glitch_samples=10)
    archive.save_good_events(path, series="s", detector=0, channel=0, detector_ids=["1_0_Phonon_4096"],
                             cut_name="c", config=new)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = archive.load_good_events(path, "s", 0, 0)
    assert np.isclose(result["sample_period_s"], 0.8e-6)
