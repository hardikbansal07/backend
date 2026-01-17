from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# Request / Response Models
class LocationIn(BaseModel):
    place: Optional[str] = Field(None, description="City,CountryCode or free text")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    tzOffset: float = Field(..., description="Timezone offset hours from UTC (e.g. 5.5)")

class HoroscopeRequest(BaseModel):
    # Preferred new structured fields
    birthDateTime: datetime | None = Field(None, description="Birth datetime in local time of given tzOffset")
    location: LocationIn | None = None
    ayanamsaMode: str = Field("TRUE_CITRA")
    calcType: Literal['drik','ss'] = 'drik'
    houseSystem: str | None = Field(None, description="House system / bhava madhya method override (e.g., PLACIDUS, EQUAL, SRIPATI)")
    language: str = Field("en")
    years: int = 1
    months: int = 1
    sixtyHours: int = 1
    praveshaType: int = 0
    divisionalFactors: Optional[List[int]] = Field(None, description="List of divisional chart factors to compute, defaults to common subset")
    sendToAgent: bool = False
    sendToAgentMode: Literal['summary','bundle','full'] = 'summary'
    # Legacy flat fields (for backward compatibility with earlier UI / scripts)
    name: Optional[str] = Field(None, description="(legacy) Person name / place label")
    date: Optional[str] = Field(None, description="(legacy) Date YYYY-MM-DD")
    time: Optional[str] = Field(None, description="(legacy) Time HH:MM or HH:MM:SS")
    tzOffsetMinutes: Optional[int] = Field(None, description="(legacy) Timezone offset minutes from UTC")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="(legacy) Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="(legacy) Longitude")
    compact: bool = Field(False, description="If true, return a reduced (compact) horoscope payload: trimmed calendar, no divisionalCharts, minimal planet fields.")

    @field_validator("birthDateTime", mode="before")
    @classmethod
    def parse_birth_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            try:
                return datetime.fromisoformat(v)
            except Exception as e:
                raise ValueError(f"Invalid birthDateTime format: {v}. Expected ISO format like '2000-01-01T06:30:00'. Error: {e}")
        raise ValueError(f"birthDateTime must be a datetime or string, got {type(v)}")

    @field_validator("divisionalFactors")
    @classmethod
    def validate_divisionals(cls, v):
        if v is not None:
            for f in v:
                if f <= 0:
                    raise ValueError("Divisional factor must be > 0")
        return v

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):  # override to inject legacy conversion before standard validation
        if isinstance(obj, dict):
            data = dict(obj)
            if (data.get('birthDateTime') is None or data.get('location') is None) and data.get('date') and data.get('time'):
                # Build birthDateTime
                dt_str = data['date'].strip() + 'T' + data['time'].strip()
                # Ensure seconds
                if len(data['time'].split(':')) == 2:
                    dt_str += ':00'
                try:
                    data['birthDateTime'] = datetime.fromisoformat(dt_str)
                except Exception:
                    pass
            if data.get('location') is None and (data.get('latitude') is not None or data.get('longitude') is not None or data.get('tzOffsetMinutes') is not None):
                tz_minutes = data.get('tzOffsetMinutes')
                tz_hours = tz_minutes/60.0 if isinstance(tz_minutes,(int,float)) else 0.0
                data['location'] = {
                    'place': data.get('name') or 'Unknown',
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'tzOffset': tz_hours
                }
            obj = data
        return super().model_validate(obj, *args, **kwargs)

class PlanetOut(BaseModel):
    name: str
    house: int
    houseRel: Optional[int] = None  # 1..12 relative from ascendant
    houseAbs: Optional[int] = None  # preserve original absolute sign index (+1)
    longitudeDMS: str
    rawLongitudeDeg: float
    retrograde: bool
    charaKaraka: Optional[str] = None
    sign: Optional[str] = None
    absoluteLongitude: Optional[float] = None
    nakshatra: Optional[str] = None
    nakshatraPada: Optional[int] = None
    dignity: Optional[str] = None  # Exalted, Debilitated, Own, Moolatrikona, Neutral
    isExalted: Optional[bool] = None
    isDebilitated: Optional[bool] = None
    isOwnSign: Optional[bool] = None
    isMoolatrikona: Optional[bool] = None
    isCombust: Optional[bool] = None
    isVargottama: Optional[bool] = None

class HouseOut(BaseModel):
    index: int
    items: List[str]
    signNumber: Optional[int] = None  # absolute zodiac sign number (Aries=1)

