"""A small synthetic series written in four formats from one set of events, to test every adapter and cross-format consistency.

    python python/tests/synthetic_series.py OUTDIR            # writes OUTDIR/{idx,midas,rq_parquet,rq_root,goldpan}

The data are **made up** (nothing here is from a detector): the series name and the layout imitate the Run 76 (Side-2 readout)
series 07221203_2025 so that the real channel map and presets apply, but the numbers are random. The same `Dump` objects are
written as

* `idx/<series>_<dump>/`: the NSDF archive layout read by `nsdf_dark_matter.idx` (`<name>.idx`, `.csv`, `.txt` and `<name>/0000.bin`); needs OpenVisus.
* `midas/`: the SuperCDMS SNOLAB DAQ raw format, as `.mid.gz` files (format version 8 of the CDMS I/O library, written here
  from its `pack_event`; `read_midas` below reads it back, following `unpack_event`).
* `rq_parquet/` and `rq_root/`: the processed quantities (RQs) of every event in the style of the collaboration's reconstruction
  (`rqDir/eventTree` and `rqDir/zip1` in the ROOT file), with Run 76 channel names; needs uproot for the ROOT files.
* `goldpan/`: the traces as a native goldpan Parquet dataset (`goldpan.adapters.parquet`).

Deterministic: the same arguments give the same files. `read_midas`, `rqs` and `all_dumps` are the references the tests compare
the other readers with.
"""
import gzip
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from goldpan.channels import sensor_channels                       # noqa: E402
from goldpan.config import DCRC_RUN76                              # noqa: E402

SERIES = "07221203_2025"
N_SAMPLES = 4096
N_BOARDS, N_INPUTS = 3, 4                  # DCRC1, DCRC3, DCRC4 with four inputs each (dump detector index 0, 1, 2)
CONFIG = DCRC_RUN76                        # 1000-sample pretrigger window, 10 glitch samples, 0.8 us
AMPS_PER_COUNT = 1.0e-8                    # synthetic calibration, counts to amps
BASELINE_COUNTS = 8000
TRIGGER_TYPES = {1: "Physics", 2: "BeginOfRunRandom", 3: "InRunRandom"}     # the codes of CDMS_EVENT.triggerType
DUMPS = (("F0001", 14, 10000), ("F0002", 10, 10000))                         # (dump, n events, first event number)
START_TIME = 1670120747                    # unix seconds, the first event of the real series


