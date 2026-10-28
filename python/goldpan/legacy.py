"""The flat module names of the first versions (`pulse_quantities`, `pulse_cuts`, ...), as aliases of the package.

Before the package existed, the library was eight flat modules, and the notebooks, notes and guides import them
(`import pulse_cuts as pc`). They are kept as thin files in `python/` that call `flat_namespace` below, so that they
are the *same code* as the package with two differences, both for the sake of those notebooks, which all analyse the
Run 76 readout:

* a function that takes a `config` gets the Run 76 readout as the default;
* `pulse_config.PulseConfig` has the Run 76 values as defaults (and warns when 1.6e-6 s is given, the value those
  notebooks used wrongly until 2026-10-22), and `DEFAULT_CONFIG = PulseConfig()`.

These defaults are frozen at the values the notebooks and notes were run with, including the 1000-sample pretrigger window: the
Run 76 pulses start at about sample 500, so `goldpan.config.DCRC_RUN76` has 500 since 2026-10-28 (issue 154), but changing the
flat defaults would change the results of every notebook that is run again. Pass a `config` (or `n_samples=500`) to get the
window before the pulse.

New code should import `goldpan.*` and name its readout. The flat names will be removed in a later release.
"""
import functools
import inspect
import warnings
from dataclasses import dataclass
from typing import Optional

from . import config as _config

_RETIRED_SAMPLE_PERIOD_S = 1.6e-6
"""The value used in the notebooks and notes until 2026-10-22, which was wrong for the Run 76 readout."""


@dataclass(frozen=True)
class PulseConfig(_config.PulseConfig):
    """`goldpan.config.PulseConfig` with the Run 76 readout as defaults (the flat `pulse_config.PulseConfig`)."""
    pretrigger_samples: int = 1000
    glitch_samples: int = 10
    sample_period_s: Optional[float] = 0.8e-6

    def __post_init__(self):
        if self.sample_period_s is not None and abs(self.sample_period_s - _RETIRED_SAMPLE_PERIOD_S) < 1e-12:
            warnings.warn(
                "PulseConfig(sample_period_s=1.6e-6): 1.6 us is the value our notebooks and notes used until "
                "2026-10-22 and it is wrong for the Run 76 phonon channels, which sample every 0.8 us (1.25 MHz); see "
                "'The sample period' in python/README.md. Results made with 1.6 us have times and energies twice too "
                "large, frequencies twice too small, PSDs twice and ASDs 1.41 times too large. 1.6 us is the right value "
                "for the Z7 readout: for other data use goldpan.config.PulseConfig and name the readout.",
                UserWarning, stacklevel=3)


DEFAULT_CONFIG = PulseConfig()


def alias_function(func):
    """`func` under the flat name: `DEFAULT_CONFIG` is the default of its `config` argument (if it has one).

    The wrapper keeps the signature, docstring and `@status` tag; `flat_namespace` sets its `__module__` to the flat
    module, so that `list_statuses` and the documentation tools see it as that module's function."""
    sig = inspect.signature(func)
    if "config" not in sig.parameters:
        @functools.wraps(func)
        def plain(*args, **kwargs):
            return func(*args, **kwargs)
        return plain
    new_sig = sig.replace(parameters=[p.replace(default=DEFAULT_CONFIG) if p.name == "config" else p
                                      for p in sig.parameters.values()])

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if "config" not in sig.bind_partial(*args, **kwargs).arguments:
            kwargs["config"] = DEFAULT_CONFIG
        return func(*args, **kwargs)

    wrapper.__signature__ = new_sig
    return wrapper


def flat_namespace(source, name):
    """The names of the package module `source`, for the flat module called `name` (see the module docstring)."""
    ns = {}
    for key, obj in vars(source).items():
        if key.startswith("__") and key != "__doc__":
            continue
        if inspect.isfunction(obj) and obj.__module__ == source.__name__:
            obj = alias_function(obj)
            obj.__module__ = name
        ns[key] = obj
    if "PulseConfig" in ns:
        ns["PulseConfig"] = PulseConfig
        ns["DEFAULT_CONFIG"] = DEFAULT_CONFIG
    if source is _config:                       # constants of the old pulse_config module
        ns["PHONON_SAMPLE_PERIOD_S"] = _config.DCRC_RUN76.sample_period_s
        ns["_RETIRED_SAMPLE_PERIOD_S"] = _RETIRED_SAMPLE_PERIOD_S
    return ns
