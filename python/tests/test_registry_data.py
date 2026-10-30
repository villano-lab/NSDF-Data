"""The registry of this repository (`registry/`, data and not library code) is valid, agrees with the library where both state the
same thing, and the example that uses it gives the same results as the example that writes everything out. If the folder moves to a
repository of its own, these tests go with it (they skip when the folder is not here)."""
import dataclasses
from pathlib import Path

import pytest

from goldpan import channels, config, dataset, registry
from goldpan.config import DCRC_RUN76

REPO = Path(__file__).resolve().parents[2]
FOLDER = REPO / "registry"
EXAMPLES = REPO / "goldsluice" / "examples"

pytestmark = pytest.mark.skipif(not FOLDER.is_dir(), reason="the registry folder is not in this checkout")


def reg():
    return registry.load(FOLDER, use_environment=False)


def test_the_folder_is_a_valid_registry_and_every_entry_says_where_it_comes_from():
    r = reg()
    assert r.detectors()
    for rec in list(r.detectors().values()) + list(r.readouts().values()):
        assert rec.status in registry.STATUSES and rec.evidence.strip()
    for rec in r.detectors().values():
        if rec.readout is not None:
            r.readout_config(rec.readout)                                    # the readout it names exists


def test_nai_s2_has_the_channel_map_that_goldpan_channels_holds_and_the_run_76_readout():
    rec = reg().detector("NAI-S2")
    idx = rec.read_defaults("idx")
    assert {name: tuple(v) for name, v in idx["channels"].items()} == \
        {c.name: (c.detector, c.channel) for c in channels.sensor_channels()}
    assert set(idx["roles"]) == set(idx["channels"]) and set(idx["roles"].values()) == {"phonon"}
    assert reg().readout_config(rec.readout) == DCRC_RUN76
    assert rec.status == "inferred" and "07221203_2025" in rec.series


def test_the_example_that_uses_the_registry_means_the_same_as_the_one_that_writes_everything():
    explicit = dataset.load(EXAMPLES / "r76.dataset.toml")
    via = dataset.load(EXAMPLES / "r76-registry.dataset.toml")
    a, b = explicit.sources[0], via.sources[0]
    assert (a.readout, dict(a.read), a.detector) == (b.readout, dict(b.read), b.detector)
    n = len(explicit.steps)                                                            # the registry example has more steps: all the algorithms
    assert [(s.algorithm, s.channels, s.params) for s in via.steps[:n]] == [(s.algorithm, s.channels, s.params) for s in explicit.steps]
    same_steps = dataclasses.replace(via, steps=explicit.steps)                        # then only the way the detector is described differs
    assert dataset.fingerprint(explicit, a) == dataset.fingerprint(same_steps, same_steps.sources[0])     # processed files stay valid
    assert b.detector_record.number == 1


def test_the_registry_example_gives_root_output_without_root_detector(tmp_path):
    text = (EXAMPLES / "r76-registry.dataset.toml").read_text(encoding="utf-8")
    text = text.replace('# output_format = "root"', 'output_format = "root"').replace('"../../registry"', repr(str(FOLDER)).replace("'", '"'))
    p = tmp_path / "r76-root.dataset.toml"
    p.write_text(text, encoding="utf-8")
    spec = dataset.load(p)
    assert (spec.output_format, spec.root_detector) == ("root", 1)


def test_the_readouts_of_the_registry_and_the_presets_of_goldpan_config_are_the_same_numbers():
    r = reg()
    assert {"DCRC_RUN76", "Z7"} <= set(r.readouts())
    for name, rec in r.readouts().items():
        preset = getattr(config, name, None)
        if preset is not None:
            assert rec.config == preset, f"readout {name}: the registry and goldpan.config disagree"


def test_the_run_76_readout_ends_its_baseline_window_where_the_pulses_start():
    rec = reg().readouts()["DCRC_RUN76"]
    assert rec.config.pretrigger_samples == 500 and rec.config.sample_period_s == 0.8e-6
    assert "480 to 520" in rec.evidence and rec.status in registry.STATUSES              # the measurement it rests on is stated
