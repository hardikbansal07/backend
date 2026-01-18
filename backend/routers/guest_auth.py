from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import logging
from auth import create_access_token, get_password_hash, create_refresh_token
from models import UserInDB
from mongo import mongo_db

router = APIRouter()
logger = logging.getLogger(__name__)

class GuestLoginRequest(BaseModel):
    date_of_birth: str
    time_of_birth: str
    place_of_birth: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: str = "English"

@router.post("/guest-login")
async def guest_login(details: GuestLoginRequest):
    """
    Create a temporary guest user and return an access token.
    Guests are limited to 2 questions.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        # 1. Generate unique guest ID
        guest_uuid = str(uuid.uuid4())
        guest_email = f"{guest_uuid}@astrocare.guestuser.com"
        
        # 2. Create Guest User
        guest_user = UserInDB(
            email=guest_email,
            username="Guest User",
            full_name="Guest",
            hashed_password=get_password_hash(guest_uuid), # Use UUID as password
            disabled=False,
            is_guest=True,
            credits=2.0, # Strict limit
            role="user",
            preferred_language=details.preferred_language,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await mongo_db.db.users.insert_one(guest_user.dict())
        
        # 3. Save Birth Details
        birth_details = {
            "user_email": guest_email,
            "date_of_birth": details.date_of_birth,
            "time_of_birth": details.time_of_birth,
            "place_of_birth": details.place_of_birth,
            "latitude": details.latitude,
            "longitude": details.longitude,
            "preferred_language": details.preferred_language,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await mongo_db.db.user_birth_details.update_one(
            {"user_email": guest_email},
            {"$set": birth_details},
            upsert=True
        )
        
        # 4. Generate Tokens
        access_token = create_access_token(data={"sub": guest_email})
        refresh_token = await create_refresh_token(guest_email)
        
        logger.info(f"Created guest user: {guest_email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "email": guest_email,
                "is_guest": True,
                "credits": 2
            }
        }

    except Exception as e:
        logger.error(f"Guest login failed: {e}")
        raise HTTPException(status_code=500, detail=f"Guest login failed: {str(e)}")
