"""
Deva Agent Router
Connects AI Astrology frontend to Deva Agent backend
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from auth import get_current_active_user, get_optional_user
from models import User
from mongo import mongo_db
from horoscope_service import get_user_horoscope
import sys
import os
from pathlib import Path
import logging
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import Vertex AI components
from services.vertex_service import init_vertex_ai, get_model_name
from vertexai.generative_models import GenerativeModel, Content, Part
from services.vertex_service import init_vertex_ai, get_model_name
from vertexai.generative_models import GenerativeModel, Content, Part
from utils.vertex_autogen_client import VertexGenAIClient
from guest_dependency import get_guest_id, check_guest_limit, increment_guest_usage

logger = logging.getLogger(__name__)

router = APIRouter()

# Add deva-agent to Python path
deva_agent_path = Path(__file__).parent / "deva-agent-deva_wow" / "deva-agent"
if str(deva_agent_path) not in sys.path:
    sys.path.insert(0, str(deva_agent_path))

class ChatRequest(BaseModel):
    question: str
    request_id: Optional[str] = None  # Horoscope request ID

class ChatResponse(BaseModel):
    status: str
    response: str
    conversation_id: str
    has_horoscope_data: bool
    questions_remaining: int
    total_questions_asked: int

class BirthDetailsRequest(BaseModel):
    date_of_birth: str  # Format: YYYY-MM-DD
    time_of_birth: str  # Format: HH:MM
    place_of_birth: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: str = "English"

class QuestionFeedbackRequest(BaseModel):
    question_id: str
    question: str  # "Are you satisfied?", "Do you have suggestions?", "Are you willing to pay?"
    answer: str  # "Yes", "No", or the actual suggestion text
    reason: Optional[str] = None  # Optional reason or price range

@router.get("/")
async def deva_status():
    """Deva Agent service status"""
    return {
        "service": "Deva Agent",
        "status": "operational",
        "version": "1.0.0",
        "description": "AI Astrology agent powered by horoscope data (Vertex AI)"
    }

@router.post("/chat", response_model=ChatResponse)
async def deva_chat(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    guest_id: Optional[str] = Depends(get_guest_id)
):
    """
    Chat with Deva Agent
    Requires user authentication OR guest limit check
    """
    try:
        user_email = current_user.email if current_user else f"guest_{guest_id}"
        is_guest = current_user is None
        
        logger.info(f"[DEVA] Chat request from: {user_email}, question: {request.question[:50]}...")
        
        # --- GUEST FLOW ---
        if is_guest:
             if not guest_id:
                 raise HTTPException(status_code=401, detail="Authentication required")
             
             # Check Guest Limit (Raises 403 if limit reached)
             await check_guest_limit(guest_id)
             
             # Create a valid request_id for basic astrology if none (Guests don't have horoscopes usually)
             if not request.request_id:
                 request.request_id = "guest_session"
        
        # --- LOGGED IN FLOW ---
        else:
            # Step 0: Check Credit Balance
            if current_user.credits < 1:
                return ChatResponse(
                    status="limit_reached",
                    response="You have 0 credits. Please recharge your credits to continue asking questions.",
                    conversation_id="",
                    has_horoscope_data=False,
                    questions_remaining=0,
                    total_questions_asked=0
                )
                
            # Deduct 1 Credit
            await mongo_db.db.users.update_one(
                {"email": current_user.email},
                {"$inc": {"credits": -1}}
            )
            current_user.credits -= 1
            logger.info(f"Deducted 1 credit for user {current_user.email}. New balance: {current_user.credits}")

        # Common Logic
        response_text = ""
        has_horoscope_data = False
        
        # Step 1: Find horoscope (Only for logged in users)
        horoscope_data = None
        if not is_guest:
            if not request.request_id:
                logger.info(f"[DEVA] No request_id provided, fetching most recent horoscope for {current_user.email}")
                horoscopes = await mongo_db.db.horoscopes.find({
                    "user_email": current_user.email
                }).sort("created_at", -1).limit(1).to_list(length=1)
                
                if horoscopes:
                    request.request_id = horoscopes[0]["request_id"]
                    logger.info(f"[DEVA] Using request_id: {request.request_id}")
                    
                    # Fetch horoscope Data
                    horoscope_data = await get_user_horoscope(
                        user_email=current_user.email,
                        request_id=request.request_id
                    )
                    has_horoscope_data = True
        
        # Step 2: Generate Response
        if horoscope_data:
            # Full Deva Agent with Horoscope
            chart_data = convert_to_deva_format(horoscope_data)
            logger.info(f"[DEVA] Running Deva Agent analysis (Vertex AI)")
            response_text = await run_deva_agent(
                question=request.question,
                chart_data=chart_data,
                user_email=user_email,
                request_id=request.request_id,
                preferred_language=getattr(current_user, "preferred_language", "English") if current_user else "English"
            )
        else:
            # Basic analysis (Guests or Users without horoscope)
            # Try to get birth details if logged in
            birth_details = None
            if current_user:
                birth_details = await mongo_db.db.user_birth_details.find_one({
                    "user_email": current_user.email
                })
            
            # If guest, use generic/basic context
            # We don't have birth details for guests usually unless passed in request (not in current scope)
            # So we act as a general financial/astrology advisor
            
            if birth_details:
                 response_text = await run_basic_astrology_analysis(
                    question=request.question,
                    birth_details=birth_details,
                    user_email=user_email,
                    preferred_language=getattr(current_user, "preferred_language", "English")
                )
            else:
                # Fallback for guests or no-data users
                # Use run_basic_astrology_analysis with dummy/empty details or a specific guest function
                # For now, let's misuse run_basic_astrology_analysis or create a simpler one?
                # Let's use run_basic_astrology_analysis with handled "Not provided"
                response_text = await run_basic_astrology_analysis(
                    question=request.question,
                    birth_details={}, 
                    user_email=user_email,
                    preferred_language="English"
                )

        # Step 3: Store conversation
        conversation_id = await store_conversation(
            user_email=user_email,
            request_id=request.request_id,
            question=request.question,
            response=response_text
        )
        
        # Step 4: Post-Processing (Increment usage)
        remaining_credits = 0
        if is_guest:
             await increment_guest_usage(guest_id)
        else:
             remaining_credits = int(current_user.credits)

        return ChatResponse(
            status="success",
            response=response_text,
            conversation_id=conversation_id,
            has_horoscope_data=has_horoscope_data,
            questions_remaining=remaining_credits,
            total_questions_asked=0
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deva Agent chat failed: {e}", exc_info=True)
        # Refund credit if user
        if current_user:
            try:
                if mongo_db.db:
                    await mongo_db.db.users.update_one(
                        {"email": current_user.email},
                        {"$inc": {"credits": 1}}
                    )
            except: pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

def convert_to_deva_format(horoscope_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB horoscope chunks to Deva Agent input format"""
    if not horoscope_data:
        return {}
    
    chart_data = {
        "meta": horoscope_data.get("meta", {}),
        "lagna": horoscope_data.get("lagna"),
        "dasha": horoscope_data.get("dasha"),
        "d_series": horoscope_data.get("d_series", {})
    }
    return chart_data

