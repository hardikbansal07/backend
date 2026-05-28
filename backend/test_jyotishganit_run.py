import os
import sys
import math
from datetime import datetime

# Setup paths
sys.path.append(r"c:\Users\acer\backend folder\backend")
sys.path.insert(0, r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src")
os.environ["SE_EPHE_PATH"] = r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src\jhora\data\ephe"

import swisseph as swe
swe.set_ephe_path(os.environ["SE_EPHE_PATH"])

from jhora.panchanga import drik
from jhora.horoscope.chart import charts, strength
from jhora import utils, const

# --- Constants adapted for self-contained run ---
ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGN_LORDS = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}
EXALTATION_DEGREES = {'Sun': 10, 'Moon': 33, 'Mars': 298, 'Mercury': 165, 'Jupiter': 95, 'Venus': 357, 'Saturn': 200}
PLANET_GENDERS = {'Sun': 'MALE', 'Moon': 'FEMALE', 'Mars': 'MALE', 'Mercury': 'NEUTER', 'Jupiter': 'MALE', 'Venus': 'FEMALE', 'Saturn': 'NEUTER'}
NAISARGIKA_VALUES = {'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71, 'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57}
KENDRA_BALA_SCORES = {1: 60.0, 4: 60.0, 7: 60.0, 10: 60.0, 2: 30.0, 5: 30.0, 8: 30.0, 11: 30.0, 3: 15.0, 6: 15.0, 9: 15.0, 12: 15.0}

