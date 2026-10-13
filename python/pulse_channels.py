"""Which physical detector channel is a dump's (detector, channel) pair?

A dump labels its traces `<event>_<detector>_Phonon_<n>` and holds 4 channels per
detector, so a trace is addressed by two small integers: `detector` (0, 1, 2) and
`channel` (0 to 3). In Run 76 those are not three detectors but three 4-channel
readout boards (DCRC1, DCRC3, DCRC4) of one two-sided detector, and the real
channel names are `Side1pA` ... `Side1pF`, `Side2pA` ... `Side2pF`. This module
turns the two integers into those names::

    import pulse_channels as pch

    pch.channel_name(0, 2)      # 'Side1pC'
    pch.channel_label(0, 2)     # 'Side1pC (DCRC1, Face3pC)'
    pch.channel_info(0, 2)      # Channel(detector=0, channel=2, name='Side1pC', ...)
    pch.find_channel('Side1pC') # (0, 2)
    pch.all_channels()          # the 12 Channel records, in (detector, channel) order

The table behind it is the *Setup* table of the Run 76 summary
(https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76.html), read
with the `Label` column as the channel name (the HV columns repeat entries and are
not used). Only this module knows the table; everything else in `python/` works on
plain arrays and indices.

The mapping is **under development**: that the dump's detectors 0, 1, 2 are DCRC1,
DCRC3, DCRC4 (ascending board number) is inferred, and that channels 0 to 3 follow
the table's row order within a board is assumed. Both are explained, with the
evidence, in section 7 of `noise-psd-randoms-buddy.ipynb` on the `student-buddy` branch.
If they turn out wrong, change `DCRC_OF_DETECTOR` or `ROWS` below and nothing else.
"""
from typing import NamedTuple

from pulse_status import status, UNDER_DEVELOPMENT

_NOTE = ("the dump's detector index -> DCRC board order (0,1,2 = DCRC1,DCRC3,DCRC4) is inferred, and "
         "the channel order within a board is assumed; not yet confirmed against the run's ODB")

# Rows of the Run 76 Setup table for each DCRC board, in table order:
# (tower input, Label column = detector channel).
ROWS = {
    "DCRC1": [("Face3pA", "Side2pC"), ("Face3pB", "Side2pF"), ("Face3pC", "Side1pC"), ("Face3pD", "Side1pF")],
    "DCRC3": [("Face5pA", "Side1pE"), ("Face5pB", "Side1pB"), ("Face5pC", "Side1pD"), ("Face5pD", "Side2pE")],
    "DCRC4": [("Face2pA", "Side2pB"), ("Face2pB", "Side2pA"), ("Face2pC", "Side1pA"), ("Face2pD", "Side2pD")],
}
# Dump detector index -> DCRC board.
DCRC_OF_DETECTOR = {0: "DCRC1", 1: "DCRC3", 2: "DCRC4"}


class Channel(NamedTuple):
    """One physical channel: where it is in the dump and what it is on the detector."""
    detector: int       # dump detector index (0, 1, 2)
    channel: int        # dump channel index within the detector (0 to 3)
    name: str           # detector channel, e.g. 'Side1pC'
    side: int           # 1 or 2
    letter: str         # 'A' to 'F'
    dcrc: str           # readout board, e.g. 'DCRC1'
    tower_input: str    # tower input, e.g. 'Face3pC'


def _build():
    table = []
    for det, dcrc in DCRC_OF_DETECTOR.items():
        for ch, (tower, name) in enumerate(ROWS[dcrc]):
            table.append(Channel(det, ch, name, int(name[4]), name[-1], dcrc, tower))
    return {(c.detector, c.channel): c for c in table}


_CHANNELS = _build()


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_info(detector: int, channel: int) -> Channel:
    """The `Channel` record for a dump (detector, channel) pair."""
    try:
        return _CHANNELS[(int(detector), int(channel))]
    except KeyError:
        raise ValueError(f"no such channel: detector {detector}, channel {channel} "
                         "(detector is 0 to 2, channel is 0 to 3)") from None


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_name(detector: int, channel: int) -> str:
    """Detector channel name, e.g. `channel_name(0, 2) == 'Side1pC'`."""
    return channel_info(detector, channel).name


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_label(detector: int, channel: int) -> str:
    """Name with the board and tower input, for plot labels: `'Side1pC (DCRC1, Face3pC)'`."""
    c = channel_info(detector, channel)
    return f"{c.name} ({c.dcrc}, {c.tower_input})"


@status(UNDER_DEVELOPMENT, note=_NOTE)
def find_channel(name: str) -> tuple:
    """The dump `(detector, channel)` of a detector channel name, e.g. `find_channel('Side1pC') == (0, 2)`."""
    for (det, ch), c in _CHANNELS.items():
        if c.name == name:
            return det, ch
    raise ValueError(f"unknown channel name {name!r} (expected Side1pA ... Side2pF, as listed by all_channels())")


@status(UNDER_DEVELOPMENT, note=_NOTE)
def all_channels() -> list:
    """All 12 `Channel` records, in (detector, channel) order."""
    return list(_CHANNELS.values())
