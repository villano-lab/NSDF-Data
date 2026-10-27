"""The example adapter of the guide "Writing an adapter" passes the conformance test, and behaves as the guide says."""
import numpy as np
import pytest

import example_adapter as npz
from goldpan import adapters
from goldpan.config import PulseConfig
from goldpan.testing import check_adapter

CONFIG = PulseConfig(pretrigger_samples=20, glitch_samples=2, sample_period_s=1e-6)
KW = dict(detector_name="TOY", config=CONFIG, series="S1", dump="F0001")


@pytest.fixture()
def sample(tmp_path):
    rng = np.random.default_rng(0)
    path = tmp_path / "toy.npz"
    np.savez(path, event=np.arange(10) + 100, period_s=1e-6, A=rng.normal(size=(10, 64)), B=rng.normal(size=(10, 64)))
    return path


def test_the_example_passes_the_conformance_test(sample):
    assert check_adapter(npz, sample, **KW) == ["read() returns Events", "the invariants of Events hold",
                                                "iter_chunks joined equals read", "a round trip loses nothing"]


def test_read_builds_the_events_the_guide_describes(sample):
    ev = npz.read(sample, **KW)
    assert ev.detector.channel_names() == ["A", "B"] and ev.n_events == 10 and ev.trace("A").shape == (10, 64)
    assert ev.quantities["event"].to_list() == list(range(100, 110)) and ev.quantities["series"].to_list()[0] == "S1"
    assert not ev.trace("A").flags.writeable
    assert npz.read(sample, channels=["B"], **KW).detector.channel_names() == ["B"]


def test_the_readout_is_checked_against_the_file(sample):
    with pytest.raises(ValueError, match="1 us.*0.8 us"):
        npz.read(sample, **{**KW, "config": PulseConfig(20, 2, 0.8e-6)})
    with pytest.raises(KeyError, match="no arrays"):
        npz.read(sample, channels=["Z"], **KW)


def test_it_registers_like_any_other_adapter(sample):
    adapters.register("toy-npz", npz)
    assert len(adapters.read(sample, format="toy-npz", **KW)) == 10
