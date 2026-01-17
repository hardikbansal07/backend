from __future__ import annotations

from typing import Sequence

from autogen_agentchat.agents import AssistantAgent

from ..config.models import build_chat_completion_client

# Disable parallel tool calls by default, as many agents use TeamTool/AgentTool internally.
model_client = build_chat_completion_client(parallel_tool_calls=False)

sm_review = (
    "You are the Intake Skeptic for the Astro Orchestrator. Approach every first message with a researcher mindset: demand specific, testable details before forwarding anything to analysis.\n\n"
    "Decision guardrails (apply in order):\n"
    "1) Pure greetings or vague curiosities are insufficient evidence. Reply with FOLLOW_UP: challenging the user to supply a concrete area, intent, and timeframe.\n"
    "2) If the brief hints at astrology claims without data (no life area, no objective, no dates/periods), issue FOLLOW_UP: asking for the single piece of information that would let a skeptic verify the claim.\n"
    "3) Only when the request already states a falsifiable astrology task (life area + intent + timeframe cues) do you respond with PROCEED: summarising the task crisply for the analyst team.\n\n"
    "Hard rules:\n"
    "- Output MUST start with either 'PROCEED:' or 'FOLLOW_UP:' and nothing else.\n"
    "- For FOLLOW_UP, immediately after the prefix, introduce yourself as 'Namaste! I'm AI developed by Astro Care.' and explain why tighter evidence is required.\n"
    "- Never perform chart analysis yourself or hand-wave uncertainty; flag it directly.\n"
    "- Keep tone warm yet forthright, Indian English, one or two sentences max.\n\n"
    "Examples:\n"
    "- Input: 'Hi' -> FOLLOW_UP: Namaste! I'm AI developed by Astro Care. Please share the area, intent, and timeframe so we can test something real.\n"
    "- Input: 'Evaluate my career for 2025' -> PROCEED: Stress-test the native's 2025 career prospects, highlighting risks, evidence gaps, and decision windows.\n"
)


def birth_chart_packet_to_highlights(packet: object) -> str:
    '''Convert Lagna packets into concise highlights without using a model client.'''
    if packet is None:
        return ''
    if isinstance(packet, str):
        return packet.strip()
    if isinstance(packet, Sequence) and not isinstance(packet, (str, bytes, dict)):
        parts = [birth_chart_packet_to_highlights(item) for item in packet]
        return '\n'.join(part for part in parts if part)
    if isinstance(packet, dict):
        lines: list[str] = []
        asc = packet.get('ascendantSign') or packet.get('ascendant_sign')
        if asc:
            lines.append(f'Ascendant: {asc}')
        house_notes: list[str] = []
        for house in packet.get('houses', []):
            if not isinstance(house, dict):
                continue
            number = house.get('index') or house.get('number')
            sign = house.get('sign') or house.get('signNumber')
            occupants = house.get('items') or house.get('planets') or []
            occupant_text = ', '.join(str(item) for item in occupants if item)
            fragments: list[str] = []
            if number is not None:
                fragments.append(f'House {number}')
            if sign:
                fragments.append(f'sign {sign}')
            text = ' '.join(fragments).strip()
            if occupant_text:
                text = (text + ' -> ' if text else '') + occupant_text
            if text:
                house_notes.append(text)
        if house_notes:
            lines.append('Key houses\n- ' + '\n- '.join(house_notes))
        planet_notes: list[str] = []
        for planet in packet.get('planets', []):
            if not isinstance(planet, dict):
                continue
            name = planet.get('name')
            if not name:
                continue
            traits: list[str] = []
            sign = planet.get('sign')
            house = planet.get('house')
            dignity = planet.get('dignity')
            if sign:
                traits.append(f'sign {sign}')
            if house is not None:
                traits.append(f'house {house}')
            if dignity:
                traits.append(f'dignity {dignity}')
            if planet.get('isCombust'):
                traits.append('combust')
            if planet.get('retrograde'):
                traits.append('retrograde')
            if traits:
                planet_notes.append(f"{name}: " + ', '.join(traits))
            else:
                planet_notes.append(str(name))
        if planet_notes:
            lines.append('Planet strengths\n- ' + '\n- '.join(planet_notes))
        yoga_notes: list[str] = []
        for yoga in packet.get('yogas', []):
            if isinstance(yoga, dict):
                name = yoga.get('name') or yoga.get('code')
                effect = yoga.get('effect') or yoga.get('outcome')
                if name and effect:
                    yoga_notes.append(f"{name}: {effect}")
                elif name:
                    yoga_notes.append(str(name))
            elif yoga:
                yoga_notes.append(str(yoga))
        if yoga_notes:
            lines.append('Yogas\n- ' + '\n- '.join(yoga_notes))
        return '\n'.join(line for line in lines if line)
    return str(packet).strip()

sm_master_writer = (
    "You are an astro-skeptical researcher asked to summarise chart-derived hypotheses. Treat every pattern as a claim needing evidence.\n"
    "Inputs arrive from: (1) Lagna synthesis, (2) D-series synthesis, (3) Dasha timeline notes, plus the user brief.\n"
    "Rules: never fabricate chart data, never imply certainty, cite the source stream (Lagna/D-series/Dasha) for each claim, and highlight where astrology lacks empirical backing.\n"
    "Structure your Markdown report as follows:\n"
    "# Reality Check - two sentences stating what the skeptic can or cannot validate.\n"
    "# Chart Hypotheses - up to four bullets. Each bullet: [Source] statement (<22 words) + note on assumptions or missing proof.\n"
    "# Contradictions & Gaps - bullets calling out clashes between sources or weak evidence.\n"
    "# Timeline Watch - table with <=3 rows (Window | Astrology Claim | How to fact-check in real life).\n"
    "# Action Experiments - numbered list (max four) suggesting pragmatic steps or observations the user can run to verify claims.\n"
    "Close with one succinct disclaimer reminding the user that astrology interpretations are speculative."
)


def create_review_agent() -> AssistantAgent:
    '''Factory for the intake reviewer.'''
    return AssistantAgent(
        name='REVIEW_GATE',
        description='Screens user questions before triggering deep analysis.',
        model_client=model_client,
        model_client_stream=True,
        system_message=sm_review,
    )


def create_master_writer_agent() -> AssistantAgent:
    '''Factory for the final-stage synthesis agent.'''
    return AssistantAgent(
        name='MASTER_WRITER',
        description='Hyper-analyst that fuses Lagna, D-series, and Dasha insights into the final report.',
        model_client=model_client,
        model_client_stream=True,
        system_message=sm_master_writer,
    )

__all__ = [
    'birth_chart_packet_to_highlights',
    'create_master_writer_agent',
    'create_review_agent',
]
