# Registry of detectors

The facts about the detectors that the analysis needs and the library must not contain: a detector's number, type, readout and
where each named channel is wired in a given file format. Read by `goldpan.registry` (specification in its docstring).

- One or more `*.toml` files. Every entry has a `status` (`confirmed` or `inferred`) and `evidence` that says where it comes from.
- A dataset definition names this folder with `[dataset] registry = ["../registry"]` (relative to the definition file), or the
  environment variable `GOLDPAN_REGISTRY` lists folders. Anything the definition file writes itself wins over the registry.
- This folder is **data, not library code**, and nothing in `python/` or `goldsluice/` depends on it. It is laid out so that it
  can move to a repository of its own (or be replaced by a database behind the same `goldpan.registry` interface) without a change
  to the library.
- A name may be defined once. To add a detector, add a table to a file here (or a new file) and run
  `python -m pytest python/tests/test_registry_data.py`.

For a MIDAS file, `goldpan.adapters.midas.detectors(path)` returns what the file's ODB says about each detector and
`goldpan.adapters.midas.registry_entry(detector)` writes a starting entry from it; `goldpan.registry.compare` checks a record
against what a file says.

Issue 150 has the design.
