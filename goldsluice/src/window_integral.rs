//! Integral of the baseline-subtracted trace between two samples.
//!
//! The Python mirror is `python/goldsluice/reference/window_integral.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`: `baseline` = mean of `x[glitch_samples .. pretrigger_samples]`, and
//! `window_integral` = (sum of `x[i] - baseline` for `i` in `start_sample .. stop_sample`) * `sample_period_s`.
//! `stop_sample` is not included; `0 .. n_samples` gives the `integral` of the whole trace.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct WindowIntegralParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
    pub sample_period_s: f64,
    pub start_sample: usize,
    pub stop_sample: usize,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &WindowIntegralParams) -> Option<String> {
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
    if p.start_sample >= p.stop_sample {
        return Some(format!(
            "start_sample ({}) must be smaller than stop_sample ({})",
            p.start_sample, p.stop_sample
        ));
    }
    if p.stop_sample > n_samples {
        return Some(format!(
            "stop_sample ({}) is past the end of the trace ({} samples)",
            p.stop_sample, n_samples
        ));
    }
    None
}

/// The windowed integral of one trace. The parameters must already pass `problem`.
pub fn window_integral_one(trace: &[f64], p: &WindowIntegralParams) -> f64 {
    let window = &trace[p.glitch_samples..p.pretrigger_samples];
    let mut total = 0.0;
    for &v in window {
        total += v;
    }
    let baseline = total / window.len() as f64;
    let mut area = 0.0;
    for &v in &trace[p.start_sample..p.stop_sample] {
        area += v - baseline;
    }
    area * p.sample_period_s
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` gets one value per trace.
pub fn window_integral_many(traces: &[f64], n_samples: usize, p: &WindowIntegralParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_iter_mut())
        .for_each(|(trace, o)| *o = window_integral_one(trace, p));
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::integral::{IntegralParams, integral_one};

    const P: WindowIntegralParams = WindowIntegralParams {
        glitch_samples: 1,
        pretrigger_samples: 5,
        sample_period_s: 0.5,
        start_sample: 5,
        stop_sample: 7,
    };

    #[test]
    fn a_small_trace() {
        // window = [2, 2, 2, 2]: baseline 2. Deviations of samples 5 and 6: 3, 10 -> 13; times 0.5
        let t = [900.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        assert_eq!(window_integral_one(&t, &P), 6.5);
    }

    #[test]
    fn the_glitch_counts_when_the_limits_include_it() {
        // samples 0 and 1: 898 + 0, times 0.5
        let t = [900.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        let p = WindowIntegralParams {
            start_sample: 0,
            stop_sample: 2,
            ..P
        };
        assert_eq!(window_integral_one(&t, &p), 449.0);
    }

    #[test]
    fn the_whole_trace_is_the_integral() {
        let t = [900.0, 2.0, 2.0, 2.0, 2.0, 5.0, 12.0, 3.0];
        let whole = WindowIntegralParams {
            start_sample: 0,
            stop_sample: t.len(),
            ..P
        };
        let i = IntegralParams {
            glitch_samples: 1,
            pretrigger_samples: 5,
            sample_period_s: 0.5,
        };
        assert_eq!(window_integral_one(&t, &whole), integral_one(&t, &i));
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |start, stop| {
            problem(
                10,
                &WindowIntegralParams {
                    start_sample: start,
                    stop_sample: stop,
                    ..P
                },
            )
        };
        assert_eq!(bad(4, 4).unwrap(), "start_sample (4) must be smaller than stop_sample (4)");
        assert_eq!(bad(6, 3).unwrap(), "start_sample (6) must be smaller than stop_sample (3)");
        assert_eq!(
            bad(0, 11).unwrap(),
            "stop_sample (11) is past the end of the trace (10 samples)"
        );
        assert!(bad(0, 10).is_none());
        let no_period = WindowIntegralParams {
            sample_period_s: 0.0,
            ..P
        };
        assert_eq!(problem(10, &no_period).unwrap(), "sample_period_s must be positive");
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 8;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let mut out = vec![0.0; 3];
        window_integral_many(&traces, n, &P, &mut out);
        for k in 0..3 {
            assert_eq!(out[k], window_integral_one(&traces[k * n..(k + 1) * n], &P));
        }
    }
}
