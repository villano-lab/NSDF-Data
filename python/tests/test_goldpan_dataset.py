"""goldpan.dataset: the dataset definition file, and reading pulses with their processed quantities."""
import awkward as ak
import numpy as np
import pytest

from goldpan import dataset
from goldpan.adapters import parquet
from goldpan.config import DCRC_RUN76, PulseConfig, Z7
from goldpan.data import ChannelInfo, Detector, Events, Readout
from goldpan.dataset import Dataset, Source, Step

N_SAMPLES = 1100


def toy_events(n=4, series="S1", dump="F0001", seed=0):
    det = Detector("TOY", (ChannelInfo("A", role="phonon"), ChannelInfo("B", role="phonon"), ChannelInfo("Q", role="charge")),
                   Readout.single(N_SAMPLES, DCRC_RUN76))
    rng = np.random.default_rng(seed)
    return Events.from_arrays(det, {c: rng.normal(100, 3, size=(n, N_SAMPLES)) for c in "ABQ"}, series=series, dump=dump)


def spec_text(raw, extra_source="", steps=None, top='name = "toy"\noutput = "out"'):
    steps = steps if steps is not None else ('[[processing]]\nalgorithm = "peak"\nchannels = "role:phonon"\n'
                                              '[processing.params]\nglitch_samples = "@readout.glitch_samples"\n'
                                              'amps_per_adc = 2.5\n')
    return (f"[dataset]\n{top}\n\n[[sources]]\nname = \"raw\"\nformat = \"parquet\"\npaths = [{str(raw)!r}]\n"
            f"detector = \"TOY\"\n{extra_source}\n{steps}")


@pytest.fixture(autouse=True)
def no_output_root(monkeypatch):
    monkeypatch.delenv(dataset.ENV_OUTPUT, raising=False)          # a developer's own GOLDSLUICE_OUTPUT must not change these tests


@pytest.fixture
def raw(tmp_path):
    parquet.write(toy_events(), tmp_path / "raw")
    return tmp_path / "raw" / "TOY" / "S1_F0001.parquet"


