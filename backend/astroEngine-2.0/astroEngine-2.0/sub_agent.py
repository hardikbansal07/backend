"""
SubAgent with Tool-Use Architecture
The LLM decides which tools to call based on the user's query
"""

import os
import json
from typing import Optional, List, Dict, Any
from llm_interface import GeminiLLM
from astro_tools import AstroTools, get_tool_definitions
from logger_config import setup_logger


class SubAgent:
    def __init__(self, use_thinking=True):
        self.logger = setup_logger("SubAgent")
        # Use regular model with thinking enabled
        self.llm = GeminiLLM(model_name="gemini-2.5-flash")
        self.use_thinking = use_thinking
        self.logger.info(f"SubAgent initialized with model: gemini-2.5-flash (thinking={'enabled' if use_thinking else 'disabled'})")
        self.request_id = None
        self.request_id = None
        self.email = None
        self.user_context = None
        self.tools = None
        self.tool_definitions = get_tool_definitions()
        self.max_turns = 10  # Maximum number of tool-calling turns
        self.common_planet_roles = self._load_planet_roles()

    def _load_planet_roles(self):
        """Loads common planetary roles from JSON file."""
        try:
            path = "planet_roles.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load planet_roles.json: {e}")
            return {}

    def set_identity(self, request_id: Optional[str] = None, email: Optional[str] = None, user_context: Optional[dict] = None):
        """Set the identity context for data retrieval."""
        self.request_id = request_id
        self.email = email
        self.user_context = user_context
        self.tools = AstroTools(request_id=request_id, email=email)
        self.logger.info(f"SubAgent identity set: ID={request_id}, Email={email}")

    def analyze(self, query: str, pattern: dict):
        """
        Performs comprehensive astrological analysis using tool calling.
        The LLM decides which tools to call based on the query.
        
        Args:
            query: User's question
            pattern: Domain pattern from patterns.json
            
        Returns:
            Dictionary with content and metrics
        """
        if not self.request_id and not self.email:
            self.logger.error("No identity context available for analysis")
            return {
                "content": "Error: No user identity provided for data retrieval.",
                "metrics": {}
            }
        
        self.logger.info(f"Starting tool-based analysis for query: {query}")
        self.logger.info(f"Domain: {pattern.get('description', 'Unknown')}")
        
        # Build initial prompt with domain context
        initial_prompt = self._build_initial_prompt(query, pattern)
        
        # Multi-turn conversation with tool calling
        total_metrics = {
            "duration_seconds": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "tool_calls_made": 0,
            "turns": 0
        }
        
        # MUST start with the user prompt in history for Gemini function calling consistency
        conversation_history = [
            {"role": "user", "parts": [initial_prompt]}
        ]
        
        for turn in range(self.max_turns):
            total_metrics["turns"] = turn + 1
            self.logger.info(f"--- Turn {turn + 1}/{self.max_turns} ---")
            
            # Add delay between turns to avoid rate limiting
            if turn > 0:
                import time
                time.sleep(2)  # 2 second delay between turns
            
            # Call LLM with tools (enable thinking for deeper reasoning)
            # Always pass history now, as turn 0 is the response to the first history item
            response_obj = self.llm.generate_with_tools(
                prompt="",
                tools=self.tool_definitions,
                history=conversation_history,
                enable_thinking=self.use_thinking
            )

            
            # Check for errors
            if "error" in response_obj:
                error_msg = response_obj.get("error", "Unknown error")
                self.logger.error(f"LLM error: {error_msg}")
                
                # Check if it's a rate limit error
                if "429" in str(error_msg) or "quota" in str(error_msg).lower():
                    self.logger.warning("Rate limit hit. Falling back to simple analysis.")
                    # Fall back to simple non-tool analysis
                    return self._fallback_analysis(query, pattern, total_metrics)
                
                return {
                    "content": f"Error during analysis: {error_msg}",
                    "metrics": total_metrics
                }
            
            # Aggregate metrics
            metrics = response_obj.get("metrics", {})
            for key in ["duration_seconds", "input_tokens", "output_tokens"]:
                if key in metrics:
                    total_metrics[key] += metrics[key]
            
            # Check if LLM wants to call tools
            if response_obj.get("has_function_calls"):
                function_calls = response_obj.get("function_calls", [])
                total_metrics["tool_calls_made"] += len(function_calls)
                
                self.logger.info(f"LLM requested {len(function_calls)} tool call(s)")
                
                # Execute each tool call
                tool_results = []
                for fc in function_calls:
                    tool_name = fc["name"]
                    tool_args = fc["args"]
                    
                    self.logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                    
                    # Execute the tool
                    result = self._execute_tool(tool_name, tool_args)
                    tool_results.append({
                        "name": tool_name,
                        "result": result
                    })
                    
                    self.logger.debug(f"Tool {tool_name} returned: {result}")
                
                # Add to conversation history in the correct format
                # Preserve all parts (including thoughts/text) to satisfy API requirements
                conversation_history.append({
                    "role": "model",
                    "parts": response_obj["original_parts"]
                })

                
                # The function responses - must match the number of function calls
                function_response_parts = []
                for tr in tool_results:
                    function_response_parts.append({
                        "function_response": {
                            "name": tr["name"],
                            "response": tr["result"]
                        }
                    })
                
                conversation_history.append({
                    "role": "user",  # Function responses come from user role
                    "parts": function_response_parts
                })
                
            else:
                # LLM has final answer
                final_text = response_obj.get("text", "")
                
                if final_text:
                    self.logger.info("LLM provided final answer")
                    self.logger.info(f"Total turns: {turn + 1}, Total tool calls: {total_metrics['tool_calls_made']}")
                    
                    # Log the final output
                    self.logger.info("="*70)
                    self.logger.info("LLM GENERATED PREDICTION (Tool-Based):")
                    self.logger.info("="*70)
                    for line in final_text.split('\n'):
                        self.logger.info(line)
                    self.logger.info("="*70)
                    
                    return {
                        "content": final_text,
                        "metrics": total_metrics
                    }
                else:
                    self.logger.warning("LLM response has no text and no function calls")
                    break
        
        # Max turns reached
        self.logger.warning(f"Reached maximum turns ({self.max_turns}) without final answer")
        return {
            "content": "Analysis incomplete: Maximum tool-calling turns reached. Please try rephrasing your question.",
            "metrics": total_metrics
        }

    def _build_initial_prompt(self, query: str, pattern: dict) -> str:
        """
        Build the initial prompt for the LLM with domain context and tool instructions.
        """
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are an expert Vedic astrologer with deep knowledge of classical texts and modern interpretation techniques.

