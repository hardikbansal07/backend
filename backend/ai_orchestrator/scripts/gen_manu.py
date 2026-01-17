import json
import os
import re
from typing import List, Dict, Any


# This script generates input/manu/dseries/*.json and input/manu/lagna.json
# from the provided horoscope_info, varga_charts and bhava data pasted below.


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def clean_lines(block: str) -> List[str]:
    if not block:
        return []
    parts = [p.strip() for p in block.split("\n")]
    return [p for p in parts if p]


def houses_to_dict(houses_list: List[str]) -> Dict[str, List[str]]:
    # Convert a list of 12 strings (with newlines) into {"1": [...], ..., "12": [...]}
    out: Dict[str, List[str]] = {}
    for i in range(12):
        items = clean_lines(houses_list[i] if i < len(houses_list) else "")
        out[str(i + 1)] = items
    return out


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


def parse_sign_and_dms(text: str) -> Dict[str, Any]:
    # Normalize curly quotes and symbols
    norm = text.replace("’", "'").replace("″", '"').replace("“", '"').replace("”", '"')
    # Extract sign word and DMS
    # Examples: "♏︎Scorpio 14° 42’ 2\"" or "♒︎Aquarius 0° 8’ 51\""
    m = re.search(r"([A-Za-z]+)\s+(\d+)°\s*(\d+)[’']\s*(\d+)", norm)
    if not m:
        # Sometimes there may be degree without seconds, handle minimal case
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
        raise ValueError(f"Unknown sign name '{sign}' in: {text}")
    return {"sign": sign, "deg": deg, "min": minute, "sec": sec}


def absolute_longitude(sign: str, deg: int, minute: int, sec: int) -> float:
    base = SIGN_TO_INDEX[sign] * 30.0
    return base + deg + minute / 60.0 + sec / 3600.0