async def run_basic_astrology_analysis(
    question: str,
    birth_details: Dict[str, Any],
    user_email: str,
    preferred_language: str = "English"
) -> str:
    """
    Provide basic astrology analysis using DIRECT Vertex AI
    """
    try:
        init_vertex_ai()
        logger.info(f"[VERTEX-DIRECT] Running Vertex-powered analysis for user: {user_email}")
        
        dob = birth_details.get("date_of_birth", "Not provided")
        tob = birth_details.get("time_of_birth", "Not provided")
        pob = birth_details.get("place_of_birth", "Not provided")
        
        system_instruction = """You are Astro Care AI, an advanced Vedic astrology intelligence system.
IDENTITY: Answer only as "Astro Care AI".
YOUR ROLE: Vedic astrology expert.
INSTRUCTIONS:
1. Provide meaningful astrological insights based on the birth information provided.
2. Use Vedic astrology terminology.
3. Be warm, compassionate, and helpful.
4. Make reasonable astrological interpretations based on the date, time, and place of birth.
5. RESPOND IN {preferred_language} LANGUAGE."""

        user_prompt = f"""BIRTH INFORMATION:
- Date: {dob}
- Time: {tob}
- Place: {pob}
USER'S QUESTION: {question}
Provide a detailed astrological response."""

        model = GenerativeModel(
            get_model_name(),
            system_instruction=[system_instruction]
        )
        
        response = await model.generate_content_async(
            user_prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 8192}
        )
        
        return response.text
    
    except Exception as e:
        logger.error(f"[VERTEX-DIRECT] Vertex AI call failed: {e}", exc_info=True)
        return "I am Astro Care AI. I'm currently experiencing a connection alignment issue. Please try again later."

