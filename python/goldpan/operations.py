"""Operations: pulses in, new (modified) pulses out -- same pulse-shaped family.

Every function takes an array shaped ``(..., n_samples)`` and returns an array
of the same leading shape (trailing/sample axis may shrink, e.g. `trim_glitch`),
never a scalar or boolean -- that's what distinguishes an operation from a
quantity or a cut. None of these mutate their input in place.
"""
import numpy as np

from .config import PulseConfig
from .quantities import pretrigger_mean
from .status import status, DONE


@status(DONE)
def baseline_subtract(pulses, config: PulseConfig):
    """Subtract each pulse's own pretrigger mean (see `goldpan.quantities.pretrigger_mean`)."""
    pulses = np.asarray(pulses)
    bmean = pretrigger_mean(pulses, config)
    return pulses - bmean[..., np.newaxis]


@status(DONE)
def trim_glitch(pulses, config: PulseConfig):
    """Drop the leading `config.glitch_samples` samples from every pulse.

    Shortens the sample axis by `glitch_samples` -- downstream sample indices
    (e.g. from `goldpan.quantities.rise_sample`) computed on the *untrimmed*
    array will no longer line up after this.
    """
    pulses = np.asarray(pulses)
    return pulses[..., config.glitch_samples:]


@status(DONE)
def clip(pulses, low=None, high=None):
    """Clip every sample to `[low, high]`. Plain `np.clip` wrapper for pipeline symmetry
    with the other operations (e.g. clipping a display copy without touching source data)."""
    return np.clip(np.asarray(pulses), low, high)
