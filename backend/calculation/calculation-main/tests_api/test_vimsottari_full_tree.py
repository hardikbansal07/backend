from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def _rid():
    body = {
        "birthDateTime": "1985-11-23T03:45:00",
        "location": {"place": "Delhi,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200
    return r.json()['meta']['requestId']

def test_full_tree_basic():
    rid = _rid()
    r = client.get(f'/api/dhasa/vimsottari?request_id={rid}&limit=2&depth=4&full_tree=true&max_nodes=200')
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'allChains' in data and isinstance(data['allChains'], list)
    # Each chain path length should be >= depth requested (maha, antar, praty, sookshma)
    if data['allChains']:
        assert all(len(path) >= 4 for path in data['allChains'])
    if data.get('allChainsTruncated'):
        # if truncated, the size should hit the limit boundary roughly
        assert len(data['allChains']) <= 200
