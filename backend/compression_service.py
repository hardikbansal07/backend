"""
Horoscope Compression Service
Converts full horoscope output into compressed two-layer format
"""
import json
import re
from typing import Dict, Any, List, Optional

# Planet and Sign Mappings
PLANET_NAMES = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Merc", 4: "Jup", 
    5: "Ven", 6: "Sat", 7: "Rahu", 8: "Ketu", 9: "Asc",
    10: "Uran", 11: "Nept", 12: "Plu"
}

SIGN_NAMES = {
    1: "Ari", 2: "Tau", 3: "Gem", 4: "Can", 5: "Leo", 6: "Vir",
    7: "Lib", 8: "Sco", 9: "Sag", 10: "Cap", 11: "Aqu", 12: "Pis"
}

SIGN_MAP_FROM_STR = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4, "Leo": 5, "Virgo": 6,
    "Libra": 7, "Scorpio": 8, "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
}

def get_sign_id(sign_str: str) -> int:
    """Convert sign string to ID"""
    clean_sign = re.sub(r"[^a-zA-Z]", "", sign_str)
    for key, val in SIGN_MAP_FROM_STR.items():
        if key in clean_sign:
            return val
    return 0

def get_planet_name(p_data: Dict[str, Any]) -> str:
    """Extract and normalize planet name"""
    name = p_data.get("name", "")
    clean_name = re.sub(r"[^a-zA-Z]", "", name)
    
    if "Sun" in clean_name: return "Sun"
    if "Moon" in clean_name: return "Moon"
    if "Mars" in clean_name: return "Mars"
    if "Mercury" in clean_name: return "Merc"
    if "Jupiter" in clean_name: return "Jup"
    if "Venus" in clean_name: return "Ven"
    if "Saturn" in clean_name: return "Sat"
    if "Raagu" in clean_name or "Rahu" in clean_name: return "Rahu"
    if "Kethu" in clean_name or "Ketu" in clean_name: return "Ketu"
    if "Ascendant" in clean_name: return "Asc"
    if "Uranus" in clean_name: return "Uran"
    if "Neptune" in clean_name: return "Nept"
    if "Pluto" in clean_name: return "Pluto"
    
    return clean_name

def get_sign_name(sign_num: int) -> str:
    """Get sign abbreviation"""
    return SIGN_NAMES.get(sign_num, str(sign_num))

def round_float(val: Any) -> Any:
    """Round float values to 2 decimals"""
    if isinstance(val, (int, float)):
        return round(val, 2)
    return val

def clean_calendar_value(val: Any) -> Any:
    """Clean calendar string values"""
    if isinstance(val, str):
        val = val.split(" starts at")[0].split(" ends at")[0].split(" from")[0]
        val = re.sub(r'[^\x00-\x7F]+', '', val)
        return val.strip()
    return val

