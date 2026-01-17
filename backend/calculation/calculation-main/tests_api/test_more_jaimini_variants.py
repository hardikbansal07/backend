from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def make_request():
    body = {"birthDateTime":"1990-01-01T10:00:00","location":{"tzOffset":5.5,"latitude":19.076,"longitude":72.8777,"place":"Mumbai"}}
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']


def test_brahma_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/brahma?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json(); assert data['system'].startswith('brahma'); assert data['periods']

def test_mandooka_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/mandooka?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json(); assert data['system'].startswith('mandooka'); assert data['periods']

def test_sudasa_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/sudasa?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json(); assert data['system'].startswith('sudasa'); assert data['periods']

def test_kalachakra_dasha():
    rid = make_request()
    r = client.get(f'/api/dhasa/kalachakra?request_id={rid}&limit=30')
    assert r.status_code == 200, r.text
    data = r.json(); assert data['system'].startswith('kalachakra'); assert data['periods']
