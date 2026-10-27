//! `cargo bench` times the kernels alone (no Python, no copying): the floor that the Python wrapper adds its overhead to.

use _core::peak::{PeakParams, peak_many, peak_one};
use criterion::{Criterion, Throughput, criterion_group, criterion_main};
use std::hint::black_box;

fn traces(n_events: usize, n_samples: usize) -> Vec<f64> {
    (0..n_events * n_samples).map(|i| ((i * 2654435761) % 4096) as f64).collect()
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
}

criterion_group!(benches, bench_peak);
criterion_main!(benches);
