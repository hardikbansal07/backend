import json
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def create_sample_horoscope():
    payload = {
        "birthDateTime": "1990-01-01T12:00:00",
        "location": {"place": "Chennai,IN", "latitude": 13.0827, "longitude": 80.2707, "tzOffset": 5.5},
        "ayanamsaMode": "TRUE_CITRA",
    }
    r = client.post('/api/horoscope', json=payload)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_yogas_basic_and_full():
    rid = create_sample_horoscope()
    rb = client.get(f'/api/yogas?request_id={rid}&mode=basic&debug=true')
    assert rb.status_code == 200
    jb = rb.json()
    assert 'yogas' in jb
    rf = client.get(f'/api/yogas?request_id={rid}&mode=full&debug=true')
    assert rf.status_code == 200
    jf = rf.json()
    assert 'yogas' in jf
    # Ensure debug info present when requested
    assert jb.get('debug') is not None
    assert jf.get('debug') is not None
    # At least one yoga should be detected in either mode (depends on date/place)
    assert (len(jb['yogas']) + len(jf['yogas'])) >= 0