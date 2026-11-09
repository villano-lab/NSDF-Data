---
title: "Finding the Am-241 peaks"
subtitle: "NSDF-Data student guide 10 — an exploration, for every computer"
date: "Version 2 · 9 November 2026"
---

::: tip
**This is a guide to a question, not a recipe.** It tells you what to look for and gives hints in three levels. It does not tell you which cells to run. Work out your own way, and open the next level of hints only when you are stuck. Notes about what you tried, including what did not work, are welcome.
:::

## The question

Part of the Run 76 data was taken with an **Am-241 source** near the detector. Americium-241 emits a gamma ray of **59.54 keV** and a whole family of lower-energy X-rays and gamma rays from the neptunium it turns into. In a good spectrum these show up as **peaks**: bumps at fixed energies on top of a smooth background.

**Can you find the Am-241 peaks in the Run 76 data, say which energy each one is, and show how sure you are?**

You are not given a calibration. The detector reports an uncalibrated pulse size (the *integral* of the pulse, in ADC counts), not keV. Finding the peaks and putting energies on them is the same job: once you know which bump is which line, the bumps *are* your calibration.

## Before you start

- You finished the setup guide and the first analysis for your computer, and you can open a notebook and plot a pulse.
- You know what a *series*, a *dump*, an *event* and a *channel* are (guide 2).
- You have data to look at: the file described in *Your first look* below. It holds the events of one region of the detector at one voltage. If you want other data, ask the project lead; you can also process dumps yourself with goldpan.

::: careful
**Do not run anything that rewrites a shared file.** If a notebook writes an `.h5` file or a processed folder, check with the project lead first. Read the data, and write your own results somewhere of your own.
:::

## Your first look: load, then histogram

This is one way to get started. It is the only code in this guide, and it is a starting point to change, not a solution.