def write(tmp_path, text, name="toy.dataset.toml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_reads_sources_steps_and_a_relative_output(tmp_path, raw):
    spec = dataset.load(write(tmp_path, spec_text(raw)))
    assert spec.name == "toy" and spec.output == tmp_path.resolve() / "out"
    assert [s.name for s in spec.sources] == ["raw"] and spec.sources[0].detector == "TOY"
    assert spec.steps == (Step("peak", "role:phonon", {"glitch_samples": "@readout.glitch_samples", "amps_per_adc": 2.5}),)
    assert spec.source() is spec.sources[0] and spec.source("raw") is spec.sources[0]
    with pytest.raises(KeyError, match="no source 'x'"):
        spec.source("x")


def test_a_relative_output_goes_under_goldsluice_output_when_it_is_set_and_a_full_path_never_does(tmp_path, raw, monkeypatch):
    root = tmp_path / "root"
    monkeypatch.setenv(dataset.ENV_OUTPUT, str(root))
    assert dataset.load(write(tmp_path, spec_text(raw))).output == root / "out"                       # relative: under the root
    full = tmp_path / "elsewhere"
    top = f'name = "toy"' + chr(10) + f'output = {str(full)!r}'
    assert dataset.load(write(tmp_path, spec_text(raw, top=top), "b.toml")).output == full             # full path: as written
    monkeypatch.setenv(dataset.ENV_OUTPUT, "   ")
    assert dataset.load(write(tmp_path, spec_text(raw))).output == tmp_path.resolve() / "out"          # blank = not set
    monkeypatch.delenv(dataset.ENV_OUTPUT)
    assert dataset.load(write(tmp_path, spec_text(raw))).output == tmp_path.resolve() / "out"          # not set: next to the file


def test_the_output_root_is_not_part_of_the_fingerprint(tmp_path, raw, monkeypatch):
    a = dataset.load(write(tmp_path, spec_text(raw)))
    monkeypatch.setenv(dataset.ENV_OUTPUT, str(tmp_path / "root"))
    b = dataset.load(write(tmp_path, spec_text(raw)))
    assert a.output != b.output and dataset.fingerprint(a, a.sources[0]) == dataset.fingerprint(b, b.sources[0])


def test_the_readout_is_a_preset_or_all_three_numbers_never_a_default(tmp_path, raw):
    assert dataset.load(write(tmp_path, spec_text(raw, 'readout = "Z7"'))).sources[0].readout == Z7
    inline = 'readout = { pretrigger_samples = 10, glitch_samples = 1, sample_period_s = 1e-6 }'
    assert dataset.load(write(tmp_path, spec_text(raw, inline))).sources[0].readout == PulseConfig(10, 1, 1e-6)
    with pytest.raises(ValueError, match=r"needs \['glitch_samples', 'sample_period_s'\]"):
        dataset.load(write(tmp_path, spec_text(raw, 'readout = { pretrigger_samples = 10 }')))
    with pytest.raises(ValueError, match="not a preset"):
        dataset.load(write(tmp_path, spec_text(raw, 'readout = "NOSUCH"')))


@pytest.mark.parametrize("edit, message", [
    ('format = "parquet"\n', "needs 'format'"),
    ('detector = "TOY"\n', "needs 'detector'"),
    ('[dataset]\nname = "toy"\noutput = "out"\n', "needs a \\[dataset\\] table"),
    ('output = "out"', "needs 'output'"),
    ('algorithm = "peak"\n', "needs 'algorithm'"),
    ('channels = "role:phonon"\n', "needs 'channels'"),
])
def test_missing_pieces_are_named(tmp_path, raw, edit, message):
    text = spec_text(raw)
    with pytest.raises(ValueError, match=message):
        dataset.load(write(tmp_path, text.replace(edit, "", 1)))


def test_channels_must_be_all_a_role_or_a_list(tmp_path, raw):
    bad = spec_text(raw).replace('channels = "role:phonon"', 'channels = "phonons"')
    with pytest.raises(ValueError, match="channels must be"):
        dataset.load(write(tmp_path, bad))


def test_unknown_keys_are_refused_so_a_typo_is_not_silent(tmp_path, raw):
    with pytest.raises(ValueError, match=r"unknown key\(s\) \['readuot'\]"):
        dataset.load(write(tmp_path, spec_text(raw, 'readuot = "Z7"')))
    with pytest.raises(ValueError, match=r"unknown key\(s\) \['procesing'\]"):
        dataset.load(write(tmp_path, spec_text(raw) + "\n[[procesing]]\nalgorithm = 'x'\n"))


def test_bad_toml_and_a_newer_format_version(tmp_path, raw):
    with pytest.raises(ValueError, match="not valid TOML"):
        dataset.load(write(tmp_path, "[dataset\n"))
    with pytest.raises(ValueError, match="newer than this goldpan"):
        dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\nformat_version = 99')))


def test_source_files_expand_globs_in_order_and_refuse_patterns_that_match_nothing(tmp_path):
    for n in ("b", "a"):
        (tmp_path / f"{n}.dump").write_text("x")
    src = Source("s", "idx", ("*.dump",), "D", None, {}, tmp_path)
    assert [f.name for f in src.files()] == ["a.dump", "b.dump"]
    with pytest.raises(ValueError, match="matches nothing"):
        Source("s", "idx", ("*.none",), "D", None, {}, tmp_path).files()
    with pytest.raises(ValueError, match="matches nothing"):
        Source("s", "idx", ("absent.dump",), "D", None, {}, tmp_path).files()


def test_step_channels_by_role_name_or_all(tmp_path):
    det = toy_events().detector
    assert Step("peak", "all", {}).channel_names(det) == ["A", "B", "Q"]
    assert Step("peak", "role:phonon", {}).channel_names(det) == ["A", "B"]
    assert Step("peak", ("B",), {}).channel_names(det) == ["B"]
    with pytest.raises(ValueError, match="no channel with role 'nope'"):
        Step("peak", "role:nope", {}).channel_names(det)
    with pytest.raises(KeyError):
        Step("peak", ("Z",), {}).channel_names(det)


def test_readout_references_resolve_from_the_data_and_unknown_ones_are_refused():
    step = Step("peak", "all", {"g": "@readout.glitch_samples", "p": "@readout.pretrigger_samples", "n": 5, "s": "text"})
    assert step.resolve(DCRC_RUN76) == {"g": 10, "p": 500, "n": 5, "s": "text"}
    with pytest.raises(ValueError, match="the readout has"):
        Step("peak", "all", {"g": "@readout.gain"}).resolve(DCRC_RUN76)
    with pytest.raises(ValueError, match="does not give sample_period_s"):
        Step("peak", "all", {"t": "@readout.sample_period_s"}).resolve(PulseConfig(10, 1, None))


def test_the_fingerprint_changes_with_the_processing_and_the_reading_but_not_with_the_name(tmp_path, raw):
    base = dataset.load(write(tmp_path, spec_text(raw)))
    same = dataset.load(write(tmp_path, spec_text(raw, top='name = "renamed"\noutput = "elsewhere"'), "b.toml"))
    other = dataset.load(write(tmp_path, spec_text(raw).replace("2.5", "3.5"), "c.toml"))
    read = dataset.load(write(tmp_path, spec_text(raw, "[sources.read]\nchannels = ['A']"), "d.toml"))
    fp = lambda s: dataset.fingerprint(s, s.sources[0])
    assert fp(base) == fp(same) != fp(other)
    assert fp(read) != fp(base)


def test_read_raw_reads_one_file_whole_or_in_chunks(tmp_path, raw):
    src = dataset.load(write(tmp_path, spec_text(raw))).sources[0]
    whole = list(dataset.read_raw(src, raw))
    assert len(whole) == 1 and whole[0].n_events == 4
    pieces = list(dataset.read_raw(src, raw, chunk=3))
    assert [p.n_events for p in pieces] == [3, 1]


def test_an_adapter_that_needs_a_readout_says_so_and_unknown_read_arguments_are_refused(tmp_path):
    from goldpan.adapters import midas
    src = Source("m", "midas", ("x.mid",), "D", None, {"channels": {"A": 0}}, tmp_path)
    with pytest.raises(ValueError, match="needs a readout"):
        list(dataset.read_raw(src, tmp_path / "x.mid"))
    src = Source("m", "midas", ("x.mid",), "D", DCRC_RUN76, {"colour": 1}, tmp_path)
    with pytest.raises(ValueError, match=r"has no argument \['colour'\]"):
        list(dataset.read_raw(src, tmp_path / "x.mid"))
    assert midas.read                                                              # the adapter exists; only its arguments were wrong


def processed_events(n=4):
    """What goldsluice writes: the key and one record per channel, no pulses."""
    ev = toy_events(n)
    q = ak.Array({"series": ev.quantities["series"], "dump": ev.quantities["dump"], "event": ev.quantities["event"],
                  "A": ak.zip({"adc_max": ev.trace("A").max(axis=1)}, depth_limit=1)})
    return Events(ev.detector, {}, q, {})


def test_read_attaches_the_processed_quantities_to_the_pulses_and_processed_alone_has_no_pulses(tmp_path, raw):
    spec = write(tmp_path, spec_text(raw))
    ds = Dataset.open(spec)
    with pytest.raises(FileNotFoundError, match="python -m goldsluice run"):
        ds.processed()
    parquet.write(processed_events(), tmp_path / "out")
    q = ds.processed()
    assert not q.traces and q.n_events == 4
    ev = ds.read()
    assert sorted(ev.traces) == [("A", "main"), ("B", "main"), ("Q", "main")]
    np.testing.assert_array_equal(ak.to_numpy(ev.quantities["A"]["adc_max"]), ev.trace("A").max(axis=1))
    assert "A" not in ak.fields(ds.read(processed=False).quantities)
    assert "Dataset(" in repr(ds)


def test_read_names_the_file_the_batch_run_has_not_covered(tmp_path, raw):
    spec = write(tmp_path, spec_text(raw))
    parquet.write(processed_events(2), tmp_path / "out")                         # only 2 of the 4 events were processed
    with pytest.raises(ValueError, match="has the batch run covered this file"):
        Dataset.open(spec).read()


def test_the_output_is_parquet_unless_the_file_says_root_and_names_the_detector(tmp_path, raw):
    plain = dataset.load(write(tmp_path, spec_text(raw)))
    assert (plain.output_format, plain.root_detector) == ("parquet", None)
    root = dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\noutput_format = "root"\nroot_detector = 7'), "r.toml"))
    assert (root.output_format, root.root_detector) == ("root", 7)
    for top, message in [('output_format = "root"', "needs root_detector"),
                         ('output_format = "root"\nroot_detector = "7"', "needs root_detector"),
                         ('output_format = "root"\nroot_detector = true', "needs root_detector"),
                         ('output_format = "root"\nroot_detector = -1', "needs root_detector"),
                         ('root_detector = 7', "only applies"),
                         ('output_format = "hdf5"', "must be one of")]:
        with pytest.raises(ValueError, match=message):
            dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\n' + top), "x.toml"))


def test_the_root_output_changes_the_fingerprint_but_a_parquet_definition_keeps_the_one_it_had(tmp_path, raw):
    fp = lambda s: dataset.fingerprint(s, s.sources[0])
    top = 'name = "t"\noutput = "o"\n'
    plain = dataset.load(write(tmp_path, spec_text(raw)))
    explicit = dataset.load(write(tmp_path, spec_text(raw, top=top + 'output_format = "parquet"'), "e.toml"))
    root7 = dataset.load(write(tmp_path, spec_text(raw, top=top + 'output_format = "root"\nroot_detector = 7'), "r7.toml"))
    root8 = dataset.load(write(tmp_path, spec_text(raw, top=top + 'output_format = "root"\nroot_detector = 8'), "r8.toml"))
    assert fp(plain) == fp(explicit) != fp(root7) != fp(root8)


def test_processed_says_where_root_output_is_read_instead_of_failing_obscurely(tmp_path, raw):
    spec = write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\noutput_format = "root"\nroot_detector = 7'))
    with pytest.raises(ValueError, match="rq_root.read"):
        Dataset.open(spec).processed()
