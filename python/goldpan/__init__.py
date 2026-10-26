"""goldpan: analysis of digitized pulses together with their scalar quantities.

The modules (import what you need; none is imported automatically, so that optional dependencies such as h5py are only
needed by the modules that use them):

* `goldpan.config`     the readout of your data (`PulseConfig`, with the presets `DCRC_RUN76` and `Z7`); it has no defaults
* `goldpan.data`       the immutable container of one detector's events (`Events`, `Detector`, `Readout`; needs `awkward`)
* `goldpan.quantities` per-pulse numbers (baseline, excursion, spectrum, ...)
* `goldpan.cuts`       selections built from the quantities
* `goldpan.operations` pulse in, pulse out (baseline subtraction, glitch trimming)
* `goldpan.io`         loading traces of a dump into arrays
* `goldpan.archive`    writing and reading HDF5 archives of selected pulses
* `goldpan.channels`   which physical channel is a dump's (detector, channel); the map of the Run 76 readout
* `goldpan.status`     the `@status` tag of every public function

The flat names of the first versions (`pulse_quantities`, `pulse_cuts`, ...) still work: they are aliases of these
modules with the Run 76 readout as the default `config`, kept for the existing notebooks (`goldpan.legacy`).
"""
