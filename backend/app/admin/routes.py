from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from models import CreditRequest, BanRequest, AdminLog, AdminActionType, CreditUpdate
from mongo import mongo_db
from bson import ObjectId
import logging
from datetime import datetime, timedelta

# Update prefix here if needed, or keep it standard and handle prefix in main.py
# In main.py, it was app.include_router(admin_router) without prefix (defined in router)
# The original router had prefix="/admin". 
# The Auth router has prefix="/api/admin".
# We should probably align them or keep them distinct but in same folder.
# Let's keep existing behavior for now to avoid breaking frontend again.
router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

# --- Dependency ---
async def verify_admin():
    """
    Placeholder for JWT admin verification.
    In production, verify the token and check for 'admin' role.
    """
    # TODO: Replace with actual JWT verification logic
    return "admin_id_placeholder"

# --- Endpoints ---

@router.get("/stats", response_model=dict)
async def admin_stats(
    admin_id: str = Depends(verify_admin)
):
    """
    Get user analytics and system stats.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    now = datetime.utcnow()
    
    # 1. Total Users
    total_users = await mongo_db.db.users.count_documents({})
    
    # 2. Banned Users
    banned_users = await mongo_db.db.users.count_documents({"is_banned": True})
    
    # 3. Total Credits (Aggregation)
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$credits"}}}
    ]
    cursor = mongo_db.db.users.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    total_credits = result[0]["total"] if result else 0
    
    # 4. New Users (Time-based)
    stats_24h = await mongo_db.db.users.count_documents({"created_at": {"$gte": now - timedelta(hours=24)}})
    stats_7d = await mongo_db.db.users.count_documents({"created_at": {"$gte": now - timedelta(days=7)}})
    stats_30d = await mongo_db.db.users.count_documents({"created_at": {"$gte": now - timedelta(days=30)}})
    
    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_credits": total_credits,
        "new_users_24h": stats_24h,
        "new_users_7d": stats_7d,
        "new_users_30d": stats_30d,
        "timestamp": now
    }

@router.get("/users", response_model=List[dict])
async def list_users(
    skip: int = 0, 
    limit: int = 1000, 
    email_search: Optional[str] = None,
    search: Optional[str] = None,
    admin_id: str = Depends(verify_admin)
):
    """
    List users with pagination and regex search (email, username, full_name).
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    # HACK: Frontend sends limit=100 which hides users > 100. 
    # Since we can't fix frontend, we force fetch ALL users (up to 10000)
    # so client-side filtering (if any) or just the list works significantly better.
    limit = 10000
    
    query = {}
    
    # Support both new 'search' param and legacy 'email_search'
    search_term = search or email_search
    
    if search_term:
        regex_pattern = {"$regex": search_term, "$options": "i"}
        query["$or"] = [
            {"email": regex_pattern},
            {"username": regex_pattern},
            {"full_name": regex_pattern}
        ]
    
    cursor = mongo_db.db.users.find(query).skip(skip).limit(limit)
    users = []
    async for user in cursor:
        user_dict = user
        user_dict["id"] = str(user["_id"])
        user_dict["_id"] = str(user["_id"]) # Ensure _id is also string for serialization
        if "hashed_password" in user_dict:
             # Validating existence of hashed_password but not removing it
             # if "hashed_password" in user:
             #    del user["hashed_password"]
             pass
        
        # Apply model defaults for display
        # if "credits" not in user_dict:
        #    user_dict["credits"] = 5
            
        users.append(user_dict)
    
    return users

@router.post("/users/{user_id}/credits/add", response_model=dict)
async def add_credits(
    user_id: str,
    request: CreditUpdate,
    admin_id: str = Depends(verify_admin)
):
    """
    Add credits to a specific user.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        user_oid = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = await mongo_db.db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_balance = user.get("credits", 5) # Default to 5 as per User model
    new_balance = old_balance + request.amount

    # Update User
    await mongo_db.db.users.update_one(
        {"_id": user_oid},
        {"$set": {"credits": new_balance}}
    )

    # Audit Log
    log = AdminLog(
        admin_id=admin_id,
        target_user_id=user_id,
        action_type=AdminActionType.CREDIT_CHANGE,
        amount=request.amount,
        reason=request.reason
    )
    await mongo_db.db.admin_logs.insert_one(log.dict())

    logger.info(f"Admin {admin_id} added {request.amount} credits to {user_id}. New Balance: {new_balance}")

    return {
        "message": "Credits added successfully",
        "user_id": user_id,
        "old_balance": old_balance,
        "new_balance": new_balance
    }

@router.post("/users/{user_id}/credits/deduct", response_model=dict)
async def deduct_credits(
    user_id: str,
    request: CreditUpdate,
    admin_id: str = Depends(verify_admin)
):
    """
    Deduct credits from a specific user.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        user_oid = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = await mongo_db.db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_balance = user.get("credits", 5) # Default to 5 as per User model
    new_balance = old_balance - request.amount

    # Optional: Prevent negative balance
    # if new_balance < 0:
    #     raise HTTPException(status_code=400, detail="Insufficient credits")

    # Update User
    await mongo_db.db.users.update_one(
        {"_id": user_oid},
        {"$set": {"credits": new_balance}}
    )

    # Audit Log
    log = AdminLog(
        admin_id=admin_id,
        target_user_id=user_id,
        action_type=AdminActionType.CREDIT_CHANGE,
        amount=-request.amount, # Negative for deduction in log if desired, or keep positive amount but action context implies deduction
        reason=request.reason
    )
    await mongo_db.db.admin_logs.insert_one(log.dict())

    logger.info(f"Admin {admin_id} deducted {request.amount} credits from {user_id}. New Balance: {new_balance}")

    return {
        "message": "Credits deducted successfully",
        "user_id": user_id,
        "old_balance": old_balance,
        "new_balance": new_balance
    }

