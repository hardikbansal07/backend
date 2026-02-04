import os
from autogen_agentchat.agents import AssistantAgent
from config.models import build_chat_completion_client
from tools.astro_tools import (
    calculate_varga_positions, 
    get_current_dasha, 
    check_divisional_strength,
    calculate_strength_report,
    get_dignity_report,
    get_amk_report,
    get_current_transits_report
)

# Load Prompts
def load_prompt(filename):
    base_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "library")
    with open(os.path.join(base_path, filename), "r", encoding="utf-8") as f:
        return f.read()

# Factory function to create fresh instances
def get_specialists(model_client=None):
    if not model_client:
        model_client = build_chat_completion_client()
    
    lagna_pati = AssistantAgent(
        name="LagnaPati",
        model_client=model_client,
        system_message=load_prompt("d1_lagna_rules.md"),
        tools=[calculate_varga_positions, calculate_strength_report, get_dignity_report],
        description="analyzes the Rashi (D1) chart, planetary strengths, and general fortune."
    )

    kala_purusha = AssistantAgent(
        name="KalaPurusha",
        model_client=model_client,
        system_message=load_prompt("dasha_logic.md"),
        tools=[get_current_dasha, get_current_transits_report],
        description="determines the quality of time, calculating Dasha periods and their effects."
    )

    varga_vizier = AssistantAgent(
        name="VargaVizier",
        model_client=model_client,
        system_message=load_prompt("d10_career_rules.md"), 
        tools=[check_divisional_strength, get_amk_report],
        description="analyzes the Dashamsha (D10) chart for career and public status details."
    )
    
    return lagna_pati, kala_purusha, varga_vizier
 