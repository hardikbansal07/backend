from __future__ import annotations

from autogen_agentchat.conditions import FunctionalTermination, MaxMessageTermination
from autogen_agentchat.teams import MagenticOneGroupChat

from ..config.models import build_chat_completion_client
from .agents import (
    D10_DASAMSA,
    D11_RUDRAMSA,
    D12_DVADASAMSA,
    D16_SHODASHAMSA,
    D20_VIMSHAMSA,
    D24_CHATURVIMSHAMSA,
    D27_SAPTAVIMSHAMSA,
    D2_HORA,
    D30_TRIMSAMSA,
    D3_DREKKANA,
    D40_KHAVEDAMSA,
    D45_AKSHAVEDAMSA,
    D4_CHATURTHAMSA,
    D5_PANCHAMSA,
    D60_SHASHTIAMSHA,
    D6_SHASHTAMSA,
    D7_SAPTAMSA,
    D8_ASHTAMSA,
    D9_NAVAMSA,
    D_SERIES_STRATEGIST,
)


def _termination_condition() -> MaxMessageTermination | FunctionalTermination:
    max_messages = MaxMessageTermination(40)

    async def _status_stop(messages):  # pragma: no cover - simple guard
        for message in messages:
            content = getattr(message, "content", "")
            if isinstance(content, str) and "FINALISE" in content:
                return True
        return False

    return max_messages | FunctionalTermination(_status_stop)


class DSeriesTeam(MagenticOneGroupChat):
    """MagenticOne team orchestrating D-series specialists."""

    def __init__(self) -> None:
        participants = [
            D2_HORA,
            D3_DREKKANA,
            D4_CHATURTHAMSA,
            D5_PANCHAMSA,
            D6_SHASHTAMSA,
            D7_SAPTAMSA,
            D8_ASHTAMSA,
            D9_NAVAMSA,
            D10_DASAMSA,
            D11_RUDRAMSA,
            D12_DVADASAMSA,
            D16_SHODASHAMSA,
            D20_VIMSHAMSA,
            D24_CHATURVIMSHAMSA,
            D27_SAPTAVIMSHAMSA,
            D30_TRIMSAMSA,
            D40_KHAVEDAMSA,
            D45_AKSHAVEDAMSA,
            D60_SHASHTIAMSHA,
            D_SERIES_STRATEGIST,
        ]
        super().__init__(
            participants=participants,
            model_client=build_chat_completion_client(),
            termination_condition=_termination_condition(),
            max_turns=20,
        )