@router.post("/users/ban", response_model=dict)
async def ban_user(
    request: BanRequest,
    admin_id: str = Depends(verify_admin)
):
    """
    Ban or Unban a user (The Hammer).
    Logs the action in admin_logs.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        user_oid = ObjectId(request.user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = await mongo_db.db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update User
    await mongo_db.db.users.update_one(
        {"_id": user_oid},
        {"$set": {"is_banned": request.is_banned}}
    )

    # Audit Log
    action = AdminActionType.BAN if request.is_banned else AdminActionType.UNBAN
    log = AdminLog(
        admin_id=admin_id,
        target_user_id=request.user_id,
        action_type=action,
        reason=request.reason
    )
    await mongo_db.db.admin_logs.insert_one(log.dict())
    
    status_msg = "banned" if request.is_banned else "unbanned"
    logger.info(f"Admin {admin_id} {status_msg} user {request.user_id}")

    return {
        "message": f"User {status_msg} successfully",
        "user_id": request.user_id,
        "is_banned": request.is_banned
    }

@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    admin_id: str = Depends(verify_admin)
):
    """
    Delete a user permanently.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        user_oid = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    # 1. Fetch user first to get email (needed for other collections)
    user = await mongo_db.db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email = user.get("email")
    uid_str = str(user["_id"])

    # 2. Delete related data (Cascading Delete)
    # Collections using user_id (str)
    await mongo_db.db.api_keys.delete_many({"user_id": uid_str})
    await mongo_db.db.sessions.delete_many({"user_id": uid_str})
    
    # Delete Chats and Messages
    # Find all chat IDs first
    cursor = mongo_db.db.chats.find({"user_id": uid_str}, {"_id": 1})
    chat_ids = [str(doc["_id"]) async for doc in cursor]
    if chat_ids:
        await mongo_db.db.chat_messages.delete_many({"chat_id": {"$in": chat_ids}})
        await mongo_db.db.chats.delete_many({"user_id": uid_str})

    # Collections using email
    if email:
        await mongo_db.db.refresh_tokens.delete_many({"user_email": email})
        await mongo_db.db.horoscopes.delete_many({"user_email": email})
        await mongo_db.db.horoscope_chunks.delete_many({"user_email": email})
        await mongo_db.db.deva_conversations.delete_many({"user_email": email})
        await mongo_db.db.user_birth_details.delete_many({"user_email": email})
        await mongo_db.db.chat_question_tracking.delete_many({"user_email": email})

    # 3. Finally delete the user
    result = await mongo_db.db.users.delete_one({"_id": user_oid})
    
    if result.deleted_count == 0:
        # Should not happen since we found user above, but safety check
        raise HTTPException(status_code=404, detail="User could not be deleted")

    # Audit Log (Using 'BAN' type as a placeholder or could add DELETE to enum)
    log = AdminLog(
        admin_id=admin_id,
        target_user_id=user_id,
        action_type="DELETE", # Ideally add DELETE to AdminActionType enum
        reason="Admin initiated delete"
    )
    await mongo_db.db.admin_logs.insert_one(log.dict())

    logger.info(f"Admin {admin_id} deleted user {user_id}")
    return {"message": "User deleted successfully", "user_id": user_id}

@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    admin_id: str = Depends(verify_admin)
):
    """
    Get a single user's details.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        user_oid = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid User ID format")
        
    user = await mongo_db.db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user["id"] = str(user["_id"])
    user["_id"] = str(user["_id"])
    # Validating existence of hashed_password but not removing it
    # if "hashed_password" in user:
    #    del user["hashed_password"]
        
    # Apply model defaults
    if "credits" not in user:
        user["credits"] = 5
        
    return user

@router.get("/logs", response_model=List[dict])
async def get_admin_logs(
    limit: int = 50,
    admin_id: str = Depends(verify_admin)
):
    """
    Get recent admin logs/transactions.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    cursor = mongo_db.db.admin_logs.find().sort("timestamp", -1).limit(limit)
    logs = []
    async for log in cursor:
        log_dict = log
        log_dict["id"] = str(log["_id"])
        log_dict["_id"] = str(log["_id"])
        logs.append(log_dict)
    return logs
