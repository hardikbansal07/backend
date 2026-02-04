import os
from autogen_agentchat.agents import AssistantAgent
from config.models import build_chat_completion_client

# Load Prompts
def load_prompt(filename):
    base_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "library")
    with open(os.path.join(base_path, filename), "r", encoding="utf-8") as f:
        return f.read()

# Factory function to create fresh instances
def get_principal(model_client=None):
    if not model_client:
        model_client = build_chat_completion_client()
    
    maha_rishi = AssistantAgent(
        name="MahaRishi",
        model_client=model_client,
        system_message=load_prompt("synthesis_rules.md"),
        description="synthesizes reports from all specialists into a final coherent prediction."
    )
    
    return maha_rishi
