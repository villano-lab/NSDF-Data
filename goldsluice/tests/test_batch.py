"""Batch mode: a dataset definition in, processed quantities out, read back by goldpan."""
import json

import numpy as np
import pytest

pytest.importorskip("goldpan")
pytest.importorskip("pyarrow")
import awkward as ak

from goldpan.adapters import parquet
from goldpan.config import PulseConfig
from goldpan.data import ChannelInfo, Detector, Events, Readout
from goldpan.dataset import Dataset

from goldsluice import batch
from goldsluice.algorithms import ALGORITHMS
from goldsluice.__main__ import main

N_SAMPLES = 1500
READOUT = PulseConfig(pretrigger_samples=1000, glitch_samples=10, sample_period_s=0.8e-6)     # the pulse of the toy traces starts at sample 1200
AMPS = 1.5e-9


def make_raw(root, dumps=(("S1", "F0001", 7), ("S1", "F0002", 5)), seed=0, trigger_types=False):
    """A small raw dataset in the native format: one file per dump, three channels (two phonon, one charge)."""
    rng = np.random.default_rng(seed)
    det = Detector("TOY", (ChannelInfo("A", role="phonon"), ChannelInfo("B", role="phonon"), ChannelInfo("Q", role="charge")),
                   Readout.single(N_SAMPLES, READOUT))
    files = []
    for series, dump, n in dumps:
        traces = {c: rng.normal(2000.0, 5.0, size=(n, N_SAMPLES)) for c in "ABQ"}
        traces["A"][:, 1200:1300] += 3000.0
        labels = {"trigger_type": np.array(["Physics", "Unknown"] * n)[:n]} if trigger_types else None     # the label of the dump's .csv, as text
        ev = Events.from_arrays(det, traces, series=series, dump=dump, quantities=labels)
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


def test_a_new_revision_of_an_algorithm_the_definition_uses_redoes_the_files_and_no_other_change_does(setup, monkeypatch, capsys):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    assert all(f.skipped for f in batch.run(spec, progress=None).files)
    # what the definition does not use changes nothing: another algorithm fixed, and new versions of the packages
    monkeypatch.setattr(ALGORITHMS["baseline"], "REVISION", 2)
    monkeypatch.setattr(batch, "_versions", lambda: {"goldsluice": "9.9.9", "goldpan": "9.9.9"})
    assert all(f.skipped for f in batch.run(spec, progress=None).files)
    # the algorithm it uses was fixed: its outputs are redone, and then current again
    monkeypatch.setattr(ALGORITHMS["peak"], "REVISION", 2)
    assert not any(f.skipped for f in batch.run(spec).files)
    assert "algorithm peak revision 1 -> 2" in capsys.readouterr().out
    assert all(f.skipped for f in batch.run(spec, progress=None).files)


def test_a_new_revision_of_the_reader_redoes_the_files_made_with_it(setup, monkeypatch, capsys):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    from goldpan.adapters import parquet
    monkeypatch.setattr(parquet, "REVISION", 2)                                                  # the format of the toy dataset
    assert not any(f.skipped for f in batch.run(spec).files)
    assert "reader parquet revision 1 -> 2" in capsys.readouterr().out
    assert all(f.skipped for f in batch.run(spec, progress=None).files)


