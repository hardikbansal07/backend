# API Routing Documentation
**Astro Care AI — Backend API**
_FastAPI · MongoDB · Vertex AI_

---

## Base URL

| Environment | Base URL |
|---|---|
| Production | `https://ai-astrology-481805.as.r.appspot.com` |
| Local Dev | `http://localhost:8000` |

---

## Authentication

Most protected routes require a **Bearer token** in the header:

```
Authorization: Bearer <access_token>
```

Access tokens are obtained from the login endpoints. Refresh tokens are used to renew access.

---

## Router Overview

| Router | Mount Prefix | Internal Prefix | Final Path Base |
|---|---|---|---|
| Central Auth | `/calc/api/v1` | `/auth` | `/calc/api/v1/auth/...` |
| User / Profile | `/calc` | `/api/v1/auth` | `/calc/api/v1/auth/...` |
| Referral | `/calc` | `/api/v1/referral` | `/calc/api/v1/referral/...` |
| Calculation Engine | `/calc` | _(none)_ | `/calc/api/...` |
| AI Orchestrator | `/calc/api/v1/ai` | _(none)_ | `/calc/api/v1/ai/...` |
| Deva Agent | `/calc/api/v1/deva` | _(none)_ | `/calc/api/v1/deva/...` |
| Love Chat | `/calc` | `/api/v1/love-chat` | `/calc/api/v1/love-chat/...` |
| Payment (Razorpay) | `/calc` | `/api/v1/payment` | `/calc/api/v1/payment/...` |
| Reports | `/calc/api/v1` | `/reports` | `/calc/api/v1/reports/...` |
| Places | `/calc/api/v1` | `/places` | `/calc/api/v1/places/...` |
| Admin Panel | _(none)_ | `/admin` | `/admin/...` |
| Admin Auth | `/api/admin` | _(none)_ | `/api/admin/login` |
| Blog (Admin) | _(none)_ | `/admin/blogs` | `/admin/blogs/...` |
| Blog (Public) | `/calc` | `/api/blogs` | `/calc/api/blogs/...` |

---

## 1. Auth Routes
**Source:** `routers/auth_routes.py` → mounted at `/calc/api/v1`

### `POST /calc/api/v1/auth/unified-login`
Unified entry point for all authentication methods.

**Request Body:**
```json
{
  "provider": "guest | google | facebook | email",
  "data": { ... }
}
```

**Provider Payloads:**

| Provider | Data Fields |
|---|---|
| `guest` | `device_id` (optional), `preferred_language` |
| `google` | `token` (Google ID token) |
| `facebook` | `token` (Facebook access token) |
| `email` | `email`, `password` |

