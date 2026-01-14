"""
Calculation Engine Router
Wraps the calculation API and integrates with compression & storage
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import sys
import os

# Add calculation source to path
calculation_src_path = os.path.join(os.path.dirname(__file__), "calculation", "calculation-main", "src")
if calculation_src_path not in sys.path:
    sys.path.insert(0, calculation_src_path)

from api.app import app as calculation_app
from auth import get_current_active_user
from models import User
from horoscope_service import compress_and_store_horoscope

router = APIRouter()

# Mount calculation routes without /calc prefix to avoid duplication
# The routes will be mounted at /calc in main.py
for route in calculation_app.routes:
    if hasattr(route, 'path'):
        # Remove /calc prefix if present to avoid duplication
        if route.path.startswith('/calc'):
            route.path = route.path[5:]  # Remove '/calc'
    router.routes.append(route)

# Add authenticated endpoint for storing horoscope after calculation
@router.post("/api/horoscope/store")
async def store_horoscope_authenticated(
    request_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Store a calculated horoscope for authenticated user
    Flow: Fetch calculation → Fetch Dasha → Compress → Store in MongoDB
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get the horoscope data from calculation engine
        from api import service as calc_service
        
        stored_horo = calc_service._store.get(request_id)
        if not stored_horo:
            raise HTTPException(status_code=404, detail=f"Horoscope {request_id} not found in calculation cache")
        
        # Convert to JSON format safely
        # StoredHoroscope has: request, response, agentDispatched, internalHoroscope
        # We need the 'response' which is HoroscopeResponse containing rasiChart, divisionalCharts, etc.
        try:
            logger.info(f"[STORE] stored_horo type: {type(stored_horo)}")
            logger.info(f"[STORE] stored_horo has 'response': {hasattr(stored_horo, 'response')}")
            
            # Priority 1: Use stored_horo.response directly (this is HoroscopeResponse with rasiChart, etc.)
            if hasattr(stored_horo, 'response') and stored_horo.response is not None:
                if hasattr(stored_horo.response, 'dict'):
                    horoscope_data = stored_horo.response.dict()
                    logger.info(f"[STORE] Used stored_horo.response.dict()")
                elif hasattr(stored_horo.response, 'model_dump'):
                    horoscope_data = stored_horo.response.model_dump()
                    logger.info(f"[STORE] Used stored_horo.response.model_dump()")
                else:
                    horoscope_data = dict(stored_horo.response)
                    logger.info(f"[STORE] Used dict(stored_horo.response)")
            # Fallback: try stored_horo.dict() and extract response
            elif hasattr(stored_horo, 'dict'):
                full_data = stored_horo.dict()
                if 'response' in full_data and isinstance(full_data['response'], dict):
                    horoscope_data = full_data['response']
                    logger.info(f"[STORE] Extracted 'response' from stored_horo.dict()")
                else:
                    horoscope_data = full_data
                    logger.info(f"[STORE] Used full stored_horo.dict()")
            else:
                horoscope_data = dict(stored_horo)
                logger.info(f"[STORE] Used dict(stored_horo)")
            
            # Log the keys we got
            logger.info(f"[STORE] horoscope_data keys: {list(horoscope_data.keys())}")
            logger.info(f"[STORE] 'rasiChart' present: {'rasiChart' in horoscope_data}")
            logger.info(f"[STORE] 'divisionalCharts' present: {'divisionalCharts' in horoscope_data}, count: {len(horoscope_data.get('divisionalCharts', []))}")
            logger.info(f"[STORE] 'dasha' present: {'dasha' in horoscope_data}")
            
        except Exception as conv_error:
            logger.error(f"Error converting stored horoscope: {conv_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to convert horoscope data: {str(conv_error)}")
        
        # Fetch Vimsottari Dasha data
        try:
            from jhora.horoscope.dhasa.graha import vimsottari as _vimsottari
            h = getattr(stored_horo, 'internalHoroscope', None)
            
            if h:
                jd = getattr(h, 'julian_day', None)
                place = getattr(h, 'Place', None)
                
                if jd and place:
                    # Get Vimsottari dasha with antardhasa (2 layers)
                    bal, res = _vimsottari.get_vimsottari_dhasa_bhukthi(jd, place, include_antardhasa=True)
                    
                    # Planet names mapping
                    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
                    
                    # Transform to expected format: group by mahadasha
                    mahadasha_dict = {}
                    for row in res:
                        if len(row) >= 3:
                            md_idx, ad_idx, start = row[0], row[1], row[2]
                            md_lord = planet_names[md_idx] if md_idx < len(planet_names) else str(md_idx)
                            ad_lord = planet_names[ad_idx] if ad_idx < len(planet_names) else str(ad_idx)
                            
                            if md_lord not in mahadasha_dict:
                                mahadasha_dict[md_lord] = {
                                    'lord': md_lord,
                                    'start': str(start),
                                    'antardasha': []
                                }
                            
                            # Add antardasha
                            mahadasha_dict[md_lord]['antardasha'].append({
                                'lord': ad_lord,
                                'start': str(start)
                            })
                    
                    # Build dasha structure
                    horoscope_data['dasha'] = {
                        'vimsottari': {
                            'periods': list(mahadasha_dict.values())
                        }
                    }
                    logger.info(f"Successfully fetched Dasha data for {request_id}")
        except Exception as dasha_error:
            # Log warning but continue without dasha data
            logger.warning(f"Could not fetch Dasha data for {request_id}: {dasha_error}")
        
        # Compress and store
        result = await compress_and_store_horoscope(
            user_email=current_user.email,
            horoscope_data=horoscope_data,
            request_id=request_id
        )
        
        logger.info(f"Successfully stored horoscope {request_id} for user {current_user.email}")
        
        return {
            "status": "success",
            "message": "Horoscope compressed and stored successfully",
            "user": current_user.email,
            "request_id": request_id,
            "chunks_stored": result.get("chunks_count", 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store horoscope {request_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store horoscope: {str(e)}")
