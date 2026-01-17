# deva agent

## 1. Overview
**The Celestial Council** is a next-generation Agentic AI system for astrological analysis. Unlike traditional linear pipelines, it simulates a **Round-Table Consultation** between independent specialist agents.

It is built on top of **Microsoft Autogen** and features:
*   **Rich Intelligence**: Agents are grounded in classical texts via detailed "Knowledge Base" prompts.
*   **Active Tooling**: Agents can perform real-time calculations (Dasha, Varga positions) using integrated Python tools.
*   **Synthesis**: A specialized "MahaRishi" agent synthesizes conflicting data into a coherent narrative.

---

## 2. Architecture & Methodology

### The "Council" Model
Instead of a single AI trying to know everything, we split the domain into specific "Department Heads":

1.  **LagnaPati (The Ascendant Architect)**: Focuses on the D1 Chart, physical body, and general fortune.
2.  **KalaPurusha (The Time Keeper)**: Focuses on *Timing* (Vimshottari Dasha, Transits).
3.  **VargaVizier (The Divisional Specialist)**: Focuses on specific areas like Career (D10) or Wealth (D2).
4.  **MahaRishi (The Synthesizer)**: The Chair. Listens to all reports, weighs evidence, and delivers the final verdict.

### The Workflow
1.  **Input Loading**: The Runtime loads `lagna.json` (Chart Positions) and `meta.json` (Birth Time).
2.  **Context Injection**: Data is flattened into a "System Context" visible to all agents.
3.  **Round Robin Consultation**:
    *   *Step A*: LagnaPati assesses structural strength.
    *   *Step B*: KalaPurusha checks if the current time is favorable.
    *   *Step C*: VargaVizier checks the specific harmonic chart (e.g., D10).
    *   *Step D*: MahaRishi combines these inputs ("Structure is good, Time is bad, D10 protects...").
4.  **Tool Execution**: During their turn, agents can "Pause" and call Python functions (e.g., `check_divisional_strength`) to verify facts before speaking.

---

## 3. Directory Structure

```text
deva/
├── agents/                 # The "Personnel"
│   ├── specialists.py      # The department heads (LagnaPati, KalaPurusha, VargaVizier)
│   └── principals.py       # The management (MahaRishi)
├── config/                 # Infrastructure
│   └── models.py           # LLM Client Configuration (Gemini)
├── prompts/                # The "Brains" (Knowledge Base)
│   └── library/            # Markdown files with specific astrological rules
│       ├── d1_lagna_rules.md
│       ├── dasha_logic.md
│       └── ...
├── tools/                  # The "Hands" (Capabilities)
│   ├── astro_tools.py      # Autogen-ready wrappers
│   └── vedic_utils.py      # Core calculation engine (Math/Logic)
└── runtime.py              # The "Office" (CLI Entry Point)
```

---

## 4. Component Deep Dive

### A. The Knowledge Base (`prompts/library`)
Agents are not just given a name; they are given a *Persona*. 
*   **Example**: `d1_lagna_rules.md` explicitly instructs `LagnaPati` to check for *Pancha Mahapurusha Yoga* and *Dig Bala*.
*   **Why**: This injects domain expertise that general LLMs might miss, ensuring they follow classical protocols.

### B. The Tooling Layer (`tools/`)
Agents have access to **Real-Time Calculations**. They do not rely solely on the input JSON.
*   **`vedic_utils.py`**: The heavy lifting engine (Legacy code integrated).
*   **`astro_tools.py`**: Exposes functions like:
    *   `calculate_varga_positions(planet_positions)`: Checks Vargottama status.
    *   `get_current_dasha(moon_degree, birth_date)`: Calculates current Mahadasha/Antardasha.
    *   `check_divisional_strength(planet, degree, varga_num)`: Finds where a planet sits in D10, D9, etc.

### C. The Runtime (`runtime.py`)
This script orchestrates the session.
1.  **Parses Arguments**: `--case` (folder) and `--question`.
2.  **Hydrates Context**: Reads `lagna.json` and `meta.json`.
3.  **Initializes Council**: Spins up the `RoundRobinGroupChat`.
4.  **Streams Output**: Prints the conversation to the console in real-time.

---

## 5. Input Data Specification

The system expects a case folder with two files:

### 1. `lagna.json` (The Map)
Contains the astronomical positions of planets.
```json
{
  "ascendantSign": "Aries",
  "planets": [
    { "name": "Sun", "sign": "Aries", "longitudeDMS": "10d15m", ... },
    ...
  ]
}
```

### 2. `meta.json` (The Clock)
Contains birth details required for Dasha calculation.
```json
{
  "name": "User Name",
  "birth": {
    "datetime": "1990-01-01T06:00:00+05:30"
  }
}
```

---

## 6. How to Run

From the root directory (`ai/`), run:

```powershell
python -m agent3_celestial_council.runtime `
    --case "path/to/case/folder" `
    --question "Will I be successful in business?"
```

**Required Environment Variables**:
*   `GEMINI_API_KEY`: Your Google Gemini API Key.

---

## 7. Extending the System

To add a new specialist (e.g., `RelationshipExpert`):
1.  **Create Prompt**: Write `prompts/library/relationship_rules.md` (Rules for D9/D7).
2.  **Define Agent**: Add `RelationshipExpert` in `agents/specialists.py` loading that prompt.
3.  **Register**: Add the agent to the `participants` list in `runtime.py`.
4.  **Run**: The Council now has a new member!
