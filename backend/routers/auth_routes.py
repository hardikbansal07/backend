from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests
from auth import (
    create_access_token, 
    create_refresh_token, 
    verify_password, 
    get_password_hash,
    verify_google_token,
    get_or_create_google_user,
    verify_facebook_token,
    get_or_create_facebook_user
)
from models import User, UserInDB, Token
from mongo import mongo_db

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# --- Unified Auth ---

class UnifiedLoginRequest(BaseModel):
    provider: str # "google", "guest", "email", "facebook" etc.
    data: Dict[str, Any]

@router.post("/unified-login")
async def unified_login(request: UnifiedLoginRequest):
    """
    Single entry point for all authentication methods.
    payload examples:
    - Guest: { "provider": "guest", "data": { "preferred_language": "English" } }
    - Google: { "provider": "google", "data": { "token": "..." } }
    - Email: { "provider": "email", "data": { "email": "...", "password": "..." } }
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        # === GUEST LOGIN ===
        if request.provider == "guest":
            device_id = request.data.get("device_id")
            preferred_language = request.data.get("preferred_language", "English")
            
            # Try to find existing guest user by device_id
            existing_guest = None
            if device_id:
                existing_guest = await mongo_db.db.users.find_one({
                    "is_guest": True,
                    "device_id": device_id
                })
            
            if existing_guest:
                # Reuse existing guest account
                logger.info(f"Reusing existing guest user: {existing_guest['email']} (device_id: {device_id})")
                
                # Convert MongoDB document to User model (removes ObjectId)
                existing_guest["_id"] = str(existing_guest["_id"])  # Convert ObjectId to string
                user_obj = User(**existing_guest)
                
                access_token = create_access_token(data={"sub": existing_guest["email"]})
                refresh_token = await create_refresh_token(existing_guest["email"])
                
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": user_obj.dict()  # Use Pydantic model's dict() method
                }
            
            # Create new guest user
            guest_uuid = str(uuid.uuid4())
            guest_email = f"{guest_uuid}@astrocare.guestuser.com"
            
            guest_user = UserInDB(
                email=guest_email,
                username="Guest User",
                full_name="Guest",
                hashed_password=get_password_hash(guest_uuid),
                disabled=False,
                is_guest=True,
                device_id=device_id,  # Store device_id for future lookups
                credits=2.0,
                role="user",
                preferred_language=preferred_language,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await mongo_db.db.users.insert_one(guest_user.dict())
            
            access_token = create_access_token(data={"sub": guest_email})
            refresh_token = await create_refresh_token(guest_email)
            
            logger.info(f"Created new guest user: {guest_email} (device_id: {device_id})")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": guest_user.dict()
            }

        # === GOOGLE LOGIN ===
        elif request.provider == "google":
            token = request.data.get("token") or request.data.get("google_token")
            if not token:
                raise HTTPException(status_code=400, detail="Missing google_token in data")

            # Verify Google Token
            google_info = await verify_google_token(token)
            
            # Get/Create User
            user = await get_or_create_google_user(google_info)
            
            # Tokens
            access_token = create_access_token(data={"sub": user.email})
            refresh_token = await create_refresh_token(user.email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user.dict()
            }

        # === FACEBOOK LOGIN ===
        elif request.provider == "facebook":
            token = request.data.get("token")
            if not token:
                raise HTTPException(status_code=400, detail="Missing token in data")

            # Verify Facebook Token
            facebook_info = await verify_facebook_token(token)
            
            # Get/Create User
            user = await get_or_create_facebook_user(facebook_info)
            
            # Tokens
            access_token = create_access_token(data={"sub": user.email})
            refresh_token = await create_refresh_token(user.email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user.dict()
            }
            
        # === EMAIL LOGIN ===
        elif request.provider == "email":
            email = request.data.get("email")
            password = request.data.get("password")
            if not email or not password:
                raise HTTPException(status_code=400, detail="Missing email or password")
                
            user_dict = await mongo_db.db.users.find_one({"email": email})
            if not user_dict:
                raise HTTPException(status_code=401, detail="Incorrect email or password")
            
            user = UserInDB(**user_dict)
            if not verify_password(password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Incorrect email or password")

            # Update Active
            await mongo_db.db.users.update_one({"email": user.email}, {"$set": {"last_active": datetime.utcnow()}})

            access_token = create_access_token(data={"sub": user.email})
            refresh_token = await create_refresh_token(user.email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_dict # Return full user object
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unified login failed: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    from auth import verify_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
    from datetime import timedelta
    
    email = await verify_refresh_token(request.refresh_token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    from auth import revoke_refresh_token
    await revoke_refresh_token(request.refresh_token)
    return {"message": "Logged out successfully"}
