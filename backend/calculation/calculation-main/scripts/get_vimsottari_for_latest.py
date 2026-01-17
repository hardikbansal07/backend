"""List stored requests and print the API-style Vimsottari JSON for the most recent request.
Run: python scripts/get_vimsottari_for_latest.py
"""
import json
from api import service
from api import models
from jhora.panchanga import drik
from jhora import utils

def build_api_vimsottari_response(request_id, h):
    # Build dob/tob/place similar to API handler
    dob = drik.Date(h.Date.year, h.Date.month, h.Date.day)
    try:
        bt_tuple = tuple(int(x) for x in h.birth_time)
    except Exception:
        bt_tuple = (getattr(h,'birth_hour',0), getattr(h,'birth_minute',0), getattr(h,'birth_second',0))
    place = h.Place
    # Call helper
    get_vim = getattr(h, '_get_vimsottari_dhasa_bhukthi', None)
    if not callable(get_vim):
        raise RuntimeError('Horoscope missing _get_vimsottari_dhasa_bhukthi')
    raw_res = get_vim(dob, bt_tuple, place)
    # Normalize
    if isinstance(raw_res, (list, tuple)) and len(raw_res)==2 and isinstance(raw_res[1], (list, tuple)):
        balance, periods_raw = raw_res
    else:
        periods_raw = list(raw_res)
        balance = getattr(h, '_vimsottari_balance', [])
    periods = []
    for lord_pair, start in periods_raw:
        if '-' in lord_pair:
            d_l, b_l = lord_pair.split('-',1)
        else:
            d_l, b_l = lord_pair, ''
        periods.append({'dhasaLord': d_l, 'bhuktiLord': b_l, 'start': str(start)})
    resp = {
        'requestId': request_id,
        'balance': list(balance) if isinstance(balance,(list,tuple)) else [],
        'periods': periods,
        'total': len(periods_raw),
        'returned': len(periods)
    }
    return resp

# List stored requests
items = service.list_requests(limit=20)
if not items:
    print('No stored requests. Create one via POST /api/horoscope or run scripts/compare_vimsottari_api_vs_lib.py to create one.')
else:
    print('Stored requests (most recent first):')
    for i,it in enumerate(items[:10]):
        print(i+1, it['requestId'], 'generatedAt=', it.get('generatedAt'))
    # Use the first item
    rid = items[0]['requestId']
    print('\nUsing request_id:', rid)
    stored = service.get_stored(rid)
    if not stored:
        print('Failed to load stored horoscope for', rid)
    else:
        h = stored.internalHoroscope
        resp = build_api_vimsottari_response(rid, h)
        print('\nVimsottari API-style JSON:')
        print(json.dumps(resp, indent=2, ensure_ascii=False))
