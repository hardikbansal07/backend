from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional


SIGNS_ORDER = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SIGN_TO_INDEX = {name: idx for idx, name in enumerate(SIGNS_ORDER)}

NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]


def get(obj: Dict[str, Any], path: List[str]) -> Optional[Any]:
    cur: Any = obj
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def clean_lines(block: str) -> List[str]:
    if not block:
        return []
    parts = [p.strip() for p in block.split("\n")]
    return [p for p in parts if p]


def houses_to_dict(houses_list: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for i in range(12):
        items = clean_lines(houses_list[i] if i < len(houses_list) else "")
        out[str(i + 1)] = items
    return out


def parse_sign_and_dms(text: str) -> Dict[str, Any]:
    norm = (
        text.replace("’", "'")
        .replace("″", '"')
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
    )
    m = re.search(r"([A-Za-z]+)\s+(\d+)°\s*(\d+)[’']\s*(\d+)", norm)
    if not m:
        m = re.search(r"([A-Za-z]+)\s+(\d+)°\s*(\d+)", norm)
        if not m:
            raise ValueError(f"Could not parse sign/degrees from: {text}")
        sign = m.group(1)
        deg = int(m.group(2))
        minute = int(m.group(3))
        sec = 0
    else:
        sign = m.group(1)
        deg = int(m.group(2))
        minute = int(m.group(3))
        sec = int(m.group(4))
    if sign not in SIGN_TO_INDEX:
        raise ValueError(f"Unknown sign '{sign}' in: {text}")
    return {"sign": sign, "deg": deg, "min": minute, "sec": sec}


def absolute_longitude(sign: str, deg: int, minute: int, sec: int) -> float:
    base = SIGN_TO_INDEX[sign] * 30.0
    return base + deg + minute / 60.0 + sec / 3600.0


def nakshatra_from_longitude(lon: float) -> Dict[str, Any]:
    nk_len = 13.3333333333
    pada_len = nk_len / 4.0
    idx = int(lon // nk_len) % 27
    within = lon - (idx * nk_len)
    pada = int(within // pada_len) + 1
    return {"name": NAKSHATRA_NAMES[idx], "pada": pada}


def parse_planet_line(line: str) -> Dict[str, Any]:
    part, karaka = line, None
    mkar = re.search(r"\(([^)]+)\)", line)
    if mkar:
        karaka = mkar.group(1)
        part = line[: mkar.start()].strip()
    s = parse_sign_and_dms(part)
    lon = absolute_longitude(s["sign"], s["deg"], s["min"], s["sec"])
    nk = nakshatra_from_longitude(lon)
    data: Dict[str, Any] = {
        "sign": s["sign"],
        "degrees": f"{s['deg']}° {s['min']}' {s['sec']}\"",
        "longitude": round(lon, 6),
        "nakshatra": nk["name"],
        "pada": nk["pada"],
    }
    if karaka:
        data["karaka"] = karaka
    return data


def expand_abbrev(abbrev: str) -> str:
    mapping = {
        "Ascℒ": "Ascendantℒ",
        "Ra☊": "Raagu☊",
        "Ke☋": "Kethu☋",
        "Mo☾": "Moon☾",
        "Su☉": "Sun☉",
        "Me☿": "Mercury☿",
        "Ve♀": "Venus♀",
        "Ma♂℞": "Mars♂℞",
        "Ju♃": "Jupiter♃",
        "Sa♄": "Saturn♄",
        "Ne♆": "Neptune♆",
        "Pl♇": "Pluto♇",
        "Ur⛢": "Uranus⛢",
    }
    return mapping.get(abbrev, abbrev)


def planet_meta_from_key(key: str) -> Dict[str, Any]:
    # key examples: "Raasi-Sun☉", "Raasi-Mars♂℞", "Raasi-Jupiter♃"
    # Extract the tag after the prefix and collect glyphs + retrograde
    tag = key.split("Raasi-")[-1]
    # glyphs: any non-word, non-space characters
    glyphs = "".join(ch for ch in tag if not ch.isalnum() and not ch.isspace())
    symbol = glyphs[0] if glyphs else ""
    retro = ("℞" in glyphs) or ("℞" in tag) or ("Rx" in tag)
    return {"glyphs": glyphs, "symbol": symbol, "retrograde": retro}


def circular_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def select_root(block: Dict[str, Any]) -> Dict[str, Any]:
    # PyJHora-style JSON usually nests data under top['primary']
    return block.get("primary") or block


def build_lagna(root: Dict[str, Any]) -> Dict[str, Any]:
    horoscope_info: Dict[str, str] = root.get("horoscope_info", {})
    asc_line = horoscope_info.get("Raasi-Ascendantℒ")
    if not asc_line:
        raise KeyError("Missing 'Raasi-Ascendantℒ' in horoscope_info")

    asc_parsed = parse_sign_and_dms(asc_line)
    asc_lon = absolute_longitude(asc_parsed["sign"], asc_parsed["deg"], asc_parsed["min"], asc_parsed["sec"])
    asc_nk = nakshatra_from_longitude(asc_lon)
    ascendant = {
        "sign": asc_parsed["sign"],
        "degrees": f"{asc_parsed['deg']}° {asc_parsed['min']}' {asc_parsed['sec']}\"",
        "longitude": round(asc_lon, 6),
        "nakshatra": asc_nk["name"],
        "pada": asc_nk["pada"],
    }

    # Special lagnas
    special_keys = [
        "Raasi-Bhava Lagna (BL)",
        "Raasi-Hora Lagna (HL)",
        "Raasi-Ghati Lagna (GL)",
        "Raasi-Vighati Lagna (VL)",
        "Raasi-Pranapada Lagna (PL)",
        "Raasi-Indu Lagna (IL)",
        "Raasi-Bhrigu Bindhu Lagna (BB)",
        "Raasi-Kunda Lagna (KL)",
        "Raasi-Sree Lagna (SL)",
        "Raasi-Varnada Lagna",
        "Raasi-Maandhi (Md)",
    ]
    special_lagnas = {key.replace("Raasi-", ""): horoscope_info.get(key) for key in special_keys if key in horoscope_info}

    # Arudha padas from D1
    arudha_keys = [
        "D-1-Arudha Lagna (AL)",
        "D-1-Dhanarudha (A2)",
        "D-1-Bhatrarudha (A3)",
        "D-1-Matri Pada (A4)",
        "D-1-Mantra Pada (A5)",
        "D-1-Roga Pada (A6)",
        "D-1-Dara Pada (A7)",
        "D-1-Mrityu Pada (A8)",
        "D-1-Bhagya Pada (A9)",
        "D-1-Karma Pada (A10)",
        "D-1-Labha Pada (A11)",
        "D-1-Upapada Lagna (UL)",
    ]
    arudha_padas = {key.replace("D-1-", ""): horoscope_info.get(key) for key in arudha_keys if key in horoscope_info}

    # Planets
    planet_map = {
        "Sun": "Raasi-Sun☉",
        "Moon": "Raasi-Moon☾",
        "Mars": "Raasi-Mars♂℞",
        "Mercury": "Raasi-Mercury☿",
        "Jupiter": "Raasi-Jupiter♃",
        "Venus": "Raasi-Venus♀",
        "Saturn": "Raasi-Saturn♄",
        "Rahu": "Raasi-Raagu☊",
        "Ketu": "Raasi-Kethu☋",
        "Uranus": "Raasi-Uranus⛢",
        "Neptune": "Raasi-Neptune♆",
        "Pluto": "Raasi-Pluto♇",
    }
    planets: List[Dict[str, Any]] = []

    # Compute Sun longitude first for combustion checks
    sun_line = horoscope_info.get(planet_map["Sun"]) or ""
    sun_lon = None
    if sun_line:
        sun_parsed = parse_planet_line(sun_line)
        sun_lon = sun_parsed.get("longitude")

    # Typical combustion thresholds (degrees) in Vedic practice
    combust_thresholds = {
        "Mercury": 12.0,
        "Venus": 10.0,
        "Mars": 17.0,
        "Jupiter": 11.0,
        "Saturn": 15.0,
        # Moon often considered within 12° as 'asta' influence; include flag for completeness
        "Moon": 12.0,
        # No combustion for Rahu, Ketu, Uranus, Neptune, Pluto, and Sun itself
    }
    for pname, key in planet_map.items():
        if key in horoscope_info:
            raw = horoscope_info[key]
            pdata = parse_planet_line(raw)
            meta = planet_meta_from_key(key)
            pdata["name"] = pname
            pdata["symbol"] = meta.get("symbol")
            pdata["glyphs"] = meta.get("glyphs")
            pdata["retrograde"] = meta.get("retrograde")
            pdata["raw"] = raw
            # Combust check where applicable and sun_lon available
            if sun_lon is not None and pname in combust_thresholds:
                sep = circular_sep(pdata["longitude"], sun_lon)
                thr = combust_thresholds[pname]
                pdata["combust"] = sep <= thr
                pdata["combust_sep_deg"] = round(sep, 3)
                pdata["combust_threshold_deg"] = thr
            planets.append(pdata)

    # Sensitive points (Upagrahas etc.)
    sensitive_keys = [
        "Raasi-kaala (Kl)",
        "Raasi-Mrithyu (Mr)",
        "Raasi-Artha Praharaka (Ap)",
        "Raasi-Yama Ghantaka (Yg)",
        "Raasi-Gulika (Gk)",
        "Raasi-Dhuma (Dm)",
        "Raasi-Vyathipatha (Vp)",
        "Raasi-Parivesha (Pv)",
        "Raasi-Indrachapa (Ic)",
        "Raasi-Upakethu (Uk)",
    ]
    sensitive_points = {key.replace("Raasi-", ""): horoscope_info.get(key) for key in sensitive_keys if key in horoscope_info}

    # Houses from charts.bhava.details if present
    charts = root.get("charts", {})
    bhava = charts.get("bhava", {}) if isinstance(charts, dict) else {}
    house_rows: List[List[str]] = bhava.get("details", []) if isinstance(bhava, dict) else []
    houses: List[Dict[str, Any]] = []
    for row in house_rows:
        if not row or len(row) < 4:
            continue
        hnum, start, mid, end = row[0], row[1], row[2], row[3]
        occ = clean_lines(row[4]) if len(row) > 4 else []
        occ_full = [expand_abbrev(o) for o in occ]
        houses.append({
            "house": hnum,
            "start": start,
            "mid": mid,
            "end": end,
            "occupants": occ_full,
        })

    return {
        "ascendant": ascendant,
        "special_lagnas": special_lagnas,
        "arudha_padas": arudha_padas,
        "planets": planets,
        "houses": houses,
        "sensitive_points": sensitive_points,
    }


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def convert_core(input_path: str, output_root: str, name: Optional[str] = None) -> str:
    with open(input_path, "r", encoding="utf-8") as f:
        core = json.load(f)

    root = select_root(core)
    # Determine person name
    if not name:
        base = os.path.splitext(os.path.basename(input_path))[0]
        name = base

    person_dir = os.path.join(output_root, name)

    # 1) Build lagna.json
    lagna = build_lagna(root)
    write_json(os.path.join(person_dir, "lagna.json"), lagna)

    # 2) Build D-series files from charts.varga_charts (if available)
    charts = root.get("charts", {})
    vargas = charts.get("varga_charts") if isinstance(charts, dict) else None
    if isinstance(vargas, list):
        dseries_dir = os.path.join(person_dir, "dseries")
        os.makedirs(dseries_dir, exist_ok=True)
        for item in vargas:
            label = item.get("label", "")
            m = re.search(r"\(D(\d+)\)", label)
            if not m:
                continue
            dnum = m.group(1)
            if dnum == "1":
                continue
            houses_list = item.get("houses", [])
            data = {"label": label, "houses": houses_to_dict(houses_list)}
            write_json(os.path.join(dseries_dir, f"d{dnum}.json"), data)
    else:
        # No varga charts present; skip D-series generation
        pass

    return person_dir


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Convert a PyJHora-like core JSON into structured per-person files.")
    parser.add_argument("--input", required=True, help="Path to the core JSON file (e.g., input/manu.json)")
    parser.add_argument("--output", default="input", help="Root folder to place the person directory (default: input)")
    parser.add_argument("--name", default=None, help="Person subfolder name (default: input file stem)")
    args = parser.parse_args(argv)

    out_dir = convert_core(args.input, args.output, args.name)
    print(f"Converted to: {out_dir}")


if __name__ == "__main__":
    main()
