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

def test_flat_endpoint_has_no_lagna_row():
    rid = create_request()
    rv = client.get(f'/api/horoscope/sslike/flat?request_id={rid}&factor=1')
    assert rv.status_code == 200, rv.text
    data = rv.json()
    rows = data.get('rows') or []
    assert rows, 'rows empty'
    assert not any(r.get('body','').lower().startswith('lagna') for r in rows), 'Lagna row should be removed'
    # Ascendant synthetic planet should still appear in rows (body contains Ascendant or normalized name)
    assert any('ascendant' in (r.get('body','').lower()) for r in rows), 'Ascendant not present'
