//! goldsluice: fast pulse-reduction kernels. The Python package `goldsluice` wraps this module as `goldsluice._core`.
//!
//! One `#[pyfunction]` per algorithm, named like the algorithm and taking the same keyword arguments as its Python mirror.

pub mod baseline;
pub mod max_time;
pub mod peak;

use numpy::{IntoPyArray, PyArray1, PyReadonlyArray2, PyUntypedArrayMethods};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

type Pair<'py> = (Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>);

/// peak(traces, *, glitch_samples, pretrigger_samples, amps_per_adc) -> (adc_max, current_max)
///
/// `traces` is a C-contiguous float64 array of shape (n_events, n_samples); the result is one value per event.
#[pyfunction]
#[pyo3(name = "peak", signature = (traces, *, glitch_samples, pretrigger_samples, amps_per_adc))]
fn peak_py<'py>(
    py: Python<'py>,
    traces: PyReadonlyArray2<'py, f64>,
    glitch_samples: usize,
    pretrigger_samples: usize,
    amps_per_adc: f64,
) -> PyResult<Pair<'py>> {
    let p = peak::PeakParams {
        glitch_samples,
        pretrigger_samples,
        amps_per_adc,
    };
    let [n_events, n_samples] = *traces.shape() else {
        unreachable!("a 2-D array has two axes")
    };
    if let Some(why) = peak::problem(n_samples, &p) {
        return Err(PyValueError::new_err(why));
    }
    let data = traces
        .as_slice()
        .map_err(|_| PyValueError::new_err("traces must be C-contiguous (use numpy.ascontiguousarray)"))?;
    let mut adc = vec![0.0; n_events];
    let mut current = vec![0.0; n_events];
    py.detach(|| peak::peak_many(data, n_samples, &p, &mut adc, &mut current));
    Ok((adc.into_pyarray(py), current.into_pyarray(py)))
}

/// baseline(traces, *, glitch_samples, pretrigger_samples) -> (baseline_mean, baseline_std)
///
/// The mean and the standard deviation of `traces[:, glitch_samples:pretrigger_samples]`, one value per event.
#[pyfunction]
#[pyo3(name = "baseline", signature = (traces, *, glitch_samples, pretrigger_samples))]
fn baseline_py<'py>(
    py: Python<'py>,
    traces: PyReadonlyArray2<'py, f64>,
    glitch_samples: usize,
    pretrigger_samples: usize,
) -> PyResult<Pair<'py>> {
    let p = baseline::BaselineParams {
        glitch_samples,
        pretrigger_samples,
    };
    let [n_events, n_samples] = *traces.shape() else {
        unreachable!("a 2-D array has two axes")
    };
    if let Some(why) = baseline::problem(n_samples, &p) {
        return Err(PyValueError::new_err(why));
    }
    let data = traces
        .as_slice()
        .map_err(|_| PyValueError::new_err("traces must be C-contiguous (use numpy.ascontiguousarray)"))?;
    let mut mean = vec![0.0; n_events];
    let mut std = vec![0.0; n_events];
    py.detach(|| baseline::baseline_many(data, n_samples, &p, &mut mean, &mut std));
    Ok((mean.into_pyarray(py), std.into_pyarray(py)))
}

/// max_time(traces, *, sample_period_s) -> (max_time_s,)
#[pyfunction]
#[pyo3(name = "max_time", signature = (traces, *, sample_period_s))]
fn max_time_py<'py>(
    py: Python<'py>,
    traces: PyReadonlyArray2<'py, f64>,
    sample_period_s: f64,
) -> PyResult<(Bound<'py, PyArray1<f64>>,)> {
    let p = max_time::MaxTimeParams { sample_period_s };
    let [n_events, n_samples] = *traces.shape() else {
        unreachable!("a 2-D array has two axes")
    };
    if let Some(why) = max_time::problem(n_samples, &p) {
        return Err(PyValueError::new_err(why));
    }
    let data = traces
        .as_slice()
        .map_err(|_| PyValueError::new_err("traces must be C-contiguous (use numpy.ascontiguousarray)"))?;
    let mut out = vec![0.0; n_events];
    py.detach(|| max_time::max_time_many(data, n_samples, &p, &mut out));
    Ok((out.into_pyarray(py),))
}

#[pymodule(name = "_core")]
fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(peak_py, m)?)?;
    m.add_function(wrap_pyfunction!(max_time_py, m)?)?;
    m.add_function(wrap_pyfunction!(baseline_py, m)?)?;
    Ok(())
}
