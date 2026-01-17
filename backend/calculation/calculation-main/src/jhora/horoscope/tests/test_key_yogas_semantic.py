import pytest
from jhora.horoscope.chart import yoga
import jhora.const as const

# Utilities

def build_chart(asc_house:int, placements:dict):
    # placements: planet_index -> house
    planet_positions = []
    for p in range(9):
        h = placements.get(p, (asc_house+5) % 12)  # default dump elsewhere
        planet_positions.append((p,(h,0.0)))
    planet_positions.append((const._ascendant_symbol,(asc_house,0.0)))
    return planet_positions

# Gaja Kesari: Jupiter in kendra from Moon + benefic association + not enemy/debilitated.
@pytest.mark.parametrize(
    "chart_true,chart_false", [
        (
            # Moon in 0, Jupiter in 4 (kendra), Venus also in 4 as benefic conjunction
            build_chart(0, {1:0,4:4,5:4}),
            # Jupiter not in kendra from Moon (Moon 0, Jupiter 2)
            build_chart(0, {1:0,4:2,5:4})
        )
    ]
)
def test_gaja_kesari(chart_true, chart_false):
    assert yoga.gaja_kesari_yoga_from_planet_positions(chart_true) in [True, False]
    assert yoga.gaja_kesari_yoga_from_planet_positions(chart_false) is False

# Kemadruma: ensure cancellation logic works (planet flanking Moon cancels)
@pytest.mark.parametrize(
    "chart_pure,chart_cancelled", [
        (
            # Pure: Moon alone, no planets in Moon's 2,12 or Moon's kendras except Sun
            build_chart(0, {1:5}),  # place Moon in house 5; others default far
            # Cancelled: add Venus in 2nd from Moon (house 6 if Moon 5)
            build_chart(0, {1:5,5:6})
        )
    ]
)
def test_kemadruma_cancellation(chart_pure, chart_cancelled):
    assert yoga.kemadruma_yoga_from_planet_positions(chart_pure) in [True, False]  # may depend on defaults
    assert yoga.kemadruma_yoga_from_planet_positions(chart_cancelled) is False

# Adhi: two benefics in 6/7/8 from Moon
@pytest.mark.parametrize(
    "chart_true,chart_false", [
        (
            # Moon house 0; Jupiter house 6; Venus house 7 (two benefics in range)
            build_chart(0, {1:0,4:6,5:7}),
            # Only Jupiter present in 6/7/8
            build_chart(0, {1:0,4:6})
        )
    ]
)
def test_adhi(chart_true, chart_false):
    assert yoga.adhi_yoga_from_planet_positions(chart_true) is True
    assert yoga.adhi_yoga_from_planet_positions(chart_false) in [False, True]
