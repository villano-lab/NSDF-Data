"""Which physical detector channel is a dump's (detector, channel) pair?

A dump labels its traces `<event>_<detector>_Phonon_<n>` and holds 4 channels per
detector, so a trace is addressed by two small integers: `detector` (0, 1, 2) and
`channel` (0 to 3). In Run 76 those are not three detectors but three 4-channel
readout boards (DCRC1, DCRC3, DCRC4) of one two-sided detector, and the real
channel names are `Side1pA` ... `Side1pF`, `Side2pA` ... `Side2pF`. This module
turns the two integers into those names::

    import pulse_channels as pch

    pch.channel_name(0, 0)      # 'Side2pC'
    pch.channel_label(0, 0)     # 'Side2pC (DCRC1 pA, HV2 pA)'
    pch.channel_info(0, 0)      # Channel(detector=0, channel=0, name='Side2pC', ...)
    pch.find_channel('Side2pC') # (0, 0)
    pch.all_channels()          # the 12 Channel records, in (detector, channel) order
    pch.sensor_channels()       # the 6 that are QET channels of the detector

**Which table to use.** The *Setup* table of the Run 76 summary
(https://villano-lab.github.io/R76Analysis/cdms/k100/run_summary/run_76.html; Matt
Fritts's explanation of it is on page 28 of notebook N-MISC-23-001) gives, for every
sensor `Label`, the HV connector pin it is wired to in **Side-1 readout** and in
**Side-2 readout**. HV1 and HV2 are the two D-sub connectors the DCRCs plug into
(HV1 is DCRC3, HV2 is DCRC1; the 2022 run diaries' header says
"HV 1(L)/2(R) -> DCRC50(3)/DCRC55(1), ... NaI trigger signal -> DCRCX(4)"), and pin
`pA` ... `pD` of a connector is input `pA` ... `pD` of its DCRC. The table's
*DCRC (2-sided)* column is for the two-sided readout and is **not** used. The run
was in Side-2 readout from late in the Run 76 diaries, so the December 2022 series
(`07221203_2025`) is Side-2 readout, the default here (`readout=2`). In Side-2 readout
only the pins A, B and D carry sensors (pC is for Side-1 readout) and DCRC4 pA
carries the trigger signal of the NaI array, so six channels are sensors, one is the NaI
trigger input and five are not connected. (For DCRC1 the table's A/B order is the one
used; the explanatory text next to the table has A and B the other way round, which
is taken to be a typo.)

Only this module knows the table; everything else in `python/` works on plain
arrays and indices.

The mapping is **under development**: that the dump's detectors 0, 1, 2 are DCRC1,
DCRC3, DCRC4 (ascending board number) is inferred, and that channels 0 to 3 are the
board inputs pA to pD in order is assumed. If they turn out wrong, change
`DCRC_OF_DETECTOR` or the order of the rows in `PINS` and nothing else.

*History.* Until 2026-10-22 this module used the table's *DCRC (2-sided)* column and
named twelve sensors on both sides, which was wrong for Side-2 readout (six of its
"Side 1" channels do not exist in the readout of this series).
"""
from typing import NamedTuple, Optional

from pulse_status import status, UNDER_DEVELOPMENT

_NOTE = ("the dump's detector index -> DCRC board order (0,1,2 = DCRC1,DCRC3,DCRC4) is inferred, and "
         "channels 0 to 3 = board inputs pA to pD is assumed; not yet confirmed against the run's ODB")

#: Roles of a channel.
SENSOR, NAI_TRIGGER, NOT_CONNECTED = "sensor", "nai_trigger", "not_connected"

# Label of each DCRC board input, by readout, in the order of the inputs pA..pD (= dump channels 0..3).
# A sensor is its Label of the Setup table; 'NaI' is the trigger input of the NaI array; None is not connected.
PINS = {
    2: {   # Side-2 readout: HV1 = DCRC3, HV2 = DCRC1, NaI trigger on DCRC4 pA
        "DCRC1": ["Side2pC", "Side2pF", None, "Side2pE"],      # HV2 pA, pB, pC, pD
        "DCRC3": ["Side2pB", "Side2pA", None, "Side2pD"],      # HV1 pA, pB, pC, pD
        "DCRC4": ["NaI", None, None, None],
    },
    1: {   # Side-1 readout (from the same table; not used for the December 2022 series)
        "DCRC1": [None, "Side1pA", "Side1pC", "Side1pF"],      # HV2 pA, pB, pC, pD
        "DCRC3": ["Side1pE", "Side1pB", "Side1pD", None],      # HV1 pA, pB, pC, pD
        "DCRC4": ["NaI", None, None, None],
    },
}
HV_OF_BOARD = {"DCRC1": "HV2", "DCRC3": "HV1", "DCRC4": None}
# Dump detector index -> DCRC board.
DCRC_OF_DETECTOR = {0: "DCRC1", 1: "DCRC3", 2: "DCRC4"}