async def run_deva_agent(
    question: str,
    chart_data: Dict[str, Any],
    user_email: str,
    request_id: str,
    preferred_language: str = "English"
) -> str:
    """
    Run Deva Agent analysis programmatically using VertexGenAIClient
    """
    try:
        logger.info("[DEVA] Starting run_deva_agent")
        # Import Deva Agent components
        from agents.specialists import get_specialists
        from agents.principals import get_principal
        from autogen_agentchat.teams import RoundRobinGroupChat
        
        # Initialize Vertex Client
        logger.info("[DEVA] Initializing VertexGenAIClient")
        client = VertexGenAIClient()
        
        # Initialize agents with Vertex Client
        logger.info("[DEVA] Getting specialists")
        lagna_pati, kala_purusha, varga_vizier = get_specialists(model_client=client)
        logger.info("[DEVA] Getting principal")
        maha_rishi = get_principal(model_client=client)
        
        # Construct context message
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        
        context_message = f"""
SYSTEM CONTEXT: TIME ANCHOR
CURRENT DATE: {date_str}
EXISTING CHART DATA
-----------------------------------
{json.dumps(chart_data, indent=2, default=str)}
-----------------------------------
USER QUESTION: {question}

INSTRUCTIONS FOR COUNCIL:
1. LagnaPati: Analyze D1 strength.
2. KalaPurusha: Check current Dasha relative to TODAY ({date_str}).
3. VargaVizier: Check D10 Career strength.
4. MahaRishi (Astro Care AI): Synthesize final answer.
IMPORTANT: Provide your final response in {preferred_language} language.
"""
        logger.info("[DEVA] Creating council")
        # Create council
        council = RoundRobinGroupChat(
            participants=[lagna_pati, kala_purusha, varga_vizier, maha_rishi],
            max_turns=4
        )
        
        logger.info("[DEVA] Running council stream")
        # Collect messages
        messages = []
        async for msg in council.run_stream(task=context_message):
            try:
                # Debugging msg structure
                source = getattr(msg, "source", "Unknown")
                # Handle potentially missing content or if it's a method
                raw_content = getattr(msg, "content", "")
                if callable(raw_content):
                     content = str(raw_content)
                else:
                     content = str(raw_content)
                
                messages.append({"source": str(source), "content": content})
                
                # Safe logging
                log_snippet = content[:50] if content else "Empty"
                logger.debug(f"[DEVA] {source}: {log_snippet}...")
            except Exception as inner_e:
                logger.error(f"[DEVA] Error processing message stream item: {inner_e} - Type: {type(msg)}")

        
        # Extract final response
        final_response = ""
        for msg in reversed(messages):
            if msg["source"] == "MahaRishi":
                final_response = msg["content"]
                break
        
        if not final_response and messages:
            final_response = messages[-1]["content"]
        
        return final_response or "Unable to generate response."
    
    except Exception as e:
        logger.error(f"[DEVA] Deva Agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Deva Agent analysis failed: {str(e)}"
        )

async def store_conversation(
    user_email: str,
    request_id: str,
    question: str,
    response: str
) -> str:
    """Store Deva Agent conversation in MongoDB"""
    if mongo_db.db is None: return ""
    try:
        conversation_doc = {
            "user_email": user_email,
            "request_id": request_id,
            "question": question,
            "response": response,
            "created_at": datetime.utcnow(),
            "agent": "deva_vertex",
            "status": "completed"
        }
        result = await mongo_db.db.deva_conversations.insert_one(conversation_doc)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"[STORE] Failed: {e}")
        return ""

