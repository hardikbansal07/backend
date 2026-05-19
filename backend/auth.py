import os
import time
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from mongo import mongo_db
from models import User, UserInDB, Token, TokenData
import logging
import httpx
import json
from google.oauth2 import id_token
from google.auth.transport import requests

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-it-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Access token (60 minutes — needed for long report generation)
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Long-lived refresh token (7 days)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/v1/auth/google/callback")

# Facebook OAuth Configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)







def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_refresh_token(email: str) -> str:
    """
    Create and store a refresh token in the database
    """
    import uuid
    
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Generate unique refresh token
    refresh_token = str(uuid.uuid4())
    
    # Calculate expiration (use utcnow() for offset-naive datetime)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store in database
    await mongo_db.db.refresh_tokens.insert_one({
        "token": refresh_token,
        "user_email": email,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
        "is_revoked": False
    })
    
    logger.info(f"Created refresh token for {email}, expires at {expires_at}")
    return refresh_token

async def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify refresh token and return user email if valid
    """
    if mongo_db.db is None:
        return None
    
    token_doc = await mongo_db.db.refresh_tokens.find_one({"token": token})
    
    if not token_doc:
        logger.warning(f"Refresh token not found: {token[:8]}...")
        return None
    
    # Check if revoked
    if token_doc.get("is_revoked", False):
        logger.warning(f"Refresh token revoked: {token[:8]}...")
        return None
    
    # Check if expired (use utcnow() to match MongoDB's datetime format)
    if token_doc["expires_at"] < datetime.utcnow():
        logger.warning(f"Refresh token expired: {token[:8]}...")
        return None
    
    return token_doc["user_email"]

async def revoke_refresh_token(token: str):
    """
    Revoke a refresh token (logout)
    """
    if mongo_db.db is None:
        return
    
    await mongo_db.db.refresh_tokens.update_one(
        {"token": token},
        {"$set": {"is_revoked": True}}
    )
    logger.info(f"Revoked refresh token: {token[:8]}...")

async def get_user(email: str):
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    user_dict = await mongo_db.db.users.find_one({"email": email})
    if user_dict:
        print(f"DEBUG: Loaded user {email} from DB. Language: {user_dict.get('preferred_language')}")
        return UserInDB(**user_dict)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_oauth2_scheme)):
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = await get_user(email=email)
        return user
    except (JWTError, Exception):
        return None

import asyncio

# ---------------------------------------------------------------------------
# Shared persistent httpx client — avoids creating a new TCP connection per login
# ---------------------------------------------------------------------------
_http_client: Optional[httpx.AsyncClient] = None

def _get_http_client() -> httpx.AsyncClient:
    """Return a module-level shared httpx client (created once, reused across requests)."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))  # 10s timeout
    return _http_client

# ---------------------------------------------------------------------------
# Google cert cache — certs are valid for ~1 hour, no need to fetch every login
# ---------------------------------------------------------------------------
_google_cert_cache: Dict[str, Any] = {}
_google_cert_cache_ts: float = 0.0
_GOOGLE_CERT_TTL_SECONDS = 3600  # 1 hour

