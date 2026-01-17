from __future__ import annotations

from typing import Callable

from autogen_agentchat.messages import MessageFactory
from pydantic import BaseModel, Field


class PlanetInsight(BaseModel):
    planet: str = Field(..., description="Planet name")
    house: str = Field(..., description="House information")
    narrative: str = Field(..., description="Summary insight")


class YogaSummary(BaseModel):
    name: str
    effect: str
    activation_timing: str | None = None


class PsychProfile(BaseModel):
    archetype: str
    traits: list[str]
    cautions: list[str]


class DashaWindow(BaseModel):
    period: str
    focus: str
    confidence: float = 0.5


class CombinedForecast(BaseModel):
    headline: str
    highlights: list[str]
    markdown_report: str


def register_default_messages(factory: MessageFactory) -> None:
    """Register orchestrator message models with the factory."""

    for model in (PlanetInsight, YogaSummary, PsychProfile, DashaWindow, CombinedForecast):
        if not factory.is_registered(model):
            factory.register(model)
