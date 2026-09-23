# archives/

`good_noise.h5`: a durable record of which `detector_id`s a given noise-selection
cut kept, per `(series, detector, channel)` -- written and read with
`python/pulse_archive.py` (`save_good_events`/`load_good_events`/
`list_archive`). See that module's docstring for the on-disk layout. Those
functions are cut-agnostic (any cut's `detector_id` selection, not just a noise
one) -- a future non-noise archive (e.g. "good triggered pulses") would get its
own file here rather than a group in this one.

This isn't a cache of raw pulse data (which stays in `~/idx/...`, downloaded
via `nsdf-cli`) -- it's a record of a cut's *result*, so a later notebook, or
a re-run after the cut's parameters change, can compare against what was kept
before instead of re-deriving it by hand from notebook output.

Saving a `(series, detector, channel)` group overwrites it -- this holds the
*current* good-event list per key, not a history of every past run. If a
cut's status is `under_development` (e.g. `excursion_band_AI` as of
2026-09-23), that status is stored in the group's `cut_status` attribute, so a
reader knows the archived selection may still change as the cut is refined.

First entries (2026-09-23): `07221203_2025`/detector 0/channel 0, from
`excursion_band_AI` in `R76/analysis_notes/07221203_2025_dump1_noise.ipynb`.
