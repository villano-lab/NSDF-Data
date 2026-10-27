//! Peak of a trace: the largest ADC value and the largest current above the pretrigger baseline.
//!
//! The Python mirror is `python/goldsluice/reference/peak.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x` of `n` samples:
//! * `adc_max`     = max over all samples of `x` (raw counts);
//! * `baseline`    = mean of `x[glitch_samples .. pretrigger_samples]`;
//! * `current_max` = `(adc_max - baseline) * amps_per_adc` (amps).

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct PeakParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
    pub amps_per_adc: f64,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &PeakParams) -> Option<String> {
    if p.glitch_samples >= p.pretrigger_samples {
        return Some(format!(
            "glitch_samples ({}) must be smaller than pretrigger_samples ({})",
            p.glitch_samples, p.pretrigger_samples
        ));
    }
    if p.pretrigger_samples > n_samples {
        return Some(format!(
            "pretrigger_samples ({}) is longer than the trace ({} samples)",
            p.pretrigger_samples, n_samples
        ));
    }
    None
}

/// `(adc_max, current_max)` of one trace. The parameters must already pass `problem`.
pub fn peak_one(trace: &[f64], p: &PeakParams) -> (f64, f64) {
    let mut adc_max = trace[0];
    for &v in &trace[1..] {
        if v > adc_max {
            adc_max = v;
        }
    }
    let window = &trace[p.glitch_samples..p.pretrigger_samples];
    let mut sum = 0.0;
    for &v in window {
        sum += v;
    }
    let baseline = sum / window.len() as f64;
    (adc_max, (adc_max - baseline) * p.amps_per_adc)
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `adc` and `current` get one value per trace.
pub fn peak_many(traces: &[f64], n_samples: usize, p: &PeakParams, adc: &mut [f64], current: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(adc.par_iter_mut().zip(current.par_iter_mut()))
        .for_each(|(trace, (a, c))| {
            let (x, y) = peak_one(trace, p);
            *a = x;
            *c = y;
        });
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: PeakParams = PeakParams {
        glitch_samples: 1,
        pretrigger_samples: 5,
        amps_per_adc: 0.5,
    };

    #[test]
    fn a_small_pulse() {
        // baseline = mean(2, 2, 2, 2) = 2; max = 12
        let t = [900.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        let (a, c) = peak_one(&t, &P);
        assert_eq!(a, 900.0); // the glitch sample is still part of the raw maximum, as in `goldpan.algorithms.pulse_max`
        assert_eq!(c, (900.0 - 2.0) * 0.5);
        let t = [0.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        assert_eq!(peak_one(&t, &P), (12.0, 5.0));
    }

    #[test]
    fn many_traces_match_one_by_one() {
        let n = 8;
        let data: Vec<f64> = (0..40).map(|i| ((i * 37) % 11) as f64).collect();
        let (mut a, mut c) = (vec![0.0; 5], vec![0.0; 5]);
        peak_many(&data, n, &P, &mut a, &mut c);
        for (k, t) in data.chunks(n).enumerate() {
            assert_eq!((a[k], c[k]), peak_one(t, &P));
        }
    }

    #[test]
    fn bad_parameters_are_named() {
        assert!(problem(8, &P).is_none());
        assert!(problem(4, &P).unwrap().contains("longer than the trace"));
        let bad = PeakParams { glitch_samples: 5, ..P };
        assert!(problem(8, &bad).unwrap().contains("smaller than"));
    }
}
