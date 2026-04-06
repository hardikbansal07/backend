
import os
import logging
from autogen_agentchat.ui import Console

logger = logging.getLogger(__name__)

def build_chat_completion_client(model: str = None, api_key: str = None):
    """
    Builds a ChatCompletionClient using Vertex AI (same as Deva Agent).
    Falls back to OpenAI-compatible Gemini API if Vertex AI fails.
    """
    # Primary: Use Vertex AI (Google Cloud ADC - no API key needed)
    try:
        from utils.vertex_autogen_client import VertexGenAIClient
        client = VertexGenAIClient(model=model)
        logger.info(f"[R1] Using Vertex AI client (same as Deva Agent)")
        return client
    except Exception as e:
        logger.warning(f"[R1] Vertex AI client failed: {e}. Falling back to Gemini API.")
    
    # Fallback: OpenAI-compatible Gemini API
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    
    key = api_key or os.environ.get("GEMINI_API_KEY") or "AIzaSyCXgomyIBb-FLFME07pftB6olJRzyod_B4"
    override_model = os.environ.get("GEMINI_MODEL")
    final_model = override_model if override_model else (model or "gemini-2.5-flash")

    logger.info(f"[R1] Using Gemini API fallback with model: {final_model}")
    return OpenAIChatCompletionClient(
        model=final_model,
        api_key=key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "gemini-2.0-flash",
        },
    )
