---
id: "TBD"
title: "Can a machine-learning classifier pick the noise traces for a PSD template better than the current cut?"
author: "George Spilver"
date: "2026-11-02"
status: "In progress"
keywords: "noise PSD, noise template, machine learning, optimal filter, gradient boosting, randoms, 07221203_2025"
description: "A tree-based classifier that picks noise traces for the PSD template, run on Run 76 dump 07221203_2025_F0001: its template agrees with a robust reference at low frequency where the current cut's sits higher, but with the settings carried over from the sample data it keeps fewer randoms than the current cut, and the reason is now known."
---

<!--
==========================================================================================
HOW TO USE THIS DRAFT  (read once, then delete this whole box)
==========================================================================================
Everything between the comment markers (the less-than, exclamation mark, two dashes at the start and two
dashes, greater-than at the end) is a COMMENT. Comments never appear on the website, so all my explanations
live in them. There are two kinds:

  [COMMENTARY]  my explanation of what a section is for, why I put things there, and what your professor's
                format expects. Read it, then delete it.
  [YOUR TURN]   something only you can do: your name, your conclusions, a decision. Search the file for
                "YOUR TURN" to find every one of them.

When the file has no comments left, it is your final copy.

HOW THE NOTES SYSTEM WORKS (the parts that matter for this note):
- This file IS the note. The website page is generated from it automatically. The header block at the very
  top (between the two lines of three dashes) is the only required part.
- Leave  id: "TBD"  alone: your professor (or the bot on the pull request) gives the note its number.
- Status stays "In progress" until the question is answered and you will not change the note again.
- Every "##" heading becomes a section, and the clickable outline at the top of the page is built from them.
  Do not write an outline yourself.
- Pictures live in notes/src/img/ and are named after the note: ml-noise-selection-r76-fig1.png and so on.
  A picture line is: exclamation mark, the caption in square brackets, the file in round brackets.
- Every number in the text must be printed in the notebook's saved output. The checker below verifies it.
  If you change a number, rerun the notebook (do not type a new number by hand).
- Code links point at one exact commit (here d6a07ce), so they keep showing the code that made the numbers.
  The website adds a small "latest" link next to each one by itself.
- Math goes between dollar signs, exactly as written below. A box for a warning or correction is a paragraph
  between two lines of three colons (see the guide "Writing a note", section "A coloured box").
- Before asking for review, run this from the NSDF-Data folder with the darkmatter_cli_env environment active:
      python tools/check_note.py notes/src/ml-noise-selection-r76.md
  Its last line must say "ready for review". It also lists numbers it cannot find in the notebook output.
- Publishing: commit this file and its five pictures on student-george, push (GitHub Desktop: Push origin),
  open a pull request into develop. It goes live about two minutes after your professor merges it.
  Nothing is on the website before that, but your branch on GitHub is public.
==========================================================================================
-->

<!-- [YOUR TURN] Put your full name in the "author" line of the header above. -->

<!-- [COMMENTARY] The title. The guide asks for the note's question, written as a sentence. I kept the
question of your abstract. The description (header) is one sentence on what was done and found; rewrite it
in your words once you have read the results. -->

## Code repository

<!-- [COMMENTARY] Required in practice: every file that made a number, each pinned to the commit that made
it. d6a07ce is the Run 76 run; 1f80598 is the earlier run on the sample data. Do not shorten these links:
the website only adds its "latest" link to links written in full like this. -->

