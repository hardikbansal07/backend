from typing import Dict, Any, List, Optional
from .constants import SIGNS, ASPECTS
from . import tools_data
from .tools_data import _get_sign_name, _get_lord_of_sign

class TimingEngine:
    """
    Implements the 8-Parameter Timing of Marriage Framework 
    from "Astrology and Timing of Marriage (a Scientific Approach)".
    """

    @staticmethod
    def _get_sign_index(sign_name: str) -> int:
        if sign_name in SIGNS:
            return SIGNS.index(sign_name)
        return -1

    @staticmethod
    def _is_aspecting(planet_name: str, current_sign_idx: int, target_sign_idx: int) -> bool:
        """
        Checks if a planet in `current_sign_idx` aspects `target_sign_idx`.
        """
        if current_sign_idx == -1 or target_sign_idx == -1:
            return False
            
        # Distance counting from current (1) to target
        distance = (target_sign_idx - current_sign_idx) + 1
        if distance <= 0: distance += 12
        
        aspects = ASPECTS.get(planet_name, [7]) # Default 7th aspect
        
        # Conjunction (distance 1) is often considered an "aspect" or "influence" in these rules (PAC)
        if distance == 1:
            return True
            
        return distance in aspects

    @staticmethod
    def _get_planet_sign(loader: Any, chart_code: str, planet_name: str) -> Optional[str]:
        if not loader: return None
        p = loader.get_planet_details(chart_code, planet_name)
        if "sign" in p: return p["sign"]
        return None

    @staticmethod
    def _get_house_sign_and_lord(loader: Any, chart_code: str, house_num: int) -> (Optional[str], Optional[str]):
        if not loader: return (None, None)
        h = loader.get_house_details(chart_code, house_num)
        if "signNumber" in h:
            s_name = _get_sign_name(h["signNumber"])
            l_name = _get_lord_of_sign(h["signNumber"])
            return (s_name, l_name)
        return (None, None)

    @staticmethod
    def calculate_vivah_saham(loader: Any) -> Optional[str]:
        """
        Calculates Vivah Saham Sign. 
        Formula: (Long(LL) + Long(7L)) % 360 -> Sign
        """
        if not loader: return None
        
        # Get Lagna Lord and 7th Lord
        _, ll_name = TimingEngine._get_house_sign_and_lord(loader, "D1", 1)
        _, l7_name = TimingEngine._get_house_sign_and_lord(loader, "D1", 7)
        
        if not ll_name or not l7_name: return None
        
        # Get exact longitudes (Assuming 'fullDegree' or similar exists in data, else approximate via Sign)
        # Note: The JSON structure isn't fully visible, but typical scraping has 'longitude' or 'normDegree'.
        # Fallback: Use Sign Index * 30 + 15 (Start of sign? Mid?) 
        # Better: Look for 'total_degrees' or 'longitude' in planet details.
        
        p_ll = loader.get_planet_details("D1", ll_name)
        p_l7 = loader.get_planet_details("D1", l7_name)
        
        # Heuristic to find degree
        def get_deg(p_data):
            if not p_data or "error" in p_data:
                return None
            if "global_degree" in p_data:
                return float(p_data["global_degree"])
            if "total_degree" in p_data:
                return float(p_data["total_degree"])
            if "longitude" in p_data:
                return float(p_data["longitude"])
            # Fallback based on sign
            s = p_data.get("sign")
            idx = TimingEngine._get_sign_index(s)
            if idx != -1:
                return (idx * 30.0) + 15.0 # Center of sign
            return None

        deg_ll = get_deg(p_ll)
        deg_l7 = get_deg(p_l7)
        if deg_ll is None or deg_l7 is None:
            return None
        
        vs_deg = (deg_ll + deg_l7) % 360
        vs_sign_idx = int(vs_deg / 30)
        return SIGNS[vs_sign_idx]

    def analyze_timing(
        current_vimshottari_md: str,
        current_vimshottari_ad: str,
        current_chara_ad_sign: str,
        transit_saturn_sign: str,
        transit_jupiter_sign: str,
        transit_lagna_lord_sign: str,
        transit_7th_lord_sign: str,
        transit_sun_sign: str = "Unknown",
        transit_planets_in_1_7_count: int = 0,
        data_loader: Any = None,
        gender: str = "Male"
    ) -> Dict[str, Any]:
        """
        Analyzes the 8 Parameters for a specific time window defined by the arguments.
        """
        loader = data_loader or tools_data._DATA_LOADER
        if not loader:
             return {"error": "Data Loader not initialized"}

        report = {
            "parameters_met": 0,
            "total_parameters": 8,
            "details": {}
        }
        
        # --- PREPARE NATAL DATA ---
        d1_lagna_sign, d1_ll_name = TimingEngine._get_house_sign_and_lord(loader, "D1", 1)
        d1_7h_sign, d1_7l_name = TimingEngine._get_house_sign_and_lord(loader, "D1", 7)
        
        d9_lagna_sign, d9_ll_name = TimingEngine._get_house_sign_and_lord(loader, "D9", 1)
        d9_7h_sign, d9_7l_name = TimingEngine._get_house_sign_and_lord(loader, "D9", 7) # Correction: Rule says D9 Lagna/7H connection

        # --- PARAMETER 1: VIMSHOTTARI DASHA ---
        # Rule: MD/AD connected to 1H/7H/LL/7L in D1 or D9
        # Simplified Check: Is MD or AD one of the Lords? Or in the House?
        # (Full PAC implementation is complex without full aspect table, focusing on Lords/Placement)
        
        def check_planet_connection(planet, chart):
            # Is it the LL or 7L?
            l_sign, ll = TimingEngine._get_house_sign_and_lord(loader, chart, 1)
            h7_sign, l7 = TimingEngine._get_house_sign_and_lord(loader, chart, 7)
            if planet in [ll, l7]: return True
            
            # Is it placed in 1H or 7H?
            p_data = loader.get_planet_details(chart, planet)
            p_sign = p_data.get("sign")
            if p_sign in [l_sign, h7_sign]: return True
            
            return False

        p1_met = False
        md_ok = check_planet_connection(current_vimshottari_md, "D1") or check_planet_connection(current_vimshottari_md, "D9")
        ad_ok = check_planet_connection(current_vimshottari_ad, "D1") or check_planet_connection(current_vimshottari_ad, "D9")
        
        if md_ok and ad_ok: p1_met = True
        report["details"]["P1_Vimshottari"] = p1_met
        if p1_met: report["parameters_met"] += 1


        # --- PARAMETER 2: JAIMINI CHARA DASHA ---
        # Rule: AD Sign connected to DK, DKN, DP, UPL
        # We need to know DK (lowest degree planet).
        # We need DP, UPL (Calculation required, assume simplistic or skip if unavailable)
        # For now: Check connection to 7th Lord or D1 7H as proxy if Jaimini markers absent? 
        # No, strict rules. We MUST find DK.
        
        # Find DK
        dk_planet = "Unknown"
        min_deg = 360
        all_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"] # Rahu/Ketu usually excluded in some schemes, but let's stick to 7 chara karakas standard
        for p_name in all_planets:
            p_data = loader.get_planet_details("D1", p_name)
            # local_degree usually 0-30
            deg = 0
            if "local_degree" in p_data: deg = float(p_data["local_degree"])
            elif "degree" in p_data: deg = float(p_data["degree"]) # Assuming normalized
            
            if deg < min_deg:
                min_deg = deg
                dk_planet = p_name
        
        dk_sign_d1 = TimingEngine._get_planet_sign(loader, "D1", dk_planet)
        dk_sign_d9 = TimingEngine._get_planet_sign(loader, "D9", dk_planet) # DKN
        
        # Check connection (1-7 axis)
        # Is AD Sign same or opposite to DK sign?
        current_ad_idx = TimingEngine._get_sign_index(current_chara_ad_sign)
        dk_idx = TimingEngine._get_sign_index(dk_sign_d1)
        dkn_idx = TimingEngine._get_sign_index(dk_sign_d9)
        
        def is_axis_1_7(idx1, idx2):
            if idx1 == -1 or idx2 == -1: return False
            dist = abs(idx1 - idx2)
            return dist == 0 or dist == 6
            
        p2_met = is_axis_1_7(current_ad_idx, dk_idx) or is_axis_1_7(current_ad_idx, dkn_idx)
        report["details"]["P2_Chara_Dasha"] = p2_met
        if p2_met: report["parameters_met"] += 1


        # --- PARAMETER 3: VIVAH SAHAM ---
        # Jupiter aspects VS
        vs_sign = TimingEngine.calculate_vivah_saham(loader)
        vs_idx = TimingEngine._get_sign_index(vs_sign)
        jup_transit_idx = TimingEngine._get_sign_index(transit_jupiter_sign)
        
        p3_met = TimingEngine._is_aspecting("Jupiter", jup_transit_idx, vs_idx)
        report["details"]["P3_Vivah_Saham"] = p3_met
        if p3_met: report["parameters_met"] += 1


        # --- PARAMETER 4: DOUBLE TRANSIT ---
        # Saturn AND Jupiter aspect [Lagna, 7H, LL, 7L, VS]
        targets = [d1_lagna_sign, d1_7h_sign, 
                   TimingEngine._get_planet_sign(loader, "D1", d1_ll_name),
                   TimingEngine._get_planet_sign(loader, "D1", d1_7l_name),
                   vs_sign]
        
        # Filter None
        targets = [t for t in targets if t]
        target_indices = [TimingEngine._get_sign_index(t) for t in targets]
        
        sat_idx = TimingEngine._get_sign_index(transit_saturn_sign)
        
        sat_hits = any(TimingEngine._is_aspecting("Saturn", sat_idx, ti) for ti in target_indices)
        jup_hits = any(TimingEngine._is_aspecting("Jupiter", jup_transit_idx, ti) for ti in target_indices)
        
        p4_met = sat_hits and jup_hits
        report["details"]["P4_Double_Transit"] = p4_met
        if p4_met: report["parameters_met"] += 1


        # --- PARAMETER 5: PIYA MILAN ---
        # Transit LL and Transit 7L connection (PAC). 
        # Simplified: Conjunction (Same Sign) or Opposition (1/7).
        t_ll_idx = TimingEngine._get_sign_index(transit_lagna_lord_sign)
        t_l7_idx = TimingEngine._get_sign_index(transit_7th_lord_sign)
        
        p5_met = is_axis_1_7(t_ll_idx, t_l7_idx)
        report["details"]["P5_Piya_Milan"] = p5_met
        if p5_met: report["parameters_met"] += 1


        # --- PARAMETER 6: ACTIVATION OF NATAL PLANETS ---
        # Jupiter aspects Natal Venus (Male) or Natal Mars (Female).
        
        karaka_planet = "Venus"
        if gender and gender.lower().startswith("f"): # Female
            karaka_planet = "Mars"
        
        natal_karaka_sign = TimingEngine._get_planet_sign(loader, "D1", karaka_planet)
        nk_idx = TimingEngine._get_sign_index(natal_karaka_sign)
        # Check aspect
        p6_met = TimingEngine._is_aspecting("Jupiter", jup_transit_idx, nk_idx)
        
        report["details"]["P6_Jupiter_Activates_Karaka"] = p6_met
        report["details"]["P6_Karaka_Used"] = karaka_planet
        if p6_met: report["parameters_met"] += 1


        # --- PARAMETER 7: PLANETARY CONGREGATION ---
        # Sun + Majority (>4?) planets in 1H or 7H.
        # This is strictly "Day of Marriage".
        # We use the arg 'transit_planets_in_1_7_count'.
        # Also check Sun position if provided
        
        # Need house indices of 1H/7H
        # This relies on Transit Signs being overlayed on Natal Houses.
        # 1H is Natal Lagna Sign.
        l_idx = TimingEngine._get_sign_index(d1_lagna_sign)
        h7_idx = TimingEngine._get_sign_index(d1_7h_sign)
        
        sun_idx = TimingEngine._get_sign_index(transit_sun_sign)
        sun_in_axis = (sun_idx == l_idx or sun_idx == h7_idx)
        
        p7_met = (transit_planets_in_1_7_count >= 4) and sun_in_axis # "Sun and majority"
        report["details"]["P7_Planetary_Congregation"] = p7_met
        if p7_met: report["parameters_met"] += 1


        # --- PARAMETER 8: LORDSHIP TRANSIT ---
        # LL in 7H OR 7L in 1H
        # Using Transit Positions vs Natal Houses
        
        ll_in_7h = (t_ll_idx == h7_idx)
        l7_in_1h = (t_l7_idx == l_idx)
        
        p8_met = ll_in_7h or l7_in_1h
        report["details"]["P8_Lordship_Exchange"] = p8_met
        if p8_met: report["parameters_met"] += 1


        return report
