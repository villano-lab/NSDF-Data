---
id: "TBD"
title: "What is the current best PSD estimate from series 07221203_2025?"
author: "Buddy Holly (A. Villano)"
date: "2026-10-05"
status: "In progress"
keywords: "PSD, Noise, Randoms, PuBe"
description: "I took all of the clean randoms selected in Note 2 and produced a noise PSD for 07221203_2025. Since there are no known real pulses in those noise traces this is a true characterization of our noise environment."
---

## Code repository

- [`noise-psd-randoms-buddy.ipynb`](https://github.com/villano-lab/NSDF-Data/data_analysis/R76/student/buddy/noise-psd-randoms-buddy.ipynb) — the notebook for everything below. Pinned to `2ceffd`: the link shows the notebook as it was at that commit, which may be older than the latest version, and the file may have moved since (see `data_analysis/README.md`).

## Data and setup

We are using the file 07221203_2025_F0001, which is series 07221203_2025, Dump 1. The first 1000 events are ``random'' triggers; random triggers are snapshots of our detector traces taken at any time (rather than when a pulse occurs) to sample the noise environment. The line in the third code block of the `noise-psd-randoms-buddy.ipynb` notebook shows the randoms cut defined as `quiet_noise = pc.excursion_band(pulses, config_500) & (np.log10(bstd_500) < 0.5)` in addition to selecting the trigger specification for random events.  

::: callout
**Note.** The trigger specifications have the wrong wording (see [Note 2a](https://villano-lab.github.io/NSDF-Data/notes/note-02a-bstd-vs-time.html#randoms))
:::

It may also be useful to have a diagram of the detector and which channels are working during the R76 run period at UMN. 

![Two sides of detector S104, the 7 working channels are displayed on the top and bottom (Side 1 & 2).](img\channel-status-07221203_2025_F0001.png)

## The question

Based on this series' "Beginning of Run Randoms (BORR)," what is our best estimate for the noise environment of the experimental setup? The noise environment is typically summarized in terms of the Power Spectral Density (PSD).

## Results



![Caption: Channel 0 examples of clean random traces.](img/chan0-traces-07221203_2025_F0001.png)

## Reading

## Caveats

## Next steps
