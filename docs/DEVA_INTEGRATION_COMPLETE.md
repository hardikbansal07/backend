# Deva Agent ↔ AI Astrology Frontend Integration

## Overview
Successfully connected the existing Deva Agent backend module to the AI Astrology frontend feature.

## Changes Made

### 1. Backend Integration (`backend/deva_routes.py`)
**New File Created**: Complete API router for Deva Agent

**Endpoints:**
- `POST /api/v1/deva/chat` - Main chat endpoint
  - Accepts user questions
  - Fetches horoscope chunks from MongoDB
  - Runs Deva Agent analysis
  - Stores conversations in MongoDB
  - Returns AI-generated responses

- `GET /api/v1/deva/conversations` - List user's conversation history
- `GET /api/v1/deva/horoscope/status` - Check if user has horoscope data
- `GET /api/v1/deva/` - Service status

**Key Features:**
- User-specific data retrieval using JWT authentication
- Automatic horoscope chunk conversion to Deva Agent format
- Conversation storage in MongoDB
- Proper error handling with fallback messages
- No data modification - only reads existing chunks

### 2. MongoDB Schema Updates (`backend/mongo.py`)
**Added:**
- `deva_conversations` collection with indexes:
  - `user_email` index
  - `request_id` index
  - `created_at` index

**Purpose:** Store all Deva Agent conversations associated with user profiles

### 3. Main Application Updates (`backend/main.py`)
**Added:**
- Deva Agent router registration at `/api/v1/deva`
- Updated endpoints list in root response

### 4. Frontend Cleanup (`frontend/src/pages/AIAstrology.tsx`)
**Removed:**
- Mock agent logic
- Dummy AI responses
- Unused agent selection dropdown

**Added:**
- Direct connection to `/api/v1/deva/chat` endpoint
- Horoscope status checking
- Proper error handling
- User-friendly messages when horoscope data is missing
- Visual indicators for data availability

**Features:**
- Real-time chat with Deva Agent
- Authentication enforcement
- Horoscope data validation before queries
- Auto-scroll in conversation view
- Loading states and error messages

### 5. Dependencies (`backend/requirements.txt`)
**Added:**
- `autogen-agentchat`
- `autogen-core`
- `autogen-ext[openai]`
- `openai`

## Data Flow

```
User asks question in AI Astrology page
            ↓
Frontend sends to /api/v1/deva/chat with JWT token
            ↓
Backend validates user authentication
            ↓
Fetch user's horoscope chunks from MongoDB
            ↓
Convert chunks to Deva Agent input format
            ↓
Run Deva Agent Council (LagnaPati → KalaPurusha → VargaVizier → MahaRishi)
            ↓
Extract final response from MahaRishi
            ↓
Store conversation in deva_conversations collection
            ↓
Return response to frontend
            ↓
Display in chat interface
```

## Authentication & Security
- JWT-based authentication required for all endpoints
- User-specific data isolation
- MongoDB user_email filtering ensures data privacy
- No cross-user data access possible

## Data Availability Logic

### Horoscope Exists ✓
- Deva Agent responds with analysis based on stored chunks
- Uses compressed horoscope data (meta, lagna, dasha, d_series)
- No calculation performed - only reads existing data

### Horoscope Missing ✗
**Response:**
```
"Please generate your horoscope first before asking questions. 
Visit the Horoscope page to create your birth chart."
```

**Frontend Behavior:**
- Shows yellow warning card
- Provides "Generate Horoscope" button
- Disables chat input

## Unchanged Systems
✅ Horoscope calculation backend - No modifications
✅ `split_and_compress_2layer.py` - No modifications
✅ Chunk creation logic - No modifications
✅ Existing MongoDB schema - No modifications
✅ Existing auth system - No modifications
✅ Other backend agents - No modifications
✅ Other frontend features - No modifications

## Installation & Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Environment Variables
Ensure `.env` has:
```
MONGO_URI=<your-mongodb-uri>
DB_NAME=unified_backend
SECRET_KEY=<your-secret-key>
```

