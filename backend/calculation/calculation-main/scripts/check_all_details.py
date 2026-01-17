from api import service
from api import models
from jhora.panchanga import drik
import json

def check_for_request(req):
    stored = service.compute_horoscope(req)
    rid = stored.response.meta.get('requestId')
    resp = stored.response
    print('\n==== RequestId:', rid, 'calcType=', req.calcType)
    # Check divisional charts presence
    factors = {c.factor: c for c in resp.divisionalCharts}
    need = [1,36,72,144]
    for f in need:
        if f in factors:
            print(f'  D{f}: PRESENT')
        else:
            print(f'  D{f}: MISSING')
    # For each of the needed charts, check planets have longitudeDMS and rawLongitudeDeg
    for f in need:
        ch = factors.get(f)
        if not ch:
            continue
        ok_planet = False
        for p in ch.planets:
            if getattr(p,'longitudeDMS',None) and getattr(p,'rawLongitudeDeg',0):
                ok_planet = True
                break
        print(f'  D{f} planets have longitude fields: {"OK" if ok_planet else "MISSING"} (planet count={len(ch.planets)})')
    # Check D1 special lagna and sphuta
    d1 = factors.get(1)
    if d1:
        sl = d1.specialLagna
        sph = d1.sphuta
        sl_present = any(getattr(sl,attr) for attr in sl.__fields__.keys())
        sph_present = bool(sph)
        print('  D1 specialLagna present:', sl_present)
        print('  D1 sphuta present:', sph_present, 'keys=', list(sph.keys())[:10])
    # Check rasiChart planets (rasiChart is resp.rasiChart)
    rasi = resp.rasiChart
    rasi_ok = False
    for p in rasi.planets:
        if getattr(p,'longitudeDMS',None) and getattr(p,'rawLongitudeDeg',0):
            rasi_ok = True
            break
    print('  Rasi chart planets have longitude fields:', rasi_ok, 'count=', len(rasi.planets))
    # Check Vimsottari via horoscope helper
    h = stored.internalHoroscope
    dob = drik.Date(h.Date.year,h.Date.month,h.Date.day)
    try:
        bt = tuple(int(x) for x in h.birth_time)
    except Exception:
        bt = (getattr(h,'birth_hour',0),getattr(h,'birth_minute',0),getattr(h,'birth_second',0))
    raw = h._get_vimsottari_dhasa_bhukthi(dob,bt,h.Place)
    # Normalize
    periods_raw = []
    bal = getattr(h,'_vimsottari_balance', [])
    if isinstance(raw,(list,tuple)) and len(raw)==2 and isinstance(raw[1],(list,tuple)):
        bal_candidate, per = raw
        periods_raw = list(per)
        if not bal and bal_candidate:
            bal = bal_candidate
    else:
        try:
            periods_raw = list(raw)
        except Exception:
            periods_raw = []
    print('  Vimsottari periods count via helper:', len(periods_raw), 'balance=', bal)
    # quick sample
    if periods_raw:
        print('   sample periods (first 4):')
        for item in periods_raw[:4]:
            print('    ', item)
    return stored

if __name__ == '__main__':
    # sample request (same used previously)
    req1 = models.HoroscopeRequest(birthDateTime='1990-01-01T06:30:00', location=models.LocationIn(place='Chennai,IN', latitude=13.0827, longitude=80.2707, tzOffset=5.5), calcType='drik')
    req2 = models.HoroscopeRequest(birthDateTime='1990-01-01T06:30:00', location=models.LocationIn(place='Chennai,IN', latitude=13.0827, longitude=80.2707, tzOffset=5.5), calcType='ss')
    s1 = check_for_request(req1)
    s2 = check_for_request(req2)
    print('\nDone checks.')
