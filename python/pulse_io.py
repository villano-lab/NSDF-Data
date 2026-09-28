"""Bridge from `nsdf_dark_matter`'s `cdms` objects into the plain-ndarray
convention (`(n_pulses, n_samples)`, samples on the last axis) the rest of this
library expects. Only this module knows about `cdms`; everything else in
`python/` only ever sees plain arrays.
"""
import numpy as np

from pulse_status import status, DONE


@status(DONE)
def detector_index(detector_id: str) -> int:
    """The `<detector>` component of a `"<event>_<detector>_Phonon_<n>"` id."""
    return int(detector_id.split('_')[1])


@status(DONE)
def event_id(detector_id: str) -> str:
    """The `<event>` component of a `"<event>_<detector>_Phonon_<n>"` id."""
    return detector_id.split('_')[0]


@status(DONE)
def filter_by_detector(detector_ids, detector):
    """Keep only ids whose `<detector>` component matches `detector`."""
    detector = str(detector)
    return [d for d in detector_ids if d.split('_')[1] == detector]


@status(DONE)
def load_channel_batch(cdms, detector_ids, channel: int):
    """Stack one channel from a list of detector_ids into a batch array.

    Returns `(ids, data)`: `ids` is `np.array(detector_ids)` (same order as
    `data`), `data` is float64 shape `(len(detector_ids), n_samples)`.
    """
    ids = np.asarray(list(detector_ids))
    data = np.stack([cdms.get_detector_channels(d)[channel] for d in ids]).astype(np.float64)
    return ids, data


@status(DONE)
def trigger_types(cdms, detector_ids):
    """The `trigger_type` string the dump's `.csv` records for each id's event, as an
    array aligned with `detector_ids` (e.g. `"Physics"`, `"Unknown"`). Metadata is per
    event, so the three detectors of one event share a value. Feed it to
    `pulse_cuts.randoms` / `real_triggers`."""
    return np.array([cdms.get_event_metadata(event_id(d)).trigger_type for d in detector_ids])


@status(DONE)
def load_channel_batch_multi(cdms_by_dump, channel: int, detector=None):
    """Like `load_channel_batch`, pooled across multiple dumps.

    `cdms_by_dump`: `{dump_label: cdms}` (e.g. `{"F0002": cdms2, "F0003": cdms3}`).
    Pass `detector` to filter each dump's ids with `filter_by_detector` first.

    Returns `(dumps, ids, data)`, all the same length, concatenated across
    dumps in `cdms_by_dump`'s iteration order: `dumps[i]`/`ids[i]` name which
    dump and detector_id `data[i]` came from.
    """
    all_dumps, all_ids, all_data = [], [], []
    for dump, cdms in cdms_by_dump.items():
        ids = cdms.get_detector_ids()
        if detector is not None:
            ids = filter_by_detector(ids, detector)
        ids, data = load_channel_batch(cdms, ids, channel)
        all_dumps.append(np.full(len(ids), dump))
        all_ids.append(ids)
        all_data.append(data)
    return np.concatenate(all_dumps), np.concatenate(all_ids), np.concatenate(all_data, axis=0)
