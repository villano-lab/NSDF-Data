import numpy as np

import pulse_io as io


class FakeCdms:
    """Minimal stand-in for nsdf_dark_matter's `cdms` object -- just enough
    surface (`get_detector_channels`) for `pulse_io` to depend on."""

    def __init__(self, data, triggers=None):
        self._data = data  # detector_id -> (n_channels, n_samples) array
        self._triggers = triggers or {}  # event id string -> trigger_type

    def get_detector_channels(self, detector_id):
        return self._data[detector_id]

    def get_event_metadata(self, event):
        return type("Meta", (), {"trigger_type": self._triggers[event]})()


def test_load_channel_batch_stacks_correct_channel_in_order():
    ids = ["100_0_Phonon_8", "101_0_Phonon_8", "102_1_Phonon_8"]
    data = {d: (np.arange(32).reshape(4, 8) + i) for i, d in enumerate(ids)}
    cdms = FakeCdms(data)

    out_ids, batch = io.load_channel_batch(cdms, ids, channel=2)

    assert batch.shape == (3, 8)
    np.testing.assert_array_equal(out_ids, ids)
    for i, d in enumerate(ids):
        np.testing.assert_array_equal(batch[i], data[d][2].astype(np.float64))


def test_filter_by_detector():
    ids = ["1_0_Phonon_8", "2_1_Phonon_8", "3_0_Phonon_8"]
    assert io.filter_by_detector(ids, 0) == ["1_0_Phonon_8", "3_0_Phonon_8"]
    assert io.filter_by_detector(ids, "1") == ["2_1_Phonon_8"]


def test_event_id_and_detector_index():
    assert io.event_id("12345_2_Phonon_4096") == "12345"
    assert io.detector_index("12345_2_Phonon_4096") == 2


def test_load_channel_batch_multi_pools_and_labels_dumps():
    ids_a = ["100_0_Phonon_8", "101_1_Phonon_8"]
    ids_b = ["200_0_Phonon_8", "201_0_Phonon_8"]
    data_a = {d: (np.full((4, 8), i)) for i, d in enumerate(ids_a)}
    data_b = {d: (np.full((4, 8), i + 10)) for i, d in enumerate(ids_b)}

    class MultiFakeCdms(FakeCdms):
        def __init__(self, ids, data):
            super().__init__(data)
            self._ids = ids

        def get_detector_ids(self):
            return self._ids

    cdms_by_dump = {
        "F0002": MultiFakeCdms(ids_a, data_a),
        "F0003": MultiFakeCdms(ids_b, data_b),
    }

    dumps, ids, batch = io.load_channel_batch_multi(cdms_by_dump, channel=1, detector=0)

    # detector filter keeps "100_0_..." from A and both "200_0_.../201_0_..." from B
    np.testing.assert_array_equal(dumps, ["F0002", "F0003", "F0003"])
    np.testing.assert_array_equal(ids, ["100_0_Phonon_8", "200_0_Phonon_8", "201_0_Phonon_8"])
    assert batch.shape == (3, 8)


def test_trigger_types_looks_up_each_ids_event_in_order():
    ids = ["100_0_Phonon_8", "100_1_Phonon_8", "101_0_Phonon_8"]
    cdms = FakeCdms({}, triggers={"100": "Physics", "101": "Unknown"})

    out = io.trigger_types(cdms, ids)

    np.testing.assert_array_equal(out, ["Physics", "Physics", "Unknown"])