async def check_and_update_question_limit(user_email: str) -> Dict[str, int]:
    """Check user's question limit"""
    # (Existing logic preserved, compacted for brevity in this replace block, 
    # ensuring no functionality loss from original file)
    if mongo_db.db is None: raise Exception("Database not initialized")
    try:
        tracking = await mongo_db.db.chat_question_tracking.find_one({"user_email": user_email})
        if not tracking:
            tracking = {"user_email": user_email, "questions_asked": 0, "feedback_given": 0}
            await mongo_db.db.chat_question_tracking.insert_one(tracking)
        
        questions_asked = tracking.get("questions_asked", 0)
        feedback_given = tracking.get("feedback_given", 0)
        base_limit = 3
        effective_feedback = min(feedback_given, questions_asked)
        total_limit = base_limit + effective_feedback
        remaining = total_limit - questions_asked
        
        if remaining <= 0:
            return {"allowed": False, "remaining": 0, "total_asked": questions_asked, "feedback_needed": True}
        
        update_op = {"$inc": {"questions_asked": 1}, "$set": {"updated_at": datetime.utcnow()}}
        if feedback_given > questions_asked:
             update_op["$set"]["feedback_given"] = questions_asked
        
        await mongo_db.db.chat_question_tracking.update_one({"user_email": user_email}, update_op)
        return {"allowed": True, "remaining": remaining - 1, "total_asked": questions_asked + 1, "feedback_needed": False}
    except Exception as e:
        logger.error(f"Limit check failed: {e}")
        raise

async def submit_question_feedback(user_email: str, question_id: str, question: str, answer: str, reason: Optional[str] = None) -> bool:
    if mongo_db.db is None: raise Exception("No DB")
    try:
        existing = await mongo_db.db.question_feedback.find_one({"user_email": user_email, "question_id": question_id})
        if existing and not question_id.startswith("general"): return False
        
        await mongo_db.db.question_feedback.insert_one({
            "user_email": user_email, "question_id": question_id, "question": question, 
            "answer": answer, "reason": reason, "created_at": datetime.utcnow()
        })
        await mongo_db.db.chat_question_tracking.update_one(
            {"user_email": user_email}, 
            {"$inc": {"feedback_given": 1}, "$set": {"updated_at": datetime.utcnow()}}, 
            upsert=True
        )
        return True
    except: return False

