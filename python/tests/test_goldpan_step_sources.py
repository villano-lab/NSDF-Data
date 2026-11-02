"""goldpan.dataset: a step may name the sources it applies to (`sources`, definition format 7)."""
import json

import pytest

from goldpan import dataset
from goldpan.dataset import Step

from test_goldpan_dataset import raw, write   # noqa: F401  (the fixture `raw` and the helper)

PEAK = '[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n{extra}[processing.params]\nglitch_samples = "@readout.glitch_samples"\namps_per_adc = 2.5\n'
FILTER = '[[processing]]\nalgorithm = "lowpass"\nname = "lp"\nchannels = "role:phonon"\n{extra}[processing.params]\ncutoff_hz = 1000.0\n'


def text(raw, *blocks):
    sources = "".join(f'[[sources]]\nname = "{n}"\nformat = "parquet"\npaths = [{str(raw)!r}]\ndetector = "TOY"\n\n' for n in ("a", "b"))
    return '[dataset]\nname = "toy"\noutput = "out"\n\n' + sources + "\n".join(blocks)


def load(tmp_path, raw, *blocks):
    return dataset.load(write(tmp_path, text(raw, *blocks)))


def test_a_step_without_sources_runs_on_every_source_and_one_with_sources_only_there(tmp_path, raw):
    spec = load(tmp_path, raw, PEAK.format(extra=""), PEAK.format(extra='sources = ["b"]\n').replace('"peak"', '"baseline"'))
    everywhere, only_b = spec.steps
    assert everywhere.sources is None and only_b.sources == ("b",)
    assert [everywhere.applies_to(n) for n in ("a", "b")] == [True, True] and [only_b.applies_to(n) for n in ("a", "b")] == [False, True]


def test_the_sources_of_a_step_are_checked(tmp_path, raw):
    for value, match in (('["nobody"]', "not sources of this file"), ('[]', "non-empty list"), ('"a"', "non-empty list"), ('["a", "a"]', "twice"), ('[1]', "non-empty list")):
        with pytest.raises(ValueError, match=match):
            load(tmp_path, raw, PEAK.format(extra=f"sources = {value}\n"))


def test_a_step_that_reads_a_filter_must_run_where_the_filter_runs(tmp_path, raw):
    reads = PEAK.format(extra='input = "lp"\n')
    load(tmp_path, raw, FILTER.format(extra=""), reads)                                                       # filter everywhere: fine
    load(tmp_path, raw, FILTER.format(extra='sources = ["a"]\n'), reads.replace('input = "lp"\n', 'input = "lp"\nsources = ["a"]\n'))     # both on a: fine
    with pytest.raises(ValueError, match=r"runs on the sources \['a', 'b'\] but the step 'lp' that it reads runs only on \['a'\]"):
        load(tmp_path, raw, FILTER.format(extra='sources = ["a"]\n'), reads)                                  # the reader would also run on b


def test_the_record_and_the_fingerprint_change_only_for_the_sources_a_step_runs_on(tmp_path, raw):
    one = PEAK.format(extra="")
    other = PEAK.format(extra='sources = ["b"]\n').replace('"peak"', '"baseline"')
    spec = load(tmp_path, raw, one, other)
    assert dataset.step_record(spec.steps[0]) == {"algorithm": "peak", "channels": "role:phonon", "params": spec.steps[0].params}      # nothing new when absent
    assert dataset.step_record(spec.steps[1])["sources"] == ["b"]
    fa, fb = (dataset.fingerprint(spec, s) for s in spec.sources)
    other2 = other.replace("amps_per_adc = 2.5", "amps_per_adc = 9.0")
    changed = load(tmp_path, raw, one, other2)
    ca, cb = (dataset.fingerprint(changed, s) for s in changed.sources)
    assert ca == fa and cb != fb                                    # editing a step of b leaves the output of a as it was
    plain = load(tmp_path, raw, one).steps[0]
    assert dataset.fingerprint(load(tmp_path, raw, one), load(tmp_path, raw, one).sources[0]) == dataset.fingerprint(spec, spec.sources[0])  # same steps for a: same fingerprint
    assert Step("peak", "all", {}).sources is None and plain.applies_to("anything")


def test_dump_writes_and_reads_back_a_step_with_sources(tmp_path, raw):
    spec = load(tmp_path, raw, PEAK.format(extra='sources = ["b"]\n'))
    again = dataset.dump(spec, tmp_path / "again.dataset.toml")
    assert again.steps[0].sources == ("b",) and json.dumps(again.raw, default=str) == json.dumps(spec.raw, default=str)


def test_the_format_version_says_7():
    assert dataset.FORMAT_VERSION == 7
