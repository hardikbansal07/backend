"""
Astrology Tools - Callable functions for LLM to use
Provides specific astrological data extraction tools that the LLM can invoke as needed
"""

import json
from typing import List, Dict, Any, Optional
from logger_config import setup_logger


from db_manager import MongoDBManager

class AstroTools:
    """
    Collection of astrological analysis tools that can be called by the LLM.
    Each tool extracts specific data from the horoscope on-demand from MongoDB.
    """
    
    def __init__(self, request_id: Optional[str] = None, email: Optional[str] = None):
        self.request_id = request_id
        self.email = email
        self.horoscope_data = None
        self.logger = setup_logger("AstroTools")
        self.logger.info(f"AstroTools initialized with ID: {request_id}, Email: {email}")
    
    def _get_data(self) -> Dict[str, Any]:
        """Lazy load horoscope data from MongoDB."""
        if self.horoscope_data is not None:
            return self.horoscope_data
            
        self.logger.info("Lazy loading horoscope data from MongoDB...")
        db_manager = MongoDBManager()
        try:
            if self.request_id:
                self.horoscope_data = db_manager.get_horoscope_by_request_id(self.request_id)
            elif self.email:
                self.horoscope_data = db_manager.get_horoscope_by_email(self.email)
            
            if not self.horoscope_data:
                raise ValueError(f"No horoscope data found for {self.request_id or self.email}")
                
            # If it's a list, take the first one (should be a dict)
            if isinstance(self.horoscope_data, list) and len(self.horoscope_data) > 0:
                self.horoscope_data = self.horoscope_data[0]
                
            return self.horoscope_data
        finally:
            db_manager.close()
    
    SIGN_NAMES = {
        1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
        7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
    }
    
    SIGN_LORDS = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }
    
    REV_SIGN_NAMES = {
        "ari": 1, "tau": 2, "gem": 3, "can": 4, "leo": 5, "vir": 6,
        "lib": 7, "sco": 8, "sag": 9, "cap": 10, "aqu": 11, "pis": 12,
        "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4, "leo": 5, "virgo": 6,
        "libra": 7, "scorpio": 8, "sagittarius": 9, "capricorn": 10, "aquarius": 11, "pisces": 12
    }
    
    # Planet name normalization map (DB abbreviations -> Full names)
    PLANET_NAME_MAP = {
        "sun": "sun",
        "moon": "moon",
        "mars": "mars",
        "merc": "mercury",
        "mercury": "mercury",
        "jup": "jupiter",
        "jupiter": "jupiter",
        "ven": "venus",
        "venus": "venus",
        "sat": "saturn",
        "saturn": "saturn",
        "rahu": "rahu",
        "ketu": "ketu",
        "uran": "uranus",
        "uranus": "uranus",
        "nept": "neptune",
        "neptune": "neptune",
        "pluto": "pluto"
    }

    def get_house_data(self, houses: List[int], chart: str = "D1") -> Dict[str, Any]:
        """
        Get planetary positions, occupants, and lords for specific houses.
        
        Args:
            houses: List of house numbers to analyze (1-12)
            chart: Divisional chart to analyze (D1, D9, D10, etc.)
        
        Returns:
            Dictionary with house data including occupants and lords
        """
        self.logger.info(f"Tool called: get_house_data(houses={houses}, chart={chart})")
        
        chart_data = self._find_chart(chart)
        if not chart_data:
            return {"error": f"Chart {chart} not found in horoscope"}
        
        # Pre-map planet names to houses for lord placement
        planet_to_house = {}
        for p in chart_data.get('planets', []):
            p_name = self._clean_planet_name(p.get('name', ''))
            planet_to_house[p_name] = p.get('houseRel', p.get('house'))

        result = {
            "chart": chart,
            "houses": {}
        }
        
        # Check if 'houses' data is missing (common in compact formats)
        if not chart_data.get('houses') and (chart_data.get('ascendantSign') or chart_data.get('asc_sign')):
            self.logger.info("House data missing in chart, reconstructing from asc_sign...")
            asc_sign_name = chart_data.get('ascendantSign', chart_data.get('asc_sign', ''))
            asc_sign_num = self.REV_SIGN_NAMES.get(asc_sign_name.lower()[:3])
            
            if asc_sign_num:
                for house_num in houses:
                    # Vedic houses are equal sign from Lagna
                    sign_num = ((asc_sign_num + house_num - 2) % 12) + 1
                    house_info = {
                        "house_number": house_num,
                        "occupants": [],
                        "sign": self.SIGN_NAMES.get(sign_num, "Unknown"),
                        "lord": self.SIGN_LORDS.get(sign_num, "Unknown"),
                        "lord_placed_in": planet_to_house.get(self.SIGN_LORDS.get(sign_num, ""), "Unknown")
                    }
                    
                    # Find occupants
                    for p in chart_data.get('planets', []):
                        p_house = p.get('houseRel', p.get('house'))
                        if p_house == house_num:
                            house_info["occupants"].append(self._clean_planet_name(p.get('name', '')))
                    
                    result["houses"][str(house_num)] = house_info
                
                return result

        # Standard processing if houses are present
        for house_num in houses:
            house_info = {
                "house_number": house_num,
                "occupants": [],
                "sign": "Unknown",
                "lord": "Unknown",
                "lord_placed_in": "Unknown"
            }
            
            # Get sign and lord from existing houses list
            for h in chart_data.get('houses', []):
                if h.get('index') == house_num:
                    sign_num = h.get('signNumber')
                    house_info["sign"] = self.SIGN_NAMES.get(sign_num, "Unknown")
                    house_info["lord"] = self.SIGN_LORDS.get(sign_num, "Unknown")
                    house_info["lord_placed_in"] = planet_to_house.get(house_info["lord"], "Unknown")
                    house_info["occupants"] = [self._clean_planet_name(p) for p in h.get('items', [])]
                    break
            
            result["houses"][str(house_num)] = house_info
        
        self.logger.info(f"get_house_data complete. Found {len(result['houses'])} houses.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def get_planet_details(self, planets: List[str], chart: str = "D1") -> Dict[str, Any]:
        """
        Get detailed information about specific planets.
        
        Args:
            planets: List of planet names (e.g., ["Venus", "Mars"])
            chart: Divisional chart to analyze (D1, D9, etc.)
        
        Returns:
            Dictionary with detailed planetary information
        """
        self.logger.info(f"Tool called: get_planet_details(planets={planets}, chart={chart})")
        
        chart_data = self._find_chart(chart)
        if not chart_data:
            return {"error": f"Chart {chart} not found in horoscope"}
        
        result = {
            "chart": chart,
            "planets": {}
        }
        
        for planet_name in planets:
            planet_data = self._find_planet(chart_data, planet_name)
            if planet_data:
                result["planets"][planet_name] = {
                    "sign": planet_data.get('sign', planet_data.get('sign_name', 'Unknown')),
                    "house": planet_data.get('houseRel', planet_data.get('house', 'Unknown')),
                    "degree": planet_data.get('longitudeDMS', planet_data.get('deg', 'Unknown')),
                    "nakshatra": planet_data.get('nakshatra', planet_data.get('nak', 'Unknown')),
                    "pada": planet_data.get('nakshatraPada', planet_data.get('pada', 'Unknown')),
                    "dignity": planet_data.get('dignity', 'Neutral'),
                    "retrograde": planet_data.get('retrograde', planet_data.get('is_retro', False)),
                    "combust": planet_data.get('isCombust', planet_data.get('is_combust', False)),
                    "exalted": planet_data.get('isExalted', False),
                    "debilitated": planet_data.get('isDebilitated', False),
                    "own_sign": planet_data.get('isOwnSign', False),
                    "chara_karaka": planet_data.get('charaKaraka', None)
                }
            else:
                result["planets"][planet_name] = {"error": f"Planet {planet_name} not found"}
        
        self.logger.info(f"get_planet_details complete. Extracted {len(result['planets'])} planets.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def get_panchanga(self) -> Dict[str, Any]:
        """
        Get Panchanga (5 limbs of time) for birth chart.
        
        Returns:
            Dictionary with complete Panchanga and calendar data
        """
        self.logger.info("Tool called: get_panchanga()")
        
        horoscope_data = self._get_data()
        calendar = horoscope_data.get('calendar', {})
        
        # Return ALL calendar data from MongoDB PLUS birth details
        result = {
            # Birth Details
            "name": horoscope_data.get('name', 'Unknown'),
            "gender": horoscope_data.get('gender', 'Unknown'),
            "birth_date": horoscope_data.get('birth_date', 'Unknown'),
            "birth_time": horoscope_data.get('birth_time', 'Unknown'),
            "birth_place": horoscope_data.get('birth_place', 'Unknown'),
            
            # Core Panchanga (5 limbs)
            "tithi": calendar.get('Tithi', 'Unknown'),
            "nakshatra": calendar.get('Nakshatram', 'Unknown'),
            "yoga": calendar.get('Yoga', 'Unknown'),
            "karana": calendar.get('Karana', 'Unknown'),
            "day": calendar.get('Day', 'Unknown'),
            
            # Sun & Moon timings
            "sunrise": calendar.get('Sun Rise', 'Unknown'),
            "sunset": calendar.get('Sun Set', 'Unknown'),
            "moonrise": calendar.get('Moon Rise', 'Unknown'),
            "moonset": calendar.get('Moon Set', 'Unknown'),
            
            # Raasi (Moon sign) 
            "raasi": calendar.get('Raasi', 'Unknown'),
            
            # Inauspicious timings
            "raagu_kaalam": calendar.get('Raagu Kaalam', 'Unknown'),
            "yamagandam": calendar.get('Yamagandam', 'Unknown'),
            "kuligai": calendar.get('KuLigai', 'Unknown'),
            
            # Auspicious timings
            "abhijit": calendar.get('Abhijit', 'Unknown'),
            "dhur_muhurtham": calendar.get('Dhur Muhurtham', 'Unknown'),
            
            # Years and Months
            "lunar_year_month": calendar.get('Lunar Year/Month:', 'Unknown'),
            "solar_month": calendar.get('Solar Month:', 'Unknown'),
            "kali_year": calendar.get('Kali Year', 'Unknown'),
            "vikrama_year": calendar.get('Vikarama Year', 'Unknown'),
            "saka_year": calendar.get('Saka Year', 'Unknown'),
            
            # Location and time
            "place": calendar.get('Place', 'Unknown'),
            "latitude": calendar.get('Latitude', 'Unknown'),
            "longitude": calendar.get('Longitude', 'Unknown'),
            "timezone_offset": calendar.get('Timezone Offset', 'Unknown'),
            "report_date": calendar.get('Report Date', 'Unknown'),
            "calculation_type": calendar.get('Calcuation Type:', 'Unknown')
        }
        
        self.logger.info("get_panchanga complete.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def get_dasha_periods(self, planet: str = None, time_period: str = None, scope: str = "all") -> Dict[str, Any]:
        """
        Get Dasha (planetary periods) with optional filtering.
        
        Args:
            planet: Optional planet name to filter (e.g., "Saturn", "Jupiter")
            time_period: Optional time filter - "current", "past", "future", or specific year (e.g., "2025")
            scope: "all" (default), "mahadasha_only", or "antardasha_only"
        
        Returns:
            Dictionary with filtered Dasha period information
        """
        self.logger.info(f"Tool called: get_dasha_periods(planet={planet}, time_period={time_period}, scope={scope})")
        
        # Check if horoscope has Dasha data (stored as 'periods' in MongoDB)
        horoscope_data = self._get_data()
        self.logger.debug(f"Available keys in horoscope data: {list(horoscope_data.keys())}")
        
        # Try 'periods' first (MongoDB structure), fallback to 'dasha'
        dasha_data = horoscope_data.get('periods', horoscope_data.get('dasha', None))
        
        if not dasha_data:
            result = {
                "note": "Dasha calculation not available in this horoscope",
                "suggestion": "Dasha periods would be calculated based on Moon's nakshatra position",
                "available_keys": list(horoscope_data.keys())[:20]
            }
        else:
            # Apply filters if requested
            from datetime import datetime
            
            filtered_data = []
            current_date = datetime.now()
            
            for maha in dasha_data if isinstance(dasha_data, list) else []:
                # Filter by planet if specified
                if planet and maha.get('lord', '').lower() != planet.lower():
                    continue
                
                # Filter by time period if specified
                if time_period:
                    maha_start = maha.get('start', '')
                    if time_period == "current":
                        # Check if current date falls within this mahadasha
                        # This would need proper date parsing and comparison
                        pass  # LLM can infer current from dates
                    elif time_period == "past":
                        # Include only past dashas
                        pass
                    elif time_period == "future":
                        # Include only future dashas
                        pass
                    elif time_period.isdigit() and len(time_period) == 4:
                        # Filter by year
                        if time_period not in str(maha_start):
                            continue
                
                # Filter by scope
                if scope == "mahadasha_only":
                    # Remove antardasha details
                    filtered_maha = {k: v for k, v in maha.items() if k != 'antardasha'}
                    filtered_data.append(filtered_maha)
                elif scope == "antardasha_only":
                    # Only include antardashas
                    if 'antardasha' in maha:
                        filtered_data.append({
                            'mahadasha_lord': maha.get('lord'),
                            'antardasha': maha.get('antardasha', [])
                        })
                else:
                    # Include full data
                    filtered_data.append(maha)
            
            result = {
                "dashas": filtered_data if filtered_data else dasha_data,
                "filters_applied": {
                    "planet": planet,
                    "time_period": time_period,
                    "scope": scope
                },
                "note": "Filtered dasha periods based on query parameters" if (planet or time_period or scope != "all") else "All dasha periods"
            }
        
        self.logger.info("get_dasha_periods complete.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def get_divisional_chart_ascendant(self, chart: str) -> Dict[str, Any]:
        """
        Get ascendant information for divisional charts.
        
        Args:
            chart: Chart name (D1, D9, D10, etc.)
        
        Returns:
            Dictionary with ascendant information
        """
        self.logger.info(f"Tool called: get_divisional_chart_ascendant(chart={chart})")
        
        chart_data = self._find_chart(chart)
        if not chart_data:
            return {"error": f"Chart {chart} not found in horoscope"}
        
        result = {
            "chart": chart,
            "ascendant_sign": chart_data.get('ascendantSign', 'Unknown'),
            "ascendant_degree": chart_data.get('ascendantLongitudeDMS', 'Unknown'),
            "ascendant_nakshatra": chart_data.get('ascendantNakshatra', 'Unknown'),
            "ascendant_pada": chart_data.get('ascendantNakshatraPada', 'Unknown'),
            "ascendant_house": chart_data.get('ascendantHouse', 1)
        }
        
        self.logger.info(f"get_divisional_chart_ascendant complete for {chart}.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def get_chart_comparison(self, chart1: str, chart2: str, planet: str) -> Dict[str, Any]:
        """
        Compare a planet's position across two divisional charts.
        
        Args:
            chart1: First chart (e.g., "D1")
            chart2: Second chart (e.g., "D9")
            planet: Planet name to compare
        
        Returns:
            Dictionary comparing planet position in both charts
        """
        self.logger.info(f"Tool called: get_chart_comparison(chart1={chart1}, chart2={chart2}, planet={planet})")
        
        chart1_data = self._find_chart(chart1)
        chart2_data = self._find_chart(chart2)
        
        if not chart1_data or not chart2_data:
            return {"error": "One or both charts not found"}
        
        planet1 = self._find_planet(chart1_data, planet)
        planet2 = self._find_planet(chart2_data, planet)
        
        result = {
            "planet": planet,
            chart1: {
                "sign": planet1.get('sign') if planet1 else 'Not found',
                "house": planet1.get('houseRel') if planet1 else 'Not found',
                "dignity": planet1.get('dignity') if planet1 else 'Not found'
            },
            chart2: {
                "sign": planet2.get('sign') if planet2 else 'Not found',
                "house": planet2.get('houseRel') if planet2 else 'Not found',
                "dignity": planet2.get('dignity') if planet2 else 'Not found'
            },
            "is_vargottama": (planet1.get('sign') == planet2.get('sign')) if (planet1 and planet2) else False
        }
        
        self.logger.info(f"get_chart_comparison complete for {planet}.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    




    
    def get_planet_linkage(self, houses: List[int], chart: str = "D1") -> Dict[str, Any]:
        """
        Calculates comprehensive planet linkage chain with co-tenants, dispositor, and distance.
        
        Args:
            houses: List of house numbers (1-12) to investigate.
            chart: Chart to use for placement (default D1).
        
        Returns:
            Dictionary with complete linkage analysis.
        """
        self.logger.info(f"Tool called: get_planet_linkage(houses={houses}, chart={chart})")
        
        chart_data = self._find_chart(chart)
        if not chart_data:
            return {"error": f"Chart {chart} not found"}
        
        # Get ascendant to calculate house signs
        asc_data = chart_data.get('ascendantSign') or chart_data.get('asc_sign', 'Pisces')
        asc_num = self.REV_SIGN_NAMES.get(asc_data.lower()[:3], 12)
        
        # Build house-to-sign mapping for this chart
        house_signs = {}
        for h in range(1, 13):
            sign_num = ((asc_num + h - 2) % 12) + 1
            house_signs[h] = {
                "sign_name": self.SIGN_NAMES[sign_num],
                "sign_num": sign_num,
                "lord": self.SIGN_LORDS[sign_num]
            }
        
        # Get all planets with their positions
        # Normalize names to full names for consistent lookup
        all_planets = {}
        for p in chart_data.get('planets', []):
            p_name = self._clean_planet_name(p.get('name', ''))
            if p_name.lower() == 'asc':
                continue
            # Normalize to full planet name
            normalized_name = self.PLANET_NAME_MAP.get(p_name.lower(), p_name.lower())
            # Convert back to title case for consistency with SIGN_LORDS
            full_name = normalized_name.title()
            all_planets[full_name] = {
                "house": p.get('houseRel', p.get('house')),
                "sign": p.get('sign', p.get('sign_name')),
                "degree": p.get('longitudeDMS', p.get('deg', 0))
            }
        
        linkages = {}
        
        for focal_house in houses:
            house_info = house_signs[focal_house]
            lord = house_info["lord"]
            
            self.logger.info(f"Analyzing House {focal_house}: Sign={house_info['sign_name']}, Lord={lord}")
            
            # PART 1: LORD ANALYSIS
            lord_data = all_planets.get(lord, {})
            lord_house = lord_data.get("house", "Unknown")
            lord_sign = lord_data.get("sign", "Unknown")
            lord_degree = lord_data.get("degree", 0)
            
            # Find co-tenants (planets in same house as lord)
            co_tenants = []
            if lord_house != "Unknown":
                for p_name, p_data in all_planets.items():
                    if p_data["house"] == lord_house and p_name != lord:
                        deg_diff = abs(p_data["degree"] - lord_degree)
                        co_tenants.append({
                            "planet": p_name,
                            "degree": p_data["degree"],
                            "degree_difference": round(deg_diff, 2),
                            "is_conjunct": deg_diff < 12
                        })
            
            # Find host/dispositor (lord of the sign where planet sits)
            host = "Unknown"
            if lord_sign != "Unknown":
                sign_num = self.REV_SIGN_NAMES.get(lord_sign.lower()[:3], 0)
                if sign_num:
                    host = self.SIGN_LORDS[sign_num]
            
            # Bhavat Bhavam distance (anti-clockwise from focal_house to lord_house, inclusive)
            if lord_house != "Unknown":
                distance = ((lord_house - focal_house) % 12) + 1
                bhavat_bhavam_distance = distance if distance <= 12 else 1
            else:
                bhavat_bhavam_distance = None
            
            lord_chain = {
                "planet": lord,
                "rules_house": focal_house,
                "current_placement": {
                    "house": lord_house,
                    "sign": lord_sign,
                    "degree": lord_degree
                },
                "co_tenants": co_tenants,
                "host_dispositor": host,
                "bhavat_bhavam_distance": bhavat_bhavam_distance
            }
            
            # PART 2: OCCUPANTS ANALYSIS (planets sitting IN focal house)
            occupants = []
            for p_name, p_data in all_planets.items():
                if p_data["house"] == focal_house:
                    # Find this planet's natural position
                    # (Which house would its natural sign be in this chart?)
                    natural_houses = []
                    for h_num, h_info in house_signs.items():
                        if h_info["lord"] == p_name:
                            natural_houses.append(h_num)
                    
                    # Distance from natural position
                    distances = [abs(focal_house - nh) for nh in natural_houses] if natural_houses else []
                    min_distance = min(distances) if distances else None
                    
                    # Find what planets are in this planet's natural house
                    natural_house_occupants = []
                    for nh in natural_houses:
                        for op_name, op_data in all_planets.items():
                            if op_data["house"] == nh:
                                natural_house_occupants.append({
                                    "planet": op_name,
                                    "in_house": nh
                                })
                    
                    occupants.append({
                        "planet": p_name,
                        "degree": p_data["degree"],
                        "natural_houses": natural_houses,
                        "displacement_distance": min_distance,
                        "planets_in_natural_house": natural_house_occupants
                    })
            
            linkages[str(focal_house)] = {
                "focal_house": focal_house,
                "focal_sign": house_info["sign_name"],
                "lord_chain": lord_chain,
                "occupants_chain": occupants
            }
        
        result = {
            "chart": chart,
            "linkage_analysis": linkages
        }
        
        # Automatically extract and enrich conjunctions
        conjunctions_enriched = self.extract_conjunctions_with_roles(result)
        result["conjunctions_enriched"] = conjunctions_enriched
        
        # Calculate planetary aspects
        planetary_aspects = self._calculate_planetary_aspects(all_planets)
        result["planetary_aspects"] = planetary_aspects
        
        self.logger.info(f"get_planet_linkage complete for houses {houses}.")
        self.logger.info(f"Return: {json.dumps(result, indent=2)}")
        return result
    
    def _calculate_planetary_aspects(self, all_planets: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Calculate Vedic planetary aspects with inclusive counting.
        
        Aspect rules:
        - All planets: 7th house from itself
        - Mars: 4th, 7th, 8th houses from itself
        - Jupiter: 5th, 7th, 9th houses from itself
        - Saturn: 3rd, 7th, 10th houses from itself
        - Rahu: 5th, 7th, 9th houses from itself
        - Ketu: 5th, 7th, 9th houses from itself
        
        Inclusive counting: Planet in H1 aspecting 3rd = H1,H2,H3 = 3 houses
        """
        # Define aspect patterns  ( aspect means how many houses forward from current)
        ASPECT_RULES = {
            'Sun': [7],
            'Moon': [7],
            'Mars': [4, 7, 8],
            'Mercury': [7],
            'Jupiter': [5, 7, 9],
            'Venus': [7],
            'Saturn': [3, 7, 10],
            'Rahu': [5, 7, 9],
            'Ketu': [5, 7, 9]
        }
        
        aspects_by_planet = {}
        aspects_by_house = {h: [] for h in range(1, 13)}
        
        for planet_name, planet_data in all_planets.items():
            current_house = planet_data['house']
            aspect_pattern = ASPECT_RULES.get(planet_name, [7])  # Default to 7th
            
            # Only include planets with special aspects (more than just 7th house)
            has_special_aspects = len(aspect_pattern) > 1
            if not has_special_aspects:
                continue  # Skip planets with only standard 7th house aspect
            
            aspected_houses = []
            aspected_planets = []
            
            for aspect_offset in aspect_pattern:
                # Inclusive counting: Planet in H1, 7th aspect = 1+2+3+4+5+6+7 = H7
                # Formula: ((current - 1) + (offset - 1)) % 12 + 1
                target_house = ((current_house - 1) + (aspect_offset - 1)) % 12 + 1
                
                aspected_houses.append({
                    'house': target_house,
                    'aspect_type': f'{aspect_offset}th_house'
                })
                
                # Find which planets are in the aspected house
                for other_planet, other_data in all_planets.items():
                    if other_data['house'] == target_house and other_planet != planet_name:
                        aspected_planets.append({
                            'planet': other_planet,
                            'in_house': target_house,
                            'aspect_type': f'{aspect_offset}th_house'
                        })
                
                # Track which planet aspects this house
                aspects_by_house[target_house].append({
                    'aspecting_planet': planet_name,
                    'from_house': current_house,
                    'aspect_type': f'{aspect_offset}th_house'
                })
            
            aspects_by_planet[planet_name] = {
                'current_house': current_house,
                'current_sign': planet_data.get('sign', 'Unknown'),
                'degree': planet_data.get('degree', 0),
                'aspects_houses': aspected_houses,
                'aspects_planets': aspected_planets,
                'has_special_aspects': True  # Always True since we filtered above
            }
        
        return {
            'by_planet': aspects_by_planet,
            'by_house': aspects_by_house,
            'note': 'Only planets with special aspects (Mars, Jupiter, Saturn, Rahu, Ketu) are included'
        }

    
    def extract_conjunctions_with_roles(self, linkage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts all conjunct planets and enriches with linkage info + roles.
        Returns planet-centric format: each planet with its complete story.
        """
        import os
        
        # Load planet roles
        planet_roles_path = os.path.join(os.path.dirname(__file__), 'planet_roles.json')
        with open(planet_roles_path, 'r') as f:
            planet_roles = json.load(f)
        
        # Collect all planets involved in conjunctions with their context
        planets_data = {}
        
        # Iterate through each house analysis
        for house_num, house_data in linkage_data.get('linkage_analysis', {}).items():
            focal_house = house_data['focal_house']
            focal_sign = house_data['focal_sign']
            lord = house_data['lord_chain']['planet']
            lord_placement = house_data['lord_chain']['current_placement']
            
            # Get all conjunct planets for this lord
            conjunct_planets = []
            for co_tenant in house_data['lord_chain'].get('co_tenants', []):
                if co_tenant['is_conjunct']:  # Only < 12°
                    conjunct_planets.append({
                        'name': co_tenant['planet'],
                        'degree_diff': co_tenant['degree_difference']
                    })
            
            # Only process if there are actual conjunctions
            if conjunct_planets:
                # Add lord data
                if lord not in planets_data:
                    planets_data[lord] = {
                        'linkage_info': {
                            'rules_house': focal_house,
                            'current_house': lord_placement['house'],
                            'current_sign': lord_placement['sign'],
                            'degree': lord_placement['degree'],
                            'displacement': house_data['lord_chain']['bhavat_bhavam_distance'],
                            'conjunct_with': []
                        },
                        'roles': planet_roles.get(lord, {})
                    }
                
                # Add conjunct planets to lord's list
                for cp in conjunct_planets:
                    if cp['name'] not in [c['planet'] for c in planets_data[lord]['linkage_info']['conjunct_with']]:
                        planets_data[lord]['linkage_info']['conjunct_with'].append({
                            'planet': cp['name'],
                            'degree_difference': cp['degree_diff']
                        })
                    
                    # Add each conjunct planet's data
                    if cp['name'] not in planets_data:
                        planets_data[cp['name']] = {
                            'linkage_info': {
                                'current_house': lord_placement['house'],
                                'current_sign': lord_placement['sign'],
                                'conjunct_with': [{
                                    'planet': lord,
                                    'degree_difference': cp['degree_diff']
                                }]
                            },
                            'roles': planet_roles.get(cp['name'], {})
                        }
                    else:
                        # Add to existing conjunct_with list
                        if lord not in [c['planet'] for c in planets_data[cp['name']]['linkage_info']['conjunct_with']]:
                            planets_data[cp['name']]['linkage_info']['conjunct_with'].append({
                                'planet': lord,
                                'degree_difference': cp['degree_diff']
                            })
        
        result = {
            'chart': linkage_data.get('chart', 'D1'),
            'total_planets_in_conjunctions': len(planets_data),
            'planets': planets_data
        }
        
        self.logger.info(f"Extracted {len(planets_data)} planet(s) involved in conjunctions with roles")
        return result
    
    # Helper methods
    
    def _find_chart(self, chart_name: str) -> Optional[Dict[str, Any]]:
        """Find a divisional chart by name (D1, D9, etc.)"""
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
            data = self._get_data()
            if 'rasiChart' in data:
                return data['rasiChart']
            if 'planets' in data:
                return data
            return None
        
        # Find in divisional charts
        div_charts = self._get_data().get('divisionalCharts', [])
        if not div_charts and 'div_charts' in self._get_data():
            div_charts = self._get_data()['div_charts']

        for chart in div_charts:
            if chart.get('factor') == factor:
                return chart
        
        if "chart_analysis" in self._get_data():
            for chart in self._get_data()["chart_analysis"]:
                if chart.get("divisional_chart") == chart_name:
                    return self._transform_analyzed_to_raw(chart)

        return None

    def _transform_analyzed_to_raw(self, analyzed_chart: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms the analyzed report format into a minimal raw format for the tools."""
        raw = {
            "ascendantSign": analyzed_chart.get("ascendant", {}).get("sign"),
            "ascendantNakshatra": analyzed_chart.get("ascendant", {}).get("nakshatra"),
            "houses": [],
            "planets": []
        }
        
        for house in analyzed_chart.get("houses", []):
            h_num = house.get("house_number")
            raw["houses"].append({
                "index": h_num,
                "items": house.get("planet_names", []),
                "signNumber": None
            })
            
            for p in house.get("planets_present", []):
                raw["planets"].append({
                    "name": p.get("name"),
                    "houseRel": h_num,
                    "sign": p.get("sign"),
                    "longitudeDMS": p.get("longitude"),
                    "nakshatra": p.get("nakshatra"),
                    "charaKaraka": p.get("charaKaraka"),
                    "dignity": p.get("dignity")
                })
        return raw
    
    def _find_planet(self, chart_data: Dict[str, Any], planet_name: str) -> Optional[Dict[str, Any]]:
        """Find a planet in a chart by name"""
        normalized_search = self.PLANET_NAME_MAP.get(planet_name.lower(), planet_name.lower())
        
        for planet in chart_data.get('planets', []):
            clean_name = self._clean_planet_name(planet.get('name', ''))
            normalized_db = self.PLANET_NAME_MAP.get(clean_name.lower(), clean_name.lower())
            
            if normalized_search == normalized_db:
                return planet
        return None
    
    def _clean_planet_name(self, name: str) -> str:
        """Remove Unicode symbols from planet names"""
        symbols = ['☉', '☾', '♂', '☿', '♃', '♀', '♄', '☊', '☋', '⛢', '♆', '♇', '℞', 'ℒ']
        for symbol in symbols:
            name = name.replace(symbol, '')
        return name.strip()


# Tool definitions for Gemini function calling
def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Returns tool definitions in Gemini's function calling format.
    """
    return [
            {
                "name": "get_house_data",
                "description": "Get planetary positions and occupants for specific houses in a divisional chart. Use this to see which planets are in which houses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "houses": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of house numbers to analyze (1-12). For marriage, use [7]. For career, use [10]. For children, use [5]."
                        },
                        "chart": {
                            "type": "string",
                            "enum": ["D1", "D2", "D3", "D4", "D5", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30"],
                            "description": "Divisional chart to analyze. D1=Rasi (main chart), D9=Navamsa (marriage), D10=Dasamsa (career), D7=Saptamsa (children)",
                            "default": "D1"
                        }
                    },
                    "required": ["houses"]
                }
            },
            {
                "name": "get_planet_details",
                "description": "Get detailed information about specific planets including sign, house, nakshatra, dignity, and strength. Use this to analyze planet positions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "planets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of planet names. Options: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Uranus, Neptune, Pluto"
                        },
                        "chart": {
                            "type": "string",
                            "enum": ["D1", "D2", "D3", "D4", "D5", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30"],
                            "description": "Divisional chart to analyze",
                            "default": "D1"
                        }
                    },
                    "required": ["planets"]
                }
            },
            {
                "name": "get_panchanga",
                "description": "Get Panchanga (5 limbs of time) including Tithi, Nakshatra, Yoga, Karana for the birth chart. Use this to understand birth time factors.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_dasha_periods",
                "description": "Get current Dasha (planetary periods) including Mahadasha and Antardasha. Use this for timing predictions.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_divisional_chart_ascendant",
                "description": "Get ascendant (Lagna) information for a specific divisional chart. Use this to understand the chart's rising sign.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chart": {
                            "type": "string",
                            "enum": ["D1", "D2", "D3", "D4", "D5", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30"],
                            "description": "Divisional chart name"
                        }
                    },
                    "required": ["chart"]
                }
            },
            {
                "name": "get_chart_comparison",
                "description": "Compare a planet's position across two divisional charts. Use this to check if a planet is Vargottama or to see how it changes between charts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chart1": {
                            "type": "string",
                            "enum": ["D1", "D9", "D10", "D7", "D30"],
                            "description": "First chart to compare"
                        },
                        "chart2": {
                            "type": "string",
                            "enum": ["D1", "D9", "D10", "D7", "D30"],
                            "description": "Second chart to compare"
                        },
                        "planet": {
                            "type": "string",
                            "description": "Planet name to compare"
                        }
                    },
                    "required": ["chart1", "chart2", "planet"]
                }
            },
            {
                "name": "get_planet_linkage",
                "description": "Calculate Planet Linkage between Focal Houses and the Kal-Purush (Natural Zodiac). Use this to find deep structural connections between areas of life.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "houses": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of house numbers to investigate linkage for."
                        },
                        "chart": {
                            "type": "string",
                            "enum": ["D1", "D9", "D10"],
                            "description": "Chart to use for placement data.",
                            "default": "D1"
                        }
                    },
                    "required": ["houses"]
                }
            }
        ]
