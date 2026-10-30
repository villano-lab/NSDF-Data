//! Zero-phase Butterworth low-pass filter of a trace (a transform: the result is a trace of the same length), made with the FFT.
//!
//! The Python mirror is `python/goldsluice/reference/lowpass.py` (a numpy *reference*, not in the kernel subset; see `PORTING.md`); the
//! two agree to rounding (`ATOL` in the mirror). The recipe is that of `goldpan.algorithms.lowpass`. For one trace `x` of `n` samples
//! and `dt = sample_period_s`:
//! * `pad = min(n - 1, 3 * round(1 / (cutoff_hz * dt)) + 1)` with `round(v) = floor(v + 0.5)` (half up, as in the mirror: Python's own
//!   `round` is half to even and Rust's is half away from zero);
//! * both ends are extended by `pad` samples with odd symmetry about the end points, giving `N = n + 2 * pad` samples;
//! * the spectrum of the extension is multiplied by `1 / (1 + (f / cutoff_hz)^(2 * order))`, `f = min(k, N - k) / (N * dt)` for bin
//!   `k` (the response is symmetric, so the whole complex transform is multiplied, not only its half);
//! * the result is the middle `n` samples of the inverse transform (divided by `N`).
//!
//! The transform plans and the response are made once per call (they depend only on `N`), not once per trace.

use rayon::prelude::*;
use rustfft::num_complex::Complex;
use rustfft::{Fft, FftPlanner};
use std::sync::Arc;

#[derive(Clone, Copy, Debug)]
pub struct LowpassParams {
    pub cutoff_hz: f64,
    pub order: i64,
    pub sample_period_s: f64,
}

/// The reason the parameters do not fit a trace of `n_samples`, or `None` if they do. The message is the same as in Python.
pub fn problem(n_samples: usize, p: &LowpassParams) -> Option<String> {
    if p.sample_period_s.is_nan() || p.sample_period_s <= 0.0 {
        return Some("sample_period_s must be positive".to_string());
    }
    if p.cutoff_hz.is_nan() || p.cutoff_hz <= 0.0 {
        return Some("cutoff_hz must be positive".to_string());
    }
    if p.cutoff_hz >= 0.5 / p.sample_period_s {
        return Some("cutoff_hz must be below the Nyquist frequency, half the sampling frequency".to_string());
    }
    if p.order < 1 {
        return Some("order must be at least 1".to_string());
    }
    if n_samples < 2 {
        return Some(format!("a trace needs at least 2 samples ({} given)", n_samples));
    }
    None
}

/// Everything that depends only on the parameters and the trace length: the two transforms and the response of every bin.
pub struct Plan {
    n: usize,
    pad: usize,
    len: usize,
    forward: Arc<dyn Fft<f64>>,
    inverse: Arc<dyn Fft<f64>>,
    response: Vec<f64>,
    scratch_len: usize,
}

impl Plan {
    /// The parameters must already pass `problem` for `n_samples`.
    pub fn new(n_samples: usize, p: &LowpassParams) -> Plan {
        let n = n_samples;
        let pad = (n - 1).min(3 * (1.0 / (p.cutoff_hz * p.sample_period_s) + 0.5).floor() as usize + 1);
        let len = n + 2 * pad;
        let mut planner = FftPlanner::<f64>::new();
        let forward = planner.plan_fft_forward(len);
        let inverse = planner.plan_fft_inverse(len);
        let exponent = 2.0 * p.order as f64;
        let response = (0..len)
            .map(|k| {
                let f = k.min(len - k) as f64 / (len as f64 * p.sample_period_s);
                1.0 / (1.0 + (f / p.cutoff_hz).powf(exponent))
            })
            .collect();
        let scratch_len = forward.get_inplace_scratch_len().max(inverse.get_inplace_scratch_len());
        Plan {
            n,
            pad,
            len,
            forward,
            inverse,
            response,
            scratch_len,
        }
    }

    /// Buffers for one thread: the extended trace, and the scratch space of the transforms.
    pub fn buffers(&self) -> (Vec<Complex<f64>>, Vec<Complex<f64>>) {
        (
            vec![Complex::new(0.0, 0.0); self.len],
            vec![Complex::new(0.0, 0.0); self.scratch_len],
        )
    }

    /// Filter one trace (of the length the plan was made for) into `out`.
    pub fn apply(&self, trace: &[f64], out: &mut [f64], buf: &mut [Complex<f64>], scratch: &mut [Complex<f64>]) {
        let (n, pad, len) = (self.n, self.pad, self.len);
        for j in 0..pad {
            buf[j] = Complex::new(2.0 * trace[0] - trace[pad - j], 0.0);
            buf[pad + n + j] = Complex::new(2.0 * trace[n - 1] - trace[n - 2 - j], 0.0);
        }
        for (b, &v) in buf[pad..pad + n].iter_mut().zip(trace) {
            *b = Complex::new(v, 0.0);
        }
        self.forward.process_with_scratch(buf, scratch);
        for (b, &r) in buf.iter_mut().zip(&self.response) {
            *b *= r;
        }
        self.inverse.process_with_scratch(buf, scratch);
        let scale = 1.0 / len as f64;
        for (o, b) in out.iter_mut().zip(&buf[pad..pad + n]) {
            *o = b.re * scale;
        }
    }
}

