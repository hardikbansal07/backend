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

logger = logging.getLogger(__name__)

router = APIRouter()

# Add deva-agent to Python path
deva_agent_path = Path(__file__).parent / "deva-agent-deva_wow" / "deva-agent"
if str(deva_agent_path) not in sys.path:
    sys.path.insert(0, str(deva_agent_path))

# Add calculation source to Python path
calculation_src_path = Path(__file__).parent / "calculation" / "calculation-main" / "src"
if str(calculation_src_path) not in sys.path:
    sys.path.insert(0, str(calculation_src_path))

# ─────────────────────────────────────────────────────────────────────────────
# GENDER PLANET POWER — User gender matches corresponding planet power
# ─────────────────────────────────────────────────────────────────────────────
GENDER_PLANET_POWER = {
    "Male": {
        "rule": "USER IS MALE. Male planets (Sun, Mars, Jupiter) will have higher power in this chart."
    },
    "Female": {
        "rule": "USER IS FEMALE. Female planets (Moon, Venus) will have higher power in this chart."
    },
    "Transgender": {
        "rule": "USER IS TRANSGENDER. Neutral planets (Mercury, Saturn) will have higher power in this chart."
    },
    "Unknown": {
        "rule": "USER GENDER IS UNKNOWN. Standard planetary weights apply."
    }
}
# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN CONFIG — Har engine ka focused house + planet + instructions
# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN CONFIG — Har engine ka main house aur title config
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_CONFIG = {
    "general": {
        "title": "Personality",
        "main_house": 1
    },
    "career": {
        "title": "Career & Business",
        "main_house": 10
    },
    "finance": {
        "title": "Finance & Wealth",
        "main_house": 2
    },
    "family": {
        "title": "Family & Comforts",
        "main_house": 2
    },
    "children": {
        "title": "Children & Family",
        "main_house": 5
    },
    "public": {
        "title": "Public & Masses",
        "main_house": 10
    },
    "crush_dating": {
        "title": "Crush & Dating",
        "main_house": 5
    },
    "love_marriage": {
        "title": "Love & Marriage 2.0",
        "main_house": 7
    }
}

