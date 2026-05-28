import os
import sys
import itertools
from datetime import datetime

sys.path.append(r"c:\Users\acer\backend folder\backend")
sys.path.insert(0, r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src")
os.environ["SE_EPHE_PATH"] = r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src\jhora\data\ephe"

import swisseph as swe
swe.set_ephe_path(os.environ["SE_EPHE_PATH"])

from jhora.horoscope.chart import strength
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora import const
from jhora import utils

# Hardik birth info
dob = drik.Date(2001, 3, 7)
tob = (16, 20, 0)
place = drik.Place('Delhi', 28.6328027, 77.2197713, 5.5)
jd = utils.julian_day_number(dob, tob)

# Planets positions
pp = charts.rasi_chart(jd, place, ayanamsa_mode="LAHIRI")
asc_long = pp[0][1][0]*30 + pp[0][1][1]
pp_planets = pp[1:-2]

expected_drig = [78.15, 75.09, 63.70, 50.01, 49.67, 50.17, 27.64, 2.76, 17.33, 38.07, 7.83, -10.42]

def test_combination(use_equal_house, remove_guard, div_by_4_inside, div_by_4_outside):
    dk = [[ 0 for _ in range(7)] for _ in range(12)]
    subha_grahas = [1,3,4,5] ; asubha_grahas = [0,2,6]
    
    if use_equal_house:
        bm = [(asc_long + h*30)%360 for h in range(12)]
    else:
        bm = drik.bhaava_madhya(jd, place)
        
    for h in range(12): # Aspected House
        h_mid = bm[h]
        for p in range(7): # Aspecting Planet
            p_long = pp_planets[p][1][0]*30+pp_planets[p][1][1]
            dk_h_p = round((360.0+h_mid-p_long)%360,2)
            # Use raw planet aspect function
            dk_h_p = strength.__drik_bala_calc_1(dk_h_p, p, h)
            
            # Apply inside division factor if not Mercury/Jupiter
            if div_by_4_inside and (p not in [3, 4]):
                dk_h_p = dk_h_p * 0.25
                
            dk[h][p] = dk_h_p
            
    dkp = [0 for _ in range(12)] ; dkm = [0 for _ in range(12)]; dk_final = [0 for _ in range(12)]
    for row in range(12):
        for col in range(7):
            if col in subha_grahas:
                dkp[row] += dk[row][col] 
            if col in asubha_grahas:
                dkm[row] += dk[row][col]
        val = dkp[row] - dkm[row]
        if div_by_4_outside:
            val = val / 4.0
        dk_final[row] = round(val, 2)
    return dk_final

# Let's run grid search over options
options = {
    'use_equal_house': [True, False],
    'remove_guard': [True], # JHora uses no guard
    'div_by_4_inside': [True, False],
    'div_by_4_outside': [True, False]
}

keys = list(options.keys())
combinations = list(itertools.product(*[options[k] for k in keys]))

results = []
for comb in combinations:
    cfg = dict(zip(keys, comb))
    res = test_combination(**cfg)
    err = sum(abs(res[i] - expected_drig[i]) for i in range(12)) / 12.0
    results.append((err, cfg, res))

results.sort()
print("\nSorted by average error (lowest first):")
for err, cfg, res in results:
    print(f"Error: {err:6.2f} | Config: {cfg}")
    print(f"  Calculated: {[round(r, 2) for r in res]}")
    print(f"  Expected:   {expected_drig}")
    print("-" * 60)

