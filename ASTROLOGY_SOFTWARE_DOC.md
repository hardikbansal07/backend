# AstroCare AI — Astrology Software Deep Dive Documentation

> Complete technical documentation of all astrology-related modules, engines, AI agents, and algorithms used in the AstroCare platform.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [PyJHora Calculation Engine](#2-pyjhora-calculation-engine)
3. [Horoscope Data Pipeline](#3-horoscope-data-pipeline)
4. [Deva Agent — Celestial Council](#4-deva-agent--celestial-council)
5. [AstroEngine 2.0 — Love & Domain Analysis](#5-astroengine-20--love--domain-analysis)
6. [R1 Algorithm — Report Generation Council](#6-r1-algorithm--report-generation-council)
7. [Vedic Astrology Concepts Reference](#7-vedic-astrology-concepts-reference)
8. [Calculation Engine API Reference](#8-calculation-engine-api-reference)
9. [Data Compression & Storage](#9-data-compression--storage)
10. [Vertex AI Integration](#10-vertex-ai-integration)

---

## 1. System Overview

The AstroCare astrology software is composed of **4 major modules** that work together:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER (Mobile App / Web)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │       FastAPI Backend            │
              │     (main.py — Orchestrator)     │
              └────┬────────┬──────────┬────────┘
                   │        │          │
          ┌────────▼──┐  ┌──▼──────┐  ┌▼──────────────┐
          │ PyJHora    │  │ Deva    │  │ AstroEngine   │
          │ Calc       │  │ Agent   │  │ 2.0           │
          │ Engine     │  │ (Chat)  │  │ (Love Chat)   │
          │            │  │         │  │               │
          │ SwissEph + │  │ 4-Agent │  │ MainAgent +   │
          │ JHora Lib  │  │ Council │  │ SubAgent +    │
          │            │  │         │  │ HouseMapper   │
          └──────┬─────┘  └────┬────┘  └──────┬────────┘
                 │             │              │
                 │      ┌──────▼──────┐       │
                 │      │  R1 Algo    │       │
                 │      │  (Reports)  │       │
                 │      │  6-Agent    │       │
                 │      │  Council    │       │
                 │      └─────────────┘       │
                 │                            │
          ┌──────▼────────────────────────────▼──────┐
          │           Google Vertex AI                │
          │        (Gemini 2.5 Flash Lite)            │
          └──────────────────────────────────────────┘
```

### Module Summary

| Module | Purpose | Technology | Lines of Code |
|--------|---------|-----------|---------------|
| **PyJHora Engine** | Vedic astrology calculations | Swiss Ephemeris + JHora lib | 2,184+ (API only) |
| **Deva Agent** | Interactive AI chat | AutoGen + Vertex AI | ~900 |
| **AstroEngine 2.0** | Love/domain-specific analysis | Gemini LLM + HouseMapper | ~1,200 |
| **R1 Algorithm** | PDF report generation | AutoGen multi-agent council | ~800 |

---

## 2. PyJHora Calculation Engine

### Location: `backend/calculation/calculation-main/src/`

This is the **core mathematical engine** that performs all Vedic astrology calculations. It wraps the **JHora** library (a Python port of Jagannatha Hora) and the **Swiss Ephemeris** (PySwissEph) for precise planetary position computation.

### 2.1 Architecture

```
calculation-main/src/
├── api/
│   ├── app.py          # FastAPI routes (2,184 lines, 104 functions)
│   ├── models.py       # Pydantic data models (HoroscopeRequest, Response)
│   ├── service.py      # Business logic — compute_horoscope(), build_detailed_calculations()
│   ├── agent.py        # Agent dispatch (AI analysis relay)
│   ├── events.py       # SQLite event tracking
│   └── render.py       # SVG chart rendering
│
├── jhora/              # JHora Library (304 files)
│   ├── const.py        # Constants (planets, signs, nakshatras)
│   ├── utils.py        # Utility functions (Julian Day, conversions)
│   ├── data/
│   │   ├── ephe/       # Swiss Ephemeris data files
│   │   └── world_cities_with_tz.csv  # Place database
│   │
│   ├── panchanga/
│   │   ├── drik.py         # Core astronomical calculations (Swiss Ephemeris wrapper)
│   │   ├── pancha_paksha.py # Pancha Paksha analysis
│   │   └── vratha.py       # Vratha (fasting) calculations
│   │
│   ├── horoscope/
│   │   ├── chart/
│   │   │   ├── charts.py       # Chart computation (D1-D60)
│   │   │   ├── ashtakavarga.py # Ashtakavarga strength
│   │   │   ├── dosha.py        # Dosha detection (Manglik, Kaal Sarp)
│   │   │   ├── yoga.py         # Yoga computation
│   │   │   ├── raja_yoga.py    # Raja Yoga detection
│   │   │   ├── house.py        # House analysis
│   │   │   ├── sphuta.py       # Sphuta points (sensitive degrees)
│   │   │   ├── strength.py     # Planet & house strength (Shadbala, Bhavabala)
│   │   │   └── arudhas.py      # Arudha Pada calculations
│   │   │
│   │   ├── dhasa/
│   │   │   ├── graha/          # Planet-based Dasha systems
│   │   │   │   ├── vimsottari.py   # Vimsottari Dasha (primary)
│   │   │   │   ├── ashtottari.py   # Ashtottari Dasha
│   │   │   │   ├── yogini.py       # Yogini Dasha
│   │   │   │   └── ... (6 more systems)
│   │   │   │
│   │   │   ├── raasi/          # Sign-based Dasha systems
│   │   │   │   ├── chara.py        # Jaimini Chara Dasha
│   │   │   │   ├── narayana.py     # Narayana Dasha
│   │   │   │   ├── sthira.py       # Sthira Dasha
│   │   │   │   └── ... (11 more systems)
│   │   │   │
│   │   │   ├── annual/         # Annual Dasha systems
│   │   │   │   ├── mudda.py        # Mudda Dasha
│   │   │   │   └── patyayini.py    # Patyayini Dasha
│   │   │   │
│   │   │   └── sudharsana_chakra.py  # Sudharsana Chakra
│   │   │
│   │   ├── match/
│   │   │   └── compatibility.py  # Marriage compatibility (Guna Milan)
│   │   │
│   │   ├── transit/
│   │   │   ├── tajaka.py         # Tajaka annual charts
│   │   │   ├── tajaka_yoga.py    # Tajaka yogas
│   │   │   └── saham.py          # Saham (Lots)
│   │   │
│   │   └── prediction/
│   │       ├── general.py        # General predictions
│   │       ├── longevity.py      # Longevity analysis
│   │       └── naadi_marriage.py # Naadi marriage prediction
│   │
│   └── ...
```

### 2.2 How a Horoscope is Calculated

**Input (HoroscopeRequest):**
```json
{
  "birthDateTime": {
    "year": 1990, "month": 5, "day": 15,
    "hour": 7, "minute": 30, "second": 0
  },
  "latitude": 13.0827,
  "longitude": 80.2707,
  "timezoneOffset": 5.5,
  "placeName": "Chennai",
  "ayanamsa": "Lahiri",
  "houseSystem": "Placidus",
  "sendToAgent": false
}
```

**Calculation Pipeline:**

```
1. Parse birth data → Convert to Julian Day Number (JD)
2. Set Swiss Ephemeris path → Load ephemeris data files
3. Set Ayanamsa → Calculate sideral offset (Lahiri default: ~24°)
4. Calculate planetary positions → Sun through Ketu (+ optional Uranus/Neptune/Pluto)
5. Compute Ascendant (Lagna) → Based on birth time + location
6. Map planets to houses (1-12) relative to Ascendant
7. Calculate Nakshatras → 27 divisions of zodiac, Pada (quarter)
8. Compute Planetary Dignity → Exalted/Debilitated/Own Sign/Enemy Sign
9. Generate Divisional Charts → D1 (Rasi) through D60
10. Calculate Vimsottari Dasha balance → Based on Moon's Nakshatra
11. Compute Panchanga → Tithi, Nakshatra, Yoga, Karana, Vara
12. Detect Yogas → Pancha Mahapurusha, Gajakesari, etc.
13. Detect Doshas → Manglik, Kaal Sarp, etc.
14. Calculate Strength → Shadbala (6 sources), Bhavabala (house strength)
15. Generate SVG chart rendering → South/North/East Indian styles
```

**Output Structure (HoroscopeResponse):**
```json
{
  "meta": {
    "requestId": "uuid-xxx",
    "computedAt": "2026-02-15T00:00:00Z",
    "ayanamsa": "Lahiri",
    "houseSystem": "Placidus"
  },
  "rasiChart": {
    "ascendantHouse": 3,
    "houses": [
      {
        "index": 1,
        "sign": "Gemini",
        "items": ["Sun", "Mercury"]
      }
    ],
    "planets": [
      {
        "name": "Sun",
        "sign": "Aries",
        "signIndex": 0,
        "house": 11,
        "longitudeDMS": "1° 25' 30\"",
        "rawLongitude": 1.425,
        "nakshatra": "Ashwini",
        "nakshatraPada": 1,
        "isRetrograde": false,
        "dignity": "Exalted"
      }
    ],
    "specialLagna": { ... },
    "sphuta": { ... }
  },
  "divisionalCharts": [
    { "factor": 9, "label": "Navamsa (D9)", ... },
    { "factor": 10, "label": "Dasamsa (D10)", ... }
  ],
  "vimsottariDasha": [ ... ],
  "panchanga": { ... }
}
```

### 2.3 Supported Calculations

#### Planets (Grahas)

| # | Planet | Sanskrit | Role |
|---|--------|----------|------|
| 0 | Sun | Surya | Soul, father, authority |
| 1 | Moon | Chandra | Mind, mother, emotions |
| 2 | Mars | Mangal | Energy, courage, land |
| 3 | Mercury | Budha | Intelligence, communication |
| 4 | Jupiter | Guru | Wisdom, wealth, children |
| 5 | Venus | Shukra | Love, luxury, arts |
| 6 | Saturn | Shani | Discipline, karma, delays |
| 7 | Rahu | — | Obsession, foreign, unconventional |
| 8 | Ketu | — | Detachment, spirituality, past karma |
| 9* | Uranus | — | Innovation (optional) |
| 10* | Neptune | — | Intuition (optional) |
| 11* | Pluto | — | Transformation (optional) |

*Outer planets toggleable via `POST /api/config/outer_planets`*

#### Zodiac Signs (Rashis)

| # | Sign | Element | Ruler |
|---|------|---------|-------|
| 0 | Aries | Fire | Mars |
| 1 | Taurus | Earth | Venus |
| 2 | Gemini | Air | Mercury |
| 3 | Cancer | Water | Moon |
| 4 | Leo | Fire | Sun |
| 5 | Virgo | Earth | Mercury |
| 6 | Libra | Air | Venus |
| 7 | Scorpio | Water | Mars |
| 8 | Sagittarius | Fire | Jupiter |
| 9 | Capricorn | Earth | Saturn |
| 10 | Aquarius | Air | Saturn |
| 11 | Pisces | Water | Jupiter |

#### Nakshatras (27 Lunar Mansions)

| # | Nakshatra | Ruler | Degree Range |
|---|-----------|-------|-------------|
| 1 | Ashwini | Ketu | 0°00' – 13°20' Aries |
| 2 | Bharani | Venus | 13°20' – 26°40' Aries |
| 3 | Krittika | Sun | 26°40' Aries – 10°00' Taurus |
| 4 | Rohini | Moon | 10°00' – 23°20' Taurus |
| 5 | Mrigashira | Mars | 23°20' Taurus – 6°40' Gemini |
| 6 | Ardra | Rahu | 6°40' – 20°00' Gemini |
| 7 | Punarvasu | Jupiter | 20°00' Gemini – 3°20' Cancer |
| 8 | Pushya | Saturn | 3°20' – 16°40' Cancer |
| 9 | Ashlesha | Mercury | 16°40' – 30°00' Cancer |
| 10 | Magha | Ketu | 0°00' – 13°20' Leo |
| 11 | Purva Phalguni | Venus | 13°20' – 26°40' Leo |
| 12 | Uttara Phalguni | Sun | 26°40' Leo – 10°00' Virgo |
| 13 | Hasta | Moon | 10°00' – 23°20' Virgo |
| 14 | Chitra | Mars | 23°20' Virgo – 6°40' Libra |
| 15 | Swati | Rahu | 6°40' – 20°00' Libra |
| 16 | Vishakha | Jupiter | 20°00' Libra – 3°20' Scorpio |
| 17 | Anuradha | Saturn | 3°20' – 16°40' Scorpio |
| 18 | Jyeshtha | Mercury | 16°40' – 30°00' Scorpio |
| 19 | Mula | Ketu | 0°00' – 13°20' Sagittarius |
| 20 | Purva Ashadha | Venus | 13°20' – 26°40' Sagittarius |
| 21 | Uttara Ashadha | Sun | 26°40' Sagittarius – 10°00' Capricorn |
| 22 | Shravana | Moon | 10°00' – 23°20' Capricorn |
| 23 | Dhanishta | Mars | 23°20' Capricorn – 6°40' Aquarius |
| 24 | Shatabhisha | Rahu | 6°40' – 20°00' Aquarius |
| 25 | Purva Bhadrapada | Jupiter | 20°00' Aquarius – 3°20' Pisces |
| 26 | Uttara Bhadrapada | Saturn | 3°20' – 16°40' Pisces |
| 27 | Revati | Mercury | 16°40' – 30°00' Pisces |

#### Divisional Charts (Varga Charts)

| Chart | Name | Division | What it Shows |
|-------|------|----------|---------------|
| D1 | Rasi | 1 | Overall life, body, general fortune |
| D2 | Hora | 2 | Wealth and financial prosperity |
| D3 | Drekkana | 3 | Siblings, courage, short travels |
| D4 | Chaturthamsa | 4 | Property, home, fixed assets |
| D5 | Panchamsa | 5 | Spiritual merit, past life |
| D7 | Saptamsa | 7 | Children, progeny |
| D9 | Navamsa | 9 | **Marriage, spouse, dharma** (most important after D1) |
| D10 | Dasamsa | 10 | **Career, profession, status** |
| D12 | Dwadasamsa | 12 | Parents, lineage |
| D16 | Shodasamsa | 16 | Vehicles, comforts, luxuries |
| D20 | Vimsamsa | 20 | Spiritual progress, worship |
| D24 | Chaturvimsamsa | 24 | Education, learning |
| D27 | Bhamsa | 27 | Physical strength, stamina |
| D30 | Trimsamsa | 30 | **Health, misfortunes, evils** |
| D40 | Khavedamsa | 40 | Auspicious/inauspicious effects |
| D45 | Akshavedamsa | 45 | General well-being |
| D60 | Shashtiamsa | 60 | Past life karma (finest division) |

#### Dasha Systems (Timing Predictions)

**Graha (Planet-based) Dasha Systems:**

| System | Total Cycle | Description |
|--------|-------------|-------------|
| **Vimsottari** | 120 years | Primary system — based on Moon's Nakshatra |
| Ashtottari | 108 years | Alternative — used when Rahu in Kendra/Trikona |
| Yogini | 36 years | Simple — 8 Yogini energies |
| Shodashottari | 116 years | Rare — 16 subdivisions |
| Dwadasottari | 112 years | 12-based cycle |
| Panchottari | 105 years | 5-based cycle |
| Shatabdika | 100 years | Century-based |
| Chaturashiti Sama | 84 years | Equal 84-year cycle |
| Dwisaptati Sama | 72 years | 72-year cycle |
| Shashtihayani | 60 years | 60-year cycle |

**Rasi (Sign-based) Dasha Systems:**

| System | Description |
|--------|-------------|
| **Chara (Jaimini)** | Sign-based — Parasara/KN Rao methods |
| Narayana | From Narayana (Vishnu) — sign periods |
| Sthira | Fixed periods per sign |
| Drig | Sight-based (aspects) |
| Yogardha | Half-yoga periods |
| Paryaaya | Cyclic rotation |
| Brahma | Named after Brahma |
| Mandooka | Frog-leap movement |
| Sudasa | Ten-based |
| Kalachakra | Wheel of time |
| Navamsa | D9-based sign periods |
| Trikona | Triangle-based |
| Chakra | Wheel movement |
| Kendraadhi Rasi | Kendra-priority |
| Shoola | Trident-based |

**Vimsottari Dasha Depth Levels:**
```
Level 1: Mahadasha (MD)     — 7-20 years each
Level 2: Antardasha (AD)    — Months to years
Level 3: Pratyantardasha (PD) — Weeks to months
Level 4: Sookshma Dasha (SD)  — Days to weeks
Level 5: Prana Dasha (PAD)    — Hours to days
```

**Annual Dasha Systems:**
- **Mudda Dasha** — Annual planetary periods
- **Patyayini Dasha** — Annual progression

---

## 3. Horoscope Data Pipeline

### Files: `horoscope_service.py` + `compression_service.py`

After the PyJHora engine computes a horoscope, the data goes through a **compression and storage pipeline** before being stored in MongoDB:

```
PyJHora Engine (100+ KB JSON)
    │
    ▼
Compression Service
    │ ├── Map planet names → 2-char codes (Sun→Su, Moon→Mo)
    │ ├── Map sign names → 3-char codes (Aries→Ari, Taurus→Tau)
    │ ├── Round all floats to 2 decimal places
    │ ├── Clean calendar strings
    │ ├── Compress Dasha data (remove redundant fields)
    │ └── Compress chart data (minimize JSON)
    │
    ▼
Chunk Splitter
    │ ├── Splits compressed data into 500KB chunks
    │ └── Each chunk stored as separate MongoDB document
    │
    ▼
MongoDB Storage
    ├── horoscopes collection (index entry: user_email + request_id)
    └── horoscope_chunks collection (data chunks: user_email + request_id + chunk_index)
```

### Compression Mappings

**Planet Short Codes:**
```
Sun → Su    Moon → Mo    Mars → Ma    Mercury → Me
Jupiter → Ju    Venus → Ve    Saturn → Sa
Rahu → Ra    Ketu → Ke    Ascendant → As
```

**Sign Short Codes:**
```
Aries → Ari      Taurus → Tau     Gemini → Gem     Cancer → Can
Leo → Leo        Virgo → Vir      Libra → Lib      Scorpio → Sco
Sagittarius → Sag  Capricorn → Cap  Aquarius → Aqu  Pisces → Pis
```

### Storage Benefits
- **Raw horoscope** data: ~100-300 KB
- **Compressed**: ~30-80 KB
- **Per chunk**: Max 500 KB (stays within MongoDB document limit)
- **Retrieval**: Chunks are reassembled on read

---

## 4. Deva Agent — Celestial Council

### Location: `backend/deva-agent-deva_wow/deva-agent/`
### Integrated via: `backend/deva_routes.py`

The Deva Agent is the **primary AI chat system** — when a user asks an astrology question, this module handles it.

### 4.1 Council Architecture

```
User Question: "Will I get promoted this year?"
     │
     ▼
┌─────────────────────────────────────────────┐
│          RoundRobinGroupChat (4 turns)       │
│                                              │
│  Turn 1: LagnaPati (The Ascendant Architect) │
│  ├── Analyzes D1 chart structure             │
│  ├── Checks planet dignity & strength        │
│  └── Reports: "10th house lord is strong..." │
│                                              │
│  Turn 2: KalaPurusha (The Time Keeper)       │
│  ├── Checks current Vimshottari Dasha        │
│  ├── Compares dasha dates to TODAY           │
│  └── Reports: "Saturn MD running until..."   │
│                                              │
│  Turn 3: VargaVizier (The Divisional Expert) │
│  ├── Analyzes D10 (Career) chart             │
│  ├── Checks planet positions in D10          │
│  └── Reports: "D10 shows strong Jupiter..."  │
│                                              │
│  Turn 4: MahaRishi (The Synthesizer)         │
│  ├── Reads all 3 specialist reports          │
│  ├── Weighs conflicting information          │
│  ├── Synthesizes final coherent answer       │
│  └── Speaks as "Astro Care AI"               │
│                                              │
└─────────────────────────────────────────────┘
     │
     ▼
Final Response → "Based on your chart, the 10th house
indicates strong career progression. Currently running
Saturn Mahadasha which favors hard work..."
```

### 4.2 Agent Specializations

| Agent | Focus | Chart Data Used | Knowledge Base |
|-------|-------|----------------|----------------|
| **LagnaPati** | Ascendant, body, general fortune | D1 (Rasi chart) | `d1_lagna_rules.md` — Pancha Mahapurusha Yoga, Dig Bala, house strength |
| **KalaPurusha** | Timing, periods, transits | Vimsottari Dasha, transit data | `dasha_logic.md` — Dasha interpretation, time anchoring |
| **VargaVizier** | Career (D10), Marriage (D9) | Divisional charts | Specialized varga analysis rules |
| **MahaRishi** | Synthesis & final verdict | All above + context | Synthesizer — weighs evidence, resolves conflicts |

### 4.3 Tool Capabilities

Agents are not just LLM chatbots — they have **active tools** to verify calculations:

| Tool | Function | Description |
|------|----------|-------------|
| `calculate_varga_positions` | Check Vargottama status (planet in same sign in D1 and D9) |
| `get_current_dasha` | Calculate which Mahadasha/Antardasha is currently running |
| `check_divisional_strength` | Find planet's position in any divisional chart |

### 4.4 Integration Flow (via `deva_routes.py`)

```python
# 1. User sends chat request
POST /calc/api/v1/deva/chat
Body: { "question": "Will I get promoted?" }

# 2. Backend flow:
a. Check user credits (≥1 required)
b. Deduct 1 credit
c. Fetch compressed horoscope from MongoDB
d. Reconstruct full chart data
e. Fetch last 5 conversations for context
f. Build system context with chart data + birth details + conversation history
g. Run Deva Agent council (4 agents via Vertex AI)
h. Store conversation in MongoDB
i. Return response + credits_remaining

# 3. Response format:
{
  "response": "🌟 **To The Point**\nBased on your chart...\n\n💡 **Advice**\n...\n\n✨ *What else would you like to know?*",
  "credits_remaining": 4,
  "request_id": "uuid-xxx"
}
```

### 4.5 Response Format

Every response follows a structured template:
```
🌟 **To The Point** → Direct, concise answer
💡 **Advice** → Practical remedies and guidance  
✨ *Closing Question* → Engagement prompt for follow-up
```

### 4.6 Multi-Language Support

The system supports responses in multiple languages:
- English, Hindi (हिंदी), Telugu (తెలుగు), Tamil (தமிழ்), Kannada (ಕನ್ನಡ)
- Bengali (বাংলা), Marathi (मराठी), Gujarati (ગુજરાતી)
- User's preferred language is stored in their profile

---

## 5. AstroEngine 2.0 — Love & Domain Analysis

### Location: `backend/astroEngine-2.0/astroEngine-2.0/`
### Integrated via: `backend/love_chat_routes.py`

AstroEngine 2.0 is a specialized module for **domain-specific astrology analysis**, particularly love and relationships.

### 5.1 Architecture

```
User Query: "Will my crush say yes to me?"
    │
    ▼
MainAgent (Orchestrator)
    │
    ├── 1. Intent Detection
    │   ├── Keyword matching (fast): "crush" → Dating domain
    │   └── LLM fallback (slow): If no keywords match
    │
    ├── 2. Domain Pattern Selection
    │   └── Load "Dating" pattern from patterns.json
    │       ├── Focus houses: [5, 7, 8, 11]
    │       ├── Key planets: [Venus, Mars, Moon]
    │       └── Charts: [D1, D9]
    │
    ├── 3. Data Extraction (HouseMapper)
    │   ├── Extract planets in houses 5, 7, 8, 11
    │   ├── Get Venus, Mars, Moon positions
    │   ├── Pull D9 chart data
    │   ├── Extract Panchanga
    │   ├── Check Vargottama status
    │   ├── Check Combustion
    │   └── Extract Chara Karakas
    │
    └── 4. SubAgent Analysis
        ├── Build structured prompt with extracted data
        ├── Send to Gemini LLM
        └── Return natural language prediction
```

### 5.2 Supported Domains (9 total)

| Domain | Focus Houses | Key Planets | Primary Charts | Example Questions |
|--------|-------------|-------------|----------------|-------------------|
| **Dating** | 5, 7, 8, 11 | Venus, Mars, Moon | D1, D9 | "Will my crush say yes?" |
| **Marriage** | 1, 2, 7, 8, 12 | Venus, Jupiter, Mars | D1, D9 | "When will I get married?" |
| **Career** | 1, 2, 6, 10, 11 | Saturn, Sun, Jupiter | D1, D10 | "Will I get a promotion?" |
| **Children** | 1, 5, 9, 11 | Jupiter, Sun, Moon | D1, D7 | "Can I have children?" |
| **Education** | 1, 2, 4, 5, 9 | Mercury, Jupiter, Moon | D1, D24 | "Will I pass the exam?" |
| **Health** | 1, 6, 8, 12 | Sun, Moon, Mars, Saturn | D1, D30 | "What health issues do I face?" |
| **Wealth** | 1, 2, 5, 9, 11 | Jupiter, Venus, Mercury | D1, D9 | "Will I become rich?" |
| **Spirituality** | 1, 5, 8, 9, 12 | Jupiter, Ketu, Saturn | D1, D9, D12 | "What is my spiritual path?" |
| **General** | All | All | D1, D9 | "What is my life path?" |

### 5.3 HouseMapper — Intelligent Data Extraction

The HouseMapper (`house_mapper.py`, 18,059 bytes) is the **core innovation** of AstroEngine 2.0. Instead of sending the entire horoscope to the LLM, it:

1. **Identifies relevant houses** based on the detected domain
2. **Extracts only relevant planetary data** for those houses
3. **Includes divisional chart positions** for additional depth
4. **Adds contextual data**: Panchanga, Vargottama, Combustion, Chara Karakas

This reduces token usage by ~70% while improving answer quality.

### 5.4 Data Extracted for Analysis

| Data Type | Details |
|-----------|---------|
| **Planetary positions** | Sign, house, degree, nakshatra, pada |
| **Planetary strength** | Dignity (exalted/debilitated/own sign) |
| **Retrograde status** | Identifies retrograde planets |
| **House occupants** | Planets in each relevant house |
| **Divisional charts** | D1, D5, D7, D9, D10, D12, D24, D30 |
| **Panchanga** | Tithi, Nakshatra, Yoga, Karana |
| **Special Yogas** | Vargottama, Combustion |
| **Chara Karakas** | Atma Karaka, Amatya Karaka, etc. |
| **Current transits** | If available in horoscope data |

### 5.5 Configuration Files

**`patterns.json`** (3,180 bytes) — Defines domain patterns:
```json
{
  "dating": {
    "houses": [5, 7, 8, 11],
    "planets": ["Venus", "Mars", "Moon"],
    "charts": ["D1", "D9"],
    "keywords": ["crush", "love", "dating", "romance", "girlfriend", "boyfriend"],
    "guidance": "Focus on 5th house (romance) and 7th house (partnerships)..."
  }
}
```

**`planet_roles.json`** (12,228 bytes) — Role of each planet in each domain:
```json
{
  "Venus": {
    "dating": "Primary karaka for love and attraction",
    "marriage": "Karaka for marriage and spouse",
    "career": "Arts, beauty, luxury industries"
  }
}
```

**`chart_house_mapping.json`** (14,629 bytes) — House significance across charts.

---

## 6. R1 Algorithm — Report Generation Council

### Location: `backend/r1_algo/`
### Integrated via: `backend/routers/report_routes.py`

The R1 Algorithm generates **comprehensive PDF relationship reports** using a multi-agent AI council.

### 6.1 Architecture

```
r1_algo/
├── __init__.py          # Entry point: generate_report()
├── agents/
│   ├── council.py       # Creates the 6-agent RoundRobinGroupChat
│   └── prompts/
│       └── master_prompt.md  # R1 Orchestrator's system prompt
├── core/
│   ├── loader.py              # DataLoader — loads chart data into structured format
│   ├── constants.py           # Astrological constants
│   ├── engine.py              # Base engine class
│   ├── timing_engine.py       # Marriage timing analysis (12,477 bytes)
│   ├── spouse_nature_engine.py  # Spouse description engine (4,935 bytes)
│   ├── spouse_meeting_place_engine.py  # Direction/distance engine (5,150 bytes)
│   ├── love_vs_arranged_engine.py  # Love vs Arranged analysis (6,385 bytes)
│   └── tools_data.py         # Chart data retrieval tool
├── config/
│   └── settings.py    # Model client configuration
└── utils/
    └── helpers.py     # Load prompts from markdown files
```

### 6.2 The R1 Council (6 Agents)

| Agent | Role | Tool | Description |
|-------|------|------|-------------|
| **R1_Orchestrator** | Manager | `retrieve_chart_data` | Routes questions to specialists, synthesizes final report |
| **RupaMaya** | Physical Appearance | `SpouseNatureEngine` | Analyzes 7th house lord → complexion, height, body type |
| **DikPala** | Location & Distance | `SpouseMeetingPlaceEngine` | Direction (NSEW), distance (km), meeting context |
| **NamaKarana** | Name Analysis | `SpouseNatureEngine` | Name initials and sounds based on Nakshatra |
| **KalaVidya** | Timing Expert | `TimingEngine` | Marriage timing (Dasha + transits → score 0-8) |
| **SambandaVidya** | Relationship Type | `LoveVsArrangedEngine` | Love marriage vs arranged marriage prediction |

### 6.3 Report Sections

The R1 report is divided into **4 sections**, each generated by consulting the council:

| Section | Question | Agents Used |
|---------|----------|-------------|
| **1. The Timing Question** | "When will I meet my partner? At what age will I marry?" | KalaVidya → R1_Orchestrator |
| **2. The Identity Question** | "What will my spouse look like? What profession?" | RupaMaya + DikPala → R1_Orchestrator |
| **3. Love vs. Arranged** | "Will it be love or arranged marriage?" | SambandaVidya → R1_Orchestrator |
| **4. Life After Marriage** | "What will married life be like?" | SambandaVidya → R1_Orchestrator |

### 6.4 Timing Engine (Scoring System)

The `TimingEngine` scores marriage timing probability using **8 classical parameters**:

| # | Parameter | What it Checks | Score |
|---|-----------|----------------|-------|
| 1 | Vimshottari MD | Is current Mahadasha lord a marriage significator? | 0 or 1 |
| 2 | Vimshottari AD | Is Antardasha lord a marriage significator? | 0 or 1 |
| 3 | Chara Dasha | Is Chara Antardasha in a marriage sign? | 0 or 1 |
| 4 | Saturn Transit | Is Saturn transiting a marriage-relevant house? | 0 or 1 |
| 5 | Jupiter Transit | Is Jupiter aspecting 7th house? | 0 or 1 |
| 6 | Lagna Lord Transit | Is ascendant lord in angular house? | 0 or 1 |
| 7 | 7th Lord Transit | Is 7th lord transiting strongly? | 0 or 1 |
| 8 | Sun Transit | Is Sun supporting the timing? | 0 or 1 |

**Score Interpretation:**
- **6-8**: Very strong → Marriage likely in this period
- **4-5**: Moderate → Possibility exists
- **1-3**: Weak → Less likely in this period
- **0**: No indicators → Unlikely now

### 6.5 Report Generation Pipeline

```
1. User → POST /calc/api/v1/reports/generate { "report_type": "full" }
2. Background task starts:
   a. Fetch latest horoscope from MongoDB
   b. Initialize DataLoader with chart data
   c. Build Vertex AI model client
   d. Create R1 Council (6 agents)
   e. For each section:
      │ ├── Build section-specific prompt with chart context
      │ ├── Run council (up to 10 turns of agent discussion)
      │ └── Extract R1_Orchestrator's final answer
   f. Compile all sections into Markdown
   g. Convert Markdown → PDF (ReportLab)
   h. Upload PDF to Supabase Storage
   i. Return download URL
3. User polls → GET /calc/api/v1/reports/status/{job_id}
4. Download PDF from URL
```

---

## 7. Vedic Astrology Concepts Reference

### 7.1 Houses (Bhavas) — Life Areas

| House | Name | Rules Over |
|-------|------|-----------|
| 1st | Lagna/Tanu | Self, body, personality, appearance |
| 2nd | Dhana | Wealth, family, speech, early education |
| 3rd | Sahaja | Siblings, courage, short travels, communication |
| 4th | Sukha | Mother, home, property, vehicles, happiness |
| 5th | Putra | Children, romance, creativity, past life merit |
| 6th | Ripu | Enemies, disease, debts, service, competition |
| 7th | Kalatra | **Marriage, spouse, partnerships, business** |
| 8th | Mruthyu | Death, longevity, secrets, occult, inheritance |
| 9th | Dharma | Luck, father, religion, higher education, long travels |
| 10th | Karma | **Career, profession, status, government** |
| 11th | Labha | Gains, income, friends, elder siblings, desires |
| 12th | Vyaya | Losses, foreign lands, spirituality, moksha, expenses |

### 7.2 Panchanga (Five Elements of Time)

| Element | Description |
|---------|-------------|
| **Tithi** | Lunar day (30 tithis per month — waxing/waning) |
| **Vara** | Day of the week (each ruled by a planet) |
| **Nakshatra** | Moon's position in 27 lunar mansions |
| **Yoga** | Sun-Moon angular relationship (27 types) |
| **Karana** | Half of a Tithi (11 types, 60 per month) |

### 7.3 Planetary Dignity

| Status | Meaning | Strength |
|--------|---------|----------|
| **Exalted (Uchcha)** | Planet in its strongest sign | ★★★★★ |
| **Moolatrikona** | Planet in its executive sign | ★★★★ |
| **Own Sign (Swakshetra)** | Planet in the sign it rules | ★★★★ |
| **Friend's Sign** | Planet in a friendly sign | ★★★ |
| **Neutral Sign** | Planet in a neutral sign | ★★ |
| **Enemy's Sign** | Planet in an unfriendly sign | ★ |
| **Debilitated (Neecha)** | Planet in its weakest sign | ☆ |

### 7.4 Key Yogas (Planetary Combinations)

| Yoga | Formed When | Effect |
|------|-------------|--------|
| **Gajakesari** | Jupiter in Kendra from Moon | Wisdom, wealth, fame |
| **Budhaditya** | Sun + Mercury conjunction | Intelligence, communication |
| **Pancha Mahapurusha** | Mars/Mercury/Jupiter/Venus/Saturn in own/exalted sign in Kendra | Exceptional personality |
| **Dhana Yoga** | Wealth house lords connected | Financial prosperity |
| **Raja Yoga** | Kendra + Trikona lords connected | Power, authority, success |
| **Kaal Sarp Dosha** | All planets between Rahu-Ketu axis | Obstacles, delays |
| **Manglik Dosha** | Mars in 1st/2nd/4th/7th/8th/12th house | Marriage challenges |

### 7.5 Ashtakavarga

A **scoring system** where each planet gets points (0-8) in each sign based on the positions of other planets. Used for:
- Transit strength prediction
- House strength assessment
- Marriage timing confirmation

### 7.6 Shadbala (Six Sources of Strength)

| Bala | Type | What it Measures |
|------|------|------------------|
| Sthana Bala | Positional | Dignity, direction, house placement |
| Dig Bala | Directional | Angular house strength |
| Kala Bala | Temporal | Day/night, hora, year lord strength |
| Chesta Bala | Motional | Speed, retrograde effect |
| Naisargika Bala | Natural | Inherent strength of planet |
| Drik Bala | Aspectual | Strength from aspects received |

---

## 8. Calculation Engine API Reference

### Complete Endpoint List (60+ endpoints)

#### Core Horoscope

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/horoscope` | **Create new horoscope** (main entry point) |
| GET | `/api/horoscope/{id}` | Retrieve computed horoscope (with ETag caching) |
| GET | `/api/horoscope/{id}/details` | Detailed calculations (Yogas, Raja Yogas, etc.) |
| GET | `/api/horoscope/{id}/render` | SVG chart rendering (D1-D60, South/North/East style) |
| GET | `/api/horoscope` | List all computed horoscopes |
| DELETE | `/api/horoscope/{id}` | Delete horoscope + cleanup |

#### Dasha Systems

| Method | Path | System |
|--------|------|--------|
| GET | `/api/dhasa/vimsottari` | Vimsottari (depth 1-5) |
| GET | `/api/dhasa/chara` | Jaimini Chara (Parasara/KN Rao) |
| GET | `/api/dhasa/ashtottari` | Ashtottari |
| GET | `/api/dhasa/graha/{system}` | Generic graha dasha (yogini, shodashottari, etc.) |
| GET | `/api/dhasa/sthira` | Sthira |
| GET | `/api/dhasa/narayana` | Narayana |
| GET | `/api/dhasa/drig` | Drig |
| GET | `/api/dhasa/yogardha` | Yogardha |
| GET | `/api/dhasa/paryaaya` | Paryaaya |
| GET | `/api/dhasa/brahma` | Brahma |
| GET | `/api/dhasa/mandooka` | Mandooka |
| GET | `/api/dhasa/sudasa` | Sudasa |
| GET | `/api/dhasa/kalachakra` | Kalachakra |
| GET | `/api/dhasa/navamsa` | Navamsa |
| GET | `/api/dhasa/trikona` | Trikona |
| GET | `/api/dhasa/chakra` | Chakra |
| GET | `/api/dhasa/kendraadhi_rasi` | Kendraadhi Rasi |
| GET | `/api/dhasa/shoola` | Shoola |
| GET | `/api/dhasa/sudharsana_chakra` | Sudharsana Chakra |

#### Annual/Tajaka Systems

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tajaka/annual` | Tajaka annual chart for a specific year |
| GET | `/api/tajaka/yogas` | Tajaka yogas for a specific year |
| GET | `/api/dhasa/annual/mudda` | Mudda Dasha for a year |
| GET | `/api/dhasa/annual/patyayini` | Patyayini Dasha for a year |

#### Analysis & Strength

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analysis/chart` | Chart analysis (planet strengths, aspects) |
| GET | `/api/analysis/strength` | Planetary strength overview |
| GET | `/api/analysis/shadbala` | Shadbala (6-fold strength calculation) |
| GET | `/api/analysis/bhavabala` | Bhavabala (house strength) |
| GET | `/api/analysis/ashtakavarga` | Ashtakavarga scores |
| GET | `/api/analysis/vaiseshikamsa` | Vaiseshikamsa analysis |
| GET | `/api/analysis/sphuta` | Sphuta points (sensitive degrees) |

#### Charts & Yogas

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/alt_charts` | Alternative lagnas (Chandra, Surya) |
| GET | `/api/bhava_chakra` | Bhava Chakra (house cusps) |
| GET | `/api/yogas` | Yoga analysis |
| GET | `/api/raja_yogas` | Raja Yoga detection |
| GET | `/api/aspects` | Graha & Rasi Drishti |
| GET | `/api/summary` | Horoscope summary |
| GET | `/api/panchanga` | Panchanga data |

#### Configuration

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/config/outer_planets` | Toggle Uranus/Neptune/Pluto |
| GET | `/api/config/outer_planets` | Get outer planets status |
| GET | `/api/house_systems` | List available house systems |
| GET | `/api/languages` | List supported languages |
| GET | `/api/health` | Health check + diagnostics |

---

## 9. Data Compression & Storage

### Compression Service (`compression_service.py`)

The compression service reduces horoscope data size for efficient MongoDB storage.

**Key functions:**

| Function | Purpose |
|----------|---------|
| `compress_planet_name()` | "Jupiter" → "Ju" |
| `compress_sign_name()` | "Sagittarius" → "Sag" |
| `round_floats()` | 23.456789 → 23.46 |
| `clean_calendar_string()` | Remove redundant whitespace/formatting |
| `compress_planet()` | Compress single planet data object |
| `compress_chart()` | Compress entire chart (houses + planets) |
| `compress_dasha()` | Compress Dasha period data |
| `split_into_chunks()` | Split compressed data into 500KB chunks |

### Horoscope Service (`horoscope_service.py`)

Manages the end-to-end lifecycle:

| Function | Purpose |
|----------|---------|
| `fetch_vimsottari_dasha()` | Get Dasha data from calculation engine |
| `compress_and_store_horoscope()` | Full pipeline: compress → chunk → store in MongoDB |
| `get_user_horoscope()` | Retrieve + reconstruct horoscope from chunks |
| `list_user_horoscopes()` | List all horoscopes for a user |
| `delete_user_horoscope()` | Remove horoscope + all chunks |
| `get_birth_details()` | Fetch stored birth details |

---

## 10. Vertex AI Integration

### Service: `services/vertex_service.py`
### AutoGen Client: `utils/vertex_autogen_client.py`

### 10.1 Vertex AI Service

Handles initialization and basic LLM calls:

```python
# Initialization
vertexai.init(
    project="ai-astrology-481805",
    location="us-central1",
    credentials=google.auth.default()
)

# Model
model = GenerativeModel(
    "gemini-2.5-flash-lite",
    system_instruction=["You are an expert Vedic Astrologer..."]
)
```

### 10.2 Custom AutoGen Client (`VertexGenAIClient`)

A **custom implementation** of AutoGen's `ChatCompletionClient` that routes all LLM calls through Vertex AI:

| Feature | Value |
|---------|-------|
| **Provider** | Google Vertex AI |
| **Model** | `gemini-2.5-flash-lite` (configurable) |
| **Max Output Tokens** | 8,192 |
| **Temperature** | 0.7 |
| **Top-P** | 0.95 |
| **Safety Settings** | Block only high probability (lenient for astrology terms) |
| **Instantiation** | Per-call (supports different system instructions per agent) |

### 10.3 Safety Settings

```python
# Lenient settings to avoid blocking astrology-specific terms
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: BLOCK_ONLY_HIGH,
}
```

This ensures terms like "death" (8th house), "enemy" (6th house), "combustion" are not incorrectly flagged.

---

> **Note:** This documentation covers the astrology software as of February 2026. For backend infrastructure, deployment, and payment system documentation, see `DEVELOPER_HANDOFF_DOC.md`.
