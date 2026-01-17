from fastapi import Header, HTTPException, status
from mongo import mongo_db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def get_guest_id(x_guest_id: str = Header(None)) -> str:
    """
    Dependency to extract X-GUEST-ID header.
    """
    if not x_guest_id:
        return None
    return x_guest_id

async def check_guest_limit(guest_id: str):
    """
    Check if guest has exceeded the free limit (2 questions).
    """
    if not guest_id:
        return # Skip if no guest_id (should be handled by auth or optional logic)
        
    if mongo_db.db is None:
        logger.error("Database not initialized inside check_guest_limit")
        return # Fail open or closed? Let's assume open for safety but log error

    try:
        usage = await mongo_db.db.guest_usage.find_one({"guest_id": guest_id})
        
        if usage:
            count = usage.get("request_count", 0)
            if count >= 2:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "GUEST_LIMIT_REACHED", 
                        "message": "You've used your 2 free financial insights. Log in to continue tracking your wealth."
                    }
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking guest limit: {e}")
        # Proceed if DB error to avoid blocking user due to system failure
        pass

async def increment_guest_usage(guest_id: str):
    """
    Increment usage count for a guest.
    """
    if not guest_id or mongo_db.db is None:
        return

    try:
        await mongo_db.db.guest_usage.update_one(
            {"guest_id": guest_id},
            {
                "$inc": {"request_count": 1},
                "$set": {"last_active": datetime.utcnow()},
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Failed to increment guest usage: {e}")
