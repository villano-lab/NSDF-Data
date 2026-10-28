"""The example definition that shows every algorithm (`examples/r76-registry.dataset.toml`) keeps showing every algorithm."""
from pathlib import Path

import numpy as np
import pytest

dataset = pytest.importorskip("goldpan.dataset")

from goldsluice.algorithms import ALGORITHMS, run

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "r76-registry.dataset.toml"


def test_the_registry_example_uses_every_algorithm_and_every_step_runs_with_its_parameters():
    spec = dataset.load(EXAMPLE)
    assert sorted({s.algorithm for s in spec.steps}) == sorted(ALGORITHMS), \
        "examples/r76-registry.dataset.toml must have a step for every algorithm of goldsluice (add the new one)"
    rng = np.random.default_rng(0)
    traces = rng.normal(3000.0, 5.0, size=(4, 4096))
    traces[:, 600:900] += 800.0                                          # a pulse after the pretrigger window
    config = spec.sources[0].readout                                     # from the registry: the readout of the detector
    for step in spec.steps:
        out = run(step.algorithm, traces, **step.resolve(config))
        assert list(out) == list(ALGORITHMS[step.algorithm].OUTPUTS)


def test_no_two_steps_of_the_registry_example_write_the_same_quantity():
    spec = dataset.load(EXAMPLE)
    names = [name for s in spec.steps for name in ALGORITHMS[s.algorithm].OUTPUTS]
    assert len(names) == len(set(names)), f"two steps give the same quantity: {names}"
