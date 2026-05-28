import os
import sys
import math
from datetime import datetime

sys.path.append(r"c:\Users\acer\backend folder\backend")
sys.path.insert(0, r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src")
os.environ["SE_EPHE_PATH"] = r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src\jhora\data\ephe"

import swisseph as swe
swe.set_ephe_path(os.environ["SE_EPHE_PATH"])

from jhora.panchanga import drik
from jhora.horoscope.chart import charts, strength
from jhora import utils, const

ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGN_LORDS = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}

PLANETARY_RELATIONS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutrals": ["Mercury"]},
    "Moon": {"friends": ["Sun", "Mercury"], "enemies": [], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutrals": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutrals": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutrals": ["Saturn"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutrals": ["Mars", "Jupiter"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutrals": ["Jupiter"]}
}

def normalize(angle: float) -> float: return (angle % 360 + 360) % 360
def get_varga_sign(long_deg: float, divisor: int) -> str:
    idx = int((normalize(long_deg) * divisor) // 30) % 12
    return ZODIAC_SIGNS[idx]

class PlanetaryRelationshipMatrix:
    def __init__(self):
        self.natural_relations = PLANETARY_RELATIONS
        self.sign_lords = SIGN_LORDS
        
    def get_natural_relationship(self, planet1: str, planet2: str) -> str:
        if planet1 not in self.natural_relations: return "SAMA"
        if planet2 in self.natural_relations[planet1]["friends"]: return "MITRA"
        elif planet2 in self.natural_relations[planet1]["enemies"]: return "SHATRU"
        else: return "SAMA"
    
    def get_temporary_relationship(self, planet1_sign: str, planet2_sign: str) -> str:
        if not planet1_sign or not planet2_sign: return "SAMA"
        try:
            sign1_idx = ZODIAC_SIGNS.index(planet1_sign)
            sign2_idx = ZODIAC_SIGNS.index(planet2_sign)
            house_diff = (sign2_idx - sign1_idx) % 12
            friendly_positions = [1, 2, 3, 9, 10, 11]
            return "MITRA" if house_diff in friendly_positions else "SHATRU"
        except (ValueError, IndexError):
            return "SAMA"
    
    def get_combined_relationship(self, natural_rel: str, temporary_rel: str) -> str:
        nat_rel = natural_rel.upper()
        temp_rel = temporary_rel.upper()
        if nat_rel == "MITRA" and temp_rel == "MITRA": return "ATHIMITRA"
        elif nat_rel == "MITRA" and temp_rel == "SHATRU": return "SAMA"
        elif nat_rel == "SHATRU" and temp_rel == "MITRA": return "SAMA"
        elif nat_rel == "SHATRU" and temp_rel == "SHATRU": return "ATHISHATRU"
        elif nat_rel == "SAMA" and temp_rel == "MITRA": return "MITRA"
        elif nat_rel == "SAMA" and temp_rel == "SHATRU": return "SHATRU"
        else: return "SAMA"
    
    def is_moolatrikona_sign(self, planet: str, sign: str) -> bool:
        mool_signs = {"Sun": "Leo", "Moon": "Taurus", "Mars": "Aries", "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius"}
        return mool_signs.get(planet) == sign
    
    def is_own_sign(self, planet: str, sign: str) -> bool:
        return sign in self.sign_lords and self.sign_lords[sign] == planet
    
    def get_relationship_score(self, planet: str, sign_lord: str, planet_sign: str, lord_sign: str) -> float:
        if self.is_moolatrikona_sign(planet, planet_sign): return 45.0
        if self.is_own_sign(planet, planet_sign): return 30.0
        natural_rel = self.get_natural_relationship(planet, sign_lord)
        temporary_rel = self.get_temporary_relationship(planet_sign, lord_sign)
        combined_rel = self.get_combined_relationship(natural_rel, temporary_rel)
        relationship_scores = {"ATHIMITRA": 22.5, "MITRA": 15.0, "SAMA": 7.5, "SHATRU": 3.75, "ATHISHATRU": 1.875}
        return relationship_scores.get(combined_rel.upper(), 7.5)

def run_calc():
    dob = drik.Date(2001, 3, 7)
    tob = (16, 20, 0)
    place = drik.Place('Delhi', 28.6328027, 77.2197713, 5.5)
    jd = utils.julian_day_number(dob, tob)
    
    pp = charts.rasi_chart(jd, place, ayanamsa_mode="LAHIRI")
    p_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    # 1. Calculate using existing backend
    existing_svb = strength._sapthavargaja_bala1(jd, place)
    
    # 2. Calculate using new code
    rel_matrix = PlanetaryRelationshipMatrix()
    divisions = [1, 2, 3, 7, 9, 12, 30]
    
    new_svb = []
    for idx, name in enumerate(p_names):
        h, (s_idx, s_deg) = next((h, pos) for p_idx, pos in pp[1:8] for h in range(1, 13) if p_idx == idx)
        tot_long = s_idx * 30 + s_deg
        planet_sign = ZODIAC_SIGNS[s_idx]
        
        total_score = 0.0
        for div in divisions:
            v_sign = get_varga_sign(tot_long, div)
            sign_lord = SIGN_LORDS[v_sign]
            lord_idx = p_names.index(sign_lord)
            lord_s_idx, _ = next(pos for p_idx, pos in pp[1:8] if p_idx == lord_idx)
            lord_sign = ZODIAC_SIGNS[lord_s_idx]
            score = rel_matrix.get_relationship_score(name, sign_lord, v_sign, lord_sign)
            total_score += score
        new_svb.append(total_score)
        
    print("\n" + "="*80)
    print("      SAPTAVARGAJA BALA COMPARISON: EXISTING BACKEND vs NEW JYOTISHGANIT")
    print("="*80)
    print("Planet  | Existing Backend (Shashtiamsas) | New Jyotishganit (Shashtiamsas)")
    print("-" * 80)
    for idx, name in enumerate(p_names):
        print(f"{name:7} | {existing_svb[idx]:31.2f} | {new_svb[idx]:31.2f}")
    print("="*80)

if __name__ == "__main__":
    run_calc()
