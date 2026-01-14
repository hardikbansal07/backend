from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent

from ..config.models import build_chat_completion_client

model_client = build_chat_completion_client()

sm1 = ("You are the Lagna skeptic. Parse the summary to extract ascendant context, planetary strengths, and dignity claims, but tag each insight with confidence levels and note any missing evidence.")
sm2 = ("You narrate planetary roles only as hypotheses. Link chart factors to observable life outcomes, flagging every assumption and pointing out non-astrological explanations the user should investigate.")
sm3 = ("Inventory any cited yogas or combinations, explain their supposed activation conditions, and underline where classical doctrine lacks empirical support or conflicts with the dataset.")
sm4 = ("You are the Deep Diver skeptic. Audit prior Lagna insights, surface contradictions or blind spots, and keep track of what is already evidenced.\n"
    "You must ask exactly one clarifying follow-up before concluding: prefix it with [ASK_HUMAN], keep it plain Indian English, and spell out why the data point matters for testing the hypothesis.\n"
    "Use short sentences (<= 20 words), empathetic yet forthright tone, and after the human reply (tagged [HUMAN_REPLY]) restate the new fact, note its reliability, update your scratchpad, then proceed.\n"
    "When you are convinced you have enough evidence, hand off to PSY_SIGNATURE with [PROCEED_TO_PSY] (never combine with [ASK_HUMAN]).")
sm5 = ("Synthesize cautious psychological and behavioural hypotheses, explicitly labelling speculative sections and contrasting them with real-world behaviours the user could actually observe.")

def _deep_diver_human_input(prompt: str, cancellation_token=None) -> str:
    """Collect human clarification and keep prompting until we receive a real response."""
    text = prompt.strip()
    if text.startswith('[ASK_HUMAN]'):
        text = text[len('[ASK_HUMAN]'):].strip()
    while True:
        try:
            reply = input("\nDeep Diver follow-up -> " + text + "\nYour reply: ")
        except (EOFError, KeyboardInterrupt):
            print("\nManual input is required for the Deep Diver to continue. Please provide the clarification above.")
            continue
        cleaned = reply.strip()
        if cleaned:
            return f'[HUMAN_REPLY] {cleaned}'
        print("\nPlease share a clarification so the Deep Diver can proceed.")

H_s_p = AssistantAgent(
    name="H_s_p",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm1,
)

p_n = AssistantAgent(
    name="p_n",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm2,
)

C_Y_A = AssistantAgent(
    name="C_Y_A",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm3,
)

DEEP_DIVER = AssistantAgent(
    name="DEEP_DIVER",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm4,
)

DEEP_DIVER_RESPONDER = UserProxyAgent(
    name="DEEP_DIVER_RESPONDER",
    description="Human collaborator who answers Deep Diver follow-up queries.",
    input_func=_deep_diver_human_input,
)


PSY_SIGNATURE = AssistantAgent(
    name="PSY_SIGNATURE",
    model_client=model_client,
    model_client_stream=True,
    system_message=sm5,
)
