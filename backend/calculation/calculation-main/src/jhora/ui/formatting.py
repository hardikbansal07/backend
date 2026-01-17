"""Lightweight formatting helpers extracted from horo_chart for testability without PyQt dependency."""
from __future__ import annotations
import re

_VIM_LEVEL_LABELS = ['MD','AD','PD','SD','PAD']
_PLANET_SHORT_MAP = {
    'sun':'Su','moon':'Mo','mars':'Ma','mercury':'Me','jupiter':'Ju','venus':'Ve','saturn':'Sa',
    'rahu':'Ra','raagu':'Ra','ketu':'Ke','lagnam':'L','ascendant':'As'
}

def _short_planet(token: str) -> str:
    if not token:
        return ''
    m = re.match(r'([A-Za-z]+)', token)
    if m:
        name = m.group(1).lower()
        return _PLANET_SHORT_MAP.get(name, name[:2].capitalize())
    return token[:2]

def format_vimsottari_chain(chain_str: str) -> str:
    if not chain_str or not isinstance(chain_str, str):
        return ''
    parts = chain_str.split('-')
    out = []
    for i, part in enumerate(parts):
        label = _VIM_LEVEL_LABELS[i] if i < len(_VIM_LEVEL_LABELS) else f'L{i+1}'
        short = _short_planet(part)
        out.append(f"{label}:{short}")
    return ' → '.join(out)