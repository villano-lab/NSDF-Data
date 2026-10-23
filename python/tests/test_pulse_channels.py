import pytest

import pulse_channels as pch


# the functions are tagged under_development and warn on every call
pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def test_twelve_channels_with_unique_names():
    chans = pch.all_channels()
    assert len(chans) == 12
    assert len({c.name for c in chans}) == 12
    assert {(c.detector, c.channel) for c in chans} == {(d, c) for d in range(3) for c in range(4)}


def test_side2_readout_has_six_sensors_all_on_side_2():
    sensors = pch.sensor_channels()
    assert {c.name for c in sensors} == {f"Side2p{l}" for l in "ABCDEF"}
    assert all(c.side == 2 for c in sensors)


def test_side2_readout_map_from_the_setup_table():
    # HV2 = DCRC1: pA, pB, pD = Side2pC, Side2pF, Side2pE (the table, not the explanatory text)
    assert [pch.channel_name(0, c) for c in (0, 1, 3)] == ["Side2pC", "Side2pF", "Side2pE"]
    # HV1 = DCRC3: pA, pB, pD = Side2pB, Side2pA, Side2pD
    assert [pch.channel_name(1, c) for c in (0, 1, 3)] == ["Side2pB", "Side2pA", "Side2pD"]
    # DCRC4 pA is the trigger signal of the NaI array
    assert pch.channel_name(2, 0) == "NaI"


def test_pC_inputs_and_the_rest_of_DCRC4_are_not_connected():
    free = {(c.detector, c.channel) for c in pch.all_channels() if c.role == pch.NOT_CONNECTED}
    assert free == {(0, 2), (1, 2), (2, 1), (2, 2), (2, 3)}
    assert pch.channel_name(0, 2) == "DCRC1pC"


def test_roles():
    roles = [c.role for c in pch.all_channels()]
    assert roles.count(pch.SENSOR) == 6 and roles.count(pch.NAI_TRIGGER) == 1 and roles.count(pch.NOT_CONNECTED) == 5


def test_channel_info_fields():
    c = pch.channel_info(1, 0)
    assert (c.dcrc, c.board_input, c.hv_output, c.name, c.side, c.letter) == ("DCRC3", "pA", "HV1 pA", "Side2pB", 2, "B")
    n = pch.channel_info(2, 0)
    assert (n.role, n.side, n.letter, n.hv_output) == (pch.NAI_TRIGGER, None, None, None)


def test_label_includes_board_input_and_hv_pin():
    assert pch.channel_label(0, 0) == "Side2pC (DCRC1 pA, HV2 pA)"
    assert pch.channel_label(2, 0) == "NaI (DCRC4 pA)"


def test_find_channel_round_trips():
    for c in pch.all_channels():
        assert pch.find_channel(c.name) == (c.detector, c.channel)


def test_side1_readout_map_from_the_same_table():
    names = {c.name for c in pch.sensor_channels(readout=1)}
    assert names == {f"Side1p{l}" for l in "ABCDEF"}
    assert pch.channel_name(1, 0, readout=1) == "Side1pE"       # HV1 pA
    assert pch.channel_name(0, 3, readout=1) == "Side1pF"       # HV2 pD


@pytest.mark.parametrize("det,ch", [(3, 0), (0, 4), (-1, 0)])
def test_out_of_range_raises(det, ch):
    with pytest.raises(ValueError):
        pch.channel_info(det, ch)


def test_unknown_readout_raises():
    with pytest.raises(ValueError):
        pch.channel_info(0, 0, readout=3)


def test_find_channel_unknown_name_raises():
    with pytest.raises(ValueError):
        pch.find_channel("Side3pA")
    with pytest.raises(ValueError):
        pch.find_channel("Side1pA")          # not a channel of the Side-2 readout


def test_functions_are_tagged_under_development():
    for f in (pch.channel_info, pch.channel_name, pch.channel_label, pch.find_channel, pch.all_channels,
              pch.sensor_channels):
        assert f.status == "under_development"