def nakshatra_from_longitude(lon: float) -> Dict[str, Any]:
    # 1 nakshatra = 13°20' = 13.333333...
    nk_len = 13.3333333333
    pada_len = nk_len / 4.0  # 3°20' = 3.3333333
    idx = int(lon // nk_len) % 27
    within = lon - (idx * nk_len)
    pada = int(within // pada_len) + 1
    return {"name": NAKSHATRA_NAMES[idx], "pada": pada}


def parse_planet_line(line: str) -> Dict[str, Any]:
    # e.g. "♏︎Scorpio 14° 42’ 2\" (Bhratri Karaka)"
    part, karaka = line, None
    mkar = re.search(r"\(([^)]+)\)", line)
    if mkar:
        karaka = mkar.group(1)
        part = line[: mkar.start()].strip()
    s = parse_sign_and_dms(part)
    lon = absolute_longitude(s["sign"], s["deg"], s["min"], s["sec"])
    nk = nakshatra_from_longitude(lon)
    return {
        "sign": s["sign"],
        "degrees": f"{s['deg']}° {s['min']}' {s['sec']}\"",
        "longitude": round(lon, 6),
        "nakshatra": nk["name"],
        "pada": nk["pada"],
        **({"karaka": karaka} if karaka else {}),
    }


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


# ----------------- Input data pasted from user -----------------

horoscope_info = {
    "D-1-Arudha Lagna (AL)": "♏︎Scorpio",
    "D-1-Dhanarudha (A2)": "♊︎Gemini",
    "D-1-Bhatrarudha (A3)": "♌︎Leo",
    "D-1-Matri Pada (A4)": "♓︎Pisces",
    "D-1-Mantra Pada (A5)": "♈Aries",
    "D-1-Roga Pada (A6)": "♍︎Virgo",
    "D-1-Dara Pada (A7)": "♏︎Scorpio",
    "D-1-Mrityu Pada (A8)": "♑︎Capricorn",
    "D-1-Bhagya Pada (A9)": "♋︎Cancer",
    "D-1-Karma Pada (A10)": "♒︎Aquarius",
    "D-1-Labha Pada (A11)": "♍︎Virgo",
    "D-1-Upapada Lagna (UL)": "♓︎Pisces",
    "Raasi-Bhava Lagna (BL)": "♒︎Aquarius 2° 19’ 31\"",
    "Raasi-Hora Lagna (HL)": "♈Aries 19° 56’ 11\"",
    "Raasi-Ghati Lagna (GL)": "♐︎Sagittarius 12° 46’ 11\"",
    "Raasi-Vighati Lagna (VL)": "♎︎Libra 21° 22’ 53\"",
    "Raasi-Pranapada Lagna (PL)": "♏︎Scorpio 5° 36’ 2\"",
    "Raasi-Indu Lagna (IL)": "♑︎Capricorn 11° 27’ 42\"",
    "Raasi-Bhrigu Bindhu Lagna (BB)": "♉︎Taurus 9° 44’ 21\"",
    "Raasi-Kunda Lagna (KL)": "♎︎Libra 11° 56’ 20\"",
    "Raasi-Sree Lagna (SL)": "♐︎Sagittarius 9° 36’ 45\"",
    "Raasi-Varnada Lagna": "♓︎Pisces 0° 8’ 51\"",
    "Raasi-Maandhi (Md)": "♏︎Scorpio 24° 10’ 0\"",
    "Raasi-Ascendantℒ": "♒︎Aquarius 0° 8’ 51\"",
    "Raasi-Sun☉": "♏︎Scorpio 14° 42’ 2\" (Bhratri Karaka)",
    "Raasi-Moon☾": "♌︎Leo 11° 27’ 42\" (Pitri Karaka)",
    "Raasi-Mars♂℞": "♊︎Gemini 16° 41’ 48\" (Amatya Karaka)",
    "Raasi-Mercury☿": "♏︎Scorpio 5° 38’ 40\" (Putra Karaka)",
    "Raasi-Jupiter♃": "♐︎Sagittarius 2° 3’ 57\" (Jnaati Karaka)",
    "Raasi-Venus♀": "♎︎Libra 1° 2’ 35\" (Dhatha Karaka)",
    "Raasi-Saturn♄": "♌︎Leo 14° 18’ 14\" (Maitra Karaka)",
    "Raasi-Raagu☊": "♒︎Aquarius 8° 1’ 0\" (Atma Karaka)",
    "Raasi-Kethu☋": "♌︎Leo 8° 1’ 0\"",
    "Raasi-Uranus⛢": "♒︎Aquarius 20° 50’ 26\"",
    "Raasi-Neptune♆": "♑︎Capricorn 25° 33’ 30\"",
    "Raasi-Pluto♇": "♐︎Sagittarius 4° 4’ 6\"",
    "Raasi-kaala (Kl)": "♑︎Capricorn 4° 21’ 4\"",
    "Raasi-Mrithyu (Mr)": "♒︎Aquarius 21° 16’ 59\"",
    "Raasi-Artha Praharaka (Ap)": "♓︎Pisces 16° 48’ 2\"",
    "Raasi-Yama Ghantaka (Yg)": "♈Aries 11° 32’ 55\"",
    "Raasi-Gulika (Gk)": "♏︎Scorpio 14° 28’ 45\"",
    "Raasi-Dhuma (Dm)": "♓︎Pisces 28° 2’ 2\"",
    "Raasi-Vyathipatha (Vp)": "♈Aries 1° 57’ 58\"",
    "Raasi-Parivesha (Pv)": "♎︎Libra 1° 57’ 58\"",
    "Raasi-Indrachapa (Ic)": "♍︎Virgo 28° 2’ 2\"",
    "Raasi-Upakethu (Uk)": "♎︎Libra 14° 42’ 2\"",
}


# Varga charts (D1..D144) houses — only used to generate D-series files
varga_charts = [
    {"index": 0, "varga_factor": 1, "label": "Raasi (D1)", "houses": [
        "",
        "",
        "Mars♂℞\n",
        "",
        "Moon☾\nSaturn♄\nKethu☋\n",
        "",
        "Venus♀\n",
        "Sun☉\nMercury☿\n",
        "Jupiter♃\nPluto♇\n",
        "Neptune♆\n",
        "Ascendantℒ\nRaagu☊\nUranus⛢\n",
        ""
    ]},
    {"index": 1, "varga_factor": 2, "label": "Hora (D2)", "houses": [
        "Venus♀\n",
        "",
        "",
        "Sun☉\nMercury☿\n",
        "Jupiter♃\nPluto♇\n",
        "Mars♂℞\n",
        "Neptune♆\n",
        "",
        "Ascendantℒ\nMoon☾\nSaturn♄\nRaagu☊\nKethu☋\n",
        "Uranus⛢\n",
        "",
        ""
    ]},
    {"index": 2, "varga_factor": 3, "label": "Dhrekana (D3)", "houses": [
        "",
        "",
        "",
        "",
        "Kethu☋\n",
        "Neptune♆\n",
        "Mars♂℞\nVenus♀\nUranus⛢\n",
        "Mercury☿\n",
        "Moon☾\nJupiter♃\nSaturn♄\nPluto♇\n",
        "",
        "Ascendantℒ\nRaagu☊\n",
        "Sun☉\n"
    ]},
    {"index": 3, "varga_factor": 4, "label": "Chaturthamsa (D4)", "houses": [
        "",
        "Raagu☊\n",
        "",
        "",
        "Uranus⛢\n",
        "",
        "Venus♀\nNeptune♆\n",
        "Moon☾\nMercury☿\nSaturn♄\nKethu☋\n",
        "Mars♂℞\nJupiter♃\nPluto♇\n",
        "",
        "Ascendantℒ\nSun☉\n",
        ""
    ]},
    {"index": 4, "varga_factor": 5, "label": "Panchamsa (D5)", "houses": [
        "Ascendantℒ\nJupiter♃\nVenus♀\nPluto♇\n",
        "Mercury☿\n",
        "Uranus⛢\n",
        "",
        "",
        "",
        "",
        "Neptune♆\n",
        "Mars♂℞\nSaturn♄\n",
        "",
        "Moon☾\nRaagu☊\nKethu☋\n",
        "Sun☉\n"
    ]},
    {"index": 5, "varga_factor": 6, "label": "Shashthamsa (D6)", "houses": [
        "Ascendantℒ\nJupiter♃\nVenus♀\nPluto♇\n",
        "Raagu☊\nKethu☋\n",
        "Moon☾\nSaturn♄\n",
        "Mars♂℞\n",
        "Uranus⛢\n",
        "",
        "",
        "Mercury☿\n",
        "Sun☉\n",
        "",
        "",
        "Neptune♆\n"
    ]},
    {"index": 6, "varga_factor": 7, "label": "Sapthamsa (D7)", "houses": [
        "",
        "",
        "Mercury☿\nUranus⛢\n",
        "",
        "Sun☉\n",
        "Mars♂℞\nKethu☋\n",
        "Moon☾\nVenus♀\n",
        "Saturn♄\n",
        "Jupiter♃\nNeptune♆\nPluto♇\n",
        "",
        "Ascendantℒ\n",
        "Raagu☊\n"
    ]},
    {"index": 7, "varga_factor": 8, "label": "Ashtamsa (D8)", "houses": [
        "Venus♀\n",
        "Uranus⛢\n",
        "",
        "",
        "Jupiter♃\n",
        "Pluto♇\n",
        "Neptune♆\n",
        "",
        "Ascendantℒ\nMars♂℞\n",
        "Mercury☿\n",
        "Raagu☊\nKethu☋\n",
        "Sun☉\nMoon☾\nSaturn♄\n"
    ]},
    {"index": 8, "varga_factor": 9, "label": "Navamsam (D9)", "houses": [
        "Jupiter♃\nUranus⛢\n",
        "Pluto♇\n",
        "Kethu☋\n",
        "Moon☾\n",
        "Mercury☿\nSaturn♄\nNeptune♆\n",
        "",
        "Ascendantℒ\nVenus♀\n",
        "Sun☉\n",
        "Raagu☊\n",
        "",
        "",
        "Mars♂℞\n"
    ]},
    {"index": 9, "varga_factor": 10, "label": "Dhasamsa (D10)", "houses": [
        "Raagu☊\n",
        "Neptune♆\n",
        "",
        "",
        "Mercury☿\nUranus⛢\n",
        "",
        "Venus♀\nKethu☋\n",
        "Sun☉\nMoon☾\nMars♂℞\n",
        "Jupiter♃\nSaturn♄\n",
        "Pluto♇\n",
        "Ascendantℒ\n",
        ""
    ]},
    {"index": 10, "varga_factor": 11, "label": "Rudramsa (D11)", "houses": [
        "Moon☾\nNeptune♆\n",
        "Saturn♄\n",
        "Ascendantℒ\n",
        "",
        "Mars♂℞\nJupiter♃\nRaagu☊\n",
        "Pluto♇\n",
        "Venus♀\n",
        "Mercury☿\n",
        "",
        "Uranus⛢\n",
        "Sun☉\nKethu☋\n",
        ""
    ]},
    {"index": 11, "varga_factor": 12, "label": "Dhwadhamsa (D12)", "houses": [
        "Sun☉\n",
        "Raagu☊\n",
        "",
        "",
        "",
        "",
        "Venus♀\nUranus⛢\n",
        "Kethu☋\nNeptune♆\n",
        "Moon☾\nMars♂℞\nJupiter♃\n",
        "Mercury☿\nSaturn♄\nPluto♇\n",
        "Ascendantℒ\n",
        ""
    ]},
    {"index": 12, "varga_factor": 16, "label": "Shodamsa (D16)", "houses": [
        "Venus♀\n",
        "Neptune♆\n",
        "",
        "Uranus⛢\n",
        "Ascendantℒ\nMars♂℞\n",
        "",
        "",
        "Mercury☿\n",
        "Raagu☊\nKethu☋\n",
        "Jupiter♃\n",
        "Moon☾\nPluto♇\n",
        "Sun☉\nSaturn♄\n"
    ]},
    {"index": 13, "varga_factor": 20, "label": "Vimsamsa (D20)", "houses": [
        "Venus♀\n",
        "Raagu☊\nKethu☋\n",
        "",
        "Moon☾\nMars♂℞\n",
        "",
        "Sun☉\nJupiter♃\nSaturn♄\nNeptune♆\n",
        "Pluto♇\n",
        "",
        "Ascendantℒ\n",
        "Uranus⛢\n",
        "",
        "Mercury☿\n"
    ]},
    {"index": 14, "varga_factor": 24, "label": "Chaturvimsamsa (D24)", "houses": [
        "",
        "Moon☾\n",
        "Sun☉\n",
        "Saturn♄\n",
        "Ascendantℒ\nVenus♀\n",
        "Mars♂℞\nJupiter♃\n",
        "",
        "Mercury☿\nPluto♇\n",
        "Uranus⛢\n",
        "",
        "Raagu☊\nKethu☋\n",
        "Neptune♆\n"
    ]},
    {"index": 15, "varga_factor": 27, "label": "Nakshatramsa (D27)", "houses": [
        "Saturn♄\nUranus⛢\n",
        "Jupiter♃\nRaagu☊\n",
        "Mercury☿\nNeptune♆\n",
        "Pluto♇\n",
        "",
        "",
        "Ascendantℒ\nVenus♀\n",
        "Kethu☋\n",
        "",
        "Mars♂℞\n",
        "Sun☉\nMoon☾\n",
        ""
    ]},
    {"index": 16, "varga_factor": 30, "label": "Thrisamsa (D30)", "houses": [
        "Ascendantℒ\nJupiter♃\nVenus♀\nPluto♇\n",
        "",
        "Uranus⛢\n",
        "",
        "",
        "Mercury☿\n",
        "",
        "Neptune♆\n",
        "Moon☾\nMars♂℞\nSaturn♄\n",
        "",
        "Raagu☊\nKethu☋\n",
        "Sun☉\n"
    ]},
    {"index": 17, "varga_factor": 40, "label": "Khavedamsa (D40)", "houses": [
        "Ascendantℒ\n",
        "Sun☉\nMercury☿\nVenus♀\n",
        "Jupiter♃\n",
        "Moon☾\nUranus⛢\n",
        "Neptune♆\n",
        "Pluto♇\n",
        "",
        "Saturn♄\n",
        "",
        "",
        "Mars♂℞\nRaagu☊\nKethu☋\n",
        ""
    ]},
    {"index": 18, "varga_factor": 45, "label": "Akshavedamsa (D45)", "houses": [
        "Mercury☿\n",
        "Venus♀\nSaturn♄\n",
        "Sun☉\nNeptune♆\nPluto♇\n",
        "",
        "Ascendantℒ\nRaagu☊\nKethu☋\n",
        "",
        "",
        "",
        "",
        "Moon☾\nMars♂℞\n",
        "",
        "Jupiter♃\nUranus⛢\n"
    ]},
    {"index": 19, "varga_factor": 60, "label": "Sashtiamsa (D60)", "houses": [
        "Sun☉\nJupiter♃\nNeptune♆\n",
        "",
        "Moon☾\nRaagu☊\n",
        "Uranus⛢\n",
        "Pluto♇\n",
        "",
        "Mercury☿\n",
        "",
        "Venus♀\nSaturn♄\nKethu☋\n",
        "",
        "Ascendantℒ\n",
        "Mars♂℞\n"
    ]},
    {"index": 20, "varga_factor": 81, "label": "Nava-Navamsa (D81)", "houses": [
        "",
        "",
        "Saturn♄\nUranus⛢\n",
        "Mars♂℞\nRaagu☊\n",
        "",
        "Jupiter♃\n",
        "Ascendantℒ\nSun☉\nMoon☾\nMercury☿\nNeptune♆\n",
        "",
        "Venus♀\n",
        "Kethu☋\n",
        "Pluto♇\n",
        ""
    ]},
    {"index": 21, "varga_factor": 108, "label": "Ashtotharamsa (D108)", "houses": [
        "Mercury☿\nRaagu☊\nNeptune♆\n",
        "",
        "",
        "Uranus⛢\nPluto♇\n",
        "",
        "",
        "Ascendantℒ\nKethu☋\n",
        "Jupiter♃\nSaturn♄\n",
        "Moon☾\n",
        "Venus♀\n",
        "",
        "Sun☉\nMars♂℞\n"
    ]},
    {"index": 22, "varga_factor": 144, "label": "Dwadas-Dwadasamsa (D144)", "houses": [
        "Mercury☿\n",
        "",
        "",
        "Moon☾\nRaagu☊\n",
        "Mars♂℞\nPluto♇\n",
        "Jupiter♃\nSaturn♄\n",
        "",
        "",
        "",
        "Kethu☋\nNeptune♆\n",
        "Ascendantℒ\nSun☉\nUranus⛢\n",
        "Venus♀\n"
    ]},
]


bhava_details = [
    ["House-1", "Cp 15° 7’ 39\"", "Aq 0° 7’ 39\"", "Aq 15° 7’ 39\"", "Ascℒ\nRa☊\nNe♆"],
    ["House-2", "Aq 15° 7’ 39\"", "Pi 0° 7’ 39\"", "Pi 15° 7’ 39\"", "Ur⛢"],
    ["House-3", "Pi 15° 7’ 39\"", "Ar 0° 7’ 39\"", "Ar 15° 7’ 39\"", ""],
    ["House-4", "Ar 15° 7’ 39\"", "Ta 0° 7’ 39\"", "Ta 15° 7’ 39\"", ""],
    ["House-5", "Ta 15° 7’ 39\"", "Ge 0° 7’ 39\"", "Ge 15° 7’ 39\"", ""],
    ["House-6", "Ge 15° 7’ 39\"", "Cn 0° 7’ 39\"", "Cn 15° 7’ 39\"", "Ma♂℞"],
    ["House-7", "Cn 15° 7’ 39\"", "Le 0° 7’ 39\"", "Le 15° 7’ 39\"", "Mo☾\nSa♄\nKe☋"],
    ["House-8", "Le 15° 7’ 39\"", "Vi 0° 7’ 39\"", "Vi 15° 7’ 39\"", ""],
    ["House-9", "Vi 15° 7’ 39\"", "Li 0° 7’ 39\"", "Li 15° 7’ 39\"", "Ve♀"],
    ["House-10", "Li 15° 7’ 39\"", "Sc 0° 7’ 39\"", "Sc 15° 7’ 39\"", "Su☉\nMe☿"],
    ["House-11", "Sc 15° 7’ 39\"", "Sg 0° 7’ 39\"", "Sg 15° 7’ 39\"", "Ju♃\nPl♇"],
    ["House-12", "Sg 15° 7’ 39\"", "Cp 0° 7’ 39\"", "Cp 15° 7’ 39\"", ""],
]


def generate_dseries(base_dir: str) -> None:
    dseries_dir = os.path.join(base_dir, "input", "manu", "dseries")
    ensure_dir(dseries_dir)
    for item in varga_charts:
        label = item.get("label", "")
        # skip D1 (we keep D1 info in lagna.json)
        m = re.search(r"\(D(\d+)\)", label)
        if not m:
            continue
        dnum = m.group(1)
        if dnum == "1":
            continue
        filename = f"d{dnum}.json"
        content = {
            "label": label,
            "houses": houses_to_dict(item.get("houses", [])),
        }
        with open(os.path.join(dseries_dir, filename), "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)


def generate_lagna(base_dir: str) -> None:
    lagna_path = os.path.join(base_dir, "input", "manu", "lagna.json")
    ensure_dir(os.path.dirname(lagna_path))

    # Ascendant
    asc_line = horoscope_info["Raasi-Ascendantℒ"]
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

    # Arudha padas (D1 only)
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

    # Planets with nakshatra/pada
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
    planets = []
    for pname, key in planet_map.items():
        if key not in horoscope_info:
            continue
        pdata = parse_planet_line(horoscope_info[key])
        pdata["name"] = pname
        planets.append(pdata)

    # Sensitive points
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

    # Houses by Bhava cusp + occupants
    houses = []
    for row in bhava_details:
        hnum = row[0]
        start, mid, end = row[1], row[2], row[3]
        occ = clean_lines(row[4]) if len(row) > 4 else []
        occ_full = [expand_abbrev(o) for o in occ]
        houses.append({
            "house": hnum,
            "start": start,
            "mid": mid,
            "end": end,
            "occupants": occ_full,
        })

    lagna = {
        "ascendant": ascendant,
        "special_lagnas": special_lagnas,
        "arudha_padas": arudha_padas,
        "planets": planets,
        "houses": houses,
        "sensitive_points": sensitive_points,
    }

    with open(lagna_path, "w", encoding="utf-8") as f:
        json.dump(lagna, f, ensure_ascii=False, indent=2)


def main():
    # Base is repo root where this script lives
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    generate_dseries(base_dir)
    generate_lagna(base_dir)
    print("Generated manu dseries and lagna.json")


if __name__ == "__main__":
    main()
