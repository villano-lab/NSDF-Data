"""Batch mode: a dataset definition in, processed quantities out, read back by goldpan."""
import json

import numpy as np
import pytest

pytest.importorskip("goldpan")
pytest.importorskip("pyarrow")
import awkward as ak

from goldpan.adapters import parquet
from goldpan.config import DCRC_RUN76
from goldpan.data import ChannelInfo, Detector, Events, Readout
from goldpan.dataset import Dataset

from goldsluice import batch
from goldsluice.__main__ import main

N_SAMPLES = 1500
AMPS = 1.5e-9


def make_raw(root, dumps=(("S1", "F0001", 7), ("S1", "F0002", 5)), seed=0):
    """A small raw dataset in the native format: one file per dump, three channels (two phonon, one charge)."""
    rng = np.random.default_rng(seed)
    det = Detector("TOY", (ChannelInfo("A", role="phonon"), ChannelInfo("B", role="phonon"), ChannelInfo("Q", role="charge")),
                   Readout.single(N_SAMPLES, DCRC_RUN76))
    files = []
    for series, dump, n in dumps:
        traces = {c: rng.normal(2000.0, 5.0, size=(n, N_SAMPLES)) for c in "ABQ"}
        traces["A"][:, 1200:1300] += 3000.0
        ev = Events.from_arrays(det, traces, series=series, dump=dump)
        parquet.write(ev, root)
        files.append(root / "TOY" / f"{series}_{dump}.parquet")
    return files


def write_spec(path, files, *, params=None, steps=None, readout=""):
    params = params or ('glitch_samples = "@readout.glitch_samples"\n'
                        'pretrigger_samples = "@readout.pretrigger_samples"\n'
                        f"amps_per_adc = {AMPS}\n")
    steps = steps or f'[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n[processing.params]\n{params}'
    paths = ", ".join(json.dumps(str(f)) for f in files)
    path.write_text(f'[dataset]\nname = "toy"\noutput = "out"\n\n[[sources]]\nname = "raw"\nformat = "parquet"\n'
                    f'paths = [{paths}]\ndetector = "TOY"\n{readout}\n{steps}\n', encoding="utf-8")
    return path


@pytest.fixture
def setup(tmp_path):
    files = make_raw(tmp_path / "raw")
    return tmp_path, files, write_spec(tmp_path / "toy.dataset.toml", files)


def test_run_writes_the_quantities_of_every_phonon_channel_and_goldpan_reads_them(setup):
    tmp, files, spec = setup
    report = batch.run(spec, progress=None)
    assert [f.skipped for f in report.files] == [False, False] and report.n_events == 12
    ds = Dataset.open(spec)
    q = ds.processed()
    assert q.n_events == 12 and not q.traces
    assert set(ak.fields(q.quantities)) == {"series", "dump", "event", "A", "B"}          # the charge channel is not processed
    assert ak.fields(q.quantities["A"]) == ["adc_max", "current_max"]
    raw = Events.concatenate(*[parquet.read(f) for f in files])
    for ch in "AB":
        np.testing.assert_allclose(q.quantities[ch]["adc_max"], raw.trace(ch).max(axis=1))
        baseline = raw.trace(ch)[:, 10:1000].mean(axis=1)
        np.testing.assert_allclose(q.quantities[ch]["current_max"], (raw.trace(ch).max(axis=1) - baseline) * AMPS, rtol=1e-12)
    meta = parquet.read(tmp / "out").meta["goldsluice"]
    assert meta["steps"][0]["algorithm"] == "peak" and meta["backend"] == "rust" and "compute.peak" in meta["timing_s"]


