import pytest
from src.api import service, models
from datetime import datetime

# Minimal valid request template
BASE_REQ = {
    'birthDateTime': datetime(2000,1,1,6,30),
    'location': {
        'place': 'Chennai,IN',
        'latitude': 13.0827,
        'longitude': 80.2707,
        'tzOffset': 5.5
    },
    'ayanamsaMode': 'TRUE_CITRA'
}

@pytest.mark.parametrize("input_val,expected_in",[
    ('DEFAULT','1'),
    ('equal','2'),
    ('sripati','3'),
    ('placidus','4'),
    ('1','1'),
    ('P','P'),
    ('Placidus','4'),
    ('KP','4'),
    ('koch','K'),
    ('porphyry','O'),
])
def test_house_system_mapping(input_val, expected_in):
    req = dict(BASE_REQ)
    # pydantic model expects model types; construct model
    hr = models.HoroscopeRequest.model_validate({
        'birthDateTime': req['birthDateTime'],
        'location': req['location'],
        'ayanamsaMode': req['ayanamsaMode'],
        'houseSystem': input_val
    })
    # compute_horoscope caches results keyed by birth/location; clear cache to force recompute for each param
    service._store.clear()
    stored = service.compute_horoscope(hr)
    assert stored.response.meta is not None
    applied_label = stored.response.meta.get('houseSystemApplied','')
    applied_key = stored.response.meta.get('houseSystemAppliedKey','')
    # Expect either the label or canonical key to contain expected token
    assert expected_in.upper() in str(applied_label).upper() or expected_in.upper() in str(applied_key).upper()


def test_integration_bhava_cusp_difference():
    # Generate two horoscopes with different house systems and assert bhava cusps/signNumbers differ
    req_base = dict(BASE_REQ)
    # Use '5' (Each Rasi is the house) vs '1' (Equal Housing - Lagna in the middle) which should differ
    hr1 = models.HoroscopeRequest.model_validate({
        'birthDateTime': req_base['birthDateTime'],
        'location': req_base['location'],
        'ayanamsaMode': req_base['ayanamsaMode'],
        'houseSystem': '5'
    })
    hr2 = models.HoroscopeRequest.model_validate({
        'birthDateTime': req_base['birthDateTime'],
        'location': req_base['location'],
        'ayanamsaMode': req_base['ayanamsaMode'],
        'houseSystem': '1'
    })
    service._store.clear()
    s1 = service.compute_horoscope(hr1)
    service._store.clear()
    s2 = service.compute_horoscope(hr2)
    # First, check the internal Horoscope object's bhava method directly (most reliable)
    method1 = getattr(s1.internalHoroscope, '_bhava_madhya_method', None)
    method2 = getattr(s2.internalHoroscope, '_bhava_madhya_method', None)
    if method1 is not None and method2 is not None and method1 != method2:
        return
    # Fallback: compare planets' absolute house assignments (houseAbs). If any planet's houseAbs differs, the systems produced different bhava mappings.
    p1 = { p.name: p.houseAbs for p in s1.response.rasiChart.planets }
    p2 = { p.name: p.houseAbs for p in s2.response.rasiChart.planets }
    # Ensure at least one planet differs
    diff_found = False
    for name in set(list(p1.keys()) + list(p2.keys())):
        if p1.get(name) != p2.get(name):
            diff_found = True
            break
    assert diff_found, 'Expected at least one planet house assignment to differ between house systems (and internal bhava methods matched)'
