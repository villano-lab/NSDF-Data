# goldpan and goldsluice

Two packages for pulse data, from SuperCDMS-type detectors and anything else that has pulses plus the quantities computed from them.

**goldpan** is the analysis library: an immutable container of one detector's events (`Events`), adapters that read and write the file formats, the pulse quantities, cuts and filters, and the dataset definition file. It is in `python/` of the [NSDF-Data repository](https://github.com/villano-lab/NSDF-Data).

**goldsluice** is the reduction package: fast kernels in Rust, each with a Python mirror that is its readable definition, and a batch mode that runs a whole dataset. It is in `goldsluice/`.

Nothing about a readout is assumed by either package: the sample period, the baseline window and every algorithm parameter are written down by the user, in a preset, in code or in the dataset definition file.

```{toctree}
:maxdepth: 2
:hidden:

concepts
guides
reference/index
```

## Where to start

| You want to | Read |
|---|---|
| understand how the pieces fit | {doc}`concepts` |
| run goldsluice, define a dataset, write an algorithm, write an adapter | {doc}`guides` |
| look up a function, class or module | {doc}`reference/index` |

This documentation is generated from the code and the pages in `sphinx/`; the project front page, the student guides and the notes are at <https://villano-lab.github.io/NSDF-Data/>.
