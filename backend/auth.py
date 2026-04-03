import os
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

async def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google OAuth ID token (JWT) OR Access Token (ya29...) and return user info
    """
    try:
        # 1. Handle Access Token (ya29...) - Typically from Native/Expo Proxy
        if token.startswith("ya29."):
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if resp.status_code != 200:
                    raise ValueError(f"Invalid Access Token: {resp.text}")
                return resp.json()

        # 2. Handle ID Token (JWT) - Typically from Web
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
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
    Get existing user or create new user from Google OAuth data
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    email = google_user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")
    
    # Check if user exists
    existing_user = await mongo_db.db.users.find_one({"email": email})
    
    if existing_user:
        # Update last_active for existing user
        await mongo_db.db.users.update_one(
            {"email": email},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        return UserInDB(**existing_user)
    
    # Create new user
    new_user = UserInDB(
        email=email,
        username=google_user_info.get("name", email.split("@")[0]),
        full_name=google_user_info.get("name"),
        hashed_password="",  # No password for Google OAuth users
        disabled=False,
        last_active=datetime.utcnow()
    )
    
    await mongo_db.db.users.insert_one(new_user.dict())
    logger.info(f"Created new Google OAuth user: {email}")
    
    return new_user

async def verify_facebook_token(token: str) -> Dict[str, Any]:
    """
    Verify Facebook Access Token and return user info
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "access_token": token,
                    "fields": "id,name,email,picture"
                }
            )
            
            if resp.status_code != 200:
                raise ValueError(f"Invalid Facebook Token: {resp.text}")
                
            return resp.json()

    except Exception as e:
        logger.error(f"Facebook token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify Facebook token: {str(e)}"
        )

async def get_or_create_facebook_user(facebook_user_info: Dict[str, Any]) -> UserInDB:
    """
    Get existing user or create new user from Facebook OAuth data
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    email = facebook_user_info.get("email")
    # Facebook might not return email if user didn't grant permission or signed up with phone
    # In such cases, we might need to fallback to ID or ask user for email.
    # For now, we'll construct a placeholder email if missing, but ideally we should require it on frontend.
    if not email:
        facebook_id = facebook_user_info.get("id")
        if not facebook_id:
             raise HTTPException(status_code=400, detail="No email or ID provided by Facebook")
        email = f"{facebook_id}@facebook.user" 
    
    # Check if user exists
    existing_user = await mongo_db.db.users.find_one({"email": email})
    
    if existing_user:
        # Update last_active for existing user
        await mongo_db.db.users.update_one(
            {"email": email},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        return UserInDB(**existing_user)
    
    # Create new user
    new_user = UserInDB(
        email=email,
        username=facebook_user_info.get("name", email.split("@")[0]),
        full_name=facebook_user_info.get("name"),
        hashed_password="",  # No password for OAuth users
        disabled=False,
        last_active=datetime.utcnow()
    )
    
    await mongo_db.db.users.insert_one(new_user.dict())
    logger.info(f"Created new Facebook OAuth user: {email}")
    
    return new_user