class Channel(NamedTuple):
    """One channel of the readout: where it is in the dump and what it is on the detector."""
    detector: int            # dump detector index (0, 1, 2)
    channel: int             # dump channel index within the detector (0 to 3)
    name: str                # 'Side2pC' for a sensor, 'NaI' for the trigger input, 'DCRC1pC' for a free input
    role: str                # SENSOR, NAI_TRIGGER or NOT_CONNECTED
    side: Optional[int]      # 1 or 2 for a sensor, else None
    letter: Optional[str]    # 'A' to 'F' for a sensor, else None
    dcrc: str                # readout board, e.g. 'DCRC1'
    board_input: str         # input of that board, 'pA' to 'pD'
    hv_output: Optional[str]  # HV connector pin it is wired to, e.g. 'HV2 pA' (None for the NaI input)


def _build(readout):
    table = {}
    for det, dcrc in DCRC_OF_DETECTOR.items():
        for ch, label in enumerate(PINS[readout][dcrc]):
            inp = "p" + "ABCD"[ch]
            hv = f"{HV_OF_BOARD[dcrc]} {inp}" if HV_OF_BOARD[dcrc] else None
            if label is None:
                c = Channel(det, ch, f"{dcrc}{inp}", NOT_CONNECTED, None, None, dcrc, inp, hv)
            elif label == "NaI":
                c = Channel(det, ch, "NaI", NAI_TRIGGER, None, None, dcrc, inp, None)
            else:
                c = Channel(det, ch, label, SENSOR, int(label[4]), label[-1], dcrc, inp, hv)
            table[(det, ch)] = c
    return table


_TABLES = {r: _build(r) for r in PINS}


def _table(readout):
    try:
        return _TABLES[readout]
    except KeyError:
        raise ValueError(f"readout must be 1 or 2, got {readout!r}") from None


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_info(detector: int, channel: int, readout: int = 2) -> Channel:
    """The `Channel` record for a dump (detector, channel) pair (`readout` 2 = Side-2 readout, the default)."""
    try:
        return _table(readout)[(int(detector), int(channel))]
    except KeyError:
        raise ValueError(f"no such channel: detector {detector}, channel {channel} "
                         "(detector is 0 to 2, channel is 0 to 3)") from None


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_name(detector: int, channel: int, readout: int = 2) -> str:
    """Channel name, e.g. `channel_name(0, 0) == 'Side2pC'`; `'NaI'` for the NaI trigger input."""
    return channel_info(detector, channel, readout).name


@status(UNDER_DEVELOPMENT, note=_NOTE)
def channel_label(detector: int, channel: int, readout: int = 2) -> str:
    """Name with the board input and the HV pin, for plot labels: `'Side2pC (DCRC1 pA, HV2 pA)'`."""
    c = channel_info(detector, channel, readout)
    return f"{c.name} ({c.dcrc} {c.board_input}" + (f", {c.hv_output})" if c.hv_output else ")")


@status(UNDER_DEVELOPMENT, note=_NOTE)
def find_channel(name: str, readout: int = 2) -> tuple:
    """The dump `(detector, channel)` of a channel name, e.g. `find_channel('Side2pC') == (0, 0)`."""
    for (det, ch), c in _table(readout).items():
        if c.name == name:
            return det, ch
    raise ValueError(f"unknown channel name {name!r} for readout {readout} (see all_channels(readout={readout}))")


@status(UNDER_DEVELOPMENT, note=_NOTE)
def all_channels(readout: int = 2) -> list:
    """All 12 `Channel` records (sensors, the NaI input and the free inputs), in (detector, channel) order."""
    return list(_table(readout).values())


@status(UNDER_DEVELOPMENT, note=_NOTE)
def sensor_channels(readout: int = 2) -> list:
    """The `Channel` records of the sensors (6 in Side-2 readout), in (detector, channel) order."""
    return [c for c in _table(readout).values() if c.role == SENSOR]