USER QUERY: "{query}"

CURRENT DATE: {current_date}
(Use this to determine "current", "past", or "future" in dasha periods and predictions)

CRITICAL DATA STATUS: 
- Birth details (Date, Time, Place) are ALREADY in the database.
- User Name: {self.user_context.get('name', 'User') if self.user_context else 'User'}
- User Gender: {self.user_context.get('gender', 'Unknown') if self.user_context else 'Unknown'}
- DO NOT ask the user for birth details, date, time, or place. 

DOMAIN ANALYSIS: {pattern.get('description', 'General')}

ANALYSIS GUIDANCE:
{pattern.get('prompt_guidance', 'Analyze the query using available tools.')}

DOMAIN CONTEXT:
- Focus Houses: {', '.join(map(str, pattern.get('focus_houses', [])))}
- Focus Planets: {', '.join(pattern.get('focus_planets', []))}

RECOMMENDED CHARTS FOR THIS DOMAIN:
{self._format_required_charts(pattern.get('required_charts', {}))}

HOUSE SIGNIFICANCE:
{self._format_house_significance(pattern.get('house_significance', {}))}

PLANETARY ROLES (Vedic Significance):
{self._format_planetary_roles(pattern.get('focus_planets', []))}

AVAILABLE TOOLS & OUTPUT STRUCTURE:

1. **get_house_data(houses: list, chart: str)**
   Returns: House occupants, sign, and lord for each house
   Output fields:
   - `occupants`: Planets currently in this house
   - `sign`: Zodiac sign occupying this house
   - `lord`: Planetary lord of the sign in this house
   - `lord_placed_in`: Which house the lord is currently placed in

2. **get_planet_details(planets: list, chart: str)**
   Returns: Detailed position and dignity for each planet
   Output fields:
   - `sign`: Current zodiac sign
   - `house`: House number (1-12)
   - `degree`: Exact degree within sign
   - `nakshatra`: Lunar mansion
   - `dignity`: Exalted/Debilitated/Own Sign/Neutral
   - `retrograde`: True if moving backward