class _CachedGoogleRequest:
    """
    Drop-in replacement for google.auth.transport.requests.Request() that
    serves Google's public certificates from an in-memory cache instead of
    hitting the network on every single login.
    """
    def __call__(self, url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        global _google_cert_cache, _google_cert_cache_ts

        now = time.monotonic()
        if _google_cert_cache and (now - _google_cert_cache_ts) < _GOOGLE_CERT_TTL_SECONDS:
            # Return cached certs as a fake Response object
            logger.debug("Google certs served from cache")
            return _FakeResponse(200, _google_cert_cache)

        # Cache miss — fetch fresh certs
        real_request = requests.Request()
        response = real_request(url, method=method, body=body, headers=headers, timeout=timeout, **kwargs)
        try:
            _google_cert_cache = response.data  # type: ignore[attr-defined]
            _google_cert_cache_ts = now
            logger.info("Google public certs refreshed and cached")
        except Exception:
            pass
        return response

class _FakeResponse:
    """Minimal fake response to satisfy google-auth library's expectations."""
    def __init__(self, status, data):
        self.status = status
        self.data = data

_cached_google_request = _CachedGoogleRequest()

async def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google OAuth ID token (JWT) OR Access Token (ya29...) and return user info.
    Uses cert caching and a persistent httpx client to minimise latency.
    """
    try:
        # 1. Handle Access Token (ya29...) — Typically from Native/Expo Proxy
        if token.startswith("ya29."):
            client = _get_http_client()
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code != 200:
                raise ValueError(f"Invalid Access Token: {resp.text}")
            return resp.json()

        # 2. Handle ID Token (JWT) — Typically from Web / React Native Google Sign-In
        # asyncio.to_thread prevents this blocking call from freezing the async event loop.
        # _cached_google_request serves certs from memory after the first login.
        idinfo = await asyncio.to_thread(
            id_token.verify_oauth2_token,
            token,
            _cached_google_request,
            GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer')

        return idinfo

    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Google token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Google token"
        )

async def get_or_create_google_user(google_user_info: Dict[str, Any]) -> UserInDB:
    """
    Get existing user or create new user from Google OAuth data.
    Lookup priority:
    1. By google_id (fast index lookup, prevents duplicates)
    2. By email (link existing account to Google)
    3. Create new user
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    google_id = google_user_info.get("sub")  # Google's unique user ID
    email = google_user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    name = google_user_info.get("name", email.split("@")[0])
    profile_photo = google_user_info.get("picture")
    now = datetime.utcnow()

    # --- Lookup 1: By google_id (fastest, prevents duplicate accounts) ---
    if google_id:
        existing_by_gid = await mongo_db.db.users.find_one({"google_id": google_id})
        if existing_by_gid:
            update_data = {
                "last_active": now,
                "updated_at": now,
                "full_name": name or existing_by_gid.get("full_name"),
                "username": name or existing_by_gid.get("username"),
            }
            if profile_photo:
                update_data["profile_photo"] = profile_photo
            await mongo_db.db.users.update_one(
                {"google_id": google_id},
                {"$set": update_data}
            )
            updated = await mongo_db.db.users.find_one({"google_id": google_id})
            logger.info(f"Google re-login: existing user {google_id}")
            return UserInDB(**updated)

    # --- Lookup 2: By email (link Google to existing email account) ---
    existing_by_email = await mongo_db.db.users.find_one({"email": email})
    if existing_by_email:
        update_data = {
            "last_active": now,
            "updated_at": now,
            "auth_provider": "google",
        }
        if google_id:
            update_data["google_id"] = google_id
        if profile_photo and not existing_by_email.get("profile_photo"):
            update_data["profile_photo"] = profile_photo
        await mongo_db.db.users.update_one(
            {"email": email},
            {"$set": update_data}
        )
        updated = await mongo_db.db.users.find_one({"email": email})
        logger.info(f"Linked Google ID to existing email account: {email}")
        return UserInDB(**updated)

    # --- Lookup 3: Create new user ---
    new_user = UserInDB(
        email=email,
        username=name,
        full_name=name,
        hashed_password="",  # No password for Google OAuth users
        disabled=False,
        last_active=now,
        created_at=now,
        updated_at=now,
        auth_provider="google",
        google_id=google_id,
        profile_photo=profile_photo,
    )

    await mongo_db.db.users.insert_one(new_user.dict())
    logger.info(f"Created new Google OAuth user: {email} (google_id: {google_id})")
    return new_user

async def verify_facebook_token(token: str) -> Dict[str, Any]:
    """
    Verify Facebook Access Token using App-level /debug_token validation.
    This prevents fake or stolen tokens from being accepted.
    Steps:
    1. Validate token via Facebook's /debug_token endpoint (requires App Token)
    2. Confirm token belongs to OUR app (app_id matches)
    3. Confirm token is valid and not expired
    4. Fetch user profile from /me endpoint
    """
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        logger.error("Facebook App ID or Secret not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook OAuth not configured on server"
        )

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Validate token via /debug_token (App-level verification)
            app_access_token = f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"
            debug_resp = await client.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": token,
                    "access_token": app_access_token
                }
            )

            if debug_resp.status_code != 200:
                raise ValueError(f"Token debug failed: {debug_resp.text}")

            debug_data = debug_resp.json().get("data", {})

            # Step 2: Verify the token is valid and belongs to our app
            if not debug_data.get("is_valid", False):
                raise ValueError(f"Token is invalid or expired. Reason: {debug_data.get('error', {}).get('message', 'Unknown')}")

            if str(debug_data.get("app_id")) != str(FACEBOOK_APP_ID):
                raise ValueError("Token does not belong to this application")

            # Step 3: Fetch user profile from /me
            user_resp = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "access_token": token,
                    "fields": "id,name,email,picture.type(large)"
                }
            )

            if user_resp.status_code != 200:
                raise ValueError(f"Failed to fetch user info: {user_resp.text}")

            user_data = user_resp.json()
            logger.info(f"Facebook token verified for user: {user_data.get('id')}")
            return user_data

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Facebook token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Facebook token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Facebook token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Facebook token"
        )

