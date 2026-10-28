"""goldpan.registry: the mechanism (records read from folders of TOML files), and how a dataset definition uses it. The library holds no
detector of any experiment, so every record in these tests is written into a temporary folder."""
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from goldpan import dataset, registry
from goldpan.config import DCRC_RUN76, PulseConfig
from goldpan.registry import DetectorRecord, FolderSource, Registry

from test_goldpan_dataset import raw, spec_text, toy_events, write   # noqa: F401  (the fixture `raw` and the helpers)

TOY = '''format_version = 1

[readouts.TOY_READOUT]
pretrigger_samples = 1000
glitch_samples = 10
sample_period_s = 0.8e-6
status = "inferred"
evidence = "a test"

[detectors.TOY]
number = 7
type_code = 710
tower = 2
plane = 1
odb_name = "G149"
readout = "TOY_READOUT"
status = "confirmed"
evidence = "a test"
series = ["S1"]

[detectors.TOY.parquet]
detector = "TOY"
'''


def folder(tmp_path, text=TOY, name="toy.toml", sub="reg"):
    d = tmp_path / sub
    d.mkdir(exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")
    return d


# ---- the mechanism ---------------------------------------------------------------------------------------------------

def test_load_reads_every_toml_file_of_the_folders_and_checks_it(tmp_path):
    reg = registry.load(folder(tmp_path), use_environment=False)
    t = reg.detector("TOY")
    assert (t.number, t.type_code, t.tower, t.plane, t.odb_name, t.readout, t.status, t.series) == \
        (7, 710, 2, 1, "G149", "TOY_READOUT", "confirmed", ("S1",))
    assert t.read_defaults("parquet") == {"detector": "TOY"} and t.read_defaults("idx") == {}
    assert reg.readout("TOY_READOUT").config == PulseConfig(1000, 10, 0.8e-6)
    assert sorted(reg.detectors()) == ["TOY"] and sorted(reg.readouts()) == ["TOY_READOUT"]
    assert registry.load(use_environment=False).detectors() == {}                # no folders: an empty registry


def test_the_environment_variable_adds_folders(tmp_path, monkeypatch):
    other = folder(tmp_path, TOY.replace("TOY", "OTHER"), sub="other")
    monkeypatch.setenv(registry.ENV_VAR, str(other))
    assert sorted(registry.load().detectors()) == ["OTHER"]
    assert registry.load(use_environment=False).detectors() == {}


def test_a_readout_is_a_registry_record_or_a_preset_of_goldpan_config(tmp_path):
    reg = registry.load(folder(tmp_path), use_environment=False)
    assert reg.readout_config("TOY_READOUT") == PulseConfig(1000, 10, 0.8e-6)
    assert reg.readout_config("DCRC_RUN76") == DCRC_RUN76
    with pytest.raises(KeyError, match="TOY_READOUT.*DCRC_RUN76|DCRC_RUN76.*TOY_READOUT"):
        reg.readout_config("NOPE")
    with pytest.raises(KeyError, match="no detector 'NOPE'.*TOY"):
        reg.detector("NOPE")


@pytest.mark.parametrize("text, message", [
    ("[detectors.X]\nstatus = \"inferred\"\nevidence = \"e\"\nnumbr = 1\n", "unknown key"),
    ("[detectors.X]\nevidence = \"e\"\n", "needs 'status'"),
    ("[detectors.X]\nstatus = \"inferred\"\n", "needs 'evidence'"),
    ("[detectors.X]\nstatus = \"maybe\"\nevidence = \"e\"\n", "status must be one of"),
    ("[detectors.X]\nstatus = \"inferred\"\nevidence = \"  \"\n", "evidence must say"),
    ("[detectors.X]\nstatus = \"inferred\"\nevidence = \"e\"\nnumber = -1\n", "number must be a whole number"),
    ("[detectors.X]\nstatus = \"inferred\"\nevidence = \"e\"\nnumber = true\n", "number must be a whole number"),
    ("[readouts.R]\nstatus = \"inferred\"\nevidence = \"e\"\npretrigger_samples = 1\n", "needs .*glitch_samples"),
    ("format_version = 2\n", "newer than this goldpan"),
    ("[detectorz.X]\n", "unknown key"),
    ("[detectors.X\n", "not valid TOML"),
])
def test_a_bad_record_is_refused_with_a_message(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        registry.load(folder(tmp_path, text), use_environment=False)


def test_a_name_may_be_defined_once_and_a_missing_folder_is_an_error(tmp_path):
    a, b = folder(tmp_path, sub="a"), folder(tmp_path, sub="b")
    with pytest.raises(ValueError, match="already defined in .*toy.toml"):
        registry.load(a, b, use_environment=False)
    folder(tmp_path, TOY.replace("TOY", "TWO"), name="two.toml", sub="a")        # two files of a folder: different names are fine
    assert sorted(registry.load(a, use_environment=False).detectors()) == ["TOY", "TWO"]
    with pytest.raises(ValueError, match="does not exist"):
        registry.load(tmp_path / "missing", use_environment=False)


def test_anything_with_a_load_method_is_a_source(tmp_path):
    class Memory:                                                  # what a Git repository or a database would implement
        def load(self):
            yield "memory", {"format_version": 1, "detectors": {"M": {"status": "inferred", "evidence": "e", "number": 3}}}

    reg = Registry([Memory(), FolderSource(folder(tmp_path))])
    assert sorted(reg.detectors()) == ["M", "TOY"] and reg.detector("M").origin == "memory"


def test_compare_lists_what_the_record_states_and_the_file_contradicts(tmp_path):
    rec = registry.load(folder(tmp_path), use_environment=False).detector("TOY")
    same = SimpleNamespace(number=7, type_code=710, tower=2, plane=1, name="G149")
    assert registry.compare(rec, same) == []
    other = SimpleNamespace(number=8, type_code=710, tower=3, plane=None, name="G150")
    msgs = registry.compare(rec, other)
    assert len(msgs) == 3 and any("number 7" in m and "has 8" in m for m in msgs) and any("odb_name 'G149'" in m for m in msgs)
    bare = DetectorRecord("B", None, None, None, None, None, None, "inferred", "e")           # states nothing: nothing to contradict
    assert registry.compare(bare, other) == []


# ---- a dataset definition uses it ------------------------------------------------------------------------------------

def test_a_detector_in_the_registry_supplies_the_readout_and_the_read_defaults(tmp_path, raw):
    reg = folder(tmp_path)
    text = spec_text(raw, top=f'name = "t"\noutput = "o"\nregistry = [{str(reg)!r}]')
    spec = dataset.load(write(tmp_path, text))
    src = spec.sources[0]
    assert src.readout == PulseConfig(1000, 10, 0.8e-6) and src.detector_record.number == 7
    assert dict(src.read) == {"detector": "TOY"} and spec.registry.has_detector("TOY")


def test_what_the_file_writes_wins_over_the_registry_key_by_key(tmp_path, raw):
    reg = folder(tmp_path, TOY.replace('detector = "TOY"', 'detector = "TOY"\nchunk = 5'))
    text = spec_text(raw, extra_source='readout = "DCRC_RUN76"\n[sources.read]\nchunk = 9', top=f'name = "t"\noutput = "o"\nregistry = "{reg.as_posix()}"')
    # the file's own readout is the preset DCRC_RUN76, which equals the registry's: no warning; its read table overrides one key only
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        src = dataset.load(write(tmp_path, text)).sources[0]
    assert dict(src.read) == {"detector": "TOY", "chunk": 9}


def test_a_readout_that_disagrees_with_the_registry_is_a_warning_and_the_files_one_is_used(tmp_path, raw):
    reg = folder(tmp_path)
    text = spec_text(raw, extra_source='readout = { pretrigger_samples = 2000, glitch_samples = 10, sample_period_s = 1e-6 }',
                     top=f'name = "t"\noutput = "o"\nregistry = [{str(reg)!r}]')
    with pytest.warns(UserWarning, match="not the one the registry gives"):
        src = dataset.load(write(tmp_path, text)).sources[0]
    assert src.readout == PulseConfig(2000, 10, 1e-6)


def test_the_registry_changes_the_fingerprint_only_when_what_it_supplies_changes(tmp_path, raw):
    fp = lambda s: dataset.fingerprint(s, s.sources[0])
    explicit = dataset.load(write(tmp_path, spec_text(raw, extra_source='readout = "DCRC_RUN76"\n[sources.read]\ndetector = "TOY"'), "e.toml"))
    reg = folder(tmp_path)
    via = dataset.load(write(tmp_path, spec_text(raw, top=f'name = "toy"\noutput = "out"\nregistry = [{str(reg)!r}]'), "v.toml"))
    assert fp(via) == fp(explicit)                                     # the same readout and the same read: the same results
    changed = folder(tmp_path, TOY.replace("pretrigger_samples = 1000", "pretrigger_samples = 900"), sub="reg2")
    other = dataset.load(write(tmp_path, spec_text(raw, top=f'name = "toy"\noutput = "out"\nregistry = [{str(changed)!r}]'), "o.toml"))
    assert fp(other) != fp(via)


def test_a_name_that_is_not_in_any_registry_is_only_a_label(tmp_path, raw):
    spec = dataset.load(write(tmp_path, spec_text(raw, extra_source='readout = "DCRC_RUN76"')))
    assert spec.sources[0].detector_record is None and spec.sources[0].readout == DCRC_RUN76
    assert not spec.registry.detectors()


def test_root_detector_comes_from_the_registry_unless_the_file_writes_it(tmp_path, raw):
    reg = folder(tmp_path)
    top = f'name = "t"\noutput = "o"\noutput_format = "root"\nregistry = [{str(reg)!r}]'
    assert dataset.load(write(tmp_path, spec_text(raw, top=top))).root_detector == 7
    with pytest.warns(UserWarning, match="not the number the registry gives"):
        assert dataset.load(write(tmp_path, spec_text(raw, top=top + "\nroot_detector = 2"), "w.toml")).root_detector == 2
    nonumber = folder(tmp_path, TOY.replace("number = 7\n", ""), sub="nonumber")
    with pytest.raises(ValueError, match="needs root_detector = N.*or one detector in a registry"):
        dataset.load(write(tmp_path, spec_text(raw, top=f'name = "t"\noutput = "o"\noutput_format = "root"\nregistry = [{str(nonumber)!r}]'), "n.toml"))


def test_a_bad_registry_key_or_folder_is_refused(tmp_path, raw):
    with pytest.raises(ValueError, match="registry must be a folder or a list of folders"):
        dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\nregistry = 3')))
    with pytest.raises(ValueError, match="does not exist"):
        dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\nregistry = ["nowhere"]'), "m.toml"))


def test_relative_registry_folders_start_at_the_definition_file(tmp_path, raw):
    (tmp_path / "sub").mkdir()
    folder(tmp_path, sub="sub/reg")
    spec = dataset.load(write(tmp_path, spec_text(raw, top='name = "t"\noutput = "o"\nregistry = ["sub/reg"]')))
    assert spec.registry.has_detector("TOY")
