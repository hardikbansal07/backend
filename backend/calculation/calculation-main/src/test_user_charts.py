import sys
import os
from datetime import datetime

# Add local path
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import swisseph as _swe
_swe.set_ephe_path(os.path.join(src_dir, 'jhora', 'data', 'ephe'))

from api.models import HoroscopeRequest, LocationIn
from api.service import compute_horoscope

def test_user_charts():
    # Boy: hardik, 7 March 2001, 16:20:00, Delhi, 77E13, 28N40, 5.5
    boy_req = HoroscopeRequest(
        birthDateTime=datetime(2001, 3, 7, 16, 20, 0),
        location=LocationIn(
            place="Delhi",
            latitude=28.6667, # 28N40
            longitude=77.2167, # 77E13
            tzOffset=5.5
        ),
        ayanamsaMode="TRUE_CITRA",
        calcType="drik"
    )
    
    # Girl: d, 20 August 1998, 1:30:00, Indri, 77E4, 29N52, 5.5
    girl_req = HoroscopeRequest(
        birthDateTime=datetime(1998, 8, 20, 1, 30, 0),
        location=LocationIn(
            place="Indri",
            latitude=29.8667, # 29N52
            longitude=77.0667, # 77E4
            tzOffset=5.5
        ),
        ayanamsaMode="TRUE_CITRA",
        calcType="drik"
    )
    
    boy_res = compute_horoscope(boy_req)
    girl_res = compute_horoscope(girl_req)
    
    print("=== BOY (hardik) ===")
    boy_planets = boy_res.response.rasiChart.planets
    boy_moon = next(p for p in boy_planets if p.name.lower() == 'moon')
    print(f"Moon Nakshatra: {boy_moon.nakshatra}")
    print(f"Moon Pada: {boy_moon.nakshatraPada}")
    print(f"Moon Sign (Rasi): {boy_moon.sign}")
    
    print("\n=== GIRL (d) ===")
    girl_planets = girl_res.response.rasiChart.planets
    girl_moon = next(p for p in girl_planets if p.name.lower() == 'moon')
    print(f"Moon Nakshatra: {girl_moon.nakshatra}")
    print(f"Moon Pada: {girl_moon.nakshatraPada}")
    print(f"Moon Sign (Rasi): {girl_moon.sign}")

if __name__ == "__main__":
    test_user_charts()
