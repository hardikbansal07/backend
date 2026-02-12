import json
from typing import Any, Dict, Optional

class DataLoader:
    def __init__(self, chart_data: Dict[str, Any]):
        self.data = chart_data
        
    def load_chart(self, chart_code: str) -> Dict[str, Any]:
        """
        Loads a specific chart based on code (D1, D9, D10, etc.)
        """
        code = chart_code.upper().strip()
        
        if code == "D1":
            return self.data.get("d1", {}) or self.data.get("D1", {})
        elif code == "META":
            return self.data.get("meta", {})
        elif code == "DASHA":
            return self.data.get("dasha", {})
        elif code.startswith("D"):
            # Check d_series for D2-D144
            d_series = self.data.get("d_series", {})
            return d_series.get(code, {})
        else:
            return {"error": f"Unknown chart code: {code}"}

    def load_all_data(self) -> str:
        """
        Loads ALL valid data into a massive context string.
        """
        data_summary = []
        
        # 1. Essential Files
        meta = self.load_chart("META")
        d1 = self.load_chart("D1")
        dasha = self.load_chart("DASHA")
        
        data_summary.append(f"<Meta>{json.dumps(meta, default=str)}</Meta>")
        data_summary.append(f"<D1>{json.dumps(d1, default=str)}</D1>")
        data_summary.append(f"<Dasha>{json.dumps(dasha, default=str)}</Dasha>")
        
        # 2. Scan D-Series
        d_series = self.data.get("d_series", {})
        for key, val in d_series.items():
            data_summary.append(f"<{key}>{json.dumps(val, default=str)}</{key}>")
        
        return "\n".join(data_summary)

    def get_planet_details(self, chart_code: str, planet_name: str) -> Dict[str, Any]:
        """
        Finds specific planet details in a chart.
        """
        chart_data = self.load_chart(chart_code)
        if "error" in chart_data:
            return chart_data
            
        # Normalize planet name (e.g., "Sun" -> match "Sun☉" or just "Sun")
        target = planet_name.lower()
        
        # 1. Search in 'planets' list
        if "planets" in chart_data:
            for p in chart_data["planets"]:
                # user might say "Sun", json has "Sun☉"
                # distinct chars only?
                p_name_clean = ''.join([c for c in p["name"] if c.isalpha()]).lower()
                if target == p_name_clean or target in p["name"].lower():
                    return p
                    
        # 2. Check Ascendant (often in houses, not planet list in some schemas)
        if target == "ascendant" or target == "lagna":
             return {
                 "name": "Ascendant",
                 "sign": chart_data.get("ascendantSign", "Unknown"),
                 "house": 1
             }

        return {"error": f"Planet '{planet_name}' not found in {chart_code}"}

    def get_house_details(self, chart_code: str, house_number: int) -> Dict[str, Any]:
        """
        Get details of a specific house (Sign, Planets inside).
        """
        chart_data = self.load_chart(chart_code)
        if "error" in chart_data:
            return chart_data
            
        if "houses" not in chart_data:
             return {"error": "No house data found."}
             
        for house in chart_data["houses"]:
            if house["index"] == house_number:
                return house
                
        return {"error": f"House {house_number} not found."}
