from __future__ import annotations
from typing import List, Dict, Any, Tuple, Mapping
from datetime import datetime, UTC
import sys, os
import csv
import asyncio
import threading
# import fcntl
from types import MappingProxyType
# Ensure 'src' directory is on path when running via direct uvicorn without start script
try:
    _BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _BASE_DIR not in sys.path:
        sys.path.insert(0, _BASE_DIR)
except Exception:
    pass
from jhora.horoscope.main import Horoscope
from jhora import utils, const
from . import models
import hashlib, json, os
from pathlib import Path

# Default divisional factors to compute when client does not provide `divisionalFactors`.
# Expanded to include common + extended Vargas so the UI can show all charts without manual selection.
COMMON_DIVISIONALS = [
    1,   # D1 (Rasi)
    2,   # Hora
    3,   # Drekkana
    4,   # Chaturthamsha
    5,   # Panchamsa
    6,   # Shashthamsha
    7,   # Saptamsa
    8,   # Ashtamsa
    9,   # Navamsa
    10,  # Dasamsa
    12,  # Dvadasamsa
    16,  # Shodasamsa or Chaturvimsamsa variants
    20,  # Vimsamsa
    24,
    27,
    30,
    36,
    40,
    45,
    60,
    72,
    144
]

# Simple cache {hash: (timestamp, data)}; could be replaced by cachetools TTLCache
_horo_cache: Dict[str, models.HoroscopeResponse] = {}
_horo_cache_lock = threading.RLock()
_store: Dict[str, models.StoredHoroscope] = {}
_store_lock = threading.RLock()
# Persist only the original request payloads (serializable) so we can recompute lazily after a restart.
_persisted_requests: Dict[str, Dict[str, Any]] = {}
_persist_lock = threading.RLock()
_language_lock = threading.RLock()
PERSIST_PATH = Path(__file__).parent / 'horo_requests.json'
WORLD_CITY_DATA_PATH = Path(__file__).resolve().parent.parent / 'jhora' / 'data' / 'world_cities_with_tz.csv'

WorldCityEntry = tuple[float, float, float | None, str]
WorldCityLookup = Mapping[str, tuple[WorldCityEntry, ...]]

_WORLD_CITY_LOOKUP: WorldCityLookup | None = None
_WORLD_CITY_LOAD_ERROR: Exception | None = None
_WORLD_CITY_LOAD_LOCK = threading.Lock()

def _city_lookup_keys(city: str, country: str | None) -> List[str]:
    base = city.strip().lower()
    keys = [base]
    if country:
        country_norm = country.strip().lower()
        if country_norm:
            condensed = country_norm.replace(' ', '')
            primary = f"{base},{country_norm}"
            keys.append(primary)
            if condensed != country_norm:
                keys.append(f"{base},{condensed}")
            keys.append(f"{base},{country_norm.split(' ')[0]}")
            keys.append(f"{base},{country_norm[:2]}")
            abbrev = ''.join(part[0] for part in country_norm.split() if part)
            if abbrev:
                keys.append(f"{base},{abbrev}")
    return list(dict.fromkeys(keys))  # preserve order, remove dupes

def _build_world_city_index() -> Dict[str, tuple[WorldCityEntry, ...]]:
    if not WORLD_CITY_DATA_PATH.exists():
        raise FileNotFoundError(f"World city dataset missing at {WORLD_CITY_DATA_PATH}")

    lookup: Dict[str, List[WorldCityEntry]] = {}
    with WORLD_CITY_DATA_PATH.open('r', encoding='ISO-8859-1') as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 6:
                continue
            country, place, lat_s, lon_s, _tz_name, tz_hours_s = row[:6]
            try:
                lat_v = float(lat_s)
                lon_v = float(lon_s)
            except (TypeError, ValueError):
                continue
            tz_v: float | None
            try:
                tz_v = float(tz_hours_s) if tz_hours_s not in (None, '', 'NaN') else None
            except (TypeError, ValueError):
                tz_v = None
            place_clean = place.strip()
            city = place_clean.split(',')[0].strip().lower()
            country_norm = country.strip().lower()
            entry: WorldCityEntry = (lat_v, lon_v, tz_v, country_norm)
            for key in _city_lookup_keys(city, country_norm):
                lookup.setdefault(key, []).append(entry)
            # Include exact place string without trailing country variations
            if place_clean:
                lookup.setdefault(place_clean.strip().lower(), []).append(entry)

    return {k: tuple(v) for k, v in lookup.items()}


def _ensure_world_city_index() -> WorldCityLookup:
    global _WORLD_CITY_LOOKUP, _WORLD_CITY_LOAD_ERROR
    if _WORLD_CITY_LOOKUP is not None:
        return _WORLD_CITY_LOOKUP
    if _WORLD_CITY_LOAD_ERROR is not None:
        raise _WORLD_CITY_LOAD_ERROR
    with _WORLD_CITY_LOAD_LOCK:
        if _WORLD_CITY_LOOKUP is not None:
            return _WORLD_CITY_LOOKUP
        if _WORLD_CITY_LOAD_ERROR is not None:
            raise _WORLD_CITY_LOAD_ERROR
        try:
            _WORLD_CITY_LOOKUP = MappingProxyType(_build_world_city_index())
            _WORLD_CITY_LOAD_ERROR = None
        except Exception as exc:  # noqa: BLE001
            _WORLD_CITY_LOAD_ERROR = exc
            raise
    return _WORLD_CITY_LOOKUP


def _to_native(obj: Any):
    try:
        import numpy as _np  # type: ignore
    except Exception:
        _np = None  # type: ignore
    if obj is None or isinstance(obj, (str, bool, int, float)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if _np is not None and isinstance(obj, getattr(_np, 'generic')):  # type: ignore
        try:
            return obj.item()
        except Exception:
            return float(obj) if hasattr(obj, '__float__') else int(obj) if hasattr(obj, '__int__') else str(obj)
    if _np is not None and isinstance(obj, getattr(_np, 'ndarray')):  # type: ignore
        try:
            return [_to_native(x) for x in obj.tolist()]
        except Exception:
            return [_to_native(x) for x in list(obj)]
    if isinstance(obj, dict):
        return {str(k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_native(x) for x in obj]
    if hasattr(obj, 'model_dump'):
        try:
            return obj.model_dump()
        except Exception:
            pass
    return str(obj)


async def preload_world_city_index() -> None:
    await asyncio.to_thread(_ensure_world_city_index)


def world_city_index_ready() -> bool:
    return _WORLD_CITY_LOOKUP is not None and _WORLD_CITY_LOAD_ERROR is None


def world_city_index_error() -> Exception | None:
    return _WORLD_CITY_LOAD_ERROR


def _reset_world_city_index_cache_for_tests() -> None:
    global _WORLD_CITY_LOOKUP, _WORLD_CITY_LOAD_ERROR
    _WORLD_CITY_LOOKUP = None
    _WORLD_CITY_LOAD_ERROR = None

def _lookup_world_city(place: str, tz_offset: float | None) -> tuple[float, float, float | None] | None:
    _ensure_world_city_index()
    if not place or not _WORLD_CITY_LOOKUP:
        return None
    tokens = [t.strip() for t in place.split(',') if t.strip()]
    if not tokens:
        return None
    city = tokens[0]
    country = tokens[-1] if len(tokens) > 1 else None
    keys: List[str] = []
    if country:
        keys.extend(_city_lookup_keys(city, country))
    keys.append(city.strip().lower())
    candidates: List[tuple[float, float, float | None, str]] = []
    for key in keys:
        items = _WORLD_CITY_LOOKUP.get(key.lower())
        if items:
            candidates.extend(items)
    if not candidates:
        return None
    if tz_offset is not None:
        def _score(entry: tuple[float, float, float | None, str]) -> float:
            tz_val = entry[2]
            if tz_val is None:
                return float('inf')
            return abs(tz_val - tz_offset)
        candidates.sort(key=_score)
    chosen = candidates[0]
    return chosen[0], chosen[1], chosen[2]

def _load_persisted():
    global _persisted_requests
    if PERSIST_PATH.exists():
        try:
            data = json.loads(PERSIST_PATH.read_text(encoding='utf-8'))
            with _persist_lock:
                _persisted_requests = data
        except Exception:
            _persisted_requests = {}

def _json_default(obj: Any):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)!r} not serializable')

