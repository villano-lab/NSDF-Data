"""Shared configuration for the pulse operations/cuts/quantities library.

One `PulseConfig` instance is passed explicitly to every function in
`pulse_operations.py`, `pulse_cuts.py`, and `pulse_quantities.py`, rather than
having each function hardcode `PRETRIGGER_SAMPLES`/`GLITCH_SAMPLES` constants
the way the exploratory notebooks did.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PulseConfig:
    pretrigger_samples: int = 1000
    """Number of leading samples that make up the pretrigger (baseline) window."""

    glitch_samples: int = 10
    """Leading samples within the pretrigger window to skip before computing
    baseline mean/std, to avoid a brief electronic-glitch step artifact seen at
    the very start of some traces (see 07221203_2025_dump1_noise.ipynb)."""

    sample_period_s: Optional[float] = 1.6e-6
    """Seconds per sample (1.6 us -> 625 kHz for this readout). None if unknown
    for a given dataset -- functions that need it (e.g. frequencies_hz) will
    raise rather than silently assume a value."""

    @property
    def sample_rate_hz(self) -> float:
        if self.sample_period_s is None:
            raise ValueError("sample_period_s is not set on this PulseConfig")
        return 1.0 / self.sample_period_s


DEFAULT_CONFIG = PulseConfig()
