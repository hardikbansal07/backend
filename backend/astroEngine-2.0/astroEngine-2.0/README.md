# AstroEngine 2.0 - Vedic Astrology Reasoning Engine

A comprehensive Vedic Astrology reasoning engine with multi-agent architecture, intelligent house mapping, and natural language predictions.

## 🌟 Features

- **Multi-Agent Architecture**: MainAgent for orchestration, SubAgent for detailed analysis
- **Intelligent House Mapping**: Dynamic extraction of relevant astrological data based on query domain
- **Comprehensive Domain Coverage**: 9 major life domains (Dating, Marriage, Career, Children, Education, Health, Wealth, Spirituality, General)
- **Divisional Chart Analysis**: Supports D1, D5, D7, D9, D10, D12, D24, D30 and more
- **Natural Language Predictions**: Clear, conversational astrological guidance
- **Flexible Data Input**: Generate fresh horoscopes or load existing ones
- **Terminal-Based I/O**: Simple command-line interface

## 📋 System Requirements

- Python 3.8+
- Gemini API Key
- Required packages (see `requirements.txt`)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd d:\astroEngine-2.0

# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key in .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 2. Basic Usage

#### Interactive Mode (Recommended for first-time users)

```bash
python run.py
```

This will guide you through:
1. Selecting or generating a horoscope
2. Entering your astrological question
3. Receiving a detailed prediction

#### Command-Line Mode

```bash
# With a pre-existing horoscope file
python run.py --horoscope "calculation/calculation-main/generated_horoscopes/your_file.json" "Will I get married soon?"

# Generate a new horoscope and analyze
python run.py --generate --name "John Doe" --date "1990-01-01" --time "12:30" --lat 28.6139 --lon 77.2090 --tz 5.5 "What about my career?"
```

## 📚 System Architecture

```
User Query → MainAgent → Intent Detection (Keyword/LLM)
                ↓
         Domain Pattern Selection
                ↓
         SubAgent → HouseMapper → Extract Relevant Data
                ↓
         LLM Analysis → Natural Language Prediction
```

### Core Components

1. **HoroscopeManager** (`horoscope_manager.py`)
   - Generates fresh horoscopes using the calculation engine
   - Loads existing horoscope files
   - Interactive horoscope selection

2. **MainAgent** (`main_agent.py`)
   - Orchestrates the analysis flow
   - Intent detection (keyword-based + LLM fallback)
   - Manages horoscope data

3. **SubAgent** (`sub_agent.py`)
   - Performs detailed astrological analysis
   - Uses HouseMapper for intelligent data extraction
   - Generates comprehensive natural language predictions

4. **HouseMapper** (`house_mapper.py`)
   - Dynamically extracts relevant astrological data
   - Supports all divisional charts
   - Extracts Panchanga, Vargottama, Combustion, Chara Karakas

5. **Domain Patterns** (`patterns.json`)
   - 9 comprehensive domain definitions
   - House significance and planetary roles
   - Data requirements and analysis guidance

## 🎯 Supported Domains

| Domain | Focus Houses | Key Planets | Primary Charts |
|--------|-------------|-------------|----------------|
| **Dating** | 5, 7, 8, 11 | Venus, Mars, Moon | D1, D9 |
| **Marriage** | 1, 2, 7, 8, 12 | Venus, Jupiter, Mars | D1, D9 |
| **Career** | 1, 2, 6, 10, 11 | Saturn, Sun, Jupiter | D1, D10 |
| **Children** | 1, 5, 9, 11 | Jupiter, Sun, Moon | D1, D7 |
| **Education** | 1, 2, 4, 5, 9 | Mercury, Jupiter, Moon | D1, D24 |
| **Health** | 1, 6, 8, 12 | Sun, Moon, Mars, Saturn | D1, D30 |
| **Wealth** | 1, 2, 5, 9, 11 | Jupiter, Venus, Mercury | D1, D9 |
| **Spirituality** | 1, 5, 8, 9, 12 | Jupiter, Ketu, Saturn | D1, D9, D12 |
| **General** | All | All | D1, D9 |

## 📖 Usage Examples

### Example 1: Dating Question

```bash
python run.py "Will my crush say yes to me?"
```

**Output includes:**
- Analysis of 5th house (romance) and 7th house (partnership)
- Venus position and strength
- Mars energy for pursuit
- Moon for emotional compatibility
- D9 chart confirmation
- Timing predictions based on transits

### Example 2: Career Question

```bash
python run.py "Will I get a promotion this year?"
```

**Output includes:**
- 10th house (career) analysis in D1 and D10
- Saturn and Sun positions
- 6th house for service dynamics
- 11th house for gains
- Current Dasha periods
- Timing for career changes

### Example 3: Generate Horoscope and Analyze

```bash
python run.py --generate \
  --name "Rama Krishna" \
  --date "1990-05-15" \
  --time "07:30:00" \
  --lat 13.0827 \
  --lon 80.2707 \
  --tz 5.5 \
  --place "Chennai" \
  "What is my overall life path?"
```