class SpecialLagnaOut(BaseModel):
    bhava: Optional[str] = None
    hora: Optional[str] = None
    ghati: Optional[str] = None
    vighati: Optional[str] = None
    pranapada: Optional[str] = None
    indu: Optional[str] = None
    bhriguBindhu: Optional[str] = None
    kunda: Optional[str] = None
    sree: Optional[str] = None
    varnada: Optional[str] = None
    maandhi: Optional[str] = None

class DivisionalChartOut(BaseModel):
    factor: int
    label: str
    ascendantHouse: int
    ascendantSignNumber: Optional[int] = None  # absolute sign number (Aries=1)
    ascendantSign: Optional[str] = None  # sign name or glyph+name
    ascendantLongitudeDMS: Optional[str] = None  # e.g., 20° 25' 39"
    ascendantRawLongitudeDeg: Optional[float] = None  # within-sign degrees 0..30
    ascendantAbsoluteLongitude: Optional[float] = None  # 0..360
    ascendantNakshatra: Optional[str] = None
    ascendantNakshatraPada: Optional[int] = None
    ascendantHouseRel: Optional[int] = None  # should be 1 always for convenience
    houses: List[HouseOut]
    # Optionally keep absolute ordering of houses if primary list rotated in future
    planets: List[PlanetOut]
    specialLagna: SpecialLagnaOut
    sphuta: Dict[str, str]

class HoroscopeResponse(BaseModel):
    # Convenience top-level requestId (duplicates meta['requestId']) so simple scripts don't have to dig into meta
    requestId: str | None = None
    meta: Dict[str, Any]
    calendar: Dict[str, Any]
    rasiChart: DivisionalChartOut
    divisionalCharts: List[DivisionalChartOut] = []
    combustion: List[str] | None = None  # planet names combust in D1
    vargottama: List[str] | None = None  # planet names vargottama (D1==D9 sign)
    
    # Panchanga and Transit data (automatically included)
    panchanga: Dict[str, Any] | None = None  # Birth chart panchanga (Tithi, Nakshatra, etc.)
    currentTransits: Dict[str, Any] | None = None  # Current planetary transit positions


class DetailedCalculationItem(BaseModel):
    chart: str | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None
    benefit: str | None = None
    extra: List[str] | None = None
    raw: Any | None = None


class HoroscopeDetailsResponse(BaseModel):
    requestId: str
    language: str
    generatedAt: datetime
    calendar: Dict[str, Any] | None = None
    horoscopeInfo: Dict[str, Any] | None = None
    yogas: List[DetailedCalculationItem] | None = None
    rajaYogas: List[DetailedCalculationItem] | None = None
    yogaCount: int | None = None
    totalYogas: int | None = None
    rajaYogaCount: int | None = None
    totalRajaYogas: int | None = None
    errors: List[str] | None = None

class AgentDispatchResult(BaseModel):
    success: bool
    detail: str
    attempts: int = 0

class AgentRelayRequest(BaseModel):
    requestId: str
    payload: Dict[str, Any] | None = None