3. **get_planet_linkage(houses: list, chart: str)** ⭐ MOST IMPORTANT
   Returns TWO critical structures:
   
   A. **linkage_analysis** - House-by-house lord chains:
      For each focal house:
      - `focal_house`: The house being analyzed
      - `focal_sign`: Zodiac sign in that house
      - `lord_chain`: Information about the house lord:
        * `planet`: Name of the lord
        * `rules_house`: Which house it rules (same as focal_house)
        * `current_placement`: Where the lord actually is:
          - `house`: Current house number
          - `sign`: Current sign
          - `degree`: Exact degree
        * `co_tenants`: Planets conjunct with this lord (< 12°):
          - `planet`: Name of co-tenant
          - `degree`: Their degree
          - `degree_difference`: Gap between them
          - `is_conjunct`: True if < 12°
        * `host_dispositor`: Lord of the sign where this planet sits
        * `bhavat_bhavam_distance`: Anti-clockwise distance (inclusive) from focal_house to where lord is placed
          Example: If lord of H1 is in H7, count 1→2→3→4→5→6→7 = 7 houses
      - `occupants_chain`: Planets sitting IN the focal house:
        * `planet`: Name
        * `degree`: Exact degree
        * `natural_houses`: Where this planet naturally rules (Kal-Purush)
        * `displacement_distance`: How far from natural position
        * `planets_in_natural_house`: Which planets are in this planet's natural home

   B. **conjunctions_enriched** - Planet-centric conjunction data:
      - `total_planets_in_conjunctions`: Count of planets in any conjunction
      - `planets`: Dictionary where each key is a planet name involved in conjunctions
        Each planet has:
        * `linkage_info`: Positional and linkage data:
          - `rules_house`: (if applicable) Which house this planet rules
          - `current_house`: Where it's currently placed
          - `current_sign`: Current zodiac sign
          - `degree`: Exact degree
          - `displacement`: Distance from natural position (if applicable)
          - `conjunct_with`: List of planets < 12° away:
            + `planet`: Name of conjunct planet
            + `degree_difference`: Exact gap in degrees
        * `roles`: Complete symbolic meanings from planet_roles.json:
          - `Essence`: Core archetype (e.g., "King" for Sun)
          - `Nature`: Temperament (hot/cold, dry/moist, etc.)
          - `Rulership`: Direction, day, color, season
          - `Domains`: Life areas governed
          - `Career`: Professional significations
          - `Body_Parts`: Physical body parts ruled
          - `Psychology_Positive`: Benefits when well-placed
          - `Psychology_Afflicted`: Problems when afflicted
          - `Health`: Medical conditions
          - `Products`: Material items
          - `Locations`: Physical places
          - `Fundamental`: Core philosophical principle

4. **get_panchanga()**
   Returns birth time factors: Tithi, Nakshatra, Yoga, Karana, sunrise/sunset times

5. **get_dasha_periods(planet: str, time_period: str, scope: str)**
   Returns Vimshottari Dasha periods with optional filtering:
   - `planet`: Filter by planet (e.g., "Saturn", "Jupiter") - optional
   - `time_period`: "current", "past", "future", or year (e.g., "2025") - optional
   - `scope`: "all", "mahadasha_only", or "antardasha_only" - optional

6. **get_divisional_chart_ascendant(chart: str)**
   Returns ascendant details for specified divisional chart

7. **get_chart_comparison(chart1: str, chart2: str, planet: str)**
   Compare a planet's position across two charts

CRITICAL DATA INTERPRETATION GUIDELINES:

**Understanding Bhavat Bhavam Distance:**
- Counts anti-clockwise (inclusive) from focal_house to where lord sits
- Distance of 7 means strong "Bhavat Bhavam" yoga (7th from 7th = 1st principle)
- Shows how the lord "reflects back" energy to its ruled house

**Understanding Displacement:**
- How far a planet is from its natural Kal-Purush position
- Low displacement (1-2) = comfortable, acting naturally
- High displacement (6+) = uncomfortable, karmic lessons

**Understanding Conjunctions:**
- Planets < 12° apart influence each other
- Check `conjunct_with` list for degree_difference
- Tighter conjunction (< 3°) = stronger blending
- Use `roles` data to understand HOW planets blend

**Understanding Linkage Chain:**
- Trace: Focal House → Its Lord → Lord's Position → Lord's Dispositor
- This shows the "energy flow" through the chart
- Co-tenants modify the lord's ability to deliver results

CRITICAL INSTRUCTIONS:

Step 1: GATHER DATA STRATEGICALLY
- Stick to FOCUS HOUSES, FOCUS PLANETS, and RECOMMENDED CHARTS
- DO NOT call charts not in RECOMMENDED CHARTS unless absolutely necessary
- DO NOT call all 12 houses unless query asks for general life reading
- DO NOT repeat tool calls with same arguments
- **START with get_planet_linkage** for focal houses - it gives you both lord chains AND conjunctions
- GRACEFUL FALLBACK: If chart not found, use D1 (Rasi) and note limitation

Step 2: SYNTHESIZE & PREDICT
Once you have sufficient data, provide COMPREHENSIVE NATURAL LANGUAGE PREDICTION:

CRITICAL WRITING STYLE:
- **USE SIMPLE, EVERYDAY ENGLISH**: Write like you're telling a story to a friend
- **MINIMIZE TECHNICAL JARGON**: Avoid terms like "lord", "placement", "aspect", "conjunction" where possible
- **BE NARRATIVE**: Use storytelling style, not technical report style
- **EXPLAIN IN CONTEXT**: Instead of "7th lord in 5th", say "your marriage prospects are connected to romance"
- **USE NORMAL WORDS**: Instead of "malefic", say "challenging"; instead of "benefic", say "supportive"

