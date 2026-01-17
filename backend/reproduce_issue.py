
import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Mock setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "deva-agent-deva_wow", "deva-agent"))

# Mock VertexGenAIClient to avoid real calls for initial syntax check
# Or use real one if possible. Let's try to import the real one first.
try:
    from utils.vertex_autogen_client import VertexGenAIClient
    from agents.specialists import get_specialists
    from agents.principals import get_principal
    from autogen_agentchat.teams import RoundRobinGroupChat
except ImportError as e:
    logger.error(f"Import failed: {e}")
    sys.exit(1)

async def run_test():
    try:
        logger.info("Starting test...")
        
        # 1. Initialize Client
        # We might need to mock this if no creds, but user has env vars hopefully?
        # If not, I'll mock the internal methods.
        client = VertexGenAIClient(model="gemini-pro") 
        
        # 2. Get Agents
        lagna_pati, kala_purusha, varga_vizier = get_specialists(model_client=client)
        maha_rishi = get_principal(model_client=client)
        
        # 3. Create context
        context_message = "TEST MESSAGE"
        
        # 4. Create Council
        council = RoundRobinGroupChat(
            participants=[lagna_pati, kala_purusha, varga_vizier, maha_rishi],
            max_turns=2
        )
        
        # 5. Run Stream
        logger.info("Running stream...")
        async for msg in council.run_stream(task=context_message):
            logger.info(f"Got msg: {msg}")

    except Exception as e:
        logger.exception("CRASHED:")

if __name__ == "__main__":
    asyncio.run(run_test())