async def get_or_create_facebook_user(facebook_user_info: Dict[str, Any]) -> UserInDB:
    """
    Get existing user or create new user from Facebook OAuth data.
    Lookup priority:
    1. By facebook_id (most reliable — prevents duplicates)
    2. By email (link existing email account to Facebook)
    3. Create new user
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    facebook_id = facebook_user_info.get("id")
    if not facebook_id:
        raise HTTPException(status_code=400, detail="No Facebook user ID returned")

    email = facebook_user_info.get("email")
    name = facebook_user_info.get("name", "")

    # Extract high-res profile photo (picture.type(large))
    profile_photo = None
    picture_data = facebook_user_info.get("picture", {})
    if isinstance(picture_data, dict):
        profile_photo = picture_data.get("data", {}).get("url")

    now = datetime.utcnow()

    # --- Lookup 1: By facebook_id (most reliable, prevents duplicates) ---
    existing_by_fb_id = await mongo_db.db.users.find_one({"facebook_id": facebook_id})
    if existing_by_fb_id:
        # Update profile info on every login (name/photo may change)
        update_data = {
            "last_active": now,
            "updated_at": now,
            "full_name": name or existing_by_fb_id.get("full_name"),
            "username": name or existing_by_fb_id.get("username"),
        }
        if profile_photo:
            update_data["profile_photo"] = profile_photo
        if email and not existing_by_fb_id.get("email", "").endswith("@facebook.user"):
            update_data["email"] = email  # Update email if we got a real one

        await mongo_db.db.users.update_one(
            {"facebook_id": facebook_id},
            {"$set": update_data}
        )
        updated = await mongo_db.db.users.find_one({"facebook_id": facebook_id})
        logger.info(f"Facebook re-login: existing user {facebook_id}")
        return UserInDB(**updated)

    # --- Lookup 2: By email (link Facebook to existing email account) ---
    if email:
        existing_by_email = await mongo_db.db.users.find_one({"email": email})
        if existing_by_email:
            # Link facebook_id to this existing account
            update_data = {
                "facebook_id": facebook_id,
                "auth_provider": "facebook",
                "last_active": now,
                "updated_at": now,
            }
            if profile_photo and not existing_by_email.get("profile_photo"):
                update_data["profile_photo"] = profile_photo

            await mongo_db.db.users.update_one(
                {"email": email},
                {"$set": update_data}
            )
            updated = await mongo_db.db.users.find_one({"email": email})
            logger.info(f"Linked Facebook ID to existing email account: {email}")
            return UserInDB(**updated)

    # --- Lookup 3: Create new user ---
    # For email-less users, use a stable facebook-based identifier
    if not email:
        email = f"facebook_{facebook_id}@astrocare.social"
        logger.warning(f"No email from Facebook for user {facebook_id}, using fallback: {email}")

    new_user = UserInDB(
        email=email,
        username=name or f"user_{facebook_id[:8]}",
        full_name=name,
        hashed_password="",  # No password for OAuth users
        disabled=False,
        last_active=now,
        created_at=now,
        updated_at=now,
        auth_provider="facebook",
        facebook_id=facebook_id,
        profile_photo=profile_photo,
    )

    await mongo_db.db.users.insert_one(new_user.dict())
    logger.info(f"Created new Facebook OAuth user: {email} (fb_id: {facebook_id})")
    return new_user
