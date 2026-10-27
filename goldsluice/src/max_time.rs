//! Time of the largest sample of a trace, from the start of the trace (s). Python mirror: `python/goldsluice/reference/max_time.py`.

use rayon::prelude::*;

#[derive(Clone, Copy, Debug)]
pub struct MaxTimeParams {
    pub sample_period_s: f64,
}

pub fn problem(_n_samples: usize, p: &MaxTimeParams) -> Option<String> {
    if p.sample_period_s.is_nan() || p.sample_period_s <= 0.0 {
        return Some("sample_period_s must be positive".to_string());
    }
    None
}

/// The first of equal maxima wins, as in numpy's `argmax`.
pub fn max_time_one(trace: &[f64], p: &MaxTimeParams) -> f64 {
    let mut best = 0;
    for i in 1..trace.len() {
        if trace[i] > trace[best] {
            best = i;
        }
    }
    best as f64 * p.sample_period_s
}

pub fn max_time_many(traces: &[f64], n_samples: usize, p: &MaxTimeParams, out: &mut [f64]) {
    traces
        .par_chunks(n_samples)
        .zip(out.par_iter_mut())
        .for_each(|(trace, o)| *o = max_time_one(trace, p));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_first_maximum_wins() {
        let p = MaxTimeParams { sample_period_s: 0.5 };
        assert_eq!(max_time_one(&[1.0, 5.0, 2.0, 5.0], &p), 0.5);
        assert_eq!(max_time_one(&[9.0, 5.0], &p), 0.0);
    }
}