The data is one **Parquet file** (about 14 MB, from the project's GitHub releases), with one row per event: 129,539 events of Run 76 taken at -82 V, all close to the place on the detector where the Am-241 source events cluster. The columns are `series`, the position on the detector (`xdel_us`, `ydel_us`), and one column for each of the six channels (`Side2pA` to `Side2pF`). Each channel column holds two quantities: `window_integral` (the pulse size) and `baseline_mean`. The example downloads the file, pulls out two quantities of channel A, and draws a 1D histogram and then a 2D histogram. Paste it into a notebook cell.

```python
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

# 1. Download the data once (about 14 MB), then load it.
URL = ("https://github.com/villano-lab/NSDF-Data/releases/download/"
       "data-am241-v1/am241-patch-82v.parquet")
path = Path("am241-patch-82v.parquet")
if not path.exists():
    urllib.request.urlretrieve(URL, path)
table = pq.read_table(path)
print(table.num_rows, "events;", table.schema.names)

def quantity(table, channel, name):
    """One quantity of one channel, as a numpy array.
    Each channel is a column of its own."""
    col = table[f"Side2p{channel}"].combine_chunks()
    return pc.struct_field(col, name).to_numpy(zero_copy_only=False)

# The pulse size of channel A, and the baseline of the same events.
size = quantity(table, "A", "window_integral")
baseline = quantity(table, "A", "baseline_mean")
# Look at the numbers before you choose a plotting range.
print(np.percentile(size, [1, 50, 99]))
print(np.percentile(baseline, [1, 50, 99]))

# 2. A 1D histogram: how many events at each pulse size?
# The range and the number of bins are your choice.
fig, ax = plt.subplots()
ax.hist(size, bins=200, range=(0, 1.0))
ax.set_xlabel("window_integral of Side2pA (uncalibrated)")
ax.set_ylabel("events per bin")
ax.set_yscale("log")

# 3. A 2D histogram: the same events, pulse size against baseline.
lo, hi = np.percentile(baseline, [0.5, 99.5])
fig, ax = plt.subplots()
h = ax.hist2d(baseline, size, bins=(100, 200),
              range=((lo, hi), (0, 1.0)), norm="log", cmin=1)
fig.colorbar(h[3], label="events per bin")
ax.set_xlabel("baseline_mean of Side2pA (ADC counts)")
ax.set_ylabel("window_integral of Side2pA")
plt.show()
```

Things to try next, on your own:

- What do the printed percentiles tell you about the range worth plotting? Change the ranges and bins until the picture is useful.
- The events are not all alike. The table also has `series`, `xdel_us` and `ydel_us`. Do the histograms change if you separate the series, or cut on the position?
- Repeat for the other five channels. Replace the `"A"` and look at the 2D picture again.

## What you can lean on

You do not have to find the energies in the data. They are known, and **their ratios do not depend on your detector**:

- the lines you are looking for are at fixed energies, and
- the pulse size is, to a good approximation, proportional to the energy.

So a line at twice the energy of another sits at about twice the pulse size, with no offset. That is a very strong check: a candidate peak that does not fit the ratios is probably not an Am-241 line.

Which lines, and at what energies, is for you to look up. Good places to start: the decay scheme of Am-241 (Nuclear Data Sheets, or a reference such as LNHB's table), and the X-ray lines of neptunium. Write down the table you build, with a source for every number, and put it in your note.

## A way of working

You do not have to follow this order. It is only a map.

1. **Make the picture first.** Histogram the pulse size of one channel for the events you were given. Try different binning, a log scale, and different ranges. What is the most obvious feature? What changes when you zoom in?
2. **Decide what an "event" is for this question.** The source does not trigger every event, and the detector also records noise and other particles. Which events do you keep, and why? Look at a few pulses by eye before you decide.
3. **Look for bumps, then check them.** Mark the ones you believe. For each, ask whether it survives a different binning, a different range, and a different set of events.
4. **Match bumps to lines.** Use the ratios above. Start with the one you are surest of.
5. **Put a number on each peak.** Where is it, how wide is it, how many events are in it? Say how you got the numbers (a fit, a mean, a read-off from the plot), and how much you trust them.
6. **Look at what is left.** Which bumps do you *not* understand? Say so. An honest "I do not know what this is" is a result.

## Hints

Open these one level at a time.

::: tip
**Hint level 1: the data.** The pulse size you histogram is a sum over the trace, so anything that shifts the trace shifts the answer. Plot the pulse size against the baseline of the same event. Does the spectrum look the same for every baseline? If a feature smears out when you plot all events together, ask what it would look like if you separated them first.
:::

::: tip
**Hint level 2: the channels.** There are six sensors, and they do not see the same share of an event's energy. Do they give the same spectrum? What happens if you add them? Does the sum look better or worse than the best single channel, and is that the same at low and high energy? Where on the detector the event happened may matter too.
:::

::: tip
**Hint level 3: the fit.** A peak on a falling background is not a Gaussian by itself. If you fit one, think about what you are asking the fit to do with the background, and what range of the data you give it. Try more than one range and see whether the position moves. When two lines are closer than the width of a peak, fit them together or say that you cannot separate them.
:::

## What a good answer looks like

- A spectrum with the peaks marked, with axes you can read.
- A table: for each peak, its position in pulse-size units, the energy you assign to it, and how you decided.
- A plot of energy against pulse size for the peaks you trust, and a statement of how straight it is and whether it passes through zero.
- A short list of what you could not explain.

You are not expected to find every line. A secure calibration from the two or three strongest peaks is a better result than a long list you are not sure of.

## When you write it up

Use guide 3 to write a note, and guide 4 to publish it. A note on this question should say which series and which events you used, what you cut and why, and which numbers you are confident in. Pin your notebook to the commit that produced the results.

## Session Info

Guide version 2, 9 November 2026. Written for every computer. Please tell the project lead where a step was unclear, or where a hint gave too much away or too little.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, say which series you are using, what you have plotted so far, and what surprised you.

## Key links

- Notes site: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
- goldpan documentation: <https://villano-lab.github.io/goldpan/>
