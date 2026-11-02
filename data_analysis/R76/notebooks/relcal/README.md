# relcal: relative calibration between the channels

Work on branch `feature/villano-relcal`. The goal is to find out how the six phonon channels of the Side-2 readout compare with each other, so that a pulse height in one channel can be set against the same event's pulse height in another.

Nothing here is a result yet. Each notebook says what it does and what it does not.

## The data

The quantities of `data_analysis/R76/processing/r76-d-idx.dataset.toml`: every algorithm of `goldsluice` on the 12 Side-2 series of Run 76 (2,993 dumps), written as Parquet to `C:/NSDF/goldsluice-output/r76-d-idx/NAI-S2/`. The raw dumps are in `C:/NSDF/idx`. Neither is in the repository.

Six channels (`Side2pA` to `Side2pF`), nine quantities each: `adc_max`, `current_max`, `max_time_s`, `baseline_mean`, `baseline_std`, `max_deviation`, `excursion_ratio`, `integral`, `rise_time_s`. The unit of the pulse sizes is the ADC count (`amps_per_adc` is a placeholder equal to 1), so **no channel is calibrated to energy or current yet**. That is what this folder is for.

The readout is assumed to be the same for all 12 series as for `07221203_2025` (DCRC_RUN76). The detector record names that series only as a note. Check the pulse position of each series before trusting a comparison across series.

## The detector

The face (Side 2) is drawn as in the Note 9 channel figure and the wiki: `A` the outer ring, `B` the second ring, `C`, `D`, `E` three 120 degree sectors of the middle region, `F` the centre disc. The geometry is copied from `../pulse-normalization/detector_layout.py`. Only a rough picture: the regions are drawn to scale of the sketch, not of the real sensor layout.

## Notebooks

| notebook | what it does |
|---|---|
| `integral-on-the-face.ipynb` | reads the processed data set, and maps the `integral` of the six channels onto the face with the detector drawn under the plot |
| `positions-by-voltage.ipynb` | groups the series by high voltage (`series.csv`) and draws the event density in the plane of the delays `xdel`, `ydel` for each group, with the detector underneath; needs a `rise_crossing` step in the processing |
| `positions-82v-dcrc1pb.ipynb` | the position distribution in the plane of the 20 % delays (`xdel`, `ydel`), the azimuth `phidel` and the radius `afdel`, for the eight DCRC1pB-triggered series near -82 V; reads the output of `r76-82v-dcrc1pb.dataset.toml` (branch `feature/processing`) from `~/goldsluice-output/r76-82v-dcrc1pb`; also draws the cuts that select the two high-activity spots over `C` and `F` |
| `spots-82v-energy.ipynb` | the energy distributions (the uncalibrated sum of the six `integral`s) of the events in those two spots, against their surroundings, the excess of each spot, series by series, and the channels' shares |
| `spot-f-tight-energy.ipynb` | the energy distribution of spot F with a tight cut (within 0.5 us of its centre, about 95 % spot events), against the events outside both spots |
| `spot-f-tight-traces.ipynb` | randomly chosen events of that tight cut in all channels, one tiled figure per event (boards x inputs, as in the earlier notes) with the baseline and integration windows of `integral` drawn on every trace, and all of them overlaid; reads the raw dumps from `~/idx` |
| `spectrum-82v-total.ipynb` | the total spectrum of the -82 V DCRC1pB series with no position selection; the `integral` of Side2pF, then of all six channels with the ceiling each reaches when it stays saturated to the end of the trace, real and random triggers |
| `low-integral-traces.ipynb` | randomly chosen real triggers whose `integral` is between 0 and 0.75 in all six channels (no position cut), drawn as tiled figures with the baseline and integration windows, and overlaid |
| `integral-vs-height.ipynb` | for each channel, the `integral` of every real trigger against its pulse height (`current_max`, ADC counts above the baseline), and the ratio of the two (the effective pulse length) against the height, with the saturated height and the largest integral it allows marked |
| `spots-integral-vs-height.ipynb` | the other way round: events cut on the position first (spot F and spot C, tight), then the integral against the height of all six channels, and their ratio, against the events outside both spots, with the three Side2pF bands drawn as lines of constant integral/height; then random traces from the bulk (25-75 %) of each spot's energy spectrum, all channels, with the saturated height and the flat-top time of every channel |
| `spots_82v.py` | shared by the two notebooks above: reads the -82 V output, makes the delays and the selection, and defines the spot circles (`SPOTS`) and the rings around them |

## Rules of the folder

- Notebooks use `goldpan` (installed by `requirements.txt`), kernel `darkmatter_cli_env`. They read processed quantities and never rewrite them.
- Use real triggers only. The processed quantities do not carry the trigger type yet, so the notebook reads it from the `.csv` of each raw dump. In these dumps the label `Physics` marks the random triggers (almost none has a pulse) and `Unknown` the real ones, the working assumption of `goldpan.cuts` (Note 2a), not confirmed against the DAQ.
- The position of an event on the face is a guide made from the channels themselves (the integral-weighted centre of the regions), not a reconstruction. The ring channels `A`, `B` and the centre `F` all sit at the centre of the face in that guide.
- Save no data here. Figures that matter go in `figures/` of this folder, or in a note.
