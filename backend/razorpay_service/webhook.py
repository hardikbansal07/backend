from fastapi import Request, HTTPException, status
import hmac
import hashlib
import json
import logging
from .config import WEBHOOK_SECRET
from mongo import mongo_db
from datetime import datetime

logger = logging.getLogger(__name__)

async def handle_webhook(request: Request):
    """
    Handle Razorpay Webhook Events
    """
    if not WEBHOOK_SECRET:
        logger.warning("Razorpay Webhook Secret not configured. Ignoring webhook.")
        return {"status": "ignored"}

    # Get signature from header
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Signature")

    # Get body as bytes
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')

    # Verify Signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        body_bytes,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.error("Invalid Webhook Signature")
        raise HTTPException(status_code=400, detail="Invalid Signature")

    # Process Event
    try:
        event_data = json.loads(body_str)
        event_type = event_data.get("event")
        
        if event_type == "payment.captured":
            await process_payment_captured(event_data)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return {"status": "failed", "error": str(e)}

async def process_payment_captured(data: dict):
    """
    Process payment.captured event
    """
    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    notes = payment.get("notes", {})
    curr_email = payment.get("email") # Email from payment data if user entered it
    
    # We ideally need user_id or email attached to notes when creating order
    # If not present in notes, we might rely on the payment email or external tracking
    
    # Check if we have plan details in notes (populated during order creation)
    plan_id = notes.get("plan_id")
    questions = notes.get("questions")
    
    if not questions:
        # Fallback if not in notes (e.g. direct link), verify amount to map plan? 
        # For now assume it was passed correctly via order notes
        logger.warning(f"Payment captured but no question count in notes. Payment ID: {payment.get('id')}")
        return

    # User identification: 
    # Option 1: We stored 'user_email' in notes during create_order (Best Practice)
    user_email = notes.get("user_email")
    if not user_email:
        user_email = curr_email # Fallback to payment email
        
    if user_email:
        await add_credits(user_email, int(questions))
        logger.info(f"Webhook: Added {questions} questions to {user_email}")
    else:
        logger.warning("Webhook: Could not identify user to credit.")

async def add_credits(user_email: str, count: int):
    if mongo_db.db is None:
        logger.error("DB not connected in webhook handler")
        return

    # Update question tracking (allowance)
    # Using chat_question_tracking collection logic from deva_routes
    # We increment the 'limit_extension' or similar. 
    # Current existing logic in check_and_update_question_limit uses: 
    # total_limit = base_limit + feedback_given
    # We should add a new field 'purchased_questions' request to tracking
    
    try:
        await mongo_db.db.chat_question_tracking.update_one(
            {"user_email": user_email},
            {"$inc": {"purchased_questions": count}, "$set": {"updated_at": datetime.utcnow()}},
            upsert=True
        )
        
        # Also update User model credits (if used for display or legacy)
        # In deva_routes, it checks tracking for limits BUT also checks user.credits field in step 0.
        # It deducts from user.credits. So we must update THAT too.
        await mongo_db.db.users.update_one(
            {"email": user_email},
            {"$inc": {"credits": count}}
        )
        
    except Exception as e:
        logger.error(f"Failed to add credits to DB: {e}")
