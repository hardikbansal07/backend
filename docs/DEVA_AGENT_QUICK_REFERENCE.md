# Deva Agent - Quick Reference

## ❌ Problem
Deva Agent was responding generically: "Please provide your Lagna..." instead of analyzing actual horoscope data.

## ✅ Solution
Fixed data flow to ensure horoscope chunks are:
1. Fetched from MongoDB
2. Reconstructed into complete chart data
3. Validated (meta, lagna, dasha, d_series)
4. Passed to Gemini agents with full JSON context

## 📍 Locations to Configure Gemini

### 1. API Key & Model
**File:** `backend/.env`
```
GEMINI_API_KEY=AIzaSyBeU8JXWCdL2D_g9LmwoYAjNnNOJs8OQUY
GEMINI_MODEL=gemini-2.5-flash
```

### 2. Model Client Builder
**File:** `backend/deva-agent-deva_wow/deva-agent/config/models.py`
```python
def build_chat_completion_client(model: str = "gemini-2.0-flash-exp", api_key: str = None):
    # Reads GEMINI_API_KEY from .env
    # Can override model with GEMINI_MODEL env var
```

### 3. Agent Initialization
**File:** `backend/deva-agent-deva_wow/deva-agent/agents/specialists.py`
```python
model_client = build_chat_completion_client()

lagna_pati = AssistantAgent(
    name="LagnaPati",
    model_client=model_client,  # Uses Gemini
    system_message=load_prompt("d1_lagna_rules.md"),
)
```

**File:** `backend/deva-agent-deva_wow/deva-agent/agents/principals.py`
```python
model_client = build_chat_completion_client()

maha_rishi = AssistantAgent(
    name="MahaRishi",
    model_client=model_client,  # Uses Gemini
    system_message=load_prompt("synthesis_rules.md"),
)
```

## 🔧 How to Change Gemini Model

**Option A - Via Environment Variable:**
```bash
# In backend/.env
GEMINI_MODEL=gemini-2.0-flash-exp
```

**Option B - Update Config File:**
```python
# In backend/deva-agent-deva_wow/deva-agent/config/models.py
def build_chat_completion_client(model: str = "gemini-2.0-flash-exp", ...):
    # Change "gemini-2.0-flash-exp" to your desired model
```

## 🔄 Data Flow

```
User Question
    ↓
Fetch Horoscope (horoscopes collection)
    ↓
Fetch Chunks (horoscope_chunks collection)
    ↓
Reconstruct: { meta, lagna, dasha, d_series }
    ↓
Validate ALL components
    ↓
Pass to Gemini Agents (as JSON)
    ↓
LagnaPati → KalaPurusha → VargaVizier → MahaRishi
    ↓
Return detailed analysis
```

## 📝 What Was Modified

✅ `backend/deva_routes.py`
- Added logging at each step
- Added data validation
- Better error handling

✅ Created `backend/test_deva_flow.py`
- Test script to verify data retrieval

✅ Created documentation
- `DEVA_AGENT_FIX_GUIDE.md` - Comprehensive guide
- `DEVA_AGENT_FIX_DETAILS.md` - Code changes

## 🧪 Test the Fix

```bash
cd backend
python test_deva_flow.py
```

**Expected Output:**
```
✅ Found horoscope:
   User: your_email@example.com
   Request ID: xxx-xxx-xxx

✅ Horoscope data retrieved:
   Keys: ['meta', 'lagna', 'dasha', 'd_series']

📊 Data Components:
   Meta: ✅
   Lagna: ✅
   Dasha: ✅
   D-Series: ✅ - 16 charts

✅ Data flow test PASSED!
```

## 🐛 Debugging

Check backend logs for `[DEVA]` prefix:

```
[DEVA] Chat request from user: email@example.com
[DEVA] Fetching horoscope data for request_id: abc123...
[DEVA] Horoscope data retrieved, keys: ['meta', 'lagna', 'dasha', 'd_series']
[DEVA] Chart data - meta: True, lagna: True, dasha: True, d_series: True
[DEVA] Starting agent analysis for user: email@example.com
[DEVA] Message from LagnaPati: ...analysis...
[DEVA] Message from KalaPurusha: ...analysis...
[DEVA] Final response from MahaRishi extracted
[DEVA] Agent analysis completed successfully
```

If you see `False` values, the data is not being saved to MongoDB.

## ⚠️ If Still Getting Generic Responses

1. **Verify horoscope was saved:** Check MongoDB `horoscopes` collection
2. **Verify chunks were saved:** Check MongoDB `horoscope_chunks` collection
3. **Check request_id matches:** Both should have same request_id
4. **Run test script:** `python test_deva_flow.py`
5. **Check backend logs:** Look for `[DEVA]` messages and errors

## 📞 Key Functions

### Get Horoscope from MongoDB
```python
from horoscope_service import get_user_horoscope

horoscope_data = await get_user_horoscope(
    user_email="user@example.com",
    request_id="request-id-123"
)
```

### Start Deva Chat
```python
# POST /deva/chat
{
    "question": "Tell me about my finances",
    "request_id": "optional-request-id"
}
```

### Check Horoscope Status
```python
# GET /deva/horoscope/status
# Returns: { has_horoscope: true, request_id: "...", created_at: "..." }
```
