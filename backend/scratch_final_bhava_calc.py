import os
import sys
import asyncio
from datetime import datetime

sys.path.append(r"c:\Users\acer\backend folder\backend")
sys.path.insert(0, r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src")
os.environ["MONGO_URI"] = "mongodb+srv://Astrocare7:Astrocare7337@cluster0.ydviwil.mongodb.net/"
os.environ["DB_NAME"] = "Astrocare7"
os.environ["SE_EPHE_PATH"] = r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src\jhora\data\ephe"

import swisseph as swe
swe.set_ephe_path(os.environ["SE_EPHE_PATH"])

from api.models import HoroscopeRequest, LocationIn
from api.service import compute_horoscope
from jhora.horoscope.chart import strength as _strength
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora import const
from jhora import utils

# Proposed _bhava_dig_bala
def proposed_bhava_dig_bala(jd, place, ayanamsa_mode=const._DEFAULT_AYANAMSA_MODE):
    pp = charts.rasi_chart(jd, place, ayanamsa_mode=ayanamsa_mode)
    asc_long = pp[0][1][0]*30 + pp[0][1][1]
    bm = [(asc_long + h*30)%360 for h in range(12)]
    
    brl = {0:const.nara_rasi_longitudes,3:const.jalachara_rasi_longitudes,9:const.chatushpada_rasis,6:const.keeta_rasis}
    chk = []
    for k, v in brl.items():
        chk += list(set([((k+h)%12, abs(60-abs(h)*10)) for h in range(-7,7) for l1,l2 in v if bm[(k+h)%12] >= l1 and bm[(k+h)%12] <= l2]))
    chk = {k:v for k,v in chk}
    return [dict(sorted(chk.items())).get(h, 0.0) for h in range(12)]

# Proposed _bhava_drik_bala
def proposed_bhava_drik_bala(jd, place, ayanamsa_mode=const._DEFAULT_AYANAMSA_MODE):
    dk = [[ 0 for _ in range(7)] for _ in range(12)]
    pp = charts.rasi_chart(jd, place, ayanamsa_mode=ayanamsa_mode)
    asc_long = pp[0][1][0]*30 + pp[0][1][1]
    pp = pp[1:-2]
    subha_grahas = [1,3,4,5] ; asubha_grahas = [0,2,6]
    
    bm = [(asc_long + h*30)%360 for h in range(12)]
    
    for h in range(12): # Aspected House
        h_mid = bm[h]
        for p in range(7): # Aspecting Planet
            p_long = pp[p][1][0]*30+pp[p][1][1]
            dk_h_p = round((360.0+h_mid-p_long)%360,2)
            dk_h_p = _strength.__bhava_drik_bala_calc_1(dk_h_p,p)
            dk[h][p] = round(dk_h_p,2)
            
    dkp = [0 for _ in range(12)] ; dkm = [0 for _ in range(12)]; dk_final = [0 for _ in range(12)]
    for row in range(12):
        for col in range(7):
            if col in subha_grahas:
                dkp[row] += dk[row][col] 
            if col in asubha_grahas:  # Corrected bug
                dkm[row] += dk[row][col]
        # Not dividing by 4 at the end
        dk_final[row] = round(dkp[row] - dkm[row],2) 
    return dk_final

async def test_run():
    loc = LocationIn(
        place="Delhi, India",
        latitude=28.6328027,
        longitude=77.2197713,
        tzOffset=5.5
    )
    birth_dt = datetime.fromisoformat("2001-03-07T16:20:00")
    req_obj = HoroscopeRequest(
        birthDateTime=birth_dt,
        location=loc,
        language="en",
        name="hardik",
        ayanamsaMode="LAHIRI"
    )
    stored = compute_horoscope(req_obj)
    h = stored.internalHoroscope
    jd = h.julian_day
    place = h.Place
    
    # 1. Lord's Bala
    bab = _strength._bhava_adhipathi_bala(jd, place)
    
    # 2. Dig Bala
    bdb = proposed_bhava_dig_bala(jd, place)
    
    # 3. Drig Bala
    bdrb = proposed_bhava_drik_bala(jd, place)
    
    # Expected from JHora table:
    expected_bhava_bala = [563.91, 508.98, 574.29, 529.46, 388.19, 497.54, 455.59, 410.70, 454.70, 396.58, 507.28, 510.16]
    expected_dig_bala = [30.00, 20.00, 40.00, 30.00, 40.00, 20.00, 30.00, 10.00, 10.00, 60.00, 50.00, 50.00]
    expected_drig_bala = [78.15, 75.09, 63.70, 50.01, 49.67, 50.17, 27.64, 2.76, 17.33, 38.07, 7.83, -10.42]
    expected_lords_bala = [455.75, 413.89, 470.59, 449.45, 298.51, 427.37, 397.95, 397.95, 427.37, 298.51, 449.45, 470.59]
    
    print("\nPlanet Shadbalas used as Lord's Bala in our proposed engine:")
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    sb_sum = _strength.shad_bala(jd, place)[6]
    for idx, p in enumerate(planet_names):
        print(f"  {p}: {sb_sum[idx]:.2f} (JHora Expected: {expected_lords_bala[[1, 0, 4, 2, 5, 3, 6][idx]]:.2f})")
        
    print("\n=== FINAL VERIFICATION OF PROPOSED BHAVA BALA ===")
    print("House | Lord's Bala (Calc vs JHora) | Dig Bala (Calc vs JHora) | Drig Bala (Calc vs JHora) | Total Bhava Bala (Calc vs JHora)")
    print("-" * 115)
    for h_idx in range(12):
        tot = bab[h_idx] + bdb[h_idx] + bdrb[h_idx]
        print(f"House {h_idx+1:2d} | "
              f"{bab[h_idx]:6.2f} vs {expected_lords_bala[h_idx]:6.2f} | "
              f"{bdb[h_idx]:6.2f} vs {expected_dig_bala[h_idx]:6.2f} | "
              f"{bdrb[h_idx]:6.2f} vs {expected_drig_bala[h_idx]:6.2f} | "
              f"{tot:6.2f} vs {expected_bhava_bala[h_idx]:6.2f}")
              
asyncio.run(test_run())
