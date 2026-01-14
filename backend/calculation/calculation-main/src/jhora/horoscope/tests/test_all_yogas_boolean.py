import inspect
import pytest
from jhora.horoscope.chart import yoga

# Provide a spread planet_positions so not all planets in same house.
# planet index p placed in house p (0-8) with dummy longitude 0.0; add Lagna 'L' at house 0.
PLANET_POSITIONS = [(p, (p % 12, 0.0)) for p in range(9)] + [('L', (0, 0.0))]

# Some yoga functions expect optional global navamsa mapping; ensure it's present (empty ok).
if not hasattr(yoga, 'p_to_h_navamsa'):
    yoga.p_to_h_navamsa = {}

# Collect all yoga detection functions in yoga.py following naming convention.
yoga_funcs = []
for name, obj in inspect.getmembers(yoga, inspect.isfunction):
    if name.endswith('_yoga_from_planet_positions'):
        yoga_funcs.append(obj)

# Sort for deterministic order
yoga_funcs = sorted(yoga_funcs, key=lambda f: f.__name__)

@pytest.mark.parametrize('func', yoga_funcs, ids=lambda f: f.__name__)
def test_yoga_function_returns_bool(func):
    """Each yoga function should return a boolean (True/False) and not raise exceptions with generic input."""
    try:
        result = func(PLANET_POSITIONS)
    except Exception as e:
        pytest.fail(f"{func.__name__} raised exception: {e}")
    assert isinstance(result, bool), f"{func.__name__} returned non-bool type {type(result)} value={result}"
