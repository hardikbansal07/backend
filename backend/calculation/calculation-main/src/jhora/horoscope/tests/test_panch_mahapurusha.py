import pytest
from jhora.horoscope.chart import yoga
import jhora.const as const

# Helper to build planet_positions list
# planet_positions iterable of (planet,(house,long)) plus ('L',(asc_house,0.0)) for ascendant
# Unspecified planets can be placed in some neutral house (e.g., (asc_house+2)%12)

def build_chart(asc_house:int, placements:dict):
    neutral = (asc_house + 2) % 12
    planet_positions = []
    for p in range(9):  # 0..8
        h = placements.get(p, neutral)
        planet_positions.append((p,(h,0.0)))
    planet_positions.append((const._ascendant_symbol,(asc_house,0.0)))
    return planet_positions

# Expected triggering charts for each Mahapurusha yoga.
# Ruchaka: Mars (2) in Aries(0)/Scorpio(7)/Capricorn(9) and kendra from Lagna.
# Bhadra: Mercury (3) in Gemini(2)/Virgo(5) and kendra from Lagna.
# Hamsa: Jupiter (4) in Cancer(3)/Sagittarius(8)/Pisces(11) and kendra.
# Maalavya: Venus (5) in Taurus(1)/Libra(6)/Pisces(11) and kendra.
# Sasa: Saturn (6) in Capricorn(9)/Aquarius(10)/Libra(6) and kendra.

@pytest.mark.parametrize(
    "name,func,chart_true,chart_false",
    [
        (
            "Ruchaka", yoga.ruchaka_yoga_from_planet_positions,
            build_chart(0, {2:0}),  # Lagna Aries, Mars in Aries (kendra 1st)
            build_chart(0, {2:5})   # Mars in Virgo (not allowed sign)
        ),
        (
            "Bhadra", yoga.bhadra_yoga_from_planet_positions,
            build_chart(2, {3:2}),  # Lagna Gemini, Mercury in Gemini
            build_chart(2, {3:4})   # Mercury in Leo (not Gemini/Virgo)
        ),
        (
            "Hamsa", yoga.hamsa_yoga_from_planet_positions,
            build_chart(8, {4:8}),  # Lagna Sagittarius, Jupiter in Sagittarius
            build_chart(8, {4:7})   # Jupiter in Scorpio (not allowed sign)
        ),
        (
            "Maalavya", yoga.maalavya_yoga_from_planet_positions,
            build_chart(1, {5:1}),  # Lagna Taurus, Venus in Taurus
            build_chart(1, {5:0})   # Venus in Aries
        ),
        (
            "Sasa", yoga.sasa_yoga_from_planet_positions,
            build_chart(9, {6:9}),  # Lagna Capricorn, Saturn in Capricorn
            build_chart(9, {6:8})   # Saturn in Sagittarius
        ),
    ]
)
def test_panch_mahapurusha(name, func, chart_true, chart_false):
    assert func(chart_true) is True, f"{name} yoga should be True for triggering chart"
    assert func(chart_false) is False, f"{name} yoga should be False for non-triggering chart"
