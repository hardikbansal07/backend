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

logger = logging.getLogger(__name__)

router = APIRouter()

# Add astroEngine-2.0 to Python path
astro_engine_path = Path(__file__).parent / "astroengine-2.0" / "astroEngine-2.0"
if str(astro_engine_path) not in sys.path:
    sys.path.insert(0, str(astro_engine_path))

# Import AstroEngine components
try:
    from main_agent import MainAgent
    from horoscope_manager import HoroscopeManager
    logger.info("✅ AstroEngine 2.0 modules imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import AstroEngine modules: {e}")
    MainAgent = None
    HoroscopeManager = None


class LoveChatRequest(BaseModel):
    question: str = Field(..., description="User's love/relationship question")
    request_id: Optional[str] = Field(None, description="Horoscope request ID (if exists)")
    birth_details: Optional[Dict[str, Any]] = Field(None, description="Birth details if no horoscope exists")


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
        current_user.credits -= 1
        logger.info(f"Deducted 1 credit. Remaining: {current_user.credits}")
        
        # Initialize AstroEngine agent
        agent = MainAgent()
        
        # Set user identity (email or request_id)
        if request.request_id:
            agent.set_identity(request_id=request.request_id, email=current_user.email)
            logger.info(f"Using horoscope request_id: {request.request_id}")
        else:
            agent.set_identity(email=current_user.email)
            logger.info("No request_id provided, using email-based horoscope lookup")
        
        # Run analysis
        analysis_text, metrics = agent.run_flow(request.question)
        
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
        
        manager = HoroscopeManager()
        
        horoscope = manager.generate_horoscope(
            name=request.name,
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            place=request.place
        )
        
        if not horoscope:
            raise HTTPException(status_code=500, detail="Failed to generate horoscope")
        
        # Save to database
        horoscope_doc = {
            "user_email": current_user.email,
            "name": request.name,
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "timezone": request.timezone,
            "place": request.place,
            "horoscope_data": horoscope,
            "created_at": datetime.utcnow()
        }
        
        result = await mongo_db.db.astroengine_horoscopes.insert_one(horoscope_doc)
        
        return {
            "status": "success",
            "request_id": str(result.inserted_id),
            "message": "Horoscope generated successfully"
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
        
        # Convert ObjectId to string
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        
        return {
            "status": "success",
            "conversations": conversations,
            "count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
