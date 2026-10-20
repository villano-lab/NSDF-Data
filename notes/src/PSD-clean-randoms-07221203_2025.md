---
id: "9"
title: "What is the current best PSD estimate from series 07221203_2025?"
author: "Buddy Holly (A. Villano)"
date: "2026-10-05"
status: "In progress"
keywords: "PSD, Noise, Randoms, PuBe"
description: "I created a sample of clean randoms selected in the same way as Note 2 and produced a noise PSD for 07221203_2025. The randoms selection is updated/improved but the technique is the same. Since there are no known real pulses in those noise traces this is a true characterization of our noise environment."
---

## Code repository

All code is pinned to commit `bf0ed61`: each link shows the file as it was when the results below were made, which may be older than the latest version, and the file may have moved since (see `data_analysis/README.md`). On the published page a small "latest" link after each one opens the file on `develop` today.

- [`psd-clean-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/psd-clean-randoms-buddy.ipynb): the PSDs of every channel from the `clean_randoms` cut, and the saved HDF5 file [`psd-clean-randoms-07221203_2025_F0001.h5`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/psd-clean-randoms-07221203_2025_F0001.h5) (Noise Power Spectral Densities).
- [`chan0-cut-on-all-channels-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/chan0-cut-on-all-channels-buddy.ipynb): how good the PCS2 cut (the channel names are explained under Data and setup) is on the other channels, and the definition of the cut we use (`clean_randoms`) (Selection of Randoms in All Channels, Data and setup for the timing of the randoms, Appendices A and B).
- [`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb): the channel map and the noise spectra of the 31 events of the strictest cut (Data and setup, Appendix A).
- [`extract_odb_facts.py`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/extract_odb_facts.py) and [`odb-facts-07220916_2200.json`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/odb-facts-07220916_2200.json): the run configuration of series `07220916_2200` (board order, QET biases, random rates) read from its raw file, which is not in the repository, and the numbers it gave; section 12 of `noise-psd-randoms-buddy.ipynb` prints them (Data and setup, Caveats).
- [`pulse_channels.py`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/python/pulse_channels.py), [`pulse_cuts.py`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/python/pulse_cuts.py) and [`pulse_quantities.py`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/python/pulse_quantities.py): the library for the channel names, the randoms and excursion-band cuts, and the PSD.

## Data and setup

We are using the file 07221203_2025_F0001, which is series 07221203_2025, Dump 1. The first 1000 events are "random" triggers (the "Beginning of Run Randoms," BORR, taken at about 20 Hz: 1000 events in 49 seconds); random triggers are snapshots of our detector traces taken at any time (rather than when a pulse occurs) to sample the noise environment. The line in the third code block of the [`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb) notebook shows the randoms cut defined as `quiet_noise = pc.excursion_band(pulses, config_500) & (np.log10(bstd_500) < 0.5)` in addition to selecting the trigger specification for random events. The other 8 of the 1008 events that carry the randoms label are "in-run" randoms: they are spread through the rest of the dump, one every 1 to 2 seconds (all 8 in the last 9 seconds of the dump; the timestamps have one-second resolution). The run configuration of series `07220916_2200` lists 5 Hz for in-run randoms, which does not match what we see here, so that rate should not be assumed for this series. 

::: callout
**Note.** The trigger-type labels in the dump's `.csv` are the wrong way round. The column `trigger_type` has two values, `Physics` and `Unknown`. By their names one would read `Physics` as an event triggered by a pulse and `Unknown` as a trigger of undetermined type. In this dump it is the opposite: the first 1000 events, which are the Beginning of Run Randoms (the run configuration asks for 1000 randoms at 20 Hz, and these 1000 events span 49 s, which is 20.4 Hz), are all labelled `Physics`, and the other events, 509 in this dump, are labelled `Unknown`. So we take `Physics` to mean a random trigger and `Unknown` to mean a real (pulse) trigger, which is what `pc.randoms` and `pc.real_triggers` do. This is a working assumption: nothing in the data files or the DAQ documentation we have confirms it, and the two functions are tagged under development for that reason (see [Note 2a](https://villano-lab.github.io/NSDF-Data/notes/note-02a-bstd-vs-time.html#randoms)).
:::

