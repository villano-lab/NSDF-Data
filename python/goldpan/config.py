"""Configuration of a readout, shared by the pulse quantities, cuts and operations.

One `PulseConfig` is passed explicitly to every function in `goldpan.quantities`, `goldpan.cuts` and
`goldpan.operations`. **It has no defaults**: how long the pretrigger window is, how many leading samples carry a
glitch and how long one sample lasts all belong to a *readout*, not to this library, and a wrong silent default
(the library once assumed 1.6 us for a readout that samples every 0.8 us) changes every time, frequency and energy
without any error. Name the readout of your data, either with a preset or with the numbers::

    from goldpan.config import DCRC_RUN76, Z7, PulseConfig

    config = DCRC_RUN76                                                  # the Run 76 phonon channels
    config = PulseConfig(pretrigger_samples=2000, glitch_samples=10, sample_period_s=1e-6)   # your own

The presets are data, not recommendations (the registry, `goldpan.registry`, holds the same readouts with their evidence): `DCRC_RUN76` is the DCRC readout of the Run 76 (UMN, 2022) series, 0.8 us per
sample (1.25 MHz; see "The sample period" in `python/README.md` for the evidence), and `Z7` is the Z7 (SNOLAB) readout,
1.6 us per sample (625 kHz). Both are right for their data and wrong for each other's.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PulseConfig:
    pretrigger_samples: int
    """Number of leading samples that make up the pretrigger (baseline) window."""

    glitch_samples: int
    """Leading samples within the pretrigger window to skip before computing
    baseline mean/std, to avoid a brief electronic-glitch step artifact seen at
    the very start of some traces (see 07221203_2025_dump1_noise.ipynb)."""

    sample_period_s: Optional[float]
    """Seconds per sample. Pass `None` if it is unknown for a dataset: the functions that need it (for example
    `frequencies_hz`) then raise rather than silently assume a value."""

    @property
    def sample_rate_hz(self) -> float:
        if self.sample_period_s is None:
            raise ValueError("sample_period_s is not set on this PulseConfig")
        return 1.0 / self.sample_period_s


DCRC_RUN76 = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=0.8e-6)
"""The DCRC readout of the Run 76 series (UMN): 500-sample pretrigger window, 0.8 us per sample (1.25 MHz), a trace of
4096 samples is 3.2768 ms. The pulses of the trigger-locked events start at about sample 500, not at 1000 (value until 2026-10-28;
issue 154). The record with the evidence is `[readouts.DCRC_RUN76]` in `registry/readouts.toml` (`goldpan.registry`); this preset is
kept for existing code and a test checks that the two agree."""

Z7 = PulseConfig(pretrigger_samples=6250, glitch_samples=10, sample_period_s=1.6e-6)
"""The Z7 readout (SNOLAB): 6250-sample pretrigger window (10 ms), 1.6 us per sample (625 kHz)."""
