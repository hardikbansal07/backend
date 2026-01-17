from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def make_request():
    body = {"birthDateTime":"1990-01-01T10:00:00","location":{"tzOffset":5.5,"latitude":19.076,"longitude":72.8777,"place":"Mumbai"}}
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']


def test_yogardha_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/yogardha?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['system'].startswith('yogardha')
    assert data['periods']


def test_paryaaya_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/paryaaya?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['system'].startswith('paryaaya')
    assert data['periods']
