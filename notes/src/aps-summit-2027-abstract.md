---
id: "12"
title: "George Spilver APS Global Physics Summit 2027 Poster Presentation"
author: "George Spilver"
date: "2026-11-03"
status: "In progress"
keywords: "APS, Global Physics Summit, abstract, noise PSD, noise template, machine learning, optimal filter"
description: "I submitted an abstract for the APS Global Physics Summit 2027 on using a machine-learning model to choose the noise traces that build SuperCDMS noise PSD templates, and I plan to present it there in person; this note records the abstract and the plan."
---

## Summit Information
- **Meeting:** APS Global Physics Summit 2027
- **Dates and place:** Atlanta, Georgia, April 11th-16th
- **Session / category:** Undergraduate/Particle Physics
- **Format:** in person poster presentation
- **Co-authors and advisors:** Anthony Villano, Kathryn Mickleson

## The abstract

**Using Machine Learning to Categorize Noise Traces for SuperCDMS Power Spectral Density Templates**

The continued pursuit of direct dark matter detection relies on the ability to accurately measure low energy interactions, requiring as much mitigation of electronic noise as possible. One way this can be accomplished is by sampling the noise environment of the detectors, using raw traces (digitized sensor signals containing either noise or an event pulse) to create a Power Spectral Density (PSD) noise template by averaging the squared magnitudes of Fast Fourier Transforms of selected noise traces. The Optimal Filter algorithm uses the PSD template and an ideal pulse shape template to reduce noise and find best-fit values for event energy and time. Currently, in open test data from the University of Minnesota taken with a SuperCDMS detector and an intense neutron source, which generates dark matter-like events, only about 10% of randomly triggered traces pass our selection cuts. We are incorporating machine learning into the process of categorizing noise samples. By analyzing both time and frequency domain features, a tree-based ensemble model can identify anomalous noise traces and categorize them as good or bad, strengthening the PSD template by building it from a larger and more accurate selection of noise traces. In future work, we will quantify model performance and build PSD templates for localized sections of data. <!-- numbers-ok -->

## Where the numbers and ideas come from

- The "about 10%" is the current selection of clean random triggers in series `07221203_2025`, dump `F0001`: 101 of 1008 randoms ([Note 9](student-psd-clean-randoms-07221203-2025.html), after Notes 2 and 2a). <!-- numbers-ok -->
- The selection cuts are described in [Note 2](note-02-noise-selection.html) and [Note 9](student-psd-clean-randoms-07221203-2025.html); the noise PSD in [Note 3](note-03-noise-psd.html).
- My first machine-learning and Fourier-transform work is in `data_analysis/legacy/` (`MLmodelImplementaion.ipynb`, `Fourier Transform Analysis.ipynb`). The analysis behind the abstract is still in progress and will get its own notes as each step is done.

## Budget
Estimated cost of attendance: <!-- numbers-ok -->

| Item | Estimate |
|---|---|
| Registration | $385 | <!-- numbers-ok -->
| Airfare | $700 round trip | <!-- numbers-ok -->
| Ride from the airport | $50 | <!-- numbers-ok -->
| Hotel | $350 per night, 6 nights | <!-- numbers-ok -->
| Per diem | $86 per day, 6 days (0.75x of that on the first and last day) | <!-- numbers-ok -->
| **Total** | **$3700** | <!-- numbers-ok -->

I aim to get funding through a EUReCA student research grant, as well as any other possible grants/resources from the Physics department, and the rest will be covered by the DOE grant.
