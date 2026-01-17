from api import service
from api import models
from jhora.panchanga import drik
import pprint

req = models.HoroscopeRequest(
    birthDateTime='1990-01-01T06:30:00',
    location=models.LocationIn(place='Chennai,IN', latitude=13.0827, longitude=80.2707, tzOffset=5.5),
    calcType='drik'
)
stored = service.compute_horoscope(req)
h = stored.internalHoroscope
try:
    bt_tuple = tuple(int(x) for x in h.birth_time)
except Exception:
    bt_tuple = (getattr(h,'birth_hour',0), getattr(h,'birth_minute',0), getattr(h,'birth_second',0))
dob = drik.Date(h.Date.year, h.Date.month, h.Date.day)

# Request include_antardhasa True to get nested chains
raw_res = h._get_vimsottari_dhasa_bhukthi(dob, bt_tuple, h.Place, include_antardhasa=True)

print('raw_res type:', type(raw_res))
try:
    # If function returned (balance, periods) tuple
    if isinstance(raw_res, (list, tuple)) and len(raw_res)==2 and isinstance(raw_res[1], (list,tuple)):
        periods_raw = list(raw_res[1])
    else:
        periods_raw = list(raw_res)
except Exception as e:
    print('failed to normalize raw_res:', e)
    periods_raw = []

print('first 20 raw items (repr):')
for i, it in enumerate(periods_raw[:20]):
    print(i, '->', repr(it))

print('\nSample items pretty printed:')
pprint.pprint(periods_raw[:20])
