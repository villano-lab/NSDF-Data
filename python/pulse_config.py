"""Shared configuration for the pulse operations/cuts/quantities library.

One `PulseConfig` instance is passed explicitly to every function in
`pulse_operations.py`, `pulse_cuts.py`, and `pulse_quantities.py`, rather than
having each function hardcode `PRETRIGGER_SAMPLES`/`GLITCH_SAMPLES` constants
the way the exploratory notebooks did.

The sample period (`sample_period_s`) is 0.8 us (1.25 MHz) for the phonon channels of the DCRC
readout. Until 2026-10-22 the library used 1.6 us, which was wrong: see "The sample period" in
`python/README.md` for the evidence. `PulseConfig` warns when 1.6e-6 is passed explicitly.
"""
import warnings
from dataclasses import dataclass
from typing import Optional

PHONON_SAMPLE_PERIOD_S = 0.8e-6
"""Seconds per sample of the DCRC phonon channels (1.25 MHz): a trace of 4096 samples is 3.2768 ms."""

_RETIRED_SAMPLE_PERIOD_S = 1.6e-6
"""The value used here, in the notebooks and in the notes until 2026-10-22, which was wrong."""


@dataclass(frozen=True)
class PulseConfig:
    pretrigger_samples: int = 1000
    """Number of leading samples that make up the pretrigger (baseline) window."""

    glitch_samples: int = 10
    """Leading samples within the pretrigger window to skip before computing
    baseline mean/std, to avoid a brief electronic-glitch step artifact seen at
    the very start of some traces (see 07221203_2025_dump1_noise.ipynb)."""

    sample_period_s: Optional[float] = PHONON_SAMPLE_PERIOD_S
    """Seconds per sample (0.8 us -> 1.25 MHz for the phonon channels of this readout). None if
    unknown for a given dataset -- functions that need it (e.g. frequencies_hz) will raise rather
    than silently assume a value."""

    def __post_init__(self):
        if self.sample_period_s is not None and abs(self.sample_period_s - _RETIRED_SAMPLE_PERIOD_S) < 1e-12:
            warnings.warn(
                "PulseConfig(sample_period_s=1.6e-6): 1.6 us is the value our notebooks and notes used until "
                "2026-10-22 and it is wrong. The phonon channels sample every 0.8 us (1.25 MHz); see 'The sample "
                "period' in python/README.md. Results made with 1.6 us have times and energies twice too large, "
                "frequencies twice too small, PSDs twice and ASDs 1.41 times too large. "
                "Remove the explicit value so that the default (0.8 us) is used.",
                UserWarning, stacklevel=3)

    @property
    def sample_rate_hz(self) -> float:
        if self.sample_period_s is None:
            raise ValueError("sample_period_s is not set on this PulseConfig")
        return 1.0 / self.sample_period_s


DEFAULT_CONFIG = PulseConfig()
