from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from .agents import birth_chart_packet_to_highlights


def _clean(value: object) -> str:
    """Return a readable ASCII-only string for downstream summaries."""
    if value is None:
        return ''
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    filtered = ''.join(ch for ch in text if 32 <= ord(ch) <= 126)
    return filtered.strip()


def _join_notes(items: Iterable[object]) -> str:
    cleaned = [item for item in (_clean(value) for value in items) if item]
    return ', '.join(cleaned)


def summarize_dseries_packet(packet: object) -> str:
    """Build a compact textual summary for divisional chart packets."""
    if packet is None:
        return ''
    if isinstance(packet, str):
        return _clean(packet)
    if isinstance(packet, list):
        return '\n'.join(note for note in (summarize_dseries_packet(item) for item in packet) if note)
    if not isinstance(packet, dict):
        return _clean(packet)

    lines: List[str] = []
    asc = _clean(packet.get('ascendantSign') or packet.get('ascendant_sign'))
    if asc:
        lines.append(f'Ascendant: {asc}')
    houses: List[str] = []
    for house in packet.get('houses', []):
        if not isinstance(house, dict):
            continue
        number = _clean(house.get('index') or house.get('number'))
        sign = _clean(house.get('sign') or house.get('signNumber'))
        occupants = _join_notes(house.get('items') or house.get('planets') or [])
        label_parts = []
        if number:
            label_parts.append(f'House {number}')
        if sign:
            label_parts.append(f'sign {sign}')
        label = ' '.join(label_parts).strip()
        if occupants:
            label = f"{label} -> {occupants}" if label else occupants
        if label:
            houses.append(label)
    if houses:
        lines.append('Key houses\n- ' + '\n- '.join(houses))

    planets: List[str] = []
    for planet in packet.get('planets', []):
        if not isinstance(planet, dict):
            continue
        name = _clean(planet.get('name'))
        if not name:
            continue
        traits: List[str] = []
        sign = _clean(planet.get('sign'))
        house = _clean(planet.get('house'))
        dignity = _clean(planet.get('dignity'))
        if sign:
            traits.append(f'sign {sign}')
        if house:
            traits.append(f'house {house}')
        if dignity:
            traits.append(f'dignity {dignity}')
        if planet.get('isCombust'):
            traits.append('combust')
        if planet.get('retrograde'):
            traits.append('retrograde')
        planets.append(f"{name}: {', '.join(traits)}" if traits else name)
    if planets:
        lines.append('Planet factors\n- ' + '\n- '.join(planets))

    summary = _clean(packet.get('summary'))
    if summary:
        lines.append(summary)
    return '\n'.join(line for line in lines if line)


def summarize_dasha_periods(timeline: Dict[str, Any], limit: int = 8) -> str:
    """Condense dasha timelines into a small set of checkpoints."""
    if not isinstance(timeline, dict):
        return _clean(timeline)
    periods = timeline.get('periods') or []
    if not periods:
        return ''
    lines: List[str] = []
    slice_end = max(limit, 0)
    for entry in periods[:slice_end or None]:
        if not isinstance(entry, dict):
            continue
        start = _clean(entry.get('start')) or '--'
        mahadasha = _clean(entry.get('dhasaLord') or entry.get('mahadasaLord')) or '--'
        antar = _clean(entry.get('bhuktiLord') or entry.get('antarLord')) or '--'
        note = _clean(entry.get('notes'))
        line = f"{start} | Mahadasha: {mahadasha} | Antar: {antar}"
        if note:
            line += f" | Note: {note}"
        lines.append(line)
    return '\n'.join(lines)


@dataclass
class MainOrchestratorTeam:
    """Deterministic helpers replacing the earlier multi-agent GraphFlow."""

    birth_converter: Any = birth_chart_packet_to_highlights

    def convert_birth_packet(self, packet: object) -> str:
        return self.birth_converter(packet)

    def summarize_dseries(self, packet: object) -> str:
        return summarize_dseries_packet(packet)

    def summarize_dasha(self, timeline: Dict[str, Any], limit: int = 8) -> str:
        return summarize_dasha_periods(timeline, limit=limit)


__all__ = [
    'MainOrchestratorTeam',
    'birth_chart_packet_to_highlights',
    'summarize_dasha_periods',
    'summarize_dseries_packet',
]
