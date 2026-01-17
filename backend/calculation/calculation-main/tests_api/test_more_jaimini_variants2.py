import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

@pytest.fixture(scope="module")
def request_id():
    # Create a basic horoscope first
    payload = {
        "birthDateTime": "1990-01-01T06:30:00",
        "location": {"place": "Chennai", "tzOffset": 5.5, "latitude": 13.0827, "longitude": 80.2707},
    }
    r = client.post('/api/horoscope', json=payload)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

@pytest.mark.parametrize('endpoint,params', [
    ('/api/dhasa/navamsa', {"include_antardhasa": True}),
    ('/api/dhasa/trikona', {"include_antardhasa": True}),
    ('/api/dhasa/chakra', {"include_antardhasa": False}),
    ('/api/dhasa/kendraadhi_rasi', {"include_antardhasa": True}),
])
def test_new_jaimini_variants(request_id, endpoint, params):
    params = { **params, 'request_id': request_id }
    r = client.get(endpoint, params=params)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['requestId'] == request_id
    assert data['periods'], 'Periods should not be empty'
    # Check first period structure
    first = data['periods'][0]
    assert 'dhasaRasi' in first
    assert 'start' in first
    if params.get('include_antardhasa'):
        # when antardhasa included we may or may not have bhuktiRasi depending on parser outcome
        pass
