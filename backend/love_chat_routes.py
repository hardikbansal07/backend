"""
Love Chat Router - AstroEngine 2.0 Integration
Connects frontend to AstroEngine 2.0 for love/relationship astrology analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from auth import get_current_active_user
from models import User
from mongo import mongo_db
from horoscope_service import get_user_horoscope
import sys
import os
from pathlib import Path
import logging
import json
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_provider_analysis_error(analysis_text: str) -> bool:
    """Detect upstream/provider failures returned as plain text from agent flow."""
    if not analysis_text:
        return False
    lowered = analysis_text.lower()
    return (
        lowered.startswith("error during analysis:")
        or "503 unavailable" in lowered
        or "status': 'unavailable'" in lowered
        or "\"status\": \"unavailable\"" in lowered
        or "rate limit" in lowered
    )

# Add astroEngine-2.0 to Python path
astro_engine_path = Path(__file__).parent / "astroengine-2.0" / "astroEngine-2.0"
if str(astro_engine_path) not in sys.path:
    sys.path.insert(0, str(astro_engine_path))

# Import AstroEngine components
try:
    from main_agent import MainAgent
    from horoscope_manager import HoroscopeManager
    from api.service import compute_horoscope
    from api.models import HoroscopeRequest, LocationIn
    from horoscope_service import compress_and_store_horoscope
    logger.info("✅ AstroEngine 2.0 modules imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import AstroEngine modules: {e}")
    MainAgent = None
    HoroscopeManager = None


class LoveChatRequest(BaseModel):
    question: str = Field(..., description="User's love/relationship question")
    request_id: Optional[str] = Field(None, description="Horoscope request ID (if exists)")
    birth_details: Optional[Dict[str, Any]] = Field(None, description="Birth details if no horoscope exists")

class DeleteChatRequest(BaseModel):
    conversation_ids: List[str]


class LoveChatResponse(BaseModel):
    status: str
    analysis: str
    domain: str
    confidence: float
    metrics: Dict[str, Any]
    credits_remaining: int


class GenerateHoroscopeRequest(BaseModel):
    name: str
    birth_date: str  # Format: YYYY-MM-DD
    birth_time: str  # Format: HH:MM:SS or HH:MM
    latitude: float
    longitude: float
    timezone: float
    place: str


class DomainsResponse(BaseModel):
    domains: List[Dict[str, Any]]


@router.post("/api/v1/love-chat/analyze", response_model=LoveChatResponse)
async def analyze_love_question(
    request: LoveChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze a love/relationship question using AstroEngine 2.0
    
    Supports queries about:
    - Dating, Romance, Crush
    - Marriage, Spouse
    - Relationship compatibility
    - Love predictions
    """
    credit_deducted = False
    try:
        if not MainAgent:
            raise HTTPException(status_code=500, detail="AstroEngine 2.0 not available")
        
        logger.info(f"[LOVE-CHAT] User {current_user.email} asked: {request.question[:100]}")
        
        # Check credits
        if current_user.credits < 1:
            raise HTTPException(status_code=402, detail="Insufficient credits")
        
        # Deduct 1 credit
        await mongo_db.db.users.update_one(
            {"email": current_user.email},
            {"$inc": {"credits": -1}}
        )
        credit_deducted = True
        current_user.credits -= 1
        logger.info(f"Deducted 1 credit. Remaining: {current_user.credits}")
        
        # Initialize AstroEngine agent
        agent = MainAgent()
        
        # Construct user context with preferences
        user_ctx = dict(request.birth_details) if request.birth_details else {}
        user_ctx["preferred_language"] = getattr(current_user, 'preferred_language', 'English')
        if not user_ctx.get("name"):
             user_ctx["name"] = current_user.full_name or current_user.username or "User"
        if not user_ctx.get("gender"):
             user_ctx["gender"] = getattr(current_user, 'gender', "Unknown")
             
        # Set user identity (email or request_id)
        if request.request_id:
            agent.set_identity(
                request_id=request.request_id, 
                email=current_user.email,
                user_context=user_ctx
            )
            logger.info(f"Using horoscope request_id: {request.request_id}")
        else:
            agent.set_identity(
                email=current_user.email,
                user_context=user_ctx
            )
            logger.info("No request_id provided, using email-based horoscope lookup")
        
        # Run analysis
        analysis_text, metrics = agent.run_flow(request.question)

        # Provider failures can come back as plain text; treat as failed request and refund.
        if _is_provider_analysis_error(analysis_text):
            if credit_deducted:
                await mongo_db.db.users.update_one(
                    {"email": current_user.email},
                    {"$inc": {"credits": 1}}
                )
                credit_deducted = False
                current_user.credits += 1
                logger.info(f"Refunded 1 credit to {current_user.email} due to provider failure")
            raise HTTPException(status_code=503, detail=analysis_text)
        
        # Extract domain/intent from metrics if available
        domain = "Love/Dating"  # Default domain
        confidence = 0.9
        
        # Save conversation to database
        conversation_doc = {
            "user_email": current_user.email,
            "question": request.question,
            "response": analysis_text,
            "domain": domain,
            "confidence": confidence,
            "metrics": metrics,
            "request_id": request.request_id,
            "created_at": datetime.utcnow()
        }
        
        await mongo_db.db.love_chat_conversations.insert_one(conversation_doc)
        logger.info("Saved love chat conversation to database")
        
        return LoveChatResponse(
            status="success",
            analysis=analysis_text,
            domain=domain,
            confidence=confidence,
            metrics=metrics,
            credits_remaining=current_user.credits
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in love chat analysis: {e}", exc_info=True)
        
        # Refund credit on failure
        try:
            if credit_deducted:
                await mongo_db.db.users.update_one(
                    {"email": current_user.email},
                    {"$inc": {"credits": 1}}
                )
                logger.info(f"Refunded 1 credit to {current_user.email} due to error")
        except Exception as refund_error:
            logger.error(f"Failed to refund credit: {refund_error}")
            
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/love-chat/generate-horoscope")
async def generate_horoscope(
    request: GenerateHoroscopeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new horoscope using AstroEngine's calculation engine"""
    try:
        if not HoroscopeManager:
            raise HTTPException(status_code=500, detail="Horoscope Manager not available")
        
        logger.info(f"Generating horoscope for {request.name}")
        
        # Construct proper Location object
        loc = LocationIn(
            place=request.place,
            latitude=request.latitude,
            longitude=request.longitude,
            tzOffset=request.timezone
        )
        
        # Parse datetime
        # request.birth_time might be HH:MM or HH:MM:SS
        time_str = request.birth_time
        if len(time_str.split(':')) == 2:
            time_str += ":00"
            
        dt_str = f"{request.birth_date}T{time_str}"
        birth_dt = datetime.fromisoformat(dt_str)
        
        # Create HoroscopeRequest
        req_obj = HoroscopeRequest(
            birthDateTime=birth_dt,
            location=loc,
            language="en",
            name=request.name  # For legacy/logging support if needed
        )
        
        # Compute using the calculation engine
        stored = compute_horoscope(req_obj)
        
        # Extract response data
        if hasattr(stored.response, 'model_dump'):
            horoscope_data = stored.response.model_dump()
        else:
            horoscope_data = stored.response.dict()
            
        # Save or update birth details in MongoDB so it's persisted for the user BEFORE storing chunks
        birth_details_doc = {
            "user_email": current_user.email,
            "name": request.name,
            "gender": "Unknown", # LoveChat form may not pass gender
            "date_of_birth": request.birth_date,
            "time_of_birth": request.birth_time,
            "place_of_birth": request.place,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "timezone": request.timezone,
            "preferred_language": getattr(current_user, "preferred_language", "English"),
            "updated_at": datetime.utcnow()
        }
        
        await mongo_db.db.user_birth_details.update_one(
            {"user_email": current_user.email},
            {"$set": birth_details_doc},
            upsert=True
        )

        # Store using the service (handles chunking, compression, and MongoDB storage)
        request_id = stored.response.requestId
        store_result = await compress_and_store_horoscope(
            user_email=current_user.email,
            horoscope_data=horoscope_data,
            request_id=request_id
        )

        return {
            "status": "success", 
            "horoscope_id": request_id,
            "message": "Horoscope generated and stored successfully",
            "chunks_count": store_result.get("chunks_count", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating horoscope: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/love-chat/domains", response_model=DomainsResponse)
async def get_available_domains():
    """Get list of all available astrology domains"""
    try:
        patterns_path = astro_engine_path / "patterns.json"
        
        with open(patterns_path, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        
        domains = []
        for name, pattern in patterns.items():
            domains.append({
                "name": name,
                "description": pattern.get("description", ""),
                "focus_houses": pattern.get("focus_houses", []),
                "key_planets": pattern.get("key_planets", [])
            })
        
        return DomainsResponse(domains=domains)
        
    except Exception as e:
        logger.error(f"Error loading domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/love-chat/history")
async def get_chat_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """Get user's love chat conversation history"""
    try:
        cursor = mongo_db.db.love_chat_conversations.find(
            {"user_email": current_user.email}
        ).sort("created_at", -1).limit(limit)
        
        conversations = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and map response to analysis for frontend compatibility
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
            if "response" in conv and "analysis" not in conv:
                conv["analysis"] = conv["response"]
        
        return {
            "status": "success",
            "conversations": conversations,
            "count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/love-chat/history")
async def delete_love_chat_history(
    request: DeleteChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Delete multiple chat history records"""
    try:
        object_ids = []
        for cid in request.conversation_ids:
            try:
                object_ids.append(ObjectId(cid))
            except:
                pass
                
        if not object_ids:
            return {"status": "success", "deleted_count": 0}
            
        result = await mongo_db.db.love_chat_conversations.delete_many({
            "_id": {"$in": object_ids},
            "user_email": current_user.email
        })
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
