"""Development-status tagging for functions in this library.

Usage::

    from pulse_status import status, DONE, UNDER_DEVELOPMENT

    @status(DONE)
    def pretrigger_mean(pulses, config=DEFAULT_CONFIG):
        ...

    @status(UNDER_DEVELOPMENT, note="fraction=0.5 crossing heuristic, lightly validated")
    def rise_sample(pulses, config=DEFAULT_CONFIG, fraction=0.5):
        ...

`DONE` functions are called normally. `UNDER_DEVELOPMENT` functions still run,
but emit a `UserWarning` on every call (with the note, if given) so it's
obvious in notebook output when a result depends on something not yet
considered settled. Use `list_statuses(module)` to get an overview of a whole
module at a glance.
"""
import functools
import inspect
import warnings

DONE = "done"
UNDER_DEVELOPMENT = "under_development"
_VALID = (DONE, UNDER_DEVELOPMENT)


def status(level, note=None):
    """Decorator: tag a function with a development status.

    Attaches `.status` and `.status_note` to the function either way. For
    `UNDER_DEVELOPMENT`, also wraps the function to emit a `UserWarning` on
    every call.
    """
    if level not in _VALID:
        raise ValueError(f"status must be one of {_VALID}, got {level!r}")

    def decorator(func):
        if level == DONE:
            func.status = level
            func.status_note = note
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__name__} is marked under_development"
            if note:
                msg += f": {note}"
            warnings.warn(msg, UserWarning, stacklevel=2)
            return func(*args, **kwargs)

        wrapper.status = level
        wrapper.status_note = note
        return wrapper

    return decorator


def list_statuses(module):
    """Return `{function_name: (status, note)}` for every status-tagged
    function defined in `module` (skips imports from other modules)."""
    out = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        if hasattr(obj, "status"):
            out[name] = (obj.status, getattr(obj, "status_note", None))
    return out
