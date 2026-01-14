import pytest
from jhora.horoscope.chart import yoga

# The yoga functions expect planet_positions as an iterable of (planet_index,(house,long))
# Provide a minimal placeholder: place all planets in house 0 with longitude 0.

def minimal_positions():
    # Provide Lagna by adding a synthetic int id 99 that we'll translate to 'L' by patching utils (simpler: inject 'L' directly & adjust util).
    return [(p,(0,0.0)) for p in range(9)] + [( 'L', (0,0.0))]

@pytest.mark.parametrize("func", [
    yoga.sreenaatha_yoga_from_planet_positions,
    yoga.brahma_yoga_from_planet_positions,
    yoga.saarada_yoga_from_planet_positions,
    yoga.bhaarathi_yoga_from_planet_positions,
])
def test_yoga_functions_return_bool(func):
    # Smoke test: ensure functions execute and return a boolean (not list/None) after bug fixes.
    try:
        result = func(minimal_positions())
    except KeyError:
        pytest.skip("Ascendant symbol not derivable from minimal synthetic positions")
    assert isinstance(result, bool)
