"""
FACADE for new Modular Engines.
This file is maintained for backward compatibility but all logic is delegated.
"""

from src.core.timing_engine import TimingEngine
from src.core.love_vs_arranged_engine import LoveVsArrangedEngine
from src.core.spouse_meeting_place_engine import SpouseMeetingPlaceEngine
from src.core.spouse_nature_engine import SpouseNatureEngine

# --- Legacy Wrapper Functions ---

def get_timing_analysis(
    current_dasha_lord: str, # Preserved signature but might strictly need more args now
    saturn_transit_sign: str,
    jupiter_transit_sign: str,
    seventh_house_sign: str,
    seventh_lord_sign: str
):
    # Map old simple args to new robust engine
    # We need to make assumptions or fetch missing data if possible.
    # However, for the Agent, we will update the Agent Tool Definition in council.py.
    # For this facade, we return the robust dict.
    
    # We lack inputs for full 8 parameters here (like Sun Sign, Vimshottari AD, Chara).
    # We will pass defaults or "Unknown".
    
    return TimingEngine.analyze_timing(
        current_vimshottari_md=current_dasha_lord,
        current_vimshottari_ad="Unknown",
        current_chara_ad_sign="Unknown",
        transit_saturn_sign=saturn_transit_sign,
        transit_jupiter_sign=jupiter_transit_sign,
        transit_lagna_lord_sign="Unknown",
        transit_7th_lord_sign="Unknown"
    )

def get_relationship_type(*args, **kwargs):
    return LoveVsArrangedEngine.analyze({})

def get_meeting_context(*args, **kwargs):
    return SpouseMeetingPlaceEngine.analyze({})

def get_spouse_direction_distance(*args, **kwargs):
    # This was part of Meeting Place / DikPala data
    return SpouseMeetingPlaceEngine.analyze({})

def get_physical_appearance(*args, **kwargs):
    return SpouseNatureEngine.analyze({})

def get_spouse_initials(*args, **kwargs):
    return SpouseNatureEngine.analyze({}) # Name sound considered part of identity/nature

def get_marital_quality(*args, **kwargs):
    return LoveVsArrangedEngine.analyze({}) # Grouped with relationship quality
