"""Tests of the `goldpan` package layout (phase 2 of issue 71): the readout has no defaults in the package, and the old
flat names are aliases of the package modules with the Run 76 readout as the default config."""
import inspect
import warnings

import numpy as np
import pytest

import pulse_config as flat_config
import pulse_cuts as flat_cuts
import pulse_io as flat_io
import pulse_operations as flat_operations
import pulse_quantities as flat_quantities
import pulse_status as flat_status
from goldpan import config as gc
from goldpan import cuts as gcuts
from goldpan import operations as gop
from goldpan import quantities as gq
from goldpan import status as gstatus


def pulses(n=6, length=2000, seed=0):
    rng = np.random.default_rng(seed)
    out = rng.normal(0, 2.0, (n, length))
    out[::2, 1200:1300] += 80.0
    return out


# ---- the package has no readout defaults -------------------------------------------------------------------------

def test_pulse_config_has_no_defaults():
    with pytest.raises(TypeError):
        gc.PulseConfig()
    with pytest.raises(TypeError):
        gc.PulseConfig(pretrigger_samples=1000)
    assert gc.PulseConfig(1000, 10, None).sample_period_s is None


def test_presets_name_their_readouts():
    assert (gc.DCRC_RUN76.pretrigger_samples, gc.DCRC_RUN76.sample_period_s) == (1000, 0.8e-6)
    assert (gc.Z7.pretrigger_samples, gc.Z7.sample_period_s) == (6250, 1.6e-6)
    assert gc.DCRC_RUN76.sample_rate_hz == pytest.approx(1.25e6)
    assert gc.Z7.sample_rate_hz == pytest.approx(625e3)


def test_package_config_does_not_warn_about_1_6_us_which_is_right_for_z7():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        gc.PulseConfig(6250, 10, 1.6e-6)


def test_unknown_sample_period_raises_instead_of_assuming():
    with pytest.raises(ValueError):
        gc.PulseConfig(1000, 10, None).sample_rate_hz


def test_package_functions_require_a_config():
    p = pulses()
    with pytest.raises(TypeError):
        gq.pretrigger_mean(p)
    with pytest.raises(TypeError):
        gcuts.dead_channel(p)
    with pytest.raises(TypeError):
        gop.baseline_subtract(p)
    with pytest.raises(TypeError):
        gq.frequencies_hz(100)


def test_the_readout_changes_the_numbers_it_should():
    p = pulses()
    np.testing.assert_allclose(gq.pretrigger_mean(p, gc.DCRC_RUN76), p[:, 10:1000].mean(axis=-1))
    np.testing.assert_allclose(gq.pretrigger_mean(p, gc.Z7), p[:, 10:2000].mean(axis=-1))   # the trace is shorter than 6250
    f_run76 = gq.frequencies_hz(100, gc.DCRC_RUN76)
    f_z7 = gq.frequencies_hz(100, gc.Z7)
    np.testing.assert_allclose(f_run76, 2 * f_z7)


# ---- the flat names are aliases ---------------------------------------------------------------------------------

def test_flat_functions_default_to_the_run76_readout_and_equal_the_package():
    p = pulses()
    np.testing.assert_array_equal(flat_quantities.pretrigger_std(p), gq.pretrigger_std(p, gc.DCRC_RUN76))
    np.testing.assert_array_equal(flat_quantities.excursion_ratio(p), gq.excursion_ratio(p, gc.DCRC_RUN76))
    np.testing.assert_array_equal(flat_cuts.dead_channel(p), gcuts.dead_channel(p, gc.DCRC_RUN76))
    np.testing.assert_array_equal(flat_operations.baseline_subtract(p), gop.baseline_subtract(p, gc.DCRC_RUN76))
    np.testing.assert_array_equal(flat_quantities.frequencies_hz(100), gq.frequencies_hz(100, gc.DCRC_RUN76))


def test_a_config_given_positionally_or_by_name_still_wins():
    p = pulses()
    expected = gq.pretrigger_mean(p, gc.Z7)
    np.testing.assert_array_equal(flat_quantities.pretrigger_mean(p, gc.Z7), expected)
    np.testing.assert_array_equal(flat_quantities.pretrigger_mean(p, config=gc.Z7), expected)
    np.testing.assert_array_equal(flat_quantities.pretrigger_mean(pulses=p, config=gc.Z7), expected)


def test_flat_signatures_show_the_default_config():
    param = inspect.signature(flat_quantities.bstd).parameters["config"]
    assert param.default is flat_config.DEFAULT_CONFIG
    assert "config" in inspect.signature(gq.bstd).parameters
    assert inspect.signature(gq.bstd).parameters["config"].default is inspect.Parameter.empty


def test_flat_config_keeps_the_old_defaults_and_the_warning_for_1_6_us():
    assert flat_config.DEFAULT_CONFIG == flat_config.PulseConfig(1000, 10, 0.8e-6)
    assert flat_config.PHONON_SAMPLE_PERIOD_S == 0.8e-6
    with pytest.warns(UserWarning, match="1.6"):
        flat_config.PulseConfig(sample_period_s=1.6e-6)
    assert isinstance(flat_config.DEFAULT_CONFIG, gc.PulseConfig)   # the package functions accept it


def test_every_public_function_of_a_package_module_exists_in_its_flat_alias():
    pairs = [(gq, flat_quantities), (gcuts, flat_cuts), (gop, flat_operations)]
    for package_module, alias in pairs:
        names = [n for n, f in inspect.getmembers(package_module, inspect.isfunction)
                 if not n.startswith("_") and f.__module__ == package_module.__name__]
        missing = [n for n in names if not hasattr(alias, n)]
        assert not missing, f"{alias.__name__} lacks {missing}"


def test_status_tags_survive_the_alias_and_list_statuses_sees_them():
    assert flat_quantities.pretrigger_mean.status == "done"
    assert flat_cuts.randoms.status == "under_development"
    listed = flat_status.list_statuses(flat_cuts)
    assert "dead_channel" in listed and listed["randoms"][0] == "under_development"
    @flat_status.status(flat_status.DONE)
    def tagged():
        """A function tagged through the flat name."""
    assert tagged.status == gstatus.DONE


def test_aliases_of_functions_without_a_config_behave_like_the_package_ones():
    import goldpan.io as gio
    labels = ["a", "b", "a"]
    np.testing.assert_array_equal(flat_cuts.randoms(labels, label="a"), gcuts.randoms(labels, label="a"))
    assert flat_io.trigger_types.__doc__ == gio.trigger_types.__doc__
    assert flat_io.trigger_types.__module__ == "pulse_io"
