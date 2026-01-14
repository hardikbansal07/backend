from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def _make_request():
    body = {
        "birthDateTime": "1992-03-05T14:20:00",
        "location": {"place": "Mumbai,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_vimsottari_depth3():
    rid = _make_request()
    r = client.get(f'/api/dhasa/vimsottari?request_id={rid}&limit=3&depth=3')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['returned'] <= 3
    for p in data['periods']:
        # pratyantardasha should be present (may be None if expansion failed)
        assert 'pratyantardashaLord' in p

def test_vimsottari_depth5():
    rid = _make_request()
    r = client.get(f'/api/dhasa/vimsottari?request_id={rid}&limit=2&depth=5')
    assert r.status_code == 200, r.text
    data = r.json()
    for p in data['periods']:
        # Ensure sookshma and prana keys present
        assert 'sookshmaLord' in p and 'pranaLord' in p
