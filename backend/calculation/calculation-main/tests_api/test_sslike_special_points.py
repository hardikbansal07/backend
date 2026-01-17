import sys, pathlib, pytest
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def _create_request():
    body = {
        "birthDateTime": "1990-01-01T12:00:00",
        "location": {"place": "Delhi,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_special_points_structured():
    rid = _create_request()
    resp = client.get(f"/api/horoscope/sslike/view?request_id={rid}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Validate new structured arrays exist
    assert "specialLagnaRows" in data, "specialLagnaRows missing from response"
    assert "sphutaRows" in data, "sphutaRows missing from response"
    # If present, rows should have expected keys
    for arr_name in ("specialLagnaRows","sphutaRows"):
        for row in data.get(arr_name) or []:
            for k in ("body","longitude","rasi","longitudeDMS"):
                assert k in row
            if row.get("nakshatra"):
                assert row.get("pada") in (1,2,3,4)
            if row.get("signNumber"):
                assert 1 <= row["signNumber"] <= 12
            if row.get("rawDegreesInSign") is not None:
                assert 0 <= row["rawDegreesInSign"] < 30