def test_a_ledger_without_revisions_counts_as_revision_1_if_it_has_versions_and_is_redone_once_if_it_has_neither(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    ledger = tmp / "out" / batch.LEDGER
    data = json.loads(ledger.read_text(encoding="utf-8"))
    for entry in data["files"].values():
        del entry["revisions"]                                                                   # written by the ledger that compared versions
    ledger.write_text(json.dumps(data), encoding="utf-8")
    assert all(f.skipped for f in batch.run(spec, progress=None).files)
    data = json.loads(ledger.read_text(encoding="utf-8"))
    for entry in data["files"].values():
        entry.pop("revisions", None)
        del entry["versions"]                                                                    # written before versions were recorded
    ledger.write_text(json.dumps(data), encoding="utf-8")
    assert not any(f.skipped for f in batch.run(spec, progress=None).files)
    assert all(f.skipped for f in batch.run(spec, progress=None).files)


def test_adding_a_step_to_the_definition_processes_the_files_again_because_the_definition_changed(setup):
    tmp, files, spec = setup
    batch.run(spec, progress=None)
    window = 'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\n'
    steps = ('[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n[processing.params]\n' + window + f"amps_per_adc = {AMPS}\n\n"
             '[[processing]]\nalgorithm = "baseline"\nchannels = "role:phonon"\n[processing.params]\n' + window)
    write_spec(spec, files, steps=steps)
    assert not any(f.skipped for f in batch.run(spec, progress=None).files)
    assert all(f.skipped for f in batch.run(spec, progress=None).files)


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


def test_a_batch_run_can_write_rq_style_root_files_with_our_names(tmp_path):
    uproot = pytest.importorskip("uproot")
    from goldpan.adapters import rq_root
    tmp = tmp_path                                                          # a series name is a number in an RQ file: not the toy S1
    files = make_raw(tmp / "raw", dumps=(("24260424_145101", "F0001", 7), ("24260424_145101", "F0002", 5)))
    spec = write_spec(tmp / "toy.dataset.toml", files)
    spec.write_text(spec.read_text(encoding="utf-8").replace('output = "out"', 'output = "out"\noutput_format = "root"\nroot_detector = 3'),
                    encoding="utf-8")
    report = batch.run(spec, progress=None)
    assert report.n_events == 12
    assert sorted(p.name for p in (tmp / "out").glob("*.root")) == ["24260424_145101_F0001.root", "24260424_145101_F0002.root"]
    t = rq_root.read(tmp / "out", detector=3)
    assert len(t) == 12 and "A_adc_max" in t.fields and "B_current_max" in t.fields and "Q_adc_max" not in t.fields
    raw = Events.concatenate(*[parquet.read(f) for f in files])
    np.testing.assert_allclose(ak.to_numpy(t["A_adc_max"]), raw.trace("A").max(axis=1))
    with uproot.open(tmp / "out" / "24260424_145101_F0001.root") as f:
        assert json.loads(str(f["infoDir/goldsluice"]))["steps"][0]["algorithm"] == "peak"          # the provenance travels
    assert [f.skipped for f in batch.run(spec, progress=None).files] == [True, True]                 # the ledger works for ROOT too
    with pytest.raises(ValueError, match="rq_root.read"):
        Dataset.open(spec).processed()


def test_what_the_adapter_knows_about_each_event_is_in_the_output_not_only_the_key(tmp_path):
    files = make_raw(tmp_path / "raw", trigger_types=True)
    spec = write_spec(tmp_path / "toy.dataset.toml", files)
    batch.run(spec, progress=None)
    q = Dataset.open(spec).processed().quantities
    assert set(ak.fields(q)) == {"series", "dump", "event", "trigger_type", "A", "B"}
    assert q["trigger_type"].to_list() == (["Physics", "Unknown"] * 7)[:7] + (["Physics", "Unknown"] * 5)[:5]     # verbatim, not interpreted


def test_a_batch_run_to_root_writes_the_trigger_type_as_a_number_in_the_event_tree(tmp_path):
    uproot = pytest.importorskip("uproot")
    from goldpan.adapters import rq_root
    files = make_raw(tmp_path / "raw", dumps=(("24260424_145101", "F0001", 7),), trigger_types=True)
    spec = write_spec(tmp_path / "toy.dataset.toml", files)
    spec.write_text(spec.read_text(encoding="utf-8").replace('output = "out"', 'output = "out"\noutput_format = "root"\nroot_detector = 3'),
                    encoding="utf-8")
    batch.run(spec, progress=None)
    t = rq_root.read(tmp_path / "out", detector=3)
    assert len(t) == 7 and "A_adc_max" in t.fields
    assert t["trigger_type"].to_list() == [{"Physics": 1, "Unknown": 0}[x] for x in (["Physics", "Unknown"] * 7)[:7]]
    with uproot.open(tmp_path / "out" / "24260424_145101_F0001.root") as f:
        assert json.loads(str(f["infoDir/trigger_types"]))["Physics"] == 1                       # the table travels with the file


# ---- the output must not land in a Git repository

def _repo(tmp_path, gitignore=None, **spec_kwargs):
    """A Git working tree with a dataset definition inside it, whose output ("out") would be inside the tree."""
    import shutil
    import subprocess
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    if gitignore is not None:
        (repo / ".gitignore").write_text(gitignore, encoding="utf-8")
    files = make_raw(tmp_path / "raw")                                  # the raw data is elsewhere
    return repo, write_spec(repo / "toy.dataset.toml", files, **spec_kwargs)


def test_an_output_inside_a_git_tree_that_does_not_ignore_it_is_refused_and_nothing_is_written(tmp_path, capsys):
    repo, spec = _repo(tmp_path)
    with pytest.raises(ValueError, match="inside the Git working tree"):
        batch.check(spec)
    with pytest.raises(ValueError, match="must not be committed"):
        batch.run(spec, progress=None)
    assert not (repo / "out").exists()
    assert main(["run", str(spec)]) == 1 and "inside the Git working tree" in capsys.readouterr().err
    assert main(["check", str(spec)]) == 1


def test_the_refusal_can_be_overridden_on_purpose(tmp_path):
    repo, spec = _repo(tmp_path)
    assert len(batch.check(spec, allow_output_in_repo=True)) == 2
    assert main(["check", str(spec), "--allow-output-in-repo"]) == 0
    assert batch.run(spec, allow_output_in_repo=True, progress=None).n_events == 12
    assert (repo / "out").is_dir()


def test_an_output_that_the_tree_ignores_is_accepted_and_git_sees_no_results(tmp_path):
    import subprocess
    repo, spec = _repo(tmp_path, gitignore="out/\n")
    assert batch.run(spec, progress=None).n_events == 12
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo, capture_output=True, text=True).stdout
    assert "out/" not in status and "toy.dataset.toml" in status


