"""goldpan.registry.add_record and record_text: a detector or a readout is checked as the reader checks it and appended to a registry folder."""
import tomllib

import pytest

from goldpan import registry

READOUT = {"pretrigger_samples": 500, "glitch_samples": 10, "sample_period_s": 0.8e-6, "status": "inferred", "evidence": "measured on a test dump",
           "description": "a test readout"}
DETECTOR = {"number": 3, "readout": "TEST_READOUT", "status": "inferred", "evidence": "the wiring table of the test setup, not checked on a file",
            "description": "a test detector", "series": ["S1"],
            "idx": {"channels": {"PhA": [0, 0], "PhB": [0, 1]}, "roles": {"PhA": "phonon", "PhB": "phonon"}}}


def test_a_readout_and_a_detector_are_added_to_a_new_folder_and_read_back(tmp_path):
    folder = tmp_path / "reg"
    assert registry.add_record(folder, "readouts", "TEST_READOUT", READOUT) == folder / "readouts.toml"
    assert registry.add_record(folder, "detectors", "TEST-DET", DETECTOR) == folder / "detectors.toml"
    assert (folder / "detectors.toml").read_text(encoding="utf-8").startswith("format_version = 1")
    reg = registry.load(folder, use_environment=False)
    r, d = reg.readout("TEST_READOUT"), reg.detector("TEST-DET")
    assert (r.config.pretrigger_samples, r.config.sample_period_s, r.status, r.description) == (500, 0.8e-6, "inferred", "a test readout")
    assert d.number == 3 and d.readout == "TEST_READOUT" and d.series == ("S1",) and d.evidence.startswith("the wiring table")
    assert d.read_defaults("idx") == DETECTOR["idx"]
    assert registry.record_text("detectors", "TEST-DET", DETECTOR) in (folder / "detectors.toml").read_text(encoding="utf-8")


def test_a_record_is_appended_and_what_was_in_the_file_stays_as_it_was(tmp_path):
    folder = tmp_path / "reg"
    folder.mkdir()
    original = "# my notes on the first detector\nformat_version = 1\n\n[readouts.R1]  # the Run 76 numbers\npretrigger_samples = 500\nglitch_samples = 10\nsample_period_s = 0.8e-6\nstatus = \"confirmed\"\nevidence = \"a document\"\n"
    (folder / "readouts.toml").write_text(original, encoding="utf-8")
    registry.add_record(folder, "readouts", "R2", {**READOUT, "sample_period_s": 1.6e-6})
    text = (folder / "readouts.toml").read_text(encoding="utf-8")
    assert text.startswith(original) and "[readouts.R2]" in text
    assert set(registry.load(folder, use_environment=False).readouts()) == {"R1", "R2"}
    registry.add_record(folder, "readouts", "R3", READOUT, file="other.toml")                     # a second file
    assert set(registry.load(folder, use_environment=False).readouts()) == {"R1", "R2", "R3"}


def test_a_bad_record_is_refused_and_nothing_is_written(tmp_path):
    folder = tmp_path / "reg"
    registry.add_record(folder, "readouts", "TEST_READOUT", READOUT)
    before = {p.name: p.read_text(encoding="utf-8") for p in folder.iterdir()}
    for kind, name, table, match in (
            ("detectors", "D", {k: v for k, v in DETECTOR.items() if k != "evidence"}, "evidence"),
            ("detectors", "D", {**DETECTOR, "status": "certain"}, "status must be"),
            ("detectors", "D", {**DETECTOR, "evidence": "  "}, "evidence must say"),
            ("detectors", "D", {**DETECTOR, "readout": "NOT_A_READOUT"}, "no readout"),
            ("detectors", "D", {**DETECTOR, "colour": "red"}, "unknown key"),
            ("detectors", "D", {**DETECTOR, "number": -1}, "whole number"),
            ("readouts", "R", {k: v for k, v in READOUT.items() if k != "glitch_samples"}, "glitch_samples"),
            ("readouts", "TEST_READOUT", READOUT, "already defined"),
            ("pulses", "R", READOUT, "kind must be")):
        with pytest.raises(ValueError, match=match):
            registry.add_record(folder, kind, name, table)
    with pytest.raises(ValueError, match="file must be"):
        registry.add_record(folder, "readouts", "R", READOUT, file="../escape.toml")
    assert {p.name: p.read_text(encoding="utf-8") for p in folder.iterdir()} == before


def test_a_detector_may_name_a_preset_of_goldpan_config_as_its_readout(tmp_path):
    registry.add_record(tmp_path / "reg", "detectors", "D", {**DETECTOR, "readout": "DCRC_RUN76"})
    assert registry.load(tmp_path / "reg", use_environment=False).detector("D").readout == "DCRC_RUN76"


def test_the_text_is_valid_toml_for_awkward_names_and_values(tmp_path):
    name = 'odd "name" with spaces'
    text = registry.record_text("detectors", name, {"status": "inferred", "evidence": "line one\nline two, with a \"quote\" and a backslash \\ and é", "odb_name": "G149"})
    parsed = tomllib.loads(text)
    assert parsed["detectors"][name]["evidence"].startswith("line one") and parsed["detectors"][name]["odb_name"] == "G149"
    registry.add_record(tmp_path / "reg", "detectors", name, {"status": "inferred", "evidence": "x"})
    assert name in registry.load(tmp_path / "reg", use_environment=False).detectors()


def test_a_file_that_would_not_load_is_restored(tmp_path, monkeypatch):
    folder = tmp_path / "reg"
    registry.add_record(folder, "readouts", "TEST_READOUT", READOUT)
    path = folder / "readouts.toml"
    before = path.read_text(encoding="utf-8")
    real = registry.load
    calls = []

    def failing(*args, **kwargs):
        calls.append(1)
        if len(calls) > 1:                                          # the check after the write fails
            raise ValueError("pretend the file no longer loads")
        return real(*args, **kwargs)

    monkeypatch.setattr(registry, "load", failing)
    with pytest.raises(ValueError, match="pretend"):
        registry.add_record(folder, "readouts", "R2", READOUT)
    assert path.read_text(encoding="utf-8") == before
