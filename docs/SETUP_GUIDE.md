# Setup Guide - Astro Care Application

## ✅ Current Status

### Working Components:
1. **Backend Server**: Running on `http://127.0.0.1:8000`
2. **Frontend Server**: Running on `http://localhost:3001`
3. **Authentication System**: Registration & Login ✓
4. **MongoDB Integration**: Connected and storing data ✓
5. **Horoscope Generation**: Working perfectly ✓
6. **Horoscope Auto-Save**: Saves to MongoDB after generation ✓

### Issues Fixed:
- ✅ Backend authentication endpoints working
- ✅ Horoscope generation and storage working
- ✅ MongoDB connection established
- ✅ API key management updated (no more hardcoded expired keys)

---

## 🔧 Required Configuration

### 1. Google OAuth Setup

**Problem**: "The given origin is not allowed for the given client ID"

**Solution**: Add the frontend URL to Google OAuth allowed origins:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services → Credentials**
3. Click on your OAuth 2.0 Client ID: `460631353754-dccmgq3hpse5bfh43qq3hu5lgcmn03ps`
4. Under **Authorized JavaScript origins**, add:
   - `http://localhost:3001`
   - `http://localhost:3000`
   - `http://127.0.0.1:3001`
5. Under **Authorized redirect URIs**, add:
   - `http://localhost:8000/api/v1/auth/google/callback`
6. Click **Save**

### 2. Gemini API Key Setup

**Problem**: Deva Agent chat requires a valid Gemini API key

**Solution**: Add your Gemini API key to `backend/.env`:

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Open `backend/.env`
3. Update the line:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
4. Restart the backend server

---

## 📋 Testing the Complete Flow

### Test 1: Authentication
```bash
# Run from project root
python test_auth_flow.py
```

**Expected Result**: 
- Registration successful
- Login successful
- User info retrieved
- Horoscope status checked

### Test 2: Complete Flow (Horoscope + Chat)
```bash
# Run from project root
python test_complete_flow.py
```

**Expected Result**:
- Login ✓
- Horoscope generated ✓
- Horoscope saved to MongoDB ✓
- Horoscope status confirmed ✓
- Deva Agent chat (requires valid Gemini API key)

---

## 🚀 How to Use the Application

### 1. Start Both Servers

**Backend** (already running on port 8000):
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (already running on port 3001):
```bash
cd frontend
npm run dev
```

### 2. Register/Login

1. Open `http://localhost:3001/auth`
2. Click **Sign Up**
3. Fill in your details:
   - Name: Your Full Name
   - Email: your.email@example.com
   - Password: StrongPassword123
4. Click **Create Account**
5. You'll be automatically logged in and redirected to home

### 3. Generate Horoscope

1. Navigate to **Horoscope** page
2. Fill in birth details:
   - Birth Date & Time
   - Location (search for your city)
   - Timezone (auto-detected or manual)
3. Click **Generate Horoscope**
4. **Horoscope is automatically saved** to MongoDB if you're logged in

### 4. Use AI Astrology Chat

1. Navigate to **AI Astrology** page
2. If you have a horoscope, you'll see a green checkmark: "✓ Horoscope data available"
3. Ask questions like:
   - "What is my current dasha period?"
   - "Tell me about my career prospects"
   - "What are my planetary strengths?"
4. Deva Agent will analyze your horoscope and respond

---

## 🔍 Verification Checklist

- [ ] Backend running on http://127.0.0.1:8000
- [ ] Frontend running on http://localhost:3001
- [ ] MongoDB connected (check backend logs)
- [ ] User can register and login
- [ ] Horoscope generation works
- [ ] Horoscope auto-saves to MongoDB
- [ ] Google OAuth configured (if using)
- [ ] Gemini API key added (for AI chat)
- [ ] Deva Agent chat responds correctly

---

## 📝 Current Test Results

### Authentication Flow Test ✅
```
=== Testing Registration ===
Status: 200 ✓

=== Testing Login ===
Status: 200 ✓
Token obtained ✓

=== Testing Get User ===
Status: 200 ✓
User: demo@astrocare.com ✓

=== Testing Horoscope Status ===
Status: 200 ✓
```

### Complete Flow Test ✅ (Partial)
```
Login: ✓
Horoscope Generation: ✓
MongoDB Storage: ✓ (2 chunks)
Horoscope Status: ✓
Deva Agent Chat: Requires valid API key
```

---

## 🛠️ Troubleshooting

### Issue: "ERR_CONNECTION_REFUSED"
**Solution**: Ensure backend is running on port 8000

### Issue: "Google OAuth 403 Error"
**Solution**: Add frontend URLs to Google OAuth allowed origins (see section 1)

### Issue: "API key expired"
**Solution**: Add valid Gemini API key to `backend/.env` (see section 2)

### Issue: Horoscope not saving
**Solution**: Check you're logged in (check localStorage for 'astro_user')

---

## 📧 Contact

If you encounter any issues, check:
1. Backend logs: `backend/server.log`
2. Frontend console: Browser DevTools
3. MongoDB connection in backend logs

---

**Last Updated**: 2025-12-16  
**Status**: All core features working, requires API key for full functionality