def compress_planet(p_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Compress planet data to minimal readable format"""
    if not p_data:
        return None
    
    name = get_planet_name(p_data)
    if not name:
        return None

    comp_p = {
        "name": name,
        "house": p_data.get("house"),
        "sign": get_sign_name(get_sign_id(p_data.get("sign", ""))),
        "deg": round_float(p_data.get("rawLongitudeDeg", 0))
    }

    # Nakshatra
    nak = p_data.get("nakshatra")
    pada = p_data.get("nakshatraPada")
    if nak:
        comp_p["nak"] = f"{nak}-{pada}" if pada else nak

    # Boolean flags (only if True)
    if p_data.get("retrograde"):
        comp_p["retrograde"] = True
    if p_data.get("isCombust"):
        comp_p["combust"] = True
    if p_data.get("isExalted"):
        comp_p["exalted"] = True
    if p_data.get("isDebilitated"):
        comp_p["debilitated"] = True
    if p_data.get("isOwnSign"):
        comp_p["own_sign"] = True
    if p_data.get("isMoolatrikona"):
        comp_p["moolatrikona"] = True
    if p_data.get("isVargottama"):
        comp_p["vargottama"] = True
    
    # Chara Karaka
    chara = p_data.get("charaKaraka")
    if chara:
        comp_p["charaKaraka"] = chara
        
    return comp_p

def compress_chart(chart_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Compress chart data"""
    if not chart_data:
        return None

    label = chart_data.get("label", "")
    asc_sign_num = chart_data.get("ascendantSignNumber", 0)
    
    compressed_chart = {
        "label": label,
        "asc_sign": get_sign_name(asc_sign_num),
        "asc_deg": round_float(chart_data.get("ascendantRawLongitudeDeg", 0)),
        "planets": []
    }

    for p in chart_data.get("planets", []):
        cp = compress_planet(p)
        if cp:
            compressed_chart["planets"].append(cp)

    return compressed_chart

def process_dasha_2layer(dasha_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process Dasha data with 2-layer depth (Mahadasha + Antardasha only)"""
    if not dasha_data or "vimsottari" not in dasha_data:
        return None

    vim = dasha_data["vimsottari"]
    compressed_dasha = {
        "system": "Vimsottari",
        "periods": []
    }

    # Loop over Mahadashas
    for md in vim.get("periods", []):
        comp_md = {
            "lord": md.get("lord"),
            "start": md.get("start"),
            "antardasha": []
        }
        
        # Loop over Antardashas (2-layer limit)
        for ad in md.get("antardasha", []):
            comp_ad = {
                "lord": ad.get("lord"),
                "start": ad.get("start")
            }
            comp_md["antardasha"].append(comp_ad)
            
        compressed_dasha["periods"].append(comp_md)

    return compressed_dasha

def compress_horoscope(data: Dict[str, Any], birth_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main compression function
    Converts full horoscope data into compressed chunks
    
    Args:
        data: Full horoscope calculation output
        birth_details: Optional dict with birth info (date_of_birth, time_of_birth, place_of_birth, latitude, longitude)
    
    Returns:
        Compressed horoscope data with meta, lagna, dasha, and d_series
    """
    compressed = {
        "meta": {},
        "lagna": None,
        "dasha": None,
        "d_series": {}
    }

    # 1. Meta + Calendar
    if "meta" in data:
        compressed["meta"].update(data["meta"])
    if "calendar" in data:
        clean_cal = {k: clean_calendar_value(v) for k, v in data["calendar"].items()}
        compressed["meta"]["calendar"] = clean_cal
    
    # 1.5. Add birth details to meta if provided
    if birth_details:
        compressed["meta"]["name"] = birth_details.get("name")
        compressed["meta"]["gender"] = birth_details.get("gender")
        compressed["meta"]["birth_date"] = birth_details.get("date_of_birth")
        compressed["meta"]["birth_time"] = birth_details.get("time_of_birth")
        compressed["meta"]["birth_place"] = birth_details.get("place_of_birth")
        compressed["meta"]["latitude"] = birth_details.get("latitude")
        compressed["meta"]["longitude"] = birth_details.get("longitude")

    # 2. Lagna (Rasi Chart / D1)
    if "rasiChart" in data:
        compressed["lagna"] = compress_chart(data["rasiChart"])

    # 3. Dasha (2-layer)
    if "dasha" in data:
        compressed["dasha"] = process_dasha_2layer(data["dasha"])

    # 4. D-Series (Divisional Charts)
    for chart in data.get("divisionalCharts", []):
        label = chart.get("label", "Unknown")
        if label == "Raasi":
            continue  # Already in lagna
        
        match = re.search(r"D-(\d+)", label)
        if match:
            key = f"D{match.group(1)}"
        else:
            safe_label = re.sub(r"[^a-zA-Z0-9]", "_", label)
            key = safe_label
        
        compressed["d_series"][key] = compress_chart(chart)

    return compressed

def split_into_chunks(compressed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Split compressed data into storage chunks
    Returns list of chunks for MongoDB storage
    """
    chunks = []
    
    # Chunk 1: Meta
    chunks.append({
        "chunk_type": "meta",
        "data": compressed_data.get("meta", {})
    })
    
    # Chunk 2: Lagna
    if compressed_data.get("lagna"):
        chunks.append({
            "chunk_type": "lagna",
            "data": compressed_data["lagna"]
        })
    
    # Chunk 3: Dasha
    if compressed_data.get("dasha"):
        chunks.append({
            "chunk_type": "dasha",
            "data": compressed_data["dasha"]
        })
    
    # Chunks 4+: D-Series (one chunk per divisional chart)
    for d_key, d_data in compressed_data.get("d_series", {}).items():
        chunks.append({
            "chunk_type": "divisional",
            "chart_name": d_key,
            "data": d_data
        })
    
    return chunks
