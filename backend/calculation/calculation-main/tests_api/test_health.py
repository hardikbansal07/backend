import asyncio
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status']=='ok'