def sensors():
    """`[(name, board, input)]` of the six Side-2 sensors, from `goldpan.channels.sensor_channels()`."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return [(c.name, c.detector, c.channel) for c in sensor_channels()]


@dataclass
class Dump:
    """One dump: `traces` is `(n_events, 3, 4, n_samples)` uint16 (event, board, input, sample)."""
    series: str
    dump: str
    event: np.ndarray            # event numbers
    trigger_type: np.ndarray     # codes of TRIGGER_TYPES
    timestamp: np.ndarray        # unix seconds
    traces: np.ndarray
    pileup: np.ndarray           # a random trigger with a pulse in it

    @property
    def n_events(self):
        return len(self.event)


def _pulse(amplitude, start=1000):
    t = np.arange(N_SAMPLES - start) * CONFIG.sample_period_s
    shape = np.exp(-t / 150e-6) - np.exp(-t / 15e-6)
    out = np.zeros(N_SAMPLES)
    out[start:] = amplitude * shape / shape.max()
    return out


def make_dump(dump, n_events, first_event, seed):
    """Deterministic events: every third a physics trigger with a pulse in all six sensors, the rest random triggers (one of
    them, the 5th, with a pulse in it: pileup)."""
    rng = np.random.default_rng(seed)
    event = np.arange(n_events) + first_event
    trigger_type = np.where(np.arange(n_events) % 3 == 0, 1, np.where(np.arange(n_events) % 3 == 1, 2, 3))
    pileup = np.zeros(n_events, dtype=bool)
    pileup[4] = True
    trigger_type[4] = 3
    traces = np.empty((n_events, N_BOARDS, N_INPUTS, N_SAMPLES), dtype=np.uint16)
    share = {(b, i): rng.uniform(0.6, 1.0) for _, b, i in sensors()}
    for e in range(n_events):
        for b in range(N_BOARDS):
            for i in range(N_INPUTS):
                y = BASELINE_COUNTS + 40 * b + 7 * i + rng.normal(0.0, 3.0, N_SAMPLES)
                if (b, i) in share and (trigger_type[e] == 1 or pileup[e]):
                    y += _pulse(rng.uniform(300, 1500) * share[(b, i)])
                traces[e, b, i] = np.clip(np.round(y), 0, 65535).astype(np.uint16)
    return Dump(SERIES, dump, event, trigger_type.astype(int), START_TIME + 2 * np.arange(n_events), traces, pileup)


def all_dumps():
    return [make_dump(d, n, first, seed=100 + k) for k, (d, n, first) in enumerate(DUMPS)]


# ---- idx -------------------------------------------------------------------------------------------------------

def write_idx(dump: Dump, outdir) -> Path:
    """`<outdir>/<series>_<dump>/` holding `<series>_<dump>.{idx,csv,txt}` and the folder with `0000.bin`: the layout of a dump
    in `~/idx`, as `nsdf_dark_matter.idx.load_all_data` expects. Returns that folder."""
    import OpenVisus as ov
    name = f"{dump.series}_{dump.dump}"
    outdir = Path(outdir) / name
    outdir.mkdir(parents=True, exist_ok=True)
    rows = dump.traces.reshape(dump.n_events * N_BOARDS * N_INPUTS, N_SAMPLES)
    db = ov.CreateIdx(url=str(outdir / f"{name}.idx"), dims=[N_SAMPLES, rows.shape[0]], fields=[ov.Field("data", "uint16")],
                      compression="zip")
    db.write(np.ascontiguousarray(rows))
    lines, r = [], 0
    for ev in dump.event:
        for b in range(N_BOARDS):
            lines.append(f"{ev}_{b}_Phonon_{N_SAMPLES} {r} {r + N_INPUTS}")
            r += N_INPUTS
    (outdir / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    csv = ["event,trigger_type,readout_type,global_timestamp"]
    csv += [f"{e},{TRIGGER_TYPES[t]},None,{ts}" for e, t, ts in zip(dump.event, dump.trigger_type, dump.timestamp)]
    (outdir / f"{name}.csv").write_text("\n".join(csv) + "\n", encoding="utf-8")
    return outdir


# ---- MIDAS -----------------------------------------------------------------------------------------------------

FORMAT_VERSION = 8
HEAD = dict(channel=0x0, channelBlock=0x1, detectorBlock=0x2, detectorHead=0x3, trigger=0x5, primBlock=0x6, primHead=0x7,
            trailer=0x8, overall=0x9, sduPrimHead=0xA, sduHead=0xF)
DETECTOR_TYPE, DCRC_VERSION, PHONON = 700, 40, 1
SAMPLE_RATE_KHZ = 1250
FIRST_EVENT = {d: first for d, _, first in DUMPS}
RUN_NUMBER = 2626                           # also the serial number of the begin- and end-of-run events, as in the real files
BOR_MASK = 0x494D                           # the mask of the begin/end-of-run events of the real DAQ
POLLING = 8                                 # trigger type of a polling-cycle event: no detectors, no traces


def _hdr(kind, value):
    return (HEAD[kind] << 28) | value


def pack_event(dump: Dump, e: int) -> np.ndarray:
    """The CDMS event `e` of `dump` as a uint32 array in the SNOLAB format, version 8 (`CDMSIOLIB::pack_event`)."""
    w = []
    esb = N_BOARDS * N_INPUTS * 2 * N_SAMPLES                                    # eventSizeBytes: the waveforms only
    ts = int(dump.timestamp[e])
    w += [_hdr("overall", (FORMAT_VERSION << 12) | 1)]
    # trigger block: size, triggerID, eventNumber, readoutType<<8 | triggerType, global time low/high, polling cycle time and fraction
    w += [_hdr("trigger", esb), int(dump.event[e]) - FIRST_EVENT[dump.dump] + 1, int(dump.event[e]),
          (0 << 8) | int(dump.trigger_type[e]), ts, 0, 0, 0]
    w += [_hdr("primHead", 1), 6 * 4]                                            # one primitive; the library counts 6 words x 4 bytes
    w += [_hdr("primBlock", (1 << 12) | (1 << 2)), ts, 0, 0, 0, 0xFFFF << 16, 1000]
    w += [_hdr("detectorHead", N_BOARDS)]
    for b in range(N_BOARDS):
        # detector block: type/ID/DCRC index; serials and versions; status and series time; fraction; waveform read times (3)
        w += [_hdr("detectorBlock", (DETECTOR_TYPE << 10) | ((b + 1) << 2) | 0),
              (DCRC_VERSION << 16) | ((b + 1) << 8) | DCRC_VERSION, 0, 0, 0, 0, 0]
        w += [_hdr("channel", N_INPUTS)]
        for i in range(N_INPUTS):
            # channel block: pretrigger offset, channel number, baseline control, type; pre-, on-, post-pulse lengths;
            # sample rate and downsampling factor
            w += [_hdr("channelBlock", (CONFIG.pretrigger_samples << 6) | (i << 2) | (0 << 1) | PHONON),
                  0, N_SAMPLES, 0, (SAMPLE_RATE_KHZ << 16) | 1]
            words = np.ascontiguousarray(dump.traces[e, b, i]).astype("<u2").view("<u4")     # two samples per word, first one low
            w += [int(x) for x in words]
    w += [_hdr("sduPrimHead", 0), 0, _hdr("sduHead", 0)]
    w += [_hdr("trailer", 0)]
    return np.array(w, dtype="<u4")


def pack_polling_event(timestamp: int) -> np.ndarray:
    """A polling-cycle metadata event (trigger type 8): its SCD0 bank in the real files has no primitives and no detectors."""
    w = [_hdr("overall", (FORMAT_VERSION << 12) | 1), _hdr("trigger", 0), 2, 0, POLLING, timestamp, 0, 2234, 7000000,
         _hdr("primHead", 0), 0, _hdr("detectorHead", 0), _hdr("sduPrimHead", 0), 0, _hdr("sduHead", 0), _hdr("trailer", 0)]
    return np.array(w, dtype="<u4")


def _midas_event(event_id, mask, serial, timestamp, data: bytes) -> bytes:
    return struct.pack("<HHIII", event_id, mask, serial, timestamp, len(data)) + data


def odb_xml(dump: Dump, final: bool = False) -> bytes:
    """A small ODB (begin of run, or end of run with `final=True`) in the XML of the DAQ: `Runinfo` and the readout control settings
    of the detectors. Keys carry a `handle` attribute and directories too, as in the real files."""
    def key(name, typ, value):
        return f'<key name="{name}" type="{typ}" handle="1">{value}</key>'
    stop = START_TIME + 7200 if final else 0
    parts = ['<?xml version="1.0" encoding="ISO-8859-1"?>', '<odb root="/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xsi:noNamespaceSchemaLocation="http://midas.psi.ch/odb.xsd">', '<dir name="Experiment"><dir name="Edit on start">',
             key("Data type", "INT", 1), key("Start comment", "STRING", "synthetic series for tests"), '</dir></dir>',
             '<dir name="Runinfo" handle="1">', key("State", "INT", 3 if final else 1), key("Run number", "INT", RUN_NUMBER),
             key("Start time binary", "UINT32", START_TIME), key("Stop time binary", "UINT32", stop), '</dir>',
             '<dir name="Detectors">']
    for b in range(N_BOARDS):
        parts += [f'<dir name="Det{b + 1:02d}"><dir name="DCRCInfo">', key("Tower", "INT", 1), key("DetectorType", "INT", DETECTOR_TYPE),
                  '</dir><dir name="Readback"><dir name="ReadoutControl">',
                  key("Phonon pre-trigger offset (samp)", "INT", CONFIG.pretrigger_samples),
                  key("Phonon on-pulse length (samp)", "INT", N_SAMPLES), key("Phonon pre-pulse length (samp)", "INT", 0),
                  key("Phonon post-pulse length (samp)", "INT", 0),
                  key("Phonon sampling rate (Hz)", "FLOAT", f"{1.0 / CONFIG.sample_period_s:f}"),
                  '</dir></dir></dir>']
    parts += ['</dir></odb>']
    return "\n".join(parts).encode("latin-1")


def write_midas(dump: Dump, outdir) -> Path:
    """`<outdir>/<series>_<dump>.mid.gz`: a begin-of-run event with the ODB, a veto-only event (bank `LDV0`), one event per trigger
    with the bank `SCD0` and a polling-cycle event after the third, then the end-of-run event with the final ODB."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{dump.series}_{dump.dump}.mid.gz"
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(_midas_event(0x8000, BOR_MASK, RUN_NUMBER, START_TIME, odb_xml(dump)))
        serial = 0

        def write_bank(name, payload, timestamp):
            nonlocal serial
            if len(payload) % 2:                                                  # banks are aligned to 8 bytes
                payload = np.append(payload, np.uint32(0))
            bank = name + struct.pack("<II", 6, len(payload) * 4)                 # name, TID_DWORD, size in bytes
            body = bank + payload.tobytes()
            data = struct.pack("<II", len(body), (1 | (1 << 4))) + body           # bank header: size, flags (version | 32-bit)
            f.write(_midas_event(1, 0, serial, timestamp, data))
            serial += 1

        write_bank(b"LDV0", np.arange(31, dtype="<u4") + 0xF0000000, START_TIME)
        for e in range(dump.n_events):
            write_bank(b"SCD0", pack_event(dump, e), int(dump.timestamp[e]))
            if e == 2:
                write_bank(b"SCD0", pack_polling_event(int(dump.timestamp[e]) + 1), int(dump.timestamp[e]) + 1)
        f.write(_midas_event(0x8001, BOR_MASK, RUN_NUMBER, START_TIME + 7200, odb_xml(dump, final=True)))
    return path


