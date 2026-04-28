import json
from typing import Optional
from llm_interface import GeminiLLM
from sub_agent import SubAgent
from horoscope_manager import HoroscopeManager
from logger_config import setup_logger
import re


class MainAgent:
    def __init__(self, patterns_path=None):
        if patterns_path is None:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            patterns_path = os.path.join(base_dir, "patterns.json")
            
        self.logger = setup_logger("MainAgent")
        self.llm = GeminiLLM()
        self.sub_agent = SubAgent()
        self.horoscope_manager = HoroscopeManager()
        self.patterns = self._load_patterns(patterns_path)
        self.request_id = None
        self.request_id = None
        self.email = None
        self.user_context = None

    def _load_patterns(self, path):
        """Load domain patterns from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
                self.logger.info(f"Loaded {len(patterns)} analysis patterns from {path}")
                return patterns
        except FileNotFoundError:
            self.logger.error(f"Patterns file not found at {path}")
            return {}

    def set_identity(self, request_id: Optional[str] = None, email: Optional[str] = None, user_context: Optional[dict] = None):
        """Set identity for analysis."""
        self.request_id = request_id
        self.email = email
        self.user_context = user_context
        self.sub_agent.set_identity(request_id, email, user_context)
        self.logger.info(f"Identity set in MainAgent: ID={request_id}, Email={email}, Context={user_context}")

    def analyze_intent(self, query: str):
        """Analyze user query intent using LLM."""
        if self._is_explicitly_out_of_scope(query):
            self.logger.info("Rule-based out_of_scope detected before LLM intent detection.")
            return {
                "intent": "out_of_scope",
                "confidence": 1.0,
                "reasoning": "Explicit non-love domain detected by deterministic rules.",
                "method": "rule_based"
            }, {}
        return self._analyze_intent_with_llm(query)

    def _is_explicitly_out_of_scope(self, query: str) -> bool:
        """
        Deterministic guardrail to keep Love AI focused on romance topics.
        Returns True only when the query is clearly non-love and does not include love intent.
        """
        query_lower = query.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", query_lower)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        love_keywords = [
            "love", "romance", "romantic", "dating", "relationship",
            "partner", "spouse", "marriage", "crush", "breakup",
            "boyfriend", "girlfriend", "husband", "wife", "compatibility"
        ]
        out_of_scope_keywords = [
            "family", "parents", "mother", "father", "siblings",
            "career", "carrier", "job", "jobs", "work", "profession",
            "business", "startup", "education", "study", "exam",
            "finance", "financial", "money", "income", "salary",
            "resource", "resources", "investment", "investments",
            "property", "wealth", "growth"
        ]

        has_love_signal = any(k in normalized for k in love_keywords)
        has_out_of_scope_signal = any(k in normalized for k in out_of_scope_keywords)
        return has_out_of_scope_signal and not has_love_signal

    def _analyze_intent_with_llm(self, query: str):
        """
        Uses LLM to determine the intent of the query.
        
        Args:
            query: User's question
            
        Returns:
            Tuple of (intent_data, metrics)
        """
        available_intents = []
        for intent_name, pattern in self.patterns.items():
            available_intents.append({
                "name": intent_name,
                "description": pattern.get("description", "")
            })
        
        prompt = f"""Analyze the following user query and determine the most relevant astrology analysis domain. YOU ARE A STRICT LOVE, ROMANCE, DATING AND EMOTIONAL ASTROLOGY AGENT. 

User Query: "{query}"

Available Domains:
{json.dumps(available_intents, indent=2)}

Output valid JSON only:
{{
    "intent": "domain_name",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

CRITICAL INSTRUCTION: If the user EXPLICITLY asks about family, career, growth, finance, jobs, education, business, or other general life prospects non-related to love/romance, you MUST set "intent" to "out_of_scope". 
However, if the query is vague, emotional, conversational, or general (e.g., 'give me a suggestion', 'I feel lost', 'help me'), you MUST ASSUME it is related to their emotional/dating profile and map it to an available domain (do NOT set it to out_of_scope).
"""
        
        self.logger.info(f"Analyzing intent with LLM for query: '{query}'")
        result_obj = self.llm.generate_json(prompt)
        result = result_obj.get("content", {})
        metrics = result_obj.get("metrics", {})
        
        result["method"] = "llm"
        self.logger.debug(f"LLM Intent Detection result: {result}")
        return result, metrics

    def run_flow(self, query: str):
        """
        Main execution flow for astrological analysis.
        
        Args:
            query: User's question
            
        Returns:
            Tuple of (response_text, total_metrics)
        """
        self.logger.info(f"--- Starting Analysis Flow ---")
        self.logger.info(f"Query: {query}")
        
        total_metrics = {
            "duration_seconds": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        
        # Helper to sum metrics
        def add_metrics(new_m):
            for k in total_metrics:
                if k in new_m:
                    total_metrics[k] += new_m[k]

        # Check if identity is set
        if not self.request_id and not self.email:
            self.logger.error("No identity context available")
            return "Error: No user identity provided. Please specify Email or Request ID.", total_metrics

        # 1. Intent Detection
        self.logger.info("Step 1: Detecting query intent...")
        intent_data, intent_metrics = self.analyze_intent(query)
        add_metrics(intent_metrics)
        
        intent = intent_data.get("intent")
        confidence = intent_data.get("confidence", 0.0)
        method = intent_data.get("method", "unknown")
        
        if intent == "out_of_scope":
            self.logger.warning(f"Out of scope intent detected.")
            return "I am a specific AI designed only for Love, Dating, Romance, and Emotional patterns. I cannot answer queries related to family, career, growth, finance, or general life prospects. Please use the 'General Vedic AI' for those questions.", total_metrics

        if intent not in self.patterns:
            self.logger.warning(f"Unknown intent detected: {intent}")
            intent = list(self.patterns.keys())[0] if self.patterns else "unknown"
            self.logger.info(f"Defaulting to '{intent}' analysis")

        # 2. Get Pattern
        if intent in self.patterns:
            pattern = self.patterns[intent]
        else:
            self.logger.error("No patterns available for analysis.")
            return "Server configuration error: No analysis patterns loaded.", total_metrics
        self.logger.info(f"Domain: {pattern.get('description', 'Unknown')}")
        
        # 3. Delegate to Sub Agent
        self.logger.info("Step 2: Performing detailed astrological analysis...")
        analysis_result_obj = self.sub_agent.analyze(query, pattern)
        
        # Extract content and metrics
        content = analysis_result_obj.get("content", "Error in analysis")
        sub_metrics = analysis_result_obj.get("metrics", {})
        add_metrics(sub_metrics)
        
        self.logger.info(f"Analysis completed successfully")
        self.logger.info(f"Total Tokens: {total_metrics['input_tokens'] + total_metrics['output_tokens']}")
        
        # 3. Return Final Response
        return content, total_metrics


if __name__ == "__main__":
    # Test
    agent = MainAgent()
    
    # Set identity (replaces set_horoscope_data)
    agent.set_identity(email="user@example.com")
    
    # Run analysis
    response, metrics = agent.run_flow("Will I find love soon?")
    print(response)
