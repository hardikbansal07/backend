from __future__ import annotations

import os
from typing import Optional

from autogen_core.models import ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient

DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = "AIzaSyDiXbgrjI9k8hPHBxLnTHfjEgPN7UHQ8tY" #GOOGLE BABITA Account



def build_chat_completion_client(
    *, model: Optional[str] = None, api_key: Optional[str] = None, parallel_tool_calls: Optional[bool] = None
) -> ChatCompletionClient:
    """Return a Gemini-backed OpenAI-compatible chat completion client.

    Args:
        model: Optional override for the Gemini model name. Defaults to `DEFAULT_MODEL`
            or the value of the `GEMINI_MODEL` environment variable if set.
        api_key: Optional override for the API key. Defaults to the value of the
            `GEMINI_API_KEY` environment variable.
    """

    model_name = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    api_token = api_key or os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    if not api_token:
        raise ValueError(
            "Gemini API key missing. Provide it via the api_key argument or set GEMINI_API_KEY."
        )

    kwargs = {"model": model_name, "api_key": api_token}
    if parallel_tool_calls is not None:
        kwargs["parallel_tool_calls"] = parallel_tool_calls
    return OpenAIChatCompletionClient(**kwargs)  # type: ignore[arg-type]
