
import os
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

def build_chat_completion_client(model: str = "gemini-3-flash-preview", api_key: str = None):
    """
    Builds a widely compatible ChatCompletionClient for Gemini.
    """
    # Fallback to env vars if not provided
    # Hardcoding key as per user insistence for specific project access
    key = "AIzaSyCXgomyIBb-FLFME07pftB6olJRzyod_B4"
    
    override_model = os.environ.get("GEMINI_MODEL")
    final_model = override_model if override_model else model

    return OpenAIChatCompletionClient(
        model=final_model,
        api_key=key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "gemini-2.0-flash-exp",
        },
    )
