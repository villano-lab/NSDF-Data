"""Batch mode with a step that names its sources (definition format 7): different processing for different sources."""
import json

import pytest

pytest.importorskip("goldpan")
pytest.importorskip("pyarrow")

from goldpan.dataset import Dataset

from goldsluice import batch

from test_batch import AMPS, make_raw

PEAK = ('[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n{extra}[processing.params]\n'
        f'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\namps_per_adc = {AMPS}\n')
BASELINE = ('[[processing]]\nalgorithm = "baseline"\nchannels = "role:phonon"\n{extra}[processing.params]\n'
            'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = {pre}\n')


def write_two(path, files, *steps):
    paths = [json.dumps(str(f)) for f in files]
    sources = "".join(f'[[sources]]\nname = "{n}"\nformat = "parquet"\npaths = [{p}]\ndetector = "TOY"\n\n' for n, p in zip(("a", "b"), paths))
    path.write_text('[dataset]\nname = "toy"\noutput = "out"\n\n' + sources + "\n".join(steps), encoding="utf-8")
    return path


@pytest.fixture
def two(tmp_path):
    files = make_raw(tmp_path / "raw", dumps=(("S1", "F0001", 4), ("S2", "F0001", 3)))
    return tmp_path, files


def used(report):
    return {f.path.split("/")[-1].split("\\")[-1]: set(f.compute_s) for f in report.files}


def test_each_source_runs_only_the_steps_that_apply_to_it(two):
    tmp, files = two
    spec = write_two(tmp / "toy.dataset.toml", files, PEAK.format(extra='sources = ["a"]\n'), BASELINE.format(extra='sources = ["b"]\n', pre=1000))
    report = batch.run(spec, progress=None)
    assert used(report) == {"S1_F0001.parquet": {"peak"}, "S2_F0001.parquet": {"baseline"}}
    q = Dataset.open(spec).processed().quantities
    rows = {name: q[q["series"] == name]["A"].to_list() for name in ("S1", "S2")}
    assert set(rows["S1"][0]) == {"adc_max", "current_max"}                                         # S1 got the peak and nothing else
    assert set(rows["S2"][0]) == {"baseline_mean", "baseline_std"}                                  # S2 got the baseline and nothing else


def test_a_step_without_sources_still_runs_on_all_of_them(two):
    tmp, files = two
    spec = write_two(tmp / "toy.dataset.toml", files, PEAK.format(extra=""))
    assert used(batch.run(spec, progress=None)) == {"S1_F0001.parquet": {"peak"}, "S2_F0001.parquet": {"peak"}}


def test_changing_a_step_of_one_source_redoes_only_that_source(two):
    tmp, files = two
    spec = write_two(tmp / "toy.dataset.toml", files, PEAK.format(extra='sources = ["a"]\n'), BASELINE.format(extra='sources = ["b"]\n', pre=1000))
    batch.run(spec, progress=None)
    assert all(f.skipped for f in batch.run(spec, progress=None).files)
    write_two(spec, files, PEAK.format(extra='sources = ["a"]\n'), BASELINE.format(extra='sources = ["b"]\n', pre=900))
    again = batch.run(spec, progress=None)
    assert {f.path.split("/")[-1].split("\\")[-1]: f.skipped for f in again.files} == {"S1_F0001.parquet": True, "S2_F0001.parquet": False}


def test_a_source_that_no_step_runs_on_is_refused(two):
    tmp, files = two
    spec = write_two(tmp / "toy.dataset.toml", files, PEAK.format(extra='sources = ["a"]\n'))
    with pytest.raises(ValueError, match="no step runs on the source 'b'"):
        batch.check(spec)
