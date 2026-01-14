from __future__ import annotations
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys, logging, os
from typing import Any, Dict
from collections import OrderedDict
from . import models, service, agent, events
from datetime import datetime, UTC, timedelta
import importlib
import inspect

# Helper to recursively convert numpy types (np.int64, np.float64, arrays) to native Python types
def _to_native(obj):  # noqa
    try:
        import numpy as _np  # type: ignore
    except Exception:  # numpy may not be present; just return obj
        _np = None  # type: ignore
    # Fast paths
    if obj is None or isinstance(obj, (str, bool, int, float)):  # already native
        return obj
    # numpy scalar
    if _np is not None and isinstance(obj, getattr(_np, 'generic')):  # type: ignore
        try:
            return obj.item()
        except Exception:
            return float(obj) if hasattr(obj, '__float__') else int(obj) if hasattr(obj, '__int__') else str(obj)
    # list / tuple
    if isinstance(obj, (list, tuple)):
        return [ _to_native(x) for x in obj ]
    # numpy array
    if _np is not None and isinstance(obj, getattr(_np, 'ndarray')):  # type: ignore
        try:
            return [ _to_native(x) for x in obj.tolist() ]
        except Exception:
            return [ _to_native(x) for x in list(obj) ]
    # dict
    if isinstance(obj, dict):
        return { str(k): _to_native(v) for k,v in obj.items() }
    return obj
import csv, os

# Ensure our repo's src is at the front of sys.path and Swiss Ephemeris path is correct
try:
    _SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _SRC_DIR not in sys.path:
        sys.path.insert(0, _SRC_DIR)
except Exception:
    pass

# Force Swiss Ephemeris to use the repo-bundled ephemeris data even if a different jhora is imported
try:
    import swisseph as _swe  # type: ignore
    _EPHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jhora', 'data', 'ephe'))
    if os.path.isdir(_EPHE_DIR):
        _swe.set_ephe_path(_EPHE_DIR)
        os.environ['SE_EPHE_PATH'] = _EPHE_DIR
    else:
        logging.warning(f"Ephemeris directory not found at {_EPHE_DIR}")
except Exception as _e:
    logging.warning(f"Failed to set Swiss Ephemeris path: {_e}")

from jhora import const as _jconst
from jhora import utils as _jut
from jhora.horoscope.dhasa.annual import mudda as _mudda
from jhora.horoscope.dhasa.annual import patyayini as _patyayini
from jhora.horoscope.dhasa import sudharsana_chakra as _sudharsana
from jhora.horoscope.dhasa.graha import vimsottari as _vimsottari
from jhora.horoscope.chart import ashtakavarga as _ashtakavarga
from jhora.horoscope.chart import dosha as _dosha
from jhora.horoscope.chart import yoga as _yoga
from jhora.horoscope.chart import raja_yoga as _raja_yoga
from jhora.horoscope.chart import charts as _charts
from jhora.horoscope.chart import arudhas as _arudhas
from jhora.horoscope.chart import house as _house
from jhora.horoscope.chart import sphuta as _sphuta
from jhora.horoscope.chart import strength as _strength
from jhora.horoscope.match import compatibility as _compatibility
from jhora.horoscope.transit import tajaka as _tajaka
from jhora.horoscope.transit import tajaka_yoga as _tajaka_yoga
from jhora.horoscope.transit import saham as _saham
from jhora.horoscope.prediction import general as _general
from jhora.horoscope.prediction import longevity as _longevity
from jhora.horoscope.prediction import naadi_marriage as _naadi_marriage
from jhora.panchanga import pancha_paksha as _pancha_paksha
from jhora.panchanga import vratha as _vratha

# Ensure outer planets are enabled by default at server startup
try:
    if not getattr(_jconst, '_INCLUDE_URANUS_TO_PLUTO', False):
        _jconst._INCLUDE_URANUS_TO_PLUTO = True
        logging.info('Outer planets enabled by default at startup (Uranus/Neptune/Pluto).')
    # Sync the active planet list so Uranus/Neptune/Pluto are included in computations
    try:
        from jhora.panchanga import drik as _drik
        _drik.set_sideral_planets()
    except Exception as _ie:
        logging.debug(f"set_sideral_planets failed at startup: {_ie}")
except Exception as _e:
    logging.warning(f"Failed to set outer planets default: {_e}")

app = FastAPI(title='PyJHora API', version='0.1')
_RESP_CACHE: OrderedDict[str, dict] = OrderedDict()
_RESP_CACHE_MAX = 256
_RESP_CACHE_TTL = timedelta(hours=1)
_RESP_CACHE_LOCK = asyncio.Lock()
_PLACES: list[dict[str, Any]] | None = None

def _cache_prune_locked(now: datetime | None = None) -> None:
    if not _RESP_CACHE:
        return
    now = now or datetime.now(UTC)
    expired: list[str] = []
    for key, entry in list(_RESP_CACHE.items()):
        ts = entry.get('ts')
        if not ts:
            continue
        try:
            ts_dt = datetime.fromisoformat(ts)
        except Exception:
            expired.append(key)
            continue
        if now - ts_dt > _RESP_CACHE_TTL:
            expired.append(key)
    for key in expired:
        _RESP_CACHE.pop(key, None)

async def _cache_set(key: str, value: dict[str, Any]) -> None:
    data = dict(value)
    data.setdefault('ts', datetime.now(UTC).isoformat())
    async with _RESP_CACHE_LOCK:
        _cache_prune_locked()
        _RESP_CACHE[key] = data
        _RESP_CACHE.move_to_end(key)
        while len(_RESP_CACHE) > _RESP_CACHE_MAX:
            _RESP_CACHE.popitem(last=False)

async def _cache_get(key: str) -> dict[str, Any] | None:
    async with _RESP_CACHE_LOCK:
        entry = _RESP_CACHE.get(key)
        if not entry:
            return None
        _cache_prune_locked()
        entry = _RESP_CACHE.get(key)
        if not entry:
            return None
        _RESP_CACHE.move_to_end(key)
        return entry