**Response:**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<token>",
  "token_type": "bearer",
  "user": { ... }
}
```

**Notes:**
- Guest users with an existing `device_id` will reuse their account.
- New guest users receive **2 free credits**.

---

### `POST /calc/api/v1/auth/refresh`
Refresh the access token using a refresh token.

**Request Body:**
```json
{ "refresh_token": "<token>" }
```

**Response:**
```json
{ "access_token": "<new_jwt>", "token_type": "bearer" }
```

---

### `POST /calc/api/v1/auth/logout`
Revoke user refresh token.

**Request Body:**
```json
{ "refresh_token": "<token>" }
```

**Response:**
```json
{ "message": "Logged out successfully" }
```

---

## 2. User / Profile Routes
**Source:** `user_routes.py` → mounted at `/calc/api/v1/auth`

### `GET /calc/api/v1/auth/users/me` 🔒
Get the currently authenticated user's profile.

**Response:** `User` model

---

### `PUT /calc/api/v1/auth/profile` 🔒
Update user profile fields.

**Request Body:**
```json
{
  "full_name": "string",
  "gender": "string",
  "profile_photo": "base64_or_url",
  "preferred_language": "English"
}
```

**Response:** Updated `User` model

---

## 3. Referral Routes
**Source:** `referral_routes.py` → mounted at `/calc/api/v1/referral`

### `GET /calc/api/v1/referral/code` 🔒
Get or generate user's referral code.

**Response:**
```json
{ "referral_code": "ABCD1234" }
```

---

### `GET /calc/api/v1/referral/stats` 🔒
Get referral statistics for the current user.

**Response:**
```json
{
  "referral_code": "ABCD1234",
  "total_referrals": 5,
  "total_earnings": 500.0
}
```

---

### `POST /calc/api/v1/referral/validate`
Validate a referral code (public — no auth required).

**Request Body:**
```json
{ "code": "ABCD1234" }
```

**Response:**
```json
{ "valid": true, "referrer_email": "user@example.com" }
```

---

## 4. Calculation Engine Routes
**Source:** `calculation_routes.py` + inner `calculation-main` app → mounted at `/calc`

Routes are forwarded from the embedded Calculation Engine FastAPI app. Paths from that engine originally start with `/calc` — the prefix is stripped before re-mounting.

**Common calculation paths (illustrative):**
- `GET /calc/api/horoscope/{request_id}` — Fetch calculated horoscope
- `POST /calc/api/calculate` — Run a new calculation

### `POST /calc/api/horoscope/store` 🔒
Store a previously calculated horoscope for an authenticated user.
Compresses the data and saves it to MongoDB.

**Query Params:**
| Param | Type | Description |
|---|---|---|
| `request_id` | string | ID of the horoscope in the calculation cache |

**Response:**
```json
{
  "status": "success",
  "message": "Horoscope compressed and stored successfully",
  "user": "user@example.com",
  "request_id": "<id>",
  "chunks_stored": 4
}
```

---

## 5. AI Orchestrator Routes
**Source:** `ai_routes.py` → mounted at `/calc/api/v1/ai`

### `GET /calc/api/v1/ai/`
Service health check.

**Response:**
```json
{ "service": "AI Orchestrator", "status": "operational", "version": "1.0.0" }
```

---

### `POST /calc/api/v1/ai/analyze` 🔒
Analyze a stored horoscope using the AI orchestrator.
**Costs 1 credit.**

**Request Body:**
```json
{
  "request_id": "<horoscope_request_id>",
  "analysis_type": "full"
}
```
`analysis_type` options: `full`, `summary`, `birth_chart`, `dasha`, `d_series`

**Response:**
```json
{
  "status": "success",
  "analysis": { ... },
  "tokens_used": 1
}
```

**Errors:**
- `402` — Insufficient credits
- `404` — Horoscope not found

---

### `GET /calc/api/v1/ai/models`
List available AI models.

**Response:**
```json
{
  "models": [
    { "name": "gpt-4", "provider": "openai", "status": "available" },
    { "name": "gemini-pro", "provider": "google", "status": "available" }
  ]
}
```

---

### `POST /calc/api/v1/ai/chat` 🔒
Chat with the Vedic Astrologer (powered by Vertex AI).

**Request Body:**
```json
{
  "query": "What does my birth chart say about career?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:**
```json
{ "response": "<ai_text>", "status": "success" }
```

---

## 6. Deva Agent Routes
**Source:** `deva_routes.py` → mounted at `/calc/api/v1/deva`
_Powered by Vertex AI + AutoGen multi-agent council_

### `GET /calc/api/v1/deva/`
Service health check.

---

### `POST /calc/api/v1/deva/chat` 🔒
Chat with Deva Agent (multi-agent Vedic astrology council).
**Costs 1 credit per question.**

**Request Body:**
```json
{
  "question": "What is my current Mahadasha?",
  "request_id": "<optional_horoscope_id>",
  "preferred_language": "English"
}
```
- If `request_id` is omitted, the most recent stored horoscope is used.
- If no horoscope is found, falls back to birth-details-based analysis.

**Response:**
```json
{
  "status": "success",
  "response": "<astrology insight text>",
  "conversation_id": "<mongo_id>",
  "has_horoscope_data": true,
  "questions_remaining": 9,
  "total_questions_asked": 1
}
```

**Special status values:**
| Status | Meaning |
|---|---|
| `success` | Normal response |
| `limit_reached` | Credits exhausted |
| `no_data` | No horoscope found |

**Errors:**
- `403` — Guest user hit 2-question limit
- `500` — Agent failure (credit auto-refunded)

---

### `GET /calc/api/v1/deva/conversations` 🔒
List all Deva conversations for the current user.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `limit` | 50 | Max records to return |
| `skip` | 0 | Offset for pagination |

---

### `GET /calc/api/v1/deva/chat/history` 🔒
Get full conversation history.

**Query Params:**
| Param | Description |
|---|---|
| `request_id` | (Optional) Filter by horoscope ID |

**Response:**
```json
{
  "history": [
    {
      "question": "...",
      "response": "...",
      "created_at": "2026-03-01T10:00:00",
      "conversation_id": "<id>"
    }
  ]
}
```

---

### `GET /calc/api/v1/deva/horoscope/status` 🔒
Check if the user has a stored horoscope.

**Response:**
```json
{
  "has_horoscope": true,
  "request_id": "<id>",
  "created_at": "2026-01-15T08:30:00"
}
```

---

### `POST /calc/api/v1/deva/birth-details` 🔒
Save user's birth details for AI astrology.

**Request Body:**
```json
{
  "name": "Hardik",
  "gender": "Male",
  "date_of_birth": "1998-05-10",
  "time_of_birth": "14:30",
  "place_of_birth": "Mumbai",
  "latitude": 19.076,
  "longitude": 72.877,
  "preferred_language": "English"
}
```

---

### `GET /calc/api/v1/deva/birth-details` 🔒
Retrieve saved birth details.

**Response:**
```json
{
  "has_details": true,
  "details": {
    "date_of_birth": "1998-05-10",
    "time_of_birth": "14:30",
    "place_of_birth": "Mumbai",
    "latitude": 19.076,
    "longitude": 72.877,
    "preferred_language": "English"
  }
}
```

---

### `POST /calc/api/v1/deva/birth-details/reset` 🔒
Reset all user data — deletes birth details and all horoscopes.
_(Chat history, credits, and account are preserved.)_

**Response:**
```json
{ "status": "success", "message": "User data reset successfully" }
```

---

### `GET /calc/api/v1/deva/question-status` 🔒
Get detailed question tracking status including recent conversations.

**Response:**
```json
{
  "questions_asked": 3,
  "feedback_given": 1,
  "questions_remaining": 7,
  "total_limit": 5,
  "recent_conversations": [ ... ]
}
```

---

## 7. Love Chat Routes (AstroEngine 2.0)
**Source:** `love_chat_routes.py` → mounted at `/calc`

### `POST /calc/api/v1/love-chat/analyze` 🔒
Analyze a love/relationship question using AstroEngine 2.0.
**Costs 1 credit.**

**Request Body:**
```json
{
  "question": "Will I meet my soulmate this year?",
  "request_id": "<optional_horoscope_id>",
  "birth_details": { ... }
}
```

**Response:**
```json
{
  "status": "success",
  "analysis": "<analysis text>",
  "domain": "Love/Dating",
  "confidence": 0.9,
  "metrics": { ... },
  "credits_remaining": 8
}
```

**Errors:**
- `402` — Insufficient credits (credit refunded on failure)

---

### `POST /calc/api/v1/love-chat/generate-horoscope` 🔒
Generate and store a horoscope using AstroEngine's calculation engine.

**Request Body:**
```json
{
  "name": "Hardik",
  "birth_date": "1998-05-10",
  "birth_time": "14:30",
  "latitude": 19.076,
  "longitude": 72.877,
  "timezone": 5.5,
  "place": "Mumbai"
}
```

**Response:**
```json
{
  "status": "success",
  "horoscope_id": "<request_id>",
  "message": "Horoscope generated and stored successfully",
  "chunks_count": 4
}
```

---

### `GET /calc/api/v1/love-chat/domains`
Get all available astrology analysis domains (public).

**Response:**
```json
{
  "domains": [
    {
      "name": "Love/Dating",
      "description": "...",
      "focus_houses": [5, 7],
      "key_planets": ["Venus", "Moon"]
    }
  ]
}
```

---

### `GET /calc/api/v1/love-chat/history` 🔒
Fetch the user's love chat conversation history.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `limit` | 10 | Max records to return |

---

## 8. Payment Routes (Razorpay)
**Source:** `razorpay_service/api.py` → mounted at `/calc/api/v1/payment`

### `POST /calc/api/v1/payment/create-order` 🔒
Create a Razorpay order for a credit plan.

**Request Body:**
```json
{ "plan_id": "basic" }
```

**Response:**
```json
{
  "order_id": "order_xxx",
  "amount": 9900,
  "currency": "INR",
  "key": "<razorpay_key_id>",
  "user_email": "user@example.com",
  "user_name": "Hardik"
}
```

---

### `POST /calc/api/v1/payment/verify-payment` 🔒
Verify Razorpay signature and credit the user's account.

**Request Body:**
```json
{
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "<hmac_sha256>",
  "plan_id": "basic"
}
```

**Response:**
```json
{ "status": "success", "new_balance": 15 }
```

---

### `POST /calc/api/v1/payment/webhook`
Razorpay webhook handler (public — Razorpay calls this).

---

## 9. Report Routes
**Source:** `routers/report_routes.py` → mounted at `/calc/api/v1/reports`
_Reports are generated asynchronously using the R1 council AI engine._

### `POST /calc/api/v1/reports/generate` 🔒
Queue a new report generation job.

**Request Body:**
```json
{
  "report_type": "full",
  "birth_details_id": "<optional>"
}
```

**Response:**
```json
{
  "job_id": "<uuid>",
  "status": "pending",
  "message": "Queued for generation",
  "estimated_time": "30 seconds"
}
```

---

### `GET /calc/api/v1/reports/status/{job_id}` 🔒
Poll for report job status.

**Response:**
```json
{
  "job_id": "<uuid>",
  "status": "processing | completed | failed",
  "message": "Consulting the Star Council (Agents)...",
  "download_url": "https://...",
  "estimated_time": "2 minutes remaining"
}
```

> **Note:** Job state is stored in-memory only. It resets on server restart. Production should use Redis.

---

## 10. Place Search Routes
**Source:** `routers/place_routes.py` → mounted at `/calc/api/v1/places`
_Backed by the Photon API (OpenStreetMap data)_

### `GET /calc/api/v1/places/search`
Search for places by name (public — no auth required).

**Query Params:**
| Param | Required | Default | Description |
|---|---|---|---|
| `q` | ✅ | — | Place name (min 2 chars) |
| `limit` | ❌ | 10 | Max results (1–50) |
| `lang` | ❌ | `en` | Language code |

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "results": [
    {
      "name": "Mumbai",
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "latitude": 19.076,
      "longitude": 72.877,
      "label": "Mumbai, Maharashtra, India",
      "raw": { ... }
    }
  ]
}
```

---

## 11. Admin Panel Routes
**Source:** `app/admin/routes.py` → mounted at `/admin`

> ⚠️ Admin verification is currently placeholder-only (`verify_admin`). Not production-secured via JWT yet.

### `GET /admin/stats`
Get system-wide analytics and user statistics.

**Response:**
```json
{
  "total_users": 1200,
  "banned_users": 3,
  "total_credits": 15000,
  "new_users_24h": 45,
  "new_users_7d": 210,
  "new_users_30d": 800,
  "timestamp": "2026-03-29T13:00:00"
}
```

---

### `GET /admin/users`
List all users with optional search filter.

**Query Params:**
| Param | Description |
|---|---|
| `search` | Regex search across email, username, full_name |
| `email_search` | (Legacy) Same as `search` |
| `skip` | Pagination offset |
| `limit` | Overridden to 10,000 internally |

---

### `GET /admin/users/{user_id}`
Get a single user's full profile.

---

### `POST /admin/users/{user_id}/credits/add`
Add credits to a user.

**Request Body:**
```json
{ "amount": 10, "reason": "Promotional reward" }
```

---

### `POST /admin/users/{user_id}/credits/deduct`
Deduct credits from a user.

**Request Body:**
```json
{ "amount": 5, "reason": "Manual correction" }
```

---

### `POST /admin/users/ban`
Ban or unban a user.

**Request Body:**
```json
{
  "user_id": "<mongo_object_id>",
  "is_banned": true,
  "reason": "Abusive behavior"
}
```

---

### `DELETE /admin/users/{user_id}`
Permanently delete a user and all associated data (horoscopes, conversations, tokens, etc.).

---

### `GET /admin/logs`
Get recent admin audit logs.

**Query Params:**
| Param | Default | Description |
|---|---|---|
| `limit` | 50 | Number of logs |

---

## 12. Admin Auth Routes
**Source:** `app/admin/auth.py` → mounted at `/api/admin`

### `POST /api/admin/login`
Admin login using email/password form. Returns a JWT with `role: admin` claim.

**Form Data (x-www-form-urlencoded):**
```
username=admin@example.com
password=supersecretpassword
```

**Response:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

**Errors:**
- `401` — Wrong credentials
- `403` — User exists but does not have admin role

---

## 13. Blog Routes

### Admin Blog Routes
**Source:** `app/admin/blog_routes.py` → mounted at `/admin/blogs`

_(Endpoint details to be documented from `blog_routes.py`)_

### Public Blog Routes
**Source:** `app/admin/blog_routes.py` → mounted at `/calc/api/blogs`

---

## 14. Root & Debug Endpoints

### `GET /`
Returns API status and available endpoint groups.

### `GET /health`
Health check for the service (used by App Engine).

**Response:**
```json
{ "status": "healthy", "service": "astrology-backend" }
```

### `GET /calc/chk`
Debug endpoint. Shows which routers loaded successfully and lists all registered routes.

**Response:**
```json
{
  "status": "debug",
  "errors": { ... },
  "routers": {
    "calculation": true,
    "ai": true,
    "deva": true
  },
  "all_routes": ["/", "/calc/api/v1/auth/unified-login", "..."]
}
```

---

## Error Reference

| Code | Meaning |
|---|---|
| `400` | Bad request / invalid input |
| `401` | Unauthorized — missing or invalid token |
| `402` | Payment required — insufficient credits |
| `403` | Forbidden — guest limit reached or not admin |
| `404` | Resource not found |
| `500` | Internal server error |
| `503` | External service unavailable (e.g., Photon API) |

---

## Credit System

| Action | Cost |
|---|---|
| Deva Agent chat | 1 credit |
| Love Chat analyze | 1 credit |
| AI Orchestrator analyze | 1 credit |
| New guest user signup | +2 credits (free) |
| Payment (plan-based) | +N credits via Razorpay |

> Credits are refunded automatically if the AI call fails with an internal server error.

---

_Generated: 2026-03-29 | Source: `main.py` and all route files_
