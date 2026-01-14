from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import re
import time
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Literal, Sequence
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_core.models import SystemMessage, UserMessage

if __package__ in (None, ""):
    package_root = Path(__file__).resolve().parent
    project_root = package_root.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    __package__ = "agent2.astro_orchestrator"

from .config.models import build_chat_completion_client

from .birth_chart.team import BirthChartTeam
from .d_series.team import DSeriesTeam
from .dasha.team import DashaTeam
from .main.agents import create_master_writer_agent, create_review_agent
from .reinforcement.memory import ReinforcementMemory, build_feature_set, format_similarity_context

LOGGER_NAME = "astro_orchestrator"
logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
DEFAULT_TEAM_RETRIES = 5
DEFAULT_TEAM_BACKOFF = 1.0
DEFAULT_TEAM_JITTER = 0.75

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
    elapsed: float = 0.0
    messages: int = 0
    agents_invoked: List[str] = field(default_factory=list)
    raw_messages: List[Any] = field(default_factory=list)


@dataclass
class ReviewDecision:
    status: Literal["proceed", "follow_up"]
    message: str
    raw: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    elapsed: float = 0.0


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

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


def _try_parse_datetime(value: str) -> Optional[datetime]:
    value = value.strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _find_birth_datetime(value: Any) -> Optional[datetime]:
    birth_keys = {
        "birth_datetime",
        "birth_datetime_utc",
        "birthdate",
        "birth_date",
        "dob",
        "date_of_birth",
    }
    if isinstance(value, dict):
        for key, val in value.items():
            if isinstance(key, str) and key.lower() in birth_keys and isinstance(val, str):
                dt = _try_parse_datetime(val)
                if dt:
                    return dt
            dt = _find_birth_datetime(val)
            if dt:
                return dt
    elif isinstance(value, list):
        for item in value:
            dt = _find_birth_datetime(item)
            if dt:
                return dt
    return None


def _compute_subject_context(meta: Dict[str, Any]) -> Dict[str, Any]:
    birth = _find_birth_datetime(meta)
    info: Dict[str, Any] = {"birth_datetime": birth.isoformat() if birth else None}
    if birth:
        if birth.tzinfo is not None:
            birth = birth.astimezone(timezone.utc).replace(tzinfo=None)
        now = datetime.utcnow()
        age_years = (now - birth).days / 365.25
        info["age_years"] = round(age_years, 2)
        info["birth_year"] = birth.year
    return info

def _format_review_context(meta: Dict[str, Any]) -> str:
    if not meta:
        return ""
    try:
        serialized = json.dumps(meta, indent=2, ensure_ascii=False)
    except TypeError:
        serialized = str(meta)
    return "[CASE_METADATA]\n" + serialized + "\n"


