//! Rise time of the largest pulse of a trace (s), as `goldpan.algorithms.rise_time`.
//!
//! The Python mirror is `python/goldsluice/reference/rise_time.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`: `baseline` = mean of `x[glitch_samples .. pretrigger_samples]`, `y[i] = x[i] - baseline`; the peak is the first
//! largest `y` over all samples, at `peak` with height `amp`; `i_lo` (`i_hi`) is the last `i <= peak` with `y[i] < lo * amp`
//! (`hi * amp`), or -1; the result is `(i_hi - i_lo) * sample_period_s`, and `nan` unless `amp > 0` and both were found.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct RiseTimeParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
    pub sample_period_s: f64,
    pub lo: f64,
    pub hi: f64,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &RiseTimeParams) -> Option<String> {
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
    if p.lo.is_nan() || p.hi.is_nan() || p.lo < 0.0 || p.lo >= p.hi || p.hi > 1.0 {
        return Some("lo and hi must satisfy 0 <= lo < hi <= 1".to_string());
    }
    None
}

/// The rise time of one trace. The parameters must already pass `problem`.
pub fn rise_time_one(trace: &[f64], p: &RiseTimeParams) -> f64 {
    let window = &trace[p.glitch_samples..p.pretrigger_samples];
    let mut total = 0.0;
    for &v in window {
        total += v;
    }
    let baseline = total / window.len() as f64;
    let mut peak = 0;
    let mut amp = trace[0] - baseline;
    for (i, &v) in trace.iter().enumerate().skip(1) {
        let y = v - baseline;
        if y > amp {
            amp = y;
            peak = i;
        }
    }
    let mut i_lo: i64 = -1;
    let mut i_hi: i64 = -1;
    for (i, &v) in trace.iter().enumerate().take(peak + 1) {
        let y = v - baseline;
        if y < p.lo * amp {
            i_lo = i as i64;
        }
        if y < p.hi * amp {
            i_hi = i as i64;
        }
    }
    if amp > 0.0 && i_lo >= 0 && i_hi >= 0 {
        (i_hi - i_lo) as f64 * p.sample_period_s
    } else {
        f64::NAN
    }
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` gets one value per trace.
pub fn rise_time_many(traces: &[f64], n_samples: usize, p: &RiseTimeParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_iter_mut())
        .for_each(|(trace, o)| *o = rise_time_one(trace, p));
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: RiseTimeParams = RiseTimeParams {
        glitch_samples: 0,
        pretrigger_samples: 4,
        sample_period_s: 2.0,
        lo: 0.1,
        hi: 0.9,
    };

    #[test]
    fn a_small_pulse() {
        // baseline 0 (window 0, 0, 0, 0); peak 100 at index 8; y < 10 up to index 5 (value 5), y < 90 up to index 7 (value 60)
        let t = [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 30.0, 60.0, 100.0, 40.0];
        assert_eq!(rise_time_one(&t, &P), (7 - 5) as f64 * 2.0);
    }

    #[test]
    fn no_positive_peak_or_no_quiet_level_gives_nan() {
        assert!(rise_time_one(&[0.0; 10], &P).is_nan()); // amp is 0
        let starts_high = [0.0, 0.0, 0.0, 0.0, 100.0, 50.0, 20.0, 5.0]; // the peak is the first sample after the window: nothing below 10 % before it but the window
        assert_eq!(rise_time_one(&starts_high, &P), 0.0); // i_lo = i_hi = 3: the window is below both levels
        let peak_first = [100.0, 0.0, 0.0, 0.0, 0.0, 0.0];
        assert!(rise_time_one(&peak_first, &P).is_nan()); // the peak at index 0: nothing before it
    }

    #[test]
    fn the_first_of_equal_peaks_wins() {
        let t = [0.0, 0.0, 0.0, 0.0, 5.0, 100.0, 100.0, 20.0];
        // peak at index 5: y < 10 up to index 4, y < 90 up to index 4
        assert_eq!(rise_time_one(&t, &P), 0.0);
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |g, t, s, lo, hi| {
            problem(
                10,
                &RiseTimeParams {
                    glitch_samples: g,
                    pretrigger_samples: t,
                    sample_period_s: s,
                    lo,
                    hi,
                },
            )
        };
        assert_eq!(
            bad(5, 5, 1.0, 0.1, 0.9).unwrap(),
            "glitch_samples (5) must be smaller than pretrigger_samples (5)"
        );
        assert_eq!(
            bad(0, 11, 1.0, 0.1, 0.9).unwrap(),
            "pretrigger_samples (11) is longer than the trace (10 samples)"
        );
        assert_eq!(bad(0, 5, 0.0, 0.1, 0.9).unwrap(), "sample_period_s must be positive");
        for (lo, hi) in [
            (0.9, 0.1),
            (-0.1, 0.9),
            (0.1, 1.5),
            (f64::NAN, 0.9),
            (0.1, f64::NAN),
            (0.5, 0.5),
        ] {
            assert_eq!(bad(0, 5, 1.0, lo, hi).unwrap(), "lo and hi must satisfy 0 <= lo < hi <= 1");
        }
        assert!(bad(0, 5, 1.0, 0.0, 1.0).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 12;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 23) as f64).collect();
        let mut out = vec![0.0; 3];
        rise_time_many(&traces, n, &P, &mut out);
        for k in 0..3 {
            let one = rise_time_one(&traces[k * n..(k + 1) * n], &P);
            assert!(out[k] == one || (out[k].is_nan() && one.is_nan()));
        }
    }
}