- [`noise-template-ml-r76.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/d6a07ce/data_analysis/R76/student/george/noise-template-ml-r76.ipynb): the notebook for everything below on Run 76 (features, classifier, the three selections, templates, the optimal-filter check, local templates, and two diagnostics). Pinned to `d6a07ce`, the run of 2 November 2026.
- [`noise-templates-ml-07221203_2025_F0001.h5`](https://github.com/villano-lab/NSDF-Data/blob/d6a07ce/data_analysis/R76/student/george/noise-templates-ml-07221203_2025_F0001.h5): the templates it writes, with every trace's $p_\mathrm{good}$ and which events are randoms.
- [`noise-template-ml-george.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/1f80598/data_analysis/R76/student/george/noise-template-ml-george.ipynb): the same method on the sample data of series `07180827_0000`, where it was developed (section *Where this started*). Pinned to `1f80598`.
- [`MLmodelImplementaion.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/1f80598/data_analysis/legacy/MLmodelImplementaion.ipynb): my first Isolation Forest (my FFT and PSD work is `Fourier Transform Analysis.ipynb`, in the same folder).
- The library, at `d6a07ce`: [`goldpan/cuts.py`](https://github.com/villano-lab/NSDF-Data/blob/d6a07ce/python/goldpan/cuts.py) (`randoms`, `excursion_band`), [`goldpan/quantities.py`](https://github.com/villano-lab/NSDF-Data/blob/d6a07ce/python/goldpan/quantities.py) (`pretrigger_std`, `max_deviation`, `power_spectrum`) and [`goldpan/channels.py`](https://github.com/villano-lab/NSDF-Data/blob/d6a07ce/python/goldpan/channels.py) (the channel names).

The notebooks were written with an AI coding assistant (Claude Code), starting from my earlier notebooks; I have run them, and I am checking their results (section *What I still have to verify*).

<!-- [YOUR TURN] Keep or reword the sentence above. I recommend keeping it: the guides weigh honesty about
where code and numbers come from very highly. -->

## Data and setup

<!-- [COMMENTARY] The guide asks for: which series, dump, detector and channels; which quantities; which
windows and cuts; and a definition of every word a newcomer would not know, given once here and used the
same way afterwards. That is why the quantities are a list. -->

**Data.** Run 76 at the University of Minnesota, series `07221203_2025`, dump `F0001`: a SuperCDMS-type detector with a PuBe neutron source, read out on Side 2. It is the dump of Notes 2, 2a and 9. The dump has 1517 events over 58 s: 1008 recorded as `Physics`, taken to be **random triggers** (*randoms*, `cuts.randoms`), and 509 recorded as `Unknown`, taken to be real triggers. The six sensor channels are used, named by the library's channel map: `Side2pA` to `Side2pF`. DCRC4 pA, the NaI trigger input, is left out.

**Processing.** The readout is the library's `DCRC_RUN76`: $\Delta t = 0.8\ \mu\mathrm{s}$ per sample, 4096 samples per trace. Each trace has its pretrigger mean (the first 500 samples) subtracted, and its first 10 samples dropped (an electronics glitch), leaving 4086 samples.

![**Figure 1.** Channel `Side2pC`, dump 07221203_2025_F0001, all 1517 traces. Left: the largest deviation from the pretrigger mean (log scale), for the randoms (blue) and the other, triggered events (orange). Right: three randoms (blue) and two triggered events (orange). Look at the overlap on the left: some randoms hold pulses, and some triggered events look like noise.](img/ml-noise-selection-r76-fig1.png)

In `Side2pC` the median of that largest deviation is 12.3 counts for the randoms and 190.6 counts for the other events (Figure 1).

**Quantities.**

- A **trace** is one channel's digitized signal for one event. A **noise trace** holds no pulse.
- $\sigma$ is the pretrigger standard deviation of a trace (`bstd`). A channel's **typical noise σ** is the median $\sigma$ of its quietest traces: 1.53 to 2.58 counts here.
- The **PSD** of a trace is the one-sided power spectral density $S[k] = \frac{2\,\Delta t}{N}|X[k]|^2$ in counts²/Hz, with $X[k]$ the FFT of the $N$-sample trace. A channel's **noise template** is the mean PSD of the randoms a method accepts. The figures show its square root, the amplitude spectral density (ASD).
- The **optimal filter (OF)** fits the amplitude $\hat A$ of a pulse of known shape $s$ in a trace $v$, weighting each frequency by the noise template $J$:
$$\hat A = \frac{\sum_k \mathrm{Re}(S_k^* V_k)/J_k}{\sum_k |S_k|^2/J_k}.$$
Its **resolution** $\sigma_A$ is the spread of $\hat A$ on pure noise: *predicted* from the template, and *realised* by measuring that spread on held-out randoms. The pulse shape of each channel is the average of 59 to 276 clean triggered pulses.
- The **current cut** is `clean_randoms` of Note 9: a random trigger whose `Side2pA` trace is in the Tight excursion band ($0.5 \le \log_{10}$ ratio $< 0.7$) and has $\log_{10}\sigma < 0.5$. The event list it gives is used for every channel. Rebuilt in this notebook, it keeps 101 of the 1008 randoms, the number Note 9 gives.

## The question

<!-- [COMMENTARY] The guide: "the question again, and why it matters". This is your abstract's motivation in
note form. The guide wants the question to be specific enough that the note can answer it. -->

The optimal filter needs a noise template made only from noise, and the current cut keeps 101 of the 1008 randoms of this dump. Every good trace it throws away is noise information lost, and any small pulse or tail it lets in raises the low-frequency end of the template. Can a machine-learning classifier, using time-domain, frequency-domain and optimal-filter features of every trace, keep more of the real noise while still rejecting contaminated traces, and does that give a better template?

## How the classifier works

<!-- [COMMENTARY] The method, kept to what a reader needs to trust the numbers. The full details (every
setting) are in the notebook, which is linked; the guide prefers linking code over pasting it. The feature
table answers your old question "what actually decides good versus bad". -->

**Features.** Each trace is described by 26 numbers that a person could check by eye:

| Group | Features | What they catch |
|---|---|---|
| Time domain | `log_bstd`, `log_std_post`, `log_maxdev_pre`, `log_maxdev_post`, `log_ratio`, `smooth_peak`, `drift`, `slope`, `spike`, `skew`, `kurt` | a noisy pretrigger, a pulse after the trigger, small slow pulses, tails of earlier pulses, glitches |
| Frequency domain | `band_0` to `band_7` (8 log-spaced bands), `psd_peak`, `psd_mean_log` | the trace's power in each band against the channel's median: pulses and tails put power at low frequency |
| Optimal filter | `of_trig`, `of_peak` | the OF amplitude at the trigger time, and the largest anywhere in the trace, in units of the $\sigma_A$ of simulated noise |
| Across channels | `other_smooth`, `other_maxdev`, `other_of` | the same quantities in the other channels of the event: a real pulse shows in several at once |

Each feature is put on a common scale per channel (its distance from typical noise in robust spreads), so one model is trained on all six channels.

**Labels.** There are no hand labels. A trace is a **seed good** if all its time-domain, OF and cross-channel features are within 3 spreads of typical noise, and a **seed bad** if it is obviously not noise. The training set also holds **injected** bad traces with known truth: the channel's own pulse shape, spikes and slow drifts, added to seed-good traces at a range of sizes. The events are split in half first, and every result marked *test half* uses only events the classifier never saw.

**The classifier** is a gradient-boosted tree ensemble (`HistGradientBoostingClassifier`, scikit-learn), trained on every event of the training half: 122 good and 10781 bad traces (seeds and 7255 injections). It gives each trace a probability $p_\mathrm{good}$, and accepts it if $p_\mathrm{good} > 0.5$. Because the labels come from confident cuts and simulation, not from people, it is *semi-supervised*. The template is then built from the **randoms** it accepts. It is compared with the current cut and with an **Isolation Forest** (unsupervised anomaly detection, my first approach).

**Settings.** Every setting is the one chosen on the sample data (section *Where this started*); nothing was tuned on Run 76.

## What each method keeps, and what it rejects

<!-- [COMMENTARY] The results, number first, as the guide asks. Ranges over the six channels keep the
tables short; the notebook prints every channel. -->

| Randoms accepted (of 1008) | Current cut | Isolation Forest | ML classifier |
|---|---|---|---|
| per channel | 101 | 836 to 900 | 47 to 73 |
| seed-good randoms of the test half kept | 89.0% | 100.0% | 92.7% |

With the settings from the sample data, the classifier keeps **fewer** randoms than the current cut. The Isolation Forest keeps almost all of them, pulses included. Section *Why the classifier is too strict here* explains the first; the second is expected, because pulses are not rare enough in a dump to look like anomalies.

![**Figure 2.** Share of injected bad traces rejected, against their visible amplitude in units of the channel's noise σ, for injected pulses, spikes and drifts (test half, all six channels). Orange: current cut; green: Isolation Forest; blue: ML classifier. At the left end the injection is buried in the noise, so the share rejected there is the share of good noise each method throws away. Look at where each curve reaches 1.](img/ml-noise-selection-r76-fig2.png)

Figure 2 shows that the classifier rejects injected pulses and drifts at smaller sizes than the current cut does. It also shows the price: it rejects more of the traces whose injection is invisible, that is, more good noise. The area under the ROC curve for separating test seeds from injections of 3 σ and above is 0.9894 for the classifier and 0.6484 for the Isolation Forest.

![**Figure 3.** Permutation importance: how much the ROC AUC drops when one feature is shuffled. The largest OF amplitude in the trace (`of_peak`) and the largest sample-to-sample jump (`spike`) carry almost all of it; the frequency bands carry almost none.](img/ml-noise-selection-r76-fig3.png)

<!-- [YOUR TURN] Your abstract says the model analyzes "both time and frequency domain features". Figure 3
says the frequency bands contribute almost nothing on their own (permutation importance under-credits a
feature whose information another feature also carries, and the OF features are built from the noise
spectrum, so this is not a proof that they are useless). You said this is not a priority now: one sentence
here saying so is enough. -->

## The noise templates

![**Figure 4.** Noise templates of the six sensor channels by selection method, with the number of randoms in brackets. Top: ASD in counts/√Hz against frequency, log-log. Bottom: each template divided by the robust reference (the bin-by-bin median of the per-trace PSDs of the ML-accepted randoms, divided by ln 2). Look below 3 kHz: the current cut (orange) sits above 1, the classifier (blue) near 1, and the Isolation Forest (green) far above.](img/ml-noise-selection-r76-fig4.png)

The **robust reference** is the median of the per-trace PSDs divided by ln 2: for pure Gaussian noise that equals the mean, and a median is hardly moved by a few contaminated traces.

| | Current cut | ML classifier | Isolation Forest |
|---|---|---|---|
| Template / reference, 0.3 to 3 kHz | 1.251 to 2.705 | 0.857 to 1.083 | 536 to 1162 |
| Median relative standard error per bin | 0.098 to 0.099 | 0.114 to 0.141 | 0.035 to 0.053 |
| OF resolution, realised / predicted | 0.708 to 1.016 | 0.998 to 1.271 | 0.578 to 1.328 |

The resolutions were measured with templates from one random half of the events (54 randoms for the current cut, 18 to 33 for the classifier), applied to the seed-good randoms of the other half. In `Side2pC` the realised resolution is 0.511 counts with the current-cut template, 0.529 with the classifier's and 2.505 with the Isolation Forest's. As a check of the OF code, a pulse of amplitude 20 added to held-out randoms comes back 20.000 higher.

On pure noise the OF amplitude at the trigger averages 0. For the accepted randoms it averages −1.36 to −0.38 $\sigma_A$ (current cut) and −0.73 to −0.29 (classifier), and −0.75 to 0.03 for the seed-good randoms: slightly *negative*, which a hidden pulse would not cause. A slow downward drift of the baseline would (see *Caveats*).

## Why the classifier is too strict here

<!-- [COMMENTARY] This section reports a diagnostic I added after the first run, instead of retuning the
classifier until the numbers looked good: choosing the analysis is your decision, and the guide asks for
what was found, including what did not work. -->

Only 28 to 36 randoms per channel are seed-good, so the classifier learns "good" from very few examples. The diagnostic in the notebook (section 3.1) counts, for each feature, the share of randoms that fail the seed test:

| Feature | Randoms failing the 3-spread test |
|---|---|
| `other_of` | 95.8% to 96.4% |
| `of_peak` | 88.6% to 93.1% |
| `of_trig` | 48.8% to 74.6% |
| every other feature | at most 27.6% |

The three OF features are scaled against simulated Gaussian noise with a preliminary PSD, and real Run 76 randoms are far from that simulation. On the sample data this scaling worked. Here it rejects nearly every random as a seed, and the classifier inherits that strictness. This is a setting to change, not a property of the method (*Next steps*).

## Is one template per dump enough?

<!-- [COMMENTARY] This is the "localized templates" part of your abstract. On Run 76 it cannot be answered
yet, and the note says why; on the sample data it was answered (next section). -->

Not testable yet on this dump. The randoms are all in its first part: 189 or 190 in each of the first five blocks of events (event numbers 10000 onward), 54 in the sixth, and 2 and 4 in the last two, which hold the triggered events. The block test therefore finds no traces in the last blocks, and with 47 to 73 accepted randoms per channel the rolling templates could be built only from 30 neighbours. Those give the same realised resolution as the dump-wide template within a few percent (in `Side2pC`, 0.4470 against 0.4503 counts).

## Where this started: the sample data

<!-- [COMMENTARY] One note covers the whole line of work so far, as you asked: the method was built on the
sample data that came with the NSDF setup, and the earlier notebooks are linked in Code repository. Kept
short on purpose: the Run 76 sections above are the main result. -->

The method was first built on the sample data that came with the NSDF setup: series `07180827_0000`, dump `F0002` (7588 events, no random triggers, sample period assumed to be 0.8 µs). It is from Run 68, also with the PuBe source: `DataSeriesList.xlsx` (in `data_analysis/R76/series_lists/`, sheet Run68) lists it under the dataset `p40_PuBe_2`. <!-- numbers-ok --> It began as an Isolation Forest on three features (variance, slope and the correlation of two channels, `MLmodelImplementaion.ipynb`), grew into the classifier above, and was then moved to Run 76 with its settings unchanged.

On the sample data the classifier kept 2548 to 2629 traces per channel against 441 to 773 for the current cut, and kept 99.8% of the clean held-out traces against 23.7%. Its template agreed with the robust reference within 1.017 to 1.064 at 0.3 to 3 kHz, where the current cut's was low (0.761 to 0.910). One template per dump was enough there: blocks and rolling templates showed no change in time over its 62 s.

![**Figure 5.** The same comparison as Figure 4 on the sample data (series 07180827_0000, dump F0002, six channels named by dump index). The classifier (blue) keeps about four times as many traces as the current cut (orange) and sits on the reference below 3 kHz.](img/ml-noise-selection-r76-fig5.png)

<!-- [YOUR TURN] "about four times" in the Figure 5 caption is my reading of 2548-2629 against 441-773;
keep it or replace it with the two ranges. -->

## What this shows, and what it does not

<!-- [YOUR TURN] This is the "Reading": your interpretation. The guides say it must be yours, so the bullets
below are a draft to rewrite or replace, not to keep as they are. A sentence in the results sections states
a number; a sentence here says what it might mean. -->

- On both data sets the classifier's template agrees with the robust reference at low frequency, and the current cut's does not: low on the sample data, high on Run 76.
- On Run 76, with settings carried over unchanged, the classifier keeps fewer randoms than the current cut, so the gain the abstract describes (a larger selection) is not shown yet on Run 76. The cause is identified (the OF features in the seed definition), and is a setting.
- The classifier rejects injected pulses and drifts at smaller sizes than the current cut, at the cost of more good noise.
- The frequency-domain features are not shown to help (Figure 3).
- Whether local templates help cannot be decided from this dump.

## Caveats

<!-- [COMMENTARY] The guide strongly suggests caveats: "a note that states its limits is trusted more". These
are the ones a reader should know before trusting the comparison. -->

- **The robust reference is not independent of the classifier.** It is the median of the ML-accepted randoms, so the classifier's template agreeing with it is partly built in, especially with 47 to 73 traces. A reference built from all randoms, or from both selections, would be a fairer test.
- **The randoms label is an assumption** of the library (`cuts.randoms`: `Physics` taken to be the randoms, Note 2a), and so is the channel map. Both are marked under development.
- **The labels come from cuts and simulation.** No trace was labelled by hand, the injected shapes are idealized, and the pool of events seed-good in every channel is small (18 training and 17 test events), so the injection test reuses the same few events.
- **Drifts may be part of the noise.** The negative OF amplitudes and the drifting traces of Figure 1 suggest a slow baseline drift. The classifier is taught that drifts are bad, which may make it reject real noise.
- **One dump, one random split, settings unchanged from other data.** The numbers move with the random seeds.
- **The OF resolution uses no time shift;** a real analysis also fits the pulse start.

## What I still have to verify

<!-- [COMMENTARY] You said you still have to go through and verify the results of the notebook Claude Code
wrote. This checklist turns that into concrete steps, and keeps the note honest while it is In progress.
Tick items off (change the brackets to [x]) as you do them, or delete the section once all are done. -->

<!-- [YOUR TURN] Add anything else you want to check, and tick items as you go. -->

- [ ] Read the notebook section by section and confirm that each step does what its text says.
- [ ] Check by eye the traces the methods disagree on (notebook section 4.1).
- [ ] Recompute two or three numbers of this note by hand from the notebook output.
- [ ] Confirm the random-trigger label and the channel names with the project lead.
- [ ] Check that `clean_randoms` here is the same event list as Note 9's (both give 101; compare the event numbers).

## Next steps

<!-- [YOUR TURN] Keep, cut or reorder. The first item is the one that would make the classifier usable on
Run 76; your abstract's two future-work items are the third and the last. -->

- Scale the OF features against the randoms themselves (or drop them from the seed definition), rerun, and see whether the classifier then keeps more randoms than the current cut.
- Build the robust reference from all randoms, so the template comparison is independent of the classifier.
- Choose the Run 76 dumps to use on purpose (the same trigger and source, a fixed detector voltage; the notebook lists every series on NSDF), since `07221203_2025_F0001` is one example dump of one series.
- Quantify model performance: repeat with other random seeds and on those dumps.
- Test the local templates on the randoms only, in blocks of randoms rather than blocks of events, and on longer stretches of data.
- Retrain with and without the frequency-domain features to see what they add.
