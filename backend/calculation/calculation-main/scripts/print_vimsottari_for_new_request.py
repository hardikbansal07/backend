from api import service
from api import models
from jhora.panchanga import drik
import json

req = models.HoroscopeRequest(
    birthDateTime='1990-01-01T06:30:00',
    location=models.LocationIn(place='Chennai,IN', latitude=13.0827, longitude=80.2707, tzOffset=5.5),
    calcType='drik'
)
stored = service.compute_horoscope(req)
request_id = stored.response.meta.get('requestId')
print('request_id:', request_id)
# emulate handler normalization
h = stored.internalHoroscope
try:
    bt_tuple = tuple(int(x) for x in h.birth_time)
except Exception:
    bt_tuple = (getattr(h,'birth_hour',0), getattr(h,'birth_minute',0), getattr(h,'birth_second',0))
from jhora.panchanga import drik
dob = drik.Date(h.Date.year, h.Date.month, h.Date.day)
raw_res = h._get_vimsottari_dhasa_bhukthi(dob, bt_tuple, h.Place)
periods_raw = []
balance = getattr(h,'_vimsottari_balance', [])
if isinstance(raw_res,(list,tuple)) and len(raw_res)==2 and isinstance(raw_res[1],(list,tuple)):
    _balance_candidate, _periods = raw_res
    periods_raw = list(_periods)
    if not balance and _balance_candidate:
        balance = _balance_candidate
else:
    periods_raw = list(raw_res)

periods = []
for lord_pair, start in periods_raw[:200]:
    if '-' in lord_pair:
        d_l, b_l = lord_pair.split('-',1)
    else:
        d_l, b_l = lord_pair, ''
    periods.append({'dhasaLord': d_l, 'bhuktiLord': b_l, 'start': str(start)})

out = {'requestId': request_id, 'balance': list(balance) if isinstance(balance,(list,tuple)) else [], 'periods': periods, 'total': len(periods_raw), 'returned': len(periods)}
print(json.dumps(out, indent=2))
