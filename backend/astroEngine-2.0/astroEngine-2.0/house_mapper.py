"""
Intelligent House Mapper - Dynamic house and chart selection based on query domain
Extracts relevant astrological data from horoscope based on patterns
"""

import json
from typing import Dict, Any, List, Optional
from logger_config import setup_logger


class HouseMapper:
    SIGN_LORDS = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }

    def __init__(self, chart_house_mapping_path="chart_house_mapping.json"):
        self.logger = setup_logger("HouseMapper")
        self.chart_house_mapping = self._load_chart_mapping(chart_house_mapping_path)
        
    def _load_chart_mapping(self, path: str) -> Dict[str, Any]:
        """Load the chart-house mapping configuration."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                self.logger.info(f"Loaded chart-house mapping from {path}")
                return mapping
        except FileNotFoundError:
            self.logger.warning(f"Chart mapping file not found at {path}")
            return {}
    
    def extract_data_for_pattern(
        self, 
        horoscope_data: Dict[str, Any], 
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract relevant astrological data based on the pattern.
        
        Args:
            horoscope_data: Complete horoscope data
            pattern: Domain pattern from patterns.json
            
        Returns:
            Dictionary containing extracted and structured data
        """
        self.logger.info(f"Extracting data for pattern: {pattern.get('description', 'Unknown')}")
        
        extracted = {
            "domain": pattern.get("description", "Unknown"),
            "focus_houses": pattern.get("focus_houses", []),
            "focus_planets": pattern.get("focus_planets", []),
            "rasi_chart": {},
            "divisional_charts": {},
            "panchanga": {},
            "current_transits": {},
            "special_data": {},
            "all_planets_summary": {}
        }
        
        # Extract Global Planet Summary (Always included for context)
        extracted["all_planets_summary"] = self._extract_all_planets_summary(horoscope_data)
        
        # Extract Rasi Chart (D1) data
        extracted["rasi_chart"] = self._extract_rasi_chart(
            horoscope_data, 
            pattern.get("focus_houses", []),
            pattern.get("focus_planets", [])
        )
        
        # Extract Divisional Charts data
        required_charts = pattern.get("required_charts", ["D1"])
        optional_charts = pattern.get("optional_charts", [])
        all_charts = required_charts + optional_charts
        
        for chart_name in all_charts:
            chart_data = self._extract_divisional_chart(
                horoscope_data,
                chart_name,
                pattern.get("focus_houses", []),
                pattern.get("focus_planets", [])
            )
            if chart_data:
                extracted["divisional_charts"][chart_name] = chart_data
        
        # Extract Panchanga if required
        if "panchanga" in pattern.get("data_requirements", []):
            extracted["panchanga"] = self._extract_panchanga(horoscope_data)
        
        # Extract Current Transits if required
        if "currentTransits" in pattern.get("data_requirements", []):
            extracted["current_transits"] = self._extract_current_transits(horoscope_data)
        
        # Extract Special Data (Vargottama, Combustion, Chara Karaka)
        extracted["special_data"] = self._extract_special_data(
            horoscope_data,
            pattern.get("data_requirements", [])
        )
        
        self.logger.info(f"Data extraction complete. Charts: {list(extracted['divisional_charts'].keys())}")
        return extracted
    
    def _extract_rasi_chart(
        self, 
        horoscope_data: Dict[str, Any],
        focus_houses: List[int],
        focus_planets: List[str]
    ) -> Dict[str, Any]:
        """Extract Rasi Chart (D1) data."""
        rasi_chart = horoscope_data.get("rasiChart", {})
        
        # Fallback for analyzed format
        if not rasi_chart and "chart_analysis" in horoscope_data:
            for chart in horoscope_data["chart_analysis"]:
                if chart.get("divisional_chart") == "D1":
                    return self._extract_from_analyzed_format(chart, focus_houses, focus_planets)
        
        extracted = {
            "ascendant": {
                "sign": rasi_chart.get("ascendantSign", "Unknown"),
                "degree": rasi_chart.get("ascendantLongitudeDMS", "Unknown"),
                "nakshatra": rasi_chart.get("ascendantNakshatra", "Unknown"),
                "pada": rasi_chart.get("ascendantNakshatraPada", "Unknown")
            },
            "houses": {},
            "planets": {},
            "house_lords": {}
        }
        
        # Extract house data and lords
        houses = rasi_chart.get("houses", [])
        planets_data = rasi_chart.get("planets", [])
        
        # Map planet name to its house for lord placement lookup
        planet_to_house = {}
        for p in planets_data:
            p_name = self._clean_planet_name(p.get("name", ""))
            planet_to_house[p_name] = p.get("houseRel")

        for house in houses:
            house_num = house.get("index")
            sign_num = house.get("signNumber")
            lord_name = self.SIGN_LORDS.get(sign_num, "Unknown")
            
            # Populate house_lords regardless of focus (essential context)
            extracted["house_lords"][str(house_num)] = {
                "lord": lord_name,
                "placed_in_house": planet_to_house.get(lord_name, "Unknown"),
                "sign_number": sign_num
            }

            if house_num in focus_houses or not focus_houses:
                extracted["houses"][str(house_num)] = {
                    "sign_number": sign_num,
                    "occupants": house.get("items", [])
                }
        
        # Extract planetary data
        for planet in planets_data:
            planet_name = self._clean_planet_name(planet.get("name", ""))
            
            # Check if this planet is in focus
            if any(fp in planet_name for fp in focus_planets) or not focus_planets:
                extracted["planets"][planet_name] = {
                    "sign": planet.get("sign", "Unknown"),
                    "house": planet.get("houseRel", "Unknown"),
                    "degree": planet.get("longitudeDMS", "Unknown"),
                    "nakshatra": planet.get("nakshatra", "Unknown"),
                    "pada": planet.get("nakshatraPada", "Unknown"),
                    "retrograde": planet.get("retrograde", False),
                    "dignity": planet.get("dignity", "Neutral"),
                    "isExalted": planet.get("isExalted", False),
                    "isDebilitated": planet.get("isDebilitated", False),
                    "isOwnSign": planet.get("isOwnSign", False),
                    "isCombust": planet.get("isCombust", False),
                    "charaKaraka": planet.get("charaKaraka", None)
                }
        
        return extracted

    def _clean_planet_name(self, name: str) -> str:
        """Removes symbols and emojis from planet names."""
        return name.replace("☉", "").replace("☾", "").replace("♂", "").replace("☿", "").replace("♃", "").replace("♀", "").replace("♄", "").replace("☊", "").replace("☋", "").replace("⛢", "").replace("♆", "").replace("♇", "").replace("℞", "").replace("ℒ", "").strip()

    def _extract_all_planets_summary(self, horoscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts a summary of all planets' positions for global context."""
        summary = {}
        
        # Original raw format
        rasi_chart = horoscope_data.get("rasiChart", {})
        planets = rasi_chart.get("planets", [])
        
        if not planets and "chart_analysis" in horoscope_data:
            # Fallback for analyzed format: aggregate from all houses in all charts
            # (Prioritizing D1 for positions)
            for chart in horoscope_data["chart_analysis"]:
                if chart.get("divisional_chart") == "D1":
                    for house in chart.get("houses", []):
                        h_num = house.get("house_number")
                        for p in house.get("planets_present", []):
                            name = self._clean_planet_name(p.get("name", ""))
                            if name:
                                summary[name] = {
                                    "house": h_num,
                                    "sign": p.get("sign"),
                                    "dignity": p.get("dignity")
                                }
        else:
            for p in planets:
                name = self._clean_planet_name(p.get("name", ""))
                summary[name] = {
                    "house": p.get("houseRel"),
                    "sign": p.get("sign"),
                    "dignity": p.get("dignity")
                }
        return summary
    
    def _extract_divisional_chart(
        self,
        horoscope_data: Dict[str, Any],
        chart_name: str,
        focus_houses: List[int],
        focus_planets: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Extract specific divisional chart data."""
        # Map chart names to factors
        chart_factors = {
            "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5,
            "D7": 7, "D9": 9, "D10": 10, "D12": 12,
            "D16": 16, "D20": 20, "D24": 24, "D27": 27,
            "D30": 30, "D40": 40, "D45": 45, "D60": 60
        }
        
        factor = chart_factors.get(chart_name)
        if not factor:
            return None
        
        # D1 is the Rasi Chart
        if factor == 1:
            return self._extract_rasi_chart(horoscope_data, focus_houses, focus_planets)
        
        # Find the divisional chart
        div_charts = horoscope_data.get("divisionalCharts", [])
        chart_data = None
        
        for chart in div_charts:
            if chart.get("factor") == factor:
                chart_data = chart
                break
        
        # Fallback for analyzed format
        if not chart_data and "chart_analysis" in horoscope_data:
            for chart in horoscope_data["chart_analysis"]:
                if chart.get("divisional_chart") == chart_name:
                    return self._extract_from_analyzed_format(chart, focus_houses, focus_planets)

        if not chart_data:
            self.logger.warning(f"Chart {chart_name} (D{factor}) not found in horoscope data")
            return None
        
        extracted = {
            "ascendant": {
                "sign": chart_data.get("ascendantSign", "Unknown"),
                "degree": chart_data.get("ascendantLongitudeDMS", "Unknown"),
                "nakshatra": chart_data.get("ascendantNakshatra", "Unknown")
            },
            "houses": {},
            "planets": {}
        }
        
        # Extract house data
        houses = chart_data.get("houses", [])
        for house in houses:
            house_num = house.get("index")
            if house_num in focus_houses or not focus_houses:
                extracted["houses"][str(house_num)] = {
                    "sign_number": house.get("signNumber"),
                    "occupants": house.get("items", [])
                }
        
        # Extract planetary data
        planets = chart_data.get("planets", [])
        for planet in planets:
            planet_name = planet.get("name", "").replace("☉", "").replace("☾", "").replace("♂", "").replace("☿", "").replace("♃", "").replace("♀", "").replace("♄", "").replace("☊", "").replace("☋", "").replace("⛢", "").replace("♆", "").replace("♇", "").replace("℞", "").replace("ℒ", "").strip()
            
            if any(fp in planet_name for fp in focus_planets) or not focus_planets:
                extracted["planets"][planet_name] = {
                    "sign": planet.get("sign", "Unknown"),
                    "house": planet.get("houseRel", "Unknown"),
                    "degree": planet.get("longitudeDMS", "Unknown"),
                    "nakshatra": planet.get("nakshatra", "Unknown"),
                    "retrograde": planet.get("retrograde", False),
                    "dignity": planet.get("dignity", "Neutral")
                }
        
        return extracted
    
    def _extract_panchanga(self, horoscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Panchanga data."""
        calendar = horoscope_data.get("calendar", {})
        
        return {
            "tithi": calendar.get("Tithi", "Unknown"),
            "nakshatra": calendar.get("Nakshatram", "Unknown"),
            "yoga": calendar.get("Yoga", "Unknown"),
            "karana": calendar.get("Karana", "Unknown"),
            "day": calendar.get("Day", "Unknown"),
            "sunrise": calendar.get("Sun Rise", "Unknown"),
            "sunset": calendar.get("Sun Set", "Unknown")
        }
    
    def _extract_current_transits(self, horoscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract current transit data if available."""
        transits = horoscope_data.get("currentTransits", {})
        
        if not transits:
            return {"note": "Current transit data not available in horoscope"}
        
        return transits
    
    def _extract_special_data(
        self, 
        horoscope_data: Dict[str, Any],
        data_requirements: List[str]
    ) -> Dict[str, Any]:
        """Extract special astrological data."""
        special = {}
        
        # Vargottama planets
        if "vargottama" in data_requirements:
            special["vargottama"] = horoscope_data.get("vargottama", [])
        
        # Combust planets
        if "combustion" in data_requirements:
            special["combustion"] = horoscope_data.get("combustion", [])
        
        # Chara Karakas
        if "charaKaraka" in data_requirements or any("Karaka" in req for req in data_requirements):
            rasi_chart = horoscope_data.get("rasiChart", {})
            planets = rasi_chart.get("planets", [])
            karakas = {}
            
            for planet in planets:
                karaka = planet.get("charaKaraka")
                if karaka:
                    planet_name = planet.get("name", "").replace("☉", "").replace("☾", "").replace("♂", "").replace("☿", "").replace("♃", "").replace("♀", "").replace("♄", "").replace("☊", "").replace("☋", "").replace("℞", "").strip()
                    karakas[karaka] = planet_name
            
            special["chara_karakas"] = karakas
        
        return special

    def _extract_from_analyzed_format(self, chart_data: Dict[str, Any], focus_houses: List[int], focus_planets: List[str]) -> Dict[str, Any]:
        """Fallback extraction for analyzed report format."""
        extracted = {
            "ascendant": {
                "sign": chart_data.get("ascendant", {}).get("sign", "Unknown"),
                "degree": "Unknown",
                "nakshatra": chart_data.get("ascendant", {}).get("nakshatra", "Unknown"),
                "pada": "Unknown"
            },
            "houses": {},
            "planets": {},
            "house_lords": {}
        }
        
        # Re-map analyzed planets to raw-like positions
        for house in chart_data.get("houses", []):
            h_num = house.get("house_number")
            
            # Extract planets from this house
            for p in house.get("planets_present", []):
                p_name = self._clean_planet_name(p.get("name", ""))
                if not p_name: continue
                
                # Check focus
                if any(fp in p_name for fp in focus_planets) or not focus_planets:
                    extracted["planets"][p_name] = {
                        "sign": p.get("sign", "Unknown"),
                        "house": h_num,
                        "degree": p.get("longitude", "Unknown"),
                        "nakshatra": p.get("nakshatra", "Unknown"),
                        "retrograde": p.get("retrograde", False),
                        "dignity": p.get("dignity", "Neutral"),
                        "charaKaraka": p.get("charaKaraka")
                    }
            
            if h_num in focus_houses or not focus_houses:
                extracted["houses"][str(h_num)] = {
                    "sign_number": None, # Missing in analysis format
                    "occupants": house.get("planet_names", [])
                }
        
        return extracted

if __name__ == "__main__":
    # Test the mapper
    mapper = HouseMapper()
    
    # Load a sample horoscope
    import json
    import os
    sample_path = os.path.join(os.path.dirname(__file__), "rama_krishna_full_analysis_data.json")
    with open(sample_path, 'r', encoding='utf-8') as f:
        horoscope = json.load(f)
    
    # Test pattern
    test_pattern = {
        "description": "Dating analysis",
        "focus_houses": [5, 7],
        "focus_planets": ["Venus", "Mars", "Moon"],
        "required_charts": ["D1", "D9"],
        "data_requirements": ["panchanga", "vargottama"]
    }
    
    extracted = mapper.extract_data_for_pattern(horoscope, test_pattern)
    print(json.dumps(extracted, indent=2))
