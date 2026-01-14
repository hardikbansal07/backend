from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def create_request():
    body = {
        "birthDateTime": "2000-01-01T06:30:00",
        "location": {"place": "Chennai,IN", "tzOffset": 5.5},
        "language": "en",
        "divisionalFactors": [1,9]
    }
    r = client.post('/api/horoscope', json=body)
    assert r.status_code == 200, r.text
    return r.json()['meta']['requestId']

def test_flags_and_strength_summary_flow():
    rid = create_request()
    # flags
    rf = client.get(f'/api/flags/planets?request_id={rid}')
    assert rf.status_code == 200
    # summary
    rs = client.get(f'/api/summary?request_id={rid}')
    assert rs.status_code == 200
    data = rs.json()
    assert data['requestId'] == rid
    # strength
    rstr = client.get(f'/api/strength?request_id={rid}')
    assert rstr.status_code == 200
    # yogas
    ry = client.get(f'/api/yogas?request_id={rid}')
    assert ry.status_code == 200

def test_vimsottari_endpoint_basic():
    rid = create_request()
    rv = client.get(f'/api/dhasa/vimsottari?request_id={rid}&limit=15&include_antardhasa=true')
    assert rv.status_code == 200
    data = rv.json()
    assert data['requestId'] == rid
    assert data['returned'] <= 15

def test_all_rasi_dashas_minimal():
    rid = create_request()
    systems_with_system_field = [
        'sthira','narayana','drig','yogardha','paryaaya','brahma','mandooka','sudasa','kalachakra','navamsa','trikona','chakra','kendraadhi_rasi'
    ]
    chara_endpoint = 'chara'
    # Chara has a distinct response model (CharaDhasaResponse) without 'system'
    r_chara = client.get(f'/api/dhasa/{chara_endpoint}?request_id={rid}&limit=5')
    assert r_chara.status_code == 200
    jc = r_chara.json()
    assert 'method' in jc and jc['returned'] <= 5
    for s in systems_with_system_field:
        r = client.get(f'/api/dhasa/{s}?request_id={rid}&limit=5')
        assert r.status_code == 200, f"{s} failed: {r.text}"
        js = r.json()
        assert js.get('system') == s
        assert js['returned'] <= 5

def test_remaining_graha_dashas():
    rid = create_request()
    graha = ['tithi_ashtottari','tithi_yogini','shodasottari','dwadasottari','panchottari']
    for g in graha:
        r = client.get(f'/api/dhasa/{g}?request_id={rid}&limit=3')
        assert r.status_code == 200, f"{g} failed: {r.text}"
        js = r.json()
        assert js['system'] == g
        assert js['returned'] <= 3

def test_transit_and_panchanga():
    rid = create_request()
    rt = client.get(f'/api/transit?request_id={rid}')
    assert rt.status_code == 200
    rp = client.get(f'/api/panchanga?request_id={rid}')
    assert rp.status_code == 200

def test_bundle_export_minimal():
    rid = create_request()
    rb = client.get(f'/api/bundle?request_id={rid}')
    assert rb.status_code == 200
    rtxt = client.get(f'/api/export/text/{rid}')
    assert rtxt.status_code == 200