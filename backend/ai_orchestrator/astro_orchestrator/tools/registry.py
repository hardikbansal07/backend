from __future__ import annotations

from autogen_agentchat.tools import TeamTool

from ..birth_chart.team import BirthChartTeam
from ..d_series.team import DSeriesTeam
from ..dasha.team import DashaTeam


def create_birth_chart_tool() -> TeamTool:
    team = BirthChartTeam()
    return TeamTool(
        team=team,
        name="birth_chart_team",
        description="Runs Lagna-level analysis loops and returns a packet.",
        return_value_as_last_message=True,
    )


def create_dseries_tool() -> TeamTool:
    team = DSeriesTeam()
    return TeamTool(
        team=team,
        name="dseries_team",
        description="Selects D-series specialists and returns synthesis.",
        return_value_as_last_message=True,
    )


def create_dasha_tool() -> TeamTool:
    team = DashaTeam()
    return TeamTool(
        team=team,
        name="dasha_team",
        description="Analyses Mahadasha, Antar Dasha, and Prati Antar Dasha phases.",
        return_value_as_last_message=True,
    )
