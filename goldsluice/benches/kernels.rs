//! `cargo bench` times the kernels alone (no Python, no copying): the floor that the Python wrapper adds its overhead to.

use _core::baseline::{BaselineParams, baseline_many, baseline_one};
use _core::excursion::{ExcursionParams, excursion_many, excursion_one};
use _core::integral::{IntegralParams, integral_many, integral_one};
use _core::max_time::{MaxTimeParams, max_time_many};
use _core::peak::{PeakParams, peak_many, peak_one};
use _core::rise_crossing::{RiseCrossingParams, rise_crossing_many, rise_crossing_one};
use _core::rise_time::{RiseTimeParams, rise_time_many, rise_time_one};
use criterion::{Criterion, Throughput, criterion_group, criterion_main};
use std::hint::black_box;

fn traces(n_events: usize, n_samples: usize) -> Vec<f64> {
    (0..n_events * n_samples).map(|i| ((i * 2654435761) % 4096) as f64).collect()
}

/// Traces with a pulse: a baseline of 3000 with a little scatter, and a pulse of 1000 rising over 8 samples at sample 500, then decaying.
fn pulse_traces(n_events: usize, n_samples: usize) -> Vec<f64> {
    (0..n_events * n_samples)
        .map(|i| {
            let s = i % n_samples;
            let noise = ((i * 2654435761) % 7) as f64 - 3.0;
            let pulse = if s < 500 {
                0.0
            } else if s < 508 {
                (s - 500) as f64 / 8.0
            } else {
                (-((s - 508) as f64) / 300.0).exp()
            };
            3000.0 + noise + 1000.0 * pulse
        })
        .collect()
}

fn bench_peak(c: &mut Criterion) {
    // Run 76: 4096 samples per trace, a 1000-sample pretrigger window, 10 glitch samples.
    let p = PeakParams {
        glitch_samples: 10,
        pretrigger_samples: 1000,
        amps_per_adc: 1e-9,
    };
    let n_samples = 4096;
    let one = traces(1, n_samples);
    c.bench_function("peak_one, 4096 samples", |b| b.iter(|| peak_one(black_box(&one), &p)));

    let n_events = 10_000;
    let many = traces(n_events, n_samples);
    let (mut a, mut cur) = (vec![0.0; n_events], vec![0.0; n_events]);
    let mut g = c.benchmark_group("peak_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |b| {
        b.iter(|| peak_many(black_box(&many), n_samples, &p, &mut a, &mut cur))
    });
    g.finish();

    let t = MaxTimeParams { sample_period_s: 0.8e-6 };
    let mut out = vec![0.0; n_events];
    let mut g = c.benchmark_group("max_time_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |b| {
        b.iter(|| max_time_many(black_box(&many), n_samples, &t, &mut out))
    });
    g.finish();

    // the baseline of the Run 76 window (500 samples after 10 glitch samples)
    let b = BaselineParams {
        glitch_samples: 10,
        pretrigger_samples: 500,
    };
    c.bench_function("baseline_one, 4096 samples", |bch| {
        bch.iter(|| baseline_one(black_box(&one), &b))
    });
    let mut sd = vec![0.0; n_events];
    let mut g = c.benchmark_group("baseline_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |bch| {
        bch.iter(|| baseline_many(black_box(&many), n_samples, &b, &mut a, &mut sd))
    });
    g.finish();

    // the integral over the whole trace, and the excursion after the window (Run 76: 500-sample window)
    let i = IntegralParams {
        glitch_samples: 10,
        pretrigger_samples: 500,
        sample_period_s: 0.8e-6,
    };
    c.bench_function("integral_one, 4096 samples", |bch| {
        bch.iter(|| integral_one(black_box(&one), &i))
    });
    let mut g = c.benchmark_group("integral_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |bch| {
        bch.iter(|| integral_many(black_box(&many), n_samples, &i, &mut sd))
    });
    g.finish();

    let x = ExcursionParams {
        glitch_samples: 10,
        pretrigger_samples: 500,
    };
    c.bench_function("excursion_one, 4096 samples", |bch| {
        bch.iter(|| excursion_one(black_box(&one), &x))
    });
    let mut g = c.benchmark_group("excursion_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |bch| {
        bch.iter(|| excursion_many(black_box(&many), n_samples, &x, &mut a, &mut cur))
    });
    g.finish();

    // the 10-90 % rise time of a trace with a pulse at sample 500 (the peak is early, so most of the trace is only read once)
    let r = RiseTimeParams {
        glitch_samples: 10,
        pretrigger_samples: 500,
        sample_period_s: 0.8e-6,
        lo: 0.1,
        hi: 0.9,
    };
    let pulses_one = pulse_traces(1, n_samples);
    c.bench_function("rise_time_one, 4096 samples", |bch| {
        bch.iter(|| rise_time_one(black_box(&pulses_one), &r))
    });
    let pulses = pulse_traces(n_events, n_samples);
    let mut g = c.benchmark_group("rise_time_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |bch| {
        bch.iter(|| rise_time_many(black_box(&pulses), n_samples, &r, &mut sd))
    });
    g.finish();

    // the 20 % crossing time of the same traces (the same single pass as the rise time, with one level and an interpolation)
    let c20 = RiseCrossingParams {
        glitch_samples: 10,
        pretrigger_samples: 500,
        sample_period_s: 0.8e-6,
        fraction: 0.2,
    };
    c.bench_function("rise_crossing_one, 4096 samples", |bch| {
        bch.iter(|| rise_crossing_one(black_box(&pulses_one), &c20))
    });
    let mut g = c.benchmark_group("rise_crossing_many");
    g.throughput(Throughput::Elements(n_events as u64));
    g.bench_function("10000 traces x 4096 samples", |bch| {
        bch.iter(|| rise_crossing_many(black_box(&pulses), n_samples, &c20, &mut sd))
    });
    g.finish();
}

criterion_group!(benches, bench_peak);
criterion_main!(benches);
