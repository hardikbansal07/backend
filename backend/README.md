# Unified Backend

This project merges the **Calculation Service** and **AI Orchestrator Agent** into a single FastAPI application.

## Directory Structure
- `calculation/`: Contains the core Vedic Astrology calculation logic.
- `ai_orchestrator/`: Contains the AI Agentic workflow logic.
- `main.py`: The entry point for the FastAPI server.
- `requirements.txt`: Python package dependencies.

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   *Note: If you encounter issues with `pyswisseph` or other binary packages, ensure you have the necessary build tools installed.*

## Running the Server

Start the server using `uvicorn`:

```bash
python3 -m uvicorn main:app --port 8080 --reload
```

The server will be available at `http://localhost:8080`.

## API Endpoints

- **Root**: `GET /` - Server status.
- **Calculation API**:
  - `GET /api/places?q=...` - Search for cities.
  - `POST /api/horoscope` - Generate horoscope data.
  - `GET /api/health` - Check calculation service status.
- **AI Agent API**:
  - `GET /api/v1/ai/` - AI service status.
  - `POST /api/v1/ai/analyze` - Request chart analysis (placeholder).

## Development

- The `calculation` source code wraps the original `PyJHora` application.
- The `ai_orchestrator` source wraps the `agent2` logic.
- `main.py` handles the routing and startup initialization (loading world cities, etc.).
