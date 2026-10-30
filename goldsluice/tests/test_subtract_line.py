"""`subtract_line` against `numpy.polyfit`, the way the exploration code (`small_triggers.py`, `subtract_pretrigger_line`) fits the line.

goldpan has no counterpart that the library may import (`NO_GOLDPAN`), so this is the independent check of the numbers.
"""
import numpy as np
import pytest

from goldsluice.algorithms import ALGORITHMS, run

CASES = ALGORITHMS["subtract_line"].cases()


def polyfit_residual(traces, glitch_samples, fit_end_samples):
    x = np.arange(traces.shape[-1])
    slope, offset = np.polyfit(x[glitch_samples:fit_end_samples], traces[..., glitch_samples:fit_end_samples].T, 1)
    return traces - (offset[:, None] + slope[:, None] * x)


@pytest.mark.parametrize("backend", ["rust", "python"])
@pytest.mark.parametrize("index", range(len(CASES)))
def test_it_equals_polyfit_on_the_standard_cases(index, backend):
    traces, params = CASES[index]
    ours = run("subtract_line", traces, backend=backend, **params)["trace"]
    np.testing.assert_allclose(ours, polyfit_residual(traces, **params), rtol=1e-9, atol=1e-8)


def test_the_window_has_a_zero_mean_residual_and_no_slope():
    traces, params = CASES[0]
    g, e = params["glitch_samples"], params["fit_end_samples"]
    window = run("subtract_line", traces, **params)["trace"][:, g:e]
    np.testing.assert_allclose(window.mean(axis=1), 0.0, atol=1e-8)
    np.testing.assert_allclose(window @ (np.arange(g, e) - (g + e - 1) / 2), 0.0, atol=1e-5)
