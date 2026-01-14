import os
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

def build_chat_completion_client(model: str = "gemini-2.0-flash-exp", api_key: str = None):
    """
    Builds a widely compatible ChatCompletionClient for Gemini.
    """
    # Fallback to env vars if not provided
    key = api_key or os.environ.get("GEMINI_API_KEY")
    override_model = os.environ.get("GEMINI_MODEL")
    
    final_model = override_model if override_model else model

    # Validate API key is provided
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to backend/.env file.")

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
