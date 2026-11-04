# How the pieces fit

## The pieces

| Piece | What it is | Where |
|---|---|---|
| `Events` | An immutable container of one detector's events: the traces of each channel and segment (read-only arrays), and one record per event of the quantities, keyed by `series`, `dump` and `event`. | {py:mod}`goldpan.data` |
| Readout | How the data were sampled: `pretrigger_samples`, `glitch_samples`, `sample_period_s`. A `PulseConfig`, with presets such as `DCRC_RUN76` and `Z7`. **No defaults.** | {py:mod}`goldpan.config` |
| Adapter | The only code that knows a file format: it turns idx dumps, MIDAS files, Parquet or ROOT RQ files into `Events` (or a table of quantities) and, where possible, writes them. | {py:mod}`goldpan.adapters` |
| Registry | The facts about the detectors (number, type, readout, which channel is wired where in a file format), kept **outside** the package in folders of TOML files that a dataset definition names with `registry = [...]`; the library holds only the mechanism, so the folder can later become a repository or a database. | {py:mod}`goldpan.registry` |
| Dataset definition | One TOML file naming the raw files, how to read them and the processing to run. Read by both packages. | {py:mod}`goldpan.dataset` |
| Kernel | A fast per-trace algorithm in Rust, with a Python **mirror** that defines it readably. | {py:mod}`goldsluice` |
| Batch mode | `python -m goldsluice run`: reads each raw file in chunks, runs the kernels and writes the quantities into a Parquet dataset that goldpan reads back. | {py:mod}`goldsluice.batch` |

## The flow

```text
raw files --adapter--> Events (pulses) --kernels (Rust)--> quantities --Parquet dataset--> goldpan.dataset.Dataset
                                                                                              |-- .processed(): quantities only
                                                                                              |-- .read(): pulses + quantities
```

goldpan never imports goldsluice. goldsluice's batch mode imports goldpan, which does the reading and the definition file.

## Principles

- **The readout is never assumed.** A wrong silent default (the library once assumed 1.6 µs for data sampled every 0.8 µs) changes every time and frequency without an error, so a readout and every algorithm parameter must be given. In a dataset definition, `"@readout.glitch_samples"` takes a value from the readout so that the file cannot disagree with itself.
- **A quantity has one definition.** Every goldsluice algorithm has a Rust kernel and a Python mirror; a test requires that they agree on the standard inputs and refuse bad parameters with the same message, and that they agree with the goldpan function of the same quantity (or say why there is none).
- **Provenance travels with the data.** A processed file carries the steps, parameters, versions and timing that produced it.
- **Event numbers restart in every dump**, so an event is identified by `series`, `dump` and `event`, never by the number alone.

## Status of functions

A function in goldpan carries a development status. Functions that are still under development run, but warn on every call, and their entry in the reference says so.
