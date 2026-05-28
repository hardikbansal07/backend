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

from jhora.horoscope.chart import charts, strength
from jhora import utils, const
from jhora.panchanga import drik

def run_drik_test():
    dob = drik.Date(2001, 3, 7)
    tob = (16, 20, 0)
    place = drik.Place('Delhi', 28.6328027, 77.2197713, 5.5)
    jd = utils.julian_day_number(dob, tob)
    
    expected_drik = {
        "Sun": -4.53, "Moon": 7.10, "Mars": 14.17, "Mercury": 2.57,
        "Jupiter": -6.88, "Venus": 4.91, "Saturn": 0.38
    }
    
    pp = charts.rasi_chart(jd, place, ayanamsa_mode="LAHIRI")
    pp = pp[1:-2]
    
    # Let's define the three options:
    # Option A: Dynamic charts.benefics_and_malefics
    subha_A, asubha_A = charts.benefics_and_malefics(jd, place, ayanamsa_mode="LAHIRI", exclude_rahu_ketu=True)
    
    # Option B: Static (Budha is benefic, Moon is benefic since Shukla Paksha Dwitiya)
    subha_B = [1, 3, 4, 5]
    asubha_B = [0, 2, 6]
    
    # Option C: Static but Moon is malefic (if Krishna Paksha or under specific moon strength thresholds)
    subha_C = [3, 4, 5]
    asubha_C = [0, 1, 2, 6]
    
    def calc_drik(subhas, asubhas):
        dk = [[ 0 for _ in range(7)] for _ in range(7)]
        for p1 in range(7): # Aspected Planet
            p1_long = pp[p1][1][0]*30+pp[p1][1][1]
            for p2 in range(7): # Aspecting Planet
                p2_long = pp[p2][1][0]*30+pp[p2][1][1]
                dk_p1_p2 = round((360.0+p1_long-p2_long)%360,2)
                dk_p1_p2 = strength.__drik_bala_calc_1(dk_p1_p2,p2,p1)
                dk[p1][p2] = round(dk_p1_p2,2)
                
        dk_final = [0 for _ in range(7)]
        for col in range(7):
            dkp = 0; dkm = 0
            for row in range(7):
                if row in subhas:
                    dkp += dk[col][row]
                if row in asubhas:
                    dkm += dk[col][row]
            dk_final[col] = round((dkp - dkm)/4,2)
        return dk_final

    print("Expected JHora Drik Bala:", expected_drik)
    
    res_A = calc_drik(subha_A, asubha_A)
    print("\nOption A (Dynamic benefics/malefics):")
    print("  Calculated:", res_A)
    print("  Subhas:", subha_A, "Asubhas:", asubha_A)
    
    res_B = calc_drik(subha_B, asubha_B)
    print("\nOption B (Static: Moon, Mercury, Jupiter, Venus are benefics):")
    print("  Calculated:", res_B)
    print("  Subhas:", subha_B, "Asubhas:", asubha_B)
    
    res_C = calc_drik(subha_C, asubha_C)
    print("\nOption C (Static: Mercury, Jupiter, Venus are benefics; Moon is malefic):")
    print("  Calculated:", res_C)
    print("  Subhas:", subha_C, "Asubhas:", asubha_C)

if __name__ == "__main__":
    run_drik_test()
