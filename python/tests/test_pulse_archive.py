import numpy as np

import pulse_archive as archive
from pulse_config import PulseConfig


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "archive.h5"
    ids = ["101_0_Phonon_4096", "205_0_Phonon_4096"]
    config = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=1.6e-6)

    archive.save_good_events(
        path, series="07221203_2025", detector=0, channel=0, detector_ids=ids,
        cut_name="excursion_band_AI", cut_status="under_development",
        cut_params={"low": 0.5, "high": 0.7, "min_duration": 50},
        n_total=1517, dump="F0001", config=config,
        source_notebook="07221203_2025_dump1_noise.ipynb",
    )

    result = archive.load_good_events(path, "07221203_2025", 0, 0)
    np.testing.assert_array_equal(result["detector_ids"], ids)
    assert result["cut_name"] == "excursion_band_AI"
    assert result["cut_status"] == "under_development"
    assert result["cut_params"] == {"low": 0.5, "high": 0.7, "min_duration": 50}
    assert result["n_total"] == 1517
    assert result["n_kept"] == 2
    assert result["dump"] == "F0001"
    assert result["pretrigger_samples"] == 500
    assert result["glitch_samples"] == 10
    assert result["sample_period_s"] == 1.6e-6
    assert result["source_notebook"] == "07221203_2025_dump1_noise.ipynb"
    assert "created" in result


def test_save_overwrites_existing_group(tmp_path):
    path = tmp_path / "archive.h5"
    archive.save_good_events(path, "s", 0, 0, ["a", "b", "c"], "cut1")
    archive.save_good_events(path, "s", 0, 0, ["x"], "cut2")

    result = archive.load_good_events(path, "s", 0, 0)
    np.testing.assert_array_equal(result["detector_ids"], ["x"])
    assert result["cut_name"] == "cut2"


def test_multiple_series_detectors_channels_coexist(tmp_path):
    path = tmp_path / "archive.h5"
    archive.save_good_events(path, "seriesA", 0, 0, ["a1"], "cutA")
    archive.save_good_events(path, "seriesA", 1, 0, ["a2"], "cutA")
    archive.save_good_events(path, "seriesB", 0, 0, ["b1"], "cutB")

    assert archive.list_archive(path) == {
        "seriesA": {0: {0: 1}, 1: {0: 1}},
        "seriesB": {0: {0: 1}},
    }


def test_load_missing_group_raises_key_error(tmp_path):
    path = tmp_path / "archive.h5"
    archive.save_good_events(path, "s", 0, 0, ["a"], "cut")
    try:
        archive.load_good_events(path, "s", 0, 1)
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_list_archive_missing_file_returns_empty_dict(tmp_path):
    assert archive.list_archive(tmp_path / "does_not_exist.h5") == {}
