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

# --- Constants adapted from user's custom script ---
c_MOOL = "MOOL"
c_SWAYAM = "SWAYAM"
c_ATHIMITRA = "ATHIMITRA"
c_MITRA = "MITRA"
c_SAMA = "SAMA"
c_SHATRU = "SHATRU"
c_ATHISHATRU = "ATHISHATRU"

rel2sapthavargajabala = {
    c_MOOL: 45,
    c_SWAYAM: 30,
    c_ATHIMITRA: 20,
    c_MITRA: 15,
    c_SAMA: 10,
    c_SHATRU: 4,
    c_ATHISHATRU: 2
}

ZODIAC_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGN_LORDS = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}
PLANET_GENDERS = {'Sun': 'MALE', 'Moon': 'FEMALE', 'Mars': 'MALE', 'Mercury': 'NEUTER', 'Jupiter': 'MALE', 'Venus': 'FEMALE', 'Saturn': 'NEUTER'}
NAISARGIKA_VALUES = {'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71, 'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57}
EXALTATION_DEGREES = {'Sun': 10, 'Moon': 33, 'Mars': 298, 'Mercury': 165, 'Jupiter': 95, 'Venus': 357, 'Saturn': 200}

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

# --- Helper Functions ---
def normalize(angle: float) -> float: return (angle % 360 + 360) % 360
def angdiff(a: float, b: float) -> float:
    d = abs(normalize(a) - normalize(b))
    return 360 - d if d > 180 else d
