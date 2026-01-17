from __future__ import annotations

from typing import Dict, List, Mapping, Optional

from autogen_agentchat.state import BaseState
from pydantic import Field


class LagnaLoopState(BaseState):
    type: str = Field(default="LagnaLoopState", frozen=True)
    loop_index: int = 0
    counter_questions: List[str] = Field(default_factory=list)
    clarified_answers: List[str] = Field(default_factory=list)


class DSeriesLedgerState(BaseState):
    type: str = Field(default="DSeriesLedgerState", frozen=True)
    facts: str = ""
    plan: str = ""
    progress: Mapping[str, str] = Field(default_factory=dict)


class CombinedForecastState(BaseState):
    type: str = Field(default="CombinedForecastState", frozen=True)
    birth_chart_packet: Optional[Dict[str, str]] = None
    dasha_packet: Optional[Dict[str, str]] = None
    markdown_path: Optional[str] = None

