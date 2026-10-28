"""The contract every algorithm meets: a Rust function and a Python mirror of the same name, giving the same numbers."""
import pkgutil

import numpy as np
import pytest

import goldsluice
from goldsluice import _core, reference
from goldsluice.algorithms import ALGORITHMS, run

NAMES = sorted(ALGORITHMS)


def test_every_reference_module_is_registered():
    on_disk = {m.name for m in pkgutil.iter_modules(reference.__path__)}
    assert on_disk == {m.__name__.rsplit(".", 1)[1] for m in reference.ALL}


@pytest.mark.parametrize("name", NAMES)
def test_every_algorithm_has_a_rust_function(name):
    assert callable(getattr(_core, name, None)), f"no Rust function {name!r} in goldsluice._core"


def test_every_rust_function_has_a_python_mirror():
    public = {n for n in dir(_core) if not n.startswith("_") and callable(getattr(_core, n))}
    assert public == set(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_rust_and_python_agree_on_the_standard_inputs(name):
    cases = ALGORITHMS[name].cases()
    assert cases, "an algorithm needs at least one standard input"
    for traces, params in cases:
        rust, py = run(name, traces, **params), run(name, traces, backend="python", **params)
        assert list(rust) == list(py) == list(ALGORITHMS[name].OUTPUTS)
        for out in rust:
            assert rust[out].shape == py[out].shape == (len(traces),)
            np.testing.assert_allclose(rust[out], py[out], rtol=1e-12, atol=0, err_msg=f"{name}.{out}")


@pytest.mark.parametrize("name", NAMES)
def test_both_backends_refuse_bad_parameters_with_the_same_message(name):
    bad = ALGORITHMS[name].bad_cases()
    assert bad, "an algorithm needs at least one input that it refuses"
    for traces, params in bad:
        messages = []
        for backend in ("rust", "python"):
            with pytest.raises(ValueError) as e:
                run(name, traces, backend=backend, **params)
            messages.append(str(e.value))
        assert messages[0] == messages[1]


@pytest.mark.parametrize("name", NAMES)
def test_every_algorithm_has_a_revision(name):
    """`REVISION` is what the ledger of `goldsluice run` compares: a whole number, 1 for a new algorithm, raised when its results change."""
    revision = ALGORITHMS[name].REVISION
    assert isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1


def test_parameters_have_no_defaults():
    with pytest.raises(TypeError):
        run("peak", np.zeros((1, 8)), glitch_samples=1, pretrigger_samples=4)          # no amps_per_adc


def test_unknown_algorithm_and_backend():
    with pytest.raises(ValueError, match="no algorithm"):
        run("nope", np.zeros((1, 8)))
    with pytest.raises(ValueError, match="backend"):
        run("peak", np.zeros((1, 8)), backend="fortran", glitch_samples=0, pretrigger_samples=4, amps_per_adc=1.0)


def test_peak_by_hand():
    t = np.array([[900.0, 2, 2, 2, 2, 5, 12, 3], [0.0, 2, 2, 2, 2, 5, 12, 3]])
    out = run("peak", t, glitch_samples=1, pretrigger_samples=5, amps_per_adc=0.5)
    np.testing.assert_array_equal(out["adc_max"], [900.0, 12.0])
    np.testing.assert_array_equal(out["current_max"], [449.0, 5.0])


def test_input_that_is_not_float64_c_contiguous_is_converted():
    ints = np.arange(64, dtype=np.int16).reshape(4, 16)
    strided = np.asfortranarray(ints.astype(float))
    kw = dict(glitch_samples=1, pretrigger_samples=8, amps_per_adc=2.0)
    a, b = run("peak", ints, **kw), run("peak", strided, **kw)
    np.testing.assert_array_equal(a["adc_max"], b["adc_max"])
    np.testing.assert_array_equal(a["current_max"], b["current_max"])


def test_one_dimensional_input_is_refused():
    with pytest.raises(ValueError, match="shape"):
        run("peak", np.zeros(8), glitch_samples=0, pretrigger_samples=4, amps_per_adc=1.0)


@pytest.mark.parametrize("name", NAMES)
def test_every_algorithm_agrees_with_goldpan_or_says_why_it_cannot(name):
    """goldpan (analysis) and goldsluice (reduction) must not define the same quantity twice with different numbers."""
    module = ALGORITHMS[name]
    expected, reason = getattr(module, "goldpan_expected", None), getattr(module, "NO_GOLDPAN", None)
    assert (expected is None) != (reason is None), f"{name}: define goldpan_expected(traces, params) or NO_GOLDPAN = '<why>', not both or neither"
    if expected is None:
        assert isinstance(reason, str) and len(reason) > 20, f"{name}: NO_GOLDPAN must say why goldpan has no counterpart"
        return
    pytest.importorskip("goldpan")
    for traces, params in module.cases():
        ours, theirs = run(name, traces, **params), expected(traces, params)
        assert sorted(theirs) == sorted(module.OUTPUTS), f"{name}: goldpan_expected must give {list(module.OUTPUTS)}"
        for out in module.OUTPUTS:
            np.testing.assert_allclose(ours[out], theirs[out], rtol=1e-12, atol=0, err_msg=f"{name}.{out} against goldpan")


def test_compare_times_both_backends():
    traces, params = ALGORITHMS["peak"].cases()[0]
    t = goldsluice.compare("peak", traces, repeat=2, python_events=5, **params)
    assert t.rust_s > 0 and t.python_s > 0 and t.n_events == len(traces)
    assert "speedup" in str(t)
