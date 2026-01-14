import swisseph as swe
from datetime import datetime
import pytz

def get_sidereal_planet_pos(year, month, day, hour, minute):
    # Julian Day
    # Convert to UTC first
    # Simple approx for testing (assume input is UTC or close enough)
    jd = swe.julday(year, month, day, hour + minute/60.0)
    
    # Set Sidereal Mode (Lahiri)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    
    # Calculate Saturn (ID=6)
    # Flags: FLG_SWIEPH (use ephemeris), FLG_SIDEREAL
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    res = swe.calc_ut(jd, swe.SATURN, flags)
    deg = res[0][0] # Longitude
    
    return deg

now = datetime.now()
sat_deg = get_sidereal_planet_pos(now.year, now.month, now.day, now.hour, now.minute)
print(f"Saturn Sidereal Degree: {sat_deg}")

# Sign calc
sign_num = int(sat_deg / 30)
deg_in_sign = sat_deg % 30
signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
print(f"Saturn is in {signs[sign_num]} at {deg_in_sign:.2f} deg")
