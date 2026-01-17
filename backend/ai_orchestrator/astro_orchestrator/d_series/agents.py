from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from ..config.models import build_chat_completion_client

model_client = build_chat_completion_client()

D2_HORA = AssistantAgent(
    name="D2_HORA",
    description="Hora (D2) - wealth, resources, material prosperity.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Analyse the Hora (D2) chart and summarise themes around wealth and resources. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D3_DREKKANA = AssistantAgent(
    name="D3_DREKKANA",
    description="Drekkana (D3) - siblings, courage, co-borns.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Interpret D3 for siblings, teamwork, courage, and shared ventures. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D4_CHATURTHAMSA = AssistantAgent(
    name="D4_CHATURTHAMSA",
    description="Chaturthamsa (D4) - property, home, fortune, mother.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Assess D4 for property, home life, motherly support, and fortune. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D5_PANCHAMSA = AssistantAgent(
    name="D5_PANCHAMSA",
    description="Panchamsa (D5) - power, authority, spiritual inclinations.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Focus on D5 to gauge authority, leadership, and spiritual inclinations. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D6_SHASHTAMSA = AssistantAgent(
    name="D6_SHASHTAMSA",
    description="Shashtamsa (D6) - health, diseases, weaknesses.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Review D6 for health strengths, vulnerabilities, and chronic issues. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D7_SAPTAMSA = AssistantAgent(
    name="D7_SAPTAMSA",
    description="Saptamsa (D7) - children, creativity, lineage.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Use D7 to outline fertility, creativity, and lineage themes. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D8_ASHTAMSA = AssistantAgent(
    name="D8_ASHTAMSA",
    description="Ashtamsa (D8) - longevity, obstacles, sudden events.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Evaluate D8 for longevity, crises, and transformation. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D9_NAVAMSA = AssistantAgent(
    name="D9_NAVAMSA",
    description="Navamsa (D9) - marriage, dharma, spouse, fortune.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Analyse D9 for marriage, dharma alignment, spouse, and fortune. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D10_DASAMSA = AssistantAgent(
    name="D10_DASAMSA",
    description="Dasamsa (D10) - career, profession, public life.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Interpret D10 to draw career and public life insights. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D11_RUDRAMSA = AssistantAgent(
    name="D11_RUDRAMSA",
    description="Rudramsa (D11) - death, chronic ailments, destruction.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Review D11 for stress tests, chronic challenges, and endings. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D12_DVADASAMSA = AssistantAgent(
    name="D12_DVADASAMSA",
    description="Dvadasamsa (D12) - parents, ancestry, heredity.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Study D12 for parental lineage, heredity, and ancestral influence. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D16_SHODASHAMSA = AssistantAgent(
    name="D16_SHODASHAMSA",
    description="Shodashamsa (D16) - vehicles, comforts, luxuries.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Look at D16 for vehicles, comforts, and luxuries. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D20_VIMSHAMSA = AssistantAgent(
    name="D20_VIMSHAMSA",
    description="Vimshamsa (D20) - spiritual life, devotion, inner practices.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Use D20 to infer spiritual practice, devotion, and inner life. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D24_CHATURVIMSHAMSA = AssistantAgent(
    name="D24_CHATURVIMSHAMSA",
    description="Chaturvimshamsa (D24) - education, learning, knowledge.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Analyse D24 for education, learning paths, and scholarship. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D27_SAPTAVIMSHAMSA = AssistantAgent(
    name="D27_SAPTAVIMSHAMSA",
    description="Saptavimshamsa (D27) - strengths, weaknesses, inner traits.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Assess D27 for subtle strengths, weaknesses, and temperament. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D30_TRIMSAMSA = AssistantAgent(
    name="D30_TRIMSAMSA",
    description="Trimsamsa (D30) - evils, misfortunes, hidden flaws.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Inspect D30 for hidden flaws, misfortunes, and karmic blemishes. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D40_KHAVEDAMSA = AssistantAgent(
    name="D40_KHAVEDAMSA",
    description="Khavedamsa (D40) - maternal karmas, inherited blessings or curses.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Read D40 for maternal karmas and inherited patterns. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D45_AKSHAVEDAMSA = AssistantAgent(
    name="D45_AKSHAVEDAMSA",
    description="Akshavedamsa (D45) - paternal karmas, spiritual inclinations.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Review D45 for paternal karmas and spiritual inclinations. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D60_SHASHTIAMSHA = AssistantAgent(
    name="D60_SHASHTIAMSHA",
    description="Shashtiamsha (D60) - past-life karma, ultimate destiny, root causes.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Explore D60 for past-life karma, destiny, and root causes. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)

D_SERIES_STRATEGIST = AssistantAgent(
    name="D_SERIES_STRATEGIST",
    description="Synthesises divisional chart findings into a cohesive storyline.",
    model_client=model_client,
    model_client_stream=True,
    system_message="Merge outputs from all D-series specialists into a single narrative. Provide skeptical commentary by flagging weak evidence, suggesting real-world validation, and acknowledging non-astrological factors.",
)
