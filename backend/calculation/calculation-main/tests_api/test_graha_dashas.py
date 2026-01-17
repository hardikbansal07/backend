from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def _make_request():
    body = {
        "birthDateTime": "1990-06-15T12:15:00",
        "location": {"place": "Delhi,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_ashtottari_endpoint():
    rid = _make_request()
    r = client.get(f'/api/dhasa/ashtottari?request_id={rid}&limit=10')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['system'] == 'ashtottari'
    assert 'periods' in data

def test_yogini_endpoint():
    rid = _make_request()
    r = client.get(f'/api/dhasa/yogini?request_id={rid}&limit=5')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['system'] == 'yogini'
    assert 'periods' in data

def test_dwisatpathi_endpoint():
    rid = _make_request()
    r = client.get(f'/api/dhasa/dwisatpathi?request_id={rid}&limit=5')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['system'] == 'dwisatpathi'
    assert 'periods' in data