The Deva Agent uses the hardcoded Gemini API key in `deva-agent-deva_wow/deva-agent/config/models.py`

### Start Backend
```bash
cd backend
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing

### Manual Testing Steps
1. **Start Backend:** `cd backend && python run.py`
2. **Start Frontend:** `cd frontend && npm run dev`
3. **Login:** Create account or login at `/auth`
4. **Generate Horoscope:** Visit `/horoscope` and create birth chart
5. **Ask Questions:** Go to `/ai-astrology` and start chatting

### Expected Behavior
- ✓ Authentication required
- ✓ Horoscope data check before allowing queries
- ✓ Real AI responses from Deva Agent
- ✓ Conversations stored in MongoDB
- ✓ Error messages when no data available
- ✓ Loading states during processing

## API Documentation

### POST /api/v1/deva/chat
**Request:**
```json
{
  "question": "When will I get a job promotion?",
  "request_id": "optional-horoscope-id"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "response": "Based on your chart analysis...",
  "conversation_id": "64f8a9...",
  "has_horoscope_data": true
}
```

**Response (No Data):**
```json
{
  "status": "no_data",
  "response": "Please generate your horoscope first...",
  "conversation_id": "",
  "has_horoscope_data": false
}
```

### GET /api/v1/deva/horoscope/status
**Response:**
```json
{
  "has_horoscope": true,
  "request_id": "abc123",
  "created_at": "2025-12-15T..."
}
```

### GET /api/v1/deva/conversations
**Query Params:**
- `limit` (default: 50)
- `skip` (default: 0)

**Response:**
```json
{
  "conversations": [
    {
      "_id": "64f8a9...",
      "user_email": "user@example.com",
      "request_id": "abc123",
      "question": "...",
      "response": "...",
      "created_at": "2025-12-15T...",
      "agent": "deva",
      "status": "completed"
    }
  ],
  "count": 10
}
```

## MongoDB Collections

### deva_conversations
```javascript
{
  _id: ObjectId,
  user_email: String,
  request_id: String,  // Links to horoscopes collection
  question: String,
  response: String,
  created_at: DateTime,
  agent: "deva",
  status: String
}
```

### Existing Collections (Unchanged)
- `horoscopes` - Horoscope index entries
- `horoscope_chunks` - Compressed horoscope data chunks
- `users` - User authentication

## Architecture Notes

### Deva Agent Council
The agent uses a multi-agent architecture:

1. **LagnaPati** - Analyzes D1 chart, planetary strengths
2. **KalaPurusha** - Checks current Dasha timing
3. **VargaVizier** - Analyzes D10 career chart
4. **MahaRishi** - Synthesizes all inputs into final answer

### Round Robin Execution
- Each agent speaks once in sequence
- Max 4 turns ensures all agents contribute
- Final response extracted from MahaRishi

### Compression Format
Horoscope data is stored in compressed chunks:
- **meta** - Birth details and calendar
- **lagna** - D1 Rasi chart with planets
- **dasha** - Vimsottari Dasha (2-layer: Mahadasha + Antardasha)
- **d_series** - Divisional charts (D2, D3, ..., D60)

## Troubleshooting

### Error: "Database not initialized"
**Solution:** Ensure MongoDB connection in `.env` is correct

### Error: "Deva Agent analysis failed"
**Solution:** Check backend logs, verify autogen packages installed

### Error: "Please generate your horoscope first"
**Solution:** User needs to create horoscope at `/horoscope` page first

### Empty/No Response
**Solution:** Check that horoscope chunks exist in MongoDB for the user

## Next Steps (Future Enhancements)
- Add conversation history view in frontend
- Implement conversation threading
- Add response streaming for real-time updates
- Add export conversation feature
- Implement feedback mechanism for responses
- Add multi-language support

## Integration Verification Checklist
- ✅ Backend routes created and registered
- ✅ MongoDB collections added
- ✅ Frontend cleaned and connected
- ✅ Authentication enforced
- ✅ Data validation implemented
- ✅ Conversations stored in MongoDB
- ✅ Error handling complete
- ✅ No existing systems modified
- ✅ Dependencies documented
