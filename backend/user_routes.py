from datetime import timedelta, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, verify_google_token, get_or_create_google_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, verify_refresh_token, revoke_refresh_token,
    create_refresh_token
)
from models import User, UserInDB, Token
from mongo import mongo_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    profile_photo: Optional[str] = None
    preferred_language: Optional[str] = None

@router.put("/profile", response_model=User)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user profile (full_name and profile_photo only)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if mongo_db.db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        update_data = {}
        if profile_data.full_name is not None and profile_data.full_name.strip():
            update_data["full_name"] = profile_data.full_name.strip()
            update_data["username"] = profile_data.full_name.strip()
        
        if profile_data.profile_photo is not None and profile_data.profile_photo.strip():
            update_data["profile_photo"] = profile_data.profile_photo
            
        if profile_data.gender is not None:
            update_data["gender"] = profile_data.gender.strip() if profile_data.gender else None

        if profile_data.preferred_language is not None and profile_data.preferred_language.strip():
            update_data["preferred_language"] = profile_data.preferred_language.strip()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = await mongo_db.db.users.update_one(
            {"email": current_user.email},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_user = await mongo_db.db.users.find_one({"email": current_user.email})
        return User(**updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

