from __future__ import annotations

from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow

from .agents import DASHA_ANALYST


class DashaTeam(GraphFlow):
    """Single-agent team for analysing Vimshottari timelines."""

    def __init__(self) -> None:
        builder = DiGraphBuilder().add_node(DASHA_ANALYST)
        builder.set_entry_point(DASHA_ANALYST)
        graph = builder.build()

        super().__init__(
            participants=[DASHA_ANALYST],
            graph=graph,
            termination_condition=MaxMessageTermination(6),
        )