## 🔧 Advanced Usage

### Programmatic Usage

```python
from main_agent import MainAgent
from horoscope_manager import HoroscopeManager

# Initialize
manager = HoroscopeManager()
agent = MainAgent()

# Load horoscope
horoscope = manager.load_horoscope("path/to/horoscope.json")
agent.set_horoscope_data(horoscope)

# Analyze
response, metrics = agent.run_flow("Will I find love soon?")
print(response)
print(f"Cost: ${metrics['cost_usd']:.8f}")
```

### Generate Horoscope Programmatically

```python
from horoscope_manager import HoroscopeManager

manager = HoroscopeManager()

horoscope = manager.generate_horoscope(
    name="John Doe",
    birth_date="1990-01-01",
    birth_time="12:30:00",
    latitude=28.6139,
    longitude=77.2090,
    timezone=5.5,
    place="New Delhi"
)
```

## 📁 Project Structure

```
astroEngine-2.0/
├── run.py                      # Main entry point
├── main_agent.py               # Main orchestration agent
├── sub_agent.py                # Detailed analysis agent
├── horoscope_manager.py        # Horoscope generation/loading
├── house_mapper.py             # Intelligent data extraction
├── llm_interface.py            # Gemini LLM interface
├── logger_config.py            # Logging configuration
├── patterns.json               # Domain pattern definitions
├── chart_house_mapping.json    # House-chart mapping guide
├── .env                        # API keys (create this)
├── calculation/                # Vedic astrology calculation engine
│   └── calculation-main/
│       ├── generate_horoscope.py
│       ├── generated_horoscopes/  # Generated horoscope files
│       └── src/                   # Core calculation library
└── README.md                   # This file
```

## 🎓 How It Works

1. **Query Input**: User asks an astrological question
2. **Intent Detection**: System identifies the domain (dating, career, etc.)
   - First tries keyword matching for speed
   - Falls back to LLM if no keywords match
3. **Data Extraction**: HouseMapper extracts relevant data
   - Planetary positions in focus houses
   - Divisional chart analysis
   - Panchanga, Vargottama, Combustion
   - Chara Karakas
4. **LLM Analysis**: SubAgent sends structured data to Gemini
   - Comprehensive prompt with all relevant data
   - Domain-specific guidance
   - Natural language output format
5. **Prediction**: User receives detailed, conversational prediction

## 🔍 Data Extracted for Analysis

- **Planetary Positions**: Sign, house, degree, nakshatra, pada
- **Planetary Strength**: Dignity (exalted, debilitated, own sign)
- **Retrograde Status**: Identifies retrograde planets
- **House Occupants**: Planets in each relevant house
- **Divisional Charts**: D1, D5, D7, D9, D10, D12, D24, D30
- **Panchanga**: Tithi, Nakshatra, Yoga, Karana
- **Special Yogas**: Vargottama, Combustion
- **Chara Karakas**: Atma Karaka, Amatya Karaka, etc.
- **Current Transits**: If available in horoscope

## 🛠️ Troubleshooting

### "GEMINI_API_KEY not found"
- Create a `.env` file in the project root
- Add: `GEMINI_API_KEY=your_actual_api_key`

### "No horoscope data available"
- Make sure to load or generate a horoscope before asking questions
- Use interactive mode (`python run.py`) for guided setup

### "Import Error: No module named 'api'"
- Ensure you're running from the `astroEngine-2.0` directory
- The calculation engine path is automatically added to sys.path

### Horoscope Generation Fails
- Check that all required parameters are provided (name, date, time, lat, lon, tz)
- Verify date format: YYYY-MM-DD
- Verify time format: HH:MM:SS or HH:MM
- Latitude: -90 to 90, Longitude: -180 to 180

## 📊 Logging

All operations are logged to `astro_pipeline.log` with detailed information:
- Intent detection results
- Data extraction details
- LLM interactions
- Errors and warnings

## 💡 Tips for Best Results

1. **Be Specific**: Ask clear, specific questions
   - Good: "Will I get married in 2026?"
   - Less good: "Tell me about marriage"

2. **Use Keywords**: Include domain keywords for faster intent detection
   - Dating: love, crush, romance, dating
   - Career: job, promotion, work, career
   - Marriage: marriage, spouse, wedding

3. **Accurate Birth Data**: Ensure horoscope has accurate birth details
   - Exact birth time is crucial
   - Correct location coordinates

4. **Review Logs**: Check `astro_pipeline.log` for detailed analysis flow

## 🤝 Contributing

This is a comprehensive astrology engine. Future enhancements could include:
- Dasha period analysis (Vimshottari, Yogini, etc.)
- Transit predictions
- Compatibility analysis (synastry)
- Remedial measures database
- Multi-language support
- Web interface

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- Built on PyJHora calculation engine
- Powered by Google Gemini AI
- Based on classical Vedic astrology principles

---

**Made with ❤️ for accurate and insightful Vedic astrology predictions**