@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    limit: int = 50,
    skip: int = 0
):
    """
    List user's Deva Agent conversations
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        cursor = mongo_db.db.deva_conversations.find({
            "user_email": current_user.email
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        conversations = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        
        return {
            "conversations": conversations,
            "count": len(conversations)
        }
    
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )

@router.get("/horoscope/status")
async def check_horoscope_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Check if user has horoscope data available
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        logger.info(f"[HOROSCOPE_STATUS] Checking for user: {current_user.email}")
        
        # Fetch latest horoscope by sorting descending on created_at
        cursor = mongo_db.db.horoscopes.find({
            "user_email": current_user.email
        }).sort("created_at", -1).limit(1)
        
        results = await cursor.to_list(length=1)
        horoscope = results[0] if results else None
        
        logger.info(f"[HOROSCOPE_STATUS] Found horoscope: {horoscope is not None}")
        if horoscope:
            logger.info(f"[HOROSCOPE_STATUS] Request ID: {horoscope.get('request_id')}")
            logger.info(f"[HOROSCOPE_STATUS] Created at: {horoscope.get('created_at')}")
        else:
            # Check if ANY horoscopes exist for this user
            count = await mongo_db.db.horoscopes.count_documents({"user_email": current_user.email})
            logger.warning(f"[HOROSCOPE_STATUS] No horoscope found, but count_documents returned: {count}")
            
            # Also check horoscope_chunks
            chunks_count = await mongo_db.db.horoscope_chunks.count_documents({"user_email": current_user.email})
            logger.warning(f"[HOROSCOPE_STATUS] Chunks found for user: {chunks_count}")
        
        return {
            "has_horoscope": horoscope is not None,
            "request_id": horoscope.get("request_id") if horoscope else None,
            "created_at": horoscope.get("created_at") if horoscope else None
        }
    
    except Exception as e:
        logger.error(f"Failed to check horoscope status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check horoscope status: {str(e)}"
        )

@router.post("/birth-details")
async def save_birth_details(
    details: BirthDetailsRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Save user's birth details for AI astrology
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        birth_details = {
            "user_email": current_user.email,
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
            {"user_email": current_user.email},
            {"$set": birth_details},
            upsert=True
        )
        
        logger.info(f"Birth details saved for user: {current_user.email}")
        return {
            "status": "success",
            "message": "Birth details saved successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to save birth details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save birth details: {str(e)}"
        )

@router.get("/chat/history")
async def get_chat_history(
    request_id: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get chat history for the current user
    Optionally filter by request_id (horoscope)
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        query = {"user_email": current_user.email}
        if request_id:
            query["request_id"] = request_id
        
        conversations = await mongo_db.db.deva_conversations.find(
            query
        ).sort("created_at", 1).to_list(length=100)  # Limit to 100 messages
        
        # Format for frontend
        history = []
        for conv in conversations:
            history.append({
                "question": conv.get("question", ""),
                "response": conv.get("response", ""),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "conversation_id": str(conv.get("_id", ""))
            })
        
        return {"history": history}
    
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chat history: {str(e)}"
        )

@router.get("/birth-details")
async def get_birth_details(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's saved birth details
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        details = await mongo_db.db.user_birth_details.find_one({
            "user_email": current_user.email
        })
        
        if not details:
            return {
                "has_details": False,
                "details": None
            }
        
        return {
            "has_details": True,
            "details": {
                "date_of_birth": details.get("date_of_birth"),
                "time_of_birth": details.get("time_of_birth"),
                "place_of_birth": details.get("place_of_birth"),
                "latitude": details.get("latitude"),
                "longitude": details.get("longitude"),
                "preferred_language": details.get("preferred_language", "English")
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get birth details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get birth details: {str(e)}"
        )

@router.post("/question-feedback")
async def submit_feedback(
    feedback: QuestionFeedbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit feedback for a question to unlock more questions
    """
    try:
        success = await submit_question_feedback(
            user_email=current_user.email,
            question_id=feedback.question_id,
            question=feedback.question,
            answer=feedback.answer,
            reason=feedback.reason
        )
        
        if not success:
            # Idempotent response: If already submitted, treat as success but indicate it
            tracking = await mongo_db.db.chat_question_tracking.find_one({
                "user_email": current_user.email
            }) or {}
            
            questions_asked = tracking.get("questions_asked", 0)
            feedback_given = tracking.get("feedback_given", 0)
            
            base_limit = 3
            effective_feedback = min(feedback_given, questions_asked)
            total_limit = base_limit + effective_feedback
            remaining = total_limit - questions_asked
            
            return {
                "status": "already_submitted",
                "message": "Feedback already recorded.",
                "questions_remaining": max(0, remaining),
                "feedback_count": feedback_given
            }
        
        tracking = await mongo_db.db.chat_question_tracking.find_one({
            "user_email": current_user.email
        })
        
        questions_asked = tracking.get("questions_asked", 0)
        feedback_given = tracking.get("feedback_given", 0)
        feedback_given = tracking.get("feedback_given", 0)
        
        # Recalculate remaining with cap logic
        base_limit = 3
        effective_feedback = min(feedback_given, questions_asked)
        total_limit = base_limit + effective_feedback
        remaining = total_limit - questions_asked
        
        return {
            "status": "success",
            "message": "Thank you for your feedback! You've unlocked 1 more question.",
            "questions_remaining": max(0, remaining),
            "feedback_count": feedback_given
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit question feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/question-status")
async def get_question_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's question tracking status
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        tracking = await mongo_db.db.chat_question_tracking.find_one({
            "user_email": current_user.email
        })
        
        if not tracking:
            return {
                "questions_asked": 0,
                "feedback_given": 0,
                "questions_remaining": 5,
                "total_limit": 5
            }
        
        questions_asked = tracking.get("questions_asked", 0)
        feedback_given = tracking.get("feedback_given", 0)
        
        # Fixed limit: 5 questions total
        # Feedback is required for questions 3, 4, 5 but doesn't add bonus questions
        total_limit = 5
        remaining = max(0, total_limit - questions_asked)
        
        conversations = await mongo_db.db.deva_conversations.find({
            "user_email": current_user.email
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        feedback_map = {}
        for conv in conversations:
            conv_id = str(conv["_id"])
            feedback = await mongo_db.db.question_feedback.find_one({
                "user_email": current_user.email,
                "question_id": conv_id
            })
            feedback_map[conv_id] = feedback is not None
        
        return {
            "questions_asked": questions_asked,
            "feedback_given": feedback_given,
            "questions_remaining": remaining,
            "total_limit": total_limit,
            "recent_conversations": [
                {
                    "id": str(conv["_id"]),
                    "question": conv.get("question", ""),
                    "has_feedback": feedback_map.get(str(conv["_id"]), False),
                    "created_at": conv.get("created_at")
                }
                for conv in conversations
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get question status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get question status: {str(e)}"
        )
