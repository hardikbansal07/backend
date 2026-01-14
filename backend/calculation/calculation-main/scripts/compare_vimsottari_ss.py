"""Compare Vimsottari outputs when horoscope is computed with calcType='ss' (Surya Siddhanta)
Run: python scripts/compare_vimsottari_ss.py
"""
from jhora.panchanga import drik
from jhora.horoscope.dhasa.graha import vimsottari
from api import service
from jhora import utils
import pprint

# create a horoscope via service.compute_horoscope using a sample request
from api import models as api_models

req = api_models.HoroscopeRequest(
    birthDateTime='1990-01-01T06:30:00',
    location=api_models.LocationIn(place='Chennai,IN', latitude=13.0827, longitude=80.2707, tzOffset=5.5),
    calcType='ss'
)
stored = service.compute_horoscope(req)
request_id = stored.response.meta['requestId']
print('request_id:', request_id)
h = stored.internalHoroscope

# prepare dob,tob,place
from jhora.panchanga import drik

dob = drik.Date(h.Date.year, h.Date.month, h.Date.day)
try:
    bt = tuple(int(x) for x in h.birth_time)
except Exception:
    bt = (0,0,0)
place = h.Place

print('\nLibrary-level call:')
jd = utils.julian_day_number(dob, bt)
lib_balance, lib_periods = vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=True)
print('lib periods count:', len(lib_periods))
print('lib balance:', lib_balance)

print('\nHoroscope helper call:')
helper_res = h._get_vimsottari_dhasa_bhukthi(dob, bt, place)
print('helper raw type:', type(helper_res))
if isinstance(helper_res, (list,tuple)) and len(helper_res)==2 and isinstance(helper_res[1],(list,tuple)):
    helper_balance, helper_periods = helper_res
else:
    helper_balance, helper_periods = getattr(h,'_vimsottari_balance',None), list(helper_res)
print('helper periods count:', len(helper_periods))
print('helper balance:', helper_balance)

# Build normalized API-style periods list
# helper_periods entries may be tuples like ('Mars♂-Mars♂','1984-09-20 00:19:33') or library numeric lists
api_periods = []
for item in helper_periods:
    if isinstance(item, (list,tuple)) and len(item)>=1:
        lord_pair = item[0]
        if isinstance(lord_pair, str) and '-' in lord_pair:
            d_l, b_l = lord_pair.split('-',1)
        elif isinstance(lord_pair, (list,tuple)) and len(lord_pair)>=2:
            d_l = str(lord_pair[0]); b_l = str(lord_pair[1])
        else:
            d_l = str(lord_pair); b_l = ''
        api_periods.append((d_l,b_l))

print('\nNormalized API-style counts:')
print('api_periods count:', len(api_periods))

print('\nSample library first 6:')
pp = pprint.PrettyPrinter(width=120)
pp.pprint(lib_periods[:6])
print('\nSample helper first 6:')
pp.pprint(helper_periods[:6])

# Print a small JSON-like summary for frontend consumption
import json
summary = {
    'requestId': request_id,
    'lib_count': len(lib_periods),
    'helper_count': len(helper_periods),
    'api_count': len(api_periods),
    'lib_balance': lib_balance,
}
print('\nSummary JSON:')
print(json.dumps(summary, indent=2, ensure_ascii=False))

print('\nDone.')
