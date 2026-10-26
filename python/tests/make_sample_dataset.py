"""Makes the small sample dataset in `python/tests/data/sample_dataset/` (synthetic, deterministic).

    python python/tests/make_sample_dataset.py

It is committed, because it is the file that the conformance tests of goldpan read, and that the tests of goldsluice should
read too. Re-run this only when the format version changes, and commit the result with the new specification.
"""
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from goldpan.adapters import parquet                                    # noqa: E402
from goldpan.config import PulseConfig                                  # noqa: E402
from goldpan.data import ChannelInfo, Detector, Events, Readout         # noqa: E402

OUT = HERE / "data" / "sample_dataset"
N_SAMPLES = 256


def detector() -> Detector:
    return Detector("SAMPLE", (ChannelInfo("A", role="phonon", unit="board0", input="0"),
                               ChannelInfo("B", role="phonon", unit="board0", input="1")),
                    Readout.single(N_SAMPLES, PulseConfig(pretrigger_samples=64, glitch_samples=4, sample_period_s=1.0e-6)))


def events(dump: str, n: int, first_event: int, seed: int) -> Events:
    rng = np.random.default_rng(seed)
    traces = {c: rng.normal(0.0, 2.0, (n, N_SAMPLES)).astype(np.float32) for c in ("A", "B")}
    traces["A"][::3, 64:128] += 50.0                                    # every third event has a pulse in A
    std = traces["A"][:, 4:64].std(axis=-1)
    return Events.from_arrays(
        detector(), traces, series="SERIES1", dump=dump, event=np.arange(n) + first_event,
        quantities={
            "t_trigger": 100.0 + 0.5 * (np.arange(n) + first_event),
            "trigger_type": np.where(np.arange(n) % 2 == 0, "random", "physics"),
            "A": {"std": std, "max": traces["A"].max(axis=-1)},         # a record per channel
            "pulse_times": [list(np.round(np.arange(k % 3) * 1e-5, 6)) for k in range(n)],   # variable length
        },
        meta={"source": "synthetic: python/tests/make_sample_dataset.py", "clock": "sample-daq",
              "units": {"t_trigger": "s", "A.std": "counts", "A.max": "counts", "pulse_times": "s"}},
    )


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    parquet.write(events("F0001", 14, 0, 1), OUT)
    parquet.write(events("F0002", 10, 5000, 2), OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