def test_the_probe_is_a_data_file_of_the_output_format_so_ignoring_only_the_ledger_is_not_enough(tmp_path):
    repo, spec = _repo(tmp_path, gitignore="_goldsluice.json\n")        # the ledger is ignored, the data is not
    with pytest.raises(ValueError, match="inside the Git working tree"):
        batch.check(spec)
    (tmp_path / "second").mkdir()
    repo2, spec2 = _repo(tmp_path / "second", gitignore="*.parquet\n")  # Parquet ignored, but this definition writes ROOT
    spec2.write_text(spec2.read_text(encoding="utf-8").replace('output = "out"', 'output = "out"\noutput_format = "root"\nroot_detector = 1'),
                     encoding="utf-8")
    with pytest.raises(ValueError, match="inside the Git working tree"):
        batch.check(spec2)
    spec2.write_text(spec2.read_text(encoding="utf-8").replace('output_format = "root"\nroot_detector = 1', ""), encoding="utf-8")
    assert len(batch.check(spec2)) == 2                                 # Parquet again: ignored, accepted


def test_an_output_outside_any_git_tree_is_accepted(setup):
    tmp, files, spec = setup                                            # pytest's temporary folders are not in a repository
    assert len(batch.check(spec)) == 2


def test_the_example_writes_outside_the_repository_and_the_repository_ignores_processed_output():
    import shutil
    import subprocess
    from pathlib import Path
    from goldpan import dataset
    root = Path(__file__).resolve().parents[2]
    example = root / "goldsluice" / "examples" / "r76.dataset.toml"
    if not example.exists() or not (root / ".git").exists() or shutil.which("git") is None:
        pytest.skip("not in a Git checkout of the repository")
    assert root.resolve() not in dataset.load(example).output.resolve().parents
    probe = root / "goldsluice" / "examples" / "processed" / "x" / "_probe.parquet"
    assert subprocess.run(["git", "check-ignore", "-q", "--", str(probe)], cwd=root).returncode == 0


def test_the_example_loads_and_its_commented_root_lines_work_when_uncommented(tmp_path):
    from pathlib import Path
    from goldpan import dataset
    example = Path(__file__).resolve().parents[1] / "examples" / "r76.dataset.toml"
    text = example.read_text(encoding="utf-8")
    plain = dataset.load(example)
    assert (plain.output_format, plain.root_detector) == ("parquet", None)
    assert [s.algorithm for s in plain.steps] == ["peak", "max_time"]
    assert "# output_format = \"root\"" in text and "# root_detector = " in text
    root = tmp_path / "r76.dataset.toml"
    root.write_text(text.replace("# output_format = ", "output_format = ").replace("# root_detector = ", "root_detector = "), encoding="utf-8")
    spec = dataset.load(root)
    assert (spec.output_format, spec.root_detector) == ("root", 1)


