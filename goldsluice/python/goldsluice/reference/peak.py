"""Python mirror of `src/peak.rs`: the largest ADC value and the largest current above the pretrigger baseline of a trace.

For one trace `x` of `n` samples:

* `adc_max`     = max over all samples of `x` (raw counts);
* `baseline`    = mean of `x[glitch_samples:pretrigger_samples]`;
* `current_max` = `(adc_max - baseline) * amps_per_adc` (amps).

`amps_per_adc` has no default: the conversion belongs to the readout, not to this package.

This file is written in the *kernel subset* (see `PORTING.md`) so that it can be ported to Rust line by line.
"""
import numpy as np

NAME = "peak"
OUTPUTS = ("adc_max", "current_max")


def problem(n_samples, glitch_samples, pretrigger_samples, amps_per_adc):
    """Why the parameters do not fit a trace of `n_samples`, or `None` if they do."""
    if glitch_samples >= pretrigger_samples:
        return f"glitch_samples ({glitch_samples}) must be smaller than pretrigger_samples ({pretrigger_samples})"
    if pretrigger_samples > n_samples:
        return f"pretrigger_samples ({pretrigger_samples}) is longer than the trace ({n_samples} samples)"
    return None


def kernel(trace, glitch_samples, pretrigger_samples, amps_per_adc):
    adc_max = trace[0]
    for i in range(1, len(trace)):
        if trace[i] > adc_max:
            adc_max = trace[i]
    total = 0.0
    for i in range(glitch_samples, pretrigger_samples):
        total += trace[i]
    baseline = total / (pretrigger_samples - glitch_samples)
    return adc_max, (adc_max - baseline) * amps_per_adc


def cases():
    """The standard inputs the parity test runs both versions on: `[(traces, params), ...]`."""
    rng = np.random.default_rng(76)
    params = dict(glitch_samples=10, pretrigger_samples=1000, amps_per_adc=1.5e-9)
    pulses = rng.normal(2000.0, 5.0, size=(20, 4096))
    pulses[:, 1500:1800] += np.linspace(0, 3000, 300)           # a made-up pulse after the trigger
    pulses[:, :5] += 800.0                                       # the electronics glitch, inside the raw maximum
    flat = np.full((3, 64), 7.0)                                 # nothing but baseline
    ints = rng.integers(0, 4096, size=(5, 128)).astype(float)    # raw ADC counts
    return [
        (pulses, params),
        (flat, dict(glitch_samples=1, pretrigger_samples=32, amps_per_adc=1.0)),
        (ints, dict(glitch_samples=0, pretrigger_samples=64, amps_per_adc=-2.0)),
    ]
