"""Derived quantities: pulses in, one real number (or one array) per pulse out.

Every function here takes an array shaped ``(..., n_samples)`` -- a single pulse
``(n_samples,)`` or a batch ``(n_pulses, n_samples)`` both work unchanged, since
all reductions run along ``axis=-1``. Output shape is one dimension smaller
(``(...,)``) for scalar-per-pulse quantities, or ``(..., n_freq)`` for spectra.

These are the primitives: cuts in `pulse_cuts.py` are built by thresholding
the quantities defined here.
"""
import numpy as np

from pulse_config import PulseConfig, DEFAULT_CONFIG
from pulse_status import status, DONE, UNDER_DEVELOPMENT


@status(DONE)
def pretrigger_mean(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """Mean of the pretrigger window, skipping `config.glitch_samples` leading samples."""
    pulses = np.asarray(pulses)
    window = pulses[..., config.glitch_samples:config.pretrigger_samples]
    return window.mean(axis=-1)


@status(DONE)
def pretrigger_std(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """Std of the pretrigger window, skipping `config.glitch_samples` leading samples."""
    pulses = np.asarray(pulses)
    window = pulses[..., config.glitch_samples:config.pretrigger_samples]
    return window.std(axis=-1)


@status(DONE)
def max_deviation(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """Max |post-pretrigger sample - pretrigger mean| per pulse ("dev" in the notebooks).

    Measured only in the post-pretrigger region (samples `pretrigger_samples:`).
    Measuring it over the whole trace instead (including the samples used to
    compute the pretrigger mean) puts an artificial floor around
    `excursion_ratio ~ 1` regardless of any threshold, by basic extreme-value
    statistics -- see 07221203_2025_dump1_noise.ipynb for the full explanation.
    """
    pulses = np.asarray(pulses)
    bmean = pretrigger_mean(pulses, config)
    post = pulses[..., config.pretrigger_samples:]
    return np.max(np.abs(post - bmean[..., np.newaxis]), axis=-1)


@status(DONE)
def excursion_ratio(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """`max_deviation / pretrigger_std` ("ratio" in the notebooks).

    For pure noise, extreme-value statistics put this around 3-8 (the max of
    ~3000 samples is expected to be several sigma out), *not* near 1 -- traces
    that land near 1 usually have a contaminated (inflated) pretrigger std
    instead of being unusually quiet. See the "inverts the naive expectation"
    finding in 07221203_2025_dump1_noise.ipynb before using this as a
    "smaller = quieter" cut.
    """
    return max_deviation(pulses, config) / pretrigger_std(pulses, config)


@status(DONE)
def log_excursion_ratio(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """`log10(excursion_ratio)` -- the quantity actually thresholded by the
    notebooks' Branch 2 exploration (07221203_2025_dump1_noise.ipynb), since the
    ratio's dynamic range spans orders of magnitude between the contaminated and
    quiet populations."""
    return np.log10(excursion_ratio(pulses, config))


@status(UNDER_DEVELOPMENT, note="devised specifically to tell a sustained real "
        "pulse (rises and stays elevated for many *consecutive* samples while it "
        "decays) apart from noise, for use by pulse_cuts.looks_like_pulse / "
        "excursion_band_AI. Deliberately uses the longest *contiguous* run, not a "
        "total count -- with ~2500 post-pretrigger samples, a plain count of "
        "samples above half-max is dominated by ordinary Gaussian tail hits (checked "
        "against real 07221203_2025_F0001 data: an early total-count version flagged "
        "every trace in the tight excursion_band as 'pulse-like'). Not "
        "independently validated beyond that one check.")
def excursion_duration(pulses, config: PulseConfig = DEFAULT_CONFIG, fraction: float = 0.5):
    """Longest run of *consecutive* post-pretrigger samples with
    `|sample - pretrigger_mean| >= fraction * max_deviation` -- how long the trace
    stays near its own peak without dropping back down."""
    pulses = np.asarray(pulses)
    bmean = pretrigger_mean(pulses, config)
    dev = max_deviation(pulses, config)
    post = pulses[..., config.pretrigger_samples:]
    absdev = np.abs(post - bmean[..., np.newaxis])
    mask = absdev >= (fraction * dev)[..., np.newaxis]

    orig_shape = mask.shape[:-1]
    flat = mask.reshape(-1, mask.shape[-1])
    durations = np.zeros(flat.shape[0], dtype=int)
    for i, row in enumerate(flat):
        if not row.any():
            continue
        padded = np.concatenate(([False], row, [False])).astype(np.int8)
        edges = np.diff(padded)
        starts = np.flatnonzero(edges == 1)
        ends = np.flatnonzero(edges == -1)
        durations[i] = (ends - starts).max()
    return durations.reshape(orig_shape)


@status(UNDER_DEVELOPMENT, note="fraction=0.5 half-max crossing heuristic; only "
        "validated on one exploratory analysis (07221203_2025_dump1_noise.ipynb's "
        "Cut A rise-time check) -- not yet checked against noisy/multi-peak traces")
def rise_sample(pulses, config: PulseConfig = DEFAULT_CONFIG, fraction: float = 0.5):
    """First post-pretrigger sample index (absolute, not relative to the window)
    where the pulse crosses `fraction` of its own `max_deviation`.

    Guaranteed to find a crossing (the sample achieving the max deviation
    itself always satisfies `>= fraction * max_deviation` for `fraction <= 1`),
    so this never silently falls back to index 0 for "no crossing found".
    """
    pulses = np.asarray(pulses)
    bmean = pretrigger_mean(pulses, config)
    dev = max_deviation(pulses, config)
    post = pulses[..., config.pretrigger_samples:]
    absdev = np.abs(post - bmean[..., np.newaxis])
    crossed = absdev >= (fraction * dev)[..., np.newaxis]
    idx = np.argmax(crossed, axis=-1)
    return config.pretrigger_samples + idx


@status(DONE)
def power_spectrum(pulses, config: PulseConfig = DEFAULT_CONFIG):
    """Real part of `rfft(pulse) * conj(rfft(pulse))` ("complex square"/|FFT|^2) per pulse.

    Does *not* baseline-subtract for you -- pass already-baseline-subtracted
    pulses (see `pulse_operations.baseline_subtract`) or the DC bin will
    dominate every spectrum.
    """
    pulses = np.asarray(pulses)
    spectrum = np.fft.rfft(pulses, axis=-1)
    return (spectrum * np.conj(spectrum)).real


@status(DONE)
def frequencies_hz(n_samples: int, config: PulseConfig = DEFAULT_CONFIG):
    """Frequency bins (Hz) matching `power_spectrum`'s / `np.fft.rfft`'s output for
    a pulse of length `n_samples`. Raises if `config.sample_period_s` is unset."""
    return np.fft.rfftfreq(n_samples, d=config.sample_period_s)
