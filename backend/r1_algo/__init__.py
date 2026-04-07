from .agents.council import get_r1_council
from .core.loader import DataLoader
from .utils.helpers import load_prompt
from autogen_agentchat.base import TaskResult
import os
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Maximum retries for rate-limited API calls
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 30


async def _run_section_with_retry(council, prompt: str, section_title: str) -> str:
    """
    Run a single council section with retry + exponential backoff for 429 errors.
    Raises on persistent failure instead of silently returning error text.
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result: TaskResult = await council.run(task=prompt)

            # Extract final response
            answer = ""
            for msg in reversed(result.messages):
                if msg.source == "R1_Orchestrator":
                    answer = msg.content
                    break
            if not answer and result.messages:
                answer = result.messages[-1].content

            return answer

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "resource exhausted" in error_str or "rate limit" in error_str

            if is_rate_limit and attempt < MAX_RETRIES:
                wait = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))  # 30s, 60s, 120s
                logger.warning(
                    f"[R1] Section '{section_title}' hit 429 rate limit (attempt {attempt}/{MAX_RETRIES}). "
                    f"Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)
            else:
                # Non-retryable error or exhausted retries — bubble up
                raise

    # Should not reach here, but safety net
    raise last_error


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
        
    Raises:
        Exception: If report generation fails (429, network, etc.)
                   This ensures the caller marks the job as FAILED.
    """
    # 1. Initialize Loader with In-Memory Data
    loader = DataLoader(chart_data)
    
    # 2. Build Client
    from .config.settings import build_chat_completion_client
    client = build_chat_completion_client()
    
    # 3. Create Council
    council = get_r1_council(loader, client)
    
    # 4. Prepare Context
    today = datetime.now()
    
    current_age = 25  # Fallback
    birth_year = today.year - 25
    
    meta = chart_data.get("meta", {})
    if "year" in meta:
         try:
             birth_year = int(meta["year"])
             current_age = today.year - birth_year
         except: pass
    elif "birth_date" in meta:
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
        
        answer = await _run_section_with_retry(council, section['prompt'], section['title'])
        final_report.append(answer + "\n\n")
        
    return "".join(final_report)