def _serialize_persisted_requests() -> str:
    with _persist_lock:
        return json.dumps(_persisted_requests, ensure_ascii=False, indent=2, default=_json_default)


def _write_persisted_snapshot(snapshot: str) -> None:
    """Write snapshot to disk atomically using a file lock."""
    lock_path = PERSIST_PATH.with_suffix(PERSIST_PATH.suffix + '.lock')
    tmp_path = PERSIST_PATH.with_suffix('.tmp')
    PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Windows-compatible simple write without fcntl
    with tmp_path.open('w', encoding='utf-8') as fh:
        fh.write(snapshot)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp_path, PERSIST_PATH)


async def persist_requests() -> None:
    snapshot = _serialize_persisted_requests()
    await asyncio.to_thread(_write_persisted_snapshot, snapshot)


def persist_requests_sync() -> None:
    asyncio.run(persist_requests())


def upsert_persisted_request(key: str, value: Dict[str, Any]) -> None:
    with _persist_lock:
        _persisted_requests[key] = value

_load_persisted()


def _request_hash(req: models.HoroscopeRequest) -> str:
    if req.birthDateTime is None or req.location is None:
        raise ValueError('birthDateTime/location not set on request (legacy conversion failed)')
    # Include houseSystem in the hash so requests that only differ by house system are treated separately
    hs = req.houseSystem if getattr(req, 'houseSystem', None) is not None else ''
    # Also include current outer-planets policy so enabling/disabling produces a fresh requestId
    try:
        from jhora import const as _c
        outer_tag = 'outerOn' if bool(getattr(_c, '_INCLUDE_URANUS_TO_PLUTO', False)) else 'outerOff'
    except Exception:
        outer_tag = 'outerNA'
    raw = f"{req.birthDateTime.isoformat()}|{req.location.place}|{req.location.latitude}|{req.location.longitude}|{req.location.tzOffset}|{req.ayanamsaMode}|{req.calcType}|{req.language}|{req.years}|{req.months}|{req.sixtyHours}|{req.praveshaType}|{req.divisionalFactors}|{hs}|{outer_tag}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _planet_retro_list(horo: Horoscope) -> List[int]:
    # After instantiation we can reuse drik.planets_in_retrograde via horoscope methods, but quick replicate:
    from jhora.panchanga import drik
    return drik.planets_in_retrograde(horo.julian_day, horo.Place)


def _dms_to_float(dms: str) -> float:
    # Expect format like '12° 34\' 56"' or similar; utils.to_dms uses a pattern; quick parse: numbers then degrees fraction
    import re
    nums = re.findall(r"[0-9]+", dms)
    if len(nums) >= 3:
        deg, minute, sec = nums[:3]
        return int(deg) + int(minute)/60.0 + int(sec)/3600.0
    if len(nums) == 2:
        deg, minute = nums
        return int(deg) + int(minute)/60.0
    if len(nums) == 1:
        return float(nums[0])
    return 0.0


