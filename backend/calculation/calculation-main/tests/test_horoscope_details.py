from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def _create_request() -> str:
    payload = {
        "birthDateTime": "1990-01-01T12:00:00",
        "location": {"place": "Chennai,IN", "latitude": 13.0827, "longitude": 80.2707, "tzOffset": 5.5},
        "ayanamsaMode": "TRUE_CITRA",
    }
    resp = client.post('/api/horoscope', json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data['meta']['requestId']


def test_detailed_endpoint_returns_english_payload():
    rid = _create_request()
    resp = client.get(f'/api/horoscope/{rid}/details?language=en')
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data['requestId'] == rid
    assert data['language'] == 'en'
    assert isinstance(data.get('calendar'), dict)
    assert isinstance(data.get('horoscopeInfo'), dict)
    # yogas and raja yogas should be lists even if empty
    assert isinstance(data.get('yogas'), list) or data.get('yogas') is None
    assert isinstance(data.get('rajaYogas'), list) or data.get('rajaYogas') is None
    if isinstance(data.get('yogas'), list):
        assert data.get('yogaCount') == len(data['yogas']) or data.get('yogaCount') is None
    if isinstance(data.get('rajaYogas'), list):
        assert data.get('rajaYogaCount') == len(data['rajaYogas']) or data.get('rajaYogaCount') is None

