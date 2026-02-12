from typing import Dict, Any, List, Optional
from .timing_engine import TimingEngine 
from .constants import SIGNS, ASPECTS
from . import tools_data

class LoveVsArrangedEngine:
    """
    Implements the "Love vs Arranged" prediction logic from 
    'An Astrological Blueprint for Marriage'.
    
    Rule: 
    - Check D9 (Navamsha) Chart.
    - Focus on 5th House and 11th House axis.
    - If Mahadasha (MD) or Antardasha (AD) Lords have a PAC (Position, Aspect, Conjunction) 
      connection with the 5th House, 11th House, 5th Lord, or 11th Lord in D9.
    - Result: Strong indication of Love Marriage (Gandharva).
    - Else: Likely Arranged (Brahma).
    """

    @staticmethod
    def _get_sign_index(sign_name: str) -> int:
        if sign_name in SIGNS:
            return SIGNS.index(sign_name)
        return -1

    @staticmethod
    def _is_aspecting(planet_name: str, current_sign_idx: int, target_sign_idx: int) -> bool:
        if current_sign_idx == -1 or target_sign_idx == -1: return False
        distance = (target_sign_idx - current_sign_idx) + 1
        if distance <= 0: distance += 12
        if distance == 1: return True # Conjunction
        aspects = ASPECTS.get(planet_name, [7])
        return distance in aspects

    @staticmethod
    def analyze(data: Dict[str, Any], data_loader: Any) -> Dict[str, Any]:
        """
        Input data expected:
        - current_md_lord: str
        - current_ad_lord: str
        - chart_data (optional, else uses global loader)
        """
        loader = data_loader
        if not loader:
            return {"prediction": "Data Not Available (Internal Error: Loader unsupported)"}

        # 1. Extract Context (MD/AD)
        # The agent 'SambandaVidya' passes 'data' which might contain the query context? 
        # Or we need to parse it? 
        # For now, let's assume the 'data' dict *should* have MD/AD info if the agent extracted it.
        # If not, we might fail or default.
        # Let's assume the calling agent (SambandaVidya) will update to pass these.
        
        md_lord = data.get("current_md_lord", "Unknown")
        ad_lord = data.get("current_ad_lord", "Unknown")
        
        if md_lord == "Unknown" and ad_lord == "Unknown":
            return {
                "prediction": "Unable to determine relationship type.",
                "reason": "Current Vimshottari Mahadasha and Antardasha lords are required for this analysis."
            }

        # 2. Get D9 Data
        # We need 5H, 11H, 5L, 11L, and positions of MD/AD in D9.
        
        def get_house_lord_pos(house_num):
            h_data = loader.get_house_details("D9", house_num)
            if "error" in h_data: return None, None, None
            sign_num = h_data.get("signNumber")
            from src.core.tools_data import _get_sign_name, _get_lord_of_sign
            s_name = _get_sign_name(sign_num)
            l_name = _get_lord_of_sign(sign_num)
            return s_name, l_name
            
        d9_5_sign, d9_5_lord = get_house_lord_pos(5)
        d9_11_sign, d9_11_lord = get_house_lord_pos(11)
        
        if not d9_5_sign: 
             return {"prediction": "Data Not Available", "reason": "D9 Chart data missing."}

        # 3. Check Connections (PAC)
        # We check if MD/AD connects to 5H/11H or 5L/11L
        
        targets = []
        # Target Signs (Houses)
        targets.append({"type": "House", "index": 5, "sign": d9_5_sign})
        targets.append({"type": "House", "index": 11, "sign": d9_11_sign})
        
        # Target Planets (Lords) - We need their signs in D9
        targets.append({"type": "Lord", "lord": d9_5_lord})
        targets.append({"type": "Lord", "lord": d9_11_lord})
        
        def check_connection(planet_name):
            if not planet_name or planet_name == "Unknown": return False
            
            p_details = loader.get_planet_details("D9", planet_name)
            if "error" in p_details: return False
            
            p_sign = p_details.get("sign")
            p_sign_idx = LoveVsArrangedEngine._get_sign_index(p_sign)
            
            # Position/Conjunction in House?
            for t in targets:
                if t["type"] == "House":
                    t_sign_idx = LoveVsArrangedEngine._get_sign_index(t["sign"])
                    if p_sign_idx == t_sign_idx: return True # Position/Conjunction in House
                    # Aspect on House?
                    if LoveVsArrangedEngine._is_aspecting(planet_name, p_sign_idx, t_sign_idx): return True
                
                elif t["type"] == "Lord":
                    # Conjunction with Lord?
                    l_details = loader.get_planet_details("D9", t["lord"])
                    if "sign" in l_details:
                        l_sign_idx = LoveVsArrangedEngine._get_sign_index(l_details["sign"])
                        if p_sign_idx == l_sign_idx: return True
                        # Aspect on Lord?
                        if LoveVsArrangedEngine._is_aspecting(planet_name, p_sign_idx, l_sign_idx): return True
                        # Aspect FROM Lord? (Mutual)
                        if LoveVsArrangedEngine._is_aspecting(t["lord"], l_sign_idx, p_sign_idx): return True
            
            return False

        md_connects = check_connection(md_lord)
        ad_connects = check_connection(ad_lord)
        
        # 4. Formulate Result
        if md_connects or ad_connects:
            return {
                "prediction": "Love Marriage (Gandharva Vivah)",
                "confidence": "High",
                "reason": "The Dasha lords (MD/AD) form a connection with the 5th-11th axis (Romance/Desire) in the Navamsha (D9) chart.",
                "details": f"MD ({md_lord}) Connects: {md_connects}, AD ({ad_lord}) Connects: {ad_connects}"
            }
        else:
            return {
                "prediction": "Arranged Marriage (Brahma Vivah)",
                "confidence": "Moderate",
                "reason": "No strong connection found between current Dasha lords and the romantic 5th-11th axis in the D9 chart.",
                "details": f"MD ({md_lord}) Connects: {md_connects}, AD ({ad_lord}) Connects: {ad_connects}"
            }
