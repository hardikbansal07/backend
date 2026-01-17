# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### **Step 1: Install Dependencies**

```bash
cd backend
pip install -r requirements.txt
```

### **Step 2: Configure Environment**

Edit `.env` file:

```env
# Required: MongoDB Connection
MONGO_URI=mongodb+srv://your-connection-string
DB_NAME=unified_backend

# Required: Authentication Secret
SECRET_KEY=generate-a-strong-secret-key-here-min-32-chars

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

**Generate Strong SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### **Step 3: Start Server**

```bash
python start_server.py
```

Server starts at: **http://localhost:8080**

---

## 📖 API Usage Examples

### **1. Register User**

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "username": "johndoe"
  }'
```

**Response:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2025-12-15T12:00:00Z"
}
```

### **2. Login**

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save this token!** Use it in subsequent requests.

### **3. Calculate Horoscope**

```bash
curl -X POST http://localhost:8080/calc/api/horoscope \
  -H "Content-Type: application/json" \
  -d '{
    "birthDateTime": "1990-05-15T14:30:00",
    "location": {
      "place": "Mumbai, India",
      "latitude": 19.0760,
      "longitude": 72.8777,
      "tzOffset": 5.5
    },
    "ayanamsaMode": "TRUE_CITRA"
  }'
```

**Response:**
```json
{
  "requestId": "a1b2c3d4...",
  "meta": {
    "birthDateTime": "1990-05-15T14:30:00",
    "location": "Mumbai, India"
  },
  "rasiChart": {
    "label": "Rasi (D1)",
    "planets": [...]
  },
  "divisionalCharts": [...],
  "dasha": {...}
}
```

### **4. Store Horoscope (Authenticated)**

```bash
curl -X POST http://localhost:8080/calc/api/horoscope/store \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "a1b2c3d4..."
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Horoscope compressed and stored successfully",
  "user": "user@example.com",
  "request_id": "a1b2c3d4...",
  "chunks_stored": 15
}
```

---

## 🔑 Google OAuth Setup

### **1. Get Google OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: `http://localhost:8080/api/v1/auth/google/callback`
7. Copy **Client ID** and **Client Secret**

### **2. Update .env**

```env
GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
```

### **3. Frontend Integration**

```javascript
// Get Google token from Google Sign-In
const googleToken = "ya29.a0AfH6SMBx..."; // From Google OAuth flow

// Send to backend
fetch('http://localhost:8080/api/v1/auth/google/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ google_token: googleToken })
})
.then(res => res.json())
.then(data => {
  // data.access_token - Use this for authenticated requests
  localStorage.setItem('token', data.access_token);
});
```

---

## 📊 API Documentation

Once server is running, visit:

**Swagger UI:** http://localhost:8080/docs

**ReDoc:** http://localhost:8080/redoc

---

## 🧪 Testing Endpoints

### **Health Check**

```bash
curl http://localhost:8080/health
```

### **Get Current User**

```bash
curl http://localhost:8080/api/v1/auth/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Calculate Horoscope (Quick Test)**

```bash
curl -X POST http://localhost:8080/calc/api/horoscope \
  -H "Content-Type: application/json" \
  -d '{
    "date": "1990-05-15",
    "time": "14:30:00",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "tzOffsetMinutes": 330,
    "name": "Test User"
  }'
```

---

## 📁 Project Structure

```
backend/
├── start_server.py          ← Start here
├── main.py                  ← FastAPI app
├── .env                     ← Configure this
├── requirements.txt         ← Dependencies
│
├── auth.py                  ← Authentication logic
├── user_routes.py           ← Auth endpoints
├── calculation_routes.py    ← Calculation + storage
├── ai_routes.py             ← AI analysis
│
├── compression_service.py   ← Data compression
├── horoscope_service.py     ← Storage service
├── mongo.py                 ← Database
│
├── calculation/             ← Calculation engine
└── ai_orchestrator/         ← AI agents
```

---

## 🔧 Troubleshooting

### **Port Already in Use**

```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8080   # Windows (find PID, then kill)
```

### **MongoDB Connection Failed**

1. Check MONGO_URI in `.env`
2. Verify IP whitelist in MongoDB Atlas
3. Test connection:
```bash
python -c "from pymongo import MongoClient; MongoClient('YOUR_MONGO_URI').admin.command('ping')"
```

### **Import Errors**

```bash
# Verify dependencies installed
pip list | grep fastapi
pip list | grep motor

# Reinstall if needed
pip install -r requirements.txt --force-reinstall
```

### **Authentication Not Working**

1. Check SECRET_KEY is set in `.env`
2. Verify token format: `Authorization: Bearer <token>`
3. Check token expiration (default: 5 hours)

---

## 🎯 What's Working

✅ **User Registration & Login**
✅ **Google OAuth Authentication**
✅ **JWT Token Management**
✅ **Horoscope Calculation Engine**
✅ **Data Compression (80-90% reduction)**
✅ **MongoDB Storage (chunked)**
✅ **Protected Endpoints**
✅ **Complete End-to-End Flow**

---

## 📚 Next Steps

1. **Test the system:** Follow examples above
2. **Add Google OAuth:** Configure credentials
3. **Create frontend:** Integrate with API
4. **Deploy:** Use Docker or cloud platform
5. **Monitor:** Add logging & analytics

---

## 🆘 Need Help?

**Check logs:**
```bash
# Server logs show detailed info
tail -f server.log  # If using log file
```

**Enable debug mode:**
```python
# In start_server.py, add:
log_level="debug"
```

**Test MongoDB:**
```bash
python -c "import asyncio; from mongo import connect_to_mongo; asyncio.run(connect_to_mongo())"
```

---

**Ready to go! 🚀**

Your backend is now fully operational with:
- ✅ Authentication (Email + Google)
- ✅ Calculation Engine
- ✅ Compression Service
- ✅ MongoDB Storage
- ✅ Protected API Endpoints
