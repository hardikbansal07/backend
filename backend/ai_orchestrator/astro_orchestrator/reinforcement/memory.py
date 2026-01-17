from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def build_feature_set(lagna_json: Dict[str, Any]) -> List[str]:
    """Create a lightweight signature for a Lagna chart packet."""
    features: Set[str] = set()
    if not isinstance(lagna_json, dict):
        return []
    asc = lagna_json.get("ascendantSign") or lagna_json.get("ascendant_sign")
    if asc:
        features.add(f"ASC::{str(asc).strip().lower()}")
    for planet in lagna_json.get("planets", []):
        if not isinstance(planet, dict):
            continue
        name = str(planet.get("name") or "").strip().lower()
        if not name:
            continue
        house = planet.get("house")
        sign = planet.get("sign")
        dignity = planet.get("dignity")
        nakshatra = planet.get("nakshatra")
        if house is not None:
            features.add(f"HOUSE::{name}::{house}")
        if sign:
            features.add(f"SIGN::{name}::{str(sign).strip().lower()}")
        if dignity:
            features.add(f"DIGNITY::{name}::{str(dignity).strip().lower()}")
        if nakshatra:
            features.add(f"NAK::{name}::{str(nakshatra).strip().lower()}")
        if planet.get("isCombust"):
            features.add(f"COMBUST::{name}")
        if planet.get("retrograde"):
            features.add(f"RETRO::{name}")
    yogas = lagna_json.get("yogas") or lagna_json.get("yogaList")
    if isinstance(yogas, list):
        for yoga in yogas:
            if isinstance(yoga, dict):
                label = yoga.get("name") or yoga.get("code")
            else:
                label = yoga
            if label:
                features.add(f"YOGA::{str(label).strip().lower()}")
    return sorted(features)


class ReinforcementMemory:
    """Persistence layer for capturing chart-specific follow ups and outcomes."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._records: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._records = []
            return
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError):
            self._records = []
            return
        if isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
        else:
            records = payload.get("cases") if isinstance(payload, dict) else []
            if not isinstance(records, list):
                records = []
            records = [item for item in records if isinstance(item, dict)]
        self._records = records

    @property
    def records(self) -> Sequence[Dict[str, Any]]:
        return tuple(self._records)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"cases": self._records}
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def upsert_case(
        self,
        *,
        user_id: str,
        session_id: Optional[str],
        origin_case: str,
        features: Sequence[str],
        question: str,
        psy_summary: str,
        follow_ups: Sequence[Dict[str, str]],
        difference_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = (user_id, session_id)
        target: Optional[Dict[str, Any]] = None
        for record in self._records:
            if record.get("user_id") == key[0] and record.get("session_id") == key[1]:
                target = record
                break
        timestamp = _utc_now_iso()
        follow_up_entries: List[Dict[str, str]] = []
        for item in follow_ups:
            question_text = str(item.get("question", "")).strip()
            answer_text = str(item.get("answer", "")).strip()
            if not question_text and not answer_text:
                continue
            follow_up_entries.append(
                {
                    "question": question_text,
                    "answer": answer_text,
                    "captured_at": item.get("captured_at") or timestamp,
                }
            )
        if target is None:
            target = {
                "user_id": user_id,
                "session_id": session_id,
                "origin_case": origin_case,
                "chart_features": list(features),
                "question": question,
                "psy_summary": psy_summary,
                "follow_ups": follow_up_entries,
                "difference_notes": difference_notes or "",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            self._records.append(target)
        else:
            target.update(
                {
                    "origin_case": origin_case,
                    "chart_features": list(features),
                    "question": question,
                    "psy_summary": psy_summary,
                    "difference_notes": difference_notes or target.get("difference_notes", ""),
                    "follow_ups": follow_up_entries,
                    "updated_at": timestamp,
                }
            )
        return target

    def find_similar(
        self,
        features: Iterable[str],
        *,
        limit: int = 3,
        min_similarity: float = 0.25,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        feature_set = {item for item in features if item}
        if not feature_set:
            return []
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for record in self._records:
            record_features = {item for item in record.get("chart_features", []) if item}
            if not record_features:
                continue
            overlap = len(feature_set & record_features)
            union = len(feature_set | record_features)
            if union == 0:
                continue
            score = overlap / union
            if score >= min_similarity:
                scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        if limit:
            scored = scored[:limit]
        return scored


def format_similarity_context(matches: Sequence[Tuple[float, Dict[str, Any]]]) -> str:
    if not matches:
        return "[REINFORCEMENT] No prior similar cases captured yet."
    lines: List[str] = [
        "[REINFORCEMENT] Historical cases with similar Lagna signatures:",
    ]
    for idx, (score, record) in enumerate(matches, start=1):
        user_label = record.get("user_id") or "unknown"
        session_label = record.get("session_id") or "--"
        lines.append(
            f"{idx}. user={user_label} session={session_label} similarity={score:.2f}"
        )
        if record.get("psy_summary"):
            lines.append(f"   Psy profile: {record['psy_summary']}")
        for follow in record.get("follow_ups", [])[:3]:
            question = follow.get("question") or ""
            answer = follow.get("answer") or ""
            if question or answer:
                lines.append(f"   Follow-up: Q: {question} | A: {answer}")
        diff = record.get("difference_notes")
        if diff:
            lines.append(f"   Difference noted: {diff}")
    lines.append(
        "Use these patterns to validate the current native: check if the same behaviours appear or clarify divergences."
    )
    return "\n".join(lines)
