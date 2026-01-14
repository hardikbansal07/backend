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

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    username: Optional[str] = None
    full_name: Optional[str] = None
    referral_code: Optional[str] = None

@router.post("/register", response_model=User)
async def register_user(user: UserRegister):
    import secrets
    import string
    
    # Debug password length
    print(f"DEBUG: Registering user {user.email}, password length: {len(user.password)}")
    
    try:
        if mongo_db.db is None:
            raise HTTPException(status_code=500, detail="Database connection failed")

        existing_user = await mongo_db.db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        def generate_referral_code(length=8):
            characters = string.ascii_uppercase + string.digits
            return ''.join(secrets.choice(characters) for _ in range(length))
        
        new_referral_code = generate_referral_code()
        while await mongo_db.db.users.find_one({"referral_code": new_referral_code}):
            new_referral_code = generate_referral_code()

        hashed_password = get_password_hash(user.password)
        user_data = user.model_dump(exclude={"password", "referral_code"})
        user_data["referral_code"] = new_referral_code
        
        user_in_db = UserInDB(
            **user_data,
            hashed_password=hashed_password,
            disabled=False
        )
        
        await mongo_db.db.users.insert_one(user_in_db.model_dump())
        
        if user.referral_code and user.referral_code.strip():
            referrer = await mongo_db.db.users.find_one({"referral_code": user.referral_code.strip()})
            if referrer:
                referral_record = {
                    "referrer_id": referrer["email"],
                    "referee_id": user.email,
                    "code": user.referral_code.strip(),
                    "status": "completed",
                    "reward_amount": 100.0,
                    "created_at": datetime.utcnow()
                }
                await mongo_db.db.referrals.insert_one(referral_record)
        
        return user_in_db
    except HTTPException:
        raise
    except ValueError as e:
        # Catch passlib/bcrypt errors like password too long
        print(f"ValueError in registration: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        import logging
        logging.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=Token)
async def login_for_access_token(login_request: LoginRequest):
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    user_dict = await mongo_db.db.users.find_one({"email": login_request.email})
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserInDB(**user_dict)
    if not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_active timestamp
    await mongo_db.db.users.update_one(
        {"email": user.email},
        {"$set": {"last_active": datetime.utcnow()}}
    )

    # Create access token (15 minutes)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Create refresh token (7 days)
    refresh_token = await create_refresh_token(user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
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
        
        print(f"\n=== PROFILE UPDATE DEBUG ===")
        print(f"User email: {current_user.email}")
        print(f"Received full_name: {profile_data.full_name}")
        print(f"Received profile_photo (is None?): {profile_data.profile_photo is None}")
        if profile_data.profile_photo:
            print(f"Profile photo length: {len(profile_data.profile_photo)}")
            print(f"Profile photo starts with: {profile_data.profile_photo[:50]}")
        
        update_data = {}
        if profile_data.full_name is not None and profile_data.full_name.strip():
            update_data["full_name"] = profile_data.full_name.strip()
            update_data["username"] = profile_data.full_name.strip()
            logger.info(f"Updating full_name to: {profile_data.full_name}")
            print(f"Will update full_name: {profile_data.full_name}")
        
        if profile_data.profile_photo is not None and profile_data.profile_photo.strip():
            photo_size = len(profile_data.profile_photo)
            update_data["profile_photo"] = profile_data.profile_photo
            logger.info(f"Updating profile_photo, size: {photo_size} chars")
            print(f"Will update profile_photo, size: {photo_size}")

        if profile_data.preferred_language is not None and profile_data.preferred_language.strip():
            update_data["preferred_language"] = profile_data.preferred_language.strip()
            logger.info(f"Updating preferred_language to: {profile_data.preferred_language}")
            print(f"Will update preferred_language: {profile_data.preferred_language}")
        
        if not update_data:
            print("ERROR: No data to update!")
            raise HTTPException(status_code=400, detail="No data to update")
        
        update_data["updated_at"] = datetime.utcnow()
        
        print(f"Update data keys: {list(update_data.keys())}")
        logger.info(f"Updating user {current_user.email} with fields: {list(update_data.keys())}")
        
        result = await mongo_db.db.users.update_one(
            {"email": current_user.email},
            {"$set": update_data}
        )
        
        print(f"MongoDB update result - matched: {result.matched_count}, modified: {result.modified_count}")
        logger.info(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.matched_count == 0:
            print("ERROR: User not found in database!")
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_user = await mongo_db.db.users.find_one({"email": current_user.email})
        if not updated_user:
            print("ERROR: Could not fetch updated user!")
            raise HTTPException(status_code=404, detail="User not found after update")
        
        print(f"Updated user has profile_photo: {updated_user.get('profile_photo') is not None}")
        if updated_user.get('profile_photo'):
            print(f"Profile photo in DB, length: {len(updated_user.get('profile_photo', ''))}")
        print("=== END DEBUG ===\n")
        
        logger.info(f"Successfully updated profile for {current_user.email}")
        return User(**updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"EXCEPTION in profile update: {e}")
        logger.error(f"Profile update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

class GoogleAuthRequest(BaseModel):
    google_token: str

@router.post("/google/login", response_model=Token)
async def google_login(auth_request: GoogleAuthRequest):
    """
    Login or register using Google OAuth token
    """
    try:
        # Verify Google token and get user info
        google_user_info = await verify_google_token(auth_request.google_token)
        
        # Get or create user
        user = await get_or_create_google_user(google_user_info)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = await create_refresh_token(user.email)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Exchange refresh token for new access token
    """
    email = await verify_refresh_token(request.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    """
    Revoke refresh token (logout)
    """
    await revoke_refresh_token(request.refresh_token)
    
    return {"message": "Logged out successfully"}
