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

![](img/tes-squid-readout-circuit.png)

**Figure 1: The TES bias and SQUID readout circuit.** The bias current $I_\mathrm{b}$ flows down from the top through two parallel branches to ground: the shunt resistor $R_\mathrm{sh}$, and the TES in series with the parasitic resistance $R_\mathrm{par}$ and the input inductor $L_\mathrm{i}$. $L_\mathrm{i}$ is coupled (mutual inductance $M$) to the SQUID, which is biased with a small current $I_\mathrm{sq}$. The amplifier reads the SQUID voltage, and its output $V_\mathrm{out}$ returns through the feedback resistor $R_\mathrm{fb}$ to the feedback coil $L_\mathrm{f}$ (mutual inductance $M_\mathrm{f}$) to hold the SQUID flux fixed, so $V_\mathrm{out}$ is proportional to the TES current.

## The question

How can we normalize our pulses to QET current? The most basic parameter we read out with our phonon sensors is the current through the Quasi-particle Electro-thermal-feedback Transition Edge Sensors (QETs) that make up our phonon channels. If we want to model our noise environment properly we must know what current the "pulses" are reading; typically pulses are read out in arbitrary voltage units depending on the Analog-to-Digital (ADC) conversion. 

## (Your own headings from here)

After the question there is no fixed list of headings. Name each section for what is in it, and use the ones your story needs: your figures and tables, a check you made, what the results mean and do not show, what could be wrong, what to do next. Student guide 3, "The parts of a note", has examples. Delete this section when you start.

![**Figure 1.** What is plotted, for which data, and what to look for.](img/example.png)
