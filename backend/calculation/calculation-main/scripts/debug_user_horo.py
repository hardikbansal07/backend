from datetime import datetime
from src.api import service, models

# Build request for 7 March 2001 16:20 in Delhi (tz +5.5)
req_payload = {
    'birthDateTime': '2001-03-07T16:20:00',
    'location': { 'place': 'Delhi,IN', 'latitude': 28.6139, 'longitude': 77.2090, 'tzOffset': 5.5 },
    'ayanamsaMode': 'TRUE_CITRA',
    'calcType': 'drik',
    'compact': False,
    'divisionalFactors': [1,9]
}
req = models.HoroscopeRequest.model_validate(req_payload)
stored = service.compute_horoscope(req)
resp = stored.response
print('RequestId:', resp.meta.get('requestId'))
print('Combustion list (D1):', resp.combustion)
print('Vargottama list:', resp.vargottama)
print('\nPer-planet D1 flags:')
for p in resp.rasiChart.planets:
    print(f"{p.name:12} abs={p.absoluteLongitude} raw={p.rawLongitudeDeg} retro={p.retrograde} isCombust={p.isCombust}")

# If you want debug per-planet numeric details, call the debug endpoint function in app
try:
    from src.api import app as api_app
    rid = resp.meta.get('requestId')
    if isinstance(rid,str):
        dbg = api_app.debug_combustion(rid)
    else:
        dbg = {'error':'missing requestId'}
    print('\nDebug combustion endpoint result:')
    import json
    print(json.dumps(dbg, indent=2))
except Exception as e:
    print('\nFailed to call debug endpoint function directly:', e)
