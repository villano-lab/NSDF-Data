//! Excursion of a trace after its pretrigger window: the largest deviation from the baseline, and that deviation in units of the noise.
//!
//! The Python mirror is `python/goldsluice/reference/excursion.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`, with the baseline window `x[glitch_samples .. pretrigger_samples]`, its mean `m` and its (population)
//! standard deviation `s`:
//! * `max_deviation`   = the largest `|x[i] - m|` over the samples after the window;
//! * `excursion_ratio` = `max_deviation / s`; a window with no scatter gives `inf` if the trace strays and `nan` if it does not.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct ExcursionParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &ExcursionParams) -> Option<String> {
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
    if p.pretrigger_samples == n_samples {
        return Some(format!(
            "pretrigger_samples ({}) leaves no samples after the window in a trace of {} samples",
            p.pretrigger_samples, n_samples
        ));
    }
    None
}

/// `(max_deviation, excursion_ratio)` of one trace. The parameters must already pass `problem`.
pub fn excursion_one(trace: &[f64], p: &ExcursionParams) -> (f64, f64) {
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
    let std = (squares / n).sqrt();
    let mut deviation = 0.0;
    for &v in &trace[p.pretrigger_samples..] {
        let d = (v - mean).abs();
        if d > deviation {
            deviation = d;
        }
    }
    if std == 0.0 {
        if deviation > 0.0 {
            return (deviation, f64::INFINITY);
        }
        return (deviation, f64::NAN);
    }
    (deviation, deviation / std)
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `dev` and `ratio` get one value per trace.
pub fn excursion_many(traces: &[f64], n_samples: usize, p: &ExcursionParams, dev: &mut [f64], ratio: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(dev.par_iter_mut().zip(ratio.par_iter_mut()))
        .for_each(|(trace, (d, r))| {
            let (a, b) = excursion_one(trace, p);
            *d = a;
            *r = b;
        });
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: ExcursionParams = ExcursionParams {
        glitch_samples: 1,
        pretrigger_samples: 5,
    };

    #[test]
    fn a_small_trace() {
        // window = [2, 2, 4, 4]: mean 3, std 1. After it: 50 and 60 -> deviations 47 and 57; the glitch (900) is not measured
        let t = [900.0, 2.0, 2.0, 4.0, 4.0, 50.0, 60.0];
        assert_eq!(excursion_one(&t, &P), (57.0, 57.0));
    }

    #[test]
    fn a_negative_excursion_counts() {
        let t = [0.0, 2.0, 2.0, 4.0, 4.0, 3.0, -7.0];
        assert_eq!(excursion_one(&t, &P), (10.0, 10.0));
    }

    #[test]
    fn a_window_with_no_scatter_gives_inf_or_nan() {
        let strays = [0.0, 7.0, 7.0, 7.0, 7.0, 9.0, 7.0];
        let (d, r) = excursion_one(&strays, &P);
        assert_eq!((d, r), (2.0, f64::INFINITY));
        let quiet = [0.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0];
        let (d, r) = excursion_one(&quiet, &P);
        assert_eq!(d, 0.0);
        assert!(r.is_nan());
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |g, t| {
            problem(
                10,
                &ExcursionParams {
                    glitch_samples: g,
                    pretrigger_samples: t,
                },
            )
        };
        assert_eq!(
            bad(5, 5).unwrap(),
            "glitch_samples (5) must be smaller than pretrigger_samples (5)"
        );
        assert_eq!(
            bad(0, 11).unwrap(),
            "pretrigger_samples (11) is longer than the trace (10 samples)"
        );
        assert_eq!(
            bad(0, 10).unwrap(),
            "pretrigger_samples (10) leaves no samples after the window in a trace of 10 samples"
        );
        assert!(bad(0, 9).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 8;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let (mut d, mut r) = (vec![0.0; 3], vec![0.0; 3]);
        excursion_many(&traces, n, &P, &mut d, &mut r);
        for k in 0..3 {
            assert_eq!((d[k], r[k]), excursion_one(&traces[k * n..(k + 1) * n], &P));
        }
    }
}
