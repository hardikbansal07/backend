import pytest, httpx, os, json
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def create_sample():
    body = {
        "birthDateTime": "1990-01-01T10:00:00",
        "location": {"tzOffset":5.5, "latitude":19.076, "longitude":72.8777, "place":"Mumbai"},
        "divisionalFactors": [9],
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_chara_dhasa_basic():
    rid = create_sample()
    r = client.get(f'/api/dhasa/chara?request_id={rid}&limit=20&include_antardhasa=true&method=1')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['requestId'] == rid
    assert data['returned'] <= data['total']
    assert data['periods'], 'Expected at least one chara dasha period'
    # Each period must have dhasaRasi and start
    for p in data['periods'][:5]:
        assert 'dhasaRasi' in p and 'start' in p

