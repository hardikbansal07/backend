from typing import List, Dict, Any
from .loader import DataLoader

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
        if parts[0].upper().startswith("D") or parts[0].upper() == "META":
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
             
        elif "venus" in req or "jupiter" in req or "sun" in req or "moon" in req or "mars" in req or "mercury" in req or "saturn" in req or "rahu" in req or "ketu" in req or "ascendant" in req:
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