PLANETARY_RELATIONS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutrals": ["Mercury"]},
    "Moon": {"friends": ["Sun", "Mercury"], "enemies": [], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutrals": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutrals": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutrals": ["Saturn"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutrals": ["Mars", "Jupiter"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutrals": ["Jupiter"]}
}

PLANET_INDEX_MAP = {'Sun': 0, 'Moon': 1, 'Mars': 2, 'Mercury': 3, 'Jupiter': 4, 'Venus': 5, 'Saturn': 6}
DECANATE_RULER_GROUPS = {0: [0, 2, 4], 1: [3, 6], 2: [1, 5]}
DIGBALA_STRONG_HOUSES = {'Sun': 10, 'Mars': 10, 'Saturn': 7, 'Moon': 4, 'Venus': 4, 'Mercury': 1, 'Jupiter': 1}
TRIBHAGA_DAY_LORDS = {0: 'Mercury', 1: 'Sun', 2: 'Saturn'}
TRIBHAGA_NIGHT_LORDS = {0: 'Moon', 1: 'Venus', 2: 'Mars'}
WEEKDAY_LORDS = {0: 'Sun', 1: 'Moon', 2: 'Mars', 3: 'Mercury', 4: 'Jupiter', 5: 'Venus', 6: 'Saturn'}
PLANETARY_HOUR_SEQUENCE = [0, 5, 3, 1, 6, 4, 2]

# --- Helper Functions ---
def normalize(angle: float) -> float: return (angle % 360 + 360) % 360
def angdiff(a: float, b: float) -> float:
    d = abs(normalize(a) - normalize(b))
    return 360 - d if d > 180 else d
def get_varga_sign(long_deg: float, divisor: int) -> str:
    idx = int((normalize(long_deg) * divisor) // 30) % 12
    return ZODIAC_SIGNS[idx]

class PlanetaryRelationshipMatrix:
    def __init__(self):
        self.natural_relations = PLANETARY_RELATIONS
        self.sign_lords = SIGN_LORDS
        
    def get_natural_relationship(self, planet1: str, planet2: str) -> str:
        if planet1 not in self.natural_relations:
            return "SAMA"
        if planet2 in self.natural_relations[planet1]["friends"]:
            return "MITRA"
        elif planet2 in self.natural_relations[planet1]["enemies"]:
            return "SHATRU"
        else:
            return "SAMA"
    
    def get_temporary_relationship(self, planet1_sign: str, planet2_sign: str) -> str:
        if not planet1_sign or not planet2_sign:
            return "SAMA"
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
        if self.is_moolatrikona_sign(planet, planet_sign):
            return 45.0
        if self.is_own_sign(planet, planet_sign):
            return 30.0
        natural_rel = self.get_natural_relationship(planet, sign_lord)
        temporary_rel = self.get_temporary_relationship(planet_sign, lord_sign)
        combined_rel = self.get_combined_relationship(natural_rel, temporary_rel)
        relationship_scores = {"ATHIMITRA": 22.5, "MITRA": 15.0, "SAMA": 7.5, "SHATRU": 3.75, "ATHISHATRU": 1.875}
        return relationship_scores.get(combined_rel.upper(), 7.5)

# --- self-contained planet class ---
class PlanetObj:
    def __init__(self, name, house, sign, sign_deg, total_long):
        self.celestial_body = name
        self.house = house
        self.sign = sign
        self.sign_degrees = sign_deg
        self.total_longitude = total_long
        self.shadbala = {}

# --- self-contained house class ---
class HouseObj:
    def __init__(self, house_num, sign, sign_deg, lord):
        self.house_num = house_num
        self.sign = sign
        self.sign_degrees = sign_deg
        self.lord = lord
        self.bhava_bala_adhipathi = 0.0
        self.bhava_dig_bala = 0.0
        self.bhava_drik_bala = 0.0
        self.bhava_bala = 0.0

# --- Sputa Aspect Calculation ---
def get_sputa_drishti_degree(degree: float, aspecting_planet: str) -> float:
    degree = abs(degree) % 360
    if degree > 180:
        degree = 360 - degree
    
    if aspecting_planet == "Mars":
        return _calculate_planet_sputa(degree, [90, 210]) # Special aspects at 4th (90) and 8th (210) houses from Mars
    elif aspecting_planet == "Jupiter":
        return _calculate_planet_sputa(degree, [120, 240]) # Special aspects at 5th (120) and 9th (240) houses from Jupiter
    elif aspecting_planet == "Saturn":
        return _calculate_planet_sputa(degree, [60, 270]) # Special aspects at 3rd (60) and 10th (270) houses from Saturn
    else:
        return _calculate_general_sputa(degree)

def _calculate_general_sputa(degree: float) -> float:
    if degree < 30: return 0.0
    elif degree < 60: return (degree - 30) / 2.0
    elif degree < 90: return degree - 45
    elif degree < 120: return 30 + (120 - degree) / 2.0
    elif degree < 150: return 150 - degree
    else: return 2 * (degree - 150)

def _calculate_planet_sputa(degree: float, special_aspects: list) -> float:
    base_strength = _calculate_general_sputa(degree)
    max_strength = base_strength
    for aspect_angle in special_aspects:
        dist_from_aspect = abs(degree - aspect_angle)
        if dist_from_aspect <= 15.0: # Orb is 15 degrees
            orb_strength = 60.0 * (1 - dist_from_aspect / 15.0)
            max_strength = max(max_strength, orb_strength)
    return max_strength

# --- Test run function ---
def run_test():
    # Hardik birth details
    dob = drik.Date(2001, 3, 7)
    tob = (16, 20, 0)
    place = drik.Place('Delhi', 28.6328027, 77.2197713, 5.5)
    jd = utils.julian_day_number(dob, tob)
    
    # 1. Fetch D1 planetary positions
    pp = charts.rasi_chart(jd, place, ayanamsa_mode="LAHIRI")
    asc_long = pp[0][1][0]*30 + pp[0][1][1]
    
    planets = []
    # Map index to planet name
    p_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    for idx, name in enumerate(p_names):
        # find in pp (planet_positions)
        h, (s_idx, s_deg) = next((h, pos) for p_idx, pos in pp[1:8] for h in range(1, 13) if p_idx == idx)
        tot_long = s_idx * 30 + s_deg
        # House placement relative to Ascendant sign
        asc_sign = pp[0][1][0]
        house_rel = (s_idx - asc_sign + 12) % 12 + 1
        planets.append(PlanetObj(name, house_rel, ZODIAC_SIGNS[s_idx], s_deg, tot_long))
        
    # --- STHANABALA ---
    # Uchha Bala
    for p in planets:
        deb_point = normalize(EXALTATION_DEGREES[p.celestial_body] + 180)
        bala = angdiff(p.total_longitude, deb_point) / 3.0
        p.shadbala["Uchhabala"] = round(bala, 2)
        
    # Saptavargaja Bala
    rel_matrix = PlanetaryRelationshipMatrix()
    divisions = [1, 2, 3, 7, 9, 12, 30]
    for p in planets:
        total_score = 0.0
        for div in divisions:
            v_sign = get_varga_sign(p.total_longitude, div)
            sign_lord = SIGN_LORDS[v_sign]
            lord_planet = next((pl for pl in planets if pl.celestial_body == sign_lord), None)
            lord_sign = lord_planet.sign if lord_planet else None
            score = rel_matrix.get_relationship_score(p.celestial_body, sign_lord, v_sign, lord_sign)
            total_score += score
        p.shadbala["Saptavargajabala"] = round(total_score, 2)
        
    # Ojhayugmarashiamsabala
    for p in planets:
        d1_is_odd = ZODIAC_SIGNS.index(p.sign) % 2 == 0
        d9_is_odd = ZODIAC_SIGNS.index(get_varga_sign(p.total_longitude, 9)) % 2 == 0
        bala = 0
        if p.celestial_body in ['Sun', 'Mars', 'Jupiter']:
            if d1_is_odd: bala += 15
            if d9_is_odd: bala += 15
        else:
            if not d1_is_odd: bala += 15
            if not d9_is_odd: bala += 15
        p.shadbala["Ojhayugmarashiamshabala"] = float(bala)
        
    # Kendra Bala
    for p in planets:
        p.shadbala["Kendradhibala"] = KENDRA_BALA_SCORES.get(p.house, 15.0)
        
    # Drekkana Bala
    for p in planets:
        decanate_index = int(p.sign_degrees // 10.0)
        p_index = PLANET_INDEX_MAP[p.celestial_body]
        bala = 15.0 if p_index in DECANATE_RULER_GROUPS.get(decanate_index, []) else 0.0
        p.shadbala["Drekshanabala"] = bala
        
    # Sthanabala Total
    for p in planets:
        p.shadbala["Sthanabala_Total"] = round(p.shadbala["Uchhabala"] + p.shadbala["Saptavargajabala"] + p.shadbala["Ojhayugmarashiamshabala"] + p.shadbala["Kendradhibala"] + p.shadbala["Drekshanabala"], 2)

    # --- DIGBALA ---
    for p in planets:
        strong_house = DIGBALA_STRONG_HOUSES[p.celestial_body]
        strong_house_sign_idx = (pp[0][1][0] + strong_house - 1) % 12
        strong_point = strong_house_sign_idx * 30 + 15.0
        bala = (180 - angdiff(p.total_longitude, strong_point)) / 3.0
        p.shadbala["Digbala"] = round(bala, 2)
        
    # --- KAALABALA ---
    # Nathonnatabala
    sunrise, sunset = drik.sunrise(jd, place)[0], drik.sunset(jd, place)[0]
    birth_hour = tob[0] + tob[1] / 60.0 + tob[2] / 3600.0
    is_day_birth = sunrise <= birth_hour < sunset
    time_from_midpoint = abs(birth_hour - 12) if is_day_birth else abs(birth_hour - 24 if birth_hour > 12 else birth_hour)
    base_bala = (6 - time_from_midpoint) * 10
    for p in planets:
        if p.celestial_body == "Mercury": bala = 60.0
        elif p.celestial_body in ["Sun", "Jupiter", "Venus"]: bala = base_bala if is_day_birth else 60 - base_bala
        elif p.celestial_body in ["Moon", "Mars", "Saturn"]: bala = 60 - base_bala if is_day_birth else base_bala
        p.shadbala["Natonnatabala"] = round(max(0, bala), 2)
        
    # Pakshabala
    sun_long = next(pl.total_longitude for pl in planets if pl.celestial_body == "Sun")
    moon_long = next(pl.total_longitude for pl in planets if pl.celestial_body == "Moon")
    moon_phase = angdiff(moon_long, sun_long)
    for p in planets:
        if p.celestial_body in ['Moon', 'Jupiter', 'Venus']:
            p.shadbala["Pakshabala"] = round(moon_phase / 3.0, 2)
        elif p.celestial_body in ['Sun', 'Mars', 'Saturn']:
            p.shadbala["Pakshabala"] = round((180 - moon_phase) / 3.0, 2)
        else: # Mercury (depends on association, here mock to benefic/malefic, we use standard pakshabala)
            p.shadbala["Pakshabala"] = round(moon_phase / 3.0, 2)
            
    # Tribhagabala
    part_duration = (sunset - sunrise) / 3.0 if is_day_birth else (24.0 - (sunset - sunrise)) / 3.0
    birth_time_from_event = birth_hour - sunrise if is_day_birth else (birth_hour - sunset + 24) % 24
    part_index = min(2, int(birth_time_from_event / part_duration))
    ruler = TRIBHAGA_DAY_LORDS[part_index] if is_day_birth else TRIBHAGA_NIGHT_LORDS[part_index]
    for p in planets:
        p.shadbala["Tribhagabala"] = 60.0 if (p.celestial_body == "Jupiter" or p.celestial_body == ruler) else 0.0
        
    # Varsha-Maasa-Dina-Hora Bala
    # For test simplicity, we fetch varsha, maasa, dina, hora lords using standard algorithms or hardcode values from our standard run:
    # Hardik born Wed 2001-03-07 at 16:20. Day lord is Mercury. Hora lord is Mars.
    # Varsha lord: Venus, Maasa lord: Jupiter
    varshalord = "Venus"; maasalord = "Jupiter"; vaaralord = "Mercury"; horalord = "Mars"
    for p in planets:
        bala = 0.0
        if p.celestial_body == varshalord: bala += 15.0
        if p.celestial_body == maasalord: bala += 30.0
        if p.celestial_body == vaaralord: bala += 45.0
        if p.celestial_body == horalord: bala += 60.0
        p.shadbala["VarshaMaasaDinaHoraBala"] = bala
        
    # Ayanabala
    for p in planets:
        p_id = PLANET_INDEX_MAP[p.celestial_body]
        # Get declination using swisseph
        res, ret = swe.calc_ut(jd, [swe.SUN, swe.MOON, swe.MARS, swe.MERCURY, swe.JUPITER, swe.VENUS, swe.SATURN][p_id], swe.FLG_EQUATORIAL | swe.FLG_SIDEREAL)
        declination = res[1]
        definite_ayana_bala = ((declination + 24) / 48) * 60
        if p.celestial_body == "Sun": definite_ayana_bala *= 2
        p.shadbala["Ayanabala"] = round(max(0, min(120 if p.celestial_body == "Sun" else 60, definite_ayana_bala)), 2)
        
    # Kaala Bala Total
    for p in planets:
        p.shadbala["Kaalabala_Total"] = round(p.shadbala["Natonnatabala"] + p.shadbala["Pakshabala"] + p.shadbala["Tribhagabala"] + p.shadbala["VarshaMaasaDinaHoraBala"] + p.shadbala["Ayanabala"], 2)
        
    # --- CHESHTABALA ---
    # Adapted using standard epoch table
    sun_mean_long = strength.get_planet_mean_longitude(jd, place, const._SUN)
    for p in planets:
        if p.celestial_body == "Sun":
            p.shadbala["Cheshtabala"] = p.shadbala["Ayanabala"]
        elif p.celestial_body == "Moon":
            p.shadbala["Cheshtabala"] = p.shadbala["Pakshabala"]
        else:
            p_id = PLANET_INDEX_MAP[p.celestial_body]
            mean_long = strength.get_planet_mean_longitude_using_epoch_table(jd, place, p_id)
            seegrocha = sun_mean_long
            if p.celestial_body in ["Mercury", "Venus"]:
                seegrocha = mean_long
                mean_long = sun_mean_long
            ave_long = 0.5 * (p.total_longitude + mean_long)
            reduced_chesta_kendra = abs(seegrocha - ave_long) % 360
            if reduced_chesta_kendra > 180:
                reduced_chesta_kendra = 360 - reduced_chesta_kendra
            p.shadbala["Cheshtabala"] = round(reduced_chesta_kendra / 3.0, 2)
            
    # --- NAISARGIKABALA ---
    for p in planets:
        p.shadbala["Naisargikabala"] = NAISARGIKA_VALUES[p.celestial_body]
        
    # --- DRIKBALA ---
    naturalbenefics = ["Moon", "Mercury", "Jupiter", "Venus"]
    naturalmalefics = ["Sun", "Mars", "Saturn"]
    for p in planets:
        benefic_sputa = 0.0
        malefic_sputa = 0.0
        for aspecting in planets:
            if aspecting.celestial_body == p.celestial_body: continue
            dist = aspecting.total_longitude - p.total_longitude
            sputa = get_sputa_drishti_degree(dist, aspecting.celestial_body)
            if aspecting.celestial_body in naturalbenefics:
                benefic_sputa += sputa
            elif aspecting.celestial_body in naturalmalefics:
                malefic_sputa += sputa
        p.shadbala["Drikbala"] = round((benefic_sputa - malefic_sputa) / 4.0, 2)
        
    # --- SHADBALA TOTAL ---
    for p in planets:
        total = p.shadbala["Sthanabala_Total"] + p.shadbala["Digbala"] + p.shadbala["Kaalabala_Total"] + p.shadbala["Cheshtabala"] + p.shadbala["Naisargikabala"] + p.shadbala["Drikbala"]
        # Sun and Moon Cheshta is not added to total
        if p.celestial_body in ["Sun", "Moon"]:
            total -= p.shadbala["Cheshtabala"]
        p.shadbala["Shadbala_Total"] = round(total, 2)
        p.shadbala["Shadbala_Rupas"] = round(total / 60.0, 2)
        
    print("\n" + "="*80)
    print("           SHADBALA CALCULATION WITH USER'S PROVIDED JYOTISHGANIT CODE")
    print("="*80)
    print("Planet  | Sthana  | Dig     | Kaala   | Cheshta | Naisar  | Drik    | Total  | Rupas")
    print("-" * 80)
    for p in planets:
        print(f"{p.celestial_body:7} | {p.shadbala['Sthanabala_Total']:7.2f} | {p.shadbala['Digbala']:7.2f} | {p.shadbala['Kaalabala_Total']:7.2f} | {p.shadbala['Cheshtabala']:7.2f} | {p.shadbala['Naisargikabala']:7.2f} | {p.shadbala['Drikbala']:7.2f} | {p.shadbala['Shadbala_Total']:6.2f} | {p.shadbala['Shadbala_Rupas']:5.2f}")
    print("="*80)

if __name__ == "__main__":
    run_test()
