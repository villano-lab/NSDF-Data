//! Integral of the baseline-subtracted trace over the whole trace.
//!
//! The Python mirror is `python/goldsluice/reference/integral.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`: `baseline` = mean of `x[glitch_samples .. pretrigger_samples]`, and
//! `integral` = (sum over every sample of `x[i] - baseline`) * `sample_period_s`, as `goldpan.algorithms.integral`.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct IntegralParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
    pub sample_period_s: f64,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &IntegralParams) -> Option<String> {
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
    if p.sample_period_s.is_nan() || p.sample_period_s <= 0.0 {
        return Some("sample_period_s must be positive".to_string());
    }
    None
}

/// The integral of one trace. The parameters must already pass `problem`.
pub fn integral_one(trace: &[f64], p: &IntegralParams) -> f64 {
    let window = &trace[p.glitch_samples..p.pretrigger_samples];
    let mut total = 0.0;
    for &v in window {
        total += v;
    }
    let baseline = total / window.len() as f64;
    let mut area = 0.0;
    for &v in trace {
        area += v - baseline;
    }
    area * p.sample_period_s
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` gets one value per trace.
pub fn integral_many(traces: &[f64], n_samples: usize, p: &IntegralParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_iter_mut())
        .for_each(|(trace, o)| *o = integral_one(trace, p));
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: IntegralParams = IntegralParams {
        glitch_samples: 1,
        pretrigger_samples: 5,
        sample_period_s: 0.5,
    };

    #[test]
    fn a_small_trace() {
        // window = [2, 2, 2, 2]: baseline 2. Deviations of all 8 samples: 898, 0, 0, 0, 0, 3, 10, 1 -> 912; times 0.5
        let t = [900.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        assert_eq!(integral_one(&t, &P), 456.0);
    }

    #[test]
    fn a_flat_trace_has_no_area() {
        assert_eq!(integral_one(&[7.0; 9], &P), 0.0);
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |g, t, s| {
            problem(
                10,
                &IntegralParams {
                    glitch_samples: g,
                    pretrigger_samples: t,
                    sample_period_s: s,
                },
            )
        };
        assert_eq!(
            bad(5, 5, 1.0).unwrap(),
            "glitch_samples (5) must be smaller than pretrigger_samples (5)"
        );
        assert_eq!(
            bad(0, 11, 1.0).unwrap(),
            "pretrigger_samples (11) is longer than the trace (10 samples)"
        );
        assert_eq!(bad(0, 5, 0.0).unwrap(), "sample_period_s must be positive");
        assert_eq!(bad(0, 5, f64::NAN).unwrap(), "sample_period_s must be positive");
        assert!(bad(0, 10, 1.0).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 8;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let mut out = vec![0.0; 3];
        integral_many(&traces, n, &P, &mut out);
        for k in 0..3 {
            assert_eq!(out[k], integral_one(&traces[k * n..(k + 1) * n], &P));
        }
    }
}