# Internal store (simple in-memory for now)
class StoredHoroscope(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: HoroscopeRequest
    response: HoroscopeResponse
    agentDispatched: bool = False
    agentResult: Optional[AgentDispatchResult] = None
    internalHoroscope: Any | None = None  # raw Horoscope instance for further computations

# Dhasa / Panchanga / Match models
class DhasaPeriod(BaseModel):
    dhasaLord: str
    antardashaLord: str  # previously bhuktiLord
    start: str  # ISO date string or raw value from library
    # Optional deeper sub-levels (pratyantardasha, sookshma, prana, deha) as plain names if provided
    pratyantardashaLord: str | None = None
    sookshmaLord: str | None = None
    pranaLord: str | None = None
    dehaLord: str | None = None

class VimsottariDhasaResponse(BaseModel):
    requestId: str
    balance: List[int]  # (years, months, days?) as provided
    periods: List[DhasaPeriod]
    total: int
    returned: int
    # Raw level chains per returned period, e.g. [ ["Budh MD","Budh AD","Budh PD"], ... ]
    chains: Optional[List[List[str]]] = None
    # Full tree expansion (if requested) enumerating every sub-chain up to depth for the included periods
    allChains: Optional[List[List[str]]] = None
    allChainsTruncated: Optional[bool] = None
    # Raw library output (pre-parsing) if requested via query param raw=true
    rawPeriods: Optional[List[Any]] = None
    rawTotal: Optional[int] = None  # full count of library periods
    rawReturned: Optional[int] = None  # number of raw periods included
    # Depth-aware raw periods including deeper lords up to requested depth: [ MD-AD, PD, SD, ..., start ]
    rawPeriodsDepth: Optional[List[List[str]]] = None
    # Flat list of all computed sub-period boundaries with their Julian start (if available)
    rawSubPeriods: Optional[List[dict]] = None  # [{"chain":[...],"startJD":float}]

class GrahaDashaResponse(BaseModel):
    requestId: str
    system: str  # e.g. 'ashtottari', 'yogini', etc.
    periods: List[DhasaPeriod]
    total: int
    returned: int
    includeAntardhasa: bool
    chains: Optional[List[List[str]]] = None

# Jaimini (Chara) Dhasa models
class CharaDhasaItem(BaseModel):
    dhasaRasi: str
    bhuktiRasi: Optional[str] = None
    start: str
    durationYears: float | None = None

class CharaDhasaResponse(BaseModel):
    requestId: str
    periods: List[CharaDhasaItem]
    total: int
    returned: int
    includeAntardhasa: bool
    method: int  # 1 = Parasara/PVN Rao (2 cycles), 2 = KN Rao (single cycle)

# Generic Rasi-based (Jaimini style) dasha response for Sthira, Narayana, Drig etc.
class RasiDashaResponse(BaseModel):
    requestId: str
    system: str  # 'sthira' | 'narayana' | 'drig' | others
    periods: List[CharaDhasaItem]
    total: int
    returned: int
    includeAntardhasa: bool

class TransitPlanet(BaseModel):
    name: str
    longitudeDMS: str
    sign: str
    house: int

class TransitResponse(BaseModel):
    requestId: str
    date: str
    planets: List[TransitPlanet]

class PanchangaResponse(BaseModel):
    requestId: str
    calendar: Dict[str, Any]

class MatchRequest(BaseModel):
    maleNakshatra: str
    femaleNakshatra: str
    system: Optional[str] = 'default'

class MatchResponse(BaseModel):
    maleNakshatra: str
    femaleNakshatra: str
    score: float  # percentage 0-100
    rawScore: float
    maxScore: int
    details: Dict[str, Any]

# Aspects
class AspectEdge(BaseModel):
    source: str
    target: str
    sourceHouse: int
    targetHouse: int
    aspectType: str = 'graha'
    note: Optional[str] = None

class AspectsResponse(BaseModel):
    requestId: str
    edges: List[AspectEdge]
    planetHouseMap: Dict[str,int]

class StrengthResponse(BaseModel):
    requestId: str
    counts: Dict[str,int]
    retrograde: List[str]
    dignities: Dict[str,List[str]]

# Yogas
class YogaItem(BaseModel):
    name: str
    present: bool
    planets: List[str] = []
    detail: Optional[str] = None

class YogasResponse(BaseModel):
    requestId: str
    yogas: List[YogaItem]
    debug: Optional[dict] = None

class SummaryResponse(BaseModel):
    requestId: str
    strength: StrengthResponse | None = None
    yogas: List[YogaItem] = []
    aspectsCount: int = 0
    retrograde: List[str] = []

# Deep strength / analytics models
class DeepStrengthResponse(BaseModel):
    requestId: str
    ashtakavarga: dict | None = None
    shadbala: dict | None = None
    bhavaBala: dict | None = None
    vimsopaka: dict | None = None
    avasthas: dict | None = None
    ishtaPhala: List[float] | None = None
    rashmi: dict | None = None  # subha/uccha rashmi values for deeper calc
    aspects: dict | None = None
    meta: dict | None = None

class BundleResponse(BaseModel):
    requestId: str
    horoscope: HoroscopeResponse | None = None
    yogas: YogasResponse | None = None
    strength: StrengthResponse | None = None
    deepStrength: DeepStrengthResponse | None = None
    summary: SummaryResponse | None = None

class BootstrapRequest(BaseModel):
    requestId: str | None = None
    createIfMissing: bool = True
    bundle: bool = True
    yogasMode: str = 'basic'
    includeDeep: bool = True
    includeDeepAspects: bool = False
    includeDeepPrastara: bool = False
    includeSummary: bool = False
    horoscope: HoroscopeRequest | None = None

class BootstrapResponse(BaseModel):
    requestId: str
    created: bool
    bundle: BundleResponse | None = None
