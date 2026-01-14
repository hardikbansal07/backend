import math
from datetime import datetime

# Zodiac Constants
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", 
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", 
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", 
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

DASHA_PERIODS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, 
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

def get_sign_index(abs_degrees):
    """Returns 0-11 index of the sign."""
    return int((abs_degrees % 360) / 30)

def get_varga_sign_name(varga_num, abs_degrees):
    """
    Calculates the sign for a specific Divisional Chart (Varga) using Parashara rules.
    Supports Shodashavarga (D1-D60).
    """
    abs_degrees = abs_degrees % 360
    sign_idx = get_sign_index(abs_degrees)
    deg_in_sign = abs_degrees % 30
    
    # D1: Rashi
    if varga_num == 1:
        return ZODIAC_SIGNS[sign_idx]

    # D2: Hora (Parashara - Sun/Moon)
    if varga_num == 2:
        # Odd signs: 0-15 Sun (Leo), 15-30 Moon (Cancer)
        # Even signs: 0-15 Moon (Cancer), 15-30 Sun (Leo)
        is_odd = (sign_idx % 2 == 0) # Aries(0) is Odd
        is_first_half = (deg_in_sign < 15)
        
        if is_odd:
            return "Leo" if is_first_half else "Cancer"
        else:
            return "Cancer" if is_first_half else "Leo"

    # D3: Drekkana (1, 5, 9 from sign)
    if varga_num == 3:
        part = int(deg_in_sign / 10) # 0, 1, 2
        target_idx = (sign_idx + (part * 4)) % 12
        return ZODIAC_SIGNS[target_idx]

    # D4: Chaturthamsha (1, 4, 7, 10 from sign)
    if varga_num == 4:
        part = int(deg_in_sign / (30/4)) # 0, 1, 2, 3
        target_idx = (sign_idx + (part * 3)) % 12
        return ZODIAC_SIGNS[target_idx]
        
    # D7: Saptamsa (Odd: 1-7 from sign; Even: 1-7 from 7th of sign)
    if varga_num == 7:
        part = int(deg_in_sign / (30/7))
        is_odd = (sign_idx % 2 == 0)
        start_idx = sign_idx if is_odd else (sign_idx + 6) % 12
        target_idx = (start_idx + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # D9: Navamsa (1, 5, 9 method simplified: Fire->Aries, Earth->Cap, Air->Lib, Water->Can)
    if varga_num == 9:
        element_start = [0, 9, 6, 3] # Fire, Earth, Air, Water
        start = element_start[sign_idx % 4]
        part = int(deg_in_sign / (30/9))
        target_idx = (start + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # D10: Dasamsa (Odd: 1-10 from sign; Even: 1-10 from 9th of sign)
    if varga_num == 10:
        part = int(deg_in_sign / (30/10))
        is_odd = (sign_idx % 2 == 0)
        start_idx = sign_idx if is_odd else (sign_idx + 8) % 12
        target_idx = (start_idx + part) % 12
        return ZODIAC_SIGNS[target_idx]
        
    # D12: Dwadasamsa (1-12 from sign)
    if varga_num == 12:
        part = int(deg_in_sign / (30/12))
        target_idx = (sign_idx + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # D16: Shodashamsa (Moveable: Aries, Fixed: Leo, Dual: Sag)
    if varga_num == 16:
        part = int(deg_in_sign / (30/16))
        # 0=Moveable, 1=Fixed, 2=Dual (Aries=0 is Moveable)
        quality = sign_idx % 3 
        if quality == 0: start = 0 # Aries
        elif quality == 1: start = 4 # Leo
        else: start = 8 # Sag
        
        target_idx = (start + part) % 12
        return ZODIAC_SIGNS[target_idx]
        
    # D20: Vimshamsha (Moveable: from Aries, Fixed: from Sag, Dual: from Leo)
    if varga_num == 20: 
        part = int(deg_in_sign / (30/20))
        quality = sign_idx % 3
        if quality == 0: start = 0 # Aries
        elif quality == 1: start = 8 # Sag
        else: start = 4 # Leo
        target_idx = (start + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # D24: Siddhamsa (Odd: Leo, Even: Cancer - starts)
    if varga_num == 24:
        part = int(deg_in_sign / (30/24))
        is_odd = (sign_idx % 2 == 0)
        start = 4 if is_odd else 3 # Leo : Cancer
        target_idx = (start + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # D30: Trishamsha (Standard Parashara Mapping)
    if varga_num == 30:
        d = deg_in_sign
        is_odd = (sign_idx % 2 == 0)
        target = 0
        if is_odd:
            if d < 5: target_idx = 0 # Aries
            elif d < 10: target_idx = 10 # Aquarius
            elif d < 18: target_idx = 8 # Sagittarius
            elif d < 25: target_idx = 2 # Gemini
            else: target_idx = 6 # Libra
        else:
            if d < 5: target_idx = 1 # Taurus
            elif d < 12: target_idx = 5 # Virgo
            elif d < 20: target_idx = 11 # Pisces
            elif d < 25: target_idx = 9 # Capricorn
            else: target_idx = 7 # Scorpio
        return ZODIAC_SIGNS[target_idx]

    # D60: Shashtiamsa (1-60 from sign)
    if varga_num == 60:
        part = int(deg_in_sign / (30/60))
        target_idx = (sign_idx + part) % 12
        return ZODIAC_SIGNS[target_idx]

    # Fallback/Generic Harmonic (Parivritti) - good for D144
    abs_deg_harmonic = (abs_degrees * varga_num) % 360
    return ZODIAC_SIGNS[get_sign_index(abs_deg_harmonic)]


def get_nakshatra_pada(abs_degrees):
    """
    Calculates the Nakshatra, Pada, and Lord for a given absolute degree.
    """
    nakshatra_span = 360 / 27
    
    # Calculate index
    nakshatra_idx = int(abs_degrees / nakshatra_span)
    nakshatra_name = NAKSHATRAS[nakshatra_idx % 27]
    lord = NAKSHATRA_LORDS[nakshatra_idx % 9]
    
    # Calculate degrees within the Nakshatra
    degrees_in_nak = abs_degrees % nakshatra_span
    
    # 4 Padas per Nakshatra
    pada_span = nakshatra_span / 4
    pada = int(degrees_in_nak / pada_span) + 1
    
    return nakshatra_name, pada, lord

def get_vimshottari_dasha_detailed(moon_abs_pos, birth_year, birth_month, birth_day):
    """
    Calculates the Vimsottari Dasha with Antardasha support.
    """
    from datetime import datetime, timedelta
    
    nak_span = 360 / 27
    nak_idx = int(moon_abs_pos / nak_span)
    lord = NAKSHATRA_LORDS[nak_idx % 9]
    period_length = DASHA_PERIODS[lord]
    
    degrees_in_nak = moon_abs_pos % nak_span
    fraction_passed = degrees_in_nak / nak_span
    balance_years = (1 - fraction_passed) * period_length
    
    birth_date = datetime(birth_year, birth_month, birth_day)
    
    # Generate Mahadasha Sequence
    md_list = []
    
    # First Mahadasha (partial)
    current_date = birth_date
    end_date = current_date + timedelta(days=balance_years * 365.25)
    md_list.append({
        "Lord": lord,
        "Start": birth_date,
        "End": end_date,
        "IsBirth": True,
        "Duration": balance_years
    })
    
    # Subsequent Mahadashas
    start_lord_idx = (nak_idx % 9) + 1
    # Check current time
    now = datetime.now()
    
    current_md = None
    
    # Find active MD
    start_date_scan = end_date
    
    if birth_date <= now < end_date:
        current_md = md_list[0]
        
    if not current_md:
        for i in range(15): # Scan enough cycles
            curr_lord_idx = (start_lord_idx + i) % 9
            curr_lord = NAKSHATRA_LORDS[curr_lord_idx]
            duration = DASHA_PERIODS[curr_lord]
            end_date_scan = start_date_scan + timedelta(days=duration * 365.25)
            
            md_obj = {
                "Lord": curr_lord,
                "Start": start_date_scan,
                "End": end_date_scan,
                "IsBirth": False,
                "Duration": duration
            }
            # md_list.append(md_obj)
            
            if start_date_scan <= now < end_date_scan:
                current_md = md_obj
                break
                
            start_date_scan = end_date_scan
            
    return current_md

def get_antardashas(mahadasha_lord, mahadasha_start_date):
    """
    Calculates Antardashas (sub-periods) for a given Mahadasha.
    Antardasha sequence starts from the Mahadasha lord itself.
    Rule: AD period = (MD Years * AD Years) / 120 years.
    """
    from datetime import timedelta
    
    ad_list = []
    current_date = mahadasha_start_date
    md_years = DASHA_PERIODS[mahadasha_lord]
    
    cycle_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    
    # Find starting index
    start_idx = 0
    for i, p in enumerate(cycle_order):
        if p == mahadasha_lord:
            start_idx = i
            break
            
    for i in range(9):
        curr_ad_lord = cycle_order[(start_idx + i) % 9]
        ad_years = DASHA_PERIODS[curr_ad_lord]
        
        # Formula: (MD * AD) / 120
        period_years = (md_years * ad_years) / 120.0
        end_date = current_date + timedelta(days=period_years * 365.25)
        
        ad_list.append({
            "Lord": curr_ad_lord,
            "Start": current_date,
            "End": end_date
        })
        current_date = end_date
        
    return ad_list

# --- NEW ANALYSIS TOOLS ---

def get_planetary_dignity(planet, sign):
    """
    Returns the dignity of a planet in a given sign.
    """
    if planet == "Ascendant": return "Neutral"
    
    # Simple Exaltation/Debilitation/Own Mapping
    rules = {
        "Sun": {"Exalt": "Aries", "Debil": "Libra", "Own": ["Leo"]},
        "Moon": {"Exalt": "Taurus", "Debil": "Scorpio", "Own": ["Cancer"]},
        "Mars": {"Exalt": "Capricorn", "Debil": "Cancer", "Own": ["Aries", "Scorpio"]},
        "Mercury": {"Exalt": "Virgo", "Debil": "Pisces", "Own": ["Gemini", "Virgo"]},
        "Jupiter": {"Exalt": "Cancer", "Debil": "Capricorn", "Own": ["Sagittarius", "Pisces"]},
        "Venus": {"Exalt": "Pisces", "Debil": "Virgo", "Own": ["Taurus", "Libra"]},
        "Saturn": {"Exalt": "Libra", "Debil": "Aries", "Own": ["Capricorn", "Aquarius"]},
        "Rahu": {"Exalt": "Taurus", "Debil": "Scorpio", "Own": ["Aquarius"]}, # Standard approx
        "Ketu": {"Exalt": "Scorpio", "Debil": "Taurus", "Own": ["Scorpio"]}
    }
    
    p_rules = rules.get(planet)
    if not p_rules: return "Average"
    
    if sign == p_rules["Exalt"]: return "Exalted"
    if sign == p_rules["Debil"]: return "Debilitated"
    if sign in p_rules["Own"]: return "Own Sign"
    
    return "Neutral"

def get_jaimini_karakas(planet_positions):
    """
    Calculates Jaimini Karakas based on degrees (ignoring sign).
    Returns a dict mapping Karaka (AK, AmK, etc.) to Planet.
    Input: dict {"Sun": 123.45, "Moon": 45.67...}
    """
    # Filter out Rahu/Ketu/Ascendant usually for 7-Karaka scheme
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    
    candidates = []
    for p, deg in planet_positions.items():
        if p in valid_planets:
            deg_in_sign = deg % 30
            candidates.append((p, deg_in_sign))
            
    # Sort by degree descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    karakas = ["Atma Karaka (AK)", "Amatya Karaka (AmK)", "Bhratru Karaka (BK)", 
               "Matru Karaka (MK)", "Putra Karaka (PK)", "Gnati Karaka (GK)", "Dara Karaka (DK)"]
    
    result = {}
    for i, k in enumerate(karakas):
        if i < len(candidates):
            result[k] = f"{candidates[i][0]} ({candidates[i][1]:.2f}°)"
            
    return result

def calculate_shadbala_heuristic(planet, sign, house_type, is_retrograde):
    """
    Returns a simplified score (0-100) and Label.
    Factors: Dignity (40%), House (30%), Retrograde (10%), Natural Strength (20%)
    """
    score = 50 # Base
    
    # 1. Dignity
    dignity = get_planetary_dignity(planet, sign)
    if dignity == "Exalted": score += 30
    elif dignity == "Own Sign": score += 20
    elif dignity == "Debilitated": score -= 20
    
    # 2. House (Kendra/Trikona vs Dusthana)
    if house_type in ["Kendra", "Trikona"]: score += 15
    elif house_type in ["Dusthana"]: score -= 10
    
    # 3. Retrograde (Chesta Bala proxy)
    if is_retrograde and planet not in ["Sun", "Moon", "Rahu", "Ketu"]:
        score += 15 # High Chestabala
        
    # Label
    if score >= 80: label = "Superior"
    elif score >= 60: label = "Strong"
    elif score >= 40: label = "Average"
    else: label = "Weak"
    
    return {"Score": score, "Label": label, "Dignity": dignity}

# Import swisseph
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False

def get_approx_transits(target_date):
    """
    Returns the PRECISE sign placement of major planets (Jupiter, Saturn, Rahu, Ketu)
    using Swiss Ephemeris (Sidereal Lahiri).
    """
    if not HAS_SWISSEPH:
        return "Error: swisseph library not found. Cannot calculate precise transits."

    date_obj = target_date
    if isinstance(target_date, str):
        # Fallback format parsing could be added, but assuming datetime obj
        return "Transit Data Unavailable (Date Parse Error)"
    
    # 1. Set Sidereal Mode
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # 2. Convert to JD (High precision)
    utc_hour = date_obj.hour + date_obj.minute/60.0 # Simplify as UTC approx
    jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, utc_hour)
    
    # 3. Calculate
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    planet_map = {
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE # Vedic often uses Mean Node
    }
    
    transits = {}
    
    for p_name, p_id in planet_map.items():
        res = swe.calc_ut(jd, p_id, flags)
        deg_abs = res[0][0]
        sign_idx = int(deg_abs / 30)
        deg_in_sign = deg_abs % 30
        
        sign_name = ZODIAC_SIGNS[sign_idx % 12]
        transits[p_name] = f"{sign_name} ({deg_in_sign:.2f}\u00b0)"
        
        # Add Ketu 180 deg from Rahu
        if p_name == "Rahu":
            ketu_abs = (deg_abs + 180) % 360
            k_sign_idx = int(ketu_abs / 30)
            k_deg = ketu_abs % 30
            k_sign = ZODIAC_SIGNS[k_sign_idx % 12]
            transits["Ketu"] = f"{k_sign} ({k_deg:.2f}\u00b0)"

    return transits
