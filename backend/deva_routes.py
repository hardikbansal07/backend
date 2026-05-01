"""
Deva Agent Router
Connects AI Astrology frontend to Deva Agent backend
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
import asyncio
from bson import ObjectId
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import Vertex AI components
from services.vertex_service import init_vertex_ai, get_model_name
from vertexai.generative_models import GenerativeModel, Content, Part
from utils.vertex_autogen_client import VertexGenAIClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Add deva-agent to Python path
deva_agent_path = Path(__file__).parent / "deva-agent-deva_wow" / "deva-agent"
if str(deva_agent_path) not in sys.path:
    sys.path.insert(0, str(deva_agent_path))

class ChatRequest(BaseModel):
    question: str
    request_id: Optional[str] = None  # Horoscope request ID
    preferred_language: Optional[str] = None

class ChatResponse(BaseModel):
    status: str
    response: str
    conversation_id: str
    has_horoscope_data: bool
    questions_remaining: int
    total_questions_asked: int

class DeleteChatRequest(BaseModel):
    conversation_ids: List[str]

class BirthDetailsRequest(BaseModel):
    name: str  # User's name
    gender: str  # Male, Female, or Other
    date_of_birth: str  # Format: YYYY-MM-DD
    time_of_birth: str  # Format: HH:MM
    place_of_birth: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: str = "English"

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
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with Deva Agent
    Requires user authentication and horoscope data
    """
    try:
        logger.info(f"[DEVA] Chat request from user: {current_user.email}, question: {request.question[:50]}...")
        
        # Step 0: Check Credit Balance
        if current_user.credits < 1:
            # Check if guest
            if getattr(current_user, "is_guest", False):
                 raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "GUEST_LIMIT_REACHED",
                        "message": "You have used your 2 free questions. Please login to continue."
                    }
                )

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
        
        # Step 0.5: Fetch Chat History (MOVED UP)
        chat_history = []
        try:
            history_cursor = mongo_db.db.deva_conversations.find({
                "user_email": current_user.email
            }).sort("created_at", -1).limit(5)
            
            recent_convs = await history_cursor.to_list(length=5)
            for conv in reversed(recent_convs):
                chat_history.append(f"User: {conv.get('question')}")
                chat_history.append(f"Astro Care AI: {conv.get('response')}")
            logger.info(f"[DEVA] Fetched {len(recent_convs)} previous conversations")
        except Exception as e:
            logger.warning(f"[DEVA] Failed to fetch chat history: {e}")

        # Step 1: Find user's most recent horoscope if request_id not provided
        if not request.request_id:
            logger.info(f"[DEVA] No request_id provided, fetching most recent horoscope for {current_user.email}")
            horoscopes = await mongo_db.db.horoscopes.find({
                "user_email": current_user.email
            }).sort("created_at", -1).limit(1).to_list(length=1)
            
            if not horoscopes:
                logger.warning(f"[DEVA] No horoscopes found for user {current_user.email}")
                
                # Check if user has saved birth details
                birth_details = await mongo_db.db.user_birth_details.find_one({
                    "user_email": current_user.email
                })
                
                if birth_details:
                    logger.info(f"[DEVA] User has birth details but no horoscope, providing basic analysis")
                else:
                    logger.info(f"[DEVA] No stored birth details. Using chat context only.")
                    birth_details = {}

                # Determine language: Request > User Profile > Default
                language = request.preferred_language or getattr(current_user, "preferred_language", "English")

                # Provide analysis based on birth details (or lack thereof)
                response_text = await run_basic_astrology_analysis(
                    question=request.question,
                    birth_details=birth_details,
                    user_email=current_user.email,
                    preferred_language=language,
                    chat_history=chat_history
                )
                
                logger.info(f"[DEVA] Basic analysis response generated, length: {len(response_text)}")
                
                # Store conversation
                conversation_id = await store_conversation(
                    user_email=current_user.email,
                    request_id="birth_details_only",
                    question=request.question,
                    response=response_text
                )
                
                return ChatResponse(
                    status="success",
                    response=response_text,
                    conversation_id=conversation_id,
                    has_horoscope_data=False,
                    questions_remaining=int(current_user.credits),
                    total_questions_asked=0
                )

                

            
            request.request_id = horoscopes[0]["request_id"]
            logger.info(f"[DEVA] Using request_id: {request.request_id}")
        


        # Step 2: Fetch horoscope chunks

        logger.info(f"[DEVA] Fetching horoscope data for request_id: {request.request_id}")
        horoscope_data = await get_user_horoscope(
            user_email=current_user.email,
            request_id=request.request_id
        )
        
        if not horoscope_data:
            logger.warning(f"[DEVA] Horoscope data not found for request_id: {request.request_id}")
            return ChatResponse(
                status="no_data",
                response="Horoscope data not found. Please generate your horoscope first.",
                conversation_id="",
                has_horoscope_data=False,
                questions_remaining=int(current_user.credits),
                total_questions_asked=0
            )
        
        # Step 3: Convert horoscope chunks to Deva Agent format
        chart_data = convert_to_deva_format(horoscope_data)
        
        # Determine language: Request > User Profile > Default
        language = request.preferred_language or getattr(current_user, "preferred_language", "English")

        # Step 4: Run Deva Agent analysis (Vertex AI)
        logger.info(f"[DEVA] Running Deva Agent analysis (Vertex AI) in {language}")
        response_text = await run_deva_agent(
            question=request.question,
            chart_data=chart_data,
            user_email=current_user.email,
            request_id=request.request_id,
            preferred_language=language,
            chat_history=chat_history
        )
        
        # Step 5: Store conversation
        conversation_id = await store_conversation(
            user_email=current_user.email,
            request_id=request.request_id,
            question=request.question,
            response=response_text
        )
        
        return ChatResponse(
            status="success",
            response=response_text,
            conversation_id=conversation_id,
            has_horoscope_data=True,
            questions_remaining=int(current_user.credits),
            total_questions_asked=0
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deva Agent chat failed: {e}", exc_info=True)
        # Refund credit
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
    preferred_language: str = "English",
    chat_history: List[str] = None
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
5. FORMATTING RULES:
   - You MUST use these exact section headers: **To The Point**, **Advice**, **Closing Question**.
   - These headers must be in ENGLISH.
   - The CONTENT of each section must be in {preferred_language}.
   - DO NOT mix languages. If {preferred_language} is Telugu, write ALL content in Telugu.
"""

        formatted_history = "\n".join(chat_history) if chat_history else "No previous context."

        user_prompt = (
            f"BIRTH INFORMATION:\n"
            f"- Date: {dob}\n"
            f"- Time: {tob}\n"
            f"- Place: {pob}\n\n"
            f"PREVIOUS CONVERSATION:\n"
            f"{formatted_history}\n\n"
            f"USER'S NEW QUESTION: {question}\n"
            f"Provide a detailed astrological response."
        )

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
    preferred_language: str = "English",
    chat_history: List[str] = None
) -> str:
    """
    Run Deva Agent analysis programmatically using VertexGenAIClient
    """
    try:
        # Import Deva Agent components
        from agents.specialists import get_specialists
        from agents.principals import get_principal
        from autogen_agentchat.teams import RoundRobinGroupChat
        
        # Initialize Vertex Client
        client = VertexGenAIClient()
        
        logger.info(f"[DEVA] Initializing Deva Agent with preferred_language: {preferred_language}")

        # Initialize agents with Vertex Client
        lagna_pati, kala_purusha, varga_vizier = get_specialists(model_client=client)
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

PREVIOUS CONVERSATION:
{chr(10).join(chat_history) if chat_history else "No previous context."}

USER QUESTION: {question}

INSTRUCTIONS FOR COUNCIL:
1. LagnaPati: Analyze D1 strength.
2. KalaPurusha: Check current Dasha relative to TODAY ({date_str}).
3. VargaVizier: Check D10 Career strength.
4. MahaRishi (Astro Care AI): Synthesize final answer.
IMPORTANT FORMATTING:
- Use standard headers: **To The Point**, **Advice**, **Closing Question**.
- Keep headers in ENGLISH for parsing.
- Write ALL section CONTENT in {preferred_language}.
- Ensure the ENTIRE response content is in {preferred_language}, not just the first part.
"""
        
        # Create council
        council = RoundRobinGroupChat(
            participants=[lagna_pati, kala_purusha, varga_vizier, maha_rishi],
            max_turns=4
        )
        
        # Collect messages
        messages = []
        async for msg in council.run_stream(task=context_message):
            source = getattr(msg, "source", "Unknown")
            content = getattr(msg, "content", str(msg))
            messages.append({"source": source, "content": content})
            logger.debug(f"[DEVA] {source}: {content[:50]}...")
        
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
    """Check user's question limit - simplified without feedback system"""
    if mongo_db.db is None: raise Exception("Database not initialized")
    try:
        tracking = await mongo_db.db.chat_question_tracking.find_one({"user_email": user_email})
        if not tracking:
            tracking = {"user_email": user_email, "questions_asked": 0}
            await mongo_db.db.chat_question_tracking.insert_one(tracking)
        
        questions_asked = tracking.get("questions_asked", 0)
        base_limit = 3
        remaining = base_limit - questions_asked
        
        if remaining <= 0:
            return {"allowed": False, "remaining": 0, "total_asked": questions_asked, "feedback_needed": False}
        
        update_op = {"$inc": {"questions_asked": 1}, "$set": {"updated_at": datetime.utcnow()}}
        await mongo_db.db.chat_question_tracking.update_one({"user_email": user_email}, update_op)
        return {"allowed": True, "remaining": remaining - 1, "total_asked": questions_asked + 1, "feedback_needed": False}
    except Exception as e:
        logger.error(f"Limit check failed: {e}")
        raise


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
            "name": details.name,
            "gender": details.gender,
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

@router.post("/birth-details/reset")
async def reset_user_data(
    current_user: User = Depends(get_current_active_user)
):
    """
    Reset user data: Delete birth details and ALL horoscopes.
    Keep chat history/credits/account instructions.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    try:
        from horoscope_service import delete_all_user_horoscopes
        
        # 1. Delete birth details
        await mongo_db.db.user_birth_details.delete_one({
            "user_email": current_user.email
        })
        
        # 2. Delete all horoscopes and chunks
        await delete_all_user_horoscopes(current_user.email)
        
        logger.info(f"Reset data for user: {current_user.email}")
        
        return {
            "status": "success",
            "message": "User data reset successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to reset user data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset data: {str(e)}"
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

@router.delete("/chat/history")
async def delete_deva_chat_history(
    request: DeleteChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Delete multiple deva chat history records"""
    try:
        object_ids = []
        for cid in request.conversation_ids:
            try:
                object_ids.append(ObjectId(cid))
            except:
                pass
                
        if not object_ids:
            return {"status": "success", "deleted_count": 0}
            
        result = await mongo_db.db.deva_conversations.delete_many({
            "_id": {"$in": object_ids},
            "user_email": current_user.email
        })
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        logger.error(f"Error deleting deva history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
