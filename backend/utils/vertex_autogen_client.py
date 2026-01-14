import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from autogen_core.models._model_client import ChatCompletionClient, ModelCapabilities
from autogen_core.models._types import (
    UserMessage, 
    SystemMessage, 
    AssistantMessage, 
    LLMMessage,
    CreateResult,
    RequestUsage
)
from services.vertex_service import init_vertex_ai, get_model_name
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part, HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class VertexGenAIClient(ChatCompletionClient):
    """
    A custom AutoGen ChatCompletionClient for Google Vertex AI.
    Uses the official vertexai SDK.
    """

    def __init__(self, model: str = None, **kwargs):
        """
        Initialize the Vertex AI client.
        
        Args:
            model: Model name (e.g., 'gemini-1.5-flash-001'). 
                   If None, fetches from vertex_service or env.
        """
        # Ensure Vertex AI is initialized (ADC / Project ID)
        init_vertex_ai()
        
        self.model_name = model or get_model_name()
        # Default safety settings - block only high probability to avoid false positives on astrology terms
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        self.generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.95,
        }
        

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            vision=False,
            function_calling=False,
            json_output=False
        )

    def model_info(self) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "provider": "google-vertex"
        }

    async def count_tokens(self, messages: List[LLMMessage], **kwargs) -> int:
        # TODO: Implement token counting if needed
        return 0

    async def create_stream(self, messages: List[LLMMessage], **kwargs):
        # Fallback to non-streaming for now, or implement rudimentary yielding
        result = await self.create(messages, **kwargs)
        yield result.content

    def remaining_tokens(self, **kwargs) -> int:
        return 1000000 # Placeholder

    def close(self):
        pass

    def total_usage(self) -> Any:
        return {}

    async def create(
        self,
        messages: List[LLMMessage],
        **kwargs: Any
    ) -> CreateResult:
        """
        Generate a response from the model based on the messages.
        """
        try:
            # Separate System Message from History
            system_instruction = None
            history: List[Content] = []

            for msg in messages:
                if isinstance(msg, SystemMessage):
                    # Vertex AI takes system instruction at model init or generation config (depending on SDK version)
                    # For current SDK, passing it to GenerativeModel constructor is best, 
                    # but we are re-instantiating or using a shared instance.
                    # We will collect it and init a fresh model instance for this call if system prompt exists.
                    system_instruction = msg.content
                elif isinstance(msg, UserMessage):
                    history.append(Content(role="user", parts=[Part.from_text(msg.content)]))
                elif isinstance(msg, AssistantMessage):
                     history.append(Content(role="model", parts=[Part.from_text(msg.content)]))
                else:
                    # Fallback for other message types
                    content = str(msg.content) if hasattr(msg, "content") else str(msg)
                    history.append(Content(role="user", parts=[Part.from_text(content)]))

            # Instantiate model
            # We instantiate per call to support changing system instructions per agent
            model = GenerativeModel(
                self.model_name,
                system_instruction=[system_instruction] if system_instruction else None
            )

            # The last message is usually the "current" input for the generate call?
            # AutoGen usually sends the whole history. 
            # GenerativeModel.generate_content (chat=False) takes contents list.
            # GenerativeModel.start_chat takes history.
            
            # 1. Stateless approach (generate_content) with full list
            # Verify if this model supports chat-like list of contents.
            # Gemini supports passing list of Content objects to generate_content.
            
            # OR 
            
            # 2. ChatSession approach
            # chat = model.start_chat(history=history[:-1])
            # response = chat.send_message(history[-1].parts[0].text)
            
            # Since auto-gen manages state, stateless `generate_content` with all messages is usually preferred
            # BUT, `Contents` list must alternate user/model. AutoGen might not strictly guarantee this?
            # Let's try `generate_content` with the full history list.
            
            logger.info(f"[VertexGenAIClient] Generating content with model {self.model_name}")
            
            # Vertex AI SDK expects 'parts' to be a list of Part objects
            # And 'role' to be 'user' or 'model'
            
            response = await model.generate_content_async(
                contents=history,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            response_text = response.text
            
            # Return wrapped result
            return CreateResult(
                content=response_text,
                role="assistant",
                finish_reason="stop", # Map generic finish reason
                usage=RequestUsage(prompt_tokens=0, completion_tokens=0),
                cached=False
            )
        except Exception as e:
            logger.error(f"[VertexGenAIClient] Error in generate_content: {e}", exc_info=True)
            # Return an error message or re-raise
            # Returning string to keep the conversation going if possible, or fail gracefully
            raise e

    def actual_usage(self) -> Any:
        return None