class ChatRequest(BaseModel):
    question: str
    request_id: Optional[str] = None  # Horoscope request ID
    preferred_language: Optional[str] = None
    domain: Optional[str] = "general"  # Engine domain: general, career, finance, health, children, public
    chat_id: Optional[str] = None  # Specific chat session/thread ID

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
        
        # Step 0: Check Out-of-scope / Unanswerable query
        from services.astrology_metadata import identify_target_house_from_query
        target_house = identify_target_house_from_query(request.question)
        
        if target_house is None:
            logger.info(f"[DEVA] Out-of-scope question detected: '{request.question}'. Returning unanswerable status.")
            return ChatResponse(
                status="unanswerable",
                response="I am Astro Care AI. I can only assist you with astrological queries related to your horoscope. Please ask a question related to your personality, career, wealth, family, romance, or other life domains.",
                conversation_id="",
                has_horoscope_data=True,
                questions_remaining=int(current_user.credits),
                total_questions_asked=0
            )

        # Step 0.2: Check Credit Balance
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
        
        # Step 0.5: Fetch Chat History (Domain-Aware & Session-Aware)
        chat_history = []
        domain = request.domain or "general"
        if request.chat_id:
            try:
                # Query only if the user is in the same chat_id AND same engine/domain
                history_cursor = mongo_db.db.deva_conversations.find({
                    "user_email": current_user.email,
                    "domain": domain,
                    "chat_id": request.chat_id
                }).sort("created_at", -1).limit(5)
                
                recent_convs = await history_cursor.to_list(length=5)
                for conv in reversed(recent_convs):
                    chat_history.append(f"User: {conv.get('question')}")
                    chat_history.append(f"Astro Care AI: {conv.get('response')}")
                logger.info(f"[DEVA] Fetched {len(recent_convs)} previous conversations for chat_id={request.chat_id} and domain={domain}")
            except Exception as e:
                logger.warning(f"[DEVA] Failed to fetch chat history: {e}")
        else:
            logger.info(f"[DEVA] No chat_id provided. Starting fresh new chat thread for domain={domain}.")

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
                    logger.info(f"[DEVA] User has birth details but no horoscope, generating horoscope dynamically")
                    try:
                        from api.service import compute_horoscope
                        from api.models import HoroscopeRequest, LocationIn
                        from horoscope_service import compress_and_store_horoscope

                        # Resolve coordinates and timezone
                        lat = birth_details.get("latitude")
                        lon = birth_details.get("longitude")
                        if lat is None or lon is None:
                            lat, lon = 28.6139, 77.2090  # Delhi, India default

                        # Read timezone or default to 5.5
                        tz_offset = birth_details.get("timezone", 5.5)
                        if "timezone" not in birth_details and "timezoneOffset" in birth_details:
                            tz_offset = birth_details.get("timezoneOffset")

                        loc = LocationIn(
                            place=birth_details.get("place_of_birth", "Delhi, India"),
                            latitude=float(lat),
                            longitude=float(lon),
                            tzOffset=float(tz_offset)
                        )

                        time_str = birth_details.get("time_of_birth", "12:00")
                        if len(time_str.split(':')) == 2:
                            time_str += ":00"

                        dt_str = f"{birth_details.get('date_of_birth')}T{time_str}"
                        birth_dt = datetime.fromisoformat(dt_str)

                        req_obj = HoroscopeRequest(
                            birthDateTime=birth_dt,
                            location=loc,
                            language="en",
                            name=birth_details.get("name", "User")
                        )

                        # Dynamically compute horoscope
                        stored = compute_horoscope(req_obj)

                        if hasattr(stored.response, 'model_dump'):
                            horoscope_data = stored.response.model_dump()
                        else:
                            horoscope_data = stored.response.dict()

                        request_id = stored.response.requestId
                        
                        # Store in MongoDB Atlas
                        await compress_and_store_horoscope(
                            user_email=current_user.email,
                            horoscope_data=horoscope_data,
                            request_id=request_id
                        )
                        logger.info(f"[DYN-HORO] Dynamically generated and stored horoscope {request_id} for user {current_user.email}")
                        
                        # Set the request_id to use the dynamically created horoscope
                        request.request_id = request_id
                        
                        # Set horoscopes so that the block after knows we found it
                        horoscopes = [{"request_id": request_id}]
                        
                    except Exception as gen_err:
                        logger.error(f"[DYN-HORO] Failed to dynamically generate horoscope: {gen_err}", exc_info=True)
                        # If dynamic generation failed, fallback to basic analysis
                        birth_details = {}

                if not horoscopes:
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
                        response=response_text,
                        domain=request.domain or "general",
                        chat_id=request.chat_id
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

        # Step 4: Run domain engine analysis (Direct Vertex AI)
        domain = request.domain or "general"
        logger.info(f"[DOMAIN ENGINE] Running analysis in {language}, domain={domain}")
        response_text = await run_domain_engine(
            question=request.question,
            chart_data=chart_data,
            preferred_language=language,
            chat_history=chat_history,
            domain=domain
        )
        
        # Step 5: Store conversation
        conversation_id = await store_conversation(
            user_email=current_user.email,
            request_id=request.request_id,
            question=request.question,
            response=response_text,
            domain=domain,
            chat_id=request.chat_id
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
        "strength": horoscope_data.get("strength"),
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

def format_chart_data_to_text(chart_data: Dict[str, Any]) -> str:
    """
    Formats the JSON chart data into an exceptionally structured, highly readable
    Markdown table format to ensure 100% LLM accuracy and zero parsing ambiguities.
    """
    import re
    lines = []
    
    meta = chart_data.get("meta", {})
    if meta:
        lines.append("### 1. USER PROFILE & PANCHANGA")
        lines.append("| Parameter | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Name | {meta.get('name', 'User')} |")
        lines.append(f"| Gender | {meta.get('gender', 'Unknown')} |")
        lines.append(f"| Birth Date | {meta.get('birth_date', 'Unknown')} |")
        lines.append(f"| Birth Time | {meta.get('birth_time', 'Unknown')} |")
        lines.append(f"| Birth Place | {meta.get('birth_place', 'Unknown')} |")
        
        cal = meta.get("calendar", {})
        if not cal and "calendar" in chart_data:
            cal = chart_data["calendar"] or {}
            
        if cal:
            lines.append(f"| Tithi (Lunar Day) | {cal.get('Tithi', 'Unknown')} |")
            lines.append(f"| Nakshatram | {cal.get('Nakshatram', 'Unknown')} |")
            lines.append(f"| Yoga | {cal.get('Yoga', 'Unknown')} |")
            lines.append(f"| Karana | {cal.get('Karana', 'Unknown')} |")
        lines.append("")

    # Lagna D1 Table
    lagna = chart_data.get("lagna", {})
    if lagna:
        lines.append("### 2. D1 RASI CHART (MAIN LAGNA)")
        lines.append(f"- **Ascendant (Lagna) Sign:** {lagna.get('asc_sign')} | **Ascendant Degree:** {lagna.get('asc_deg')}°")
        lines.append("")
        lines.append("| Planet | House | Sign | Degree | Nakshatra | Chara Karaka | Strengths/Dignity |")
        lines.append("| :--- | :---: | :---: | :---: | :--- | :---: | :--- |")
        
        for p in lagna.get("planets", []):
            pname = p.get("name")
            clean_pname = re.sub(r"[^a-zA-Z]", "", pname)
            if clean_pname.lower() in ("asc", "ascendant"):
                continue
            house = p.get("house")
            sign = p.get("sign")
            deg = p.get("deg")
            nak = p.get("nak")
            
            # Dignity / Flags
            flags = []
            if p.get("own_sign"): flags.append("Own Sign (Swakshetra)")
            if p.get("exalted"): flags.append("Exalted")
            if p.get("debilitated"): flags.append("Debilitated")
            if p.get("vargottama"): flags.append("Vargottama (Double Strength)")
            if p.get("retrograde"): flags.append("Retrograde (Vakri)")
            if p.get("combust"): flags.append("Combust (Ast)")
            
            flags_str = ", ".join(flags) if flags else "Neutral"
            chara = p.get("charaKaraka") or "None"
            
            lines.append(f"| **{clean_pname}** | {house} | {sign} | {deg}° | {nak} | {chara} | {flags_str} |")
        lines.append("")

    # Divisional Charts Tables
    d_series = chart_data.get("d_series", {})
    if d_series:
        lines.append("### 3. DIVISIONAL CHARTS (VARGAS)")
        for d_key, d_chart in d_series.items():
            if not d_chart: continue
            lines.append(f"#### **Divisional {d_key}**")
            lines.append(f"- **Ascendant Sign:** {d_chart.get('asc_sign')} | **Ascendant Degree:** {d_chart.get('asc_deg')}°")
            lines.append("")
            lines.append("| Planet | House | Sign | Degree | Nakshatra | Dignity/Flags |")
            lines.append("| :--- | :---: | :---: | :---: | :--- | :--- |")
            
            for p in d_chart.get("planets", []):
                pname = p.get("name")
                clean_pname = re.sub(r"[^a-zA-Z]", "", pname)
                if clean_pname.lower() in ("asc", "ascendant"):
                    continue
                house = p.get("house")
                sign = p.get("sign")
                deg = p.get("deg")
                nak = p.get("nak") or "None"
                
                # Dignity / Flags
                flags = []
                if p.get("own_sign"): flags.append("Own Sign")
                if p.get("exalted"): flags.append("Exalted")
                if p.get("debilitated"): flags.append("Debilitated")
                if p.get("vargottama"): flags.append("Vargottama")
                if p.get("retrograde"): flags.append("Retrograde")
                if p.get("combust"): flags.append("Combust")
                
                flags_str = ", ".join(flags) if flags else "Neutral"
                lines.append(f"| {clean_pname} | {house} | {sign} | {deg}° | {nak} | {flags_str} |")
            lines.append("")

    # Dashas Timeline
    dasha = chart_data.get("dasha", {})
    if dasha:
        lines.append("### 4. VIMSOTTARI DASHA TIMELINE")
        lines.append("| Dasha Lord | Period Type | Start Date |")
        lines.append("| :--- | :---: | :--- |")
        
        for md in dasha.get("periods", []):
            lines.append(f"| **{md.get('lord')}** | Mahadasha (MD) | {md.get('start')} |")
            for ad in md.get("antardasha", []):
                lines.append(f"| {ad.get('lord')} | Antardasha (AD) | {ad.get('start')} |")
                for pd in ad.get("pratyantara", []):
                    lines.append(f"| {pd.get('lord')} | Pratyantardasha (PD) | {pd.get('start')} |")
        lines.append("")

    # Strength Data Tables
    strength = chart_data.get("strength")
    if strength:
        lines.append("### 5. PLANETARY STRENGTHS (SHADBALA)")
        lines.append("| Planet | Sthana Bala | Kaala Bala | Dig Bala | Cheshta Bala | Naisargika | Drik Bala | Total Score | Rupas | Strength Ratio |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        
        shadbala = strength.get("shadbala", {})
        for planet, values in shadbala.items():
            lines.append(
                f"| **{planet}** | {values.get('sthana_bala')} | {values.get('kaala_bala')} | {values.get('dig_bala')} | "
                f"{values.get('cheshta_bala')} | {values.get('naisargika_bala')} | {values.get('drik_bala')} | "
                f"{values.get('total_score')} | {values.get('rupas')} | {values.get('strength_ratio')} |"
            )
        lines.append("")
        
        lines.append("### 6. HOUSE STRENGTHS (BHAVABALA)")
        lines.append("| House | Total Score | Rupas | Strength Ratio |")
        lines.append("| :---: | :---: | :---: | :---: |")
        
        bhavabala = strength.get("bhavabala", {})
        sorted_houses = sorted(bhavabala.keys(), key=lambda x: int(x))
        for house in sorted_houses:
            values = bhavabala[house]
            lines.append(f"| **House {house}** | {values.get('total_score')} | {values.get('rupas')} | {values.get('strength_ratio')} |")
        lines.append("")

        vimsopaka = strength.get("vimsopaka", {})
        if vimsopaka:
            lines.append("### 7. PLANETARY VIMSOPAKA STRENGTHS (VARGA BALAS)")
            lines.append("| Planet | Shad Varga (6) | Sapta Varga (7) | Dasa Varga (10) | Shodasa Varga (16) |")
            lines.append("| :--- | :---: | :---: | :---: | :---: |")
            p_order = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
            sorted_planets = sorted(vimsopaka.keys(), key=lambda x: p_order.index(x) if x in p_order else 99)
            for planet in sorted_planets:
                values = vimsopaka[planet]
                shadv = values.get('shadvarga', {})
                saptv = values.get('sapthavarga', {})
                dasav = values.get('dhasavarga', {})
                shodv = values.get('shodhasavarga', {})
                lines.append(
                    f"| **{planet}** | {shadv.get('score', 0):.2f} ({shadv.get('percentage', 0):.1f}%) | "
                    f"{saptv.get('score', 0):.2f} ({saptv.get('percentage', 0):.1f}%) | "
                    f"{dasav.get('score', 0):.2f} ({dasav.get('percentage', 0):.1f}%) | "
                    f"{shodv.get('score', 0):.2f} ({shodv.get('percentage', 0):.1f}%) |"
                )
            lines.append("")

    return "\n".join(lines)

async def run_domain_engine(
    question: str,
    chart_data: Dict[str, Any],
    preferred_language: str = "English",
    chat_history: List[str] = None,
    domain: str = "general"
) -> str:
    """
    Direct Vertex AI call — domain-specific system prompt.
    Replaces the old 4-agent council (LagnaPati/KalaPurusha/VargaVizier/MahaRishi).
    """
    try:
        init_vertex_ai()

        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")

        # Domain config
        domain_cfg = DOMAIN_CONFIG.get(domain, DOMAIN_CONFIG["general"])
        domain_title     = domain_cfg["title"]
        main_house       = domain_cfg["main_house"]

        # Gender — meta se extract karo
        gender = chart_data.get("meta", {}).get("gender", "Unknown")
        gender_normalized = gender.strip().capitalize() if gender else "Unknown"
        # "Other" ko "Transgender" treat karo (backward compatibility)
        if gender_normalized == "Other":
            gender_normalized = "Transgender"
        if gender_normalized not in ("Male", "Female", "Transgender"):
            gender_normalized = "Unknown"

        # Gender planet power — universal rule (sab domains pe same)
        gender_power = GENDER_PLANET_POWER.get(gender_normalized, GENDER_PLANET_POWER["Unknown"])
        gender_context = gender_power["rule"]

        # ── Universal Astrological Matrix Engine Integration ────────────────
        import re
        from services.astrology_metadata import (
            resolve_lagna_sign_id,
            get_house_lord_circuit,
            AstrologicalMatrixEngine,
            identify_target_house_from_query
        )
        
        # 1. Resolve Lagna Sign ID
        lagna_data = chart_data.get("lagna", {})
        asc_sign = lagna_data.get("asc_sign", "Aries")
        lagna_sign_id = resolve_lagna_sign_id(asc_sign)
        
        # 2. Build lord placements dictionary: E.g., {"Sun": 10, "Moon": 2, ...}
        lord_placements = {}
        for p in lagna_data.get("planets", []):
            pname = p.get("name")
            if not pname:
                continue
            clean_name = re.sub(r"[^a-zA-Z]", "", pname).strip()
            if clean_name.lower() in ("asc", "ascendant", "lagna"):
                continue
            house = p.get("house")
            if house is not None:
                lord_placements[clean_name] = int(house)
                
        # 3. Dynamic Query Shifting (Identify Target House from Question)
        main_house = domain_cfg.get("main_house", 1)
        target_house = identify_target_house_from_query(question)
        if target_house is None:
            target_house = 1
        
        # Calculate relationship steps from main_house to target_house (if different)
        relation_str = "Target matches the active focus domain's Main House."
        if target_house != main_house:
            steps_from_main = (target_house - main_house) % 12 + 1
            relation_str = f"Target relative/topic (D1 House {target_house}) is {steps_from_main} steps inclusive (relative House {steps_from_main}) from this focus domain's Main House (House {main_house})."

        # Shift the relative Lagna of our analysis to the target_house
        shifted_matrix = AstrologicalMatrixEngine.resolve_shifted_matrix(target_house, lagna_sign_id)
        
        # 4. Resolve Dynamic Lord Circuit starting from the target_house
        lord_circuit = get_house_lord_circuit(target_house, lagna_sign_id, lord_placements)
        
        # 5. Format Shifted Matrix and Lord Circuit for LLM prompt context
        matrix_lines = []
        matrix_lines.append("### 8. UNIVERSAL ASTROLOGICAL MATRIX (LAGNA SHIFT)")
        matrix_lines.append(f"- **Focus Domain / Main House Anchor:** House {main_house}")
        matrix_lines.append(f"- **Dynamic Target House (Query Entity):** House {target_house} (acting as relative Lagna)")
        matrix_lines.append(f"- **Inter-House Relationship:** {relation_str}")
        matrix_lines.append("- **Relative House Shifting Map (Bhava Lagna):**")
        matrix_lines.append("| Relative House | Semantic Meaning | Physical D1 House | Zodiac Sign | Occupying Planets | Classifications |")
        matrix_lines.append("| :---: | :--- | :---: | :---: | :--- | :--- |")
        
        # Group D1 planets by physical house:
        planets_by_house = {}
        for p in lagna_data.get("planets", []):
            pname = p.get("name")
            if not pname:
                continue
            clean_name = re.sub(r"[^a-zA-Z]", "", pname).strip()
            if clean_name.lower() in ("asc", "ascendant", "lagna"):
                continue
            h = p.get("house")
            if h is not None:
                planets_by_house.setdefault(int(h), []).append(clean_name)
                
        for r in range(1, 13):
            cell = shifted_matrix[r]
            h = cell["physical_house_number"]
            sign_name = cell["zodiac_sign_name"]
            concept = cell["concept"]
            classifications_str = ", ".join(cell["classifications"])
            occupants = ", ".join(planets_by_house.get(h, [])) if planets_by_house.get(h) else "None"
            
            matrix_lines.append(f"| House {r} | {concept} | House {h} | {sign_name} | {occupants} | {classifications_str} |")
        matrix_lines.append("")
        
        matrix_lines.append("- **Dynamic House Lord Circuit Connection:**")
        circuit_steps = []
        for idx, step in enumerate(lord_circuit):
            is_bb = " (Bhavat Bhavam Trigger!)" if step["is_bhavat_bhavam"] else ""
            circuit_steps.append(
                f"Step {idx+1}: House {step['house']} (Sign: {step['sign_name']}, Lord: {step['lord']}) "
                f"-> Lord placed in House {step['placed_house']} ({step['steps_inclusive']} steps away){is_bb}"
            )
        matrix_lines.append("\n".join(f"  - {s}" for s in circuit_steps))
        matrix_lines.append("")
        
        matrix_payload = "\n".join(matrix_lines)

        # ── System Prompt ────────────────────────────────────────────────────
        # System instructions disabled to provide raw astrological analysis output
        system_prompt = None

        # ── User Message ─────────────────────────────────────────────────────
        history_text = "\n".join(chat_history) if chat_history else "No previous conversation."
        formatted_chart_text = format_chart_data_to_text(chart_data)
        
        user_message = f"""CURRENT DATE: {date_str}

CHART DATA:
{formatted_chart_text}

PREVIOUS CONVERSATION:
{history_text}

USER QUESTION: {question}"""

        # ── Vertex AI Call ────────────────────────────────────────────────────
        model = GenerativeModel(
            get_model_name()
        )
        response = await model.generate_content_async(
            user_message,
            generation_config={"temperature": 0.7, "max_output_tokens": 8192}
        )

        logger.info(f"[DOMAIN ENGINE] Response generated for domain={domain}")
        return response.text

    except Exception as e:
        logger.error(f"[DOMAIN ENGINE] Failed for domain={domain}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Domain engine failed: {str(e)}"
        )

async def store_conversation(
    user_email: str,
    request_id: str,
    question: str,
    response: str,
    domain: str = "general",
    chat_id: Optional[str] = None
) -> str:
    """Store Deva Agent conversation in MongoDB"""
    if mongo_db.db is None: return ""
    try:
        conversation_doc = {
            "user_email": user_email,
            "request_id": request_id,
            "question": question,
            "response": response,
            "domain": domain,
            "chat_id": chat_id,
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
    Save user's birth details for AI astrology and automatically generate/store their horoscope.
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
        
        # Delete any previous horoscopes and chunks for this user before storing the new one
        await mongo_db.db.horoscope_chunks.delete_many({"user_email": current_user.email})
        await mongo_db.db.horoscopes.delete_many({"user_email": current_user.email})
        
        await mongo_db.db.user_birth_details.update_one(
            {"user_email": current_user.email},
            {"$set": birth_details},
            upsert=True
        )
        
        logger.info(f"Birth details saved for user: {current_user.email}")

        # Automatically trigger horoscope generation and storage in MongoDB
        try:
            from api.service import compute_horoscope
            from api.models import HoroscopeRequest, LocationIn
            from horoscope_service import compress_and_store_horoscope

            # Resolve coordinates and timezone
            lat = details.latitude
            lon = details.longitude
            if lat is None or lon is None:
                lat, lon = 28.6139, 77.2090  # Delhi, India default

            loc = LocationIn(
                place=details.place_of_birth,
                latitude=float(lat),
                longitude=float(lon),
                tzOffset=5.5  # Standard India timezone offset (can be derived from place or offset)
            )

            time_str = details.time_of_birth
            if len(time_str.split(':')) == 2:
                time_str += ":00"

            dt_str = f"{details.date_of_birth}T{time_str}"
            birth_dt = datetime.fromisoformat(dt_str)

            req_obj = HoroscopeRequest(
                birthDateTime=birth_dt,
                location=loc,
                language="en",
                name=details.name
            )

            # Compute horoscope using the software engine
            stored = compute_horoscope(req_obj)

            if hasattr(stored.response, 'model_dump'):
                horoscope_data = stored.response.model_dump()
            else:
                horoscope_data = stored.response.dict()

            request_id = stored.response.requestId
            
            # Store compressed chunks directly in MongoDB Atlas
            store_result = await compress_and_store_horoscope(
                user_email=current_user.email,
                horoscope_data=horoscope_data,
                request_id=request_id
            )
            logger.info(f"[AUTO-HORO] Auto-generated and stored horoscope {request_id} for user {current_user.email}. Chunks stored: {store_result.get('chunks_count')}")

        except Exception as e_horo:
            logger.error(f"[AUTO-HORO] Failed to auto-generate horoscope: {e_horo}", exc_info=True)
            # We don't fail the entire save_birth_details request if calculation has a warning
            
        return {
            "status": "success",
            "message": "Birth details saved and horoscope generated successfully"
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
                "name": details.get("name"),
                "gender": details.get("gender"),
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
