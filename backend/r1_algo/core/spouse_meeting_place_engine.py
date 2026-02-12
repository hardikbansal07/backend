from typing import Dict, Any, List, Optional
from .constants import SIGNS, SIGN_DIRECTIONS, SIGN_MODALITIES
from . import tools_data

class SpouseMeetingPlaceEngine:
    """
    Implements Classical Vedic Astrology rules for Meeting Place & Direction.
    Note: This is based on Standard Classical Texts (Parashara/Jaimini principles),
    NOT the K.N. Rao Marriage Timing Research Group.
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
        # 1. 7th House Sign in D1 -> Direction (East/West/etc)
        # 2. 7th House Sign Modality -> Distance (Fixed=Near, Movable=Far, Dual=Medium)
        
        # Get 7th House D1
        h7_data = loader.get_house_details("D1", 7)
        if "error" in h7_data:
            return {"prediction": "Data Not Available", "reason": "House Data Missing"}
            
        sign_num = h7_data.get("signNumber")
        sign_num = h7_data.get("signNumber")
        from .tools_data import _get_sign_name
        sign_name = _get_sign_name(sign_num)
        
        if not sign_name:
             return {"prediction": "Data Not Available", "reason": "Sign Unknown"}
             
        # Direction
        direction = SIGN_DIRECTIONS.get(sign_name, "Unknown")
        
        # Distance (Modality Based)
        modality = "Unknown"
        distance = "Unknown"
        for m, signs in SIGN_MODALITIES.items():
            if sign_name in signs:
                modality = m
                break
        
        if modality == "Movable": distance = "Far from birth place (possibly overseas)"
        elif modality == "Fixed": distance = "Near birth place (same city/region)"
        elif modality == "Dual": distance = "Medium distance (nearby city/state)"
        
        # --- 4th HOUSE OVERRIDE (Village/Home Connection) ---
        # Rule: If 7th Lord is in 4th House OR associated with 4th Lord -> Prioritize "Same Village/Home Town"
        
        # Get 7th Lord Name
        from .tools_data import _get_lord_of_sign
        l7_name = _get_lord_of_sign(sign_num)
        
        # Get 4th House Details
        h4_data = loader.get_house_details("D1", 4)
        h4_sign_num = h4_data.get("signNumber")
        l4_name = _get_lord_of_sign(h4_sign_num)
        
        # Get 10th House Details (for Career/Status connection)
        h10_data = loader.get_house_details("D1", 10)
        h10_sign_num = h10_data.get("signNumber")
        
        # Check 1: 7th Lord in 4th House
        l7_in_h4 = False
        l7_data = loader.get_planet_details("D1", l7_name)
        if l7_data and "sign" in l7_data:
             # Check if planet sign matches 4th house sign
             from .tools_data import _get_sign_name
             if l7_data["sign"] == _get_sign_name(h4_sign_num):
                 l7_in_h4 = True

        # Check 2: 7th Lord conjunct 4th Lord
        l7_conjunct_l4 = False
        l4_data = loader.get_planet_details("D1", l4_name)
        if l7_data and l4_data and l7_data.get("sign") == l4_data.get("sign"):
            l7_conjunct_l4 = True
        
        # Check 3: 7th Lord in 10th House (Career/Status - can be professional OR same village with high reputation)
        l7_in_h10 = False
        if l7_data and "sign" in l7_data:
            if l7_data["sign"] == _get_sign_name(h10_sign_num):
                l7_in_h10 = True
            
        override_msg = ""
        meeting_context = ""
        
        if l7_in_h4 or l7_conjunct_l4:
            distance = "Very Near (Same Village / Neighborhood / Childhood connection)"
            override_msg = "(Strong 4th House Connection Overrides Modality)"
        elif l7_in_h10:
            # 10th House: Professional OR Same Village with High Status
            meeting_context = (
                "\n**Meeting Context**: The 7th Lord in the 10th House suggests meeting through:\n"
                "  - Professional circles, workplace, or career-related networking, OR\n"
                "  - A family-approved connection with someone of high social standing/reputation in the same community.\n"
                "  *(In Vedic tradition, this placement can manifest as either a corporate colleague or someone from the same village who has achieved notable status)*"
            )

        prediction_text = (
            f"**Direction**: Spouse likely from the **{direction}** direction relative to birth place.\n"
            f"**Distance**: Indicated as **{distance}** {override_msg} (Modality: {modality}).{meeting_context}\n"
            f"*(Note: Based on Classical 7th House & 10th House Analysis)*"
        )
        
        return {
            "prediction": prediction_text,
            "direction": direction,
            "distance": distance,
            "confidence": "High (Classical Rule)"
        }
