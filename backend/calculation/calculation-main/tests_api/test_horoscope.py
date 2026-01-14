from fastapi.testclient import TestClient
from api.app import app
import datetime

client = TestClient(app)

def test_horoscope_minimal():
    body = {
        "birthDateTime": "2000-01-01T06:30:00",
        "location": {"place": "Chennai,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1],
        "sendToAgent": False
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'meta' in data and 'rasiChart' in data
    assert data['rasiChart']['ascendantHouse'] >= 1
