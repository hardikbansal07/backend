# Vedic Astrology Calculation Engine & Web Interface

This project is a comprehensive Vedic Astrology application featuring a high-performance Python backend for calculations and a modern React-based frontend for visualization. It leverages the `PyJHora` library (based on "Vedic Astrology - An Integrated Approach" by PVR Narasimha Rao) to provide accurate astrological data.

## Features

### Core Calculations

* **Horoscope Generation**: Calculates Rasi (D1) and various Divisional Charts (Vargas) including D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.
* **Planetary Positions**: Accurate calculation of planetary longitudes, nakshatras, padas, and dignities (Exalted, Debilitated, Own Sign, Moolatrikona).
* **House Systems**: Supports multiple house systems including Placidus, Koch, Equal, Porphyrius, Regiomontanus, Campanus, and more.
* **Special Lagnas**: Bhava, Hora, Ghati, Vighati, Pranapada, Indu, Bhrigu Bindu, Kunda, Sree Lagna.
* **Upagrahas**: Gulika, Maandi, Dhuma, Vyatipaata, Parivesha, Indrachapa, Upaketu, Kaala, Mrityu, Artha Praharaka, Yama Ghantaka.
* **Arudha Padas**: Calculation of Bhava Arudhas for D1 and D9 charts.

### Dasha Systems

* **Vimsottari Dasha**: Full tree support with Maha, Antar, Pratyantara, Sookshma, Prana, and Deha dashas.
* **Rasi Dashas**: Chara, Sthira, Narayana, Drig, Yogardha, Paryaaya, Brahma, Mandooka, Sudasa, Kalachakra, Navamsa, Trikona, Chakra, Kendraadhi Rasi.
* **Graha Dashas**: Ashtottari, Yogini, Shodasottari, Dwadasottari, Dwisatpathi, Panchottari.

### Panchanga & Transit

* **Daily Panchanga**: Tithi, Nakshatra, Yoga, Karana, Vaara, Sunrise/Sunset, Moonrise/Moonset.
* **Transit**: Real-time planetary transit positions for any given date and location.

### Visualization

* **Interactive Charts**: SVG-based rendering of South Indian and North Indian chart styles.
* **Detailed Reports**: Comprehensive breakdown of planetary strengths, yogas, and raja yogas.

## Tech Stack

### Backend

* **Language**: Python 3.11+
* **Framework**: FastAPI
* **Server**: Uvicorn
* **Astrology Library**: PyJHora (customized/integrated)
* **Ephemeris**: Swiss Ephemeris (pyswisseph)

### Frontend

* **Framework**: React
* **Build Tool**: Vite
* **Styling**: Tailwind CSS
* **Language**: TypeScript

## Project Structure

```
calculation-main/
├── src/
│   ├── api/                 # FastAPI application endpoints and service logic
│   │   ├── app.py           # Main API entry point
│   │   ├── service.py       # Business logic and orchestration
│   │   ├── models.py        # Pydantic models for request/response
│   │   └── ...
│   └── jhora/               # Core Vedic Astrology library (PyJHora)
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # UI components (Charts, Panels, etc.)
│   │   ├── pages/           # Application pages
│   │   └── ...
│   └── package.json
├── requirements.txt         # Python dependencies
├── start_backend.ps1        # PowerShell script to start backend
└── start_frontend.ps1       # PowerShell script to start frontend
```

## Installation & Setup

### Prerequisites

* Python 3.11 or higher
* Node.js 18 or higher
* Windows (recommended for PowerShell scripts) or Linux/Mac

### 1. Backend Setup


1. Navigate to the project root (`calculation-main`).
2. Create a virtual environment (optional but recommended):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install Python dependencies:

   ```powershell
   pip install -r requirements.txt
   ```
4. Start the backend server:

   ```powershell
   .\start_backend.ps1
   ```

   The API will be available at `http://localhost:8080`.
   API Documentation (Swagger UI) is available at `http://localhost:8080/docs`.

### 2. Frontend Setup


1. Navigate to the frontend directory:

   ```powershell
   cd frontend
   ```
2. Install Node.js dependencies:

   ```powershell
   npm install
   ```
3. Start the development server:

   ```powershell
   npm run dev
   ```

   The application will be available at `http://localhost:5173` (or the port shown in the terminal).

## Usage


1. Open the frontend URL in your browser.
2. Enter birth details (Date, Time, Location).
3. Click "Calculate" to generate the horoscope.
4. Explore the various tabs for Divisional Charts, Dashas, and detailed analysis.

## Troubleshooting

* **Missing Ephemeris**: If you encounter errors related to Swiss Ephemeris files, ensure the `SE_EPHE_PATH` environment variable is set correctly (handled by `start_backend.ps1`) and the files exist in `src/jhora/data/ephe`.
* **Port Conflicts**: If ports 8080 or 5173 are in use, modify the `start_backend.ps1` or `vite.config.ts` files respectively.


