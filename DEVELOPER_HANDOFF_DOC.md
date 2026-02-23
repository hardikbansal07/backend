# AstroCare AI — Complete Developer Handoff Documentation

> **Project Name:** AstroCare AI (Astrocare1Project)  
> **Domain:** astrocareai.com  
> **GitHub:** https://github.com/hardikbansal07/Astrocare1Project  
> **Last Updated:** February 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Backend Architecture](#4-backend-architecture)
5. [Authentication System](#5-authentication-system)
6. [Database (MongoDB)](#6-database-mongodb)
7. [API Routes Reference](#7-api-routes-reference)
8. [AI/ML Systems](#8-aiml-systems)
9. [Payment System (Razorpay)](#9-payment-system-razorpay)
10. [Report Generation](#10-report-generation)
11. [Deployment](#11-deployment)
12. [Environment Variables](#12-environment-variables)
13. [How to Run Locally](#13-how-to-run-locally)
14. [Key Flows (Step-by-Step)](#14-key-flows-step-by-step)
15. [Known Issues & Notes](#15-known-issues--notes)

---

## 1. Project Overview

AstroCare AI is an **AI-powered Vedic Astrology platform**. Users provide their birth details (date, time, place), and the system:

1. **Calculates** a full Vedic horoscope (Rasi chart, Divisional charts D1-D60, Vimsottari Dasha)
2. **Compresses & stores** the horoscope data in MongoDB
3. **Provides AI chat** — users can ask astrology questions and get AI-generated responses based on their actual chart data
4. **Generates PDF reports** — detailed astrology reports using an AI "council" of specialist agents
5. **Love/Relationship analysis** — specialized AstroEngine 2.0 module for love-related queries

The platform uses a **credit-based monetization model** with Razorpay payments.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | Python 3.11 + **FastAPI** |
| **ASGI Server** | Uvicorn (dev) / Gunicorn+Uvicorn (prod) |
| **Database** | **MongoDB Atlas** (via Motor async driver) |
| **AI/LLM** | **Google Vertex AI** (Gemini models) |
| **AI Agent Framework** | **AutoGen** (Microsoft) — multi-agent orchestration |
| **Astrology Engine** | **PySwissEph** + **JHora** (Vedic calculation library) |
| **Payments** | **Razorpay** (India-focused payment gateway) |
| **PDF Generation** | **ReportLab** |
| **File Storage** | **Supabase Storage** (for PDF reports) |
| **Cloud Hosting** | **Google Cloud App Engine** (Standard, Python 3.11) |
| **CI/CD** | **Google Cloud Build** |
| **Frontend** | React Native / Expo (separate repo or mobile app) |

### Key Python Dependencies

```
fastapi, uvicorn, motor, pymongo, passlib[bcrypt], python-jose[cryptography],
google-auth, google-cloud-aiplatform, vertexai, autogen-agentchat, autogen-core,
openai, pyswisseph, pyephem, numpy, pandas, razorpay, reportlab, supabase,
httpx, tenacity, certifi, python-dotenv
```

See `backend/requirements.txt` for full list.

---

## 3. Project Structure

```
Astrocare1Project/
├── cloudbuild.yaml              # GCP Cloud Build config
├── dispatch.yaml                # App Engine URL routing rules
├── .gitignore
│
├── backend/                     # ★ MAIN APPLICATION
│   ├── main.py                  # FastAPI app entry point
│   ├── app.yaml                 # App Engine deployment config
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   │
│   ├── # --- Core Modules ---
│   ├── auth.py                  # JWT auth, Google/Facebook OAuth, password hashing
│   ├── models.py                # Pydantic data models (User, Chat, Payment, etc.)
│   ├── mongo.py                 # MongoDB connection + collection initialization
│   │
│   ├── # --- Route Files ---
│   ├── routers/
│   │   ├── auth_routes.py       # Unified login (Guest/Google/Facebook/Email)
│   │   ├── guest_auth.py        # Legacy guest login endpoint
│   │   ├── place_routes.py      # Photon API geo-search for birth place
│   │   └── report_routes.py     # Async report generation endpoints
│   ├── user_routes.py           # User profile CRUD
│   ├── referral_routes.py       # Referral code system
│   ├── calculation_routes.py    # Horoscope calculation engine wrapper
│   ├── ai_routes.py             # AI orchestrator (Vertex AI chat)
│   ├── deva_routes.py           # Deva Agent — main AI astrology chat (775 lines)
│   ├── love_chat_routes.py      # AstroEngine 2.0 love/relationship chat
│   │
│   ├── # --- Services ---
│   ├── services/
│   │   └── vertex_service.py    # Vertex AI initialization + Gemini model wrapper
│   ├── utils/
│   │   └── vertex_autogen_client.py  # Custom AutoGen client for Vertex AI
│   ├── horoscope_service.py     # Compress + Store + Retrieve horoscopes
│   ├── compression_service.py   # Vedic chart data compression logic
│   ├── report_service.py        # PDF generation + Supabase upload + email
│   ├── guest_dependency.py      # Guest user dependency injection
│   │
│   ├── # --- Payment ---
│   ├── razorpay_service/
│   │   ├── config.py            # Razorpay API keys
│   │   ├── service.py           # Order creation, signature verification
│   │   ├── api.py               # Payment API routes
│   │   └── webhook.py           # Razorpay webhook handler
│   │
│   ├── # --- Admin ---
│   ├── app/admin/
│   │   ├── auth.py              # Admin authentication
│   │   ├── routes.py            # Admin dashboard APIs (user mgmt, credits, bans)
│   │   ├── blog_models.py       # Blog data models
│   │   └── blog_routes.py       # Blog CRUD (admin + public)
│   │
│   ├── # --- AI Sub-Modules ---
│   ├── r1_algo/                 # R1 Report Generation Algorithm (multi-agent)
│   ├── deva-agent-deva_wow/     # Deva Agent — AI astrology council
│   ├── astroEngine-2.0/         # AstroEngine 2.0 — love/relationship module
│   │
│   ├── # --- Calculation Engine ---
│   ├── calculation/
│   │   └── calculation-main/    # Vedic astrology calculation engine (JHora/SwissEph)
│   │       └── src/
│   │           └── api/         # Calculation API (app.py, service.py, models.py)
│   │
│   └── generated/               # Locally generated PDF reports (fallback)
│
└── docs/                        # Various documentation files (21 files)
```

---

## 4. Backend Architecture

### Entry Point: `main.py`

The app starts in `main.py` which:

1. **Loads `.env`** via `python-dotenv`
2. **Adds calculation engine** to `sys.path`
3. **Configures logging** (console + optional file handler)
4. **Creates FastAPI app** with lifespan manager
5. **Connects to MongoDB** on startup, disconnects on shutdown
6. **Configures CORS** for allowed origins
7. **Imports and registers ~12 routers** with safe try/except (app won't crash if a module fails)

### Router Registration Map

| Router | Mount Prefix | Final API Path Example |
|--------|-------------|----------------------|
| `central_auth_router` | `/calc/api/v1` | `/calc/api/v1/auth/unified-login` |
| `user_router` | `/calc` | `/calc/api/v1/auth/users/me` |
| `referral_router` | `/calc` | `/calc/api/v1/referral/code` |
| `calculation_router` | `/calc` | `/calc/api/horoscope/store` |
| `ai_router` | `/calc/api/v1/ai` | `/calc/api/v1/ai/analyze` |
| `deva_router` | `/calc/api/v1/deva` | `/calc/api/v1/deva/chat` |
| `razorpay_router` | `/calc` | `/calc/api/v1/payment/create-order` |
| `love_chat_router` | `/calc` | `/calc/api/v1/love-chat/analyze` |
| `report_router` | `/calc/api/v1` | `/calc/api/v1/reports/generate` |
| `place_router` | `/calc/api/v1` | `/calc/api/v1/places/search` |
| `admin_router` | (internal) | `/admin/...` |
| `admin_auth_router` | `/api/admin` | `/api/admin/login` |
| `blog_admin_router` | (internal) | `/admin/blogs/...` |
| `blog_public_router` | `/calc` | `/calc/api/blogs/...` |

### Debug Endpoint

`GET /calc/chk` — Returns status of all router imports and lists all registered routes.

---

## 5. Authentication System

### File: `auth.py` + `routers/auth_routes.py`

The app uses **JWT-based authentication** with access + refresh tokens.

### Auth Methods (Unified Login)

**Endpoint:** `POST /calc/api/v1/auth/unified-login`

```json
{
  "provider": "google" | "guest" | "email" | "facebook",
  "data": { ... }
}
```

| Provider | Data Fields | Notes |
|----------|------------|-------|
| `guest` | `device_id`, `preferred_language` | Creates temp user, 2 free credits |
| `google` | `token` (ID token or access token) | Auto-creates user on first login |
| `facebook` | `token` (access token) | Auto-creates user on first login |
| `email` | `email`, `password` | Standard email/password login |

### Token System

| Token | Lifespan | Storage |
|-------|----------|---------|
| **Access Token** | 15 minutes | Client-side (JWT, HS256) |
| **Refresh Token** | 7 days | MongoDB `refresh_tokens` collection |

### Key Auth Functions (`auth.py`)

- `create_access_token()` — Creates JWT with user email as `sub`
- `create_refresh_token()` — Generates UUID, stores in MongoDB
- `verify_refresh_token()` — Validates refresh token from DB
- `get_current_user()` — Dependency: decodes JWT → fetches user from DB
- `get_current_active_user()` — Dependency: ensures user is not disabled
- `verify_google_token()` — Handles both ID tokens (JWT) and access tokens (`ya29.`)
- `verify_facebook_token()` — Calls Facebook Graph API
- `get_or_create_google_user()` / `get_or_create_facebook_user()` — Upsert user

### Other Auth Endpoints

| Method | Path | Description |
|--------|------|------------|
| `POST` | `/calc/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/calc/api/v1/auth/logout` | Revoke refresh token |

---

## 6. Database (MongoDB)

### Connection: `mongo.py`

- **Driver:** Motor (async MongoDB driver)
- **Connection:** MongoDB Atlas with TLS (via `certifi`)
- **DB Name:** Configured via `DB_NAME` env var (default: `unified_backend`)

### Collections (14 total)

| Collection | Purpose | Key Indexes |
|-----------|---------|-------------|
| `users` | User accounts | `email` (unique), `is_guest+device_id` |
| `api_keys` | API key management | `user_id`, `key` (unique) |
| `chats` | Chat sessions | `user_id` |
| `chat_messages` | Individual messages | `chat_id` |
| `payments` | Payment records | `user_id` |
| `referrals` | Referral tracking | `code` (unique), `referrer_id` |
| `sessions` | User sessions | `user_id`, `token_hash` (unique) |
| `horoscopes` | Horoscope index entries | `user_email+request_id` (unique) |
| `horoscope_chunks` | Compressed chart data chunks | `user_email+request_id+chunk_index` |
| `deva_conversations` | AI chat history | `user_email`, `request_id` |
| `user_birth_details` | Birth info | `user_email` (unique) |
| `chat_question_tracking` | Credit/question tracking | `user_email` (unique) |
| `blogs` | Blog posts | `created_at`, `category` |
| `refresh_tokens` | Refresh tokens | `token` (unique), `user_email` |

### User Document Schema

```json
{
  "email": "user@example.com",
  "username": "John",
  "full_name": "John Doe",
  "gender": "Male",
  "profile_photo": "https://...",
  "disabled": false,
  "referral_code": "ABC12345",
  "role": "user",
  "last_active": "2026-01-15T...",
  "credits": 5.0,
  "is_guest": false,
  "device_id": null,
  "preferred_language": "English",
  "hashed_password": "$2b$12$...",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 7. API Routes Reference

### Authentication (`/calc/api/v1/auth/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/unified-login` | ❌ | Login (Google/Facebook/Email/Guest) |
| POST | `/refresh` | ❌ | Refresh access token |
| POST | `/logout` | ❌ | Revoke refresh token |
| GET | `/users/me` | ✅ | Get current user profile |
| PUT | `/profile` | ✅ | Update profile (name, photo, gender, language) |

### Deva Agent — AI Chat (`/calc/api/v1/deva/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| GET | `/` | ❌ | Service status |
| POST | `/chat` | ✅ | Ask astrology question (costs 1 credit) |
| GET | `/conversations` | ✅ | List chat history |
| GET | `/chat/history` | ✅ | Get chat history (optionally by request_id) |
| GET | `/horoscope/status` | ✅ | Check if user has horoscope data |
| POST | `/birth-details` | ✅ | Save birth details |
| GET | `/birth-details` | ✅ | Get saved birth details |
| POST | `/birth-details/reset` | ✅ | Reset all user data (birth details + horoscopes) |
| GET | `/question-status` | ✅ | Get question/credit tracking status |

### Calculation Engine (`/calc/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/calc/api/horoscope/store` | ✅ | Store calculated horoscope |
| Various | `/calc/api/...` | Varies | Wrapped calculation engine routes |

### Love Chat — AstroEngine 2.0 (`/calc/api/v1/love-chat/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/analyze` | ✅ | Love/relationship question analysis |
| POST | `/generate-horoscope` | ✅ | Generate new horoscope |
| GET | `/domains` | ❌ | List available astrology domains |
| GET | `/history` | ✅ | Get love chat history |

### Payment (`/calc/api/v1/payment/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/create-order` | ✅ | Create Razorpay order |
| POST | `/verify-payment` | ✅ | Verify payment + credit account |
| POST | `/webhook` | ❌ | Razorpay webhook |

### Reports (`/calc/api/v1/reports/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/generate` | ✅ | Start async report generation |
| GET | `/status/{job_id}` | ✅ | Check report generation status |

### Places (`/calc/api/v1/places/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| GET | `/search?q=...` | ❌ | Search places (Photon/OSM API) |

### Referral (`/calc/api/v1/referral/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| GET | `/code` | ✅ | Get/create referral code |
| GET | `/stats` | ✅ | Get referral statistics |
| POST | `/validate` | ❌ | Validate a referral code |

### Admin (`/admin/`, `/api/admin/`)

| Method | Path | Auth | Description |
|--------|------|------|------------|
| POST | `/api/admin/login` | ❌ | Admin login |
| GET | `/admin/users` | Admin | List all users |
| PUT | `/admin/users/{id}/credits` | Admin | Update user credits |
| POST | `/admin/users/ban` | Admin | Ban/unban user |
| Various | `/admin/blogs/...` | Admin | Blog CRUD |
| GET | `/calc/api/blogs/...` | ❌ | Public blog endpoints |

---

## 8. AI/ML Systems

### 8.1 Vertex AI Service (`services/vertex_service.py`)

- Initializes Google Vertex AI with **Application Default Credentials (ADC)**
- Uses **Gemini** model (configurable via `GEMINI_MODEL` env var)
- Default model: `gemini-pro`, currently set to `gemini-2.5-flash-lite`

### 8.2 Deva Agent — Multi-Agent Council (`deva_routes.py`)

The main AI chat system uses **AutoGen** framework with a "council" of 4 AI agents:

```
User Question
    ↓
┌────────────────────┐
│  LagnaPati          │ → Analyzes D1 (Rasi chart) strength
│  KalaPurusha        │ → Checks current Dasha periods
│  VargaVizier        │ → Analyzes D10 (Career) chart
│  MahaRishi (Final)  │ → Synthesizes final answer as "Astro Care AI"
└────────────────────┘
    ↓
Final Response to User
```

- Uses `RoundRobinGroupChat` with `max_turns=4`
- Each agent runs on Vertex AI via custom `VertexGenAIClient`
- Supports **multi-language** responses (Hindi, Telugu, English, etc.)
- Response format: **To The Point** → **Advice** → **Closing Question**

### 8.3 AstroEngine 2.0 (`astroEngine-2.0/`)

Specialized module for **love/relationship** astrology queries. Uses its own `MainAgent` and `HoroscopeManager`.

### 8.4 R1 Algorithm (`r1_algo/`)

Advanced **multi-agent report generation** system. Creates detailed PDF reports by consulting specialist agents.

### 8.5 Calculation Engine (`calculation/calculation-main/`)

Vedic astrology calculation engine using:
- **PySwissEph** (Swiss Ephemeris) for planetary positions
- **JHora** library for Vedic-specific calculations
- Generates: Rasi Chart, 16+ Divisional Charts (D1-D60), Vimsottari Dasha

---

## 9. Payment System (Razorpay)

### Files: `razorpay_service/`

### Flow:

```
1. Frontend → POST /create-order { plan_id: "basic" }
2. Backend creates Razorpay Order → Returns order_id + key
3. Frontend opens Razorpay Checkout UI
4. User completes payment
5. Frontend → POST /verify-payment { razorpay_order_id, payment_id, signature }
6. Backend verifies signature → Credits added to user account
7. (Optional) Razorpay → POST /webhook for server-side confirmation
```

### Credit System

- **New User:** 5 free credits
- **Guest User:** 2 free credits
- **Each AI question** costs **1 credit**
- Credits are deducted BEFORE the AI call; refunded on failure

---

## 10. Report Generation

### Files: `report_service.py` + `routers/report_routes.py` + `r1_algo/`

### Flow:

```
1. User → POST /reports/generate { report_type: "full" }
2. Backend creates async job → Returns job_id
3. Background task:
   a. Fetches user's latest horoscope from MongoDB
   b. Runs R1 multi-agent council → Generates markdown report
   c. Converts markdown → PDF (ReportLab)
   d. Uploads to Supabase Storage (or saves locally as fallback)
4. User polls → GET /reports/status/{job_id}
5. When complete → Returns download_url
```

---

## 11. Deployment

### Google Cloud App Engine

- **Runtime:** Python 3.11
- **Service:** `backend` (deployed as default service)
- **Instance:** F2 class (512MB RAM, 1.2GHz CPU)
- **Scaling:** Fixed 1 instance (min=1, max=1)
- **Entry:** `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`

### Deploying

**Via Cloud Build (CI/CD):**
```bash
gcloud builds submit --config=cloudbuild.yaml
```

**Manual Deploy:**
```bash
cd backend
gcloud app deploy app.yaml --quiet
```

### URL Routing (`dispatch.yaml`)

All requests (`/api/*`, `/calc/*`, `*/*`) route to the `backend` service.

---

## 12. Environment Variables

These are configured in `backend/app.yaml` for production, or in a `.env` file for local development.

| Variable | Description | Example |
|----------|------------|---------|
| `MONGO_URI` | MongoDB Atlas connection string | `mongodb+srv://...` |
| `DB_NAME` | Database name | `astrocare7` |
| `SECRET_KEY` | JWT signing secret | `9bc5f5ce2dc...` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | `292043...` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | Google OAuth callback URL | `https://...` |
| `GEMINI_MODEL` | Vertex AI model name | `gemini-2.5-flash-lite` |
| `GEMINI_API_KEY` | Gemini API key (fallback) | `AIzaSy...` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `ai-astrology-481805` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |
| `SUPABASE_URL` | Supabase project URL | `https://...supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJ...` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USER` | Sender email | `support@...` |
| `EMAIL_PASSWORD` | Email app password | `...` |
| `RAZORPAY_KEY_ID` | Razorpay key | `rzp_...` |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | `...` |

> **⚠️ IMPORTANT:** The `app.yaml` file contains real credentials. Keep it secure and never commit to public repos.

---

## 13. How to Run Locally

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (or local MongoDB)
- Google Cloud SDK (for Vertex AI auth)

### Steps

```bash
# 1. Clone repository
git clone https://github.com/hardikbansal07/Astrocare1Project.git
cd Astrocare1Project/backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy from app.yaml env_variables)
# Create backend/.env with all required variables

# 5. Authenticate with Google Cloud (for Vertex AI)
gcloud auth application-default login

# 6. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Server will be available at:** `http://localhost:8000`  
**API docs (Swagger):** `http://localhost:8000/docs`

---

## 14. Key Flows (Step-by-Step)

### Flow 1: New User Registration (Google)

```
1. Mobile app → POST /calc/api/v1/auth/unified-login
   Body: { "provider": "google", "data": { "token": "ya29.xxx" } }
2. Backend verifies Google token → Creates user in MongoDB
3. Returns access_token + refresh_token
4. App stores tokens for subsequent API calls
```

### Flow 2: Getting a Horoscope Reading

```
1. User enters birth details in app
2. App → POST /calc/api/v1/deva/birth-details (saves birth info)
3. App → POST /calc/api/horoscope (triggers calculation engine)
4. Calculation engine computes full Vedic chart
5. App → POST /calc/api/horoscope/store (compresses + stores in MongoDB)
6. Horoscope is now available for AI chat
```

### Flow 3: AI Chat Conversation

```
1. App → POST /calc/api/v1/deva/chat
   Body: { "question": "What about my career?" }
2. Backend:
   a. Checks credit balance (≥1 required)
   b. Deducts 1 credit
   c. Fetches user's horoscope from MongoDB
   d. Fetches last 5 conversations for context
   e. Runs Deva Agent council (4 AI agents via Vertex AI)
   f. Stores conversation in MongoDB
   g. Returns response with credits_remaining
3. If error occurs → credit is refunded
```

### Flow 4: Buying Credits

```
1. App → POST /calc/api/v1/payment/create-order { "plan_id": "basic" }
2. Backend creates Razorpay order → Returns order details
3. App opens Razorpay checkout → User pays
4. App → POST /calc/api/v1/payment/verify-payment { order_id, payment_id, signature }
5. Backend verifies → Adds credits to user account
```

### Flow 5: Token Refresh

```
1. Access token expires (after 15 min)
2. App → POST /calc/api/v1/auth/refresh { "refresh_token": "uuid-xxx" }
3. Backend validates refresh token → Issues new access token
4. App updates stored access token
```

---

## 15. Known Issues & Notes

### Architecture Notes

- **All routers are imported with try/except** — if a module fails to import, the app still starts (only that module is disabled). Check `GET /calc/chk` to see import status.
- **File logging is disabled** for cloud deployment (commented out in `main.py`). Enable locally by uncommenting the `file_handler` lines.
- **The calculation engine** is added to `sys.path` dynamically. The path is: `backend/calculation/calculation-main/src/`.
- **Guest users** get 2 credits and are identified by `device_id` for session persistence.

### Security Notes

- `app.yaml` contains **production credentials** — keep it out of public repos
- JWT `SECRET_KEY` should be rotated periodically
- Admin authentication uses a separate auth system (`app/admin/auth.py`)
- CORS is configured for specific domains — update when adding new frontend hosts

### Scaling Notes

- Currently scaled to **1 instance** (`min_instances: 1, max_instances: 1`)
- Report generation uses **in-memory job tracking** (`Dict[str, Any]`). For multi-worker scaling, migrate to **Redis**.
- The `VertexGenAIClient` instantiates a new `GenerativeModel` per call to support different system instructions per agent.

### Frontend Integration

- The frontend is a **React Native / Expo** mobile app (not in this repo)
- All API calls go through `/calc/api/v1/...` prefix
- CORS allows `localhost:5173`, `localhost:3000`, `localhost:8081` for local development
- The app also supports Vercel deployment for web frontend

---

> **For questions, contact the original developer at the GitHub repo.**
