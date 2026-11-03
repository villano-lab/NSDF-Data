//! Baseline of a trace: the mean and the standard deviation of the pretrigger window.
//!
//! The Python mirror is `python/goldsluice/reference/baseline.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x` with the window `w = x[glitch_samples .. pretrigger_samples]` (the window `peak` uses for its baseline):
//! * `baseline_mean` = mean of `w`;
//! * `baseline_std`  = standard deviation of `w`, the population one (divided by the number of samples), in two passes.
//!
//! Both are in the units of the trace (ADC counts).

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct BaselineParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &BaselineParams) -> Option<String> {
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

/// `(baseline_mean, baseline_std)` of one trace. The parameters must already pass `problem`.
pub fn baseline_one(trace: &[f64], p: &BaselineParams) -> (f64, f64) {
    let window = &trace[p.glitch_samples..p.pretrigger_samples];
    let n = window.len() as f64;
    let mut total = 0.0;
    for &v in window {
        total += v;
    }
    let mean = total / n;
    let mut squares = 0.0;
    for &v in window {
        let d = v - mean;
        squares += d * d;
    }
    (mean, (squares / n).sqrt())
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `mean` and `std` get one value per trace.
pub fn baseline_many(traces: &[f64], n_samples: usize, p: &BaselineParams, mean: &mut [f64], std: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(mean.par_iter_mut().zip(std.par_iter_mut()))
        .for_each(|(trace, (m, s))| {
            let (a, b) = baseline_one(trace, p);
            *m = a;
            *s = b;
        });
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: BaselineParams = BaselineParams {
        glitch_samples: 1,
        pretrigger_samples: 5,
    };

    #[test]
    fn a_small_trace() {
        // window = [2, 2, 4, 4]: mean 3, every deviation 1, so the standard deviation is 1
        let t = [900.0, 2.0, 2.0, 4.0, 4.0, 50.0, 60.0];
        let (m, s) = baseline_one(&t, &P);
        assert_eq!(m, 3.0); // the glitch sample (900) and the pulse after the window are not in it
        assert_eq!(s, 1.0);
    }

    #[test]
    fn a_flat_window_has_no_scatter_and_one_sample_is_legal() {
        let t = [0.0, 7.0, 7.0, 7.0, 7.0, 9.0];
        assert_eq!(baseline_one(&t, &P), (7.0, 0.0));
        let one = BaselineParams {
            glitch_samples: 2,
            pretrigger_samples: 3,
        };
        assert_eq!(baseline_one(&t, &one), (7.0, 0.0));
    }

    #[test]
    fn a_large_baseline_keeps_its_small_scatter() {
        // E[x^2] - E[x]^2 would lose this to rounding; the second pass does not
        let t = [0.0, 1.0e9 - 1.0, 1.0e9 + 1.0, 1.0e9 - 1.0, 1.0e9 + 1.0];
        let (m, s) = baseline_one(&t, &P);
        assert_eq!((m, s), (1.0e9, 1.0));
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        assert_eq!(
            problem(
                10,
                &BaselineParams {
                    glitch_samples: 5,
                    pretrigger_samples: 5
                }
            )
            .unwrap(),
            "glitch_samples (5) must be smaller than pretrigger_samples (5)"
        );
        assert_eq!(
            problem(4, &P).unwrap(),
            "pretrigger_samples (5) is longer than the trace (4 samples)"
        );
        assert!(problem(5, &P).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 8;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let (mut m, mut s) = (vec![0.0; 3], vec![0.0; 3]);
        baseline_many(&traces, n, &P, &mut m, &mut s);
        for k in 0..3 {
            assert_eq!((m[k], s[k]), baseline_one(&traces[k * n..(k + 1) * n], &P));
        }
    }
}
