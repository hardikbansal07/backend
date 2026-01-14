from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from ..config.models import build_chat_completion_client

model_client = build_chat_completion_client()

sm_dasha = (
    "You receive a detailed Vimshottari timeline as JSON. Analyse the user's question to detect explicit or implied time frames and treat every astrological linkage as a hypothesis to test."
    " Identify the relevant Mahadasha and zoom into the Antar/Pratyantar segments covering that span, but always state confidence levels, evidence gaps, and mundane explanations."
    " Summarise potential impacts on career and relationships with exact date ranges, then advise how a skeptic could validate or falsify each claim in real life."
    " Keep the response structured, concise, and never repeat raw JSON or speculate beyond supplied data."
)

DASHA_ANALYST = AssistantAgent(
    name="DASHA_ANALYST",
    description="Evaluates the Vimshottari timeline and highlights the most relevant sub-periods.",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm_dasha,
)
