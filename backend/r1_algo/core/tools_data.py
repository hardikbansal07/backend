from typing import List, Dict, Any
from .loader import DataLoader
from .constants import SIGNS, RULERS

def _get_sign_name(sign_number: int) -> str:
    """Returns sign name for 1-based index."""
    if not isinstance(sign_number, int):
        return "Unknown"
    if 1 <= sign_number <= 12:
        return SIGNS[sign_number - 1]
    return "Unknown"

def _get_lord_of_sign(sign_number: int) -> str:
    """Returns lord of the sign."""
    if not isinstance(sign_number, int):
        return "Unknown"
    
    # RULERS is likely Dict[str, List[str]] or similar?
    # Or maybe Dict[int, str]?
    # Let's verify constants.py first.
    # If not found, I will hardcode.
    
    # Fallback Hardcoded logic just in case constants are weird
    # 1: Mars, 2: Venus, 3: Mercury, 4: Moon, 5: Sun, 6: Mercury, 7: Venus, 8: Mars, 9: Jupiter, 10: Saturn, 11: Saturn, 12: Jupiter
    lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }
    return lords.get(sign_number, "Unknown")
    
def retrieve_chart_data(requests: List[str], loader: DataLoader) -> str:
    """
    Retrieves specific astrological data.
    """
    if loader is None:
        return "Error: Data Loader not initialized."
        
    results = []
    
    for req in requests:
        req = req.strip().lower()
        parts = req.split()
        
        # Simple parsing logic
        chart_code = "D1" # Default
        if len(parts) > 0 and (parts[0].upper().startswith("D") or parts[0].upper() == "META"):
            chart_code = parts[0].upper()
            
        if "meta" in req:
            data = loader.load_chart("META")
            results.append(f"Metadata: {data}")
            
        elif "lord" in req:
             # Logic: "D1 7th Lord"
             house_num = 7
             for part in parts:
                 if part.isdigit():
                     house_num = int(part)
                     break
             
             house = loader.get_house_details(chart_code, house_num)
             if "error" in house:
                 results.append(f"{req}: {house['error']}")
                 continue
                 
             sign_number = house.get("signNumber")
             sign_name = _get_sign_name(sign_number)
             lord_name = _get_lord_of_sign(sign_number)
             
             planet = loader.get_planet_details(chart_code, lord_name)
             results.append(f"{chart_code} {house_num}th House ({sign_name}) Lord is {lord_name}. Details: {planet}")

        elif "house" in req:
             # "D1 7th House"
             house_num = 7
             for part in parts:
                 if part.isdigit():
                     house_num = int(part)
                     break
             house = loader.get_house_details(chart_code, house_num)
             sign_number = house.get("signNumber")
             sign_name = _get_sign_name(sign_number)
             results.append(f"{chart_code} {house_num}th House is {sign_name}: {house}")
             
        elif any(p in req for p in ["venus", "jupiter", "sun", "moon", "mars", "mercury", "saturn", "rahu", "ketu", "ascendant"]):
             planet_name = ""
             for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu", "ascendant"]:
                 if p in req:
                     planet_name = p
                     break
             planet = loader.get_planet_details(chart_code, planet_name)
             results.append(f"{chart_code} {planet_name.capitalize()}: {planet}")
             
        else:
             results.append(f"Could not parse request: {req}")
             
    return "\n".join(results)
