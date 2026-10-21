---
id: "TBD"
title: "How can we normalize our pulses to QET current?"
author: "Anthony"
date: "2026-10-21"
status: "In progress"
keywords: "pulse, normalization, current, squid"
description: "Want a refresher on how to analyze the SQUID readout chain for SuperCDMS detectors and include tests (e.g. IbIs) that allow us to get the absolutely normalized TES output current. Scan the UMN Wiki for records of such tests for R76 data."
---

## Code repository

- [`your-notebook.ipynb`](https://github.com/villano-lab/NSDF-Data/blob/COMMIT/data_analysis/R76/student/yourname/your-notebook.ipynb) — the notebook for everything below. Pinned to `COMMIT`: the link shows the notebook as it was at that commit, which may be older than the latest version, and the file may have moved since (see `data_analysis/README.md`).

## Data and setup

This study is partly a search through our historical records and partly an exposition of how we work with the circuits that read out our detectors. The main historical records we have for R76 is the [UMN CDMS Wiki](https://villano-lab.github.io/R76Analysis/index.html) (or the recovered copy of it).

![readout circuit of SuperCDMS](img/tes-squid-readout-circuit.png)

**Figure 1: The TES bias and SQUID readout circuit.** The bias current $I_\mathrm{b}$ flows down from the top through two parallel branches to ground: the shunt resistor $R_\mathrm{sh}$, and the TES in series with the parasitic resistance $R_\mathrm{par}$ and the input inductor $L_\mathrm{i}$. $L_\mathrm{i}$ is coupled (mutual inductance $M$) to the SQUID, which is biased with a small current $I_\mathrm{sq}$. The amplifier reads the SQUID voltage, and its output $V_\mathrm{out}$ returns through the feedback resistor $R_\mathrm{fb}$ to the feedback coil $L_\mathrm{f}$ (mutual inductance $M_\mathrm{f}$) to hold the SQUID flux fixed, so $V_\mathrm{out}$ is proportional to the TES current.

**Measurements we make on a channel** (this list will grow):

- **IbIs** ($I_\mathrm{b}$ against $I_\mathrm{s}$): sweep the QET bias current $I_\mathrm{b}$, one channel at a time, and record the QET-branch current $I_\mathrm{s}$ (read from the SQUID) at each setting. The curve gives $R_\mathrm{n}$, $R_\mathrm{par}$, and the TES resistance and power along the transition [1, 2]. See the section on Ib-Is curves below.
- **dIdV**: inject a small, known triangle-wave test signal on the bias line (100 to 500 Hz, $\mathrm{d}I_\mathrm{b} = \mathrm{d}V_\mathrm{b}/R_\mathrm{bias}$) and measure the response $\mathrm{d}I_\mathrm{QET}$ at a fixed operating point: with the TES superconducting it gives $R_\mathrm{par}$, in the normal state $R_\mathrm{n}$ (once $R_\mathrm{par}$ is known), and in the transition the transition resistance. The wiki calls the method complex impedance [3, 4]. <!-- numbers-ok -->
- **RpRn**: the measurement of the parasitic resistance $R_\mathrm{p}$ and the normal resistance $R_\mathrm{n}$ with the test signal fed into the QET line. The wiki mentions it only by name (group meeting of 4 December 2025, "figure out why RpRn not working") and does not describe it [5]; we assume it is the dIdV measurement above, made in the superconducting and in the normal state.
- **dPdI**: the slope $\mathrm{d}P/\mathrm{d}I$ of the power in the TES against its current, in volts. It turns a measured current pulse into absorbed energy, $E = (\mathrm{d}P/\mathrm{d}I)\int \Delta I\,\mathrm{d}t$ (linear approximation), and the QET biases of Run 75 and Run 76 were set where $\mathrm{d}P/\mathrm{d}I = 1.0\ \mathrm{\mu V}$ [1, 6]. <!-- numbers-ok -->

## The question

How can we normalize our pulses to QET current? The most basic parameter we read out with our phonon sensors is the current through the Quasi-particle Electro-thermal-feedback Transition Edge Sensors (QETs) that make up our phonon channels. If we want to model our noise environment properly we must know what current the "pulses" are reading; typically pulses are read out in arbitrary voltage units depending on the Analog-to-Digital (ADC) conversion. 

## Pulses in QET current units

The ADC does not record the QET current directly. This section follows the chain from the recorded counts to the current in the QET branch of Figure 1, using what the UMN wiki says about each step [3, 6]. The numbers are the wiki's, not ours: none of them has been measured or checked in this note, and the last subsection lists what is not settled.

### From counts to the feedback current

The ADC records the voltage at the output of the SQUID feedback electronics. The SQUID is run in a flux-locked loop: the feedback current $I_\mathrm{fb}$ that flows through the feedback resistor $R_\mathrm{fb}$ into the feedback coil $L_\mathrm{f}$ makes a flux that cancels the flux of the QET-branch current $I_\mathrm{QET}$ in the input coil $L_\mathrm{i}$. So the SQUID is only a null detector, and the loop holds

$$M\, I_\mathrm{QET} = M_\mathrm{f}\, I_\mathrm{fb} ,$$

with $M$ and $M_\mathrm{f}$ the couplings of the input coil and of the feedback coil to the SQUID. The magnetic coupling of the QET branch to the SQUID therefore does not need to be known by itself; only the ratio $M/M_\mathrm{f}$ of the two couplings of the same SQUID matters.

The output voltage is $V = I_\mathrm{fb}\, R_\mathrm{fb}\, G_\mathrm{DCRC}\, G_\mathrm{driver}$, with the gains of the readout board (the DCRC) and of its driver stage, and the ADC converts it to counts. In the calibration code of the Run 76 summary [6] these are 6553.6 counts per volt, $R_\mathrm{fb} = 1233\ \Omega$, $G_\mathrm{DCRC} = 2$ and $G_\mathrm{driver} = 1$. <!-- numbers-ok -->

### From the feedback current to the QET current

The wiki divides by a "loop gain" $G_\mathrm{loop} = 10.5$ [6, 3], so that $I_\mathrm{fb} = 10.5\, I_\mathrm{QET}$. We read this as the coupling ratio $M/M_\mathrm{f}$ above (the input coil couples 10.5 times better to the SQUID than the feedback coil); the wiki does not define it. Altogether <!-- numbers-ok -->

$$I_\mathrm{QET} = \frac{N_\mathrm{ADC} / 6553.6\ \mathrm{counts/V}}{R_\mathrm{fb}\, G_\mathrm{loop}\, G_\mathrm{DCRC}\, G_\mathrm{driver}} = \frac{N_\mathrm{ADC}}{1.70\times 10^{8}\ \mathrm{counts/A}} ,$$

that is, one count is 5.9 nA of QET current, or about 170 counts per µA. A pulse of 29 counts, the largest height in event 11300, is then 0.17 µA, and one of 1000 counts is 5.9 µA. The 2016 wiki page on complex impedance [3] gives the same formula, with the gains named "fixed" and "variable". <!-- numbers-ok -->

A direct calibration of the whole chain exists in principle: the DCRC signal generator can inject a known triangle-wave current into the QET branch through a known bias resistor (the dIdV measurement above) [3]. We found no record of it for these channels. The normal-state IbIs curves give a consistency check of the conversion, described in the next section.

### What is not settled

- **The 10.5.** We found no derivation or independent measurement of the loop gain on the wiki, and our reading of it as $M/M_\mathrm{f}$ is an interpretation. <!-- numbers-ok -->
- **Which gain settings apply.** The ODB of series `07220916_2200` (16 September 2022) has `VGAGain` 5 on two channels of DCRC3 (`Side1pE` and `Side2pE`) and 2 on the others, and `PGAGain` 1 on all of them. We could not establish how these fields map onto $G_\mathrm{DCRC}$ and $G_\mathrm{driver}$ of the calibration code, so the 170 counts per µA may be wrong by a factor 2.5 for those two channels. The settings of the series used here (`07221203_2025`, started at 20:25 on 3 December 2022 [7]) have to be read from its own ODB. <!-- numbers-ok -->
- **The sample period.** The calibration code uses 0.8 µs per sample [6]; the notebooks of this note use 1.6 µs. The two have to be reconciled before any time integral is converted. <!-- numbers-ok -->
- **Which channels are QET channels.** `Side2pB` (DCRC4, channel pA) is probably not a QET channel in this series: the wiki's diaries of September and October 2022 use DCRC4pA as the input of the NaI trigger [8]. No QET current exists for it.

## Ib-Is curves

An IbIs scan gives the QET-branch current $I_\mathrm{s}$ for each bias current $I_\mathrm{b}$. In the circuit of Figure 1 the shunt carries $I_\mathrm{b} - I_\mathrm{s}$ and has the same voltage as the QET branch, so

$$R_\mathrm{TES} = R_\mathrm{sh}\left(\frac{I_\mathrm{b}}{I_\mathrm{s}} - 1\right) - R_\mathrm{par} ,$$

and the power in the TES is $P = I_\mathrm{s}^2 R_\mathrm{TES}$; $\mathrm{d}P/\mathrm{d}I$ follows from the curve. The only IbIs curves on the wiki are plots from Run 75 (February to April 2022, about 42 mK) [1, 2]: $I_\mathrm{s}$ against $I_\mathrm{b}$, $R_\mathrm{TES}$ against $I_\mathrm{b}$, $P$ against $I_\mathrm{b}$, and $R_\mathrm{TES}$ against $\mathrm{d}P/\mathrm{d}I$, for all measured channels except `Side1pF`. The data behind the plots are not in the archive, and there are no IbIs curves for Run 76 or for the December 2022 series. <!-- numbers-ok -->

### A check of the conversion against the curves

In the normal state the bias current divides between the shunt and the QET branch, $I_\mathrm{s} = I_\mathrm{b}\, R_\mathrm{sh} / (R_\mathrm{sh} + R_\mathrm{par} + R_\mathrm{n})$. For `Side2pC` the Run 75 summary [1] gives $R_\mathrm{sh} = 8.0\ \mathrm{m\Omega}$, $R_\mathrm{par} = 11.0\ \mathrm{m\Omega}$ and $R_\mathrm{n} = 60.8\ \mathrm{m\Omega}$ (from IbIs curves taken at about 42 mK), so at $I_\mathrm{b} = 350\ \mathrm{\mu A}$ the current is 35 µA, and the plot of the IbIs curves there shows about 33 to 35 µA for this channel. <!-- numbers-ok -->

This is a consistency check of the wiki's numbers with each other, and not an independent measurement of the gain: the wiki derived $R_\mathrm{n}$ and $R_\mathrm{par}$ from the same curves, using the same gain. The slope of the normal-state branch alone gives only $G\, R_\mathrm{sh} / (R_\mathrm{sh} + R_\mathrm{par} + R_\mathrm{n})$, with $G$ the counts per unit current, so one point in the normal state does not fix $G$ unless $R_\mathrm{n}$ is known independently. The ratio of the slopes in the normal and the superconducting state gives $R_\mathrm{n} / (R_\mathrm{sh} + R_\mathrm{par})$ without $G$, and $G$ then needs $R_\mathrm{sh}$ (assumed to be 8.0 mΩ). <!-- numbers-ok -->

## References

1. UMN CDMS wiki, Run 75 summary, sections "IbIs measurements" and "TES properties": [https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_75.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_75.html) (static archive of the wiki, mirrored March 2026).
2. UMN CDMS wiki, "Overview of IbIs automation technique": [https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_75/ibis_automation.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_75/ibis_automation.html); the conversion script is at [github.com/bulug001/IbIs-Data](https://github.com/bulug001/IbIs-Data) (script only, no data).
3. UMN CDMS wiki, "Complex impedance" procedure (2016), section "Calibration factors to calculate dIbias and dItes": [https://villano-lab.github.io/R76Analysis/cdms/k100/procedure/complex_impedance.html](https://villano-lab.github.io/R76Analysis/cdms/k100/procedure/complex_impedance.html).
4. UMN CDMS wiki, run diary of 3 November 2016, the "SC dIdV" and "Transition dIdV" data sets: [https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20161103.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20161103.html).
5. UMN CDMS wiki, group meeting of 4 December 2025: [https://villano-lab.github.io/R76Analysis/cdms/k100/group_meetings/20251204.html](https://villano-lab.github.io/R76Analysis/cdms/k100/group_meetings/20251204.html).
6. UMN CDMS wiki, "Phonon Collection Efficiency for S104" (Run 76 summary), the "Absolute Calibration" code block (written for the first Run 76 series of March to April 2022): [https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76/phonon_collection_efficiency.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76/phonon_collection_efficiency.html).
7. UMN CDMS wiki, run diary of 3 December 2022: [https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20221203.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20221203.html).
8. UMN CDMS wiki, run diaries of 6 September to 22 October 2022 (setup line "NaI trigger signal → DCRCX(4)" and the series "trigger on DCRC4pA"), for example [https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20221022.html](https://villano-lab.github.io/R76Analysis/cdms/k100/run_diary/20221022.html).

A longer working summary of what the wiki says about the QET channels (per-channel $T_\mathrm{c}$, $R_\mathrm{n}$, $R_\mathrm{par}$ and bias settings) is in `data_analysis/R76/notebooks/pulse-normalization/umn-wiki-qet-channel-notes.md`.
