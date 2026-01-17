import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def create_request():
    body = {
        "birthDateTime": "2000-01-01T06:30:00",
        "location": {"place": "Chennai,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']


def test_sslike_view_has_ascendant_and_filters_lagna_planet():
    rid = create_request()
    rv = client.get(f'/api/horoscope/sslike/view?request_id={rid}')
    assert rv.status_code == 200, rv.text
    data = rv.json()
    # Ascendant metadata top-level
    assert data.get('ascendantLongitudeDMS'), 'Missing ascendantLongitudeDMS'
    assert data.get('ascendantRawLongitudeDeg') is not None, 'Missing ascendantRawLongitudeDeg'
    assert data.get('ascendantAbsoluteLongitude') is not None, 'Missing ascendantAbsoluteLongitude'
    assert data.get('ascendantNakshatra'), 'Missing ascendantNakshatra'
    assert data.get('ascendantNakshatraPada') is not None, 'Missing ascendantNakshatraPada'
    # Planet list includes synthetic Ascendant and excludes raw Lagna planet
    planets = data.get('planets', [])
    assert any('Ascendant' in (p.get('name') or '') for p in planets), 'Ascendant synthetic planet row absent'
    assert not any((p.get('name') or '').lower().startswith('lagna') for p in planets), 'Raw Lagna planet should be filtered out'
    first_planet = planets[0]
    assert 'Ascendant' in first_planet['name'], 'Ascendant row not first after Lagna filter'
    # Panel rows: ensure no separate Lagna row present (removed duplicate per user request)
    panel_rows = data.get('panelRows') or []
    assert panel_rows, 'panelRows empty'
    assert not any(r.get('body','').lower().startswith('lagna') for r in panel_rows), 'Lagna row should be removed from panelRows'