def _build_chart_output(horo: Horoscope, factor: int) -> Tuple[models.DivisionalChartOut, Dict[str,str]]:
    # factor ==1 means rasi (call get_horoscope_information_for_chart with divisional_chart_factor=1)
    chart_info, chart_houses, asc_house = horo.get_horoscope_information_for_chart(divisional_chart_factor=factor)
    # chart_houses is a list[str] per house; need to split items by newline
    houses_out: List[models.HouseOut] = []
    from jhora import utils as _u2
    raasi_list_full = getattr(_u2, 'RAASI_LIST', [])
    for idx, cell in enumerate(chart_houses):
        items = [x for x in cell.split('\n') if x.strip()]
        houses_out.append(models.HouseOut(index=idx+1, items=items, signNumber=idx+1))
    # planets: filter keys ending with planet names for this factor label
    cal = horo.cal_key_list
    # Build factor label from known mapping in const.division_chart_factors if available
    factor_label = cal['raasi_str'] if factor == 1 else f"D{factor}"
    # Extract planet details
    planets_out: List[models.PlanetOut] = []
    retro_list = _planet_retro_list(horo)
    karaka_pattern = '('  # quick check
    for k,v in chart_info.items():
        # chart_info is produced per-factor by the horoscope library; avoid brittle
        # string matching for factor labels (some keys use phrases like "Custom Kundali (Dn)-Sun").
        # We'll attempt to extract planet names and parse the value text for sign/longitude.
        parts = k.split('-')
        label = parts[0] if parts else k
        # Remaining part might be planet or special lagna; we only include known planets
        planet_names = getattr(utils, 'PLANET_NAMES', [])
        raasi_list = getattr(utils, 'RAASI_LIST', [])
        for pn in planet_names:
            if pn in k:
                # v like 'Leo 12° 34' 12"'
                # v is typically like '♏︎Scorpio 29° 19’ 2" (Amatya Karaka)' or 'Leo 12° 34' 12"'
                segs = str(v).split(' ')
                house_name = ''
                if len(segs) >= 1:
                    house_name = segs[0]
                longitudeDMS = ' '.join(segs[1:]) if len(segs) > 1 else ''
                # Try to robustly find the raasi/sign name inside the full value text
                # Try to robustly find the raasi/sign name inside the full value text
                found_idx = -1
                try:
                    vtext = str(v).lower()
                    for i, rn in enumerate(raasi_list):
                        if rn.lower() in vtext:
                            found_idx = i
                            house_name = raasi_list[i]
                            break
                    if found_idx >= 0:
                        sign_index = found_idx
                    else:
                        try:
                            sign_index = raasi_list.index(house_name)
                        except Exception:
                            sign_index = -1
                except Exception:
                    sign_index = -1
                raw_deg = _dms_to_float(longitudeDMS)
                try:
                    planet_index = planet_names.index(pn)
                except ValueError:
                    planet_index = -1
                # Additional astro metadata
                abs_longitude = None
                nak_name = None
                nak_pada = None
                dignity = None
                is_exalted = is_debil = is_own = is_mt = None
                sign_str = house_name
                try:
                    # Absolute longitude: sign_index * 30 + deg portion
                    if sign_index >= 0:
                        abs_longitude = sign_index * 30 + raw_deg
                    # Nakshatra (each 13°20' = 13.3333 deg) -> 27 segments
                    if abs_longitude is not None:
                        nak_index_float = abs_longitude / (13 + 1/3)
                        nak_index = int(nak_index_float)
                        from jhora import utils as _u
                        nak_list = getattr(_u, 'NAKSHATRA_LIST', [])
                        if 0 <= nak_index < len(nak_list):
                            nak_name = nak_list[nak_index]
                        # pada: fractional part *4 +1
                        nak_pada = int((nak_index_float - nak_index) * 4) + 1
                        # Normalize spelling to canonical form (without altering original index)
                        try:
                            from . import names as _names
                            nak_name = _names.normalize_nakshatra(nak_name)
                        except Exception:
                            pass
                    # Dignity using house_strengths_of_planets matrix and moola_trikona_of_planets
                    from jhora import const as _c
                    if sign_index >= 0:
                        # sign_index corresponds to rasi 0..11
                        # planet_index may differ for Rahu/Ketu mapping but we attempt simple mapping
                        hs = None
                        if 0 <= planet_index < len(_c.house_strengths_of_planets):
                            row = _c.house_strengths_of_planets[planet_index]
                            if 0 <= sign_index < len(row):
                                hs = row[sign_index]
                        mt_sign = None
                        if 0 <= planet_index < len(_c.moola_trikona_of_planets):
                            mt_sign = _c.moola_trikona_of_planets[planet_index]
                        # Interpret codes ~ map values (5 owner,4 exalted,0 debilitated)
                        if hs is not None:
                            if hs == _c._EXALTED_UCCHAM:
                                dignity = 'Exalted'; is_exalted = True
                            elif hs == _c._DEFIBILATED_NEECHAM:
                                dignity = 'Debilitated'; is_debil = True
                            elif hs == _c._OWNER_RULER:
                                dignity = 'Own'; is_own = True
                            else:
                                dignity = 'Neutral'
                        if mt_sign is not None and sign_index == mt_sign:
                            is_mt = True
                            if dignity in (None,'Neutral'):
                                dignity = 'Moolatrikona'
                except Exception:
                    pass
                # Extract chara karaka marker if present in longitudeDMS parentheses (e.g., '(Atma Karaka)')
                ck = None
                if '(' in longitudeDMS and ')' in longitudeDMS:
                    try:
                        ck = longitudeDMS.split('(')[1].split(')')[0].strip()
                        # Remove it from longitudeDMS for cleaner display
                        longitudeDMS = longitudeDMS.replace(f'({ck})','').strip()
                    except Exception:
                        ck = None
                planets_out.append(models.PlanetOut(
                    name=pn,
                    house=sign_index+1 if sign_index>=0 else 0,  # will be overridden to relative later
                    houseAbs=sign_index+1 if sign_index>=0 else 0,
                    longitudeDMS=longitudeDMS,
                    rawLongitudeDeg=raw_deg,
                    retrograde=planet_index in retro_list,
                    charaKaraka=ck,
                    sign=sign_str,
                    absoluteLongitude=abs_longitude,
                    nakshatra=nak_name,
                    nakshatraPada=nak_pada,
                    dignity=dignity,
                    isExalted=is_exalted,
                    isDebilitated=is_debil,
                    isOwnSign=is_own,
                    isMoolatrikona=is_mt
                ))
                break
    # Fallback: if planets_out is empty (some high-resolution divisional charts may list planets only in houses
    # but not in chart_info keys), try to extract planet names from houses_out items.
    if not planets_out:
        try:
            import re as _re
            import unicodedata as _ud

            planet_names_list = getattr(utils, 'PLANET_NAMES', [])
            normalized_planets = [p.lower() for p in planet_names_list]

            def _normalize_text(txt: str) -> str:
                if not txt or not isinstance(txt, str):
                    return ''
                # Unicode normalize, strip combining marks, keep basic letters and numbers/spaces
                nf = _ud.normalize('NFKD', txt)
                no_combining = ''.join(ch for ch in nf if not _ud.combining(ch))
                # Replace common punctuation with space, then collapse to tokens
                cleaned = _re.sub(r"[^0-9A-Za-z ]+", ' ', no_combining)
                cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
                return cleaned.lower()

            def _map_token_to_planet(token: str) -> str:
                t = token.lower()
                if not t:
                    return token.capitalize()
                # match common prefixes/variants
                if t.startswith('sun'):
                    return 'Sun'
                if t.startswith('moon') or t.startswith('mo'):
                    return 'Moon'
                if t.startswith('mar') or t == 'mangal':
                    return 'Mars'
                if t.startswith('mer') or 'budh' in t:
                    return 'Mercury'
                if t.startswith('jup') or 'guru' in t or t.startswith('bru'):
                    return 'Jupiter'
                if t.startswith('ven') or 'sukra' in t:
                    return 'Venus'
                if t.startswith('sat') or 'sani' in t:
                    return 'Saturn'
                # Rahu variants: rahu, rah, ragu, raag, raagu, ragu
                if 'rah' in t or 'raag' in t or 'ragu' in t or 'rahu' in t or 'raagu' in t:
                    return 'Rahu'
                # Ketu variants
                if 'ket' in t or 'keth' in t or 'kethu' in t:
                    return 'Ketu'
                # fallback: if token is numeric (unlikely), return as-is
                return token.capitalize()

            seen = set()
            for h in houses_out:
                items = h.items or []
                for it in items:
                    if not it or not isinstance(it, str):
                        continue
                    s = _normalize_text(it)
                    if not s:
                        continue
                    # split into tokens and try each token
                    tokens = s.split(' ')
                    found_name = None
                    for tok in tokens:
                        if not tok:
                            continue
                        # try direct match with known planet names
                        for pn in normalized_planets:
                            if pn == tok or pn.startswith(tok) or tok.startswith(pn) or pn in tok or tok in pn:
                                # exact-ish match
                                try:
                                    found_name = next(x for x in planet_names_list if x.lower() == pn)
                                except StopIteration:
                                    found_name = pn.capitalize()
                                break
                        if found_name:
                            break
                        # try mapping heuristics
                        candidate = _map_token_to_planet(tok)
                        if candidate:
                            # try to map candidate back to original utils name if present
                            try:
                                found_name = next(x for x in planet_names_list if x.lower() == candidate.lower())
                            except StopIteration:
                                found_name = candidate
                        if found_name:
                            break

                    if found_name:
                        # normalize candidate: strip non-letters for matching
                        _clean = _re.sub(r'[^A-Za-z]', '', found_name).lower()
                        # skip ascendant/lagna tokens accidentally matched from house labels
                        if any(x in _clean for x in ('ascend','lagna','asc')):
                            continue
                        # avoid duplicates
                        if _clean in seen:
                            continue
                        seen.add(_clean)
                        # try to map back to canonical utils.PLANET_NAMES by stripping symbols from those too
                        canon = None
                        try:
                            for x in planet_names_list:
                                if _re.sub(r'[^A-Za-z]', '', x).lower() == _clean:
                                    canon = x
                                    break
                        except Exception:
                            canon = None
                        # fallback: if no exact match, try substring matches
                        if canon is None:
                            try:
                                for x in planet_names_list:
                                    if _clean in _re.sub(r'[^A-Za-z]', '', x).lower() or _re.sub(r'[^A-Za-z]', '', x).lower() in _clean:
                                        canon = x
                                        break
                            except Exception:
                                canon = None

                        # last resort: use heuristic mapper on the token
                        if canon is None:
                            cand = _map_token_to_planet(_clean)
                            # map back to utils name if available
                            try:
                                canon = next(x for x in planet_names_list if _re.sub(r'[^A-Za-z]', '', x).lower() == _re.sub(r'[^A-Za-z]', '', cand).lower())
                            except StopIteration:
                                canon = cand

                        sign_name = None
                        try:
                            sign_idx = h.signNumber - 1 if h.signNumber else None
                            raasi_list_full = getattr(utils, 'RAASI_LIST', [])
                            sign_name = raasi_list_full[sign_idx] if sign_idx is not None and sign_idx < len(raasi_list_full) else None
                        except Exception:
                            sign_name = None

                        # attempt to extract longitudeDMS/rawLongitudeDeg by looking up chart_info
                        longitudeDMS = ''
                        raw_deg = 0.0
                        retro = False
                        chara = None
                        sign_str_local = sign_name
                        # prepare normalized tokens for comparison
                        def _strip_letters(x: str) -> str:
                            return _re.sub(r'[^A-Za-z]', '', x).lower() if x else ''
                        target_token = _strip_letters(str(canon))
                        matched_val = None
                        for ck, cv in chart_info.items():
                            if not isinstance(ck, str):
                                continue
                            key_s = ck.lower()
                            # compare stripped letters
                            if target_token and target_token in _strip_letters(ck):
                                matched_val = cv
                                break
                            # also try simple substring match
                            if canon and canon.lower() in key_s:
                                matched_val = cv
                                break
                        if matched_val:
                            try:
                                segs = str(matched_val).split(' ')
                                house_name_loc = segs[0] if segs else ''
                                longitudeDMS = ' '.join(segs[1:]).strip() if len(segs) > 1 else ''
                                if longitudeDMS:
                                    raw_deg = _dms_to_float(longitudeDMS)
                                # try to set sign string if present
                                try:
                                    raasi_list_local = getattr(utils, 'RAASI_LIST', [])
                                    sign_idx_local = raasi_list_local.index(house_name_loc) if house_name_loc in raasi_list_local else -1
                                    if sign_idx_local >= 0:
                                        sign_str_local = raasi_list_local[sign_idx_local]
                                except Exception:
                                    pass
                            except Exception:
                                longitudeDMS = ''
                                raw_deg = 0.0
                        # retrograde detection if planet present in utils list
                        try:
                            p_idx = next((i for i,x in enumerate(planet_names_list) if _strip_letters(x) == _strip_letters(str(canon))), None)
                            if p_idx is not None and p_idx != None:
                                retro = p_idx in retro_list
                        except Exception:
                            retro = False

                        planets_out.append(models.PlanetOut(
                            name=canon,
                            house=h.index,
                            houseAbs=h.signNumber or 0,
                            longitudeDMS=longitudeDMS,
                            rawLongitudeDeg=raw_deg,
                            retrograde=retro,
                            charaKaraka=chara,
                            sign=sign_str_local,
                            absoluteLongitude=None,
                            nakshatra=None,
                            nakshatraPada=None,
                            dignity=None
                        ))
        except Exception:
            pass
    # Special lagna (subset): search keys containing (Bhava Lagna Short etc.)
    special_map = {}
    for k,v in chart_info.items():
        if '(' in k and factor_label in k:
            lower = k.lower()
            if 'bhava lagna' in lower: special_map['bhava']=v
            elif 'hora lagna' in lower: special_map['hora']=v
            elif 'ghati lagna' in lower: special_map['ghati']=v
            elif 'vighati lagna' in lower: special_map['vighati']=v
            elif 'pranapada lagna' in lower: special_map['pranapada']=v
            elif 'indu lagna' in lower: special_map['indu']=v
            elif 'bhrigu bindhu' in lower: special_map['bhriguBindhu']=v
            elif 'kunda lagna' in lower: special_map['kunda']=v
            elif 'sree lagna' in lower: special_map['sree']=v
            elif 'varnada lagna' in lower and ' (v' not in lower: special_map['varnada']=v
            elif 'maandi' in lower: special_map['maandhi']=v
    # Sphuta subset: keys ending with ' Sphuta'
    sphuta_map = {}
    for k,v in chart_info.items():
        if ' Sphuta' in k and factor_label in k:
            label = k.split('-')[-1].replace(' Sphuta','').strip()
            sphuta_map[label]=v
    # Upagrahas and related special points (not tagged as Sphuta in library output)
    for k,v in chart_info.items():
        if factor_label not in k:
            continue
        lower = k.lower()
        # Include common special points under sphuta_map for unified display in UI
        if any(x in lower for x in ['gulika','kaala','mrityu','yama','artha','dhuma','vyatipaata','parivesha','indrachaapa','upaketu']):
            # normalize a short key
            key_label = None
            for token in ['gulika','kaala','mrityu','yama','artha','dhuma','vyatipaata','parivesha','indrachaapa','upaketu']:
                if token in lower:
                    key_label = token.replace('vyatipaata','vyatipata').replace('indrachaapa','indra chapa')
                    break
            if key_label:
                sphuta_map[key_label] = v
        # Capture Varnada Lagna V2..V12 variants into sphuta as V2..V12 for visibility
        if 'varnada lagna' in lower and ' (v' in lower:
            try:
                var_label = k.split('(')[-1].split(')')[0].strip().upper()  # e.g., V2
                sphuta_map[var_label] = v
            except Exception:
                pass
    # Compute relative houses (rotate so lagna = 1)
    asc_abs = asc_house + 1  # library gives 0-based
    for p in planets_out:
        if p.houseAbs is None:
            p.houseAbs = p.house
        if p.houseAbs and asc_abs:
            rel = ((p.houseAbs - asc_abs) % 12) + 1
            p.houseRel = rel
            try:
                p.house = int(rel)
            except Exception:
                pass
    # Rotate houses so ascendant sign becomes index 1 (relative). Preserve absolute version.
    houses_abs = houses_out
    if 0 <= asc_house < len(houses_out):
        # asc_house is 0-based absolute; rotation amount = asc_house
        houses_out = []
        for i in range(len(houses_abs)):
            h = houses_abs[(asc_house + i) % 12]
            houses_out.append(models.HouseOut(index=i+1, items=h.items, signNumber=h.signNumber))
    # Inject outer planets (Uranus/Neptune/Pluto) if library flag enabled but PLANET_NAMES does not list them.
    # This compensates for legacy resource files that only define Sun..Ketu names; we compute basic metadata here.
    try:
        from jhora import const as _c2
        from jhora.panchanga import drik as _drik2
        from jhora import utils as _u3
        if getattr(_c2, '_INCLUDE_URANUS_TO_PLUTO', False):
            def _norm_nm(n: str) -> str:
                import re as _re
                return _re.sub(r'[^a-z]', '', n.lower()) if isinstance(n, str) else ''
            existing_names = {p.name for p in planets_out}
            existing_bases = {_norm_nm(p.name) for p in planets_out}
            # Choose display names (without glyphs to match existing style for outers in UI code)
            outer_planet_defs = [
                ('Uranus', _c2._URANUS),
                ('Neptune', _c2._NEPTUNE),
                ('Pluto', _c2._PLUTO)
            ]
            raasi_list_full = getattr(_u3, 'RAASI_LIST', [])
            nak_list_full = getattr(_u3, 'NAKSHATRA_LIST', [])
            for disp_name, pid in outer_planet_defs:
                # Skip if any existing planet has same base name (covers glyph variants like 'Uranus♅')
                if _norm_nm(disp_name) in existing_bases:
                    continue
                try:
                    # Sidereal longitude (absolute 0..360)
                    longi_abs = _drik2.sidereal_longitude(horo.julian_day, pid)
                    sign_index = int(longi_abs // 30)
                    intra_sign_deg = longi_abs - sign_index * 30
                    d,m,s = _u3.to_dms_prec(intra_sign_deg)
                    longitudeDMS = f"{d}{_c2._degree_symbol} {m}{_c2._minute_symbol} {int(s)}\""  # coarse formatting like existing parser
                    sign_name = raasi_list_full[sign_index] if 0 <= sign_index < len(raasi_list_full) else None
                    # Nakshatra & pada
                    nak_index_float = longi_abs / (13 + 1/3)
                    nak_index = int(nak_index_float)
                    nak_name = nak_list_full[nak_index] if 0 <= nak_index < len(nak_list_full) else None
                    nak_pada = int((nak_index_float - nak_index) * 4) + 1 if nak_name else None
                    # Retrograde detection via speed (negative longitude speed)
                    try:
                        speed_info = _drik2._planet_speed_info(horo.julian_day, horo.Place, pid)
                        retro = speed_info[3] < 0
                    except Exception:
                        retro = False
                    # Dignity enrichment: treat outer planets as Neutral (no classical exaltation/debilitation in Vedic scheme)
                    is_exalted = False
                    is_debilitated = False
                    is_own = False
                    is_mt = False
                    planets_out.append(models.PlanetOut(
                        name=disp_name,
                        house=sign_index+1 if sign_index>=0 else 0,
                        houseAbs=sign_index+1 if sign_index>=0 else 0,
                        longitudeDMS=longitudeDMS,
                        rawLongitudeDeg=intra_sign_deg,
                        retrograde=retro,
                        charaKaraka=None,
                        sign=sign_name,
                        absoluteLongitude=longi_abs,
                        nakshatra=nak_name,
                        nakshatraPada=nak_pada,
                        dignity='Neutral',
                        isExalted=is_exalted,
                        isDebilitated=is_debilitated,
                        isOwnSign=is_own,
                        isMoolatrikona=is_mt
                    ))
                except Exception:
                    continue
            # After injection, recompute relative houses for the injected ones
            asc_abs = asc_house + 1
            for p in planets_out:
                if p.houseAbs and asc_abs:
                    rel = ((p.houseAbs - asc_abs) % 12) + 1
                    p.houseRel = rel
                    try:
                        p.house = int(rel)
                    except Exception:
                        pass
            # Final dedupe pass: ensure only one entry per normalized planet base name
            dedup: list[models.PlanetOut] = []
            seen_base: set[str] = set()
            for p in planets_out:
                b = _norm_nm(p.name)
                if not b:
                    dedup.append(p); continue
                if b in seen_base:
                    continue
                seen_base.add(b); dedup.append(p)
            planets_out = dedup
    except Exception:
        pass
    # Compute true Udaya Lagna (Ascendant)
    asc_long_dms: str | None = None
    asc_raw_deg: float | None = None
    asc_abs_long: float | None = None
    asc_nak_name: str | None = None
    asc_nak_pada: int | None = None
    asc_const: int | None = None
    try:
        from jhora.panchanga import drik as _dr
        from jhora import utils as _uasc
        
        # For D1, use the specialized high-precision ascendant function.
        # For divisional charts, use the data we exposed from main.py
        if factor == 1:
            asc_tuple = _dr.ascendant(horo.julian_day, horo.Place)
            # asc_tuple: [constellationIndex, withinSignLongitude, nakshatraIndex, pada]
            if isinstance(asc_tuple, (list, tuple)) and len(asc_tuple) >= 4:
                asc_const = int(asc_tuple[0])
                asc_raw_deg = float(asc_tuple[1])
                # Nakshatra provided directly
                nak_idx = int(asc_tuple[2])
                asc_nak_pada = int(asc_tuple[3])
                nak_list = getattr(_uasc, 'NAKSHATRA_LIST', [])
                if 0 <= nak_idx < len(nak_list):
                    asc_nak_name = nak_list[nak_idx]
        elif 'ascendant_data' in chart_info:
             adat = chart_info['ascendant_data']
             if isinstance(adat, (list, tuple)) and len(adat) >= 2:
                  asc_const = int(adat[0])
                  asc_raw_deg = float(adat[1])
                  # Calculate derived properties
                  _abs = asc_const * 30.0 + asc_raw_deg
                  nak_index_float = _abs / (13.33333333333)
                  nak_idx = int(nak_index_float)
                  asc_nak_pada = int((nak_index_float - nak_idx) * 4) + 1
                  nak_list = getattr(_uasc, 'NAKSHATRA_LIST', [])
                  if 0 <= nak_idx < len(nak_list):
                      asc_nak_name = nak_list[nak_idx]

        if asc_const is not None and asc_raw_deg is not None:
            asc_abs_long = asc_const * 30.0 + asc_raw_deg
            # Format DMS
            try:
                d,m,s = _uasc.to_dms_prec(asc_raw_deg)
                from jhora import const as _cc
                asc_long_dms = f"{d}{_cc._degree_symbol} {m}{_cc._minute_symbol} {s:.2f}\""
            except Exception:
                asc_long_dms = None
    except Exception:
        pass

    chart_out = models.DivisionalChartOut(
        factor=factor,
        label=factor_label,
        ascendantHouse=1,  # normalized relative representation
        ascendantSignNumber=asc_abs,
        ascendantSign=raasi_list_full[asc_house] if asc_house < len(raasi_list_full) else None,
        ascendantLongitudeDMS=asc_long_dms,
        ascendantRawLongitudeDeg=asc_raw_deg,
        ascendantAbsoluteLongitude=asc_abs_long,
    ascendantNakshatra=asc_nak_name,
    ascendantNakshatraPada=asc_nak_pada,
        ascendantHouseRel=1,
        houses=houses_out,
        # Remove any library-provided Lagna planet to avoid duplicate with synthetic Ascendantℒ
        planets=[p for p in planets_out if not (isinstance(p.name,str) and p.name.lower().startswith('lagna'))],
        specialLagna=models.SpecialLagnaOut(**special_map),
        sphuta=sphuta_map
    )
    # Inject a synthetic Ascendant row as the first planet-like entry for consistent UI rendering
    try:
        if asc_const is not None and asc_raw_deg is not None:
            asc_name = 'Ascendantℒ'
            # Prevent duplicate insertion if already present
            if not any(isinstance(p.name, str) and p.name.startswith('Ascendant') for p in chart_out.planets):
                chart_out.planets = [
                    models.PlanetOut(
                        name=asc_name,
                        house=1,
                        houseRel=1,
                        houseAbs=int(asc_const)+1,
                        longitudeDMS=asc_long_dms or '',
                        rawLongitudeDeg=float(asc_raw_deg),
                        retrograde=False,
                        charaKaraka=None,
                        sign=raasi_list_full[asc_const] if 0 <= asc_const < len(raasi_list_full) else None,
                        absoluteLongitude=float(asc_abs_long) if asc_abs_long is not None else None,
                        nakshatra=asc_nak_name,
                        nakshatraPada=asc_nak_pada,
                        dignity=None
                    )
                ] + chart_out.planets
    except Exception:
        pass
    return chart_out, chart_info


def compute_horoscope(req: models.HoroscopeRequest) -> models.StoredHoroscope:
    lang = _normalize_language(getattr(req, 'language', None))
    try:
        req.language = lang
    except Exception:
        pass
    rhash = _request_hash(req)
    with _store_lock:
        if rhash in _store:
            return _store[rhash]
    if req.birthDateTime is None or req.location is None:
        raise ValueError('birthDateTime and location are required')
    with _language_lock:
        prev_lang = getattr(const, '_DEFAULT_LANGUAGE', 'en')
        changed_lang = prev_lang != lang
        if changed_lang:
            try:
                utils.set_language(lang)
            except Exception:
                changed_lang = False
        try:
            # Ensure the drik planet list includes Uranus/Neptune/Pluto when enabled
            try:
                from jhora.panchanga import drik as _drik
                calc_type = (req.calcType or 'drik').lower()
                if calc_type == 'ss':
                    _drik.planet_list = [
                        const._SUN, const._MOON, const._MARS, const._MERCURY, const._JUPITER,
                        const._VENUS, const._SATURN, const._RAHU, const._KETU
                    ]
                elif getattr(const, '_INCLUDE_URANUS_TO_PLUTO', False):
                    _drik.set_sideral_planets()
                else:
                    _drik.planet_list = [
                        const._SUN, const._MOON, const._MARS, const._MERCURY, const._JUPITER,
                        const._VENUS, const._SATURN, const._RAHU, const._KETU
                    ]
            except Exception:
                pass
            dt = req.birthDateTime
            # Build date and time inputs
            from jhora.panchanga import drik
            d = drik.Date(dt.year, dt.month, dt.day)
            bt = dt.strftime('%H:%M:%S')
            place_with_country = req.location.place
            latitude = req.location.latitude
            longitude = req.location.longitude
            tz = req.location.tzOffset
            # If place string not provided but lat/long are, provide fallback name
            place_arg = place_with_country or 'CustomLocation'
            lat_arg = latitude if latitude is not None else None
            lon_arg = longitude if longitude is not None else None
            if place_with_country and (lat_arg is None or lon_arg is None):
                fallback = _lookup_world_city(place_with_country, tz)
                if fallback:
                    lat_arg = fallback[0]
                    lon_arg = fallback[1]
                    if tz is None and fallback[2] is not None:
                        tz = fallback[2]
            # Map requested house system to internal bhaava madhya method if provided
            from jhora import const as _c
            bhava_method = _c.bhaava_madhya_method
            house_system_applied = None
            try:
                if req.houseSystem:
                    key_raw = str(req.houseSystem).strip()
                    # Available keys in library may be ints (1,2..) or strings ('P','K',...)
                    available = _c.available_house_systems
                    selected_key = None
                    # Common alias fallbacks (highest priority)
                    # Common alias fallbacks (highest priority). Map many user-friendly names to library keys.
                    alias_map = {
                        'default': _c.bhaava_madhya_method,
                        'equal': 2,
                        'equal_housing': 2,
                        'equalmiddle': 1,
                        'equal_middle': 1,
                        'sripati': 3,
                        'sripathi': 3,
                        'placidus': 4,
                        'kp': 4,
                        'koch': 'K',
                        'porphyrius': 'O',
                        'porphyry': 'O',
                        'porphyrius': 'O',
                        'regiomontanus': 'R',
                        'campanus': 'C',
                        'alcabitus': 'B',
                        'morinus': 'M',
                        'vehlow': 'V',
                        'axial': 'X',
                    }
                    if key_raw.lower() in alias_map:
                        selected_key = alias_map[key_raw.lower()]

                    # 1) Exact key match (allow numeric strings)
                    for k in available.keys():
                        if str(k).lower() == key_raw.lower():
                            selected_key = k
                            break
                    # 2) Match by label/content (e.g., 'equal','sripati','placidus')
                    if selected_key is None:
                        for k,v in available.items():
                            if key_raw.lower() == str(v).lower() or key_raw.lower() in str(v).lower():
                                selected_key = k
                                break
                    # 3) (already handled above) fallback if still None -> leave None
                    # Apply selection if found
                    if selected_key is not None:
                        # If selected_key is numeric (string or int-like), coerce to int for library calls
                        try:
                            if isinstance(selected_key, str) and selected_key.isdigit():
                                bhava_method = int(selected_key)
                            else:
                                bhava_method = int(selected_key) if isinstance(selected_key, (int,)) else selected_key
                        except Exception:
                            bhava_method = selected_key
                        # Expose both key and human-friendly label to the API consumer
                        try:
                            # available may have integer or string keys
                            label = available[selected_key]
                        except Exception:
                            # if selected_key is numeric string, try converting
                            try:
                                label = available[int(selected_key)]
                            except Exception:
                                # fallback: attempt lookup by matching stringified keys
                                lab = None
                                for k,v in available.items():
                                    if str(k).lower() == str(selected_key).lower():
                                        lab = v; break
                                label = lab or str(selected_key)
                        house_system_applied = str(label)
                        # also keep raw key for consumers that need canonical key
                        house_system_applied_key = str(selected_key)
                    else:
                        house_system_applied = 'DEFAULT'
                        house_system_applied_key = str(_c.bhaava_madhya_method)
                else:
                    house_system_applied = 'DEFAULT'
                    house_system_applied_key = str(_c.bhaava_madhya_method)
            except Exception:
                bhava_method = _c.bhaava_madhya_method
                if not house_system_applied:
                    house_system_applied = 'DEFAULT'
                house_system_applied_key = str(_c.bhaava_madhya_method)
            # Ensure bhava_method is an int acceptable to Horoscope (library expects int keys for methods)
            try:
                bhava_method_int = int(bhava_method)
            except Exception:
                try:
                    bhava_method_int = int(_c.bhaava_madhya_method)
                except Exception:
                    bhava_method_int = 1
            horo = Horoscope(place_with_country_code=place_arg, latitude=lat_arg, longitude=lon_arg,
                             timezone_offset=tz, date_in=d, birth_time=bt, ayanamsa_mode=req.ayanamsaMode,
                             calculation_type=req.calcType, years=req.years, months=req.months,
                             sixty_hours=req.sixtyHours, pravesha_type=req.praveshaType, language=req.language,
                             bhava_madhya_method=bhava_method_int)
            calendar = horo.calendar_info
            factors = COMMON_DIVISIONALS if req.divisionalFactors is None else req.divisionalFactors
            chart_infos: Dict[int, Dict[str,str]] = {}
            # Always build rasi (D1) and include it as part of divisionalCharts so the UI's
            # "Divisional Charts (Vargas)" section includes D1 alongside other divisionals.
            rasi_chart_out, info_rasi = _build_chart_output(horo, 1)
            chart_infos[1] = info_rasi
            # Start charts_out with the D1 chart so Vargas list contains D1 first.
            charts_out: List[models.DivisionalChartOut] = [rasi_chart_out]
            for f in factors:
                if f == 1:
                    # already included
                    continue
                try:
                    ch_out, info = _build_chart_output(horo, f)
                    charts_out.append(ch_out)
                    chart_infos[f] = info
                except Exception:
                    # Skip unsupported factor gracefully
                    continue
            resp = models.HoroscopeResponse(
                requestId=rhash,
                meta={
                    "requestId": rhash,
                    "generatedAt": datetime.now(UTC).isoformat(),
                    "version": "api-0.2",  # bumped after relative house + ascendant sign enhancements
                    "compact": req.compact,
                    "agentMode": getattr(req,'sendToAgentMode','summary'),
                    "houseSystemRequested": req.houseSystem or 'DEFAULT',
                    # Human-readable label (preferred for display) and the canonical applied key
                    "houseSystemApplied": house_system_applied or 'DEFAULT',
                    "houseSystemAppliedKey": house_system_applied_key if 'house_system_applied_key' in locals() else str(_c.bhaava_madhya_method)
                },
                calendar=calendar,
                rasiChart=rasi_chart_out,
                divisionalCharts=[] if req.compact else charts_out,
                # Panchanga: Birth chart panchanga (already calculated in calendar_info)
                panchanga=calendar,
                # Current Transits: Calculate current planetary positions
                currentTransits={}  # Will be populated below
            )
            
            # Calculate current transits (current planetary positions)
            try:
                from jhora import utils as _u_transit
                from jhora.panchanga import drik as _drik_transit
                from datetime import datetime as _dt_transit, timezone as _tz_transit
                
                # Get current Julian Day
                now_utc = _dt_transit.now(_tz_transit.utc)
                current_jd = _u_transit.julian_day_number(
                    _drik_transit.Date(now_utc.year, now_utc.month, now_utc.day),
                    (now_utc.hour, now_utc.minute, now_utc.second)
                )
                
                # Calculate transit positions using same place/ayanamsa as birth chart
                transit_planets = []
                planet_ids = [const._SUN, const._MOON, const._MARS, const._MERCURY, 
                             const._JUPITER, const._VENUS, const._SATURN, 
                             const._RAHU, const._KETU]
                
                planet_names_list = getattr(_u_transit, 'PLANET_NAMES', 
                    ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'])
                raasi_list_transit = getattr(_u_transit, 'RAASI_LIST', [])
                
                for i, pid in enumerate(planet_ids):
                    try:
                        # Get sidereal longitude
                        long_abs = _drik_transit.sidereal_longitude(current_jd, pid)
                        sign_index = int(long_abs // 30)
                        intra_deg = long_abs - sign_index * 30
                        d, m, s = _u_transit.to_dms_prec(intra_deg)
                        
                        planet_name = planet_names_list[i] if i < len(planet_names_list) else f'Planet{i}'
                        sign_name = raasi_list_transit[sign_index] if 0 <= sign_index < len(raasi_list_transit) else None
                        
                        transit_planets.append({
                            'name': planet_name,
                            'sign': sign_name,
                            'longitudeDMS': f"{d}° {m}' {int(s)}\"",
                            'house': sign_index + 1
                        })
                    except Exception:
                        continue
                
                resp.currentTransits = {
                    'date': now_utc.isoformat(),
                    'planets': transit_planets
                }
            except Exception:
                # If transit calculation fails, leave as None
                pass

            # Derive combustion & vargottama and annotate (use a small robust helper)
            try:
                import re
                from jhora import const as _jconst

                def _norm(name: str) -> str:
                    if not name: return name
                    n = re.sub(r'[^A-Za-z]','', name).lower()
                    if 'sun' in n: return 'Sun'
                    if 'moon' in n: return 'Moon'
                    if 'mars' in n: return 'Mars'
                    if 'mercury' in n or 'budh' in n: return 'Mercury'
                    if 'jupiter' in n or 'guru' in n: return 'Jupiter'
                    if 'venus' in n or 'sukra' in n: return 'Venus'
                    if 'saturn' in n or 'sani' in n: return 'Saturn'
                    if 'rahu' in n or 'raagu' in n: return 'Rahu'
                    if 'ketu' in n: return 'Ketu'
                    return name

                # Helper: compute combustion given normalized absolute longitudes and retro flags
                def _compute_combustion_from_longitudes(longs: dict, retros: dict) -> tuple[list[str], dict]:
                    """Return (combust_norm_list, details_map) where combust_norm_list contains normalized planet keys (e.g. 'Mars'),
                    and details_map gives distance, limit and combust boolean for each planet checked."""
                    base_ranges = getattr(_jconst,'combustion_range_of_planets_from_sun',[12,17,14,10,11,15])
                    retro_ranges = getattr(_jconst,'combustion_range_of_planets_from_sun_while_in_retrogade',[12,8,12,11,8,16])
                    order = ['Moon','Mars','Mercury','Jupiter','Venus','Saturn']
                    # build direct map planet->limit
                    base_map = { order[i]: base_ranges[i] for i in range(min(len(order), len(base_ranges))) }
                    retro_map = { order[i]: retro_ranges[i] for i in range(min(len(order), len(retro_ranges))) }

                    def ang_diff(a:float,b:float):
                        d = abs(a-b) % 360.0
                        return d if d <= 180.0 else 360.0-d

                    sun = longs.get('Sun')
                    if sun is None:
                        return [], {}
                    combust_norm: list[str] = []
                    details: dict = {}
                    for pname in order:
                        if pname not in longs:
                            continue
                        dist = ang_diff(longs[pname], sun)
                        limit = retro_map.get(pname) if retros.get(pname, False) else base_map.get(pname)
                        is_comb = False
                        if limit is not None:
                            try:
                                is_comb = float(dist) <= float(limit)
                            except Exception:
                                is_comb = False
                        details[pname] = {'distance': round(float(dist),6), 'limit': limit, 'combust': bool(is_comb)}
                        if is_comb:
                            combust_norm.append(pname)
                    return combust_norm, details

                # Build normalized absolute longitude map using absoluteLongitude when present
                longitudes: dict[str,float] = {}
                retro_flags: dict[str,bool] = {}
                orig_names_for_norm: dict[str,str] = {}
                for p in resp.rasiChart.planets:
                    try:
                        abs_long = None
                        if getattr(p, 'absoluteLongitude', None) is not None:
                            val = p.absoluteLongitude
                            if val is not None:
                                abs_long = float(val)
                        else:
                            raw = getattr(p, 'rawLongitudeDeg', None)
                            if raw is None:
                                continue
                            rawf = float(raw)
                            ha = getattr(p, 'houseAbs', None)
                            if ha:
                                abs_long = (int(ha)-1) * 30.0 + rawf
                            else:
                                # if raw looks absolute use it
                                if rawf >= 30.0:
                                    abs_long = rawf
                                else:
                                    continue
                    except Exception:
                        continue
                    if abs_long is None:
                        continue
                    nn = _norm(p.name)
                    longitudes[nn] = abs_long
                    retro_flags[nn] = bool(getattr(p,'retrograde', False))
                    orig_names_for_norm[nn] = p.name

                combust_norm_list, combust_details = _compute_combustion_from_longitudes(longitudes, retro_flags)
                combustion: list[str] = [ orig_names_for_norm.get(n, n) for n in combust_norm_list ]

                # Vargottama: same sign in D1 and Navamsa (factor 9)
                d9 = None
                for dc in resp.divisionalCharts:
                    if dc.factor == 9:
                        d9 = dc; break
                vargottama: list[str] = []
                if d9:
                    d1_signs = {p.name: p.sign for p in resp.rasiChart.planets if p.sign}
                    d9_signs = {p.name: p.sign for p in d9.planets if p.sign}
                    vargottama = [pn for pn,s in d1_signs.items() if d9_signs.get(pn) == s]

                resp.combustion = combustion
                resp.vargottama = vargottama

                # annotate planets using normalized match
                for p in resp.rasiChart.planets:
                    pn_norm = _norm(p.name)
                    if pn_norm in combust_norm_list:
                        setattr(p,'isCombust', True)
                    if p.name in vargottama or _norm(p.name) in [re.sub(r'[^A-Za-z]','',v).capitalize() for v in vargottama]:
                        setattr(p,'isVargottama', True)
                for dc in resp.divisionalCharts:
                    for p in dc.planets:
                        if _norm(p.name) in combust_norm_list:
                            setattr(p,'isCombust', True)
                        if p.name in vargottama and dc.factor==9:
                            setattr(p,'isVargottama', True)
            except Exception:
                # Do not fail overall if combustion annotation errors
                pass
            if req.compact:
                # Trim calendar to essential keys
                essential_keys = [k for k in calendar.keys() if any(t in k.lower() for t in ['sunrise','sunset','moonrise','moonset','ayanamsa','tithi','nakshatra'])]
                resp.calendar = {k: calendar[k] for k in essential_keys}
                # Minify planet objects (drop heavy optional fields)
                for p in resp.rasiChart.planets:
                    p.absoluteLongitude = None
                    p.nakshatra = None
                    p.nakshatraPada = None
                    # keep dignity flags only
                    p.dignity = p.dignity
            stored = models.StoredHoroscope(request=req, response=resp, internalHoroscope=horo)
            with _store_lock:
                _store[rhash]=stored
            try:
                upsert_persisted_request(rhash, req.model_dump(mode='json'))
                persist_requests_sync()
            except Exception:
                pass
            return stored

        finally:
            if changed_lang:
                try:
                    utils.set_language(prev_lang)
                except Exception:
                    pass

def _normalize_language(language: str | None) -> str:
    if not language:
        return 'en'
    lang = language.strip().lower()
    if not lang:
        return 'en'
    try:
        available = set(const.available_languages.values())
        if lang not in available:
            return 'en'
    except Exception:
        pass
    return lang


def _format_detail_entries(raw: Dict[str, Any]) -> List[models.DetailedCalculationItem]:
    entries: List[models.DetailedCalculationItem] = []
    for key, value in raw.items():
        chart = name = desc = benefit = None
        extra: List[str] | None = None
        raw_payload: Any | None = None
        if isinstance(value, (list, tuple)):
            if len(value) > 0:
                chart = str(value[0]) if value[0] is not None else None
            if len(value) > 1:
                name = value[1]
            if len(value) > 2:
                desc = value[2]
            if len(value) > 3:
                benefit = value[3]
            if len(value) > 4:
                extra = [str(_to_native(v)) for v in value[4:]]
        else:
            raw_payload = _to_native(value)
        entries.append(models.DetailedCalculationItem(
            chart=chart,
            key=str(key),
            name=str(name) if name is not None else None,
            description=str(desc) if desc is not None else None,
            benefit=str(benefit) if benefit is not None else None,
            extra=extra,
            raw=raw_payload
        ))
    entries.sort(key=lambda item: (item.chart or '', item.name or '', item.key or ''))
    return entries


def _collect_calendar_and_info(horo: Horoscope, language: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    lang = _normalize_language(language)
    from copy import deepcopy
    with _language_lock:
        prev_global = getattr(const, '_DEFAULT_LANGUAGE', 'en')
        prev_lang = getattr(horo, '_language', prev_global)
        prev_cal_key_list = getattr(horo, 'cal_key_list', None)
        prev_calendar = deepcopy(getattr(horo, 'calendar_info', None))
        if prev_global != lang:
            utils.set_language(lang)
        try:
            horo._language = lang
            horo.cal_key_list = utils.resource_strings
            calendar = _to_native(horo.get_calendar_information())
            raw_info = horo.get_horoscope_information()
            if isinstance(raw_info, tuple) and raw_info:
                raw_info = raw_info[0]
            info = _to_native(raw_info)
        finally:
            if prev_global != lang:
                utils.set_language(prev_global)
            horo._language = prev_lang
            if prev_cal_key_list is not None:
                horo.cal_key_list = prev_cal_key_list
            if prev_calendar is not None:
                horo.calendar_info = prev_calendar
    return calendar, info


def build_detailed_calculations(
    stored: models.StoredHoroscope,
    language: str = 'en',
    include_yogas: bool = True,
    include_raja_yogas: bool = True,
    include_base_info: bool = True
) -> models.HoroscopeDetailsResponse:
    if not stored or not stored.internalHoroscope:
        raise ValueError('internal horoscope not available')
    lang = _normalize_language(language)
    horo = stored.internalHoroscope
    response = stored.response
    rid = response.requestId if response and response.requestId else None
    if not rid and response and isinstance(response.meta, dict):
        rid = response.meta.get('requestId')
    rid = rid or 'unknown'
    calendar: Dict[str, Any] | None = None
    info: Dict[str, Any] | None = None
    errors: List[str] = []
    if include_base_info:
        try:
            calendar, info = _collect_calendar_and_info(horo, lang)
        except Exception as exc:  # noqa: BLE001
            errors.append(f'horoscopeInfo: {exc}')
    yogas: List[models.DetailedCalculationItem] | None = None
    total_yogas = yoga_count = None
    if include_yogas:
        try:
            from jhora.horoscope.chart import yoga as _yoga  # type: ignore
            raw, count, total = _yoga.get_yoga_details_for_all_charts(horo.julian_day, horo.Place, language=lang)
            yogas = _format_detail_entries(raw)
            yoga_count = count
            total_yogas = total
        except Exception as exc:  # noqa: BLE001
            errors.append(f'yogas: {exc}')
    raja_yogas: List[models.DetailedCalculationItem] | None = None
    total_ry = ry_count = None
    if include_raja_yogas:
        try:
            from jhora.horoscope.chart import raja_yoga as _raja  # type: ignore
            raw, count, total = _raja.get_raja_yoga_details_for_all_charts(horo.julian_day, horo.Place, language=lang)
            raja_yogas = _format_detail_entries(raw)
            ry_count = count
            total_ry = total
        except Exception as exc:  # noqa: BLE001
            errors.append(f'rajaYogas: {exc}')
    payload = models.HoroscopeDetailsResponse(
        requestId=rid,
        language=lang,
        generatedAt=datetime.now(UTC),
        calendar=calendar,
        horoscopeInfo=info,
        yogas=yogas,
        rajaYogas=raja_yogas,
        yogaCount=yoga_count,
        totalYogas=total_yogas,
        rajaYogaCount=ry_count,
        totalRajaYogas=total_ry,
        errors=errors or None
    )
    return payload

async def delete_request(request_id: str) -> bool:
    """Remove a stored horoscope and its persisted request. Returns True if existed."""
    existed = False
    with _store_lock:
        if request_id in _store:
            existed = True
            try:
                del _store[request_id]
            except Exception:
                pass
    with _persist_lock:
        if request_id in _persisted_requests:
            existed = True
            try:
                del _persisted_requests[request_id]
            except Exception:
                pass
    if existed:
        try:
            await persist_requests()
        except Exception:
            pass
    # Remove cache entries referencing this request id
    try:
        with _horo_cache_lock:
            to_del = [k for k,v in _horo_cache.items() if v.meta.get('requestId') == request_id]
            for k in to_del: _horo_cache.pop(k, None)
    except Exception:
        pass
    return existed

def list_requests(limit: int = 200) -> list[dict]:
    """Return basic metadata for stored (in-memory or persisted) request IDs."""
    out = []
    # In-memory first
    with _store_lock:
        store_items = list(_store.items())[:limit]
    for rid, stored in store_items:
        meta = getattr(stored.response, 'meta', {}) if stored.response else {}
        out.append({
            'requestId': rid,
            'generatedAt': meta.get('generatedAt'),
            'charts': len(getattr(stored.response,'divisionalCharts',[]) or []),
            'hasDeep': False  # placeholder for future cached deep strength flag
        })
    # Add persisted that are not in memory (lazy recompute available)
    with _persist_lock:
        persisted_keys = list(_persisted_requests.keys())
    for rid in persisted_keys:
        if any(r['requestId']==rid for r in out):
            continue
        out.append({'requestId': rid, 'generatedAt': None, 'charts': None, 'hasDeep': False})
    return out[:limit]


def get_stored(request_id: str) -> models.StoredHoroscope | None:
    with _store_lock:
        existing = _store.get(request_id)
    if existing:
        return existing
    # Lazy recompute if we have a persisted request
    with _persist_lock:
        data = _persisted_requests.get(request_id)
    if data:
        try:
            req = models.HoroscopeRequest(**data)
            return compute_horoscope(req)
        except Exception:
            return None
    return None
