import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os
import google.auth
from typing import List, Dict, Optional

# Constants
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "astrocare1") # Default fallback
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = "gemini-pro" # Or gemini-1.5-pro-preview-0409, etc.

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
        # Check if project and location are available
        credentials, project = google.auth.default()
        
        # Prefer env var project if set, else use ADC project
        active_project = PROJECT_ID or project
        
        vertexai.init(project=active_project, location=LOCATION, credentials=credentials)
        
        _chat_model = GenerativeModel(MODEL_NAME)
        _model_initialized = True
        print(f"Vertex AI initialized for project {active_project}, location {LOCATION}")
    except Exception as e:
        print(f"Failed to initialize Vertex AI: {e}")
        # Make sure to not crash the app, but log error
        _model_initialized = False

def get_astrology_response(user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Sends user query to Gemini via Vertex AI with a Vedic Astrologer persona.
    
    Args:
        user_query: The user's question.
        chat_history: List of previous messages (optional). 
                      Format: [{"role": "user", "content": "..."}, {"role": "model", "content": "..."}]
    
    Returns:
        The text response from the model.
    """
    if not _model_initialized:
        init_vertex_ai()
        if not _model_initialized:
             return "I am currently unable to connect to the celestial stars (Service Unavailable). Please check configuration."

    # System Instruction / Persona
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
    
    # We can set system instruction in the model generation config or prepend it.
    # Vertex AI Gemini supports system instructions in `GenerativeModel` init or `start_chat`.
    # Let's re-init model with system instruction if possible or pass it as context.
    # Note: vertexai.generative_models.GenerativeModel supports `system_instruction` in recent versions.
    # To be safe with `gemini-pro` (initial versions didn't fully support system_instruction param in init), 
    # we can pass it in the history or context.
    # But let's try to instantiate a new model object with system_instruction if needed, 
    # or just prepend to the prompt for simplicity and compatibility.
    
    # Better approach for recent SDK:
    model = GenerativeModel(
        MODEL_NAME,
        system_instruction=[system_instruction]
    )
    
    # Convert chat_history to Vertex AI format
    history_objects = []
    if chat_history:
        from vertexai.generative_models import Content, Part
        for msg in chat_history:
            role = "user" if msg.get("role") in ["user", "human"] else "model"
            history_objects.append(Content(role=role, parts=[Part.from_text(msg.get("content", ""))]))

    chat = model.start_chat(history=history_objects)
    
    try:
        response = chat.send_message(user_query)
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, the planetary alignments are unclear at this moment. Please try again later."
