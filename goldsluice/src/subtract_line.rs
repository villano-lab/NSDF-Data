//! A trace minus the straight line fitted to its pretrigger samples (a transform: the result is a trace of the same length).
//!
//! The Python mirror is `python/goldsluice/reference/subtract_line.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`: the line `a + b * i` (`i` the sample index) is the least-squares fit to `x[glitch_samples .. fit_end_samples]`, with
//! `b = sum((i - ib) * (x[i] - xb)) / sum((i - ib)^2)` (`ib`, `xb` the means over the window) and `a = xb - b * ib`; the result is
//! `x[i] - (a + b * i)` for every sample of the trace. Units: those of the trace (ADC counts).

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct SubtractLineParams {
    pub glitch_samples: usize,
    pub fit_end_samples: usize,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &SubtractLineParams) -> Option<String> {
    if p.fit_end_samples < p.glitch_samples.saturating_add(2) {
        return Some(format!(
            "fit_end_samples ({}) must be at least two more than glitch_samples ({})",
            p.fit_end_samples, p.glitch_samples
        ));
    }
    if p.fit_end_samples > n_samples {
        return Some(format!(
            "fit_end_samples ({}) is longer than the trace ({} samples)",
            p.fit_end_samples, n_samples
        ));
    }
    None
}

/// The residual of one trace about its fitted line, written to `out` (same length as `trace`). The parameters must already pass `problem`.
pub fn subtract_line_one(trace: &[f64], p: &SubtractLineParams, out: &mut [f64]) {
    let m = (p.fit_end_samples - p.glitch_samples) as f64;
    let mut total_i = 0.0;
    let mut total_x = 0.0;
    let window = &trace[p.glitch_samples..p.fit_end_samples];
    for (k, &v) in window.iter().enumerate() {
        total_i += (p.glitch_samples + k) as f64;
        total_x += v;
    }
    let ib = total_i / m;
    let xb = total_x / m;
    let mut sxy = 0.0;
    let mut sxx = 0.0;
    for (k, &v) in window.iter().enumerate() {
        let di = (p.glitch_samples + k) as f64 - ib;
        sxy += di * (v - xb);
        sxx += di * di;
    }
    let b = sxy / sxx;
    let a = xb - b * ib;
    for (i, (o, &v)) in out.iter_mut().zip(trace).enumerate() {
        *o = v - (a + b * i as f64);
    }
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` has the shape of `traces`.
pub fn subtract_line_many(traces: &[f64], n_samples: usize, p: &SubtractLineParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_chunks_mut(n_samples))
        .for_each(|(trace, o)| subtract_line_one(trace, p, o));
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: SubtractLineParams = SubtractLineParams {
        glitch_samples: 1,
        fit_end_samples: 5,
    };

    #[test]
    fn a_line_in_the_window_is_removed_everywhere() {
        // the window x[1..5] = [1, 2, 3, 4] is exactly the line x = i; the glitch (900) and the sample after the window (10) stay as residuals
        let t = [900.0, 1.0, 2.0, 3.0, 4.0, 10.0];
        let mut o = [0.0; 6];
        subtract_line_one(&t, &P, &mut o);
        assert_eq!(o, [900.0, 0.0, 0.0, 0.0, 0.0, 5.0]);
    }

    #[test]
    fn a_slope_and_an_offset_are_fitted() {
        // x = 10 + 2 i in the window, noisy outside it: the fit is exact, so the residual outside is x - (10 + 2 i)
        let t = [99.0, 12.0, 14.0, 16.0, 18.0, 40.0, 0.0];
        let mut o = [0.0; 7];
        subtract_line_one(&t, &P, &mut o);
        for (i, &r) in o.iter().enumerate() {
            assert!((r - (t[i] - (10.0 + 2.0 * i as f64))).abs() < 1e-12, "{i}: {r}");
        }
    }

    #[test]
    fn two_samples_are_the_smallest_window_and_a_flat_trace_gives_zero() {
        let two = SubtractLineParams {
            glitch_samples: 2,
            fit_end_samples: 4,
        };
        let t = [5.0, 9.0, 3.0, 7.0, 100.0];
        let mut o = [0.0; 5];
        subtract_line_one(&t, &two, &mut o); // the line through (2, 3) and (3, 7) is 4 i - 5
        assert_eq!(o, [10.0, 10.0, 0.0, 0.0, 89.0]);
        let flat = [7.0; 6];
        let mut f = [1.0; 6];
        subtract_line_one(&flat, &P, &mut f);
        assert_eq!(f, [0.0; 6]);
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |g, e| SubtractLineParams {
            glitch_samples: g,
            fit_end_samples: e,
        };
        assert_eq!(
            problem(10, &bad(5, 6)).unwrap(),
            "fit_end_samples (6) must be at least two more than glitch_samples (5)"
        );
        assert_eq!(
            problem(4, &P).unwrap(),
            "fit_end_samples (5) is longer than the trace (4 samples)"
        );
        assert!(problem(5, &P).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 8;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let mut out = vec![0.0; 3 * n];
        subtract_line_many(&traces, n, &P, &mut out);
        for k in 0..3 {
            let mut one = vec![0.0; n];
            subtract_line_one(&traces[k * n..(k + 1) * n], &P, &mut one);
            assert_eq!(&out[k * n..(k + 1) * n], &one[..]);
        }
    }
}
