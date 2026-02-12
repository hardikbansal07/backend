from .agents.council import get_r1_council
from .core.loader import DataLoader
from .utils.helpers import load_prompt
from autogen_agentchat.base import TaskResult
import os
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def generate_report(
    user_email: str,
    user_gender: str,
    chart_data: dict,
    report_type: str = "full"
) -> str:
    """
    Main entry point for R1 Report Generation.
    
    Args:
        user_email: User's email
        user_gender: "Male" or "Female"
        chart_data: Dictionary containing full horoscope data (D1, D9, Dasha, etc.)
        report_type: Type of report to generate (default: "full")
        
    Returns:
        Markdown string containing the full report.
    """
    try:
        # 1. Initialize Loader with In-Memory Data
        loader = DataLoader(chart_data)
        
        # 2. Build Client (Assuming Vertex AI or similar configured in settings)
        # We need to ensure build_chat_completion_client works. 
        # For now, we import it here to avoid circular imports? 
        # Actually it was in council.py, let's move it out or re-use.
        # It's better to pass the client in, but for now let's build it here.
        from .config.settings import build_chat_completion_client
        client = build_chat_completion_client()
        
        # 3. Create Council
        council = get_r1_council(loader, client)
        
        # 4. Prepare Context
        today = datetime.now()
        
        # Calculate Age (Logic from R2/report_generator.py)
        # We need birth year.
        current_age = 25 # Fallback
        birth_year = today.year - 25
        
        meta = chart_data.get("meta", {})
        if "year" in meta:
             try:
                 birth_year = int(meta["year"])
                 current_age = today.year - birth_year
             except: pass
        elif "birth_date" in meta:
             # Try parsing YYYY-MM-DD
             try:
                 dob = datetime.strptime(meta["birth_date"], "%Y-%m-%d")
                 birth_year = dob.year
                 current_age = today.year - birth_year
             except: pass

        
        system_instruction = f"""
        CRITICAL INSTRUCTION FOR FINAL OUTPUT:
        - Act as a ONE Unified, Omniscient Astrological Expert.
        - DO NOT mention agent names like "RupaMaya" or describe your internal process.
        - Speak directly to the user with authority and empathy.
        - Use Markdown Tables and Blockquotes.
        
        TEMPORAL CONTEXT:
        - Current Date: {today.strftime('%B %d, %Y')}
        - User: {current_age} years old (Born {birth_year}), Gender: {user_gender}
        - Spouse Karaka: {'Mars' if user_gender.lower() == 'female' else 'Venus'}
        """
        
        # 5. Define Sections (Ported from R2/report_generator.py)
        # We can implement a subset for testing or the full list.
        
        full_context_data = loader.load_all_data()

        report_sections = [
            {
                "title": "1. The Timing Question",
                "prompt": f"""
[SYSTEM: FULL DATA CONTEXT]
{full_context_data}
[END DATA]

{system_instruction}

User Query: "When will I meet my future partner, and at what exact age will I get married? (I am currently {current_age})."
Context: Analyzing Timing (Dasha/Transits). User Gender: {user_gender}.
- Task: Use 'KalaVidya' to find the timeline. Pass gender='{user_gender}' to the tool.
"""
            },
            {
                "title": "2. The Identity Question",
                "prompt": f"""
{system_instruction}

User Query: "What will my future wife look like, what will her profession be, and what is her nature?"
Context: Describe physical appearance, direction, and nature.
- Task: Use 'RupaMaya' (Appearance) and 'DikPala' (Location).
"""
            },
            {
                "title": "3. Love vs. Arranged",
                "prompt": f"""
{system_instruction}

User Query: "Will I have a Love Marriage or an Arranged Marriage?"
Context: Analyze 5th (Love) and 7th (Marriage) connection in D9.
- Task: Use 'SambandaVidya' to determine the type.
"""
            },
             {
                "title": "4. Life After Marriage",
                "prompt": f"""
{system_instruction}

User Query: "What will my life be like AFTER marriage?"
Constraint: DO NOT repeat Physical Appearance, Age, or Distance.
Context: Focus on Marital Quality, Financial Status, and Shared Destiny.
- Task: Use 'SambandaVidya' for quality/wealth analysis.
"""
            }
        ]
        
        final_report = [f"# R1 Relationship Report for {user_email}\n\n"]
        
        for section in report_sections:
            logger.info(f"[R1] Generating Section: {section['title']}")
            final_report.append(f"## {section['title']}\n\n")
            
            # Run Council
            # We use 'run' which returns a TaskResult
            # Check autogen version. R2/report_generator.py uses 'await r1_council.run(task=payload)'
            result: TaskResult = await council.run(task=section['prompt'])
            
            # Extract final response
            # R2 logic: Look for "R1_Orchestrator" last message or just last message
            answer = ""
            for msg in reversed(result.messages):
                if msg.source == "R1_Orchestrator":
                    answer = msg.content
                    break
            
            if not answer and result.messages:
                answer = result.messages[-1].content
                
            final_report.append(answer + "\n\n")
            
        return "".join(final_report)

    except Exception as e:
        logger.error(f"[R1] Generation failed: {e}", exc_info=True)
        return f"Error generating report: {str(e)}"
