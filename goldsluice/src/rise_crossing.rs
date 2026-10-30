//! Time at which the rising edge of the largest pulse of a trace crosses `fraction` of its height (s).
//!
//! The Python mirror is `python/goldsluice/reference/rise_crossing.py`; the two must agree (`tests/test_parity.py`).
//!
//! For one trace `x`: `baseline` = mean of `x[glitch_samples .. pretrigger_samples]`, `y[i] = x[i] - baseline`; the peak is the first
//! largest `y` over all samples, at `peak` with height `amp`; `level = fraction * amp`; `last` is the last `i <= peak` with
//! `y[i] < level`, or -1; the result is `(last + (level - y[last]) / (y[last + 1] - y[last])) * sample_period_s` (linear interpolation
//! between the two samples), and `nan` unless `amp > 0` and `last` was found.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct RiseCrossingParams {
    pub glitch_samples: usize,
    pub pretrigger_samples: usize,
    pub sample_period_s: f64,
    pub fraction: f64,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &RiseCrossingParams) -> Option<String> {
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
    if p.fraction.is_nan() || p.fraction < 0.0 || p.fraction > 1.0 {
        return Some("fraction must satisfy 0 <= fraction <= 1".to_string());
    }
    None
}

/// The crossing time of one trace. The parameters must already pass `problem`.
pub fn rise_crossing_one(trace: &[f64], p: &RiseCrossingParams) -> f64 {
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
    let level = p.fraction * amp;
    let mut last: i64 = -1;
    for (i, &v) in trace.iter().enumerate().take(peak + 1) {
        let y = v - baseline;
        if y < level {
            last = i as i64;
        }
    }
    if amp > 0.0 && last >= 0 {
        let k = last as usize;
        let y0 = trace[k] - baseline;
        let y1 = trace[k + 1] - baseline;
        (last as f64 + (level - y0) / (y1 - y0)) * p.sample_period_s
    } else {
        f64::NAN
    }
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` gets one value per trace.
pub fn rise_crossing_many(traces: &[f64], n_samples: usize, p: &RiseCrossingParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_iter_mut())
        .for_each(|(trace, o)| *o = rise_crossing_one(trace, p));
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: RiseCrossingParams = RiseCrossingParams {
        glitch_samples: 0,
        pretrigger_samples: 4,
        sample_period_s: 2.0,
        fraction: 0.2,
    };

    #[test]
    fn a_small_pulse_is_interpolated() {
        // baseline 0; peak 100 at index 8; the level is 20; the last sample below it is index 5 (value 5), the next is 30:
        // 5 + (20 - 5) / (30 - 5) = 5.6 samples, 11.2 s
        let t = [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 30.0, 60.0, 100.0, 40.0];
        let got = rise_crossing_one(&t, &P);
        assert!((got - 5.6 * 2.0).abs() < 1e-12, "{got}");
    }

    #[test]
    fn a_sample_exactly_on_the_level_gives_that_sample() {
        let t = [0.0, 0.0, 0.0, 0.0, 10.0, 20.0, 60.0, 100.0, 40.0];
        // the level is 20: index 4 (10) is the last below it, index 5 is exactly 20: 4 + (20 - 10) / (20 - 10) = 5
        assert_eq!(rise_crossing_one(&t, &P), 5.0 * 2.0);
    }

    #[test]
    fn no_positive_peak_or_nothing_below_the_level_gives_nan() {
        assert!(rise_crossing_one(&[0.0; 10], &P).is_nan()); // amp is 0
        let peak_first = [100.0, 0.0, 0.0, 0.0, 0.0, 0.0];
        assert!(rise_crossing_one(&peak_first, &P).is_nan()); // the peak at index 0: nothing before it
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let bad = |g, t, s, f| {
            problem(
                10,
                &RiseCrossingParams {
                    glitch_samples: g,
                    pretrigger_samples: t,
                    sample_period_s: s,
                    fraction: f,
                },
            )
        };
        assert_eq!(
            bad(5, 5, 1.0, 0.2).unwrap(),
            "glitch_samples (5) must be smaller than pretrigger_samples (5)"
        );
        assert_eq!(
            bad(0, 11, 1.0, 0.2).unwrap(),
            "pretrigger_samples (11) is longer than the trace (10 samples)"
        );
        assert_eq!(bad(0, 5, 0.0, 0.2).unwrap(), "sample_period_s must be positive");
        for f in [-0.1, 1.5, f64::NAN] {
            assert_eq!(bad(0, 5, 1.0, f).unwrap(), "fraction must satisfy 0 <= fraction <= 1");
        }
        assert!(bad(0, 5, 1.0, 0.0).is_none());
        assert!(bad(0, 5, 1.0, 1.0).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 12;
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 23) as f64).collect();
        let mut out = vec![0.0; 3];
        rise_crossing_many(&traces, n, &P, &mut out);
        for k in 0..3 {
            let one = rise_crossing_one(&traces[k * n..(k + 1) * n], &P);
            assert!(out[k] == one || (out[k].is_nan() && one.is_nan()));
        }
    }
}