## Overview
[4-7 sentence summary in simple, story-like language - paint a picture of their life situation]

## Key Factors
[Explain which areas of life influence the outcome, using everyday language]

## Detailed Analysis
[Deep dive with MINIMAL jargon - focus on what it MEANS for their life, not just positions]
[Use natural language: "This shows...", "What's interesting is...", "The key here is..."]
[Explain WHY things matter in a way anyone can understand]

## Prediction
**Answer:** [Clear Yes/No/Maybe with confidence level in plain English]
**Timing:** [When this might happen - explain in simple terms]
**Conditions:** [Factors that could change outcome]

Now, start by calling tools strategically, then provide your complete analysis.

"""
        
        return prompt

    def _execute_tool(self, tool_name: str, tool_args: dict):
        """Execute a tool call and return the result."""
        try:
            if tool_name == "get_house_data":
                return self.tools.get_house_data(**tool_args)
            elif tool_name == "get_planet_details":
                return self.tools.get_planet_details(**tool_args)
            elif tool_name == "get_panchanga":
                return self.tools.get_panchanga()
            elif tool_name == "get_dasha_periods":
                return self.tools.get_dasha_periods(**tool_args)
            elif tool_name == "get_divisional_chart_ascendant":
                return self.tools.get_divisional_chart_ascendant(**tool_args)
            # elif tool_name == "get_special_yogas":
            #     return self.tools.get_special_yogas()
            elif tool_name == "get_chart_comparison":
                return self.tools.get_chart_comparison(**tool_args)
            elif tool_name == "get_planet_linkage":
                return self.tools.get_planet_linkage(**tool_args)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": f"Tool execution failed: {str(e)}"}

    def _format_house_significance(self, house_sig: dict) -> str:
        """Format house significance."""
        if not house_sig:
            return "No specific house significance provided."
        lines = []
        for house, sig in house_sig.items():
            lines.append(f"  • House {house}: {sig}")
        return "\n".join(lines)

    def _format_required_charts(self, required_charts: dict) -> str:
        """Format required charts with their significance."""
        if not required_charts:
            return "No specific charts required for this domain."
        if isinstance(required_charts, list):  # Backward compatibility
            return ", ".join(required_charts)
        lines = []
        for chart, significance in required_charts.items():
            lines.append(f"  • {chart}: {significance}")
        return "\n".join(lines)


    def _format_planetary_roles(self, focus_planets: list) -> str:
        """Format planetary roles based on common data and domain focus."""
        if not self.common_planet_roles:
            return "No planetary significance data available."
        
        lines = []
        # If no focus planets specified, show all common ones
        planets_to_show = focus_planets if focus_planets else list(self.common_planet_roles.keys())
        
        for planet in planets_to_show:
            role = self.common_planet_roles.get(planet)
            if role:
                if isinstance(role, dict):
                    lines.append(f"  • {planet}:")
                    for k, v in role.items():
                        lines.append(f"    - {k}: {v}")
                else:
                    lines.append(f"  • {planet}: {role}")
        
        return "\n".join(lines) if lines else "No matching planetary roles found."
    
    def _fallback_analysis(self, query: str, pattern: dict, current_metrics: dict):
        """
        Fallback to simple analysis without tool calling when rate limits are hit.
        """
        self.logger.info("Using fallback analysis without tool calling")
        
        # Import the old house_mapper for fallback
        from house_mapper import HouseMapper
        mapper = HouseMapper()
        
        # Extract data the old way (requires loading once)
        self.logger.info("Fetching data for fallback analysis...")
        from horoscope_manager import HoroscopeManager
        hm = HoroscopeManager()
        if self.request_id:
            horoscope_data = hm.load_from_mongodb(self.request_id)
        else:
            horoscope_data = hm.load_from_mongodb_by_email(self.email)

        extracted_data = mapper.extract_data_for_pattern(horoscope_data, pattern)
        
        # Build a simple prompt
        prompt = f"""You are an expert Vedic astrologer.

USER QUERY: "{query}"

ASTROLOGICAL DATA:
{json.dumps(extracted_data, indent=2)}

ANALYSIS GUIDANCE:
{pattern.get('prompt_guidance', 'Analyze the data provided.')}

Provide a comprehensive natural language prediction based on this data.
"""
        
        # Simple LLM call without tools
        result = self.llm.generate_content(prompt)
        
        # Aggregate metrics
        if "metrics" in result:
            for key in ["duration_seconds", "input_tokens", "output_tokens", "cost_usd"]:
                if key in result["metrics"]:
                    current_metrics[key] += result["metrics"][key]
        
        return {
            "content": result.get("content", "Error in fallback analysis"),
            "metrics": current_metrics
        }

