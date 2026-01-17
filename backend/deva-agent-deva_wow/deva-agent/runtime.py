import asyncio
from datetime import datetime
import json
import os
import argparse
from autogen_agentchat.ui import Console
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

from agents.specialists import lagna_pati, kala_purusha, varga_vizier
from agents.principals import maha_rishi

async def main():
    parser = argparse.ArgumentParser(description="The Celestial Council Runtime")
    parser.add_argument("--case", required=True, help="Path to the case folder containing lagna.json")
    parser.add_argument("--question", required=True, help="The user's astrological question")
    args = parser.parse_args()

    # 1. Load Data
    lagna_path = os.path.join(args.case, "lagna.json")
    print(f"Loading chart from: {lagna_path}")
    
    try:
        with open(lagna_path, "r", encoding="utf-8") as f:
            chart_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find lagna.json at {lagna_path}")
        return

    # 1.5 Load Meta Data (for birth details)
    meta_path = os.path.join(args.case, "meta.json")
    meta_data = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_data = json.load(f)

    # 2. Construct the Context
    # We flatten the JSON a bit or just dump it as string context
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    context_message = f"""
    SYSTEM CONTEXT: TIME ANCHOR
    -----------------------------------
    CURRENT DATE (TODAY): {date_str}
    (All predictions must be relative to this date. Dashas before this are PAST. Dashas after this are FUTURE.)
    -----------------------------------
    
    EXISTING CHART DATA
    -----------------------------------
    {json.dumps(chart_data, indent=2)}
    
    METADATA (Birth Details):
    {json.dumps(meta_data, indent=2)}
    -----------------------------------
    
    USER QUESTION: {args.question}
    
    INSTRUCTIONS FOR COUNCIL:
    1. LagnaPati: Analyze the D1 strength.
    2. KalaPurusha: Check the current Dasha. CRITICAL: Compare every date to TODAY ({date_str}).
    3. VargaVizier: Check the D10 Career strength.
    4. MahaRishi: Synthesize everything into a final answer.
    """

    # 3. Create the Council (Group Chat)
    # We use RoundRobin for this prototype to ensure everyone speaks once
    # Terminate when MahaRishi say "TERMINATE" or after 1 round?
    # Better: Use TextMentionTermination("TERMINATE") and have MahaRishi say it.
    
    council = RoundRobinGroupChat(
        participants=[lagna_pati, kala_purusha, varga_vizier, maha_rishi],
        max_turns=4, # Ensure everyone gets a turn: Lagna -> Kala -> Varga -> Rishi
    )

    # 4. Run stream
    import time
    
    # 4. Run stream with timing
    print("Invocation The Celestial Council...")
    start_time = time.time()
    step_start = start_time
    
    async for msg in council.run_stream(task=context_message):
        now = time.time()
        step_duration = now - step_start
        
        # Print the message cleanly
        source = getattr(msg, "source", "Unknown")
        # Check if it's a ToolCall or TextMessage
        if hasattr(msg, "content"):
             # Simple formatting
             print(f"\n[{source}] (Step Time: {step_duration:.2f}s)")
             print(f"{msg.content}")
        else:
             print(f"\n[{source}] (Step Time: {step_duration:.2f}s) - {type(msg).__name__}")

        step_start = now

    total_time = time.time() - start_time
    print(f"\n[TOTAL EXECUTION TIME: {total_time:.2f}s]")

if __name__ == "__main__":
    asyncio.run(main())
