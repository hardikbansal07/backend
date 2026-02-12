from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from ..core.timing_engine import TimingEngine
from ..core.love_vs_arranged_engine import LoveVsArrangedEngine
from ..core.spouse_meeting_place_engine import SpouseMeetingPlaceEngine
from ..core.spouse_nature_engine import SpouseNatureEngine
from ..core.tools_data import retrieve_chart_data
from ..utils.helpers import load_prompt
from ..core.loader import DataLoader
import os
from typing import Dict, Any

def get_r1_council(loader: DataLoader, model_client) -> RoundRobinGroupChat:
    
    # --- TOOL WRAPPERS (Inject Loader) ---
    async def tool_analyze_nature(data: Dict[str, Any]) -> Dict[str, Any]:
        return SpouseNatureEngine.analyze(data, data_loader=loader)

    async def tool_analyze_place(data: Dict[str, Any]) -> Dict[str, Any]:
        return SpouseMeetingPlaceEngine.analyze(data, data_loader=loader)

    async def tool_analyze_love(data: Dict[str, Any]) -> Dict[str, Any]:
        return LoveVsArrangedEngine.analyze(data, data_loader=loader)
        
    async def tool_retrieve_data(requests: list[str]) -> str:
        return retrieve_chart_data(requests, loader=loader)

    async def tool_analyze_timing(
        current_vimshottari_md: str,
        current_vimshottari_ad: str,
        current_chara_ad_sign: str,
        transit_saturn_sign: str,
        transit_jupiter_sign: str,
        transit_lagna_lord_sign: str,
        transit_7th_lord_sign: str,
        transit_sun_sign: str = "Unknown",
        transit_planets_in_1_7_count: int = 0,
        gender: str = "Male"
    ) -> Dict[str, Any]:
        return TimingEngine.analyze_timing(
            current_vimshottari_md=current_vimshottari_md,
            current_vimshottari_ad=current_vimshottari_ad,
            current_chara_ad_sign=current_chara_ad_sign,
            transit_saturn_sign=transit_saturn_sign,
            transit_jupiter_sign=transit_jupiter_sign,
            transit_lagna_lord_sign=transit_lagna_lord_sign,
            transit_7th_lord_sign=transit_7th_lord_sign,
            transit_sun_sign=transit_sun_sign,
            transit_planets_in_1_7_count=transit_planets_in_1_7_count,
            data_loader=loader,
            gender=gender
        )

    # --- 1. THE SPECIALISTS ---

    # RupaMaya: Physical Appearance
    rupa_maya = AssistantAgent(
        name="RupaMaya",
        model_client=model_client,
        system_message="""You are RupaMaya. The user asks about Physical Appearance. 
        You MUST use the 'analyze' tool to get the Classical Astrology prediction (7th House/Lord based).
        Present the clear physical description (Complexion, Height) to the user.
        Add a small note that this is based on Standard Classical Rules.
        """,
        tools=[tool_analyze_nature],
        description="Analyzes physical looks, height, and body type."
    )

    # DikPala: Location & Distance
    dik_pala = AssistantAgent(
        name="DikPala",
        model_client=model_client,
        system_message="""You are DikPala. The user asks about Meeting Place/Direction. 
        You MUST use the 'analyze' tool to get the Classical prediction (7th House Direction).
        Report the Direction and Distance clearly.
        Add a small note that this is based on Standard Classical Rules.
        """,
        tools=[tool_analyze_place],
        description="Calculates direction, distance (km), and meeting context."
    )

    # NamaKarana: Names 
    nama_karana = AssistantAgent(
        name="NamaKarana",
        model_client=model_client,
        system_message="You are NamaKarana. You MUST use the 'analyze' tool. If 'Data Not Available', inform the user.",
        tools=[tool_analyze_nature],
        description="Identifies name initials and sounds."
    )

    # KalaVidya: The Timer
    kala_vidya = AssistantAgent(
        name="KalaVidya",
        model_client=model_client,
        system_message="""You are KalaVidya, the expert on Marriage Timing.
        
        TEMPORAL INTELLIGENCE:
        - You have access to the user's birth year and current year from the context
        - When you analyze timing data, think about what the calendar years mean
        - Calculate calendar years from ages (Birth Year + Age = Calendar Year)
        - Intelligently interpret whether timing windows are past, present, or future
        - Adapt your language naturally based on your analysis
        
        YOUR TASK:
        - Use the 'analyze_timing' tool to validate specific time windows
        - Extract from context: Current Dasha Lords (MD/AD), Transit Signs, User Gender
        - Pass these to the tool to get a score (0-8 parameters met)
        - Synthesize findings intelligently - think about what the data reveals
        - Report timing in a contextually appropriate way
        
        CRITICAL: Use your intelligence to interpret results. Don't just dump raw data.
        """,
        tools=[tool_analyze_timing],
        description="Analyzes timing (Dasha and Transits)."
    )

    # SambandaVidya: The Connector
    sambanda_vidya = AssistantAgent(
        name="SambandaVidya",
        model_client=model_client,
        system_message="""You are SambandaVidya. The user asks about Love vs Arranged. 
        You MUST extract the current Mahadasha (MD) and Antardasha (AD) lords from the context.
        Then call 'analyze' with arguments: {"current_md_lord": "PlanetName", "current_ad_lord": "PlanetName"}.
        If the tool returns a prediction, explain it to the user.
        """,
        tools=[tool_analyze_love],
        description="Analyzes relationship type (Love/Arranged) and marital quality."
    )

    # --- 2. THE MANAGER ---

    # R1 / ShukraAcharya: The Orchestrator
    master_prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "master_prompt.md")
    
    r1_orchestrator = AssistantAgent(
        name="R1_Orchestrator",
        model_client=model_client,
        system_message=load_prompt(master_prompt_path),
        tools=[tool_retrieve_data],
        description="The R1 Manager. Routes the user question to the correct specialist and synthesizes the final answer."
    )

    # --- 3. THE COUNCIL ---

    r1_council = RoundRobinGroupChat(
        participants=[r1_orchestrator, rupa_maya, dik_pala, nama_karana, kala_vidya, sambanda_vidya],
        max_turns=10
    )
    
    return r1_council