def _format_lagna_payload(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except TypeError:
        return str(value)


def _pick_lagna_summary_config(*sources: Optional[Dict[str, Any]]) -> Any:
    keys = ("lagna_summary", "lagnaSummary")
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            if key in source:
                return source[key]
        options = source.get("options")
        if isinstance(options, dict):
            for key in keys:
                if key in options:
                    return options[key]
    return None


def _resolve_lagna_summary(lagna: Any, summary_config: Any = None) -> str:
    explicit_summary: Optional[Any] = None
    enabled = True

    if isinstance(summary_config, bool):
        enabled = summary_config
    elif isinstance(summary_config, str):
        explicit_summary = summary_config
    elif isinstance(summary_config, dict):
        if "enabled" in summary_config:
            enabled = bool(summary_config.get("enabled"))
        if "disabled" in summary_config:
            enabled = not bool(summary_config.get("disabled"))
        for key in ("summary", "text", "content", "override"):
            if summary_config.get(key):
                explicit_summary = summary_config[key]
                break

    if explicit_summary is not None:
        return _format_lagna_payload(explicit_summary)

    if not enabled:
        if isinstance(lagna, dict):
            for key in ("summary", "text", "content", "rawSummary"):
                if lagna.get(key):
                    return _format_lagna_payload(lagna[key])
        return _format_lagna_payload(lagna)

    if isinstance(lagna, dict):
        for key in ("summary", "aiSummary", "summaryText", "textSummary"):
            candidate = lagna.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate

    return _summarize_lagna(lagna)


def _summarize_lagna(lagna: Any) -> str:
    if isinstance(lagna, str):
        return lagna
    if not isinstance(lagna, dict):
        return _format_lagna_payload(lagna)

    asc_sign = lagna.get("ascendantSign") or lagna.get("ascendant_sign")
    if not asc_sign:
        ascendant = lagna.get("ascendant")
        if isinstance(ascendant, dict):
            asc_sign = ascendant.get("sign") or ascendant.get("name")

    houses: List[str] = []
    raw_houses = lagna.get("houses") or []
    if isinstance(raw_houses, dict):
        house_iterable = raw_houses.values()
    else:
        house_iterable = raw_houses
    for house in house_iterable:
        if not isinstance(house, dict):
            continue
        items = house.get("items") or []
        if isinstance(items, dict):
            items = list(items.values())
        if items:
            index = house.get("index") or house.get("number") or house.get("house")
            sign_number = house.get("signNumber") or house.get("sign_number")
            label = f"House {index}" if index is not None else "House"
            summary = f"{label}: {', '.join(str(item) for item in items if item)}"
            if sign_number:
                summary += f" (sign #{sign_number})"
            houses.append(summary)

    raw_planets = lagna.get("planets") or []
    if isinstance(raw_planets, dict):
        planet_iterable = []
        for name, details in raw_planets.items():
            if isinstance(details, dict):
                entry = dict(details)
            else:
                entry = {"value": details}
            entry.setdefault("name", name)
            planet_iterable.append(entry)
    else:
        planet_iterable = [planet for planet in raw_planets if isinstance(planet, dict)]

    planets: List[str] = []
    for planet in planet_iterable:
        name = planet.get("name") or planet.get("planet")
        if not name:
            continue
        parts: List[str] = []
        degree = planet.get("longitudeDMS") or planet.get("longitude_dms")
        if degree:
            parts.append(f"deg={degree}")
        house = planet.get("house")
        if house:
            parts.append(f"house={house}")
        sign = planet.get("sign")
        if sign:
            parts.append(f"sign={sign}")
        dignity = planet.get("dignity")
        if dignity:
            parts.append(f"dignity={dignity}")
        nak = planet.get("nakshatra")
        if nak:
            parts.append(f"nakshatra={nak}")
        pada = planet.get("nakshatraPada")
        if pada:
            parts.append(f"p{pada}")
        karaka = planet.get("charaKaraka") or planet.get("karaka")
        if karaka:
            parts.append(f"karaka={karaka}")
        notes = planet.get("notes")
        if notes and notes != karaka:
            parts.append(notes)
        if planet.get("isCombust"):
            parts.append("CMB")
        if planet.get("retrograde"):
            parts.append("R")
        planets.append(f"{name} {' '.join(parts)}".rstrip())

    lines = [f"Ascendant: {asc_sign}" if asc_sign else "Ascendant: -"]
    if houses:
        lines.append("Key house occupancies:\n- " + "\n- ".join(houses))
    if planets:
        lines.append("Planets:\n- " + "\n- ".join(planets))
    return "\n".join(lines)


def _summarize_d10(d10: Dict[str, Any]) -> str:
    asc_sign = d10.get("ascendantSign") or d10.get("ascendant_sign")
    highlights: List[str] = [f"D10 Ascendant: {asc_sign}"]
    for planet in d10.get("planets", []):
        highlight = (
            f"{planet.get('name')} deg={planet.get('longitudeDMS')} house={planet.get('house')} sign={planet.get('sign')} "
            f"dignity={planet.get('dignity')} nakshatra={planet.get('nakshatra')} p{planet.get('nakshatraPada')} karaka={planet.get('charaKaraka') or '-'}"
        )
        highlights.append(highlight)
    return "\n".join(highlights)


def _extract_focus_from_question(question: str) -> Dict[str, Any]:
    focus: Dict[str, Any] = {}
    years = sorted({int(y) for y in re.findall(r"(19|20)\d{2}", question)})
    if years:
        focus["years"] = years
    range_match = re.search(r"(20\d{2}|19\d{2})\s*[-to]+\s*(20\d{2}|19\d{2})", question)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        focus["year_range"] = [min(start, end), max(start, end)]
    age_matches = re.findall(r"(?:age|aged|at)\s*(\d{1,3})", question, flags=re.IGNORECASE)
    if age_matches:
        focus["ages"] = sorted({int(a) for a in age_matches})
    next_years = re.search(r"next\s*(\d+)\s*years", question, flags=re.IGNORECASE)
    if next_years:
        focus["next_years"] = int(next_years.group(1))
    return focus


def _ages_to_years(ages: List[int], birth_year: Optional[int]) -> List[int]:
    if birth_year is None:
        return []
    return sorted({birth_year + age for age in ages})


def _select_dasha_periods(
    dasha_json: Dict[str, Any],
    focus: Dict[str, Any],
    current_dt: datetime,
) -> List[Dict[str, Any]]:
    periods = []
    for entry in dasha_json.get("periods", []):
        start_str = entry.get("start")
        start_dt = _try_parse_datetime(start_str or "")
        if not start_dt:
            continue
        if start_dt.tzinfo is not None:
            start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
        periods.append({
            "start": start_dt,
            "dasha_lord": entry.get("dhasaLord") or entry.get("mahadasaLord"),
            "bhukti_lord": entry.get("bhuktiLord"),
            "notes": entry.get("notes"),
        })
    if not periods:
        return []

    selected: List[Dict[str, Any]] = []
    year_targets: set[int] = set(focus.get("years", []))
    if focus.get("year_range"):
        start, end = focus["year_range"]
        year_targets.update(range(start, end + 1))
    if focus.get("ages_to_years"):
        year_targets.update(focus["ages_to_years"])
    if focus.get("next_years"):
        span = focus["next_years"]
        year_targets.update(current_dt.year + offset for offset in range(span + 1))

    for entry in periods:
        year = entry["start"].year
        if year_targets and year not in year_targets:
            continue
        selected.append(entry)

    if not selected:
        # fallback: pick current and next few periods
        upcoming = [p for p in periods if p["start"] >= current_dt]
        if not upcoming:
            upcoming = periods
        selected = upcoming[:10]
    return selected


def _format_period_list(periods: List[Dict[str, Any]]) -> str:
    lines = []
    for entry in periods:
        start = entry['start'].strftime('%Y-%m-%d %H:%M')
        bhukti = entry.get('bhukti_lord') or '--'
        lines.append(
            f"- Start: {start} | Mahadasha: {entry.get('dasha_lord')} | Antar: {bhukti}"
        )
    return '\n'.join(lines)



def _extract_follow_up_pairs(messages: Iterable[Any]) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []
    pending_question: Optional[str] = None
    for message in messages:
        source = getattr(message, 'source', '') or ''
        content = _format_message(message).strip()
        if not content:
            continue
        if isinstance(source, str) and source.upper() == 'DEEP_DIVER' and '[ASK_HUMAN]' in content:
            pending_question = content.split('[ASK_HUMAN]', 1)[1].strip()
            continue
        if isinstance(source, str) and source.upper() == 'DEEP_DIVER_RESPONDER':
            answer = content
            if answer.startswith('[HUMAN_REPLY]'):
                answer = answer[len('[HUMAN_REPLY]'):].strip()
            if pending_question or answer:
                pairs.append({
                    'question': pending_question or '',
                    'answer': answer,
                    'captured_at': datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
                })
            pending_question = None
    return pairs



def _capture_psy_summary(messages: Iterable[Any]) -> str:
    for message in reversed(list(messages)):
        source = getattr(message, 'source', '') or ''
        if isinstance(source, str) and source.upper() == 'PSY_SIGNATURE':
            return _format_message(message).strip()
    return ''



def _describe_feature_delta(current: Sequence[str], reference: Optional[Dict[str, Any]]) -> str:
    if not reference:
        return ''
    current_set = {item for item in current if item}
    ref_set = {item for item in reference.get('chart_features', []) if item}
    if not current_set and not ref_set:
        return ''
    new_only = sorted(current_set - ref_set)
    missing = sorted(ref_set - current_set)
    notes: List[str] = []
    if new_only:
        notes.append('New traits: ' + ', '.join(new_only[:6]))
    if missing:
        notes.append('Absent vs prior case: ' + ', '.join(missing[:6]))
    return ' | '.join(notes)



def _build_lagna_task(summary: str, reinforcement_context: str = '') -> str:
    instructions = [
        'You are the Lagna analysis team. Study the summarised chart data and produce focused insights.',
        'Highlight ascendant context, key house occupancies, and planetary strengths. Avoid repeating data verbatim.',
    ]
    body = ['\nSummary:\n' + summary]
    if reinforcement_context:
        body.append('\nReinforcement intelligence:\n' + reinforcement_context)
    return '\n'.join(instructions + body)



def _build_dseries_task(summary: str) -> str:
    return (
        "You are the D10 divisional specialist. Analyse the summarised professional indicators below.\n"
        "Extract leadership signals, opportunities, and risks. Keep the response concise.\n"
        "\nSummary:\n" + summary
    )


def _build_dasha_task(
    question: str,
    current_dt_iso: str,
    age_years: Optional[float],
    focus: Dict[str, Any],
    selected_periods: List[Dict[str, Any]],
) -> str:
    lines = [
        "You are the Dasha analyst."
        " Use the provided timeline summary to address the user's question,"
        " giving priority to the most relevant sub-periods."
        " Highlight impacts on career and relationships and always mention date ranges.",
        "\nUser question: " + question,
        f"Current UTC time: {current_dt_iso}",
    ]
    if age_years is not None:
        lines.append(f"Subject age (years): {age_years}")
    if focus:
        lines.append("Detected focus hints: " + json.dumps(focus, ensure_ascii=False))
    lines.append("Selected periods:\n" + _format_period_list(selected_periods))
    return "\n".join(lines)


def _extract_agent_messages(task_result: TaskResult, usage: TokenUsage) -> str:
    outputs: list[str] = []
    for message in task_result.messages:
        source = getattr(message, "source", "")
        if isinstance(source, str) and source.lower() == "user":
            continue
        outputs.append(_format_message(message))
        usage.update(getattr(message, "models_usage", None))
    return "\n".join(outputs)


async def _run_review_gate(question: str, context: str = "") -> ReviewDecision:
    reviewer = create_review_agent()
    usage = TokenUsage()
    start = time.perf_counter()
    payload = question if not context else f"{question}\n\n{context}"
    result = await reviewer.run(task=payload)
    await reviewer.close()
    if not result.messages:
        raise RuntimeError("Review gate returned no messages.")
    content = ""
    for message in result.messages:
        if getattr(message, "source", "").lower() == "user":
            continue
        usage.update(getattr(message, "models_usage", None))
        content = _format_message(message)
    text = content.strip()
    if not text:
        raise RuntimeError("Review gate returned an empty message.")
    directive, _, payload = text.partition(":")
    directive = directive.strip().upper()
    payload = payload.strip()
    if directive == "PROCEED":
        status: Literal["proceed", "follow_up"] = "proceed"
        if not payload:
            payload = question.strip()
    elif directive == "FOLLOW_UP":
        status = "follow_up"
        if not payload:
            payload = "Could you share more details about what you'd like analysed?"
    else:
        raise RuntimeError(f"Unexpected review directive: {text}")
    elapsed = time.perf_counter() - start
    return ReviewDecision(status=status, message=payload, raw=text, usage=usage, elapsed=elapsed)


# ---------------------------------------------------------------------------
# Direct concierge (bypass agent framework for greetings/small-talk)
# ---------------------------------------------------------------------------

_CONCIERGE_SYSTEM = (
    "You are the front-door concierge for an astrology analysis service. Introduce yourself as â€˜Iâ€™m AI developed by Astro Care.â€™ "
    "Your job is ONLY to welcome the user and ask one short, friendly follow-up so they provide a proper question (life area "
    "like career/relationships/finances, intent, and timeframe or dates). Mention that a specific question helps generate a deep, "
    "tailored answer. Keep it to 1â€“2 sentences in warm, respectful Indian English. Do not perform any analysis."
)


def _is_greeting(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return True
    # very short greetings and variants
    greeting_tokens = {"hi", "hello", "hey", "yo", "hola", "namaste", "whatsup", "what's up", "sup"}
    if t in greeting_tokens or re.fullmatch(r"(hi+|hello+|hey+)[!. ]*", t):
        return True
    # very short small-talk without intent
    if len(t.split()) <= 3 and any(word in t for word in ("hi", "hello", "hey")):
        return True
    return False


async def _direct_concierge_follow_up(question: str) -> str:
    client = build_chat_completion_client()
    response = await client.create(
        messages=[
            SystemMessage(content=_CONCIERGE_SYSTEM),
            UserMessage(content=question, source="user"),
        ]
    )
    # Many model clients return an object with .content; fall back to str
    content = getattr(response, "content", None)
    return content if isinstance(content, str) else str(response)


# ---------------------------------------------------------------------------
# Team execution and logging
# ---------------------------------------------------------------------------


async def _run_team(team, *, label: str, task: str, verbose_tokens: bool) -> TeamRunResult:
    if verbose_tokens:
        logger.setLevel(logging.INFO)
    last_error: Exception | None = None
    for attempt in range(1, DEFAULT_TEAM_RETRIES + 1):
        usage = TokenUsage()
        agents_seen: list[str] = []
        message_count = 0
        start = time.perf_counter()
        final_result: TaskResult | None = None
        try:
            async for item in team.run_stream(task=task):
                if isinstance(item, TaskResult):
                    final_result = item
                    logger.info("%s team completed (%d messages)", label, len(item.messages))
                    continue
                summary = _format_message(item)
                source = getattr(item, "source", label) or label
                if isinstance(source, str) and source.lower() != "user" and source not in agents_seen:
                    agents_seen.append(source)
                preview = summary if verbose_tokens else " ".join(summary.split()[:20])
                logger.info("%s -> %s | %s", label, source, preview)
                usage.update(getattr(item, "models_usage", None))
                if verbose_tokens and isinstance(item, BaseChatMessage):
                    tokens = summary.split()
                    logger.info("%s token stream: %s", source, tokens[: min(len(tokens), 10)])
                message_count += 1
            if final_result is None:
                raise RuntimeError(f"{label} team did not return a TaskResult")
            elapsed = time.perf_counter() - start
            summary_text = _extract_agent_messages(final_result, usage)
            await team.reset()
            logger.info(
                "%s summary -> prompt: %s, completion: %s, total: %s, duration: %.2fs",
                label,
                usage.prompt,
                usage.completion,
                usage.total,
                elapsed,
            )
            return TeamRunResult(
                label=label,
                summary=summary_text,
                usage=usage,
                elapsed=elapsed,
                messages=message_count,
                agents_invoked=agents_seen,
                raw_messages=list(getattr(final_result, 'messages', [])),
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("%s team attempt %d/%d failed – retrying", label, attempt, DEFAULT_TEAM_RETRIES, exc)
            try:
                await team.reset()
            except Exception as reset_exc:  # noqa: BLE001
                logger.debug("Failed to reset %s team after error: %s", label, reset_exc)
            if attempt >= DEFAULT_TEAM_RETRIES:
                break
            backoff = DEFAULT_TEAM_BACKOFF * (2 ** (attempt - 1))
            jitter = random.uniform(0.0, DEFAULT_TEAM_JITTER)
            await asyncio.sleep(backoff + jitter)
    if last_error is None:
        raise RuntimeError(f"{label} team failed without raising an explicit exception")
    raise last_error



def _write_metrics_log(metrics: Dict[str, Any]) -> None:
    log_path = Path("logs/run_metrics.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(metrics, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def run_case(
    case_dir: Path,
    question: str,
    detailed_output: Path,
    user_output: Path,
    verbose_tokens: bool,
    precheck: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not case_dir.exists():
        raise FileNotFoundError(f"Case folder not found: {case_dir}")

    lagna_json = _load_json(case_dir / 'lagna.json')
    dasha_json = _load_json(case_dir / 'dasha.json')
    d10_json = _load_json(case_dir / 'dseries' / 'd10.json')
    meta_path = case_dir / 'meta.json'
    meta_json = _load_json(meta_path) if meta_path.exists() else {}
    context_path = case_dir / 'context.json'
    context_json = _load_json(context_path) if context_path.exists() else {}
    try:
        default_user = case_dir.parents[1].name
    except IndexError:
        default_user = case_dir.parent.name if case_dir.parent != case_dir else case_dir.name
    user_id = str(context_json.get('user_id') or context_json.get('tenant_id') or default_user)
    session_id = str(context_json.get('session_id') or case_dir.name)

    memory_path = Path('logs/reinforcement_memory.json')
    reinforcement_memory = ReinforcementMemory(memory_path)
    current_features = build_feature_set(lagna_json)
    similar_matches = reinforcement_memory.find_similar(current_features)
    reinforcement_context = format_similarity_context(similar_matches) if similar_matches else ''

    subject_context = _compute_subject_context(meta_json)
    current_datetime = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    lagna_summary_config = _pick_lagna_summary_config(context_json, meta_json, meta_json.get("primary"))
    lagna_summary = _resolve_lagna_summary(lagna_json, lagna_summary_config)
    lagna_task = _build_lagna_task(lagna_summary, reinforcement_context)
    dseries_task = _build_dseries_task(_summarize_d10(d10_json))

    focus_hints = _extract_focus_from_question(question)
    if subject_context.get("age_years") is not None and "ages" in focus_hints:
        focus_hints["ages_to_years"] = _ages_to_years(
            focus_hints.get("ages", []), subject_context.get("birth_year")
        )
    selected_periods = _select_dasha_periods(
        dasha_json,
        focus_hints,
        datetime.utcnow(),
    )
    dasha_task = _build_dasha_task(
        question,
        current_datetime,
        subject_context.get("age_years"),
        focus_hints,
        selected_periods,
    )

    lagna_result = await _run_team(BirthChartTeam(), label='Lagna', task=lagna_task, verbose_tokens=verbose_tokens)
    follow_up_pairs = _extract_follow_up_pairs(lagna_result.raw_messages)
    psy_summary_text = _capture_psy_summary(lagna_result.raw_messages)
    top_reference = similar_matches[0][1] if similar_matches else None
    difference_notes = _describe_feature_delta(current_features, top_reference)
    reinforcement_memory.upsert_case(
        user_id=user_id,
        session_id=session_id,
        origin_case=str(case_dir),
        features=current_features,
        question=question,
        psy_summary=psy_summary_text,
        follow_ups=follow_up_pairs,
        difference_notes=difference_notes,
    )
    reinforcement_memory.save()
    dseries_result = await _run_team(DSeriesTeam(), label='D-Series', task=dseries_task, verbose_tokens=verbose_tokens)
    dasha_result = await _run_team(DashaTeam(), label="Dasha", task=dasha_task, verbose_tokens=verbose_tokens)

    master_writer = create_master_writer_agent()
    final_prompt = (
        f"User question: {question}\n\n"
        "Birth Chart Insights:\n" + lagna_result.summary + "\n\n"
        "Divisional (D10) Insights:\n" + dseries_result.summary + "\n\n"
        "Dasha Timeline Insights:\n" + dasha_result.summary + "\n\n"
        "Deliver a single consolidated forecast."
    )

    writer_usage = TokenUsage()
    writer_start = time.perf_counter()
    final_result = await master_writer.run(task=final_prompt)
    writer_elapsed = time.perf_counter() - writer_start
    final_summary = _extract_agent_messages(final_result, writer_usage)

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
        prompt=lagna_result.usage.prompt
        + dseries_result.usage.prompt
        + dasha_result.usage.prompt
        + writer_usage.prompt,
        completion=lagna_result.usage.completion
        + dseries_result.usage.completion
        + dasha_result.usage.completion
        + writer_usage.completion,
    )

    summary_table = [
        ("Lagna", lagna_result.usage.total, lagna_result.elapsed),
        ("D-Series", dseries_result.usage.total, dseries_result.elapsed),
        ("Dasha", dasha_result.usage.total, dasha_result.elapsed),
        ("Master Writer", writer_usage.total, writer_elapsed),
    ]
    top_consumer = max(summary_table, key=lambda row: row[1])
    logger.info(
        "Token summary -> %s used the most tokens (%s)", top_consumer[0], top_consumer[1]
    )

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "case": str(case_dir),
        "question": question,
        "subject_context": subject_context,
        "focus_hints": focus_hints,
        "teams": [
            {
                "name": "Lagna",
                "tokens": lagna_result.usage.__dict__,
                "elapsed": round(lagna_result.elapsed, 2),
                "messages": lagna_result.messages,
                "agents": lagna_result.agents_invoked,
            },
            {
                "name": "D-Series",
                "tokens": dseries_result.usage.__dict__,
                "elapsed": round(dseries_result.elapsed, 2),
                "messages": dseries_result.messages,
                "agents": dseries_result.agents_invoked,
            },
            {
                "name": "Dasha",
                "tokens": dasha_result.usage.__dict__,
                "elapsed": round(dasha_result.elapsed, 2),
                "messages": dasha_result.messages,
                "agents": dasha_result.agents_invoked,
            },
            {
                "name": "Master Writer",
                "tokens": writer_usage.__dict__,
                "elapsed": round(writer_elapsed, 2),
                "messages": len(final_result.messages),
                "agents": ["MASTER_WRITER"],
            },
        ],
        "totals": {
            "prompt": total_usage.prompt,
            "completion": total_usage.completion,
            "total": total_usage.total,
        },
        "outputs": {
            "user": str(user_output),
            "detailed": str(detailed_output),
        },
    }
    _write_metrics_log(metrics)

    return {
        "lagna": lagna_result,
        "dseries": dseries_result,
        "dasha": dasha_result,
        "final_summary": final_summary,
        "detailed_output_path": str(detailed_output),
        "user_output_path": str(user_output),
        "total_usage": total_usage,
        "writer_usage": writer_usage,
        "writer_elapsed": writer_elapsed,
        "summary_table": summary_table,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

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
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="If set, will ask the user follow-up questions (via console input) until the reviewer approves to proceed.",
    )
    return parser.parse_args()


async def _async_main() -> None:
    args = _parse_args()
    case_path = Path(args.case)
    detailed_output_path = Path(args.detailed_output)
    user_output_path = Path(args.user_output)

    review_context = ""
    meta_path = case_path / "meta.json"
    if meta_path.exists():
        try:
            review_context = _format_review_context(_load_json(meta_path))
        except Exception as exc:
            logger.warning("Failed to load case meta for review gate: %s", exc)

    # Interactive pre-intake loop (concierge + reviewer) if requested
    initial_question = args.question
    if args.interactive:
        current = initial_question
        while True:
            if _is_greeting(current):
                concierge = await _direct_concierge_follow_up(current)
                print("\nNamaste! Iâ€™m AI developed by Astro Care.\n")
                print(concierge.strip())
                current = input("\nPlease share your specific question (area + intent + timeframe): ").strip()
                continue
            review_decision = await _run_review_gate(current, review_context)
            logger.info("Review decision: %s", review_decision.raw)
            if review_decision.status == "follow_up":
                print("\nThanks! To generate a deep, tailored answer, I need one more detail:\n")
                print(review_decision.message)
                current = input("\nPlease add the missing detail: ").strip()
                continue
            # proceed
            refined_question = review_decision.message or current
            break
    else:
        # One-shot concierge/reviewer behavior
        if _is_greeting(initial_question):
            concierge = await _direct_concierge_follow_up(initial_question)
            print("\nNamaste! Iâ€™m AI developed by Astro Care.\n")
            print(concierge.strip())
            print("\nReply with your specific question (area + intent + timeframe) to start deep analysis.")
            return
        review_decision = await _run_review_gate(initial_question, review_context)
        logger.info("Review decision: %s", review_decision.raw)
        if review_decision.status == "follow_up":
            print("\nIâ€™m Astro Careâ€™s AI assistant. To generate a deep, tailored answer, I need a bit more detail.\n")
            print(review_decision.message)
            print("\nPlease resend your question with the requested details (area + intent + timeframe).")
            return
        refined_question = review_decision.message or initial_question
    precheck_payload = {
        "status": review_decision.status,
        "raw": review_decision.raw,
        "message": refined_question,
        "usage": review_decision.usage.__dict__,
        "elapsed": round(review_decision.elapsed, 2),
        "original_question": args.question,
    }

    result = await run_case(
        case_dir=case_path,
        question=refined_question,
        detailed_output=detailed_output_path,
        user_output=user_output_path,
        verbose_tokens=args.verbose_tokens,
        precheck=precheck_payload,
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
    print("\nPer-team summary:")
    for name, tokens, duration in result["summary_table"]:
        print(f"  {name:<12} tokens={tokens:<8} duration={duration:.2f}s")


if __name__ == "__main__":
    asyncio.run(_async_main())