def test_dataset_read_gives_the_pulses_with_the_processed_quantities(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    ev = Dataset.open(spec).read()
    assert ev.n_events == 12 and sorted(ev.traces) == [("A", "main"), ("B", "main"), ("Q", "main")]
    np.testing.assert_array_equal(ev.quantities["A"]["adc_max"], ev.trace("A").max(axis=1))
    pulses_only = Dataset.open(spec).read(processed=False)
    assert "A" not in ak.fields(pulses_only.quantities)


def test_reading_before_the_batch_run_says_what_to_do(setup):
    _, _, spec = setup
    with pytest.raises(FileNotFoundError, match="python -m goldsluice run"):
        Dataset.open(spec).processed()


def test_a_second_run_skips_unchanged_files_and_a_changed_parameter_redoes_them(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    again = batch.run(spec, progress=None)
    assert all(f.skipped for f in again.files) and again.n_events == 0
    assert not any(f.skipped for f in batch.run(spec, force=True, progress=None).files)
    write_spec(spec, files, params='glitch_samples = 20\npretrigger_samples = 1000\n' f"amps_per_adc = {AMPS}\n")
    assert not any(f.skipped for f in batch.run(spec, progress=None).files)
    q = Dataset.open(spec).processed()
    raw = parquet.read(files[0])
    np.testing.assert_allclose(q.quantities["A"]["current_max"][:7],
                               (raw.trace("A").max(axis=1) - raw.trace("A")[:, 20:1000].mean(axis=1)) * AMPS, rtol=1e-12)


def test_a_changed_raw_file_is_processed_again(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    make_raw(tmp / "raw", dumps=(("S1", "F0001", 9),), seed=3)                 # the first dump is rewritten with more events
    done = batch.run(spec, progress=None)
    assert [f.skipped for f in done.files] == [False, True]
    assert Dataset.open(spec).processed().n_events == 14


def test_chunks_give_the_same_result_as_one_piece(setup):
    tmp, files, spec = setup
    batch.run(spec, chunk=1000, progress=None)
    whole = Dataset.open(spec).processed().quantities.to_list()
    batch.run(spec, chunk=3, force=True, progress=None)
    assert Dataset.open(spec).processed().quantities.to_list() == whole


def test_the_python_backend_gives_the_same_numbers(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    rust = Dataset.open(spec).processed().quantities
    batch.run(spec, backend="python", force=True, progress=None)
    py = Dataset.open(spec).processed().quantities
    for ch in "AB":
        for name in ("adc_max", "current_max"):
            np.testing.assert_allclose(ak.to_numpy(py[ch][name]), ak.to_numpy(rust[ch][name]), rtol=1e-12)


def test_the_report_has_the_timing_of_every_phase(setup):
    _, _, spec = setup
    text = str(batch.run(spec, progress=None))
    for word in ("2 file(s) processed", "read", "compute", "(peak)", "write", "events/s"):
        assert word in text


def test_two_steps_may_not_give_the_same_quantity_to_a_channel(setup):
    tmp, files, _ = setup
    step = ('[[processing]]\nalgorithm = "peak"\nchannels = "all"\n[processing.params]\nglitch_samples = 1\n'
            'pretrigger_samples = 100\namps_per_adc = 1.0\n') * 2
    spec = write_spec(tmp / "dup.dataset.toml", files, steps=step.replace("[[processing]]", "\n[[processing]]"))
    with pytest.raises(ValueError, match="from two steps"):
        batch.run(spec, progress=None)


@pytest.mark.parametrize("edit, message", [
    ('algorithm = "peak"', 'algorithm = "nosuch"'),
])
def test_check_refuses_an_unknown_algorithm(setup, edit, message):
    tmp, files, spec = setup
    spec.write_text(spec.read_text(encoding="utf-8").replace(edit, message), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown algorithm 'nosuch'"):
        batch.check(spec)


def test_a_missing_algorithm_parameter_is_an_error_not_a_default(setup):
    tmp, files, _ = setup
    spec = write_spec(tmp / "nop.dataset.toml", files, params="glitch_samples = 1\npretrigger_samples = 100\n")
    with pytest.raises(TypeError, match="amps_per_adc"):
        batch.run(spec, progress=None)


def test_command_line(setup, capsys):
    tmp, files, spec = setup
    assert main(["algorithms"]) == 0 and "peak: outputs ['adc_max', 'current_max']" in capsys.readouterr().out
    assert main(["check", str(spec)]) == 0 and "2 raw file(s)" in capsys.readouterr().out
    assert main(["run", str(spec), "--chunk", "4"]) == 0
    out = capsys.readouterr().out
    assert "processed" in out and "events/s" in out
    assert main(["run", str(spec)]) == 0 and "2 unchanged" in capsys.readouterr().out
    assert main(["check", str(tmp / "missing.toml")]) == 1 and "error:" in capsys.readouterr().err


def test_command_line_reports_a_missing_parameter_as_an_error_not_a_traceback(setup, capsys):
    tmp, files, _ = setup
    spec = write_spec(tmp / "nop.dataset.toml", files, params="glitch_samples = 1\npretrigger_samples = 100\n")
    assert main(["run", str(spec)]) == 1
    assert "amps_per_adc" in capsys.readouterr().err
