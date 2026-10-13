import pytest

import pulse_channels as pch


# the functions are tagged under_development and warn on every call
pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def test_twelve_channels_with_unique_names():
    chans = pch.all_channels()
    assert len(chans) == 12
    assert len({c.name for c in chans}) == 12
    assert {(c.detector, c.channel) for c in chans} == {(d, c) for d in range(3) for c in range(4)}


def test_names_cover_both_sides_a_to_f():
    names = {c.name for c in pch.all_channels()}
    assert names == {f"Side{s}p{l}" for s in (1, 2) for l in "ABCDEF"}


def test_known_entries_from_the_setup_table():
    assert pch.channel_name(0, 0) == "Side2pC"      # DCRC1, Face3pA
    assert pch.channel_name(0, 2) == "Side1pC"
    assert pch.channel_name(1, 3) == "Side2pE"      # DCRC3, Face5pD
    assert pch.channel_name(2, 2) == "Side1pA"      # DCRC4, Face2pC


def test_channel_info_fields():
    c = pch.channel_info(1, 0)
    assert (c.dcrc, c.tower_input, c.name, c.side, c.letter) == ("DCRC3", "Face5pA", "Side1pE", 1, "E")


def test_label_includes_board_and_tower_input():
    assert pch.channel_label(0, 2) == "Side1pC (DCRC1, Face3pC)"


def test_find_channel_round_trips():
    for c in pch.all_channels():
        assert pch.find_channel(c.name) == (c.detector, c.channel)


@pytest.mark.parametrize("det,ch", [(3, 0), (0, 4), (-1, 0)])
def test_out_of_range_raises(det, ch):
    with pytest.raises(ValueError):
        pch.channel_info(det, ch)


def test_find_channel_unknown_name_raises():
    with pytest.raises(ValueError):
        pch.find_channel("Side3pA")


def test_functions_are_tagged_under_development():
    for f in (pch.channel_info, pch.channel_name, pch.channel_label, pch.find_channel, pch.all_channels):
        assert f.status == "under_development"
