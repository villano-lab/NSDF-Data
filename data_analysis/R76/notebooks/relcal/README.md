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

## Rules of the folder

- Notebooks use `goldpan` (installed by `requirements.txt`), kernel `darkmatter_cli_env`. They read processed quantities and never rewrite them.
- Use real triggers only. The processed quantities do not carry the trigger type yet, so the notebook reads it from the `.csv` of each raw dump. In these dumps the label `Physics` marks the random triggers (almost none has a pulse) and `Unknown` the real ones, the working assumption of `goldpan.cuts` (Note 2a), not confirmed against the DAQ.
- The position of an event on the face is a guide made from the channels themselves (the integral-weighted centre of the regions), not a reconstruction. The ring channels `A`, `B` and the centre `F` all sit at the centre of the face in that guide.
- Save no data here. Figures that matter go in `figures/` of this folder, or in a note.
