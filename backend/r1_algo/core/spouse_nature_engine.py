from typing import Dict, Any, List, Optional
from .constants import SIGNS, SIGN_ELEMENTS, TATWA_COMPLEXION, PLANET_HEIGHT_SCORES
from . import tools_data

class SpouseNatureEngine:
    """
    Implements Classical Vedic Astrology rules for Spouse Appearance & Nature.
    Based on 7th House, 7th Lord, and Planets in 7th.
    """

    @staticmethod
    def analyze(data: Dict[str, Any], data_loader: Any) -> Dict[str, Any]:
        """
        Input: None required (uses D1 7th House)
        """
        loader = data_loader
        if not loader:
             return {"prediction": "Data Not Available", "reason": "Loader Error"}

        # Logic: 
        # 1. 7th House Sign -> Element -> General Body Type / Complexion Base
        # 2. 7th Lord -> Influence on Height/Build
        # 3. Planets in 7th -> Strongest influence modifies result (Simplification: Just list them)
        
        # Get 7th House D1
        h7_data = loader.get_house_details("D1", 7)
        if "error" in h7_data:
             return {"prediction": "Data Not Available", "reason": "House Data Missing"}

        sign_num = h7_data.get("signNumber")
        sign_num = h7_data.get("signNumber")
        from .tools_data import _get_sign_name, _get_lord_of_sign
        sign_name = _get_sign_name(sign_num)
        lord_name = _get_lord_of_sign(sign_num)
        
        # 1. Element Analysis
        element = "Unknown"
        for elem, signs in SIGN_ELEMENTS.items():
            if sign_name in signs:
                element = elem
                break
        
        complexion = TATWA_COMPLEXION.get(element, "Varied")
        
        # 2. Lord Influence
        # Height
        height_score = PLANET_HEIGHT_SCORES.get(lord_name, 0)
        height = "Average Height"
        if height_score > 0: height = "Tall / Stature"
        elif height_score < 0: height = "Short / Medium Height"
        
        # 3. Planets in 7th (Occupants override/modify)
        occupants = []
        if "planets" in h7_data:
            # h7_data['planets'] might be list of strings or dicts depending on loader
            # Loader logic in 'get_house_details' returns raw dict? Check loader.py
            # loader.py: get_house_details returns dict with "planets" key usually if implemented.
            # But earlier loader.py view showed it just returns house dict finding by index. 
            # We assume house dict matches schema. Let's assume it has 'planets' list of DB objects.
            pass
            # For safety, let's look up planets by sign instead.
            
        all_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        planets_in_7 = []
        for p in all_planets:
            pd = loader.get_planet_details("D1", p)
            if pd.get("sign") == sign_name:
                planets_in_7.append(p)

        # Synthesis
        influencers = [lord_name] + planets_in_7
        
        # --- DETERMINISTIC INITIALS (Nakshatra Based) ---
        initials = SpouseNatureEngine.get_initials(loader, sign_num) # Pass D1 7H Sign Num to find degree center or logic?
        # Better: We need the Degree of the 7th Cusp OR 7th Lord.
        # Report usually likes 7th Lord or Cusp. Let's use 7th Lord for now as it's easier to find if we don't have Cusp Degrees in House Data.
        # Actually, let's try to get 7th Lord's Nakshatra.
        
        initials_text = "Not Available"
        l7_data = loader.get_planet_details("D1", lord_name)
        if l7_data and "nakshatra" in l7_data:
             nak = l7_data["nakshatra"] # e.g., "Revathi"
             # We need a mapping.
             from .constants import NAKSHATRA_SOUNDS
             # Ensure this constant exists or define it here if missing. 
             # Safe fallback:
             sounds = NAKSHATRA_SOUNDS.get(nak, "Unknown")
             initials_text = f"**{sounds}** (based on 7th Lord {lord_name} in {nak})"

        prediction_text = (
            f"**Complexion**: Likely {complexion} (Element: {element}).\n"
            f"**Stature**: {height} (Governed by {lord_name}).\n"
            f"**Influencing Planets**: {', '.join(influencers)}.\n"
            f"**Name Sounds/Initials**: {initials_text}.\n"
            f"*(Note: Based on Classical 7th House Analysis)*"
        )

        return {
            "prediction": prediction_text,
            "element": element,
            "sign": sign_name,
            "lord": lord_name,
            "initials": initials_text,
            "confidence": "Moderate (Classical Rule)"
        }

    @staticmethod
    def get_initials(loader: Any, house_sign_num: int) -> str:
        # Placeholder or helper if we want to expand logic.
        # For now, implemented inline above is safer to ensure access to local vars.
        return "See Analysis"