It may also be useful to have a diagram of the detector and which channels are working during the R76 run period at UMN. The figure below was reconstructed from the archive of the [UMN Wiki](https://villano-lab.github.io/R76Analysis/index.html). 

**How we found which channel is which.** The data are numbered by detector (0 to 2) and channel (0 to 3), but there is one detector, S104, read out by three four-channel electronics boards (DCRC1, DCRC3, DCRC4). We matched them to the detector's channels in four steps:

1. **The channel table.** The *Setup* table of the [UMN Run 76 summary](https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76.html) lists the 12 channels by board, with the detector channel in its Label column (`Side1pA` to `Side2pF`). We used that column. The HV columns repeat entries and look like typos.
2. **The board order.** The table does not say which board is detector 0, 1 or 2. The raw file of another Run 76 series (`07220916_2200`; the raw file for series `07221203_2025`, the one analysed here, is not on NSDF) holds the run configuration. It enables boards DCRC1, DCRC3 and DCRC4, and the three records of each event carry the codes 9, 11 and 12, which are the board numbers plus 8. So detector 0, 1, 2 = DCRC1, DCRC3, DCRC4. This is inferred and not confirmed.
3. **The channels within a board.** We assumed they follow the table's row order. The data agree: the dead channels, whose signal never changes (channel 2 of DCRC1 and DCRC3, and channels 1 to 3 of DCRC4) are the ones that configuration lists with zero QET bias.
4. **The faces.** The wiki's source-position figure draws Side 2 as seen after flipping the detector over, which is how the figure below shows it.

The mapping is kept in [`python/pulse_channels.py`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/python/pulse_channels.py), marked as under development, and section 7 of *that* notebook, [`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb), gives the evidence.

**Channel names.** In the text a channel is written as P, the letter of its sensor, and its side: PCS2 is the phonon channel C on Side 2. The library, the tile titles of the figures and the HDF5 file of the PSDs use the form `Side2pC` for the same channel, and the dump numbers it as detector 0, channel 0. The seven working channels:

| In the text | Library and figures | Dump (detector / channel) | Board |
|:-:|:-:|:-:|:-:|
| PCS2 | `Side2pC` | 0 / 0 | DCRC1 |
| PFS2 | `Side2pF` | 0 / 1 | DCRC1 |
| PFS1 | `Side1pF` | 0 / 3 | DCRC1 |
| PES1 | `Side1pE` | 1 / 0 | DCRC3 |
| PBS1 | `Side1pB` | 1 / 1 | DCRC3 |
| PES2 | `Side2pE` | 1 / 3 | DCRC3 |
| PBS2 | `Side2pB` | 2 / 0 | DCRC4 |

The five dead channels, whose signal never changes, are PCS1, PDS1, PAS1, PAS2 and PDS2 (`Side1pC`, `Side1pD`, `Side1pA`, `Side2pA` and `Side2pD`).

![](img/channel-status-07221203_2025_F0001.png)

**Figure 1: The channels of detector S104.** Side 1 is on the left and Side 2 on the right (as seen after flipping the detector over). The 7 working channels are coloured; the 5 dead channels (whose signal never changes) are grey and hatched.

## The question

Based on this series' Beginning of Run Randoms (BORR), what is our best estimate for the noise environment of the experimental setup? The noise environment is typically summarized in terms of the Power Spectral Density (PSD).

## Selection of Randoms in All Channels

Typically, BORR are taken in the first events of the first "dump" (file) of a series' raw data. In this series that is the case and there are 1000 BORR. Often some of the initial traces are "contaminated" with a real physics pulse that just happened to be in the random's readout window. We call this a "pileup" pulse. Those occurances can mess up the noise computation and therefore the extracted pulse amplitudes; pulse amplitudes are used to estimate the energy deposited in each event. Here I describe how we make a cut on the data to be sure those pileups are removed. 

This sort of thing has been done on one channel, PCS2, and it is the topic of [Note 2](https://villano-lab.github.io/NSDF-Data/notes/note-02-noise-selection.html) and [Note 2a](https://villano-lab.github.io/NSDF-Data/notes/note-02a-bstd-vs-time.html). Note 2 develops the noise-pulse selection: an excursion cut on a 500-sample pretrigger window (the Tight band) together with a cut on the baseline scatter, `log10(bstd) < 0.5`, which keeps 179 of the 1517 traces. Note 2a adds the trigger cut that keeps only the randoms, 141 of those 179 (the other 38 are real triggers), and looks at how the baseline scatter changes with time. 

To use that cut I have to decide how to apply it to all of the channels. A pileup should show up in all channels simultaneously, because the origin is a real physics event. It is possible the amplitude in some channels could be small enough so that it's not obvious. Figure 2 is a plot based on the cut for PCS2 only (see the [Data and setup](#data-and-setup) section). To my slight surprise I found that this cut *does not remove* some traces that are either glitches or tails of pulses on Side 1. I don't want those pulses in the noise sample. 


![](img/chan0-cut-on-all-channels-full-07221203_2025_F0001.png)

**Figure 2: The 141 randoms that pass the PCS2 cut, in every channel.** One tile per channel (rows are the boards DCRC1, DCRC3 and DCRC4); the traces are drawn over each other with transparency, baseline-subtracted, on a free vertical scale. The cut is made on PCS2 (framed). Blue is Side 1, orange is Side 2, and red marks a trace that contains a pulse. The 5 tiles with grey text are the dead channels. Several traces carry large baseline ramps in the Side 1 and DCRC3 channels even though they are quiet in PCS2.

Based on what was seen in Figure 2. I developed a cut that will select noise for PBS1. It will hopefully not be as strict as requiring the analogous cut to be true on *all* channels. That leaves only 31 traces (see [Appendix A](#appendix-a-the-strictest-cut-every-working-channel)). 

Instead of doing *all* channels I selected instead one channel on each side to apply the standard cut to and then took the logical "AND." In that case the remaining number of traces was somewhat small (71) but the quality looked pristine. 

![](img/cut-on-S1-and-S2-full-07221203_2025_F0001.png)

**Figure 3: The randoms that pass the cut on one channel of each side, in every channel.** The cut is the quiet-noise cut on PCS2 (Side 2) **and** on PBS1 (Side 1), both framed. One tile per channel, with the traces drawn over each other with transparency on a free vertical scale. Blue is Side 1, orange is Side 2, and red would mark a trace that contains a pulse. The 5 tiles with grey text are the dead channels.

While setting this up in the Jupyter notebook [`chan0-cut-on-all-channels-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/chan0-cut-on-all-channels-buddy.ipynb), I checked if there were similar traces left in S2 after selecting on PBS1, just like we saw in S1 after selecting on PCS2. [Appendix B](#appendix-b-the-cut-on-pcs2-and-the-cut-on-pbs1) shows the traces left in S1 after the PCS2 cut (Figure 7), and then the S1 cut itself (Figure 8). To my surprise there *were not* traces in S2 that were very apparent. That means that for some reason only cutting on S1 is more pure. Since only cutting on S1 is also less restrictive than the combined cut by definition, this led to more accepted randoms (101, compared with 71 for one channel on each side and 31 for all channels).

**We will use this cut going forward:** the cut of Notes 2 and 2a (a random trigger in the Tight excursion band with `log10(bstd) < 0.5`) made on PBS1 (S1). In the notebook it is defined in one place, `clean_randoms_cut`, and the selection it makes is called `clean_randoms`.

## Noise Power Spectral Densities

The key parameter we want to get out of pulses in these detectors is the overall "amplitude" because it should be proportional to the energy deposited in a scattering event. That's hard to do for the small signals (near the noise baseline) that we have for dark matter direct detection (see the review by Schnee [1]) so we use an algorithm called the Optimal Filter (OF) (Gatti and Manfredi [2]; Golwala [3]; Press et al. [4]; Szymkowiak et al. [5]) instead of a simpler procedure like integrating the pulses. The crucial part of the OF is that it takes into account the electronic noise environment of the sensor, rather than blindly integrating. The noise is summarized by the Power Spectral Density (PSD) constructed with traces that have no pulses present--the ones we are selecting here.

The PSD is sort of like the standard deviation of different frequency components in a trace (any trace can be written as a sum of sinusoids of different frequencies, the Fourier decomposition [4]). The PSD can be calculated for discrete data sampling as below, by averaging the squared Fourier amplitudes of many traces (Welch [6]):

Take a trace of $N$ samples $x[n]$, $n = 0, \ldots, N-1$, taken every $\Delta t$ (here $\Delta t = 1.6\,\mu\mathrm{s}$), with its baseline subtracted. Its discrete Fourier transform is $X[k]$, and bin $k$ sits at the frequency $f[k] = k/(N\,\Delta t)$. Averaging over $M$ traces with no pulse in them (here the $M = 101$ traces of the `clean_randoms` cut, or the 31 of Appendix A), the one-sided PSD is

$$
\begin{aligned}
X_m[k] &= \sum_{n=0}^{N-1} x_m[n]\, e^{-2\pi i\, k n / N}, \\
S[k] &= \frac{2\,\Delta t}{N}\cdot\frac{1}{M}\sum_{m=1}^{M}\left|X_m[k]\right|^2
\qquad \left(\mathrm{counts}^2/\mathrm{Hz}\right),
\end{aligned}
$$

where $x_m[n]$ is trace $m$ and $X_m[k]$ its transform. The factor 2 folds the negative frequencies onto the positive ones (it is left out for the zero-frequency and Nyquist bins), and the $1/N$ and $\Delta t$ make $S$ independent of the trace length and the sampling rate, so that its integral over frequency equals the mean square of the trace (its variance, if the trace has zero mean). This is the convention used in the notebook ([`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb)); Note 3 plotted the raw $|X[k]|^2$ instead, which differs from $S$ only by the constant $2\,\Delta t/N$.

Figure 4 shows the PSDs of the 101 events of the `clean_randoms` cut, the cut used from now on. Above 100 kHz the mean PSD is flat, between 5.6e-6 and 6.7e-6 counts²/Hz in five of the seven channels; the narrow lines of the DCRC3 channels PES1 and PES2 raise their means to 1.3e-5 and 1.7e-5 counts²/Hz. PBS2 is the odd one: between 1 and 10 kHz its mean PSD is 6.8e-6 counts²/Hz, against 4.5e-5 to 1.5e-4 for the others (see Caveats).

![](img/psd-clean-randoms-by-side-07221203_2025_F0001.png)

**Figure 4: The noise PSD of the 101 randoms of the `clean_randoms` cut, by side.** Side 1 on the left (3 working channels) and Side 2 on the right (4 working channels), one colour per channel within each panel (the colours are not shared between the panels). Each curve is the one-sided PSD (counts²/Hz) of the mean over the 101 events, as defined above, and the thin band around it is the uncertainty on the mean (one standard error, 0.098 to 0.099 of the mean in every channel). Both panels share the same axes. The five dead channels are not shown.

### References

1. R. W. Schnee, "Introduction to dark matter experiments," in *Physics of the Large and the Small, TASI 2009* (World Scientific, 2011), [arXiv:1101.5205](https://arxiv.org/abs/1101.5205).
2. E. Gatti and P. F. Manfredi, "Processing the signals from solid-state detectors in elementary-particle physics," *Rivista del Nuovo Cimento* **9**(1), 1 (1986).
3. S. R. Golwala, *Exclusion Limits on the WIMP-Nucleon Elastic-Scattering Cross-Section from the Cryogenic Dark Matter Search*, PhD thesis, University of California, Berkeley (2000), Appendix B, "Noise and Optimal Filtering".
4. W. H. Press, S. A. Teukolsky, W. T. Vetterling and B. P. Flannery, *Numerical Recipes in C: The Art of Scientific Computing*, 2nd ed. (Cambridge University Press, 1992): chapter 12, Fast Fourier Transform, p. 496; chapter 13, section 13.3, Optimal (Wiener) Filtering with the FFT, p. 547.
5. A. E. Szymkowiak, R. L. Kelley, S. H. Moseley and C. K. Stahle, "Signal processing for microcalorimeters," *Journal of Low Temperature Physics* **93**(3-4), 281 (1993).
6. P. D. Welch, "The use of fast Fourier transform for the estimation of power spectra: a method based on time averaging over short, modified periodograms," *IEEE Transactions on Audio and Electroacoustics* **15**(2), 70 (1967), [doi:10.1109/TAU.1967.1161901](https://doi.org/10.1109/TAU.1967.1161901).

## Caveats

- **PBS2 (DCRC4) may not be a normal phonon channel.** Its noise is flat and about an order of magnitude below the other working channels at low frequencies (Figure 4), and it passes the quiet-noise cut for 958 of the 1008 randoms, against 101 to 180 for the others. This could mean the channel is superconducting or otherwise not biased into its transition. The [UMN wiki](https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76.html) does not say so: it never mentions superconducting channels, and its only related remark is that three channels (`pB`, `pD`, `pE`, with no side given) "had railed in the middle of the data period" in October. The run configuration we read for another series (`07220916_2200`) lists zero QET bias on all four DCRC4 channels, with the feedback of channel 0 disabled, which fits a channel that is not in transition but does not prove it. Until this is confirmed, the spectra of PBS2 should not be taken as a phonon noise measurement.

## Results

### The cut: `clean_randoms`

The selection of randoms that we use from now on is called **`clean_randoms`**. It is the cut of Notes 2 and 2a, made on PBS1 (S1): a random trigger (`pc.randoms`) whose trace falls in the Tight excursion band of the 500-sample pretrigger window (`pc.excursion_band`) and has `log10(bstd) < 0.5`. In series `07221203_2025`, dump F0001 it keeps **101 of the 1008 randoms**, none with a pulse or a big tail in any channel (Appendix B). It is defined by the function `clean_randoms_cut` in [`chan0-cut-on-all-channels-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/chan0-cut-on-all-channels-buddy.ipynb) (section 13), and the code below is that function. `clean_randoms` is a True/False value for every event of the dump; because the three boards share their events in the same order, the same list selects the clean random traces of every channel.

```python
import sys
from pathlib import Path
import numpy as np
from nsdf_dark_matter.idx import load_all_data

REPO = next(p for p in [Path.cwd().resolve(), *Path.cwd().resolve().parents] if (p / "python" / "pulse_io.py").exists())
sys.path.insert(0, str(REPO / "python"))
import pulse_io as pio
import pulse_quantities as pq
import pulse_cuts as pc
from pulse_config import PulseConfig

config = PulseConfig(pretrigger_samples=500, glitch_samples=10, sample_period_s=1.6e-6)

def clean_randoms_cut(pulses, trigger_types, config=config):
    """Randoms with no pulse: a random trigger in the Tight excursion band with log10(bstd) < 0.5."""
    with np.errstate(all="ignore"):
        quiet = pc.excursion_band(pulses, config) & (np.log10(pq.bstd(pulses, config)) < 0.5)
    return pc.randoms(trigger_types) & quiet

cdms = load_all_data(str(Path.home() / "idx" / "07221203_2025_F0001"))
det1 = pio.filter_by_detector(cdms.get_detector_ids(), 1)
_, pulses = pio.load_channel_batch(cdms, det1, 1)               # Side1pB: detector 1, channel 1
clean_randoms = clean_randoms_cut(pulses, pio.trigger_types(cdms, det1))   # True for the events of the cut
print(clean_randoms.sum(), "of", len(clean_randoms), "events")

det0 = pio.filter_by_detector(cdms.get_detector_ids(), 0)
_, other = pio.load_channel_batch(cdms, det0, 0)                # any other channel: same events, same order
traces = other[clean_randoms]                                   # its clean random traces
print(traces.shape)
```

Run it from inside the `NSDF-Data` folder, after downloading the dump to `~/idx`. It prints `101 of 1517 events` and `(101, 4096)`. The library prints a warning that `pc.randoms` is under development, because it assumes the trigger labels are swapped (Note 2a).

### The PSDs

I've made the current best estimate of the noise PSD specifically focusing on the series `07221203_2025`. The PSDs are accessible via [`psd-clean-randoms-07221203_2025_F0001.h5`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/psd-clean-randoms-07221203_2025_F0001.h5) file (pinned to `bf0ed61`, 270 kB), and can be accessed by:

```python
import h5py
import numpy as np

with h5py.File("data_analysis/R76/student/buddy/psd-clean-randoms-07221203_2025_F0001.h5", "r") as f:
    freq = f["frequency_hz"][:]                       # Hz, shared by all channels
    events = f["event_numbers"][:]                    # the 101 clean_randoms events
    psd = {name: (g["psd_mean"][:], g["psd_sem"][:])  # counts^2/Hz and its standard error
           for name, g in f["channels"].items()}

mean, sem = psd["Side1pB"]
print(len(events), "events;", len(psd), "channels:", ", ".join(psd))
print(f"Side1pB at {freq[100]:.0f} Hz: {mean[100]:.2e} +/- {sem[100]:.1e} counts^2/Hz")
```

Run it from the `NSDF-Data` folder. It prints the number of events and the 7 working channels (`Side1pB`, `Side1pE`, `Side1pF`, `Side2pB`, `Side2pC`, `Side2pE`, `Side2pF`: PBS1, PES1, PFS1, PBS2, PCS2, PES2 and PFS2 in the notation above); the dead channels have no spectrum. The PSDs are the mean over the 101 events of the `clean_randoms` cut, in counts²/Hz, with the standard error of the mean; the layout of the file is described in section 7 of [`psd-clean-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/psd-clean-randoms-buddy.ipynb), which also makes them. The caveats above apply, in particular to PBS2.

## Next steps

**Next steps.** There are two possibilities:

1. **Calibrate the PSD in amps.** Get the calibration for the PSD so that we can write the noise in amps, and later compare it with the theoretical best resolution. This will probably be difficult, because it is not clear that the [UMN wiki](https://villano-lab.github.io/R76Analysis/index.html) has the necessary information. As far as we found, the [DCRC v3 page](https://villano-lab.github.io/R76Analysis/cdms/dcrc/dcrcv3.html) gives the size of one ADC bin (14 bits over ±1.25 V, 152.6 µV per bin) but not the feedback resistor, the SQUID coil ratio or the TES bias power, which are needed to turn counts into amps.
2. **Find triggered pulses.** Find triggered pulses in dump 2 or later, so we can continue on the path of running the Optimal Filter on pulses.

## Appendix A: the strictest cut (every working channel)

The strictest version of the selection keeps a random only if it passes the quiet-noise cut (the Tight excursion band and `log10(bstd) < 0.5`) in **every working channel**. Seven of the 12 channels work and five are dead (their signal never changes), so the cut is applied to the seven. It keeps **31 of the 1008 randoms**, far fewer than the 141 that pass on PCS2 alone. Each of the six working channels on DCRC1 and DCRC3 passes the cut for only 101 to 180 randoms on its own (DCRC4's PBS2 for 958), and the events that fail are not the same in all of them. Any two of those six channels share 62% to 89% of the smaller set (well above the 11 to 29 events expected by chance), but each further channel removes more, so only 31 events pass in all of them, 31% of the 101 of PBS1, the strictest channel. The Tight excursion band does most of the rejecting: only 116 to 189 of the 1008 randoms fall in the band on each of those six channels, while the `log10(bstd) < 0.5` condition keeps 770 to 895.

Figure 5 shows the 31 traces themselves in every channel (section 12 of [`chan0-cut-on-all-channels-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/chan0-cut-on-all-channels-buddy.ipynb)): none of them has a pulse or a ramp, and they all look like noise, but there are only 31 of them. Figure 6 shows their noise power spectra, the mean of the 31 traces in each channel (section 11 of [`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/bf0ed61/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb)). With so few traces the spectra are jagged from bin to bin, and no spread between the traces is drawn. This is why a cut that is not required to hold on all channels, and so keeps more traces, is worth looking for.

![](img/global-cut-traces-07221203_2025_F0001.png)

**Figure 5: The 31 randoms that pass the quiet-noise cut in every working channel, in every channel.** One tile per channel (rows are the boards DCRC1, DCRC3 and DCRC4), with the traces drawn over each other with transparency, baseline-subtracted, on a free vertical scale. Blue is Side 1 and orange is Side 2; no trace contains a pulse. The 5 tiles with grey text are the dead channels.

![](img/allchan-psd-by-side-07221203_2025_F0001.png)

**Figure 6: Noise spectra of the 31 randoms that pass the quiet-noise cut in every working channel, by side.** Side 1 on the left (3 working channels) and Side 2 on the right (4 working channels), one colour per channel within each panel (the colours are not shared between the panels). Each curve is the one-sided PSD (counts²/Hz), computed as the mean over the 31 traces of the squared Fourier amplitude of each trace (baseline-subtracted, first samples skipped) scaled to a one-sided density; the spread between traces is not drawn. Both panels share the same axes. The five dead channels are not shown.

## Appendix B: the cut on PCS2 and the cut on PBS1

**What the PCS2 cut lets through.** Of the 141 randoms that pass the cut on PCS2, 10 have a pulse or a big tail in some channel: 2 contain a pulse and 8 more have a baseline sag of more than 30 counts across the trace. Figure 7 shows only these 10, each in its own colour, which is the same in every tile. Event 10550 (light green) steps up by about 273 counts in PFS1 (at sample 1139) and by about 359 counts in PES2 (at sample 1171), falls back at sample 1219 in both, and steps up again at samples 1323 and 1355. Event 10034 (light blue) is a long decay in the three DCRC3 channels, down to about -100 counts. The big tails are in DCRC3, and the sag is largest in PBS1 for 8 of the 10 events (up to 133 counts for event 10027). In the framed PCS2 tile, and in PBS2 on DCRC4, the same 10 traces lie in the same noise band as all the others, which is why the PCS2 cut cannot see them.

![](img/chan0-cut-with-pulses-or-big-tails-07221203_2025_F0001.png)

**Figure 7: The 10 randoms that pass the PCS2 cut but have a pulse or a big tail in some channel.** They are drawn in every channel, but the tails are in a few of them (mainly the three DCRC3 channels, on both sides); the other channels show only noise. The cut is made on PCS2 (framed). One colour per event, the same in every tile, and the legend gives the event numbers and whether each has a pulse or a big tail (a sag of more than 30 counts across the trace). One tile per channel (rows are the boards DCRC1, DCRC3 and DCRC4), baseline-subtracted, on a free vertical scale. The 5 tiles with grey text are the dead channels.

**The cut on PBS1 only.** The cut we will use is the one of Notes 2 and 2a on PBS1 alone: a random whose trace passes the Tight excursion band and `log10(bstd) < 0.5` on that channel. It keeps **101 of the 1008 randoms**, more than the 71 of the cut on one channel of each side and the 31 of the cut on all channels, but fewer than the 141 of the PCS2 cut. There is nothing in it that is not noise: none of the 101 events contains a pulse in any working channel, and the largest baseline sag in a Side 2 channel is 13 counts, where a sag of more than 30 counts counts as a big tail (section 10 of the notebook). Figure 8 shows the 101 events in every channel at full scale.

![](img/cut-on-S1-only-full-07221203_2025_F0001.png)

**Figure 8: The 101 randoms that pass the cut on PBS1, in every channel, at full scale.** The cut is made on PBS1 (framed). One tile per channel, with the traces drawn over each other with transparency, baseline-subtracted. Blue is Side 1 and orange is Side 2; no trace contains a pulse. The 5 tiles with grey text are the dead channels.
