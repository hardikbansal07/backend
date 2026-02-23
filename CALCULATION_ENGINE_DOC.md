# PyJHora Calculation Engine — Complete Documentation

> Full technical reference for `backend/calculation/calculation-main/` — the Vedic astrology computation engine powering AstroCare AI.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [API Layer (`src/api/`)](#3-api-layer)
4. [Data Models](#4-data-models)
5. [Service Layer — How Horoscopes Are Computed](#5-service-layer)
6. [Complete API Endpoint Reference](#6-complete-api-endpoint-reference)
7. [JHora Library Deep Dive](#7-jhora-library-deep-dive)
8. [Dasha Systems (45 Total)](#8-dasha-systems)
9. [Chart Analysis Modules](#9-chart-analysis-modules)
10. [SVG Chart Rendering](#10-svg-chart-rendering)
11. [Agent Dispatch System](#11-agent-dispatch-system)
12. [Event Tracking](#12-event-tracking)
13. [Caching & Performance](#13-caching--performance)
14. [Configuration & House Systems](#14-configuration--house-systems)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                  app.py (2,184 lines)                        │
│              60+ REST API Endpoints                         │
├─────────────┬──────────────┬────────────────────────────────┤
│ service.py  │  agent.py    │  events.py  │  render.py       │
│ (1,507 LOC) │  (136 LOC)   │  (99 LOC)   │  (158 LOC)      │
│ Computation │  Webhook     │  SQLite     │  SVG Charts      │
│ Engine      │  Dispatch    │  Tracking   │  South/North     │
├─────────────┴──────────────┴────────────────────────────────┤
│                    models.py (370 LOC)                       │
│              25 Pydantic Data Models                        │
├─────────────────────────────────────────────────────────────┤
│                   JHora Library (304 files)                  │
│  ┌──────────┬──────────┬─────────┬──────────┬─────────────┐ │
│  │ chart/   │ dhasa/   │ match/  │transit/  │ prediction/ │ │
│  │ 11 files │ 50 files │ 7 files │ 5 files  │ 5 files     │ │
│  │ 460KB    │ 300KB    │ 2.6MB   │ 91KB     │ 22KB        │ │
│  └──────────┴──────────┴─────────┴──────────┴─────────────┘ │
│  ┌──────────┬──────────┬─────────────────────────────────┐  │
│  │const.py  │ utils.py │ panchanga/ (drik.py + more)     │  │
│  │ 75KB     │ 57KB     │ Swiss Ephemeris Integration     │  │
│  └──────────┴──────────┴─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Swiss Ephemeris (PySwissEph)                    │
│           data/ephe/ — Planetary Ephemeris Files             │
└─────────────────────────────────────────────────────────────┘
```

**Key Stats:**
- Total API file: **97,452 bytes** (2,184 lines)
- Service file: **72,009 bytes** (1,507 lines)
- JHora `charts.py`: **144,302 bytes** (largest single module)
- JHora `yoga.py`: **80,881 bytes** (yoga detection)
- Total Dasha systems: **45** (23 Graha + 22 Rasi)
- Supported languages: **en, hi, ta, te, kn, ml, mr, gu, bn, or**

---

## 2. Directory Structure

```
calculation-main/src/
├── api/                          # REST API Layer
│   ├── app.py                    # FastAPI routes (2,184 lines, 60+ endpoints)
│   ├── models.py                 # 25 Pydantic models (370 lines)
│   ├── service.py                # Core computation engine (1,507 lines)
│   ├── agent.py                  # Agent webhook dispatch (136 lines)
│   ├── events.py                 # SQLite event tracking (99 lines)
│   ├── render.py                 # SVG chart renderer (158 lines)
│   ├── names.py                  # Name/label utilities (5,264 bytes)
│   ├── horo_requests.json        # Persisted request store (42KB)
│   ├── README_API.md             # Brief API readme
│   └── __init__.py               # Package init
│
└── jhora/                        # JHora Vedic Astrology Library
    ├── const.py                  # Constants: planets, signs, nakshatras (75KB)
    ├── utils.py                  # Utilities: Julian Day, DMS, conversions (57KB)
    ├── _package_info.py          # Version info
    │
    ├── data/
    │   ├── ephe/                 # Swiss Ephemeris data files (117 items)
    │   └── world_cities_with_tz.csv  # Place database with timezones
    │
    ├── panchanga/
    │   ├── drik.py               # Core astronomical engine (Swiss Ephemeris wrapper)
    │   ├── pancha_paksha.py      # Pancha Paksha analysis
    │   └── vratha.py             # Vratha (fasting) day calculations
    │
    ├── horoscope/
    │   ├── main.py               # Horoscope class (131KB — master orchestrator)
    │   ├── chart/                # Chart computation (11 files, 460KB total)
    │   │   ├── charts.py         # Divisional charts D1-D60 (144KB)
    │   │   ├── yoga.py           # 100+ yoga detection (80KB)
    │   │   ├── house.py          # House analysis, Drishti (67KB)
    │   │   ├── strength.py       # Shadbala, Bhavabala (51KB)
    │   │   ├── raja_yoga.py      # Raja Yoga detection (38KB)
    │   │   ├── sphuta.py         # 14 Sphuta points (25KB)
    │   │   ├── dosha.py          # Dosha detection (21KB)
    │   │   ├── ashtakavarga.py   # Ashtakavarga scoring (10KB)
    │   │   └── arudhas.py        # Arudha Pada calculation (8KB)
    │   │
    │   ├── dhasa/                # Dasha timing systems (50 files)
    │   │   ├── graha/            # 23 planet-based Dasha systems
    │   │   ├── raasi/            # 22 sign-based Dasha systems
    │   │   ├── annual/           # Mudda + Patyayini annual Dasha
    │   │   └── sudharsana_chakra.py
    │   │
    │   ├── match/                # Marriage compatibility
    │   │   ├── compatibility.py  # Guna Milan scoring (42KB)
    │   │   └── *.csv             # Nakshatra match data (2.5MB+)
    │   │
    │   ├── transit/              # Transit & annual analysis
    │   │   ├── tajaka.py         # Tajaka annual charts (39KB)
    │   │   ├── saham.py          # Arabic Parts/Sahams (29KB)
    │   │   └── tajaka_yoga.py    # Tajaka yogas (22KB)
    │   │
    │   └── prediction/           # Prediction engines
    │       ├── general.py        # General predictions (5KB)
    │       ├── longevity.py      # Longevity analysis (11KB)
    │       └── naadi_marriage.py # Naadi marriage prediction (5KB)
    │
    ├── lang/                     # Multi-language support (44 files)
    ├── ui/                       # UI components (23 files)
    ├── tests/                    # Test suite (7 files)
    └── docs/                     # Documentation (12 files)
```

---

## 3. API Layer

### `app.py` — FastAPI Application (2,184 lines)

**Initialization:**
- Title: `PyJHora API`, Version: `0.1`
- Sets Swiss Ephemeris path to bundled `jhora/data/ephe/`
- Enables outer planets (Uranus/Neptune/Pluto) by default
- CORS: allows all origins (`*`)
- In-memory response cache: 256 entries, 1-hour TTL

**JHora Module Imports (lines 64-87):**
```python
from jhora.horoscope.dhasa.graha import vimsottari
from jhora.horoscope.chart import ashtakavarga, dosha, yoga, raja_yoga
from jhora.horoscope.chart import charts, arudhas, house, sphuta, strength
from jhora.horoscope.match import compatibility
from jhora.horoscope.transit import tajaka, tajaka_yoga, saham
from jhora.horoscope.prediction import general, longevity, naadi_marriage
from jhora.panchanga import pancha_paksha, vratha
```

**Registered Dasha System Maps:**

Graha (10 systems via `_GRAHA_DASHA_MAP`):
`ashtottari`, `yogini`, `shodasottari`, `dwadasottari`, `panchottari`, `sataatbika`, `chathuraaseethi_sama`, `shattrimsa_sama`, `dwisaptati_sama`, `shashtihayani`

Rasi (14 systems via `_RASI_DASHA_MAP`):
`sthira`, `narayana`, `drig`, `yogardha`, `paryaaya`, `brahma`, `mandooka`, `sudasa`, `kalachakra`, `navamsa`, `trikona`, `nirayana`, `chakra`, `kendraadhi_rasi`, `shoola`

---

## 4. Data Models (`models.py` — 370 lines, 25 models)

### Request Models

| Model | Fields | Purpose |
|-------|--------|---------|
| **HoroscopeRequest** | `birthDateTime`, `location`, `ayanamsaMode`, `calcType`, `houseSystem`, `language`, `divisionalFactors`, `sendToAgent`, `compact` + legacy fields | Main horoscope creation |
| **LocationIn** | `place`, `latitude`, `longitude`, `tzOffset` | Location input |
| **AgentRelayRequest** | `requestId`, `payload` | Relay to AI agent |
| **MatchRequest** | `maleNakshatra`, `femaleNakshatra`, `system` | Marriage compatibility |
| **BootstrapRequest** | `requestId`, `createIfMissing`, `bundle`, `yogasMode`, `includeDeep` | Bootstrap all data |

### Response Models

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| **HoroscopeResponse** | `meta`, `calendar`, `rasiChart`, `divisionalCharts[]`, `combustion[]`, `vargottama[]`, `panchanga`, `currentTransits` | Full horoscope |
| **DivisionalChartOut** | `factor`, `label`, `ascendantHouse`, `houses[]`, `planets[]`, `specialLagna`, `sphuta` | Single divisional chart |
| **PlanetOut** | `name`, `house`, `houseRel`, `houseAbs`, `longitudeDMS`, `rawLongitudeDeg`, `retrograde`, `sign`, `nakshatra`, `nakshatraPada`, `dignity`, `isCombust`, `isVargottama`, `charaKaraka`, `absoluteLongitude` | Planet data |
| **HouseOut** | `index`, `items[]`, `signNumber` | House data |
| **SpecialLagnaOut** | `bhava`, `hora`, `ghati`, `vighati`, `pranapada`, `indu`, `bhriguBindhu`, `kunda`, `sree`, `varnada`, `maandhi` | 11 Special Lagnas |
| **DhasaPeriod** | `dhasaLord`, `antardashaLord`, `start`, `pratyantardashaLord`, `sookshmaLord`, `pranaLord` | Up to 6 dasha levels |
| **VimsottariDhasaResponse** | `balance`, `periods[]`, `chains[]`, `rawPeriods[]`, `rawSubPeriods[]` | Vimsottari with depth |
| **CharaDhasaItem** | `dhasaRasi`, `bhuktiRasi`, `start`, `durationYears` | Jaimini Chara |
| **DeepStrengthResponse** | `ashtakavarga`, `shadbala`, `bhavaBala`, `vimsopaka`, `avasthas`, `ishtaPhala`, `rashmi`, `aspects` | Deep analysis |
| **YogaItem** | `name`, `present`, `planets[]`, `detail` | Individual yoga |
| **AspectEdge** | `source`, `target`, `sourceHouse`, `targetHouse`, `aspectType` | Aspect data |
| **BundleResponse** | `horoscope`, `yogas`, `strength`, `deepStrength`, `summary` | Combined data bundle |

---

## 5. Service Layer — How Horoscopes Are Computed

### `service.py` — Core Engine (1,507 lines)

**Key Functions:**

| Function | Lines | Purpose |
|----------|-------|---------|
| `compute_horoscope()` | 897-1297 | **Master computation** — creates JHora Horoscope, builds all charts |
| `_build_chart_output()` | 304-894 | **Chart builder** — extracts 590 lines of planet/house/lagna data |
| `build_detailed_calculations()` | 1375-1435 | Detailed yogas + raja yogas |
| `_lookup_world_city()` | 189-217 | Place → lat/lon/tz resolution |
| `delete_request()` | 1437-1466 | Cleanup stored horoscope |
| `list_requests()` | 1468-1489 | List stored request metadata |

### `compute_horoscope()` Pipeline (400 lines)

```
1. Check cache (hash of request) → Return if exists
2. Validate birthDateTime + location
3. Set language (thread-safe lock)
4. Configure planet list (include Uranus/Neptune/Pluto if enabled)
5. Parse birth data → jhora.panchanga.drik.Date + birth_time string
6. Resolve place → lat/lon/tz via world_cities_with_tz.csv
7. Map house system → internal bhava_madhya_method
   Aliases: equal→2, sripati→3, placidus/kp→4, koch→K, etc.
8. Create JHora Horoscope object:
   Horoscope(place, lat, lon, tz, date, birth_time, ayanamsa, calc_type,
             years, months, sixty_hours, pravesha_type, language, bhava_madhya)
9. Extract calendar_info (Panchanga)
10. Build D1 (Rasi) chart via _build_chart_output(horo, 1)
11. Build divisional charts (D2-D144) via _build_chart_output(horo, factor)
    Default factors: [1,2,3,4,5,7,9,10,12,16,20,24,27,30,36,40,45,60,72,144]
12. Calculate current transits (all 9 planets at current JD)
13. Compute combustion (angular distance from Sun vs combustion limits)
14. Compute vargottama (same sign in D1 and D9)
15. Annotate planets with isCombust, isVargottama flags
16. If compact mode: trim calendar, strip optional planet fields
17. Store in memory + persist request JSON to disk
18. Return StoredHoroscope
```

### `_build_chart_output()` Pipeline (590 lines)

```
1. Get chart_info from horo.chart_info for given divisional factor
2. Parse ascendant house (0-based) from chart_info
3. Build 12 houses: sign mapping, planet occupants
4. For each planet token in each house:
   a. Normalize name → canonical (Sun, Moon, Mars, etc.)
   b. Look up from chart_info: longitude DMS, raw degrees
   c. Detect retrograde status
   d. Resolve sign name from RAASI_LIST
   e. Create PlanetOut object
5. Extract Special Lagnas: Bhava, Hora, Ghati, Vighati, Pranapada,
   Indu, Bhrigu Bindhu, Kunda, Sree, Varnada, Maandi
6. Extract Sphuta points + upagrahas (Gulika, Kaala, Mrityu, etc.)
7. Compute relative houses (rotate so Lagna = House 1)
8. Inject outer planets (Uranus/Neptune/Pluto) if enabled
9. Compute true Ascendant longitude using drik.ascendant()
10. Inject synthetic "Ascendantℒ" as first planet entry
11. Return (DivisionalChartOut, raw chart_info dict)
```

---

## 6. Complete API Endpoint Reference

### Core Horoscope (6 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/horoscope` | Create horoscope (main entry) |
| `GET` | `/api/horoscope/{id}` | Get horoscope (ETag caching) |
| `GET` | `/api/horoscope/{id}/details` | Detailed calculations (yogas, info) |
| `GET` | `/api/horoscope/{id}/render` | SVG chart (D1-D60, South/North style) |
| `GET` | `/api/horoscope` | List all stored horoscopes |
| `DELETE` | `/api/horoscope/{id}` | Delete + cleanup |

### Graha Dasha Systems (12 endpoints)

| Method | Path | System |
|--------|------|--------|
| `GET` | `/api/dhasa/vimsottari` | Vimsottari (depth 1-5, raw mode) |
| `GET` | `/api/dhasa/ashtottari` | Ashtottari (108-year cycle) |
| `GET` | `/api/dhasa/graha/{system}` | Generic: yogini, shodasottari, dwadasottari, panchottari, sataatbika, chathuraaseethi_sama, shattrimsa_sama, dwisaptati_sama, shashtihayani |

### Rasi Dasha Systems (16 endpoints)

| Method | Path | System |
|--------|------|--------|
| `GET` | `/api/dhasa/chara` | Jaimini Chara (Parasara/KN Rao methods) |
| `GET` | `/api/dhasa/sthira` | Sthira |
| `GET` | `/api/dhasa/narayana` | Narayana |
| `GET` | `/api/dhasa/drig` | Drig |
| `GET` | `/api/dhasa/yogardha` | Yogardha |
| `GET` | `/api/dhasa/paryaaya` | Paryaaya |
| `GET` | `/api/dhasa/brahma` | Brahma |
| `GET` | `/api/dhasa/mandooka` | Mandooka |
| `GET` | `/api/dhasa/sudasa` | Sudasa |
| `GET` | `/api/dhasa/kalachakra` | Kalachakra |
| `GET` | `/api/dhasa/navamsa` | Navamsa |
| `GET` | `/api/dhasa/trikona` | Trikona |
| `GET` | `/api/dhasa/chakra` | Chakra |
| `GET` | `/api/dhasa/kendraadhi_rasi` | Kendraadhi Rasi |
| `GET` | `/api/dhasa/shoola` | Shoola |
| `GET` | `/api/dhasa/sudharsana_chakra` | Sudharsana Chakra |

### Annual / Tajaka (4 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tajaka/annual` | Tajaka annual chart for year |
| `GET` | `/api/tajaka/yogas` | Tajaka yogas for year |
| `GET` | `/api/dhasa/annual/mudda` | Mudda annual Dasha |
| `GET` | `/api/dhasa/annual/patyayini` | Patyayini annual Dasha |

### Analysis & Strength (6 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/analyze/shadbala` | 6-fold planetary strength + Ishta/Kashta |
| `GET` | `/api/analyze/bhavabala` | House strength scores |
| `GET` | `/api/analyze/ashtakavarga` | BAV, SAV, Prastara, Sodhya Pindas |
| `GET` | `/api/analyze/vaiseshikamsa` | Vaiseshikamsa (Shodasha Varga) |
| `GET` | `/api/analyze/sphuta` | 14 Sphuta points (Tri, Chatur, Pancha, Prana, Deha, Mrityu, etc.) |
| `GET` | `/api/chart/analysis` | Graha Drishti + Rasi Drishti for any chart |

### Charts, Yogas, Misc (10 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/alt_charts` | Chandra Lagna + Surya Lagna charts |
| `GET` | `/api/bhava_chakra` | Bhava Chakra (house cusps) |
| `GET` | `/api/chart/raja_yoga` | Raja Yoga detection |
| `GET` | `/api/yogas` | Combined Yogas + Raja Yogas |
| `GET` | `/api/aspects` | Graha + Rasi Drishti |
| `GET` | `/api/strength` | Shadbala + Bhavabala combined |
| `GET` | `/api/summary` | Horoscope summary |
| `GET` | `/api/panchanga` | Birth chart Panchanga |
| `GET` | `/api/panchanga/transit` | Transit Panchanga for any date |
| `GET` | `/api/health` | Health check + diagnostics |

### Configuration (4 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/config/outer_planets` | Toggle Uranus/Neptune/Pluto |
| `GET` | `/api/config/outer_planets` | Get outer planets flag |
| `GET` | `/api/house_systems` | List available house systems |
| `GET` | `/api/languages` | List supported languages |

### Agent System (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/relay` | Relay horoscope to AI agent |
| `GET` | `/api/agent/events` | List agent dispatch events |
| `GET` | `/api/agent/events/{id}` | Get event payload/info |

---

## 7. JHora Library Deep Dive

### `const.py` (75,352 bytes) — Constants

Contains all Vedic astrology constants:
- **Planet IDs**: `_SUN=0` through `_KETU=8`, `_URANUS=9`, `_NEPTUNE=10`, `_PLUTO=11`
- **Sign names**: `RAASI_LIST` (12 signs, multi-language)
- **Nakshatra names**: `NAKSHATRA_LIST` (27 nakshatras)
- **Dasha periods**: Vimsottari cycle (Sun=6y, Moon=10y, Mars=7y, etc.)
- **Combustion ranges**: degrees from Sun per planet (normal + retrograde)
- **Exaltation/Debilitation**: sign mappings for each planet
- **House system constants**: `bhaava_madhya_method`, `available_house_systems`
- **Language**: `available_languages` mapping

### `utils.py` (57,161 bytes) — Utility Functions

- `julian_day_number()` — Date to Julian Day
- `to_dms_prec()` — Decimal degrees to DMS
- `set_language()` — Switch language
- `PLANET_NAMES`, `RAASI_LIST`, `NAKSHATRA_LIST` — Current language names
- `get_house_planet_list_from_planet_positions()` — Position → house chart

### `panchanga/drik.py` — Swiss Ephemeris Integration

Core astronomical engine:
- `sidereal_longitude(jd, planet_id)` — Sidereal planet position
- `ascendant(jd, place)` — Calculate precise Ascendant
- `nakshatra_pada(longitude)` — Nakshatra + Pada from longitude
- `set_sideral_planets()` — Enable all planets including outers
- `Date` class — Date representation for calculations
- `_planet_speed_info()` — Speed/retrograde detection

### `horoscope/main.py` (131,203 bytes) — Master Horoscope Class

The `Horoscope` class orchestrates everything:
- Initializes with birth data → computes Julian Day
- Calls `drik.py` for all planetary positions
- Generates `calendar_info` (Panchanga)
- Computes `chart_info` for each divisional chart
- Stores `_vimsottari_balance` for Dasha calculations

---

## 8. Dasha Systems (45 Total)

### Graha (Planet-Based) — 23 Systems

| System | File | Size | Cycle |
|--------|------|------|-------|
| **Vimsottari** | vimsottari.py | 19KB | 120 years |
| Ashtottari | ashtottari.py | 12KB | 108 years |
| Yogini | yogini.py | 8KB | 36 years |
| Shodasottari | shodasottari.py | 9KB | 116 years |
| Dwadasottari | dwadasottari.py | 9KB | 112 years |
| Panchottari | panchottari.py | 9KB | 105 years |
| Sataatbika (Shatabdika) | sataatbika.py | 9KB | 100 years |
| Chathuraaseethi Sama | chathuraaseethi_sama.py | 9KB | 84 years |
| Shattrimsa Sama | shattrimsa_sama.py | 10KB | 36 years |
| Dwisaptati Sama | dwisatpathi.py | 9KB | 72 years |
| Shashtihayani | shastihayani.py | 9KB | 60 years |
| Aayu | aayu.py | 33KB | Longevity |
| Kaala | kaala.py | 7KB | Time-based |
| Tara | tara.py | 7KB | Star-based |
| Naisargika | naisargika.py | 5KB | Natural |
| Karaka | karaka.py | 4KB | Significator |
| Buddhi Gathi | buddhi_gathi.py | 5KB | Intelligence |
| Tithi Ashtottari | tithi_ashtottari.py | 7KB | Tithi-based |
| Tithi Yogini | tithi_yogini.py | 6KB | Tithi Yogini |
| Yoga Vimsottari | yoga_vimsottari.py | 8KB | Yoga-based |
| Karana Chaturaaseethi | karana_chathuraaseethi_sama.py | 5KB | Karana-based |
| Saptharishi Nakshatra | saptharishi_nakshathra.py | 8KB | Sage-star |
| Applicability | applicability.py | 3KB | Which system applies |

### Rasi (Sign-Based) — 22 Systems

| System | File | Size |
|--------|------|------|
| **Chara (Jaimini)** | chara.py | 14KB |
| Narayana | narayana.py | 11KB |
| Kalachakra | kalachakra.py | 9KB |
| Kendraadhi Rasi | kendradhi_rasi.py | 8KB |
| Shoola | shoola.py | 8KB |
| Sudasa | sudasa.py | 6KB |
| Mandooka | mandooka.py | 6KB |
| Nirayana | nirayana.py | 5KB |
| Drig | drig.py | 5KB |
| Moola | moola.py | 5KB |
| Paryaaya | paryaaya.py | 5KB |
| Chakra | chakra.py | 4KB |
| Brahma | brahma.py | 3KB |
| Trikona | trikona.py | 3KB |
| Navamsa | navamsa.py | 3KB |
| Sandhya | sandhya.py | 3KB |
| Varnada | varnada.py | 3KB |
| Tara Lagna | tara_lagna.py | 3KB |
| Sthira | sthira.py | 2KB |
| Yogardha | yogardha.py | 3KB |
| Padhanadhamsa | padhanadhamsa.py | 2KB |
| Lagnamsaka | lagnamsaka.py | 1KB |

---

## 9. Chart Analysis Modules

### `chart/charts.py` (144,302 bytes) — Divisional Charts

Computes D1 through D60+ divisional charts:
- `rasi_chart()` — D1 (birth chart)
- `divisional_chart(jd, place, factor)` — Any divisional
- `vaiseshikamsa_shodhasavarga_of_planets()` — 16-varga analysis

### `chart/yoga.py` (80,881 bytes) — Yoga Detection

`get_yoga_details()` checks 100+ yogas:
- Pancha Mahapurusha (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
- Gajakesari, Budhaditya, Dhana Yogas
- Chandra Yogas (Sunaphaa, Anaphaa, Durudhura, Kemadruma)
- Parivartana Yoga, Viparita Raja Yoga, and many more

### `chart/raja_yoga.py` (38,049 bytes) — Raja Yoga

`get_raja_yoga_details()` — Detects combinations of Kendra + Trikona lords

### `chart/strength.py` (51,122 bytes) — Planetary & House Strength

- `shad_bala()` — 6 components: Sthana, Kaala, Dig, Cheshta, Naisargika, Drik
- `bhava_bala()` — House strength scores
- `_ishta_phala()` — Ishta/Kashta Phala (benefic/malefic quotient)

### `chart/dosha.py` (21,965 bytes) — Dosha Detection

- Manglik Dosha (Mars in 1/2/4/7/8/12)
- Kaal Sarp Dosha (all planets between Rahu-Ketu)
- Other classical doshas

### `chart/sphuta.py` (25,288 bytes) — 14 Sphuta Points

`tri_sphuta`, `chatur_sphuta`, `pancha_sphuta`, `prana_sphuta`, `deha_sphuta`, `mrityu_sphuta`, `sookshma_tri_sphuta`, `beeja_sphuta`, `kshetra_sphuta`, `tithi_sphuta`, `yoga_sphuta`, `yogi_sphuta`, `avayogi_sphuta`, `rahu_tithi_sphuta`

### `chart/house.py` (67,333 bytes) — House Analysis

- `graha_drishti_from_chart()` — Planetary aspects
- `raasi_drishti_from_chart()` — Sign-based aspects
- House strength, planet-house relationships

### `chart/ashtakavarga.py` (10,308 bytes)

- `get_ashtaka_varga()` — BAV (Bhinnashtakavarga) + SAV (Sarvashtakavarga)
- `sodhaya_pindas()` — Rasi Pindas + Graha Pindas

### `match/compatibility.py` (42,787 bytes)

Marriage compatibility (Guna Milan) scoring using Nakshatra-based system. Includes pre-computed data files (`all_nak_pad_boy_girl.csv` — 685KB, South variant 913KB).

### `transit/tajaka.py` (39,437 bytes)

Tajaka annual chart computation — Solar return for any year.

### `prediction/` — Prediction Engines

- `general.py` (5KB) — General life predictions
- `longevity.py` (11KB) — Longevity analysis methods
- `naadi_marriage.py` (5KB) — Naadi system marriage prediction

---

## 10. SVG Chart Rendering (`render.py` — 158 lines)

Two rendering styles:

**South Indian (Circular):**
- Outer circle (r=0.46*size) + inner circle (r=0.18*size)
- House numbers at 30° intervals around circle
- Planets plotted using `absoluteLongitude` → SVG coordinates
- Collision avoidance: shifts overlapping labels down by 14px

**North Indian (Boxed):**
- 4×3 grid of rectangular boxes
- Houses mapped to specific grid positions
- Planets placed inside corresponding house boxes

**Functions:**
- `chart_to_positions(chart, size)` → `{planets: [{name, x, y}], houses: [{index, x, y}]}`
- `render_chart_svg(chart, style, theme, size)` → SVG string
- Theme support: Light (white bg) / Dark (`#0b1220` bg)

---

## 11. Agent Dispatch System (`agent.py` — 136 lines)

Sends computed horoscopes to an external AI agent via webhook:

**Config (env vars):**
- `AGENT_WEBHOOK_URL` — Destination URL
- `AGENT_API_KEY` — Bearer token
- `AGENT_MAX_ATTEMPTS` — Retry limit (default: 5)
- `AGENT_BASE_BACKOFF` — Base delay seconds (default: 1.0)

**Retry Strategy:** Exponential backoff `delay = min(base * 2^(attempt-1), 30) + random(0, 0.25)`

**Payload Modes:**
- `summary` — Calendar snippet + planet positions (compact)
- `bundle` — Rasi + divisionals + dignity + planet count
- `full` — Complete horoscope + yogas + strength + deep strength

---

## 12. Event Tracking (`events.py` — 99 lines)

SQLite-based tracking of agent dispatch events:

**Table: `agent_events`**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| request_id | TEXT | Horoscope request ID |
| created_at | REAL | Unix timestamp |
| last_attempt | REAL | Last retry timestamp |
| attempts | INTEGER | Retry count |
| status | TEXT | pending/delivered/error/failed |
| detail | TEXT | Status message |
| payload | TEXT | Full JSON payload |

---

## 13. Caching & Performance

**In-Memory Response Cache:**
- `OrderedDict` with 256-entry max, 1-hour TTL
- Async lock for thread safety
- ETag-based HTTP caching (304 Not Modified)

**Request Deduplication:**
- Hash of `(birthDateTime, lat, lon, tz, ayanamsa, calcType, houseSystem, language, divisionals)` as cache key
- Same input → instant cache hit (no recomputation)

**Persisted Requests:**
- Request payloads serialized to `horo_requests.json` (42KB)
- Allows lazy recomputation after server restart

**World City Index:**
- Pre-loaded CSV of cities with lat/lon/tz at startup
- Indexed by city name for O(1) lookup
- Fuzzy matching with timezone-aware scoring

---

## 14. Configuration & House Systems

### Supported Ayanamsa Modes

`TRUE_CITRA` (default), `LAHIRI`, and others from Swiss Ephemeris

### Supported House Systems

| Alias | Key | System |
|-------|-----|--------|
| `default` | 1 | Equal Middle |
| `equal` | 2 | Equal Housing |
| `sripati` | 3 | Sri Pati |
| `placidus` / `kp` | 4 | Placidus |
| `koch` | K | Koch |
| `porphyrius` | O | Porphyry |
| `regiomontanus` | R | Regiomontanus |
| `campanus` | C | Campanus |
| `alcabitus` | B | Alcabitus |
| `morinus` | M | Morinus |
| `vehlow` | V | Vehlow |
| `axial` | X | Axial |

### Supported Languages

`en` (English), `hi` (Hindi), `ta` (Tamil), `te` (Telugu), `kn` (Kannada), `ml` (Malayalam), `mr` (Marathi), `gu` (Gujarati), `bn` (Bengali), `or` (Odia)

---

> **Last Updated:** February 2026 | **Total Engine Size:** ~1.5 MB source code + 117 ephemeris data files