def read_midas(path) -> dict:
    """Read a file made by `write_midas`, following `CDMSIOLIB::unpack_event` (format version 8).

    Returns `dict(odb=<xml bytes>, odb_end=<xml bytes or None>, vetoes=<number of veto-only events>, events=[dict(trigger_id, event_number, trigger_type, readout_type, timestamp,
    detectors=[dict(detector_type, detector_id, channels=[dict(channel_num, channel_type, pretrigger, sample_rate_khz,
    downsampling, data)])])])`.
    """
    raw = gzip.open(path, "rb").read() if str(path).endswith(".gz") else Path(path).read_bytes()
    pos, odb, odb_end, vetoes, events = 0, b"", None, 0, []
    while pos < len(raw):
        event_id, mask, serial, ts, size = struct.unpack_from("<HHIII", raw, pos)
        pos += 16
        data = raw[pos:pos + size]
        pos += size
        if event_id == 0x8000:
            odb = data
        elif event_id == 0x8001:
            odb_end = data
        elif struct.unpack_from("<4s", data, 8)[0] == b"SCD0":
            events.append(_unpack_bank_event(data))
        else:
            vetoes += 1
    return {"odb": odb, "odb_end": odb_end, "vetoes": vetoes, "events": events}


def _unpack_bank_event(data: bytes) -> dict:
    size, flags = struct.unpack_from("<II", data, 0)
    name, typ, bank_size = struct.unpack_from("<4sII", data, 8)
    assert name == b"SCD0" and flags & (1 << 4), "expected a 32-bit SCD0 bank"
    d = np.frombuffer(data, dtype="<u4", count=bank_size // 4, offset=20)
    p = 0

    def take():
        nonlocal p
        p += 1
        return int(d[p - 1])

    def head(kind):
        v = take()
        assert v >> 28 == HEAD[kind], f"expected a {kind} head, got {v >> 28:#x}"
        return v & 0x0FFFFFFF

    assert take() >> 28 == HEAD["overall"]
    head("trigger")
    ev = dict(trigger_id=take(), event_number=take())
    v = take()
    ev["readout_type"], ev["trigger_type"] = v >> 8, v & 0xFF
    lo, hi = take(), take()
    ev["timestamp"] = (hi << 32) | lo
    take(), take()                                                                # polling cycle end time and fraction
    n_prims = head("primHead")
    take()
    for _ in range(n_prims):
        head("primBlock")
        for _ in range(6):
            take()
    detectors = []
    for _ in range(head("detectorHead")):
        v = take()
        assert v >> 28 == HEAD["detectorBlock"]
        det = dict(detector_type=(v >> 10) & 0x3FFFF, detector_id=(v >> 2) & 0xFF)
        for _ in range(6):                      # serials/versions, status and series time, fraction, waveform read times (3)
            take()
        chans = []
        for _ in range(head("channel")):
            v = take()
            assert v >> 28 == HEAD["channelBlock"]
            ch = dict(pretrigger=(v >> 6) & 0x3FFFFF, channel_num=(v >> 2) & 0xF, channel_type=v & 1)
            pre, on, post, rate = take(), take(), take(), take()
            ch["sample_rate_khz"], ch["downsampling"] = rate >> 16, rate & 0xFFFF
            n = pre + on + post
            rows = (n + 1) // 2
            ch["data"] = d[p:p + rows].astype("<u4").view("<u2")[:n].copy()
            p += rows
            chans.append(ch)
        det["channels"] = chans
        detectors.append(det)
    ev["detectors"] = detectors
    head("sduPrimHead")
    take()
    head("sduHead")
    head("trailer")
    return ev


# ---- RQs -------------------------------------------------------------------------------------------------------

def rqs(dump: Dump) -> dict:
    """The processed quantities of every event as a dict of arrays: `EventNumber`, `DumpNumber`, `EventType` (1 physics, 2 random),
    `TriggerDetectorNum`, `PTOFamps`, `PTOFdelay`, and for each sensor `<name>std` (amps), `<name>max` (microamps, as BatCommon
    stores it) and `<name>maxbin`."""
    out = {"EventNumber": dump.event.astype(np.int64), "DumpNumber": np.full(dump.n_events, int(dump.dump[1:]), dtype=np.int64),
           "EventType": np.where(dump.trigger_type == 1, 1, 2).astype(np.int64),
           "TriggerDetectorNum": np.full(dump.n_events, 1, dtype=np.int64)}
    total = np.zeros(dump.n_events)
    for name, b, i in sensors():
        x = dump.traces[:, b, i, :].astype(float)
        base = x[:, CONFIG.glitch_samples:CONFIG.pretrigger_samples]
        peak = x.max(axis=1) - base.mean(axis=1)
        out[f"{name}std"] = base.std(axis=1) * AMPS_PER_COUNT
        out[f"{name}max"] = peak * AMPS_PER_COUNT * 1e6
        out[f"{name}maxbin"] = x.argmax(axis=1).astype(np.int64)
        total += peak * AMPS_PER_COUNT
    out["PTOFamps"] = total
    out["PTOFdelay"] = np.full(dump.n_events, 0.0)
    return out


def write_rq_parquet(dump: Dump, outdir) -> Path:
    """`<outdir>/<series>_<dump>.parquet`: the RQs as one flat table, with the event key columns first."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    table = pa.table({"series": [dump.series] * dump.n_events, "dump": [dump.dump] * dump.n_events, **rqs(dump)})
    table = table.replace_schema_metadata({"goldpan.kind": "rq", "goldpan.units": json.dumps({"std": "A", "max": "uA"})})
    path = outdir / f"{dump.series}_{dump.dump}.parquet"
    pq.write_table(table, path, compression="zstd")
    return path


EVENT_LEVEL_RQS = ("EventNumber", "DumpNumber", "EventType", "TriggerDetectorNum", "PTOFamps", "PTOFdelay")


def write_rq_root(dump: Dump, outdir) -> Path:
    """`<outdir>/<series>_<dump>.root`: the RQs in `rqDir/eventTree` (event level) and `rqDir/zip1` (per channel), like the
    collaboration's processed files."""
    import uproot
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    r = rqs(dump)
    path = outdir / f"{dump.series}_{dump.dump}.root"
    with uproot.recreate(path) as f:
        f["rqDir/eventTree"] = {k: r[k] for k in EVENT_LEVEL_RQS}
        f["rqDir/zip1"] = {k: v for k, v in r.items() if k not in EVENT_LEVEL_RQS}
    return path


def write_goldpan(dump: Dump, outdir) -> Path:
    """The traces of the six sensors as a native goldpan Parquet dataset (stream `NSDF`)."""
    from goldpan.adapters import parquet
    from goldpan.data import ChannelInfo, Detector, Events, Readout
    chans = sensors()
    detector = Detector("NSDF", tuple(ChannelInfo(n, role="phonon", unit=f"board{b}", input=str(i)) for n, b, i in chans),
                        Readout.single(N_SAMPLES, CONFIG))
    ev = Events.from_arrays(detector, {n: dump.traces[:, b, i, :] for n, b, i in chans}, series=dump.series, dump=dump.dump,
                            event=dump.event,
                            quantities={"trigger_type": [TRIGGER_TYPES[t] for t in dump.trigger_type],
                                        "t_trigger": (dump.timestamp - START_TIME).astype(float)},
                            meta={"source": "synthetic: python/tests/synthetic_series.py", "clock": "unix-seconds"})
    parquet.write(ev, outdir)
    return Path(outdir)


WRITERS = dict(idx=write_idx, midas=write_midas, rq_parquet=write_rq_parquet, rq_root=write_rq_root, goldpan=write_goldpan)


def write_all(outdir, formats=tuple(WRITERS)) -> dict:
    """Write every format under `outdir/<format>/`; returns `{format: folder}`."""
    outdir = Path(outdir)
    dumps = all_dumps()
    for fmt in formats:
        for dump in dumps:
            WRITERS[fmt](dump, outdir / fmt)
    return {fmt: outdir / fmt for fmt in formats}


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "synthetic_series")
    for fmt, folder in write_all(target).items():
        print(f"{fmt}: {folder}")
