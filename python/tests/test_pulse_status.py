import warnings

import pytest

from pulse_status import status, list_statuses, DONE, UNDER_DEVELOPMENT


def test_done_function_runs_silently_and_is_tagged():
    @status(DONE)
    def f(x):
        return x + 1

    assert f.status == DONE
    assert f.status_note is None
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning fails the test
        assert f(1) == 2


def test_under_development_function_warns_and_still_runs():
    @status(UNDER_DEVELOPMENT, note="heuristic")
    def g(x):
        return x * 2

    assert g.status == UNDER_DEVELOPMENT
    assert g.status_note == "heuristic"
    with pytest.warns(UserWarning, match="heuristic"):
        result = g(3)
    assert result == 6


def test_invalid_status_raises():
    with pytest.raises(ValueError):
        @status("not_a_real_status")
        def f():
            pass


def test_list_statuses_reflects_module_contents():
    import types

    mod = types.ModuleType("fake_pulse_module")

    @status(DONE)
    def a(x):
        return x

    @status(UNDER_DEVELOPMENT, note="wip")
    def b(x):
        return x

    def c(x):  # untagged -- should not appear
        return x

    a.__module__ = mod.__name__
    b.__module__ = mod.__name__
    c.__module__ = mod.__name__
    mod.a, mod.b, mod.c = a, b, c

    statuses = list_statuses(mod)
    assert statuses == {"a": (DONE, None), "b": (UNDER_DEVELOPMENT, "wip")}