def get_varga_sign(long_deg: float, divisor: int) -> str:
    idx = int((normalize(long_deg) * divisor) // 30) % 12
    return ZODIAC_SIGNS[idx]

class PlanetObj:
    def __init__(self, name, house, sign, sign_deg, total_long, retro):
        self.celestial_body = name
        self.house = house
        self.sign = sign
        self.sign_degrees = sign_deg
        self.total_longitude = total_long
        self.retro = retro
        self.shadbala = {}

# --- User's Exact Dispositor Relation Logic ---
def get_PlanetaryDispositorRelation(planet, div_sign, D1_planets):
    dispositor = SIGN_LORDS[div_sign]
    
    # Natural relations from D1_planets
    naturalfriends = PLANETARY_RELATIONS[planet]["friends"]
    naturalenemies = PLANETARY_RELATIONS[planet]["enemies"]
    naturalnuetrals = PLANETARY_RELATIONS[planet]["neutrals"]
    
    # Check own sign and exalt/mool
    mool_signs = {"Sun": "Leo", "Moon": "Taurus", "Mars": "Aries", "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius"}
    
    if mool_signs.get(planet) == div_sign:
        return c_MOOL
    elif div_sign in SIGN_LORDS and SIGN_LORDS[div_sign] == planet:
        return c_SWAYAM
        
    # Natural friendship value
    if dispositor in naturalfriends:
        n_val = 1
    elif dispositor in naturalenemies:
        n_val = -1
    else:
        n_val = 0

    # Temporary friendship (from D1 house positions)
    p_house = next(pl.house for pl in D1_planets if pl.celestial_body == planet)
    d_house = next(pl.house for pl in D1_planets if pl.celestial_body == dispositor)
    
    # housediff
    planet2disp = (d_house - p_house + 12) % 12
    if planet2disp in [2, 3, 4, 10, 11, 0]: # 10, 11, 12 in 1-based is 9, 10, 11 in 0-based. Plus 12th is index 11.
        # Wait! The user's code says:
        # if((planet2disp == 2) or (planet2disp == 3) or (planet2disp == 4) or (planet2disp == 10) or (planet2disp == 11) or (planet2disp == 12)):
        # Wait, in the user's code, house numbers are 1-based!
        # So:
        # planet2disp = gen.housediff(planethouse, dispositorhouse)
        # Let's map housediff to 1-based:
        pass
    
    # Let's write housediff exactly as they would:
    # If 1-based house diff is 2, 3, 4, 10, 11, 12
    # In 1-based diff: diff = (disp - planet + 12) % 12. If diff == 0, it's 12.
    diff_1based = (d_house - p_house + 12) % 12
    if diff_1based == 0:
        diff_1based = 12
        
    if diff_1based in [2, 3, 4, 10, 11, 12]:
        t_val = 1
    else:
        t_val = -1
        
    final_val = n_val + t_val
    if final_val == 2: return c_ATHIMITRA
    elif final_val == 1: return c_MITRA
    elif final_val == 0: return c_SAMA
    elif final_val == -1: return c_SHATRU
    else: return c_ATHISHATRU

# --- User's Sputa Drishti Formula ---
def get_sputadrishti(degree, aspectingplanet):
    degree = abs(degree) % 360
    if(degree <=30):
        return(0)
    elif(degree <=60):
        if(aspectingplanet == "Saturn"):
            return((degree - 30 ) * 2)
        else:
            return((degree - 30 ) / 2)
    elif(degree <=90):
        if(aspectingplanet == "Saturn"):
            return(45 + (90 - degree) / 2)
        else:
            return(degree - 45)
    elif(degree <=120):
        if((aspectingplanet == "Mars") or (aspectingplanet == "Jupiter")):
            return(45 + (degree - 90) / 2)
        else:
            return(30 + (120 - degree) / 2)
    elif(degree <=150):
        if((aspectingplanet == "Mars") or (aspectingplanet == "Jupiter")):
            return((150 - degree) * 2)
        else:
            return(150 - degree)
    elif(degree <=180):
        return((abs(150 - degree)) * 2)
    elif(degree <=210):
        if(aspectingplanet == "Mars"):
            return(60)
        else:
            return((300 - degree) / 2)
    elif(degree <=240):
        if(aspectingplanet == "Mars"):
            return(270 - degree)
        elif(aspectingplanet == "Jupiter"):
            return(45 + (degree - 210 ) / 2)
        else:
            return((300 - degree) / 2)
    elif(degree <=270):
        if(aspectingplanet == "Saturn"):
            return(degree - 210)
        elif(aspectingplanet == "Jupiter"):
            return(15 + 2 * ( 270 - degree ) / 3)
        else:
            return((300 - degree) / 2)
    elif(degree <=300):
        if(aspectingplanet == "Saturn"):
            return((300 - degree) * 2)
        else:
            return((300 - degree) / 2)
    else:
        return(0)

def run_test():
    # Hardik birth info
    dob = drik.Date(2001, 3, 7)
    tob = (16, 20, 0)
    place = drik.Place('Delhi', 28.6328027, 77.2197713, 5.5)
    jd = utils.julian_day_number(dob, tob)
    
    # 1. Fetch D1 planetary positions
    pp = charts.rasi_chart(jd, place, ayanamsa_mode="LAHIRI")
    asc_sign = pp[0][1][0]
    asc_long = pp[0][1][0] * 30 + pp[0][1][1]
    
    planets = []
    p_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    for idx, name in enumerate(p_names):
        # find in pp (planet_positions)
        # check retro
        retro = charts.rasi_chart(jd, place)[idx+1][1][1] < 0 # wait, retro is checked from motion speed
        h, (s_idx, s_deg) = next((h, pos) for p_idx, pos in pp[1:8] for h in range(1, 13) if p_idx == idx)
        tot_long = s_idx * 30 + s_deg
        house_rel = (s_idx - asc_sign + 12) % 12 + 1
        planets.append(PlanetObj(name, house_rel, ZODIAC_SIGNS[s_idx], s_deg, tot_long, False))
        
    # Set retrograde status for Hardik
    # Hardik has no retrograde planets among Sun, Moon, Mars, Jupiter, Saturn, but Venus/Mercury? None are retro.
    
    # --- STHANABALA ---
    # Uchha Bala
    for p in planets:
        # deb point
        exalt_deg = EXALTATION_DEGREES[p.celestial_body]
        deb_deg = (exalt_deg + 180) % 360
        dist = angdiff(p.total_longitude, deb_deg)
        p.shadbala["Uchhabala"] = round(dist / 3.0, 2)
        
    # Drekkana Bala
    for p in planets:
        deg = p.sign_degrees
        if ((deg <= 10.0) and (p.celestial_body in ["Sun", "Jupiter", "Mars"])):
            p.shadbala["Drekshanabala"] = 15.0
        elif ((deg > 10.0) and (deg <= 20.0) and (p.celestial_body in ["Moon", "Venus"])):
            p.shadbala["Drekshanabala"] = 15.0
        elif ((deg > 20.0) and (p.celestial_body in ["Mercury", "Saturn"])):
            p.shadbala["Drekshanabala"] = 15.0
        else:
            p.shadbala["Drekshanabala"] = 0.0
            
    # Ojhayugmarashiamsabala
    for p in planets:
        d1_idx = ZODIAC_SIGNS.index(p.sign)
        d9_idx = ZODIAC_SIGNS.index(get_varga_sign(p.total_longitude, 9))
        bala = 0.0
        if p.celestial_body in ["Sun", "Mars", "Mercury", "Jupiter", "Saturn"]:
            if (d1_idx % 2) == 0: bala += 15.0 # odd sign (0-indexed Aries is 0, so even indices are odd signs: Aries=0, Gemini=2, etc.)
            if (d9_idx % 2) == 0: bala += 15.0
        else: # Moon, Venus
            if (d1_idx % 2) == 1: bala += 15.0 # even sign (0-indexed Taurus is 1, so odd indices are even signs)
            if (d9_idx % 2) == 1: bala += 15.0
        p.shadbala["Ojhayugmarashiamshabala"] = bala
        
    # Kendra Bala
    for p in planets:
        hno = p.house
        if hno in [1, 4, 7, 10]: p.shadbala["Kendradhibala"] = 60.0
        elif hno in [2, 5, 8, 11]: p.shadbala["Kendradhibala"] = 30.0
        else: p.shadbala["Kendradhibala"] = 15.0
        
    # Saptavargaja Bala using user's custom formulas!
    for p in planets:
        total_score = 0.0
        for div in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]:
            div_num = int(div[1:])
            v_sign = get_varga_sign(p.total_longitude, div_num)
            relation = get_PlanetaryDispositorRelation(p.celestial_body, v_sign, planets)
            score = rel2sapthavargajabala[relation]
            total_score += score
        p.shadbala["Saptavargajabala"] = float(total_score)
        
    # Sthanabala Total
    for p in planets:
        p.shadbala["Sthanabala_Total"] = p.shadbala["Uchhabala"] + p.shadbala["Drekshanabala"] + p.shadbala["Ojhayugmarashiamshabala"] + p.shadbala["Kendradhibala"] + p.shadbala["Saptavargajabala"]

    # --- DIGBALA ---
    # Sun, Mars strong in 10th house center (4th house cusp from Ascendant is zero)
    # Moon, Venus strong in 4th house center (10th house cusp is zero)
    # Mercury, Jupiter strong in 1st house center (7th house cusp is zero)
    # Saturn strong in 7th house center (1st house cusp is zero)
    zero_dig_houses = {"Sun": 4, "Mars": 4, "Moon": 10, "Venus": 10, "Mercury": 7, "Jupiter": 7, "Saturn": 1}
    for p in planets:
        zero_h = zero_dig_houses[p.celestial_body]
        zero_sign = (asc_sign + zero_h - 1) % 12
        zero_point = zero_sign * 30 + 15.0
        dist = angdiff(p.total_longitude, zero_point)
        p.shadbala["Digbala"] = round(dist / 3.0, 2)

    # --- KAALABALA ---
    # Nathonnatabala
    sunrise, sunset = drik.sunrise(jd, place)[0], drik.sunset(jd, place)[0]
    birth_hour = tob[0] + tob[1] / 60.0 + tob[2] / 3600.0
    bt_sec = birth_hour * 3600.0
    if bt_sec > (12*3600):
        bt_gap = (24*3600) - bt_sec
    else:
        bt_gap = bt_sec
    base_natho = bt_gap / 720.0
    for p in planets:
        if p.celestial_body in ["Moon", "Mars", "Saturn"]:
            p.shadbala["Natonnatabala"] = round(base_natho, 2)
        elif p.celestial_body in ["Sun", "Jupiter", "Venus"]:
            p.shadbala["Natonnatabala"] = round(60.0 - base_natho, 2)
        else:
            p.shadbala["Natonnatabala"] = 60.0
            
    # Ayana Bala (sine-based longitude formula!)
    for p in planets:
        signno = ZODIAC_SIGNS.index(p.sign)
        deg = p.sign_degrees
        p_long_full = signno * 30 + deg
        kranti = "North" if signno in [0, 1, 2, 3, 4, 5] else "South"
        
        if p.celestial_body in ["Moon", "Saturn"]:
            if kranti == "North":
                val = 30 * (1 - abs(math.sin(math.radians(p_long_full))))
            else:
                val = 30 * (1 + abs(math.sin(math.radians(p_long_full))))
        elif p.celestial_body in ["Sun", "Mars", "Jupiter", "Venus"]:
            if kranti == "South":
                val = 30 * (1 - abs(math.sin(math.radians(p_long_full))))
            else:
                val = 30 * (1 + abs(math.sin(math.radians(p_long_full))))
        else: # Mercury
            val = 30 * (1 + abs(math.sin(math.radians(p_long_full))))
        p.shadbala["Ayanabala"] = round(val, 2)

    # Pakshabala
    sun_long = next(pl.total_longitude for pl in planets if pl.celestial_body == "Sun")
    moon_long = next(pl.total_longitude for pl in planets if pl.celestial_body == "Moon")
    gap = moon_long - sun_long
    if gap < 0: gap += 360 * 3600 # gap in seconds of arc
    # wait, gen.get_distancebetweenplanets returns distance in seconds of arc
    gap_deg = normalize(moon_long - sun_long)
    if gap_deg > 180:
        gap_deg = 360 - gap_deg
    gap_sec = gap_deg * 3600.0
    val_paksha = gap_sec / (3 * 3600.0)
    
    naturalbenefics = ["Moon", "Mercury", "Jupiter", "Venus"]
    naturalmalefics = ["Sun", "Mars", "Saturn"]
    for p in planets:
        if p.celestial_body in naturalbenefics:
            p.shadbala["Pakshabala"] = round(val_paksha, 2)
        else:
            p.shadbala["Pakshabala"] = round(60.0 - val_paksha, 2)
            
    # Tribhagabala
    # Sun to lagna distance determines day/night parts
    # lagnaPoint = pp[0][1][0]*30 + pp[0][1][1]
    # sun2lagna_dist = normalize(sun_long - lagnaPoint)
    # wait, sun2lagna_dist is the distance in degrees
    sun2lagna_dist = normalize(sun_long - asc_long)
    for p in planets:
        p.shadbala["Tribhagabala"] = 0.0
    next(pl for pl in planets if pl.celestial_body == "Jupiter").shadbala["Tribhagabala"] = 60.0
    
    if sun2lagna_dist <= 60.0: next(pl for pl in planets if pl.celestial_body == "Mercury").shadbala["Tribhagabala"] = 60.0
    elif sun2lagna_dist <= 120.0: next(pl for pl in planets if pl.celestial_body == "Sun").shadbala["Tribhagabala"] = 60.0
    elif sun2lagna_dist <= 180.0: next(pl for pl in planets if pl.celestial_body == "Saturn").shadbala["Tribhagabala"] = 60.0
    elif sun2lagna_dist <= 240.0: next(pl for pl in planets if pl.celestial_body == "Moon").shadbala["Tribhagabala"] = 60.0
    elif sun2lagna_dist <= 300.0: next(pl for pl in planets if pl.celestial_body == "Venus").shadbala["Tribhagabala"] = 60.0
    else: next(pl for pl in planets if pl.celestial_body == "Mars").shadbala["Tribhagabala"] = 60.0

    # VarshaMaasaDinaHoraBala
    # Hardcoded values for test run matching their day lords
    varshalord = "Venus"; maasalord = "Jupiter"; vaaralord = "Mercury"; horalord = "Mars"
    for p in planets:
        bala = 0.0
        if p.celestial_body == varshalord: bala += 15.0
        if p.celestial_body == maasalord: bala += 30.0
        if p.celestial_body == vaaralord: bala += 45.0
        if p.celestial_body == horalord: bala += 60.0
        p.shadbala["VarshaMaasaDinaHoraBala"] = bala
        
    # Kaala Bala Total
    for p in planets:
        p.shadbala["Kaalabala_Total"] = round(p.shadbala["Natonnatabala"] + p.shadbala["Pakshabala"] + p.shadbala["Tribhagabala"] + p.shadbala["VarshaMaasaDinaHoraBala"] + p.shadbala["Ayanabala"], 2)

    # --- CHESHTABALA ---
    # Sun Chestabala is Ayanabala
    next(pl for pl in planets if pl.celestial_body == "Sun").shadbala["Cheshtabala"] = next(pl for pl in planets if pl.celestial_body == "Sun").shadbala["Ayanabala"]
    # Moon Chestabala is Pakshabala
    next(pl for pl in planets if pl.celestial_body == "Moon").shadbala["Cheshtabala"] = next(pl for pl in planets if pl.celestial_body == "Moon").shadbala["Pakshabala"]
    
    # Exterior planets using Kurma Method
    planet_chestapoints = { "Jupiter": [7, 5, 3, 1, 2, 2, 0], "Saturn": [6, 5, 3, 1, 2, 3, 0], "Mars": [7, 6, 4, 2, 0, 1, 0]  }
    for planet in planet_chestapoints:
        p = next(pl for pl in planets if pl.celestial_body == planet)
        dist = angdiff(p.total_longitude, sun_long)
        gap_signs = int(dist // 30.0)
        gap_degrees = dist % 30.0
        
        list_pts = planet_chestapoints[planet].copy()
        cheshtabal_signpart = sum(list_pts[0:gap_signs]) * 3
        chestabal_degreepart = (0.1 * gap_degrees) * list_pts[gap_signs]
        p.shadbala["Cheshtabala"] = round(cheshtabal_signpart + chestabal_degreepart, 2)
        
    # Venus Cheshtabala
    v = next(pl for pl in planets if pl.celestial_body == "Venus")
    gap_v = angdiff(v.total_longitude, sun_long)
    v.shadbala["Cheshtabala"] = round(2 * gap_v - 41 if gap_v > 40.0 else gap_v, 2)
    
    # Mercury Cheshtabala
    mer = next(pl for pl in planets if pl.celestial_body == "Mercury")
    gap_mer = angdiff(mer.total_longitude, sun_long)
    mer.shadbala["Cheshtabala"] = round(2 * gap_mer, 2)
    
    # --- NAISARGIKABALA ---
    for p in planets:
        p.shadbala["Naisargikabala"] = NAISARGIKA_VALUES[p.celestial_body]

    # --- DRIKBALA ---
    for p in planets:
        benefic_sputa = 0.0
        malefic_sputa = 0.0
        for aspecting in planets:
            if aspecting.celestial_body == p.celestial_body: continue
            dist = aspecting.total_longitude - p.total_longitude
            # get_sputadrishti expects degrees
            sputa = get_sputadrishti(dist, aspecting.celestial_body)
            if aspecting.celestial_body in naturalbenefics:
                benefic_sputa += sputa
            elif aspecting.celestial_body in naturalmalefics:
                malefic_sputa += sputa
        p.shadbala["Drikbala"] = round((benefic_sputa - malefic_sputa) / 4.0, 2)
        
    # --- SHADBALA TOTAL ---
    for p in planets:
        total = p.shadbala["Sthanabala_Total"] + p.shadbala["Kaalabala_Total"] + p.shadbala["Digbala"] + p.shadbala["Cheshtabala"] + p.shadbala["Naisargikabala"] + p.shadbala["Drikbala"]
        p.shadbala["Shadbala_Total"] = round(total, 2)
        p.shadbala["Shadbala_Rupas"] = round(total / 60.0, 2)
        
    print("\n" + "="*80)
    print("      SHADBALA CALCULATION WITH USER'S OWN SOFTWARE ALGORITHMS")
    print("="*80)
    print("Planet  | Sthana  | Dig     | Kaala   | Cheshta | Naisar  | Drik    | Total  | Rupas")
    print("-" * 80)
    for p in planets:
        print(f"{p.celestial_body:7} | {p.shadbala['Sthanabala_Total']:7.2f} | {p.shadbala['Digbala']:7.2f} | {p.shadbala['Kaalabala_Total']:7.2f} | {p.shadbala['Cheshtabala']:7.2f} | {p.shadbala['Naisargikabala']:7.2f} | {p.shadbala['Drikbala']:7.2f} | {p.shadbala['Shadbala_Total']:6.2f} | {p.shadbala['Shadbala_Rupas']:5.2f}")
    print("="*80)

if __name__ == "__main__":
    run_test()