def test_the_baseline_step_writes_the_mean_and_the_deviation_of_the_window_and_agrees_with_peak(setup):
    tmp, files, spec = setup
    steps = ('[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n[processing.params]\n'
             'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\namps_per_adc = 1.0\n\n'
             '[[processing]]\nalgorithm = "baseline"\nchannels = "role:phonon"\n[processing.params]\n'
             'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\n')
    write_spec(spec, files, steps=steps)
    batch.run(spec, progress=None)
    q = Dataset.open(spec).processed().quantities
    raw = parquet.read(files[0])
    window = raw.trace("A")[:, 10:1000]
    np.testing.assert_allclose(q["A"]["baseline_mean"][:7], window.mean(axis=1), rtol=1e-12)
    np.testing.assert_allclose(q["A"]["baseline_std"][:7], window.std(axis=1), rtol=1e-10)
    np.testing.assert_allclose(q["A"]["baseline_mean"], q["A"]["adc_max"] - q["A"]["current_max"], rtol=1e-12)     # the baseline `peak` subtracts
    assert "baseline_mean" not in q["Q"].fields if "Q" in q.fields else True                                       # role charge: not a phonon channel


def test_the_integral_and_excursion_steps_agree_with_goldpan_on_the_toy_dataset(setup):
    tmp, files, spec = setup
    window = 'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\n'
    steps = ('[[processing]]\nalgorithm = "integral"\nchannels = "role:phonon"\n[processing.params]\n' + window +
             'sample_period_s = "@readout.sample_period_s"\n\n'
             '[[processing]]\nalgorithm = "excursion"\nchannels = "role:phonon"\n[processing.params]\n' + window)
    write_spec(spec, files, steps=steps)
    batch.run(spec, progress=None)
    q = Dataset.open(spec).processed().quantities
    raw = parquet.read(files[0])
    x = raw.trace("A")
    from goldpan import algorithms, quantities
    config = raw.detector.readout.config()
    # the integral is a sum of terms of both signs: compare with the size of the terms, not with the (possibly small) result
    scale = np.abs(x - x[:, 10:1000].mean(axis=1)[:, None]).sum(axis=1) * config.sample_period_s
    np.testing.assert_allclose(q["A"]["integral"][:7], algorithms.integral(x, config), rtol=0, atol=1e-11 * scale.max())
    np.testing.assert_allclose(q["A"]["max_deviation"][:7], quantities.max_deviation(x, config), rtol=1e-12)
    np.testing.assert_allclose(q["A"]["excursion_ratio"][:7], quantities.excursion_ratio(x, config), rtol=1e-10)


def test_the_rise_time_step_agrees_with_goldpan_and_its_levels_are_written_in_the_definition(setup):
    tmp, files, spec = setup
    steps = ('[[processing]]\nalgorithm = "rise_time"\nchannels = "role:phonon"\n[processing.params]\n'
             'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = "@readout.pretrigger_samples"\n'
             'sample_period_s = "@readout.sample_period_s"\nlo = 0.1\nhi = 0.9\n')
    write_spec(spec, files, steps=steps)
    batch.run(spec, progress=None)
    q = Dataset.open(spec).processed().quantities
    raw = parquet.read(files[0])
    from goldpan import algorithms
    expected = algorithms.rise_time(raw.trace("A"), raw.detector.readout.config(), lo=0.1, hi=0.9)
    np.testing.assert_allclose(q["A"]["rise_time_s"][:7], expected, rtol=1e-12, equal_nan=True)
    write_spec(spec, files, steps=steps.replace("lo = 0.1\n", ""))                    # the levels have no default: a definition must write them
    with pytest.raises(TypeError):
        batch.run(spec, progress=None)


