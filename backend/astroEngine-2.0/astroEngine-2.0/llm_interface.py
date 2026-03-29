import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from logger_config import setup_logger

load_dotenv()

class GeminiLLM:
    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        self.logger = setup_logger("GeminiLLM")
        
        # Determine authentication source
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_CLOUD_API_KEY")
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        # If project_id is set and no api_key or USE_VERTEX=true, use Vertex AI (ADC)
        # vertexai=True with an API key often causes 401 on standard Vertex endpoints.
        use_vertex = False
        if self.project_id and (not self.api_key or os.environ.get("USE_VERTEX") == "true"):
            use_vertex = True
            
        if use_vertex:
            self.logger.info(f"Initializing GeminiClient for Vertex AI (Project: {self.project_id})")
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
        else:
            self.logger.info("Initializing GeminiClient for Google AI Studio (using API Key)")
            self.client = genai.Client(
                api_key=self.api_key
            )
        
        self.model_name = model_name
        self.logger.info(f"GeminiLLM initialized with model: {self.model_name}")



    def generate_content(self, prompt):
        """
        Generates content and returns result with metrics.
        Returns: { "content": str, "metrics": dict }
        """
        self.logger.debug(f"Generating content for prompt (length: {len(prompt)} chars)")
        start_time = time.time()
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            duration = time.time() - start_time
            
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0
            metrics = {
                "duration_seconds": round(duration, 4),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            self.logger.info(f"Generation successful. Time: {metrics['duration_seconds']}s")
            self.logger.debug(f"Metrics: {metrics}")
            
            return {
                "content": response.text,
                "metrics": metrics
            }
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}", exc_info=True)
            return {"error": f"Error generation: {str(e)}", "metrics": {}}

    def generate_json(self, prompt):
        """
        Generates JSON and returns result with metrics.
        Returns: { "content": dict, "metrics": dict }
        """
        self.logger.debug(f"Generating JSON for prompt (length: {len(prompt)} chars)")
        start_time = time.time()
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            duration = time.time() - start_time
            
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0
            metrics = {
                "duration_seconds": round(duration, 4),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            self.logger.info(f"JSON Generation successful. Time: {metrics['duration_seconds']}s")
            
            try:
                content = json.loads(response.text)
                self.logger.debug("Successfully parsed JSON response.")
            except Exception as e:
                self.logger.error(f"Failed to parse JSON: {e}")
                self.logger.debug(f"Raw response text: {response.text}")
                content = {"error": "JSON parse failed", "raw": response.text}
            
            return {
                "content": content,
                "metrics": metrics
            }
        except Exception as e:
            self.logger.error(f"Error generating JSON: {str(e)}", exc_info=True)
            return {"error": f"Error generation: {str(e)}", "metrics": {}}

    def generate_with_tools(self, prompt, tools, history=None, enable_thinking=False):
        """
        Generate content with function calling support.
        
        Args:
            prompt: The user prompt or system instruction
            tools: List of tool definitions in Gemini format
            history: Optional conversation history
            enable_thinking: Enable thinking mode for deeper reasoning
        
        Returns:
            Response object with potential function calls
        """
        self.logger.debug(f"Generating with tools. Prompt length: {len(prompt)} chars, Tools: {len(tools)}")
        self.logger.debug(f"==== FULL PROMPT SENT TO LLM ====")
        if prompt and prompt.strip():
            # Show full prompt text (truncate if very long)
            if len(prompt) > 2000:
                self.logger.debug(f"Prompt (first 2000 chars): {prompt[:2000]}...")
                self.logger.debug(f"Prompt (last 500 chars): ...{prompt[-500:]}")
            else:
                self.logger.debug(f"Full prompt:\n{prompt}")
        start_time = time.time()
        
        try:
            # Convert tool definitions to Gemini format
            tool_declarations = []
            for tool in tools:
                tool_declarations.append(
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"]
                    )
                )
            
            config = types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=tool_declarations)]
            )
            
            # Add thinking config if enabled
            if enable_thinking:
                config.thinking_config = types.ThinkingConfig(thinking_budget=-1)
                self.logger.debug("Thinking mode enabled with unlimited budget")
            
            # Build contents in a format acceptable to Gemini SDK
            contents = []
            
            # Log conversation history if provided
            if history:
                self.logger.debug(f"==== CONVERSATION HISTORY ({len(history)} turns) ====")
                for i, turn in enumerate(history):
                    role = turn.get('role', 'unknown')
                    parts = turn.get('parts', [])
                    self.logger.debug(f"\n--- Turn {i+1}: Role={role}, Parts={len(parts)} ---")
                    for j, part in enumerate(parts):
                        if isinstance(part, str):
                            # Show FULL text without truncation
                            self.logger.debug(f"  Part {j+1} (text): {part}")
                        elif isinstance(part, dict):
                            if 'function_call' in part:
                                self.logger.debug(f"  Part {j+1} (function_call): {part['function_call']['name']}({part['function_call'].get('args', {})})")
                            elif 'function_response' in part:
                                # Show full response without truncation
                                resp_data = part['function_response'].get('response', {})
                                self.logger.debug(f"  Part {j+1} (function_response): {part['function_response']['name']} -> {resp_data}")
            
            if history:
                # history is expected to be a list of dicts (already formatted in sub_agent.py)
                for turn in history:
                    # Map dict to Content object if it's already a dict with role/parts
                    if isinstance(turn, dict) and "role" in turn and "parts" in turn:
                        # Convert parts to Part objects if they are strings
                        parts = []
                        for p in turn["parts"]:
                            if isinstance(p, str):
                                parts.append(types.Part(text=p))
                            elif isinstance(p, dict):
                                # Handle function_call and function_response
                                if "function_call" in p:
                                    parts.append(types.Part(function_call=types.FunctionCall(
                                        name=p["function_call"]["name"],
                                        args=p["function_call"]["args"]
                                    )))
                                elif "function_response" in p:
                                    parts.append(types.Part(function_response=types.FunctionResponse(
                                        name=p["function_response"]["name"],
                                        response=p["function_response"]["response"]
                                    )))
                                else:
                                    parts.append(types.Part(**p))
                            else:
                                parts.append(p)
                        
                        contents.append(types.Content(role=turn["role"], parts=parts))
                    else:
                        contents.append(turn)
            
            # Add prompt if it's not empty
            if prompt and prompt.strip():
                contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
            
            if not contents:
                return {"error": "No content provided", "has_function_calls": False, "function_calls": [], "text": None, "metrics": {}}

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            
            duration = time.time() - start_time
            
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0
            metrics = {
                "duration_seconds": round(duration, 4),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
            
            self.logger.info(f"Tool-enabled generation successful. Time: {metrics['duration_seconds']}s")
            
            # Check if response has function calls
            has_function_calls = False
            function_calls = []
            original_parts = []
            has_function_calls = False
            text_response = None
            original_parts = [] # Initialize original_parts here

            self.logger.debug(f"==== LLM RESPONSE ====")
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    original_parts.append(part) # Capture all parts to preserve history (including thoughts/text)
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        fc = {
                            "name": part.function_call.name,
                            "args": dict(part.function_call.args) if part.function_call.args else {}
                        }
                        function_calls.append(fc)
                        self.logger.debug(f"Function call: {fc['name']}({fc['args']})")
                    elif hasattr(part, 'text') and part.text:
                        text_response = part.text
                        # Show full text response without truncation
                        self.logger.debug(f"Text response: {text_response}")
            
            return {
                "response": response,
                "has_function_calls": has_function_calls,
                "function_calls": function_calls,
                "original_parts": original_parts,
                "text": text_response if not has_function_calls else None,
                "metrics": metrics
            }

            
        except Exception as e:
            self.logger.error(f"Error in tool-enabled generation: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "has_function_calls": False,
                "function_calls": [],
                "text": None,
                "metrics": {}
            }

