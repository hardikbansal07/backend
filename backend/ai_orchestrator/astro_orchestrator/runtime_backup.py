from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage

from .birth_chart.team import BirthChartTeam
from .d_series.team import DSeriesTeam
from .dasha.team import DashaTeam
from .main.agents import create_master_writer_agent

LOGGER_NAME = "astro_orchestrator"
logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(LOGGER_NAME)


@dataclass
class TokenUsage:
    prompt: int = 0
    completion: int = 0

    def update(self, models_usage: Optional[Any]) -> None:
        if not models_usage:
            return
        self.prompt += getattr(models_usage, "prompt_tokens", 0)
        self.completion += getattr(models_usage, "completion_tokens", 0)

    @property
    def total(self) -> int:
        return self.prompt + self.completion


@dataclass
class TeamRunResult:
    label: str
    summary: str
    usage: TokenUsage = field(default_factory=TokenUsage)


def _format_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Iterable) and not isinstance(value, (dict, BaseAgentEvent, BaseChatMessage)):
        return "\n".join(_format_content(item) for item in value)
    if hasattr(value, "to_model_text"):
        try:
            return value.to_model_text()  # type: ignore[attr-defined]
        except Exception:
            pass
    if hasattr(value, "content"):
        return _format_content(getattr(value, "content"))
    return str(value)


def _format_message(message: Any) -> str:
    if hasattr(message, "to_model_text"):
        try:
            return message.to_model_text()  # type: ignore[attr-defined]
        except Exception:
            pass
    return _format_content(getattr(message, "content", message))


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_agent_messages(task_result: TaskResult, usage: TokenUsage) -> str:
    outputs: list[str] = []
    for message in task_result.messages:
        source = getattr(message, "source", "")
        if isinstance(source, str) and source.lower() == "user":
            continue
        outputs.append(_format_message(message))
        usage.update(getattr(message, "models_usage", None))
    return "\n".join(outputs)


async def _run_team(team, *, label: str, task: str, verbose_tokens: bool) -> TeamRunResult:
    if verbose_tokens:
        logger.setLevel(logging.INFO)
    usage = TokenUsage()
    final_result: TaskResult | None = None
    async for item in team.run_stream(task=task):
        if isinstance(item, TaskResult):
            final_result = item
            logger.info("%s team completed (%d messages)", label, len(item.messages))
        else:
            summary = _format_message(item)
            source = getattr(item, "source", label)
            if isinstance(source, str) and source.lower() == "user":
                continue
            preview = summary if verbose_tokens else " ".join(summary.split()[:20])
            logger.info("%s -> %s | %s", label, source, preview)
            usage.update(getattr(item, "models_usage", None))
            if verbose_tokens and isinstance(item, BaseChatMessage):
                tokens = summary.split()
                logger.info("%s token stream: %s", source, tokens[: min(len(tokens), 10)])
    if final_result is None:
        raise RuntimeError(f"{label} team did not return a TaskResult")
    summary_text = _extract_agent_messages(final_result, usage)
    await team.reset()
    return TeamRunResult(label=label, summary=summary_text, usage=usage)


async def run_case(
    case_dir: Path,
    question: str,
    detailed_output: Path,
    user_output: Path,
    verbose_tokens: bool,
) -> Dict[str, Any]:
    if not case_dir.exists():
        raise FileNotFoundError(f"Case folder not found: {case_dir}")

    lagna_json = _load_json(case_dir / "lagna.json")
    dasha_json = _load_json(case_dir / "dasha.json")
    d10_json = _load_json(case_dir / "dseries" / "d10.json")

    lagna_task = json.dumps({"lagna_chart": lagna_json}, ensure_ascii=False, indent=2)
    dseries_task = json.dumps({"d10_chart": d10_json}, ensure_ascii=False, indent=2)
    dasha_task = json.dumps({"dasha_timeline": dasha_json}, ensure_ascii=False, indent=2)

    lagna_result = await _run_team(BirthChartTeam(), label="Lagna", task=lagna_task, verbose_tokens=verbose_tokens)
    dseries_result = await _run_team(DSeriesTeam(), label="D-Series", task=dseries_task, verbose_tokens=verbose_tokens)
    dasha_result = await _run_team(DashaTeam(), label="Dasha", task=dasha_task, verbose_tokens=verbose_tokens)

    master_writer = create_master_writer_agent()
    final_prompt = (
        f"User question: {question}\n\n"
        "Birth Chart Insights:\n" + lagna_result.summary + "\n\n"
        "Divisional (D10) Insights:\n" + dseries_result.summary + "\n\n"
        "Dasha Timeline Insights:\n" + dasha_result.summary + "\n\n"
        "Deliver a single consolidated forecast."
    )

    final_usage = TokenUsage()
    final_result = await master_writer.run(task=final_prompt)
    final_summary = _extract_agent_messages(final_result, final_usage)

    detailed_output.parent.mkdir(parents=True, exist_ok=True)
    user_output.parent.mkdir(parents=True, exist_ok=True)

    detailed_report = (
        "# Final Forecast\n" + final_summary + "\n\n"
        "# Birth Chart Insights\n" + lagna_result.summary + "\n\n"
        "# D10 Insights\n" + dseries_result.summary + "\n\n"
        "# Dasha Insights\n" + dasha_result.summary
    )
    detailed_output.write_text(detailed_report, encoding="utf-8")

    user_report = "# Final Forecast\n" + final_summary
    user_output.write_text(user_report, encoding="utf-8")

    logger.info("Detailed report written to %s", detailed_output)
    logger.info("User report written to %s", user_output)

    total_usage = TokenUsage(
        prompt=lagna_result.usage.prompt + dseries_result.usage.prompt + dasha_result.usage.prompt + final_usage.prompt,
        completion=lagna_result.usage.completion
        + dseries_result.usage.completion
        + dasha_result.usage.completion
        + final_usage.completion,
    )

    return {
        "lagna": lagna_result,
        "dseries": dseries_result,
        "dasha": dasha_result,
        "final_summary": final_summary,
        "detailed_output_path": str(detailed_output),
        "user_output_path": str(user_output),
        "total_usage": total_usage,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Astro Orchestrator on a specific case folder.")
    parser.add_argument("--case", required=True, help="Path to the case folder (e.g. devanssh/input/0001)")
    parser.add_argument("--question", required=True, help="User question passed to the master writer.")
    parser.add_argument(
        "--user-output",
        "--output",
        dest="user_output",
        default="reports/user_report.md",
        help="Path to write the end-user Markdown report.",
    )
    parser.add_argument(
        "--detailed-output",
        default="reports/detailed_report.md",
        help="Path to write the detailed Markdown report.",
    )
    parser.add_argument(
        "--verbose-tokens",
        action="store_true",
        help="Log streaming updates and token slices for each agent response.",
    )
    return parser.parse_args()


async def _async_main() -> None:
    args = _parse_args()
    case_path = Path(args.case)
    detailed_output_path = Path(args.detailed_output)
    user_output_path = Path(args.user_output)

    result = await run_case(
        case_dir=case_path,
        question=args.question,
        detailed_output=detailed_output_path,
        user_output=user_output_path,
        verbose_tokens=args.verbose_tokens,
    )

    print("\n=== Final Forecast ===\n")
    print(result["final_summary"].strip())
    print("\nUser report:", result["user_output_path"])
    print("Detailed report:", result["detailed_output_path"])
    print(
        "Token usage -> prompt: %s, completion: %s, total: %s"
        % (
            result["total_usage"].prompt,
            result["total_usage"].completion,
            result["total_usage"].total,
        )
    )


if __name__ == "__main__":
    asyncio.run(_async_main())
