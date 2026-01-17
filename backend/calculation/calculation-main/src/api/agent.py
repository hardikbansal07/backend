from __future__ import annotations
import os, asyncio, httpx
from .models import StoredHoroscope, AgentDispatchResult
from . import events, app as api_app
from . import service as _service
from . import models as _models
from jhora import utils

AGENT_URL = os.getenv('AGENT_WEBHOOK_URL')
AGENT_API_KEY = os.getenv('AGENT_API_KEY')
MAX_AGENT_ATTEMPTS = int(os.getenv('AGENT_MAX_ATTEMPTS', '5'))
BASE_BACKOFF = float(os.getenv('AGENT_BASE_BACKOFF', '1.0'))  # seconds

async def dispatch_to_agent(stored: StoredHoroscope) -> AgentDispatchResult:
    if not AGENT_URL:
        # Still record an event so UI shows something and user understands why relay is inert
        try:
            payload = _build_agent_payload(stored)
            events.record_event(stored.response.meta['requestId'], payload)
            events.update_event(stored.response.meta['requestId'], 'skipped_no_url', 'AGENT_WEBHOOK_URL not set', 0)
        except Exception:  # noqa
            pass
        return AgentDispatchResult(success=False, detail='AGENT_WEBHOOK_URL not set', attempts=0)
    payload = _build_agent_payload(stored)
    # record pending event if not already
    events.record_event(stored.response.meta['requestId'], payload)
    headers = {'Content-Type': 'application/json'}
    if AGENT_API_KEY:
        headers['Authorization'] = f'Bearer {AGENT_API_KEY}'
    attempts = 0
    last_err = None
    async with httpx.AsyncClient(timeout=10) as client:
        while attempts < MAX_AGENT_ATTEMPTS:
            # Exponential backoff with jitter (skip sleep first attempt)
            if attempts > 0:
                delay = BASE_BACKOFF * (2 ** (attempts-1))
                import random
                delay = min(delay, 30.0) + random.uniform(0, 0.25)
                await asyncio.sleep(delay)
            attempts += 1
            try:
                resp = await client.post(AGENT_URL, json=payload, headers=headers)
                if resp.status_code < 300:
                    detail = f'delivered in {attempts} attempt(s)'
                    events.update_event(stored.response.meta['requestId'], 'delivered', detail, attempts)
                    return AgentDispatchResult(success=True, detail=detail, attempts=attempts)
                last_err = f'status {resp.status_code}: {resp.text[:200]}'
                events.update_event(stored.response.meta['requestId'], 'error', last_err, attempts)
            except Exception as e:  # noqa
                last_err = str(e)
                events.update_event(stored.response.meta['requestId'], 'exception', last_err, attempts)
    # exhausted
    events.update_event(stored.response.meta['requestId'], 'failed', last_err or 'unknown error', attempts)
    return AgentDispatchResult(success=False, detail=last_err or 'unknown error', attempts=attempts)


def _build_agent_payload(stored: StoredHoroscope):
    r = stored.response
    mode = getattr(stored.request, 'sendToAgentMode', 'summary')
    # Always include base meta
    base = {
        'type': 'HOROSCOPE_COMPUTED',
        'requestId': r.meta['requestId'],
        'generatedAt': r.meta.get('generatedAt'),
        'ayanamsaMode': stored.request.ayanamsaMode,
        'calcType': stored.request.calcType,
        'language': stored.request.language,
        'mode': mode,
    }
    # Build summary snippet
    calendar_keys = [k for k in r.calendar.keys()][:12]
    summary_snip = {
        'calendarSnippet': {k: r.calendar.get(k) for k in calendar_keys},
        'ascendant': r.rasiChart.ascendantHouse,
        'ascendantSignNumber': getattr(r.rasiChart,'ascendantSignNumber', None),
        'planets': [ {'planet': p.name, 'house': p.house, 'houseAbs': getattr(p,'houseAbs',None), 'deg': p.rawLongitudeDeg } for p in r.rasiChart.planets ]
    }
    # Build bundle snippet
    bundle_snip = {
        'rasi': {
            'asc': r.rasiChart.ascendantHouse,
            'ascSignNumber': getattr(r.rasiChart,'ascendantSignNumber', None),
            'planets': [ {'name': p.name, 'house': p.house, 'houseAbs': getattr(p,'houseAbs',None), 'deg': p.rawLongitudeDeg, 'dignity': p.dignity} for p in r.rasiChart.planets ]
        },
        'divisionals': [ {'factor': d.factor, 'asc': d.ascendantHouse, 'planetCount': len(d.planets) } for d in (r.divisionalCharts or [])[:5] ]
    }
    # Full object
    try:
        full_obj = r.model_dump()
    except Exception:
        from pydantic import BaseModel
        if isinstance(r, BaseModel):
            full_obj = r.model_dump()
        else:
            full_obj = {}
    # Always include full plus chosen variant
    payload = base.copy()
    payload['full'] = full_obj
    if mode == 'summary':
        payload['summary'] = summary_snip
    elif mode == 'bundle':
        payload['bundle'] = bundle_snip
        payload['summary'] = summary_snip  # include summary as well for convenience
    else:  # full mode
        payload['summary'] = summary_snip
        payload['bundle'] = bundle_snip
    # Attach additional computed snapshots (lightweight basic versions) so agent has cross-endpoint data
    try:
        from .app import get_yogas, get_strength, deep_strength, _compute_summary_internal
        rid = r.meta['requestId']
        # Always include basic + full yogas
        payload['yogasBasic'] = get_yogas(rid, mode='basic')
        try:
            payload['yogasFull'] = get_yogas(rid, mode='full')
        except Exception as _e:  # noqa
            payload['yogasFullError'] = str(_e)
        payload['strength'] = get_strength(rid)
        # Deep strength always (without aspects/prastara for size unless full)
        ds = deep_strength(rid, includeAspects=False, includePrastara=False)
        payload['deepStrength'] = ds
        try:
            _summary_obj = _compute_summary_internal(rid)
            payload['summaryEndpoint'] = _summary_obj.model_dump() if hasattr(_summary_obj,'model_dump') else _summary_obj
        except Exception as _se:  # noqa
            payload['summaryEndpointError'] = str(_se)
    except Exception as e:  # noqa
        payload['extrasError'] = str(e)
    return payload

async def retry_event(request_id: str) -> AgentDispatchResult:
    from .service import get_stored
    stored = get_stored(request_id)
    if not stored:
        return AgentDispatchResult(success=False, detail='request not in memory (recompute first)', attempts=0)
    return await dispatch_to_agent(stored)
