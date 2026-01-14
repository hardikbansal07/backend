from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def make_request():
    body = {"birthDateTime":"1990-01-01T10:00:00","location":{"tzOffset":5.5,"latitude":19.076,"longitude":72.8777,"place":"Mumbai"}}
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_sthira_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/sthira?request_id={rid}&limit=30')
    assert r.status_code == 200
    data = r.json()
    assert data['system'].startswith('sthira')
    assert data['periods']


def test_narayana_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/narayana?request_id={rid}&limit=30')
    assert r.status_code == 200
    data = r.json()
    assert data['system'].startswith('narayana')
    assert data['periods']


def test_drig_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/drig?request_id={rid}&limit=30')
    assert r.status_code == 200
    data = r.json()
    assert data['system']=='drig'
    assert data['periods']
