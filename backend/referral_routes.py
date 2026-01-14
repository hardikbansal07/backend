import secrets
import string
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_active_user
from models import User
from mongo import mongo_db

router = APIRouter(prefix="/api/v1/referral", tags=["referral"])

def generate_referral_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

class ReferralStats(BaseModel):
    referral_code: str
    total_referrals: int
    total_earnings: float

class ValidateReferralRequest(BaseModel):
    code: str

class ValidateReferralResponse(BaseModel):
    valid: bool
    referrer_email: Optional[str] = None

@router.get("/code")
async def get_or_create_referral_code(current_user: User = Depends(get_current_active_user)):
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if current_user.referral_code:
        return {"referral_code": current_user.referral_code}
    
    code = generate_referral_code()
    while await mongo_db.db.users.find_one({"referral_code": code}):
        code = generate_referral_code()
    
    await mongo_db.db.users.update_one(
        {"email": current_user.email},
        {"$set": {"referral_code": code, "updated_at": datetime.utcnow()}}
    )
    
    return {"referral_code": code}

@router.get("/stats", response_model=ReferralStats)
async def get_referral_stats(current_user: User = Depends(get_current_active_user)):
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    user_data = await mongo_db.db.users.find_one({"email": current_user.email})
    if not user_data or not user_data.get("referral_code"):
        code_response = await get_or_create_referral_code(current_user)
        referral_code = code_response["referral_code"]
    else:
        referral_code = user_data["referral_code"]
    
    total_referrals = await mongo_db.db.referrals.count_documents({
        "referrer_id": current_user.email,
        "status": "completed"
    })
    
    total_earnings = total_referrals * 100.0
    
    return ReferralStats(
        referral_code=referral_code,
        total_referrals=total_referrals,
        total_earnings=total_earnings
    )

@router.post("/validate", response_model=ValidateReferralResponse)
async def validate_referral_code(request: ValidateReferralRequest):
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    if not request.code or len(request.code) < 6:
        return ValidateReferralResponse(valid=False)
    
    referrer = await mongo_db.db.users.find_one({"referral_code": request.code})
    
    if referrer:
        return ValidateReferralResponse(valid=True, referrer_email=referrer["email"])
    else:
        return ValidateReferralResponse(valid=False)
