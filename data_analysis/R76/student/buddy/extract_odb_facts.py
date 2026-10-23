"""Extract the few run-configuration facts quoted in the PSD note from a raw MIDAS file.

    python extract_odb_facts.py <path to 07220916_2200_F0001.mid.gz> [output.json]

The raw file is not in the repository (it lives on the UMN servers). This script reads its first event, the ODB
(the run configuration, as XML), and the event banks, and writes the numbers the note quotes to a small JSON file,
which the notebook `noise-psd-randoms-buddy.ipynb` (section 12) reads and prints. Only the configuration is kept,
no waveforms.

What it takes from the file:
- /Equipment/Tower01/Settings/DCRC<n>: Enabled, and the QETBias (uA), SQUIDBias (uA) and polarity (0 = feedback
  disabled) of each of the 4 phonon channels.
- /Equipment/Triggerfe2/Settings: the in-run random rate and the beginning-of-run randoms.
- The event banks: the "SCD0" bank of each event holds one record per board; the low byte of the word after each
  record's tag word (0x40000000, 0x100000) is the board code. Reading it this way is our own decoding, not a
  documented format.
"""
import collections
import gzip
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET

import numpy as np

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "odb-facts-07220916_2200.json"

CONTROL_BYTES = re.compile("[" + chr(0) + "-" + chr(8) + chr(11) + chr(12) + chr(14) + "-" + chr(31) + "]")


def flatten(odb_text):
    """The ODB XML as {path: value, or list of values for an array}. The dump has stray control bytes, which are replaced first."""
    text = CONTROL_BYTES.sub("?", odb_text)
    root = ET.fromstring(text.split("?>", 1)[1].split("</odb>")[0] + "</odb>")
    rows = {}

    def walk(element, path):
        for child in element:
            name = child.get("name", "")
            if child.tag == "dir":
                walk(child, path + "/" + name)
            elif child.tag == "key":
                rows[path + "/" + name] = (child.text or "").strip()
            elif child.tag == "keyarray":
                rows[path + "/" + name + "[]"] = [(v.text or "").strip() for v in child]

    walk(root, "")
    return rows


code_counts = collections.Counter()
with gzip.open(src, "rb") as f:
    header = f.read(16)
    size = struct.unpack("<HHIII", header)[4]
    rows = flatten(f.read(size).decode("latin1"))
    while True:
        header = f.read(16)
        if len(header) < 16:
            break
        event_id, mask, serial, ts, size = struct.unpack("<HHIII", header)
        data = f.read(size)
        if event_id == 1 and len(data) > 1000 and data[8:12] == b"SCD0":
            n = struct.unpack("<I", data[16:20])[0]
            words = np.frombuffer(data[20:20 + n][: n // 4 * 4], dtype="<u4")
            starts = np.flatnonzero(words == 0x40000000)
            starts = starts[words[starts + 1] == 0x100000]
            code_counts[tuple(int(words[i + 3] & 0xFF) for i in starts)] += 1


def board_value(n, name):
    """The value at .../Tower01/Settings/DCRC<n>/**/<name>, wherever it sits below the board."""
    pattern = re.compile("^/Equipment/Tower01/Settings/DCRC" + str(n) + "/(?:.*/)?" + re.escape(name) + "$")
    matches = [v for path, v in rows.items() if pattern.match(path)]
    assert len(matches) == 1, (n, name, len(matches))
    return matches[0]


boards = {}
for n in range(1, 7):
    boards["DCRC" + str(n)] = dict(
        enabled=board_value(n, "Enabled"),
        qet_bias_uA=[float(v) for v in board_value(n, "QETBias (uA)[]")],
        squid_bias_uA=[float(v) for v in board_value(n, "SQUIDBias (uA)[]")],
        polarity=[int(v) for v in board_value(n, "polarity[]")],
    )
trigger = {k.split("/")[-1]: v for k, v in rows.items() if k.startswith("/Equipment/Triggerfe2/Settings/")}
facts = dict(
    source=src.replace("\\", "/").split("/")[-1],
    boards=boards,
    in_run_random_rate_hz=float(trigger["RandomRate (Hz)"]),
    n_beginning_of_run_randoms=int(trigger["N Beginning of Run Randoms"]),
    beginning_of_run_freq_hz=float(trigger["Beginning of Run Freq (Hz)"]),
    n_end_of_run_randoms=int(trigger["N End of Run Randoms"]),
    board_code_sequences={",".join(map(str, k)): v for k, v in code_counts.most_common(5)},
)
json.dump(facts, open(out, "w"), indent=1)
print(json.dumps(facts, indent=1)[:3000])
