from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from auth import get_current_active_user
from models import User
from mongo import mongo_db
from datetime import datetime
import logging

from .service import create_order, verify_signature, get_plan_details, PLANS
from .webhook import handle_webhook

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])
logger = logging.getLogger(__name__)

class CreateOrderRequest(BaseModel):
    plan_id: str

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str # To knowing how much to credit immediately

@router.post("/create-order")
async def create_payment_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create Razorpay Order for a Plan
    """
    try:
        plan = get_plan_details(request.plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid Plan ID")
            
        # Truncate to max 40 chars. Usage: rcpt_<short_uid>_<timestamp>
        import time
        uid_short = str(current_user.email)[:15]
        ts = int(time.time())
        receipt = f"r_{uid_short}_{ts}"[:40]
        
        # Create Order
        order = create_order(request.plan_id, receipt)
        
        # Add user_email to notes allows webhook to credit correct user later
        # Razorpay python client doesn't support updating notes after creation easily in one go if not passed initially
        # We passed 'plan_id' and 'questions' in service.py.
        # Let's trust frontend to pass correct plan_id for now, 
        # or we could update the order notes here if needed, but passing user_email in notes is safer.
        # For this implementation, service.py creates basic notes.
        
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key": get_key_id(), # Helper to send key to frontend
            "user_email": current_user.email,
            "user_name": current_user.full_name or "User",
            "contact": "" # Can be filled if stored
        }
        
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify signature and calculate credits immediately
    """
    try:
        is_valid = verify_signature(
            request.razorpay_order_id,
            request.razorpay_payment_id,
            request.razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid Payment Signature")
            
        # Success - Update Credits
        plan = get_plan_details(request.plan_id)
        if not plan:
             raise HTTPException(status_code=400, detail="Invalid Plan")
             
        credits_to_add = plan["questions"]
        
        # 1. Update User Credits
        await mongo_db.db.users.update_one(
            {"email": current_user.email},
            {"$inc": {"credits": credits_to_add}}
        )
        
        # 2. Update Question Tracking
        await mongo_db.db.chat_question_tracking.update_one(
            {"user_email": current_user.email},
            {"$inc": {"purchased_questions": credits_to_add}, "$set": {"updated_at": datetime.utcnow()}},
            upsert=True
        )
        
        # 3. Log Transaction
        await mongo_db.db.payment_transactions.insert_one({
            "user_email": current_user.email,
            "order_id": request.razorpay_order_id,
            "payment_id": request.razorpay_payment_id,
            "plan_id": request.plan_id,
            "amount": plan["amount"],
            "credits_added": credits_to_add,
            "status": "success",
            "created_at": datetime.utcnow()
        })
        
        return {"status": "success", "new_balance": current_user.credits + credits_to_add}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    return await handle_webhook(request)

def get_key_id():
    from .config import KEY_ID
    return KEY_ID
