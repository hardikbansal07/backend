import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os
import time
import logging
import google.auth
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "astrocare-backend")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")  # us-central1 has max capacity
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")    # Gemini 2.5 Flash on Vertex AI

_model_initialized = False
_chat_model = None

def get_model_name() -> str:
    """Return the model name to use for Vertex AI."""
    return os.getenv("GEMINI_MODEL", MODEL_NAME)

def init_vertex_ai():
    """
    Initializes Vertex AI with Application Default Credentials (ADC).
    """
    global _model_initialized, _chat_model
    try:
        config_project = os.getenv("GOOGLE_CLOUD_PROJECT") or PROJECT_ID
        
        try:
            credentials, adc_project = google.auth.default()
            quota_project = getattr(credentials, "quota_project_id", "Not Set")
        except Exception as auth_err:
            print(f"Warning: Could not get default credentials: {auth_err}")
            credentials, adc_project = None, None
            quota_project = "Error"
        
        active_project = config_project or adc_project
        
        print(f"--- Vertex AI Diagnostic ---")
        print(f"Config Project: {config_project}")
        print(f"ADC Project: {adc_project}")
        print(f"Quota Project (Billing): {quota_project}")
        print(f"Final Active Project: {active_project}")
        print(f"Location: {LOCATION}")
        print(f"Model: {MODEL_NAME}")
        print(f"---------------------------")
        
        if not active_project:
            print("Error: Vertex AI initialization failed. No Project ID found.")
            _model_initialized = False
            return

        vertexai.init(project=active_project, location=LOCATION, credentials=credentials)
        _chat_model = GenerativeModel(MODEL_NAME)
        _model_initialized = True
        print(f"Vertex AI successfully initialized for {active_project}")
    except Exception as e:
        print(f"Failed to initialize Vertex AI: {e}")
        _model_initialized = False


def _generate_with_retry(model_name: str, prompt: str, system_instruction: str, max_retries: int = 3) -> str:
    """
    Call Vertex AI with exponential backoff retry on 503 errors.
    Only uses gemini-2.5-flash — no fallback.
    """
    for attempt in range(max_retries):
        try:
            model = GenerativeModel(model_name, system_instruction=[system_instruction])
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            is_503 = "503" in error_str or "UNAVAILABLE" in error_str
            is_last_attempt = attempt == max_retries - 1

            if is_503 and not is_last_attempt:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"[VERTEX] 503, attempt {attempt+1}/{max_retries}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"[VERTEX] Failed after {attempt+1} attempts: {e}")
                raise

    raise Exception("gemini-2.5-flash unavailable after retries.")


def get_astrology_response(user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Sends user query to Gemini via Vertex AI with a Vedic Astrologer persona.
    Includes retry logic for 503 errors.
    """
    if not _model_initialized:
        init_vertex_ai()
        if not _model_initialized:
            return "I am currently unable to connect to the service. Please check configuration."

    system_instruction = (
        "You are an expert Vedic Astrologer. Your persona is empathetic, mystical, yet practical. "
        "You provide advice based on Vedic principles (Jyotish). "
        "When answering:"
        "1. Use a warm, calming tone."
        "2. Reference planetary influences where appropriate (e.g., Saturn's discipline, Jupiter's wisdom)."
        "3. Offer practical remedies (upayas) alongside astrological insights."
        "4. Do not offer fatalistic predictions; always focus on free will and karma."
        "5. If the user asks non-astrological questions, politely steer them back to astrology or life guidance."
    )

    # Build full prompt with history
    history_text = ""
    if chat_history:
        for msg in chat_history:
            role = "User" if msg.get("role") in ["user", "human"] else "Model"
            history_text += f"{role}: {msg.get('content', '')}\n"

    full_prompt = f"{history_text}User: {user_query}" if history_text else user_query

    return _generate_with_retry(
        model_name=get_model_name(),
        prompt=full_prompt,
        system_instruction=system_instruction
    )