def _cache_set_sync(key: str, value: dict[str, Any]) -> None:
    """Synchronous convenience wrapper for cache writes in threadpool contexts."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        fut = asyncio.run_coroutine_threadsafe(_cache_set(key, value), loop)
        fut.result()
    else:
        asyncio.run(_cache_set(key, value))

def _cache_key(path: str):
    return path
def _build_etag(payload: dict) -> str:
    import hashlib, json
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return 'W/"'+h+'"'

# Global cache for places data
_PLACES: list[dict[str, Any]] | None = None
_PLACES_INDEX: dict[str, list[dict[str, Any]]] = {}

def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except Exception:
        return default

def _load_places() -> list[dict[str, Any]]:
    global _PLACES, _PLACES_INDEX
    if _PLACES is not None:
        return _PLACES
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jhora', 'data', 'world_cities_with_tz.csv'))
    items: list[dict[str, Any]] = []
    if not os.path.exists(csv_path):
        logging.warning(f"Place database missing at {csv_path}")
        _PLACES = []
        return _PLACES
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # Expected columns without header: country, city, lat, lon, tzName, tzOffset
                if not row or len(row) < 4:
                    continue
                try:
                    lat = _safe_float(row[2])
                    lon = _safe_float(row[3])
                except Exception:
                    continue
                tz = _safe_float(row[5]) if len(row) > 5 else _safe_float(row[4]) if len(row) > 4 else None
                country = (row[0] or '').strip()
                name = (row[1] or '').strip()
                label = name
                if country and country.lower() not in name.lower():
                    label = f"{name}, {country}"
                if not label:
                    continue
                items.append({
                    'label': label,
                    'country': country,
                    'latitude': lat,
                    'longitude': lon,
                    'tzOffsetHours': tz,
                })
    except Exception as e:
        logging.error(f"Failed to load place database: {e}")
        items = []
    
    _PLACES = items
    
    # Build prefix index for fast lookups (3-character prefix)
    _PLACES_INDEX = {}
    for place in items:
        label_lower = place['label'].lower()
        # Index by first 3 characters for fast prefix matching
        if len(label_lower) >= 3:
            prefix = label_lower[:3]
            if prefix not in _PLACES_INDEX:
                _PLACES_INDEX[prefix] = []
            _PLACES_INDEX[prefix].append(place)
    
    return _PLACES

_PLANET_NAMES = list(getattr(_jut, 'PLANET_NAMES', ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']))
if len(_PLANET_NAMES) < 9:
    _PLANET_NAMES.extend(['Rahu','Ketu'])
_SIGN_NAMES = list(getattr(_jut, 'RAASI_LIST', [
    'Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'
]))
_NAKSHATRA_NAMES = [
    # Standard 27 nakshatras in English notation
    'Ashwini',
    'Bharani',
    'Krittika',
    'Rohini',
    'Mrigashira',
    'Ardra',
    'Punarvasu',
    'Pushya',
    'Ashlesha',
    'Magha',
    'Purva Phalguni',
    'Uttara Phalguni',
    'Hasta',
    'Chitra',
    'Swati',
    'Vishakha',
    'Anuradha',
    'Jyeshtha',
    'Mula',
    'Purva Ashadha',
    'Uttara Ashadha',
    'Shravana',
    'Dhanishta',
    'Shatabhisha',
    'Purva Bhadrapada',
    'Uttara Bhadrapada',
    'Revati',
]
_MODULE_CACHE: dict[str, Any] = {}
_GRAHA_DASHA_MAP: dict[str, tuple[str, str]] = {
    'ashtottari': ('jhora.horoscope.dhasa.graha.ashtottari', 'get_ashtottari_dhasa_bhukthi'),
    'yogini': ('jhora.horoscope.dhasa.graha.yogini', 'get_yogini_dhasa_bhukthi'),
    'shodashottari': ('jhora.horoscope.dhasa.graha.shodasottari', 'get_dhasa_bhukthi'),
    'dwadasottari': ('jhora.horoscope.dhasa.graha.dwadasottari', 'get_dhasa_bhukthi'),
    'panchottari': ('jhora.horoscope.dhasa.graha.panchottari', 'get_dhasa_bhukthi'),
    'shatabdika': ('jhora.horoscope.dhasa.graha.sataatbika', 'get_dhasa_bhukthi'),
    'chaturashiti_sama': ('jhora.horoscope.dhasa.graha.chathuraaseethi_sama', 'get_dhasa_bhukthi'),
    'dwisaptati_sama': ('jhora.horoscope.dhasa.graha.dwisatpathi', 'get_dhasa_bhukthi'),
    'shashtihayani': ('jhora.horoscope.dhasa.graha.shastihayani', 'get_dhasa_bhukthi'),
}
_RASI_DASHA_MAP: dict[str, tuple[str, str]] = {
    'sthira': ('jhora.horoscope.dhasa.raasi.sthira', 'get_dhasa_antardhasa'),
    'narayana': ('jhora.horoscope.dhasa.raasi.narayana', 'narayana_dhasa_for_rasi_chart'),
    'drig': ('jhora.horoscope.dhasa.raasi.drig', 'get_dhasa_antardhasa'),
    'yogardha': ('jhora.horoscope.dhasa.raasi.yogardha', 'get_dhasa_antardhasa'),
    'paryaaya': ('jhora.horoscope.dhasa.raasi.paryaaya', 'get_dhasa_antardhasa'),
    'brahma': ('jhora.horoscope.dhasa.raasi.brahma', 'get_dhasa_antardhasa'),
    'mandooka': ('jhora.horoscope.dhasa.raasi.mandooka', 'get_dhasa_antardhasa'),
    'sudasa': ('jhora.horoscope.dhasa.raasi.sudasa', 'get_dhasa_antardhasa'),
    'kalachakra': ('jhora.horoscope.dhasa.raasi.kalachakra', 'get_dhasa_antardhasa'),
    'navamsa': ('jhora.horoscope.dhasa.raasi.navamsa', 'get_dhasa_antardhasa'),
    'trikona': ('jhora.horoscope.dhasa.raasi.trikona', 'get_dhasa_antardhasa'),
    'chakra': ('jhora.horoscope.dhasa.raasi.chakra', 'get_dhasa_antardhasa'),
    'kendraadhi_rasi': ('jhora.horoscope.dhasa.raasi.kendradhi_rasi', 'get_dhasa_antardhasa'),
    'shoola': ('jhora.horoscope.dhasa.raasi.shoola', 'get_dhasa_antardhasa'),
}

def _planet_label(value: Any) -> str:
    if isinstance(value, str):
        return 'Ascendant' if value == getattr(_jconst, '_ascendant_symbol', 'L') else value
    try:
        idx = int(value)
    except (TypeError, ValueError):
        return str(value)
    if 0 <= idx < len(_PLANET_NAMES):
        return _PLANET_NAMES[idx]
    return str(idx)

def _sign_label(value: Any) -> str:
    try:
        idx = int(value)
    except (TypeError, ValueError):
        return str(value)
    if 0 <= idx < len(_SIGN_NAMES):
        return _SIGN_NAMES[idx]
    return str(idx)

def _deg_to_dms(degrees: float) -> str:
    neg = degrees < 0
    value = abs(float(degrees))
    d = int(value)
    m = int((value - d) * 60)
    s = int(round(((value - d) * 60 - m) * 60))
    return f"{'-' if neg else ''}{d}\u00b0 {m}' {s}\""

def _format_degree(value: Any) -> str:
    try:
        return _deg_to_dms(float(value))
    except Exception:
        return str(value)

def _format_jd_datetime(jd_value: Any) -> str:
    try:
        y, m, d, fh = _jut.jd_to_gregorian(float(jd_value))
        total_seconds = int(round(fh * 3600))
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{y:04d}-{m:02d}-{d:02d} {hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return str(jd_value)

def _relative_house(sign_index: int | None, asc_sign: int | None) -> int | None:
    if sign_index is None or asc_sign is None:
        return None
    try:
        return ((int(sign_index) - int(asc_sign)) % 12) + 1
    except Exception:
        return None

def _format_sphuta_value(value: Any) -> str:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        sign = _sign_label(value[0])
        return f"{sign} {_format_degree(value[1])}"
    return str(value)

def _load_module(path: str):
    mod = _MODULE_CACHE.get(path)
    if mod is None:
        mod = importlib.import_module(path)
        _MODULE_CACHE[path] = mod
    return mod

def _get_birth_details(stored: models.StoredHoroscope):
    dob_vals, tob_vals, place = _extract_birth_context(stored)
    try:
        dob_date = _drik.Date(int(dob_vals[0]), int(dob_vals[1]), int(dob_vals[2]))
    except Exception:
        dob_date = _drik.Date(*dob_vals)  # type: ignore[arg-type]
    tob_tuple = (
        int(tob_vals[0]) if len(tob_vals) > 0 else 0,
        int(tob_vals[1]) if len(tob_vals) > 1 else 0,
        int(tob_vals[2]) if len(tob_vals) > 2 else 0,
    )
    return dob_date, tob_tuple, place

def _stored_birth_year(stored: models.StoredHoroscope) -> int | None:
    try:
        req = stored.request
        if req and getattr(req, 'birthDateTime', None):
            return int(req.birthDateTime.year)  # type: ignore[union-attr]
    except Exception:
        pass
    dob = getattr(getattr(stored, 'internalHoroscope', None), 'Date', None)
    if dob is not None and hasattr(dob, 'year'):
        try:
            return int(dob.year)
        except Exception:
            return None
    return None

def _normalize_tajaka_year(year_value: Any, stored: models.StoredHoroscope) -> int:
    try:
        target = int(year_value)
    except (TypeError, ValueError):
        raise HTTPException(400, 'year must be an integer')
    birth_year = _stored_birth_year(stored)
    if birth_year and target >= 1600:
        offset = target - birth_year
    else:
        offset = target
    if offset < 0:
        offset = abs(offset)
    return max(1, offset)

def _parse_dms_time_string(text: str) -> tuple[int, int, int]:
    import re
    if not text:
        return (0, 0, 0)
    numbers = re.findall(r'-?\d+', text)
    if not numbers:
        return (0, 0, 0)
    hours = int(numbers[0])
    minutes = int(numbers[1]) if len(numbers) > 1 else 0
    seconds = int(numbers[2]) if len(numbers) > 2 else 0
    return (hours, minutes, seconds)

def _format_patyayini_start(date_str: str, time_str: str) -> str:
    try:
        from datetime import datetime as _dt
        h, m, s = _parse_dms_time_string(time_str)
        dt = _dt.strptime(date_str.strip(), '%Y-%m-%d')
        dt = dt.replace(hour=h % 24, minute=m, second=s)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return f"{date_str} {time_str}".strip()

def _format_period_entry(dhasa: Any, bhukti: Any | None, start: Any, duration: Any | None = None, *, labeler=_planet_label):
    entry: dict[str, Any] = {
        'dhasaLord': labeler(dhasa),
        'start': str(start),
    }
    if bhukti is not None:
        entry['antardashaLord'] = labeler(bhukti)
    if duration is not None:
        try:
            entry['durationYears'] = float(duration)
        except Exception:
            entry['duration'] = duration
    return entry

def _invoke_graha_dasha(system: str, stored: models.StoredHoroscope, include_antardhasa: bool = True):
    config = _GRAHA_DASHA_MAP.get(system)
    if not config:
        raise HTTPException(404, f'Unknown graha dasha system: {system}')
    module = _load_module(config[0])
    fn = getattr(module, config[1], None)
    if not fn:
        raise HTTPException(500, f'Dasha calculator not available for {system}')
    dob, tob, place = _get_birth_details(stored)
    _, jd, _ = _ensure_horoscope_context(stored)
    kwargs: dict[str, Any] = {}
    for name in inspect.signature(fn).parameters:
        if name in {'jd', 'jd_at_dob', 'jd_at_years'}:
            kwargs[name] = jd
        elif name == 'place':
            kwargs[name] = place
        elif name == 'dob':
            kwargs[name] = dob
        elif name == 'tob':
            kwargs[name] = tob
        elif name == 'include_antardhasa':
            kwargs[name] = include_antardhasa
        elif name == 'divisional_chart_factor':
            kwargs[name] = 1
        elif name == 'chart_method':
            kwargs[name] = 1
        elif name == 'years':
            kwargs[name] = 1
        elif name == 'months':
            kwargs[name] = 1
        elif name == 'sixty_hours':
            kwargs[name] = 1
        elif name == 'star_position_from_moon':
            kwargs[name] = 1
        elif name == 'use_tribhagi_variation':
            kwargs[name] = False
        elif name == 'seed_star':
            kwargs[name] = 8
        elif name == 'dhasa_starting_planet':
            kwargs[name] = 1
    return fn(**kwargs)

def _format_graha_periods(raw: list[Any], include_antardhasa: bool, limit: int) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    for item in raw:
        if include_antardhasa and isinstance(item, (list, tuple)) and len(item) >= 3:
            duration = item[3] if len(item) > 3 else None
            periods.append(_format_period_entry(item[0], item[1], item[2], duration))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            duration = item[2] if len(item) > 2 else None
            periods.append(_format_period_entry(item[0], None, item[1], duration))
        else:
            periods.append({'dhasaLord': _planet_label(item), 'start': ''})
        if len(periods) >= limit:
            break
    return periods

def _invoke_rasi_dasha(system: str, stored: models.StoredHoroscope, include_antardhasa: bool = True):
    config = _RASI_DASHA_MAP.get(system)
    if not config:
        raise HTTPException(404, f'Unknown rasi dasha system: {system}')
    module = _load_module(config[0])
    fn = getattr(module, config[1], None)
    if not fn:
        raise HTTPException(500, f'Dasha calculator not available for {system}')
    dob, tob, place = _get_birth_details(stored)
    _, jd, _ = _ensure_horoscope_context(stored)
    kwargs: dict[str, Any] = {}
    for name in inspect.signature(fn).parameters:
        if name in {'jd', 'jd_at_dob', 'jd_at_years'}:
            kwargs[name] = jd
        elif name == 'place':
            kwargs[name] = place
        elif name == 'dob':
            kwargs[name] = dob
        elif name == 'tob':
            kwargs[name] = tob
        elif name == 'include_antardhasa':
            kwargs[name] = include_antardhasa
        elif name == 'divisional_chart_factor':
            kwargs[name] = 1
        elif name == 'chart_method':
            kwargs[name] = 1
        elif name == 'years':
            kwargs[name] = 1
        elif name == 'months':
            kwargs[name] = 1
        elif name == 'sixty_hours':
            kwargs[name] = 1
    return fn(**kwargs)

def _format_rasi_periods(raw: list[Any], include_antardhasa: bool, limit: int) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    for item in raw:
        if include_antardhasa and isinstance(item, (list, tuple)) and len(item) >= 3:
            duration = item[3] if len(item) > 3 else None
            periods.append(_format_period_entry(item[0], item[1], item[2], duration, labeler=_sign_label))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            duration = item[2] if len(item) > 2 else None
            periods.append(_format_period_entry(item[0], None, item[1], duration, labeler=_sign_label))
        else:
            periods.append({'dhasaLord': _sign_label(item[0] if isinstance(item, (list, tuple)) else item), 'start': str(item[2] if isinstance(item, (list, tuple)) and len(item) > 2 else '')})
        if len(periods) >= limit:
            break
    return periods

def _handle_rasi_dasha(system: str, request_id: str, limit: int, include_antardhasa: bool):
    stored = _get_stored_or_404(request_id)
    raw = _invoke_rasi_dasha(system, stored, include_antardhasa=include_antardhasa)
    raw_list = raw if isinstance(raw, list) else list(raw)
    periods = _format_rasi_periods(raw_list, include_antardhasa, limit)
    return {
        'requestId': request_id,
        'system': system,
        'periods': periods,
        'returned': len(periods),
        'total': len(raw_list),
        'includeAntardhasa': include_antardhasa,
    }

def _serialize_tajaka_chart(chart: list[Any]):
    asc_sign = None
    asc_long = None
    for pid, data in chart:
        if pid == getattr(_jconst, '_ascendant_symbol', 'L'):
            asc_sign = data[0]
            asc_long = data[1]
            break
    entries = []
    for pid, data in chart:
        sign = data[0]
        deg = data[1]
        if pid == getattr(_jconst, '_ascendant_symbol', 'L'):
            continue
        entries.append({
            'name': _planet_label(pid),
            'sign': _sign_label(sign),
            'longitudeDMS': _format_degree(deg),
            'house': _relative_house(sign, asc_sign),
            'rawLongitude': deg,
            'signIndex': sign,
        })
    return entries, asc_sign, asc_long

def _panchavargiya_summary(jd_year: float, place: Any) -> dict[str, Any]:
    try:
        scores = _strength.pancha_vargeeya_bala(jd_year, place)
    except Exception:
        return {}
    threshold = getattr(_jconst, 'pancha_vargeeya_bala_strength_threshold', 10)
    summary: dict[str, Any] = {}
    for idx, value in scores.items():
        summary[_planet_label(idx)] = {
            'total': round(float(value), 2),
            'strength': 'Strong' if value >= threshold else 'Average',
        }
    return summary

def _yoga_entry(name: str, planets: list[Any], detail: str | None = None) -> dict[str, Any]:
    return {
        'name': name,
        'planets': [_planet_label(p) for p in planets],
        'detail': detail or ''
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def _load_world_city_index() -> None:
    await service.preload_world_city_index()

@app.post('/api/config/outer_planets')
async def set_outer_planets(enabled: bool):
    """Toggle inclusion of Uranus/Neptune/Pluto in underlying library.
    This flips jhora.const._INCLUDE_URANUS_TO_PLUTO at runtime.
    Returns new state."""
    try:
        import jhora.const as _c
        from jhora.panchanga import drik as _drik
        _c._INCLUDE_URANUS_TO_PLUTO = bool(enabled)
        # Also switch the active planet list used by calculations
        try:
            if _c._INCLUDE_URANUS_TO_PLUTO:
                _drik.set_sideral_planets()
            else:
                # Reset to classical 9 (Sun..Saturn + Rahu/Ketu)
                _drik.planet_list = [
                    _c._SUN, _c._MOON, _c._MARS, _c._MERCURY, _c._JUPITER,
                    _c._VENUS, _c._SATURN, _c._RAHU, _c._KETU
                ]
        except Exception as _ie:
            logging.debug(f"Failed to switch planet_list when toggling outers: {_ie}")
        return { 'enabled': _c._INCLUDE_URANUS_TO_PLUTO }
    except Exception as e:  # noqa
        raise HTTPException(500, f'failed to toggle outer planets: {e}')

@app.get('/api/config/outer_planets')
async def get_outer_planets():
    try:
        import jhora.const as _c
        return { 'enabled': bool(getattr(_c,'_INCLUDE_URANUS_TO_PLUTO', False)) }
    except Exception as e:
        raise HTTPException(500, f'failed to read outer planets config: {e}')

@app.get('/api/house_systems')
async def house_systems():
    """List available house system keys and labels from library constants."""
    try:
        import jhora.const as _c
        items = [{ 'key': k, 'label': v } for k,v in _c.available_house_systems.items()]
        return { 'items': items, 'default': _c.bhaava_madhya_method }
    except Exception as e:
        raise HTTPException(500, f'failed to list house systems: {e}')

@app.get('/api/languages')
async def list_languages():
    try:
        import jhora.const as _c
        available = getattr(_c, 'available_languages', {})
        items = [{ 'label': name, 'code': code } for name, code in available.items()]
        default = getattr(_c, '_DEFAULT_LANGUAGE', 'en')
        return { 'items': items, 'default': default }
    except Exception as e:
        raise HTTPException(500, f'failed to list languages: {e}')




def _get_stored_or_404(request_id: str):
    stored = service.get_stored(request_id)
    if not stored or not stored.internalHoroscope:
        raise HTTPException(404, f"requestId '{request_id}' not found. Create one via POST /api/horoscope.")
    return stored


def _extract_birth_context(stored: models.StoredHoroscope) -> tuple[tuple[int, int, int], tuple[int, int, int], Any]:
    """Return (dob, tob, place) tuples from a stored horoscope."""
    h = getattr(stored, 'internalHoroscope', None)
    if h is None:
        raise HTTPException(500, 'Stored horoscope missing internal state')

    dob_raw = getattr(h, 'Date', None)
    place = getattr(h, 'Place', None)
    if dob_raw is None or place is None:
        raise HTTPException(500, 'Stored horoscope missing birth context')

    if hasattr(dob_raw, 'year') and hasattr(dob_raw, 'month') and hasattr(dob_raw, 'day'):
        dob = (int(dob_raw.year), int(dob_raw.month), int(dob_raw.day))
    elif isinstance(dob_raw, (tuple, list)) and len(dob_raw) >= 3:
        dob = (int(dob_raw[0]), int(dob_raw[1]), int(dob_raw[2]))
    else:
        raise HTTPException(500, 'Unable to determine birth date for stored request')

    tob_raw = getattr(h, 'birth_time', None)
    if isinstance(tob_raw, str):
        try:
            parts = [int(p) for p in tob_raw.split(':')[:3]]
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(500, f'Invalid stored birth time: {tob_raw}') from exc
        while len(parts) < 3:
            parts.append(0)
        tob = (parts[0], parts[1], parts[2])
    elif isinstance(tob_raw, (tuple, list)) and len(tob_raw) >= 2:
        parts = [int(tob_raw[0]), int(tob_raw[1])]
        sec = int(tob_raw[2]) if len(tob_raw) > 2 else 0
        parts.append(sec)
        tob = (parts[0], parts[1], parts[2])
    else:
        tob = (0, 0, 0)

    return dob, tob, place

@app.get('/api/health')
async def health():
    # Use timezone-aware UTC to avoid deprecation warning
    info: dict[str, object] = {'status':'ok','time': datetime.now(UTC).isoformat()}
    try:
        import jhora as _jh  # type: ignore
        jm = getattr(_jh, '__file__', '')
        info['jhoraModule'] = str(jm or '')
    except Exception:
        info['jhoraModule'] = ''
    try:
        ep = os.environ.get('SE_EPHE_PATH') or ''
        info['ephePath'] = ep
        info['ephePathExists'] = bool(ep and os.path.isdir(ep))
    except Exception:
        info['ephePath'] = ''
        info['ephePathExists'] = False
    try:
        info['worldCityIndexReady'] = service.world_city_index_ready()
        err = service.world_city_index_error()
        if err:
            info['worldCityIndexError'] = str(err)
    except Exception:
        info['worldCityIndexReady'] = False
    return info

@app.get('/api/places')
def search_places(q: str):
    """Simple offline place search backed by world_cities_with_tz.csv.
    Returns all matches for the given prefix (no limit).
    Frontend will filter further as user types.
    """
    if not q or len(q.strip()) < 3:
        return {'items': []}
    
    # Ensure data is loaded
    _load_places()
    
    ql = q.strip().lower()
    prefix = ql[:3]  # Use first 3 characters for index lookup
    
    # Get all candidates from index
    candidates = _PLACES_INDEX.get(prefix, [])
    
    # Return all candidates that match the prefix (no limit)
    # Frontend will filter as user types more
    results = [p for p in candidates if p['label'].lower().startswith(ql)]
    
    return {'items': results}

@app.get('/api/flags/planets')
async def planet_flags(request_id: str):
    """Return lightweight planet flags (combustion, vargottama) for a stored horoscope.
    Frontend uses this small endpoint (polled occasionally) instead of re-fetching the heavy
    full horoscope payload to refresh dynamic planet state indicators.
    Shape: { requestId, combustion: [names], vargottama: [names] }
    Falls back to empty lists if data not present (never 404 so UI can keep polling safely)."""
    stored = service.get_stored(request_id)
    if not stored:
        # Return empty but with requestId so UI can decide to stop polling.
        return { 'requestId': request_id, 'combustion': [], 'vargottama': [] }
    resp = stored.response
    comb = getattr(resp,'combustion', None)
    varg = getattr(resp,'vargottama', None)
    return {
        'requestId': request_id,
        'combustion': [c for c in comb] if isinstance(comb, (list,tuple)) else [],
        'vargottama': [v for v in varg] if isinstance(varg, (list,tuple)) else []
    }

@app.get('/api/special_lagnas')
async def special_lagnas(request_id: str):
    """Return special lagnas and key points (bhava, hora, ghati, sri, indu, bhrigu bindu) plus bhava cusps.
    Lightweight extraction from internal horoscope object. Missing items omitted silently.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    from typing import Any, cast
    out: dict[str, Any] = {'requestId': request_id}
    try:
        # Access precomputed or compute via functions on horoscope/main or drik modules
        from jhora.panchanga import drik
        from jhora.panchanga import drik1 as _drik1
        jd = getattr(h,'julian_day', None)
        place = getattr(h,'Place', None)
        ay_mode = getattr(h,'ayanamsa_mode', None)
        bt = getattr(h,'birth_time', None)
        def _simplify_lagna(raw: Any) -> dict[str, Any] | None:
            """Normalize various lagna return shapes into {house, data:[sign,deg]}.

            Expected raw forms from JHora helpers:
              - [signIndex, degreeInSign]
              - [house, signIndex, degreeInSign, ...]
              - [[house, signIndex, degreeInSign, ...], ...]
            """
            if not isinstance(raw, (list, tuple)) or not raw:
                return None
            first = raw[0] if isinstance(raw[0], (list, tuple)) else raw
            if not isinstance(first, (list, tuple)) or len(first) < 2:
                return None
            house: int | None = None
            sign_index: float
            deg_in_sign: float
            if len(first) >= 3:
                try:
                    house = int(first[0]) if first[0] is not None else None
                except Exception:
                    house = None
                sign_index = float(first[1])
                deg_in_sign = float(first[2])
            else:
                sign_index = float(first[0])
                deg_in_sign = float(first[1])
            return {'house': house, 'data': [sign_index, deg_in_sign]}

        if jd and place:
            # Functions may vary in signature; wrap in try blocks
            try:
                bl = drik.bhava_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(bl)
                if payload is not None:
                    out['bhavaLagna'] = payload
            except Exception:
                pass
            # Additional lagna computations
            try:
                vl = drik.vighati_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(vl)
                if payload is not None:
                    out['vighatiLagna'] = payload
            except Exception:
                pass
            try:
                pl = drik.pranapada_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(pl)
                if payload is not None:
                    out['pranapadaLagna'] = payload
            except Exception:
                pass
            try:
                hl = drik.hora_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(hl)
                if payload is not None:
                    out['horaLagna'] = payload
            except Exception:
                pass
            try:
                gl = drik.ghati_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(gl)
                if payload is not None:
                    out['ghatiLagna'] = payload
            except Exception:
                pass
            try:
                sl = drik.sree_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(sl)
                if payload is not None:
                    out['sriLagna'] = payload
            except Exception:
                pass
            try:
                il = drik.indu_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(il)
                if payload is not None:
                    out['induLagna'] = payload
            except Exception:
                pass
            try:
                kl = drik.kunda_lagna(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                payload = _simplify_lagna(kl)
                if payload is not None:
                    out['kundaLagna'] = payload
            except Exception:
                pass
            try:
                bb = getattr(drik,'bhrigu_bindu', None)
                if callable(bb):
                    bbr = bb(jd, place, ayanamsa_mode=ay_mode)  # type: ignore
                    out['bhriguBindu'] = bbr
            except Exception:
                pass
            # Varnada lagna (requires date/time/place) via charts.varnada_lagna if available
            try:
                from jhora.horoscope import charts as _charts  # type: ignore
                dob = getattr(h,'Date', None)
                tob = getattr(h,'birth_time', (0,0,0)) or (0,0,0)
                if dob is not None and hasattr(_charts,'varnada_lagna'):
                    # Choose house_index=1 base
                    vlr = _charts.varnada_lagna((dob.year,dob.month,dob.day), tob, place, house_index=1)  # type: ignore[attr-defined]
                    if isinstance(vlr,(list,tuple)):
                        payload = _simplify_lagna(vlr)
                        if payload is not None:
                            out['varnadaLagna'] = payload
            except Exception:
                pass
            # Upagraha longitudes (gulika / maandi) if available
            try:
                gul = getattr(_drik1,'gulika_longitude', None)
                if callable(gul):
                    out['gulika'] = gul(bt if bt else (0,0,0), bt if bt else (0,0,0), place)  # type: ignore[arg-type]
            except Exception:
                pass
            try:
                mand = getattr(_drik1,'maandi_longitude', None)
                if callable(mand):
                    out['maandi'] = mand(bt if bt else (0,0,0), bt if bt else (0,0,0), place)  # type: ignore[arg-type]
            except Exception:
                pass
        # Bhava cusps if present
        cusps = getattr(h,'bhava_cusps', None)
        if cusps and isinstance(cusps,(list,tuple)):
            out['bhavaCusps'] = cusps
    except Exception as e:  # noqa
        out['error'] = str(e)
    return out

@app.get('/api/special_points')
async def special_points(request_id: str):
    """Return extended special points / upagrahas (solar & planetary) and yogi/avayogi info.
    Includes:
      - Solar upagrahas: dhuma, vyatipaata, parivesha, indrachaapa, upaketu
      - Day/Night part based: kaala, mrityu, artha_praharaka, yama_ghantaka, gulika, maandi
      - Current yogam index (if available) plus yogi & avayogi planet short names
    All fields optional; failures captured per-item silently. Intended for diagnostic / display only.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    out: Dict[str, Any] = { 'requestId': request_id }
    try:
        from jhora.panchanga import drik as _drik
        # Basic context
        jd = getattr(h,'julian_day', None)
        place = getattr(h,'Place', None)
        ay_mode = getattr(h,'ayanamsa_mode', None)
        dob_obj = getattr(h,'Date', None)
        tob = getattr(h,'birth_time', (0,0,0)) or (0,0,0)
        # Solar upagrahas needing only solar longitude
        if jd is not None:
            try:
                sol = _drik.solar_longitude(jd)
                for name in ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu']:
                    try:
                        r = _drik.solar_upagraha_longitudes(sol, name)
                        if isinstance(r,(list,tuple)) and len(r)==2:
                            out[name] = { 'constellation': r[0], 'position': r[1] }
                    except Exception:
                        pass
            except Exception:
                pass
        # Day part based upagrahas require date/time/place
        if place is not None and dob_obj is not None:
            # Helper call wrapper to reduce duplication
            def _call(fn_name: str, label: str):
                fn = getattr(_drik, fn_name, None)
                if callable(fn):
                    try:
                        r = fn(dob_obj, tob, place, ayanamsa_mode=ay_mode)  # type: ignore[call-arg]
                        # Expect [constellation, coordinate]
                        if isinstance(r,(list,tuple)) and len(r)==2:
                            out[label] = { 'constellation': r[0], 'position': r[1] }
                        else:
                            out[label] = r
                    except Exception:
                        pass
            _call('kaala_longitude','kaala')
            _call('mrityu_longitude','mrityu')
            _call('artha_praharaka_longitude','artha_praharaka')
            _call('yama_ghantaka_longitude','yama_ghantaka')
            _call('gulika_longitude','gulika')
            _call('maandi_longitude','maandi')
        # Yogi / Avayogi info from yogam and const mapping
        try:
            if jd is not None and place is not None:
                yg = _drik.yogam(jd, place)
                if isinstance(yg,(list,tuple)) and yg:
                    idx = yg[0]
                    out['yogam'] = { 'index': idx, 'raw': yg }
                    # Mapping to yogi / avayogi
                    from jhora import const as _c
                    try:
                        pair = _c.yogam_lords_and_avayogis[idx-1]
                        # Load resource lists to populate PLANET_SHORT_NAMES if not already
                        from jhora import utils as _u
                        if not hasattr(_u,'PLANET_SHORT_NAMES') or not getattr(_u,'PLANET_SHORT_NAMES'):
                            try:
                                _u.get_resource_lists()  # populates module attributes
                            except Exception:
                                pass
                        pshort = getattr(_u,'PLANET_SHORT_NAMES', []) or []
                        out['yogiAvayogi'] = {
                            'yogiPlanetIndex': pair[0],
                            'avayogiPlanetIndex': pair[1],
                            'yogi': pshort[pair[0]] if pair[0] < len(pshort) else None,
                            'avayogi': pshort[pair[1]] if pair[1] < len(pshort) else None,
                        }
                    except Exception:
                        pass
            # Dagdha Rasi (if library exposes mapping) – heuristic: const.dagdha_rasi_list or similar
            try:
                from jhora import const as _c2
                dagdha = getattr(_c2, 'dagdha_rasi_list', None)
                if dagdha:
                    out['dagdhaRasi'] = dagdha
            except Exception:
                pass
        except Exception:
            pass
    except Exception as e:  # noqa
        out['error'] = str(e)
    return out

@app.get('/api/arudha')
async def arudha_padas(request_id: str, includeD9: bool = True):
    """Return Arudha Padas (Bhava Arudhas) for D1 (and D9 if available) plus Arudha menu grid.
    Uses internal horoscope private helper. If computation fails, returns error field.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    try:
        if not h:
            raise ValueError('internal horoscope missing')
        # Build basic dob / tob tuples
        dob = (getattr(h.Date,'year',0), getattr(h.Date,'month',0), getattr(h.Date,'day',0))  # type: ignore[attr-defined]
        tob = getattr(h,'birth_time', (0,0,0)) or (0,0,0)
        place = getattr(h,'Place', None)
        if place is None:
            raise ValueError('place missing')
        out: Dict[str, Any] = { 'requestId': request_id, 'bhavaArudhas': {}, 'bhavaArudhasD9': None, 'menu': None }
        try:
            ba_d1 = h._get_arudha_padhas(dob, tob, place, divisional_chart_factor=1)
            out['bhavaArudhas'] = _to_native(ba_d1)
            out['menu'] = _to_native(getattr(h,'_arudha_menu_dict', None))
        except Exception as e:  # noqa
            out['errorD1'] = str(e)
        if includeD9:
            try:
                ba_d9 = h._get_arudha_padhas(dob, tob, place, divisional_chart_factor=9)
                out['bhavaArudhasD9'] = _to_native(ba_d9)
            except Exception as e:  # noqa
                out['errorD9'] = str(e)
        return out
    except Exception as e:  # noqa
        return { 'requestId': request_id, 'error': str(e) }

@app.get('/api/alt_charts')
async def alternative_charts(request_id: str, includeChandra: bool = True, includeSurya: bool = True):
    """Return alternative Lagna based variants of the Rasi chart (Chandra Lagna, Surya Lagna).
    These are derived by rotating houses so that Moon / Sun occupy house 1 respectively.
    """
    stored = _get_stored_or_404(request_id)
    base = stored.response.rasiChart
    def make_alt(pivot_name: str, label: str):
        # Find pivot planet house
        pivot = next((p for p in base.planets if p.name == pivot_name), None)
        if not pivot:
            return None
        offset = (pivot.house - 1)  # houses are 1..12
        # Rotate houses
        new_houses = []
        for h in base.houses:
            new_index = ((h.index - offset - 1) % 12) + 1
            new_houses.append({'index': new_index, 'items': h.items})
        new_houses.sort(key=lambda x: x['index'])
        # Rotate planet house numbers
        new_planets = []
        for p in base.planets:
            new_house = ((p.house - offset - 1) % 12) + 1
            new_planets.append({ **p.model_dump(), 'house': new_house })  # type: ignore[attr-defined]
        return {
            'factor': 1,
            'label': label,
            'ascendantHouse': 1,
            'houses': new_houses,
            'planets': new_planets,
            'specialLagna': base.specialLagna,
            'sphuta': base.sphuta,
            'rotationOffset': offset,
        }
    out: Dict[str, Any] = { 'requestId': request_id }
    if includeChandra:
        try:
            ch = make_alt('Moon','Chandra Lagna')
            if ch: out['chandra'] = ch
        except Exception as e:  # noqa
            out['errorChandra'] = str(e)
    if includeSurya:
        try:
            su = make_alt('Sun','Surya Lagna')
            if su: out['surya'] = su
        except Exception as e:  # noqa
            out['errorSurya'] = str(e)
    return out

@app.get('/api/bhava_chakra')
async def bhava_chakra(request_id: str):
    """Return Bhava Chakra (house cusp start/mid/end with planet listing) from internal horoscope."""
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    if not h:
        raise HTTPException(404,'internal horoscope missing')
    info = getattr(h,'bhava_chart_info', None)
    chart = getattr(h,'bhava_chart', None)
    if info is None or chart is None:
        return {'requestId': request_id, 'error':'bhava data not available'}
    # info entries: (key,bss,bms,bes,ps)
    houses = []
    for entry in info:
        try:
            key,bss,bms,bes,ps = entry
            idx = int(str(key).split('-')[-1])
            houses.append({'house': idx, 'start': bss, 'mid': bms, 'end': bes, 'planets': ps.split('\n') if ps else []})
        except Exception:
            continue
    return {'requestId': request_id, 'houses': houses}

@app.get('/api/debug/horoscope/{request_id}')
async def debug_horoscope(request_id: str):
    stored = service.get_stored(request_id)
    if not stored or not stored.internalHoroscope:
        raise HTTPException(404,'not found')
    h = stored.internalHoroscope
    # Provide minimal debug context (avoid huge objects)
    info = {
        'requestId': request_id,
        'birth_time_raw': getattr(h,'birth_time', None),
        'date_tuple': (getattr(h,'Date').year, getattr(h,'Date').month, getattr(h,'Date').day) if getattr(h,'Date', None) else None,
        'has_vimsottari_balance': hasattr(h,'_vimsottari_balance'),
        'vimsottari_balance': getattr(h,'_vimsottari_balance', None),
        'calendar_keys': list(getattr(h,'calendar_info', {}).keys())[:15]
    }
    return info

async def _agent_dispatch_task(request_id: str):
    stored = service.get_stored(request_id)
    if not stored:
        return
    result = await agent.dispatch_to_agent(stored)
    stored.agentResult = result
    stored.agentDispatched = result.success

@app.post('/api/horoscope', response_model=models.HoroscopeResponse)
async def create_horoscope(req: models.HoroscopeRequest, background: BackgroundTasks):
    try:
        stored = await asyncio.to_thread(service.compute_horoscope, req)
    except Exception as e:
        # Provide clearer diagnostics during development/testing
        import traceback, logging
        logging.error("Failed to compute horoscope: %s", e)
        logging.error("Traceback:\n%s", traceback.format_exc())
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(status_code=500, detail=f"compute_horoscope failed: {type(e).__name__}: {e}")
    if req.sendToAgent:
        background.add_task(_agent_dispatch_task, stored.response.meta['requestId'])
    return stored.response

@app.get('/api/horoscope/{request_id}', response_model=models.HoroscopeResponse)
async def get_horoscope(request_id: str, request: Request, response: Response):
    stored = _get_stored_or_404(request_id)
    data = stored.response
    key = _cache_key(f"horoscope:{request_id}")
    # Build a lightweight cache representation
    payload = data.model_dump() if hasattr(data,'model_dump') else data
    etag = _build_etag({'meta': payload.get('meta'), 'asc': payload.get('rasiChart',{}).get('ascendantHouse')}) if isinstance(payload, dict) else None
    inm = request.headers.get('If-None-Match')
    if etag and inm == etag:
        response.status_code = 304
        return None  # Not Modified
    if etag:
        response.headers['ETag'] = etag
    await _cache_set(key, {'etag': etag})
    return data


@app.get('/api/horoscope/{request_id}/details', response_model=models.HoroscopeDetailsResponse)
async def get_horoscope_details(
    request_id: str,
    language: str = 'en',
    includeYogas: bool = True,
    includeRajaYogas: bool = True,
    includeBaseInfo: bool = True
):
    stored = _get_stored_or_404(request_id)
    try:
        details = await asyncio.to_thread(
            service.build_detailed_calculations,
            stored,
            language,
            includeYogas,
            includeRajaYogas,
            includeBaseInfo
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'failed to build detailed calculations: {exc}')
    return details


@app.get('/api/horoscope/{request_id}/render')
async def render_horoscope_chart(request_id: str, request: Request, response: Response, chart: str = 'D1', style: str = 'South', format: str = 'svg', theme: str = 'Light', size: int = 400):
    """Return a server-side rendered SVG (or JSON) for a stored horoscope request.
    Minimal implementation: supports format=svg and returns a simple D1 circular SVG.
    """
    stored = service.get_stored(request_id)
    if not stored:
        raise HTTPException(404, 'requestId not found')
    # Use rasiChart for D1 or find matching divisional chart
    chart_obj = None
    if chart.upper() in ('D1','RAASI','RASI'):
        chart_obj = stored.response.rasiChart
    else:
        # try find divisionalCharts
        for dc in getattr(stored.response, 'divisionalCharts', []) or []:
            if f'D{getattr(dc, "factor", None)}' == chart.upper() or str(getattr(dc,'factor',None)) == chart:
                chart_obj = dc; break
    if chart_obj is None:
        raise HTTPException(404, 'requested chart not available for this request')
    try:
        from . import render as _render
        # Use in-memory cache to avoid recomputing SVGs repeatedly
        cache_key = _cache_key(f"render:{request_id}:{chart}:{style}:{size}")
        cached = await _cache_get(cache_key)
        inm = request.headers.get('If-None-Match')
        if cached and isinstance(cached, dict) and cached.get('etag'):
            # If client has same ETag, short-circuit
            if inm and inm == cached.get('etag'):
                return Response(status_code=304)
            # return cached content
            if format == 'svg':
                resp = Response(content=cached.get('svg',''), media_type='image/svg+xml')
                resp.headers['ETag'] = str(cached.get('etag') or '')
                resp.headers['Cache-Control'] = 'public, max-age=60'
                return resp
            else:
                # return positions + svg
                return { 'svg': cached.get('svg',''), 'positions': cached.get('positions', {}), 'etag': cached.get('etag') }

        # Not cached: compute and store
        if format == 'svg':
            svg = _render.render_chart_svg(chart_obj, style=style, theme=theme, size=size)
            etag = _build_etag({'rid': request_id, 'chart': chart, 'style': style, 'size': size, 'hash': svg[:200]})
            # store in cache
            try:
                await _cache_set(cache_key, {'etag': etag, 'svg': svg})
            except Exception:
                pass
            if inm and inm == etag:
                return Response(status_code=304)
            resp = Response(content=svg, media_type='image/svg+xml')
            resp.headers['ETag'] = str(etag or '')
            resp.headers['Cache-Control'] = 'public, max-age=60'
            return resp
        else:
            positions = _render.chart_to_positions(chart_obj, size=size)
            svg = _render.render_chart_svg(chart_obj, style=style, theme=theme, size=size)
            etag = _build_etag({'rid': request_id, 'chart': chart, 'style': style, 'size': size, 'hash': svg[:200]})
            try:
                await _cache_set(cache_key, {'etag': etag, 'svg': svg, 'positions': positions})
            except Exception:
                pass
            if inm and inm == etag:
                return Response(status_code=304)
            response.headers['ETag'] = str(etag or '')
            response.headers['Cache-Control'] = 'public, max-age=60'
            return { 'svg': svg, 'positions': positions }
    except Exception as e:
        raise HTTPException(500, f'render failed: {e}')

@app.get('/api/horoscope')
async def list_horoscopes(limit: int = 200):
    return { 'items': service.list_requests(limit=limit) }

@app.delete('/api/horoscope/{request_id}')
async def delete_horoscope(request_id: str):
    existed = await service.delete_request(request_id)
    # Also remove any agent events rows (optional) - implement soft ignore if events module lacks API
    try:
        import sqlite3, os
        from . import events as _events
        # direct DB cleanup by request_id
        conn = sqlite3.connect(_events.DB_PATH)
        with conn:
            conn.execute("DELETE FROM agent_events WHERE request_id=?", (request_id,))
        conn.close()
    except Exception:
        pass
    if not existed:
        raise HTTPException(404, 'not found')
    return { 'requestId': request_id, 'deleted': True }

@app.post('/api/agent/relay')
async def relay_agent(relay: models.AgentRelayRequest):
    stored = service.get_stored(relay.requestId)
    if not stored:
        raise HTTPException(404,'requestId not found')
    result = await agent.dispatch_to_agent(stored)
    stored.agentResult = result
    stored.agentDispatched = result.success
    return result.model_dump()

@app.get('/api/dhasa/chara', response_model=models.CharaDhasaResponse)
async def get_chara_dhasa(request_id: str, limit: int = 120, include_antardhasa: bool = True, method: int = 1):
    """Return Jaimini Chara Dasha periods.
    method: 1 => Parasara/PVN Rao (two cycles), 2 => KN Rao (single cycle).
    include_antardhasa chooses whether to expand bhukti (antardhasa) layer.
    Response uses rasi short names from utils.PLANET_SHORT_NAMES mapping for consistency.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    # Build dob / tob / place
    from jhora.panchanga import drik as _drik
    dob = _drik.Date(h.Date.year, h.Date.month, h.Date.day)  # type: ignore[attr-defined]
    try:
        bt_tuple = tuple(int(x) for x in h.birth_time)  # type: ignore[attr-defined]
    except Exception:
        bt_tuple = (getattr(h,'birth_hour',0), getattr(h,'birth_minute',0), getattr(h,'birth_second',0))
    place = h.Place  # type: ignore[attr-defined]
    try:
        from jhora.horoscope.dhasa.raasi import chara as _chara
    except Exception as e:
        raise HTTPException(500, f'chara dasha module missing: {e}')
    try:
        raw = _chara.get_dhasa_antardhasa(dob, bt_tuple, place, include_antardhasa=bool(include_antardhasa), chara_method=int(method))
    except Exception as e:
        raise HTTPException(500, f'chara computation failed: {e}')
    periods: list[models.CharaDhasaItem] = []
    count = 0
    # raw entries format when include_antardhasa=True: (dhasa_rasi_index, bhukti_rasi_index, start, duration_years_fraction)
    # else: (dhasa_rasi_index, start, duration_years)
    for item in raw:
        if count >= limit:
            break
        try:
            if include_antardhasa and isinstance(item,(list,tuple)) and len(item) >= 4:
                d_r, b_r, start, dur = item[0], item[1], item[2], item[3]
                periods.append(models.CharaDhasaItem(dhasaRasi=str(d_r), bhuktiRasi=str(b_r), start=str(start), durationYears=float(dur)))
            elif (not include_antardhasa) and isinstance(item,(list,tuple)) and len(item) >= 3:
                d_r, start, dur = item[0], item[1], item[2]
                periods.append(models.CharaDhasaItem(dhasaRasi=str(d_r), start=str(start), durationYears=float(dur) if isinstance(dur,(int,float)) else None))
            else:
                # Fallback best-effort parse
                periods.append(models.CharaDhasaItem(dhasaRasi=str(item[0] if isinstance(item,(list,tuple)) else item), start=str(item[2] if isinstance(item,(list,tuple)) and len(item)>2 else '')))  # type: ignore
            count += 1
        except Exception:
            continue
    # Map indices to sign names
    sign_names = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    def sn(v: str) -> str:
        try:
            i = int(v)
            if 0 <= i < 12:
                return sign_names[i]
        except Exception:
            return v
        return v
    for p in periods:
        p.dhasaRasi = sn(p.dhasaRasi)
        if p.bhuktiRasi:
            p.bhuktiRasi = sn(p.bhuktiRasi)
    return models.CharaDhasaResponse(requestId=request_id, periods=periods, total=len(raw), returned=len(periods), includeAntardhasa=bool(include_antardhasa), method=int(method))


@app.get('/api/dhasa/vimsottari')
def dhasa_vimsottari(request_id: str, limit: int = 120, include_antardhasa: bool = True, depth: int = 2, full_tree: bool = False, max_nodes: int = 2000, raw: bool = True):
    """
    Get Vimsottari Dhasa with configurable depth.
    depth: 1=MD only, 2=MD+AD (default), 3=MD+AD+PD, 4=MD+AD+PD+SD, 5=MD+AD+PD+SD+PAD
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    jd = getattr(h,'julian_day',None)
    place = getattr(h,'Place',None)
    
    # For depth > 2, use new hierarchical function
    if depth > 2:
        try:
            result = _vimsottari.get_vimsottari_dhasa_levels(jd, place, depth=depth)
            return {
                'requestId': request_id,
                'system': 'Vimsottari',
                'depth': depth,
                'periods': result[:limit] if limit else result
            }
        except Exception as e:
            # Fallback to old method if new function fails
            pass
    
    # Original implementation for depth <= 2
    bal, res = _vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=include_antardhasa)
    
    periods = []
    pnames = getattr(_jut,'PLANET_NAMES',['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
    
    for row in res:
        if len(row) >= 3 and include_antardhasa:
            dl, bl, start = row[:3]
            periods.append({'dhasaRasi': pnames[dl] if dl < len(pnames) else str(dl), 'bhuktiRasi': pnames[bl] if bl < len(pnames) else str(bl), 'start': str(start)})
        elif len(row) >= 2:
             dl, start = row[:2]
             periods.append({'dhasaRasi': pnames[dl] if dl < len(pnames) else str(dl), 'start': str(start)})
             
    return {
        'requestId': request_id,
        'system': 'Vimsottari',
        'balance': _to_native(bal),
        'periods': periods[:limit]
    }


@app.get('/api/dhasa/ashtottari')
def dhasa_ashtottari(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    """Return Ashtottari Dasha periods.
    include_antardhasa chooses whether to expand bhukti (antardhasa) layer.
    Response uses rasi short names from utils.PLANET_SHORT_NAMES mapping for consistency.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    # Build dob / tob / place
    from jhora.panchanga import drik as _drik
    dob = _drik.Date(h.Date.year, h.Date.month, h.Date.day)  # type: ignore[attr-defined]
    try:
        bt_tuple = tuple(int(x) for x in h.birth_time)  # type: ignore[attr-defined]
    except Exception:
        bt_tuple = (getattr(h,'birth_hour',0), getattr(h,'birth_minute',0), getattr(h,'birth_second',0))
    place = h.Place  # type: ignore[attr-defined]
    try:
        from jhora.horoscope.dhasa.graha import ashtottari
    except Exception as e:
        raise HTTPException(500, f'ashtottari dasha module missing: {e}')
    try:
        raw = ashtottari.get_ashtottari_dhasa_bhukthi(dob, bt_tuple, place, include_antardhasa=bool(include_antardhasa))
    except Exception as e:
        raise HTTPException(500, f'ashtottari computation failed: {e}')
    periods: list[models.CharaDhasaItem] = []
    count = 0
    # raw entries format when include_antardhasa=True: (dhasa_rasi_index, bhukti_rasi_index, start, duration_years_fraction)
    # else: (dhasa_rasi_index, start, duration_years)
    for item in raw:
        if count >= limit:
            break
        try:
            if include_antardhasa and isinstance(item,(list,tuple)) and len(item) >= 4:
                d_r, b_r, start, dur = item[0], item[1], item[2], item[3]
                periods.append(models.CharaDhasaItem(dhasaRasi=str(d_r), bhuktiRasi=str(b_r), start=str(start), durationYears=float(dur)))
            elif (not include_antardhasa) and isinstance(item,(list,tuple)) and len(item) >= 3:
                d_r, start, dur = item[0], item[1], item[2]
                periods.append(models.CharaDhasaItem(dhasaRasi=str(d_r), start=str(start), durationYears=float(dur) if isinstance(dur,(int,float)) else None))
            else:
                # Fallback best-effort parse
                periods.append(models.CharaDhasaItem(dhasaRasi=str(item[0] if isinstance(item,(list,tuple)) else item), start=str(item[2] if isinstance(item,(list,tuple)) and len(item)>2 else '')))  # type: ignore
            count += 1
        except Exception:
            continue
    # Map indices to sign names
    sign_names = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    def sn(v: str) -> str:
        try:
            i = int(v)
            if 0 <= i < 12:
                return sign_names[i]
        except Exception:
            return v
        return v
    for p in periods:
        p.dhasaRasi = sn(p.dhasaRasi)
        if p.bhuktiRasi:
            p.bhuktiRasi = sn(p.bhuktiRasi)
    return models.CharaDhasaResponse(requestId=request_id, periods=periods, total=len(raw), returned=len(periods), includeAntardhasa=bool(include_antardhasa), method=1)

@app.get('/api/dhasa/graha/{system}')
def dhasa_graha(system: str, request_id: str, limit: int = 120, include_antardhasa: bool = True):
    stored = _get_stored_or_404(request_id)
    raw = _invoke_graha_dasha(system, stored, include_antardhasa=include_antardhasa)
    raw_list = raw if isinstance(raw, list) else list(raw)
    periods = _format_graha_periods(raw_list, include_antardhasa, limit)
    return {
        'requestId': request_id,
        'system': system,
        'periods': periods,
        'returned': len(periods),
        'total': len(raw_list),
        'includeAntardhasa': include_antardhasa,
    }

@app.get('/api/dhasa/sthira')
def dhasa_sthira(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('sthira', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/narayana')
def dhasa_narayana(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('narayana', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/drig')
def dhasa_drig(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('drig', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/yogardha')
def dhasa_yogardha(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('yogardha', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/paryaaya')
def dhasa_paryaaya(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('paryaaya', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/brahma')
def dhasa_brahma(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('brahma', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/mandooka')
def dhasa_mandooka(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('mandooka', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/sudasa')
def dhasa_sudasa(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('sudasa', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/kalachakra')
def dhasa_kalachakra(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('kalachakra', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/navamsa')
def dhasa_navamsa(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('navamsa', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/trikona')
def dhasa_trikona(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('trikona', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/chakra')
def dhasa_chakra(request_id: str, limit: int = 120, include_antardhasa: bool = False):
    return _handle_rasi_dasha('chakra', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/kendraadhi_rasi')
def dhasa_kendraadhi_rasi(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('kendraadhi_rasi', request_id, limit, include_antardhasa)

@app.get('/api/dhasa/rasi/shoola')
def dhasa_shoola(request_id: str, limit: int = 120, include_antardhasa: bool = True):
    return _handle_rasi_dasha('shoola', request_id, limit, include_antardhasa)

@app.get('/api/tajaka/annual')
def tajaka_annual(request_id: str, year: int):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    year_offset = _normalize_tajaka_year(year, stored)
    try:
        chart, start_info = _tajaka.annual_chart(jd, place, divisional_chart_factor=1, years=year_offset)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute Tajaka annual chart: {exc}') from exc
    planets, asc_sign, asc_long = _serialize_tajaka_chart(chart)
    muntha_info = None
    try:
        if asc_sign is not None:
            muntha_sign = _tajaka.muntha_house(int(asc_sign), year_offset)
            muntha_info = {
                'sign': _sign_label(muntha_sign),
                'house': _relative_house(muntha_sign, asc_sign)
            }
    except Exception:
        muntha_info = None
    try:
        lord_idx = _tajaka.lord_of_the_year(jd, place, year_offset)
        lord_name = _planet_label(lord_idx)
    except Exception:
        lord_name = None
    try:
        jd_year = _drik.next_solar_date(jd, place, years=year_offset)
    except Exception:
        jd_year = jd
    start_str = None
    if start_info and len(start_info) >= 2:
        date_tuple = start_info[0]
        time_str = start_info[1]
        date_formatted = f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
        start_str = _format_patyayini_start(date_formatted, time_str)
    ascendant_info = None
    if asc_sign is not None:
        ascendant_info = {
            'sign': _sign_label(asc_sign),
            'longitudeDMS': _format_degree(asc_long)
        }
    return {
        'requestId': request_id,
        'year': year,
        'yearOffset': year_offset,
        'planets': planets,
        'ascendant': ascendant_info,
        'muntha': muntha_info,
        'lordOfYear': lord_name,
        'chartStart': start_str,
        'panchavargiya_bala': _panchavargiya_summary(jd_year, place),
    }

@app.get('/api/tajaka/yogas')
def tajaka_yogas(request_id: str, year: int):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    year_offset = _normalize_tajaka_year(year, stored)
    try:
        chart, _ = _tajaka.annual_chart(jd, place, divisional_chart_factor=1, years=year_offset)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute Tajaka yogas: {exc}') from exc
    yogas: list[dict[str, Any]] = []
    p_to_h = _jut.get_planet_house_dictionary_from_planet_positions(chart)
    if _tajaka_yoga.ishkavala_yoga(p_to_h):
        yogas.append(_yoga_entry('Ishkavala', [], 'Planets occupy Kendras/Panapharas'))
    if _tajaka_yoga.induvara_yoga(p_to_h):
        yogas.append(_yoga_entry('Induvara', [], 'Planets occupy Apoklimas'))
    try:
        ithasala_pairs = _tajaka_yoga.get_ithasala_yoga_planet_pairs(chart)
        for p1, p2, detail in ithasala_pairs:
            yogas.append(_yoga_entry('Ithasala', [p1, p2], str(detail)))
    except Exception:
        pass
    try:
        eesarpha_pairs = _tajaka_yoga.get_eesarpha_yoga_planet_pairs(chart)
        for p1, p2 in eesarpha_pairs:
            yogas.append(_yoga_entry('Eesarpha', [p1, p2]))
    except Exception:
        pass
    try:
        nakta = _tajaka_yoga.get_nakta_yoga_planet_triples(chart)
        for triple in nakta or []:
            yogas.append(_yoga_entry('Nakta', list(triple)))
    except Exception:
        pass
    try:
        yamaya = _tajaka_yoga.get_yamaya_yoga_planet_triples(chart)
        for triple in yamaya or []:
            yogas.append(_yoga_entry('Yamaya', list(triple)))
    except Exception:
        pass
    try:
        manahoo = _tajaka_yoga.get_manahoo_yoga_planet_pairs(chart)
        for p1, p2, house in manahoo or []:
            yogas.append(_yoga_entry('Manahoo', [p1, p2], f'Mars/Saturn house {_sign_label(house)}'))
    except Exception:
        pass
    try:
        ky = _tajaka_yoga.get_kamboola_yoga_planet_pairs(chart)
        if ky and ky[0]:
            detail = ', '.join([f"{_planet_label(x)}-{_planet_label(y)}" for x, y in ky[1]])
            planets = [p for pair in ky[1] for p in pair]
            yogas.append(_yoga_entry('Kamboola', planets, detail or 'Kamboola'))
    except Exception:
        pass
    try:
        radda = _tajaka_yoga.get_radda_yoga_planet_pairs(chart)
        for p1, p2 in radda or []:
            yogas.append(_yoga_entry('Radda', [p1, p2]))
    except Exception:
        pass
    try:
        jd_year = _drik.next_solar_date(jd, place, years=year_offset)
        dky = _tajaka_yoga.get_duhphali_kutta_yoga_planet_pairs(jd_year, place)
        for p1, p2 in dky or []:
            yogas.append(_yoga_entry('Duhphali Kutta', [p1, p2]))
    except Exception:
        pass
    return {'requestId': request_id, 'yogas': yogas}

@app.get('/api/dhasa/annual/mudda')
def annual_mudda_dhasa(request_id: str, year: int, include_antardhasa: bool = True):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    year_offset = _normalize_tajaka_year(year, stored)
    try:
        dashas = _mudda.varsha_vimsottari_mahadasa(jd, place, year_offset)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute Mudda dasha: {exc}') from exc
    periods: list[dict[str, Any]] = []
    for d_lord, start_jd, duration in dashas:
        if include_antardhasa:
            try:
                bhuktis = _mudda.varsha_vimsottari_bhukti(d_lord, start_jd)
            except Exception:
                bhuktis = []
            for b_lord, b_start, b_duration in bhuktis:
                entry = {
                    'dhasaLord': _planet_label(d_lord),
                    'antardashaLord': _planet_label(b_lord),
                    'start': _format_jd_datetime(b_start),
                    'end': _format_jd_datetime(b_start + b_duration),
                    'durationDays': round(float(b_duration), 2),
                    'durationYears': round(float(b_duration) / 365.25, 3),
                }
                periods.append(entry)
        else:
            entry = {
                'dhasaLord': _planet_label(d_lord),
                'start': _format_jd_datetime(start_jd),
                'end': _format_jd_datetime(start_jd + duration),
                'durationDays': round(float(duration), 2),
                'durationYears': round(float(duration) / 365.25, 3),
            }
            periods.append(entry)
    return {
        'requestId': request_id,
        'yearOffset': year_offset,
        'system': 'mudda',
        'includeAntardhasa': include_antardhasa,
        'periods': periods,
    }

@app.get('/api/dhasa/annual/patyayini')
def annual_patyayini_dhasa(request_id: str, year: int, include_antardhasa: bool = True):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    year_offset = _normalize_tajaka_year(year, stored)
    try:
        jd_year = _drik.next_solar_date(jd, place, years=year_offset)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute annual date: {exc}') from exc
    try:
        dhasas = _patyayini.patyayini_dhasa(jd_year, place)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute Patyayini dasha: {exc}') from exc
    periods: list[dict[str, Any]] = []
    for d_lord, bhuktis, dd in dhasas:
        if include_antardhasa:
            parsed: list[tuple[Any, datetime | None, str]] = []
            for b_lord, start_str in bhuktis:
                parts = start_str.split(' ', 1)
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else '0'
                iso = _format_patyayini_start(date_part, time_part)
                try:
                    dt = datetime.fromisoformat(iso)
                except Exception:
                    dt = None
                parsed.append((b_lord, dt, iso))
            for idx, (b_lord, dt, iso) in enumerate(parsed):
                if idx + 1 < len(parsed) and parsed[idx + 1][1] is not None and dt is not None:
                    end_iso = parsed[idx + 1][1].isoformat(sep=' ')
                else:
                    end_iso = None
                entry = {
                    'dhasaLord': _planet_label(d_lord),
                    'antardashaLord': _planet_label(b_lord),
                    'start': iso,
                    'end': end_iso,
                }
                periods.append(entry)
        else:
            entry = {
                'dhasaLord': _planet_label(d_lord),
                'start': _format_jd_datetime(jd_year),
                'durationDays': round(float(dd), 2),
            }
            periods.append(entry)
    return {
        'requestId': request_id,
        'yearOffset': year_offset,
        'system': 'patyayini',
        'includeAntardhasa': include_antardhasa,
        'periods': periods,
    }

def chart_analysis(request_id: str, divisional_chart_factor: int = 1):
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    jd = getattr(h,'julian_day',None)
    place = getattr(h,'Place',None)
    
    # Get planet positions for the chart
    planet_positions = _charts.divisional_chart(jd, place, divisional_chart_factor=divisional_chart_factor)
    h_to_p = _jut.get_house_planet_list_from_planet_positions(planet_positions)
    
    # Graha Drishti
    arp, ahp, app = _house.graha_drishti_from_chart(h_to_p)
    
    # Rasi Drishti
    rarp, rahp, rapp = _house.raasi_drishti_from_chart(h_to_p)
    
    return {
        'requestId': request_id,
        'grahaDrishti': {
            'rasis': _to_native(arp),
            'houses': _to_native(ahp),
            'planets': _to_native(app)
        },
        'rasiDrishti': {
            'rasis': _to_native(rarp),
            'houses': _to_native(rahp),
            'planets': _to_native(rapp)
        }
    }

def chart_strength(request_id: str):
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    jd = getattr(h,'julian_day',None)
    place = getattr(h,'Place',None)
    
    # Shadbala
    sb = _strength.shad_bala(jd, place)
    
    # Bhava Bala
    bb = _strength.bhava_bala(jd, place)
    
    return {
        'requestId': request_id,
        'shadbala': _to_native(sb),
        'bhavabala': _to_native(bb)
    }

def chart_yoga(request_id: str, language: str = 'en'):
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    jd = getattr(h,'julian_day',None)
    place = getattr(h,'Place',None)
    
    yogas, count, total = _yoga.get_yoga_details(jd, place, divisional_chart_factor=1, language=language)
    
    return {
        'requestId': request_id,
        'yogas': _to_native(yogas),
        'count': count,
        'totalChecked': total
    }

@app.get('/api/chart/raja_yoga')
def chart_raja_yoga(request_id: str, divisional_chart_factor: int = 1, language: str = 'en'):
    """
    Get Raja Yoga details.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    jd = getattr(h,'julian_day',None)
    place = getattr(h,'Place',None)
    
    raja_yogas, count, total = _raja_yoga.get_raja_yoga_details(jd, place, divisional_chart_factor=divisional_chart_factor, language=language)
    
    return {
        'requestId': request_id,
        'rajaYogas': _to_native(raja_yogas),
        'count': count,
        'totalChecked': total
    }

@app.get('/api/aspects')
def aspects(request_id: str):
    """
    Get Aspects (Graha Drishti, Rasi Drishti).
    """
    return chart_analysis(request_id, divisional_chart_factor=1)

@app.get('/api/strength')
def strength(request_id: str):
    """
    Get Strength details.
    """
    return chart_strength(request_id)

@app.get('/api/yogas')
def yogas(request_id: str, mode: str = 'full', language: str = 'en'):
    """
    Get Yogas.
    """
    # Combine yoga and raja_yoga
    y = chart_yoga(request_id, language=language)
    ry = chart_raja_yoga(request_id, language=language)
    return {
        'requestId': request_id,
        'yogas': y.get('yogas', []),
        'rajaYogas': ry.get('rajaYogas', [])
    }

@app.get('/api/summary')
def summary(request_id: str):
    """
    Get Horoscope Summary.
    """
    # Return a composite object
    stored = _get_stored_or_404(request_id)
    return {
        'requestId': request_id,
        'meta': stored.response.meta,
        'rasi': stored.response.rasiChart,
        # Add more summary info if needed
    }

def _ensure_horoscope_context(stored: models.StoredHoroscope):
    h = stored.internalHoroscope
    if not h:
        raise HTTPException(500, 'Horoscope state is unavailable')
    jd = getattr(h, 'julian_day', None)
    place = getattr(h, 'Place', None)
    if jd is None or place is None:
        raise HTTPException(500, 'Stored horoscope missing Julian day or place information')
    return h, jd, place

@app.get('/api/analyze/shadbala')
def analyze_shadbala(request_id: str):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    try:
        sb = _strength.shad_bala(jd, place)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute shadbala: {exc}') from exc
    labels = ['sthana','kaala','dig','cheshta','naisargika','drik']
    components: dict[str, Any] = {}
    for idx, label in enumerate(labels):
        if idx < len(sb):
            components[label] = _to_native(sb[idx])
    payload: dict[str, Any] = {
        'requestId': request_id,
        'components': components,
        'total': _to_native(sb[6]) if len(sb) > 6 else None,
        'rupas': _to_native(sb[7]) if len(sb) > 7 else None,
        'percent': _to_native(sb[8]) if len(sb) > 8 else None,
    }
    try:
        ishta_vals = _strength._ishta_phala(jd, place)  # type: ignore[attr-defined]
        if isinstance(ishta_vals, (list, tuple)):
            ishta = [_to_native(v) for v in ishta_vals]
            kashta = [_to_native(max(0.0, 60.0 - float(v))) for v in ishta_vals]
            payload['ishta_kashta'] = {'ishta': ishta, 'kashta': kashta}
    except Exception:
        pass
    return payload

@app.get('/api/analyze/bhavabala')
def analyze_bhavabala(request_id: str):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    try:
        bb = _strength.bhava_bala(jd, place)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute bhavabala: {exc}') from exc
    return {
        'requestId': request_id,
        'total': _to_native(bb[0]) if len(bb) > 0 else None,
        'rupas': _to_native(bb[1]) if len(bb) > 1 else None,
        'strength': _to_native(bb[2]) if len(bb) > 2 else None,
    }

@app.get('/api/analyze/ashtakavarga')
def analyze_ashtakavarga(request_id: str):
    stored = _get_stored_or_404(request_id)
    _, jd, place = _ensure_horoscope_context(stored)
    try:
        planet_positions = _charts.rasi_chart(jd, place)
        house_chart = _jut.get_house_planet_list_from_planet_positions(planet_positions)
        bav, sav, pav = _ashtakavarga.get_ashtaka_varga(house_chart)
        raasi_pindas, graha_pindas, sodhya = _ashtakavarga.sodhaya_pindas(bav, house_chart)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute ashtakavarga: {exc}') from exc
    bav_map: dict[str, Any] = {}
    for idx, row in enumerate(bav):
        if idx < len(_PLANET_NAMES):
            name = _PLANET_NAMES[idx]
        elif idx == len(_PLANET_NAMES):
            name = 'Ascendant'
        else:
            name = f'P{idx}'
        bav_map[name] = _to_native(row)
    return {
        'requestId': request_id,
        'bav': bav_map,
        'sav': _to_native(sav),
        'sodhita': _to_native(sodhya),
        'raasiPindas': _to_native(raasi_pindas),
        'grahaPindas': _to_native(graha_pindas),
        'prastara': _to_native(pav),
    }

@app.get('/api/analyze/vaiseshikamsa')
def analyze_vaiseshikamsa(request_id: str):
    stored = _get_stored_or_404(request_id)
    h, jd, place = _ensure_horoscope_context(stored)
    ayanamsa = getattr(h, 'ayanamsa_mode', getattr(_jconst, '_DEFAULT_AYANAMSA_MODE', None))
    try:
        data = _charts.vaiseshikamsa_shodhasavarga_of_planets(jd, place, ayanamsa_mode=ayanamsa)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute vaiseshikamsa: {exc}') from exc
    items: dict[str, Any] = {}
    for idx, info in data.items():
        name = _planet_label(idx)
        count = info[0] if len(info) > 0 else 0
        chart_list = info[1] if len(info) > 1 else ''
        score = info[2] if len(info) > 2 else None
        detail = chart_list or ''
        items[name] = {
            'count': count,
            'charts': chart_list.split('/') if chart_list else [],
            'score': score,
            'yoga': detail,
        }
    return {'requestId': request_id, 'items': items}

def _yogi_description(value: Any) -> str:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return _format_sphuta_value(value)
    abs_long = float(value[0]) * 30 + float(value[1])
    try:
        nak_idx, pada = _drik.nakshatra_pada(abs_long)
    except Exception:
        nak_idx, pada = (None, None)
    nak_name = ''
    if nak_idx and 0 < nak_idx <= len(_NAKSHATRA_NAMES):
        nak_name = _NAKSHATRA_NAMES[nak_idx - 1]
    yogi_planet = None
    try:
        for planet_idx, group in getattr(_jconst, 'nakshathra_lords', {}).items():
            if nak_idx is not None and (nak_idx - 1) in group:
                yogi_planet = _planet_label(planet_idx)
                break
    except Exception:
        yogi_planet = None
    base = _format_sphuta_value(value)
    details = []
    if nak_name:
        details.append(f'{nak_name} pada {pada}')
    if yogi_planet:
        details.append(f'lord {yogi_planet}')
    if details:
        return f"{base} ({', '.join(details)})"
    return base

@app.get('/api/analyze/sphuta')
def analyze_sphuta(request_id: str):
    stored = _get_stored_or_404(request_id)
    h, _, _ = _ensure_horoscope_context(stored)
    dob, tob, place = _get_birth_details(stored)
    ayanamsa = getattr(h, 'ayanamsa_mode', getattr(_jconst, '_DEFAULT_AYANAMSA_MODE', None))
    payload: dict[str, Any] = {}
    try:
        payload['tri_sphuta'] = _format_sphuta_value(_sphuta.tri_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['chatur_sphuta'] = _format_sphuta_value(_sphuta.chatur_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['pancha_sphuta'] = _format_sphuta_value(_sphuta.pancha_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['prana_sphuta'] = _format_sphuta_value(_sphuta.prana_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['deha_sphuta'] = _format_sphuta_value(_sphuta.deha_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['mrityu_sphuta'] = _format_sphuta_value(_sphuta.mrityu_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['sookshma_tri_sphuta'] = _format_sphuta_value(_sphuta.sookshma_tri_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['beeja_sphuta'] = _format_sphuta_value(_sphuta.beeja_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['kshetra_sphuta'] = _format_sphuta_value(_sphuta.kshetra_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['tithi_sphuta'] = _format_sphuta_value(_sphuta.tithi_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['yoga_sphuta'] = _format_sphuta_value(_sphuta.yoga_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['yogi_sphuta'] = _yogi_description(_sphuta.yogi_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['avayogi_sphuta'] = _yogi_description(_sphuta.avayogi_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
        payload['rahu_tithi_sphuta'] = _format_sphuta_value(_sphuta.rahu_tithi_sphuta(dob, tob, place, ayanamsa_mode=ayanamsa))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f'Failed to compute sphuta points: {exc}') from exc
    payload['requestId'] = request_id
    return payload

@app.get('/api/dhasa/sudharsana_chakra')
async def dhasa_sudharsana_chakra(request_id: str, divisional_chart_factor: int = 1):
    """Return Sudharsana Chakra (Dhasa chart) for a request.
    This is a lightweight view suitable for direct display in UIs.
    """
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    try:
        jd = getattr(h, 'julian_day', None)
        place = getattr(h, 'Place', None)
        ayanamsa_mode = getattr(h, 'ayanamsa_mode', None)
        if jd is None or place is None:
            raise ValueError('Missing JD or Place')
        # Compute using jhora functions
        from jhora.panchanga import drik
        try:
            result = drik.sudharsana_chakra(jd, place, divisional_chart_factor=divisional_chart_factor, ayanamsa_mode=ayanamsa_mode)  # type: ignore
            return { 'requestId': request_id, 'sudharsanaChakra': _to_native(result) }
        except Exception as e:
            raise HTTPException(500, f'Error computing Sudharsana Chakra: {e}')
    except Exception as e:
        raise HTTPException(500, f'Error: {e}')
@app.get('/api/panchanga', response_model=models.PanchangaResponse)
async def get_panchanga(request_id: str):
    stored = _get_stored_or_404(request_id)
    return models.PanchangaResponse(requestId=request_id, calendar=stored.internalHoroscope.calendar_info)  # type: ignore[attr-defined]

@app.get('/api/panchanga/transit', response_model=models.PanchangaResponse)
async def get_panchanga_transit(
    request_id: str,
    dateTime: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    tzOffset: float | None = None,
    ayanamsaMode: str | None = None,
    calcType: str | None = None,
):
    """Return Panchanga (calendar info) for an arbitrary date/time/place (transit-style).

    Defaults to the stored request's place and current local time if parameters are omitted.
    """
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    try:
        from jhora.panchanga import drik as _drik
        from jhora import utils as _u
        from jhora import const as _c
    except Exception as e:  # noqa
        raise HTTPException(500, f'panchanga prerequisites unavailable: {e}')

    # Resolve place
    try:
        if latitude is not None and longitude is not None:
            tz_hours = float(tzOffset) if tzOffset is not None else float(getattr(h, 'timezone_offset', 0.0))
            place = _drik.Place('TransitPlace', float(latitude), float(longitude), tz_hours)
        else:
            place = getattr(h, 'Place', None)
            if place is None:
                raise ValueError('stored request missing Place; provide latitude/longitude/tzOffset')
    except Exception as e:
        raise HTTPException(400, f'invalid place parameters: {e}')

    # Resolve datetime (treat provided dateTime as local to place tzOffset; if not provided, use current local time)
    try:
        tz_hours = getattr(place, 'timezone', None)
        if tz_hours is None:
            tz_hours = getattr(place, 'timezone_offset', None)
        if tz_hours is None:
            tz_hours = getattr(h, 'timezone_offset', 0.0)
        tz_hours = float(tz_hours or 0.0)
        tzinfo = _tz(_td(hours=tz_hours))
        if dateTime:
            ds = dateTime.strip().replace('Z', '')
            ds = ds.replace(' ', 'T')
            try:
                dt_local = _dt.fromisoformat(ds)
            except Exception:
                try:
                    ds2 = ds.split('.')[0]
                    dt_local = _dt.fromisoformat(ds2)
                except Exception as e:
                    raise ValueError(f'bad dateTime format: {e}')
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=tzinfo)
            else:
                dt_local = dt_local.astimezone(tzinfo)
        else:
            dt_local = _dt.now(tzinfo)
        dob = _drik.Date(dt_local.year, dt_local.month, dt_local.day)
        tob = (dt_local.hour, dt_local.minute, dt_local.second)
        jd = _u.julian_day_number(dob, tob)
        julian_utc = _u.gregorian_to_jd(dob)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f'invalid date/time: {e}')

    # Set ayanamsa/calculation type
    try:
        aya = (ayanamsaMode or getattr(h, 'ayanamsa_mode', None) or getattr(_c, '_DEFAULT_AYANAMSA_MODE', 'TRUE_CITRA'))
        calc = (calcType or getattr(h, 'calculation_type', 'drik')).lower()
        if calc == 'ss':
            _drik.set_ayanamsa_mode('SURYASIDDHANTA')
        else:
            _drik.set_ayanamsa_mode(aya)
    except Exception:
        pass

    # Build a calendar_info dict in the same style as Horoscope.get_calendar_information
    try:
        cal_key_list = _u.resource_strings
        calendar_info: dict[str, object] = {
            cal_key_list['place_str']: getattr(place, 'name', getattr(place, 'place_name', '')) or 'TransitPlace',
            cal_key_list['latitude_str']: str(_u.to_dms(float(getattr(place,'latitude', getattr(place,'lat',0.0)) or 0.0), is_lat_long='lat', as_string=True)),
            cal_key_list['longitude_str']: str(_u.to_dms(float(getattr(place,'longitude', getattr(place,'long',0.0)) or 0.0), is_lat_long='long', as_string=True)),
            cal_key_list['timezone_offset_str']: "{0:.2f}".format(tz_hours),
            cal_key_list['report_date_str']: f"{dob.year}-{dob.month}-{dob.day}",
        }
        # Civil weekday label
        _civil_weekday = _dt(dob.year, dob.month, dob.day).weekday()  # Monday=0
        _panchanga_weekday = (_civil_weekday + 1) % 7
        try:
            _days = getattr(_u, 'DAYS_LIST', [])
            calendar_info[cal_key_list['vaaram_str']] = _days[_panchanga_weekday] if _days else str(_panchanga_weekday)
        except Exception:
            _days = getattr(_u, 'DAYS_LIST', [])
            vv = _drik.vaara(jd)
            calendar_info[cal_key_list['vaaram_str']] = _days[vv] if _days and 0<=vv<len(_days) else str(vv)
        # Calculation type label
        calendar_info[cal_key_list['calculation_type_str']] = cal_key_list['drik_panchang_str'] if calc!='ss' else cal_key_list['ss_panchang_str']

        # Month/year related
        jd_years = _drik.next_solar_date(jd, place, 1, 1, 1)
        maasam_no, adhik_maasa, nija_maasa = _drik.lunar_month(jd_years, place)
        nija_month_str = cal_key_list['nija_month_str'] if nija_maasa else ''
        _tithi = _drik.tithi(jd, place)
        _paksha = 1 if (_tithi[0] > 15) else 0
        tm, td = _drik.tamil_solar_month_and_date(dob, place)
        adhik_maasa_str = cal_key_list['adhika_maasa_str'] if adhik_maasa else ''
        _samvatsara = _drik.samvatsara(dob, place, zodiac=0)
        _years = getattr(_u,'YEAR_LIST', [])
        _months = getattr(_u,'MONTH_LIST', [])
        _year_name = _years[_samvatsara] if _years and 0 <= _samvatsara < len(_years) else str(_samvatsara)
        _month_name = _months[maasam_no-1] if _months and 1 <= maasam_no <= len(_months) else str(maasam_no)
        calendar_info[cal_key_list['lunar_year_month_str']] = _year_name+' / '+_month_name+' '+adhik_maasa_str+nija_month_str
        calendar_info[cal_key_list['tamil_month_str']] = (_months[tm] if _months and 0<=tm<len(_months) else str(tm)) +" "+cal_key_list['date_str']+' '+str(td)
        kali_year, vikrama_year, saka_year = _drik.elapsed_year(jd_years, maasam_no)
        calendar_info[cal_key_list['kali_year_str']] = kali_year
        calendar_info[cal_key_list['vikrama_year_str']] = vikrama_year
        calendar_info[cal_key_list['saka_year_str']] = saka_year

        # Rise/set
        sun_rise = _drik.sunrise(julian_utc, place)
        calendar_info[cal_key_list['sunrise_str']] = sun_rise[1]
        sun_set = _drik.sunset(julian_utc, place)
        calendar_info[cal_key_list['sunset_str']] = sun_set[1]
        moon_rise = _drik.moonrise(julian_utc, place)[1]
        calendar_info[cal_key_list['moonrise_str']] = moon_rise
        moon_set = _drik.moonset(julian_utc, place)[1]
        calendar_info[cal_key_list['moonset_str']] = moon_set

        # Fractions based on local birth_time
        birth_time_hrs = tob[0] + tob[1]/60.0 + tob[2]/3600.0
        frac_left_tithi = 100*_u.get_fraction(_tithi[1], _tithi[2], birth_time_hrs)
        _tithi_start_str = _u.to_dms(_tithi[1])
        _tithi_end_str = _u.to_dms(_tithi[2])
        _paksha_list = getattr(_u,'PAKSHA_LIST', [])
        _tithi_list = getattr(_u,'TITHI_LIST', [])
        _tithi_deities = getattr(_u,'TITHI_DEITIES', [])
        _paksha_name = _paksha_list[_paksha] if _paksha_list and 0<=_paksha<len(_paksha_list) else str(_paksha)
        _tithi_name = _tithi_list[_tithi[0]-1] if _tithi_list and 1<=_tithi[0]<=len(_tithi_list) else str(_tithi[0])
        _tithi_deity = _tithi_deities[_tithi[0]-1] if _tithi_deities and 1<=_tithi[0]<=len(_tithi_deities) else ''
        calendar_info[cal_key_list['tithi_str']] = (
            f"{_paksha_name} {_tithi_name} ({_tithi_deity}) "
            f"starts at {_tithi_start_str} ends at {_tithi_end_str} ("+"{0:.2f}".format(frac_left_tithi)+f"% {cal_key_list['balance_str']} )"
        )

        rasi = _drik.raasi(jd, place)
        frac_left_rasi = rasi[2]*100
        _rasi_list = getattr(_u,'RAASI_LIST', [])
        _rasi_name = _rasi_list[rasi[0]-1] if _rasi_list and 1<=rasi[0]<=len(_rasi_list) else str(rasi[0])
        calendar_info[cal_key_list['raasi_str']] = _rasi_name+' '+str(_u.to_dms(rasi[1]))+ ' ' + \
                        cal_key_list['ends_at_str'] +' ('+"{0:.2f}".format(frac_left_rasi)+'% ' + \
                        cal_key_list['balance_str']+' )'

        nak = _drik.nakshatra(jd, place)
        frac_left_nak = 100*_u.get_fraction(nak[2], nak[3], birth_time_hrs)
        _nak_start_str = _u.to_dms(nak[2])
        _nak_end_str = _u.to_dms(nak[3])
        _nak_list = getattr(_u,'NAKSHATRA_LIST', [])
        _pshort = getattr(_u,'PLANET_SHORT_NAMES', [])
        _nak_name = _nak_list[nak[0]-1] if _nak_list and 1<=nak[0]<=len(_nak_list) else str(nak[0])
        _nak_lord_idx = _c.nakshatra_lords[nak[0]-1] if hasattr(_c,'nakshatra_lords') else None
        _nak_lord = (_pshort[_nak_lord_idx] if _pshort and _nak_lord_idx is not None and 0<=_nak_lord_idx<len(_pshort) else '')
        calendar_info[cal_key_list['nakshatra_str']] = (
            f"{_nak_name} ("+_nak_lord+") "
            f"{cal_key_list['paadham_str']}{nak[1]} starts at {_nak_start_str} ends at {_nak_end_str} ("+"{0:.2f}".format(frac_left_nak)+f"% {cal_key_list['balance_str']} )"
        )

        yogam = _drik.yogam(jd, place)
        _pshort = getattr(_u,'PLANET_SHORT_NAMES', [])
        l1 = _c.yogam_lords_and_avayogis[yogam[0]-1][0]
        l2 = _c.yogam_lords_and_avayogis[yogam[0]-1][1]
        yoga_lord = ' ('+ ( _pshort[l1] if _pshort and 0<=l1<len(_pshort) else str(l1) ) +'/'+ ( _pshort[l2] if _pshort and 0<=l2<len(_pshort) else str(l2) ) +') '
        _yoga_start_str = _u.to_dms(yogam[1])
        _yoga_end_str = _u.to_dms(yogam[2])
        _yoga_list = getattr(_u,'YOGAM_LIST', [])
        _yoga_name = _yoga_list[yogam[0]-1] if _yoga_list and 1<=yogam[0]<=len(_yoga_list) else str(yogam[0])
        calendar_info[cal_key_list['yogam_str']] = (
            f"{_yoga_name} {yoga_lord}starts at {_yoga_start_str} ends at {_yoga_end_str} ("+"{0:.2f}".format(yogam[3]*100)+f"% {cal_key_list['balance_str']} )"
        )

        karanam = _drik.karana(jd, place)
        frac_left_k = 100*_u.get_fraction(karanam[1], karanam[2], birth_time_hrs)
        karana_lord = ''
        _kar_start_str = _u.to_dms(karanam[1])
        _kar_end_str = _u.to_dms(karanam[2])
        _kar_list = getattr(_u,'KARANA_LIST', [])
        _kar_name = _kar_list[karanam[0]-1] if _kar_list and 1<=karanam[0]<=len(_kar_list) else str(karanam[0])
        calendar_info[cal_key_list['karanam_str']] = (
            f"{_kar_name} ({karana_lord}) starts at {_kar_start_str} ends at {_kar_end_str} ("+"{0:.2f}".format(frac_left_k)+f"% {cal_key_list['balance_str']} )"
        )

        abhijit = _drik.abhijit_muhurta(jd, place)
        calendar_info[cal_key_list['abhijit_str']] = str(abhijit[0]) + ' '+ cal_key_list['starts_at_str']+' '+ str(abhijit[1])+' '+cal_key_list['ends_at_str']
        _dhurmuhurtham = _drik.durmuhurtam(jd, place)
        calendar_info[cal_key_list['dhurmuhurtham_str']] = str(_dhurmuhurtham[0]) + ' '+ cal_key_list['starts_at_str']+' '+ str(_dhurmuhurtham[1])+' '+cal_key_list['ends_at_str']

        return models.PanchangaResponse(requestId=request_id, calendar=calendar_info)
    except Exception as e:
        raise HTTPException(500, f'panchanga transit failed: {e}')

@app.get('/api/transit', response_model=models.TransitResponse)
async def get_transit(
    request_id: str,
    dateTime: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    tzOffset: float | None = None,
    ayanamsaMode: str | None = None,
    houseSystem: str | None = None,
    sslike: bool = False,
):
    """Return transit (planet positions) for a given request's place by default, or for an optional
    date/time and place provided via query params.

    Query params:
      - dateTime: ISO local datetime (e.g. 2025-11-12T10:00:00). If omitted, uses "now" at place.
      - latitude, longitude, tzOffset: optional place override. Defaults to stored request's place.
      - ayanamsaMode, houseSystem: optional overrides; fall back to stored settings.
    """
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    stored = _get_stored_or_404(request_id)
    h = stored.internalHoroscope
    # Resolve place
    try:
        from jhora.panchanga import drik as _drik
        from jhora.horoscope.chart import charts as _charts
        from jhora import utils as _u
    except Exception as e:  # noqa
        raise HTTPException(500, f'transit prerequisites unavailable: {e}')

    try:
        if latitude is not None and longitude is not None:
            tz_hours = float(tzOffset) if tzOffset is not None else float(getattr(h, 'timezone_offset', 0.0))
            place = _drik.Place('TransitPlace', float(latitude), float(longitude), tz_hours)
        else:
            place = getattr(h, 'Place', None)
            if place is None:
                raise ValueError('stored request missing Place; provide latitude/longitude/tzOffset')
    except Exception as e:
        raise HTTPException(400, f'invalid place parameters: {e}')

    # Resolve datetime (treat provided dateTime as local to place tzOffset; if not provided, use current local time)
    try:
        tz_hours = getattr(place, 'timezone', None)
        if tz_hours is None:
            tz_hours = getattr(place, 'timezone_offset', None)
        if tz_hours is None:
            tz_hours = getattr(h, 'timezone_offset', 0.0)
        tz_hours = float(tz_hours or 0.0)
        tzinfo = _tz(_td(hours=tz_hours))
        if dateTime:
            # Accept plain local ISO (YYYY-MM-DDTHH:MM:SS). If offset provided, ignore and treat as local.
            ds = dateTime.strip().replace('Z', '')
            # If string contains a space instead of 'T', allow it
            ds = ds.replace(' ', 'T')
            try:
                dt_local = _dt.fromisoformat(ds)
            except Exception:
                # Try trim subseconds
                try:
                    ds2 = ds.split('.')[0]
                    dt_local = _dt.fromisoformat(ds2)
                except Exception as e:
                    raise ValueError(f'bad dateTime format: {e}')
            # Ensure timezone is local tz of place
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=tzinfo)
            else:
                # Convert to local tz for JD computation
                dt_local = dt_local.astimezone(tzinfo)
        else:
            dt_local = _dt.now(tzinfo)
        dob = _drik.Date(dt_local.year, dt_local.month, dt_local.day)
        tob = (dt_local.hour, dt_local.minute, dt_local.second)
        jd = _u.julian_day_number(dob, tob)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f'invalid date/time: {e}')

    # Compute positions using selected ayanamsa and derive houses
    try:
        aya = (ayanamsaMode or getattr(h, 'ayanamsa_mode', None) or 'TRUE_CITRA')
        hs = houseSystem
        # rasi positions (asc + 9 planets)
        pp = _charts.rasi_chart(jd, place, ayanamsa_mode=aya)
        # house map (relative 1..12)
        house_map = _charts.bhava_houses(jd, place, ayanamsa_mode=aya, bhava_starts_with_ascendant=False)
        # Build TransitPlanet list (skip ascendant symbol at index 0)
        items: list[models.TransitPlanet] = []
        rasi_names = getattr(_u, 'RAASI_LIST', [])
        planet_names = getattr(_u, 'PLANET_NAMES', [])
        for entry in pp[1:]:
            try:
                p_idx, (sign_idx, sign_long) = entry
                name = planet_names[p_idx] if 0 <= int(p_idx) < len(planet_names) else str(p_idx)
                sign_str = rasi_names[sign_idx] if 0 <= int(sign_idx) < len(rasi_names) else str(sign_idx)
                dms_raw = _u.to_dms(sign_long, is_lat_long='plong')
                dms = dms_raw if isinstance(dms_raw, str) else str(dms_raw)
                house_rel = int(house_map.get(p_idx, 0)) if isinstance(house_map, dict) else 0
                items.append(models.TransitPlanet(name=name, longitudeDMS=dms, sign=sign_str, house=house_rel or 0))
            except Exception:
                continue
        resp = models.TransitResponse(requestId=request_id, date=dt_local.astimezone(_tz.utc).isoformat(), planets=items)
        if not sslike:
            return resp
        # Build sslike-style enrichment (glyphs, absoluteLongitude, nakshatra/pada, dignity) into an alternate structure
        try:
            from jhora import const as _c2
            enriched: list[dict] = []
            for entry in pp[1:]:
                try:
                    p_idx, (sign_idx, sign_long) = entry
                    name_raw = planet_names[p_idx] if 0 <= int(p_idx) < len(planet_names) else str(p_idx)
                    # glyph planet name (reuse mapping from sslike endpoint)
                    glyph_map = {
                        'Sun':'Sun\u2609','Moon':'Moon\u263E','Mars':'Mars\u2642','Mercury':'Mercury\u263F','Jupiter':'Jupiter\u2643','Venus':'Venus\u2640','Saturn':'Saturn\u2644','Rahu':'Raagu\u260A','Ketu':'Kethu\u260B'
                    }
                    name = glyph_map.get(name_raw, name_raw)
                    sign_name = rasi_names[sign_idx] if 0 <= int(sign_idx) < len(rasi_names) else str(sign_idx)
                    abs_long = sign_idx*30 + sign_long
                    # Nakshatra
                    nak_index_float = abs_long / (13 + 1/3)
                    nak_index = int(nak_index_float)
                    nak_list = getattr(_u,'NAKSHATRA_LIST', [])
                    nak_name = nak_list[nak_index] if 0 <= nak_index < len(nak_list) else None
                    nak_pada = int((nak_index_float - nak_index) * 4) + 1 if nak_name else None
                    # Dignity
                    dignity = None; isEx=None; isDe=None; isOwn=None; isMT=None
                    try:
                        hs_row = _c2.house_strengths_of_planets[p_idx] if 0 <= p_idx < len(_c2.house_strengths_of_planets) else None
                        if hs_row and 0 <= sign_idx < len(hs_row):
                            code = hs_row[sign_idx]
                            if code == _c2._EXALTED_UCCHAM: dignity='Exalted'; isEx=True
                            elif code == _c2._DEFIBILATED_NEECHAM: dignity='Debilitated'; isDe=True
                            elif code == _c2._OWNER_RULER: dignity='Own'; isOwn=True
                            else: dignity='Neutral'
                        mt_sign = _c2.moola_trikona_of_planets[p_idx] if 0 <= p_idx < len(_c2.moola_trikona_of_planets) else None
                        if mt_sign is not None and sign_idx == mt_sign:
                            isMT = True
                            if dignity in (None,'Neutral'): dignity='Moolatrikona'
                    except Exception:
                        pass
                    # Retrograde: derive from charts.rasi_chart sign_long? Use existing house_map mapping fallback to stored natal retro flags if same name
                    retro_flag = False
                    try:
                        retro_flag = bool(getattr(resp.planets[p_idx],'retrograde', False))
                    except Exception:
                        retro_flag = False
                    enriched.append({
                        'name': name,
                        'sign': sign_name,
                        'longitudeDMS': _u.to_dms(sign_long) if isinstance(_u.to_dms(sign_long), str) else str(_u.to_dms(sign_long)),
                        'absoluteLongitude': abs_long,
                        'nakshatra': nak_name,
                        'nakshatraPada': nak_pada,
                        'retrograde': retro_flag,
                        'dignity': dignity,
                        'isExalted': isEx,
                        'isDebilitated': isDe,
                        'isOwnSign': isOwn,
                        'isMoolatrikona': isMT,
                        'house': int(house_map.get(p_idx,0)) if isinstance(house_map,dict) else None
                    })
                except Exception:
                    continue
            return { 'requestId': request_id, 'date': resp.date, 'planets': enriched, 'mode': 'transit-sslike' }
        except Exception:
            return resp
    except HTTPException:
        raise
    except Exception as e:
        # Fall back to stored snapshot if computation fails, to stay non-breaking
        try:
            planets_src = getattr(stored.response, 'rasiChart', None)
            items: list[models.TransitPlanet] = []
            if planets_src and getattr(planets_src, 'planets', None):
                for p in planets_src.planets[:20]:
                    try:
                        items.append(models.TransitPlanet(
                            name=str(getattr(p,'name','')),
                            longitudeDMS=str(getattr(p,'longitudeDMS', getattr(p,'rawLongitudeDMS',''))),
                            sign=str(getattr(p,'sign','')),
                            house=int(getattr(p,'house', getattr(p,'houseAbs',0)) or 0)
                        ))
                    except Exception:
                        continue
            return models.TransitResponse(requestId=request_id, date=_dt.now(_tz.utc).isoformat(), planets=items)
        except Exception:
            raise HTTPException(500, f'transit failed: {e}')