/// Filter one trace; builds a plan for it, so use `lowpass_many` for a block. The parameters must already pass `problem`.
pub fn lowpass_one(trace: &[f64], p: &LowpassParams, out: &mut [f64]) {
    let plan = Plan::new(trace.len(), p);
    let (mut buf, mut scratch) = plan.buffers();
    plan.apply(trace, out, &mut buf, &mut scratch);
}

/// Every trace of a row-major block of `n_samples`-long traces, in parallel over traces. `out` has the shape of `traces`.
pub fn lowpass_many(traces: &[f64], n_samples: usize, p: &LowpassParams, out: &mut [f64]) {
    let plan = Plan::new(n_samples, p);
    traces.par_chunks(n_samples).zip(out.par_chunks_mut(n_samples)).for_each_init(
        || plan.buffers(),
        |(buf, scratch), (trace, o)| plan.apply(trace, o, buf, scratch),
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    const P: LowpassParams = LowpassParams {
        cutoff_hz: 0.1,
        order: 20,
        sample_period_s: 1.0,
    };

    #[test]
    fn two_samples_by_hand() {
        // n = 2 gives pad = 1: the extension of [1, 3] is [2*1-3, 1, 3, 2*3-1] = [-1, 1, 3, 5], N = 4. The bin k = 1 is at f = 0.25
        // (2.5 cutoffs), whose response is 1 / (1 + 2.5^40), about 1e-16, and k = 2 is at the Nyquist frequency (even smaller): only the
        // mean of the extension, 2, survives
        let mut o = [0.0; 2];
        lowpass_one(&[1.0, 3.0], &P, &mut o);
        assert!((o[0] - 2.0).abs() < 1e-9 && (o[1] - 2.0).abs() < 1e-9, "{o:?}");
    }

    #[test]
    fn a_constant_trace_stays_constant() {
        let p = LowpassParams {
            cutoff_hz: 0.05,
            order: 4,
            sample_period_s: 1.0,
        };
        let t = [7.0; 50];
        let mut o = [0.0; 50];
        lowpass_one(&t, &p, &mut o);
        for v in o {
            assert!((v - 7.0).abs() < 1e-12, "{v}");
        }
    }

    #[test]
    fn it_equals_a_direct_transform_with_the_same_recipe() {
        // pad = 3 * round(1 / 0.1) + 1 = 31 is limited by the trace to n - 1 = 11: the extension of 12 samples to 34
        let p = LowpassParams {
            cutoff_hz: 0.1,
            order: 2,
            sample_period_s: 1.0,
        };
        let t = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0];
        let (n, pad) = (t.len(), t.len() - 1);
        let mut ext = Vec::new();
        for j in 0..pad {
            ext.push(2.0 * t[0] - t[pad - j]);
        }
        ext.extend_from_slice(&t);
        for j in 0..pad {
            ext.push(2.0 * t[n - 1] - t[n - 2 - j]);
        }
        let len = ext.len();
        let tau = std::f64::consts::TAU;
        let mut expect = vec![0.0; n];
        let response: Vec<f64> = (0..len)
            .map(|k| 1.0 / (1.0 + (k.min(len - k) as f64 / len as f64 / 0.1).powi(4)))
            .collect();
        for (m, e) in expect.iter_mut().enumerate() {
            let at = pad + m;
            let mut s = 0.0;
            for (k, &r) in response.iter().enumerate() {
                let (mut re, mut im) = (0.0, 0.0);
                for (j, &x) in ext.iter().enumerate() {
                    let a = -tau * (k * j % len) as f64 / len as f64;
                    re += x * a.cos();
                    im += x * a.sin();
                }
                let b = tau * (k * at % len) as f64 / len as f64;
                s += r * (re * b.cos() - im * b.sin());
            }
            *e = s / len as f64;
        }
        let mut o = vec![0.0; n];
        lowpass_one(&t, &p, &mut o);
        for (a, b) in o.iter().zip(&expect) {
            assert!((a - b).abs() < 1e-10, "{a} {b}");
        }
    }

    #[test]
    fn the_parameters_that_do_not_fit_are_named() {
        let with = |c, o, d| LowpassParams {
            cutoff_hz: c,
            order: o,
            sample_period_s: d,
        };
        assert_eq!(problem(8, &with(1.0, 1, 0.0)).unwrap(), "sample_period_s must be positive");
        assert_eq!(problem(8, &with(0.0, 1, 1.0)).unwrap(), "cutoff_hz must be positive");
        assert_eq!(
            problem(8, &with(0.5, 1, 1.0)).unwrap(),
            "cutoff_hz must be below the Nyquist frequency, half the sampling frequency"
        );
        assert_eq!(problem(8, &with(0.1, 0, 1.0)).unwrap(), "order must be at least 1");
        assert_eq!(problem(1, &P).unwrap(), "a trace needs at least 2 samples (1 given)");
        assert!(problem(2, &P).is_none());
    }

    #[test]
    fn many_traces_equal_one_by_one() {
        let n = 40;
        let p = LowpassParams {
            cutoff_hz: 0.1,
            order: 3,
            sample_period_s: 1.0,
        };
        let traces: Vec<f64> = (0..3 * n).map(|i| ((i * 37) % 11) as f64).collect();
        let mut out = vec![0.0; 3 * n];
        lowpass_many(&traces, n, &p, &mut out);
        for k in 0..3 {
            let mut one = vec![0.0; n];
            lowpass_one(&traces[k * n..(k + 1) * n], &p, &mut one);
            assert_eq!(&out[k * n..(k + 1) * n], &one[..]);
        }
    }
}
