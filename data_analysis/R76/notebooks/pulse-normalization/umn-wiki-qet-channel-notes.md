# UMN wiki: QET channel settings and characteristics for series 07221203_2025

Notes collected on 21 October 2026 while working on the pulse-normalization question (how to normalize our pulses to TES current). The source is the static archive of the UMN CDMS wiki, mirrored March 2026, at <https://villano-lab.github.io/R76Analysis/index.html>. Page addresses below are relative to `https://villano-lab.github.io/R76Analysis/cdms/k100/`.

This is a working summary, not a result: the numbers are copied from the wiki and not checked against the raw IbIs data (the attachments, including data files, are not in the archive).

## Which run, which date

- Series `07221203_2025` is **3 December 2022**. The name is `07` + YYMMDD + `_hhmm` (the dump's own `global_timestamp`, 1670120747, is 2022-12-04 02:25:47 UTC, which is 20:25 in Minnesota).
- The run diary for that day, `run_diary/20221203.html`, records it as the series started at 20:25: "Start -83.2 V PuBe data series", HV supply -94.7 V, leakage 28.8 uA (detector at 88% of the supply), triggered on DCRC1pA with threshold 2, 1000 initial randoms and 5 Hz in-run randoms.
- The diary for Dec 2 to 4 describes a detector that was still cooling after the twenty-ninth 5K pumpout, with unusual MC temperature and pressure variations. Phonon baselines were re-adjusted to about -0.800 V in the morning, and the DCRC1pA baseline went from -0.790 V at the start of our series to -0.730 V by 23:05. On Dec 4 the phonon channels were lost (about 43 hours after circulation started, "pretty typical").

## Channel map used in the notes

| Board channel | Detector channel | | Board channel | Detector channel |
|---|---|---|---|---|
| DCRC1pA | Side2pC | | DCRC3pA | Side1pE |
| DCRC1pB | Side2pF | | DCRC3pB | Side1pB |
| DCRC1pC | Side1pC (dead) | | DCRC3pC | Side1pD (dead) |
| DCRC1pD | Side1pF | | DCRC3pD | Side2pE |
| DCRC4pA | Side2pB | | DCRC4pB, pC, pD | Side2pA, Side1pA, Side2pD (dead) |

## Per-channel characteristics

Tc, Rn, Rpar and Rop/Rn are from the "TES properties" table of the Run 75 summary (`run_summary/run_75.html`), measured Feb to Apr 2022: Rn from IbIs taken around 42 mK (about 5% higher in earlier IbIs at 50 to 56 mK), assuming Rshunt = 8.0 mOhm; Rpar from fitting the lowest part of the transition curve (the wiki is "not sure about the accuracy"); Rop/Rn is the operating resistance as a fraction of the normal resistance at the standard operating point.

The QET biases are the setting at which dP/dI = 1.0 uV, from 25 and 26 Aug 2022 (`run_diary/20220825.html`, `20220826.html`), as stored in the ODB of series 07220916_2200 (16 Sept 2022; `odb-facts-07220916_2200.json` in `data_analysis/R76/student/buddy/`), which matches the August values. The Jan 2022 values are not in this table because of the board mapping (see below).

| Channel (board) | Tc (mK) | Rn (mOhm) | Rpar (mOhm) | Rop/Rn | QET bias, Aug and Sept 2022 (uA) | SQUID bias, Sept 2022 ODB (uA) |
|---|---|---|---|---|---|---|
| Side2pC (DCRC1pA) | 70.0 | 60.8 | 11.0 | 0.79 | 183.0 | -80 |
| Side2pF (DCRC1pB) | 69.0 | 58.7 | 9.2 | 0.83 | 182.1 | -75 |
| Side1pF (DCRC1pD) | - | - | - | - | 229.0 | -101 |
| Side1pE (DCRC3pA) | 76.0 | 89.1 | 10.7 | 0.52 | 196.2 | -70 |
| Side1pB (DCRC3pB) | 86.0 | 95.0 | 15.2 | 0.58 | 194.0 | -75 |
| Side2pE (DCRC3pD) | 69.0 | 69.9 | 15.1 | 0.79 | 209.0 | -75 |
| Side2pB (DCRC4pA) | 77.5 | 65.6 | 7.6 | 0.60 | 0 | 0 (polarity 0) |

**Why there is no Jan 2022 column.** On 14 Jan 2022 the diary lists the bias for dP/dI = 1 uV per board channel (at about 41.5 mK): DCRC1pA 238.3, pB 283.2, pC 275, pD 198.2; DCRC3pA 178.2, pB 174.4, pC 219.2, pD none; DCRC4pA 224, pB 161.9, pC 263.2, pD 196.8 uA. These cannot be assigned to detector channels with the Run 76 map: the board-to-channel map changed over the winter (the Run 75 page has DCRC1 on Face5 = Side1pE, B, D and Side2pE, DCRC3 on Face3 = Side2pC, F and Side1pC, F; diary entries of 8 and 10 Feb 2022 give yet other assignments; the Run 76 map with DCRC1 on Face3 first appears in the diary of 30 Mar 2022). The Run 75 TES properties above are keyed by detector channel, so they do not depend on the board map. The averages in the Run 75 table are Tc 75.2 mK, Rn 79.3 mOhm, Rpar 11.0 mOhm, Rop/Rn 0.63.

## IbIs curves that exist

- **Plots only, no data.** The Run 75 summary (`run_summary/run_75.html`, section "IbIs measurements") has plots of all the measured channels (Side1pA to pE and Side2pA to pF; Side1pF is not in them), taken around 42 mK in Feb to Apr 2022: Is versus Ib (`run075_ibis.png`), TES resistance versus Ib (`run075_res_tes.png`, which plateaus at each channel's Rn), TES power versus Ib (`run075_pow_tes.png`) and TES resistance against dP/dI (`run075_res_vs_dpdi.png`), at `https://villano-lab.github.io/R76Analysis/media/cdms/k100/run_summary/`. `ibis_automation.html` shows the same four kinds of plot for one example channel.
- No IbIs curves of the December 2022 data, and none of Run 76 itself.
- The raw scans were written as `QB_scan` files on the lab computer (`/data/chocula/k100/midasraw/qbscan`), not in the wiki. The code that turns a scan into the curves is public, `https://github.com/bulug001/IbIs-Data` (`IbIs Data Calculations.py`, July 2022; the script only, no data).

## Calibration constants

- Rshunt = 8.0 mOhm (Run 75 table). The analysis code in the R76Analysis repository (`example_scripts/r76_analysis_hvcal.c` and `fritts/run076/r76_analysis_side2.c`) has `res_ratio = {1.848, 1.953, 2.371, 2.522, 2.890, 2.149}`, "derived from IbIs ... 1+Rpar/Rshunt ... From R75 IbIs". These are the Side 2 channels A to F in order (1 + Rpar/8.0 mOhm with the Rpar column above gives 1.85, 1.95, 2.38, 2.53, 2.89, 2.15).
- The operating point is set by dP/dI = 1.0 uV, "pretty different from fixing a certain fraction of Rn"; the resistance fraction is "pretty high for some of the Side2 channels" (about 0.8 for Side2pC, Side2pE, Side2pF).
- The Run 76 phonon collection efficiency page (`run_summary/run_76_phonon_collection_efficiency.html`) converts a raw integral to V*s, then to A*s with the feedback-circuit gains, then to W*s with dP/dI from IbIs, choosing one uniform dP/dI for all channels.

## Behaviour of the operating point

- IbIs is very sensitive to the temperature of the detector and to the helium film on it. Between 12 and 15 Aug 2022 the QET bias for dP/dI = 1 uV changed by 10 to 60 uA per channel (`run_diary/20220812.html` to `20220815.html`), and channels were sometimes stuck in the superconducting or normal state (`20220825.html`, `20220828.html`, `20220901.html`; also the Run 76 summary).
- A biased channel heats its neighbours, so IbIs scans are done one channel at a time with the others biased in their transitions (`run_summary/run_75/ibis_automation.html`).
- No IbIs entry exists after 1 Sept 2022. The December series used the biases set earlier ("previous QET biases"), with the phonon offsets re-adjusted after each cooldown.

## Side2pB (DCRC4pA) is probably the NaI trigger channel

- In the Sept to Oct 2022 diaries every page's setup line reads "NaI trigger signal -> DCRCX(4)", and the NaI-triggered series are "trigger on DCRC4pA threshold 20".
- On 2022-10-22: "I'm enabling DCRC4 for consistency in processing and data rate" (`run_diary/20221022.html`). The diary for 2 Dec 2022 says "Plug in DCRCs 1&3" and the IbIs checks from Aug 2022 on list only DCRC1 and DCRC3 channels.
- In the Sept 2022 ODB all DCRC4 QET biases are 0, and DCRC4pA has SQUID bias 0 and polarity 0.
- So in series 07221203_2025 the channel we call Side2pB (flat, no pulses, noise below the others) is probably not a TES. Not yet confirmed: the ODB of the December series, and whether its trace shows the NaI signal in coincidence events.

## Counts to TES-branch current: the wiki already gives the conversion

**What the number is, physically.** The ADC records the voltage of the SQUID feedback electronics. The SQUID is run in a flux-locked loop: the feedback current Ifb through the feedback resistor Rfb into the feedback coil produces a flux that cancels the flux of the TES-branch current Is in the input coil, so Mi x Is = Mf x Ifb and the SQUID is only a null detector. The magnetic coupling of the TES branch to the SQUID therefore drops out; only the ratio of the input-coil and feedback-coil couplings of the SQUID matters. Counts to volts to Ifb (= V / (Rfb x amplifier gains)) is electronics. Ifb to Is is the coil ratio. The wiki divides by a "loop gain" of 10.5, so Ifb = 10.5 x Is, which I read as Mi/Mf; the wiki does not define it (the page `procedure/complex_impedance`, 2016, only lists "Loop gain 10.5" among the gain factors), and I found no derivation or independent measurement of it.

The Run 76 phonon-collection-efficiency page (`run_summary/run_76/phonon_collection_efficiency.html`, the "Absolute Calibration" code block, written for the first Run 76 series of March to April 2022) converts the data like this:

- ADC counts to volts: `adcPERvolt = 6553.6` counts per volt (= 65536 / 10, which looks like a 16-bit ADC over 10 V; my reading).
- Volts to current in the TES branch (the current through the SQUID input coil, Is): `rgain_ohm = rfb_ohms * gloop * gdcrc * gdriver`, with `rfb_ohms = 1233` (feedback resistor), `gloop = 10.5`, `gdcrc = 2` (the DCRC `VGAGain`) and `gdriver = 1` (the `PGAGain`). Is = V / rgain_ohm.
- With those numbers rgain = 1233 x 10.5 x 2 x 1 = 25,893 ohm, i.e. 6553.6 x 25,893 = 1.70e8 counts per amp, **about 170 counts per uA of TES-branch current**.
- The 2016 page `procedure/complex_impedance` gives the same formula with the gains named differently: dItes = dVtes / (Rfeedback x Gloop x Gdcrc-fixed x Gdcrc-variable), Rfeedback 1233 ohm, Loop gain 10.5, DCRC fixed gain 2 (RevC.1) or 5 (RevC), DCRC variable gain 1, 2, 4, 8 (RevC.1) or 1 to 7 (RevC). The same page describes a calibration that injects a known current: the DCRC test-signal generator (a triangle wave, 100 to 500 Hz) across a bias resistor (10 kohm on DCRC50 and DCRC55, 1 kohm on DCRC33), dIbias = dVbias / Rbias; this is the nearest thing on the wiki to a measurement of the whole chain.
- The wiki then uses P = dP/dI x I with dP/dI = 1.0 uV (the standard operating point, see above) and the sample period `secPERsample = 8e-7` s. Our notebooks use 1.6e-6 s (625 kHz) for this dump; the two should be reconciled before using any time integral.

**Per-channel gains in the ODB of series 07220916_2200 (16 Sept 2022)**, from `odb-facts-07220916_2200.json` and the ODB dump in the scratch notes (`Equipment/Tower01/Settings/DCRCn/Phonon`; `PGAGain` is 1 on every channel):

| Board | VGAGain (channels pA, pB, pC, pD) | ADCOffset (V) | LockpointAdjust (mV) |
|---|---|---|---|
| DCRC1 | 2, 2, 2, 2 | -0.03, 0.4, 1, -0.14 | -3.5, -4.5, 0, -2.5 |
| DCRC3 | **5**, 2, 2, **5** | 0.34, 0.41, 1, 1.37 | -4.7, -3.4, 0, -5.7 |
| DCRC4 | 2, 3, 1, 3 | 0, 1, 0, 0 | 0, -3.8, -4, -2.5 |

**Not settled: how these ODB fields map onto the wiki's gains.** The wiki's other pages use "front-end gain" (10 or 5), "driver gain" (x1 to x7, register 0 to 7) and the calibration code's `gdcrc = 2`, `gdriver = 1`; the ODB has `VGAGain` and `PGAGain`. I could not establish which ODB field is which, so I cannot say whether `VGAGain` 5 on Side1pE and Side2pE (DCRC3pA, pD), against 2 on the others, changes their counts-per-uA (it would be 2.5 times larger if `VGAGain` is the `gdcrc` of the calibration code). The settings of the December series also have to be checked in its own ODB.

**Consistency check with the IbIs curves.** In the normal state, Is = Ib x Rsh / (Rsh + Rpar + Rn). For Side2pC (Rsh 8.0, Rpar 11.0, Rn 60.8 mOhm) at Ib = 350 uA this is 35 uA, and the Run 75 Is-versus-Ib plot shows about 33 to 35 uA there. The Rn and Rpar of the wiki were themselves derived from these curves with the same gain assumptions, so this checks the pieces against each other and is not an independent measurement of the gain: the normal branch slope alone gives only G x Rsh / (Rsh + Rpar + Rn). The ratio of the normal-branch and superconducting-branch slopes gives Rn / (Rsh + Rpar) without the gain, and the gain then needs Rsh (assumed 8.0 mOhm; shunts were modified in earlier runs, see `run_summary/run_66_ibis_analysis.html`).

## Not on the wiki

- No IbIs for December 2022, and no stored IbIs data files.
- No feedback resistor, SQUID coil ratio, or TES bias power for Run 76.

## Pages read

`run_summary/run_75.html`, `run_summary/run_76.html`, `run_summary/run_75/ibis_automation.html`, `run_summary/run_76_phonon_collection_efficiency.html`, `run_summary/run_66_ibis_analysis.html` (older run, same style of table), `run_diary/20220102.html`, `20220114.html`, `20220121.html`, `20220125.html`, `20220812.html` to `20220828.html`, `20220901.html`, `20221022.html`, `20221202.html` to `20221204.html`, the ODB of series 07220916_2200 (our own `extract_odb_facts.py`), and the R76Analysis repository.
