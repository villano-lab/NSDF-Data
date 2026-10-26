"""Tests of goldpan.algorithms (filters and per-trace quantities), ported from the tests of scdms-analysis-tools."""
import numpy as np
import pytest

from goldpan.algorithms import (compute, downsample, downsampled_config, integral, lowpass, max_time, pulse_max, rise_time)
from goldpan.config import PulseConfig
from goldpan.data import ChannelInfo, Detector, Events, Readout

CONFIG = PulseConfig(pretrigger_samples=100, glitch_samples=0, sample_period_s=1.6e-6)
N = 160


def ramp_trace(top=10.0, start=100, n_ramp=10, n=N):
    """Flat zero, then a linear ramp from 0 to `top` over `n_ramp` samples, then back to zero."""
    t = np.zeros(n)
    t[start:start + n_ramp + 1] = np.linspace(0, top, n_ramp + 1)
    return t


def test_downsample_averages_blocks_and_drops_the_tail():
    out = downsample(np.array([1.0, 3.0, 5.0, 7.0, 9.0]), 2)
    np.testing.assert_allclose(out, [2.0, 6.0])
    assert downsample(np.ones((3, 8)), 4).shape == (3, 2)


def test_downsampled_config_scales_the_period_and_the_counts():
    c = downsampled_config(CONFIG, 4)
    assert c.sample_period_s == pytest.approx(6.4e-6) and c.pretrigger_samples == 25
    assert downsampled_config(PulseConfig(8, 0, None), 2).sample_period_s is None


def test_lowpass_keeps_a_constant_and_a_slow_signal_and_kills_a_fast_one():
    t = np.arange(2000) * CONFIG.sample_period_s
    assert np.allclose(lowpass(np.full(300, 3.0), 50e3, CONFIG), 3.0, atol=1e-6)
    slow, fast = np.sin(2 * np.pi * 5e3 * t), np.sin(2 * np.pi * 200e3 * t)
    mid = slice(300, 1700)
    assert np.allclose(lowpass(slow, 50e3, CONFIG)[mid], slow[mid], atol=2e-3)
    assert np.abs(lowpass(fast, 50e3, CONFIG)[mid]).max() < 1e-3


def test_lowpass_is_zero_phase_and_works_on_a_stack():
    t = np.zeros((2, 600))
    t[:, 300] = 1.0
    out = lowpass(t, 50e3, CONFIG)
    assert out.shape == t.shape and np.all(out.argmax(axis=-1) == 300)
    np.testing.assert_allclose(out[..., 300 - 20:300], out[..., 300 + 20:300:-1], atol=1e-12)     # symmetric: no shift


def test_lowpass_agrees_with_scipy_away_from_the_edges():
    signal = pytest.importorskip("scipy.signal")
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.normal(size=1500))
    sos = signal.butter(4, 50e3, btype="low", fs=CONFIG.sample_rate_hz, output="sos")
    ref = signal.sosfiltfilt(sos, x)
    mine = lowpass(x, 50e3, CONFIG)
    mid = slice(300, 1200)
    assert np.abs(mine[mid] - ref[mid]).max() < 0.02 * np.ptp(ref)


def test_pulse_max_is_above_the_pretrigger_mean():
    t = ramp_trace() + 2.0
    assert pulse_max(t, CONFIG) == pytest.approx(10.0)
    assert pulse_max(np.stack([t, 2 * t]), CONFIG) == pytest.approx([10.0, 20.0])


def test_max_time_is_from_the_start_of_the_trace():
    assert max_time(ramp_trace(), CONFIG) == pytest.approx(110 * CONFIG.sample_period_s)


def test_integral_of_a_baseline_trace_is_zero_and_of_a_spike_is_its_area():
    assert integral(np.full(N, 1.0), CONFIG) == pytest.approx(0.0, abs=1e-18)
    spike = np.zeros(N)
    spike[120] = 4.0
    assert integral(spike, CONFIG) == pytest.approx(4.0 * CONFIG.sample_period_s)


def test_rise_time_of_a_clean_ramp():
    # 10 to 90 % of a 10-sample ramp is 8 samples
    assert rise_time(ramp_trace(), CONFIG) == pytest.approx(8 * CONFIG.sample_period_s)


def test_rise_time_is_nan_without_a_positive_pulse_and_works_on_a_stack():
    flat_negative = np.full(N, -5.0)
    out = rise_time(np.stack([ramp_trace(), flat_negative]), CONFIG)
    assert out[0] == pytest.approx(8 * CONFIG.sample_period_s) and np.isnan(out[1])


def test_compute_adds_a_record_per_channel_to_an_events():
    detector = Detector("S", (ChannelInfo("A"), ChannelInfo("B")), Readout.single(N, CONFIG))
    traces = {"A": np.stack([ramp_trace(10.0), ramp_trace(20.0)]), "B": np.stack([ramp_trace(1.0), ramp_trace(2.0)])}
    ev = Events.from_arrays(detector, traces, series="x", dump="F1")
    out = compute(ev, {"max": pulse_max, "tmax": max_time}, channels=["A", "B"])
    assert out.quantities["A"]["max"].to_list() == pytest.approx([10.0, 20.0])
    assert out.quantities["B"]["max"].to_list() == pytest.approx([1.0, 2.0])
    assert out.quantities["A"]["tmax"].to_list() == pytest.approx([110 * 1.6e-6] * 2)
    assert "A" not in ev.quantities.fields                                   # the original is unchanged
