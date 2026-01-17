from __future__ import annotations

from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow

from .agents import C_Y_A, DEEP_DIVER, DEEP_DIVER_RESPONDER, H_s_p, PSY_SIGNATURE, p_n


class BirthChartTeam(GraphFlow):
    """Graph-driven orchestrator for Lagna-level analysis."""

    def __init__(self) -> None:
        builder = (
            DiGraphBuilder()
            .add_node(H_s_p)
            .add_node(p_n)
            .add_node(C_Y_A)
            .add_node(DEEP_DIVER)
            .add_node(DEEP_DIVER_RESPONDER)
            .add_node(PSY_SIGNATURE)
            .add_edge(H_s_p, p_n)
            .add_edge(p_n, C_Y_A)
            .add_edge(C_Y_A, DEEP_DIVER, activation_group="analysis", activation_condition="any")
            .add_edge(DEEP_DIVER, DEEP_DIVER_RESPONDER, condition="[ASK_HUMAN]", activation_group="needs_human")
            .add_edge(
                DEEP_DIVER_RESPONDER,
                DEEP_DIVER,
                condition="[HUMAN_REPLY]",
                activation_group="human_reply",
                activation_condition="any",
            )
            .add_edge(DEEP_DIVER, PSY_SIGNATURE, condition="[PROCEED_TO_PSY]", activation_group="handoff")
        )
        builder.set_entry_point(H_s_p)
        graph = builder.build()

        super().__init__(
            participants=[H_s_p, p_n, C_Y_A, DEEP_DIVER, DEEP_DIVER_RESPONDER, PSY_SIGNATURE],
            graph=graph,
            termination_condition=MaxMessageTermination(25),
        )

