from datetime import datetime
from typing import List, Dict, Any, Annotated
from .vedic_utils import (
    get_varga_sign_name,
    get_nakshatra_pada,
    get_vimshottari_dasha_detailed,
    get_antardashas,
    get_planetary_dignity,
    get_jaimini_karakas,
    calculate_shadbala_heuristic,
    get_approx_transits,
    ZODIAC_SIGNS
)

# Constants for tools
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

def get_current_transits_report() -> Annotated[str, "Report on where Saturn, Jupiter, and Rahu are transiting TODAY"]:
    """
    Returns the current zodiac signs of major transiting planets (Saturn, Jupiter, Rahu).
    Use this to see if Saturn is transiting a natal moon (Sade Sati) or aspecting a Dasha lord.
    """
    now = datetime.now()
    transits = get_approx_transits(now)
    
    if isinstance(transits, str): return transits
    
    report = [f"TRANSIT SNAPSHOT ({now.strftime('%Y-%m-%d')}):"]
    for p, sign in transits.items():
        report.append(f"- {p} is transiting {sign}")
        
    return "\n".join(report)

def calculate_varga_positions(
    planet_positions: Annotated[Dict[str, float], "Dictionary of planet names to absolute degrees"]
) -> Annotated[str, "A formatted string report of D1 and D9 positions"]:
    """
    Calculates the Sign positions for D1 (Rashi) and D9 (Navamsa) for all planets.
    Useful for checking Vargottama and strength.
    """
    report = []
    for planet, deg in planet_positions.items():
        d1_sign = get_varga_sign_name(1, deg)
        d9_sign = get_varga_sign_name(9, deg)
        status = " (Vargottama!)" if d1_sign == d9_sign else ""
        report.append(f"{planet}: D1 {d1_sign} | D9 {d9_sign}{status}")
    return "\n".join(report)

def get_current_dasha(
    moon_degree: Annotated[float, "Absolute degree of the Moon in D1"],
    birth_year: int,
    birth_month: int,
    birth_day: int
) -> Annotated[str, "Report on the current Mahadasha and Antardashas"]:
    """
    Determines the current Mahadasha and lists the Antardashas for this period.
    """
    md = get_vimshottari_dasha_detailed(moon_degree, birth_year, birth_month, birth_day)
    if not md:
        return "Could not determine current Dasha. Date might be out of range."
    
    report = [f"Current Mahadasha: {md['Lord']}"]
    report.append(f"Period: {md['Start'].strftime('%Y-%m-%d')} to {md['End'].strftime('%Y-%m-%d')}")
    report.append("\nAntardashas (Sub-periods):")
    
    ads = get_antardashas(md['Lord'], md['Start'])
    now = datetime.now()
    
    for ad in ads:
        active = "**ACTIVE**" if ad['Start'] <= now < ad['End'] else ""
        report.append(f"- {ad['Lord']}: {ad['Start'].strftime('%Y-%m-%d')} -> {ad['End'].strftime('%Y-%m-%d')} {active}")
        
    return "\n".join(report)

def check_divisional_strength(
    planet: str,
    degree: float,
    varga_num: int
) -> Annotated[str, "The sign placement in the specific Varga chart"]:
    """
    Checks the placement of a specific planet in a specific Divisional Chart (D-Chart).
    Use varga_num=10 for Career (Dasamsa), varga_num=2 for Wealth (Hora), etc.
    """
    sign = get_varga_sign_name(varga_num, degree)
    return f"{planet} is in {sign} in the D{varga_num} chart."

def get_dignity_report(
    planet_positions: Annotated[Dict[str, float], "Dictionary of planet names to absolute degrees"]
) -> Annotated[str, "Report on Dignity (Exalted/Debilitated) for all planets"]:
    """
    Checks the dignity of all planets in the chart.
    """
    report = []
    for planet, deg in planet_positions.items():
        if planet not in PLANETS: continue
        sign = get_varga_sign_name(1, deg)
        dignity = get_planetary_dignity(planet, sign)
        report.append(f"{planet}: {dignity} ({sign})")
    return "\n".join(report)

def get_amk_report(
    planet_positions: Annotated[Dict[str, float], "Dictionary of planet names to absolute degrees"]
) -> Annotated[str, "Report identifying the Amatya Karaka (AmK)"]:
    """
    Identifies the Jaimini Karakas, specifically the AmK (Career Indicator).
    """
    karakas = get_jaimini_karakas(planet_positions)
    amk = karakas.get("Amatya Karaka (AmK)", "Unknown")
    return f"**Amatya Karaka (AmK)**: {amk}\n\nFull List:\n" + "\n".join([f"{k}: {v}" for k, v in karakas.items()])

def calculate_strength_report(
    planet: Annotated[str, "Name of the planet"],
    degree: Annotated[float, "Absolute degree"],
    house_type: Annotated[str, "Type of house (Kendra, Trikona, Dusthana, Average)"],
    is_retrograde: Annotated[bool, "Is the planet retrograde?"]
) -> Annotated[str, "Quantitative strength score (0-100) and qualitative label"]:
    """
    Calculates a heuristic 'Shadbala-like' strength score for a planet.
    """
    sign = get_varga_sign_name(1, degree)
    result = calculate_shadbala_heuristic(planet, sign, house_type, is_retrograde)
    return f"STRENGTH AUDIT for {planet}:\nScore: {result['Score']}/100\nStatus: {result['Label']}\nDignity: {result['Dignity']}"
