# Frontend-Backend Integration Guide

## Architecture Overview

### System Components

1. **Main Frontend** (`/frontend`) - Port 3000
   - Landing page, services, blogs, AI astrology
   - Authentication (Google OAuth + Email/Password)
   - Redirects `/horoscope` to backend-served horoscope app

2. **Horoscope Frontend** (`/backend/calculation/calculation-main/frontend`) - Served by backend
   - Standalone horoscope calculation dashboard
   - Integrated authentication (shares auth with main frontend)
   - Auto-saves calculations to MongoDB for authenticated users
   - Accessed via: `http://localhost:8080/horoscope/`

3. **Backend API** (`/backend`) - Port 8080
   - FastAPI server
   - Authentication endpoints: `/api/v1/auth/*`
   - Calculation endpoints: `/calc/api/*`
   - AI endpoints: `/api/v1/ai/*`
   - Serves horoscope frontend as static files

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env file with your MongoDB and Google OAuth credentials
```

### 2. Build Horoscope Frontend

```bash
cd backend/calculation/calculation-main/frontend

# Install dependencies
npm install

# Build for production
npm run build

# This creates /dist folder that backend will serve
```

### 3. Start Backend Server

```bash
cd backend
python start_server.py
# Backend runs on http://localhost:8080
# Horoscope frontend available at http://localhost:8080/horoscope/
```

### 4. Main Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

## Authentication Flow

### Email/Password Authentication

1. User registers/logs in via main frontend (`/auth`) or horoscope frontend
2. Backend validates credentials and returns JWT token
3. Token stored in `localStorage` as `astro_user`
4. All API calls include `Authorization: Bearer <token>` header

### Google OAuth Authentication

1. User clicks "Sign in with Google"
2. Google returns credential token
3. Frontend sends token to `/api/v1/auth/google/login`
4. Backend verifies token with Google API
5. Backend creates/retrieves user and returns JWT
6. JWT stored in `localStorage`

## Horoscope Calculation Flow

### For Authenticated Users

1. User logs into horoscope frontend
2. Fills birth details form
3. Clicks "Generate Horoscope"
4. Frontend calls `/calc/api/horoscope` (calculation engine)
5. On success, frontend automatically calls `/calc/api/horoscope/store`
6. Backend:
   - Fetches calculation from memory
   - Fetches Vimsottari Dasha data
   - Compresses horoscope using 2-layer compression
   - Stores in MongoDB under user's email
7. User can access saved horoscopes later

### For Unauthenticated Users

- Must log in first
- Cannot access horoscope dashboard without authentication
- Shown login page instead

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register with email/password
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/google/login` - Login with Google OAuth
- `GET /api/v1/auth/users/me` - Get current user info

### Calculation
- `POST /calc/api/horoscope` - Generate horoscope
- `POST /calc/api/horoscope/store` - Store horoscope (authenticated)
- `GET /calc/api/dhasa/vimsottari` - Fetch Vimsottari Dasha
- Other dasha endpoints available

### AI
- `POST /api/v1/ai/*` - AI orchestration endpoints

## Environment Variables

### Backend (`.env`)
```env
MONGO_URI=mongodb+srv://...
DB_NAME=unified_backend
SECRET_KEY=your-secret-key-32-chars
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Main Frontend (`/frontend/.env`)
```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_API_PROXY=http://127.0.0.1:8080
```

### Horoscope Frontend (`/backend/calculation/calculation-main/frontend/.env`)
```env
VITE_API_BASE=
VITE_API_PROXY=http://127.0.0.1:8080
```

## Storage Structure

MongoDB Collections:
- `users` - User accounts (email, hashed password, profile)
- `horoscopes` - Compressed horoscope data chunks
- `agent_events` - AI orchestration events

## Development vs Production

### Development
- Main frontend: `npm run dev` (port 3000)
- Horoscope frontend: Build once, served by backend
- Backend: `python start_server.py` (port 8080)

### Production
- Build main frontend: `npm run build`
- Build horoscope frontend: Already built
- Deploy backend with both static frontends
- Configure CORS and allowed origins
- Use production MongoDB cluster
- Use HTTPS

## Troubleshooting

### Horoscope page shows blank
- Check if horoscope frontend is built: `/backend/calculation/calculation-main/frontend/dist` should exist
- Rebuild: `cd backend/calculation/calculation-main/frontend && npm run build`

### Authentication fails
- Verify Google Client ID matches in both frontends
- Check backend `.env` has correct Google credentials
- Verify MongoDB connection string

### API calls fail
- Check backend is running on port 8080
- Verify proxy settings in vite.config files
- Check CORS configuration in backend

### Auto-save doesn't work
- User must be logged in
- Check browser console for errors
- Verify `/calc/api/horoscope/store` endpoint is accessible
- Check MongoDB connection

## Testing the Integration

1. **Test Authentication**
   ```bash
   # Start backend
   cd backend && python start_server.py
   
   # In browser, go to http://localhost:8080/horoscope/
   # Try logging in with email/password
   ```

2. **Test Horoscope Calculation**
   - After login, fill birth details
   - Generate horoscope
   - Check browser console for "Horoscope saved to database" message
   - Verify data in MongoDB

3. **Test Main Frontend Redirect**
   ```bash
   # Start main frontend
   cd frontend && npm run dev
   
   # Go to http://localhost:3000/horoscope
   # Should redirect to http://localhost:8080/horoscope/
   ```

## Key Changes Made

1. ✅ Added authentication to horoscope frontend
2. ✅ Backend serves horoscope frontend as static files
3. ✅ Main frontend redirects `/horoscope` to backend
4. ✅ Auto-save horoscopes for authenticated users
5. ✅ Shared authentication state via localStorage
6. ✅ API calls include auth headers
7. ✅ Google OAuth integration in both frontends