def test_workers_give_the_same_output_as_one_file_at_a_time(setup, tmp_path):
    tmp, files, spec = setup
    dumps = (("S1", "F0001", 7), ("S1", "F0002", 5), ("S1", "F0003", 9), ("S2", "F0001", 4), ("S2", "F0002", 6))
    files = make_raw(tmp / "raw", dumps=dumps)
    one, many = tmp / "one.dataset.toml", tmp / "many.dataset.toml"
    write_spec(one, files, steps=None)
    write_spec(many, files, steps=None)
    many.write_text(many.read_text(encoding="utf-8").replace('output = "out"', 'output = "out_many"'), encoding="utf-8")
    report_one = batch.run(one, progress=None)
    report_many = batch.run(many, workers=3, progress=None)
    assert report_many.workers == 3 and report_one.n_events == report_many.n_events == sum(n for _, _, n in dumps)
    assert [f.path for f in report_one.files] == [f.path for f in report_many.files]            # the order of the report is the order of the files
    a, b = Dataset.open(one).processed().quantities, Dataset.open(many).processed().quantities
    assert a.to_list() == b.to_list()
    ledger = json.loads((tmp / "out_many" / batch.LEDGER).read_text(encoding="utf-8"))
    assert len(ledger["files"]) == len(files)                                                    # every file is in the ledger, none lost to a race
    assert all(f.skipped for f in batch.run(many, workers=3, progress=None).files)             # and the next run does nothing


def test_a_failing_file_stops_the_run_with_its_error_and_keeps_what_was_done(setup):
    tmp, files, spec = setup
    steps = ('[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n[processing.params]\n'
             'glitch_samples = "@readout.glitch_samples"\npretrigger_samples = 99999\namps_per_adc = 1.0\n')   # a window longer than every trace
    write_spec(spec, files, steps=steps)
    with pytest.raises(ValueError, match="longer than the trace"):
        batch.run(spec, workers=2, progress=None)


def test_workers_must_be_a_whole_number_of_at_least_one(setup):
    tmp, files, spec = setup
    for bad in (0, -1, 2.5, True):
        with pytest.raises(ValueError, match="workers must be"):
            batch.run(spec, workers=bad, progress=None)
    assert main(["run", str(spec), "--workers", "2"]) == 0


# ---- reading ahead of the workers (a hard disk is read one file after the other, not by every worker at once) -----------------------

def test_readahead_does_not_change_the_output_and_its_values_are_checked(setup, tmp_path):
    tmp, files, spec = setup
    outputs = []
    for k, ahead in enumerate((None, 0, 1, 8)):
        d = tmp / f"ra{k}.dataset.toml"
        write_spec(d, files, steps=None)
        d.write_text(d.read_text(encoding="utf-8").replace('output = "out"', f'output = "out_ra{k}"'), encoding="utf-8")
        batch.run(d, workers=2, readahead=ahead, progress=None)
        outputs.append(Dataset.open(d).processed().quantities.to_list())
    assert all(o == outputs[0] for o in outputs)
    for bad in (-1, 1.5, True):
        with pytest.raises(ValueError, match="readahead must be"):
            batch.run(spec, readahead=bad, progress=None)
    assert main(["run", str(spec), "--readahead", "0", "--force"]) == 0


def test_the_prefetcher_reads_in_order_stays_ahead_by_the_places_it_has_and_always_sets_every_ready(tmp_path):
    import threading
    import time
    paths = []
    for k in range(3):
        d = tmp_path / f"dump{k}"
        d.mkdir()
        (d / "a.bin").write_bytes(b"x" * 1000)
        (d / "b.bin").write_bytes(b"y" * 1000)
        paths.append(d)
    ready = [threading.Event() for _ in paths]
    places, stop = threading.Semaphore(2), threading.Event()
    thread = threading.Thread(target=batch._prefetch, args=(paths, 2, stop, places, ready), daemon=True)
    thread.start()
    assert ready[0].wait(5) and ready[1].wait(5)
    time.sleep(0.5)
    assert not ready[2].is_set()                               # two places, both taken: it waits for a worker to finish a file
    places.release()                                           # a worker finished
    assert ready[2].wait(5)
    thread.join(5)
    assert not thread.is_alive()

    # a path that cannot be read is left to the worker, and a stop sets everything so that nothing waits for ever
    ready = [threading.Event() for _ in range(3)]
    stop = threading.Event()
    stop.set()
    batch._prefetch([tmp_path / "missing", paths[0], paths[1]], 1, stop, threading.Semaphore(0), ready)
    assert all(e.is_set() for e in ready)
    ready = [threading.Event() for _ in range(2)]
    batch._prefetch([tmp_path / "missing", paths[0]], 2, threading.Event(), threading.Semaphore(2), ready)
    assert all(e.is_set() for e in ready)
