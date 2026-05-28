"""
Horoscope Service
Manages the complete flow: Calculation → Compression → MongoDB Storage
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from mongo import mongo_db
from compression_service import compress_horoscope, split_into_chunks
import logging

logger = logging.getLogger(__name__)

async def compress_and_store_horoscope(
    user_email: str,
    horoscope_data: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    Complete flow: Compress horoscope and store in MongoDB
    
    Args:
        user_email: Authenticated user's email
        horoscope_data: Full horoscope calculation output
        request_id: Unique request identifier
    
    Returns:
        Storage result with chunk count and IDs
    """
    if mongo_db.db is None:
        raise Exception("Database not initialized")
    
    try:
        # Align inner requestId with outer request_id
        horoscope_data["requestId"] = request_id
        
        # Step 0: Fetch Vimsottari Dasha data if not present (with 3-levels)
        if "dasha" not in horoscope_data or not horoscope_data["dasha"]:
            try:
                # Get stored horoscope from calculation engine
                from api import service as calc_service
                stored_horo = calc_service._store.get(request_id)
                
                if stored_horo and stored_horo.internalHoroscope:
                    from jhora.horoscope.dhasa.graha import vimsottari as _vimsottari
                    h = stored_horo.internalHoroscope
                    jd = getattr(h, 'julian_day', None)
                    place = getattr(h, 'Place', None)
                    
                    if jd and place:
                        # Get Vimsottari dasha with depth=3 (Maha, Antar, Pratyantara)
                        res = _vimsottari.get_vimsottari_dhasa_levels(jd, place, depth=3)
                        
                        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
                        
                        mapped_periods = []
                        for md in res:
                            md_lord = planet_names[md['lord']] if isinstance(md['lord'], int) and md['lord'] < 9 else str(md['lord'])
                            md_entry = {
                                'lord': md_lord,
                                'start': md['start'],
                                'antardasha': []
                            }
                            for ad in md.get('antardasha', []):
                                ad_lord = planet_names[ad['lord']] if isinstance(ad['lord'], int) and ad['lord'] < 9 else str(ad['lord'])
                                ad_entry = {
                                    'lord': ad_lord,
                                    'start': ad['start'],
                                    'pratyantara': []
                                }
                                for pd in ad.get('pratyantara', []):
                                    pd_lord = planet_names[pd['lord']] if isinstance(pd['lord'], int) and pd['lord'] < 9 else str(pd['lord'])
                                    ad_entry['pratyantara'].append({
                                        'lord': pd_lord,
                                        'start': pd['start']
                                    })
                                md_entry['antardasha'].append(ad_entry)
                            mapped_periods.append(md_entry)
                        
                        horoscope_data['dasha'] = {
                            'vimsottari': {
                                'periods': mapped_periods
                            }
                        }
                        logger.info(f"Fetched and added 3-layer Vimsottari Dasha data for request {request_id}")
            except Exception as dasha_error:
                # Log warning but continue without dasha data
                logger.warning(f"Could not fetch Dasha data for {request_id}: {dasha_error}")
        
        # Step 0.2: Dynamically calculate and refresh correct Shadbala & Bhavabala Strength data
        try:
            from api import service as calc_service
            stored_horo = calc_service._store.get(request_id)
            if stored_horo and stored_horo.internalHoroscope:
                from jhora.horoscope.chart import strength as _strength
                h = stored_horo.internalHoroscope
                jd = getattr(h, 'julian_day', None)
                place = getattr(h, 'Place', None)
                ayanamsa = getattr(h, 'ayanamsa_mode', 'LAHIRI')
                
                if jd and place:
                    sb = _strength.shad_bala(jd, place, ayanamsa_mode=ayanamsa)
                    bb = _strength.bhava_bala(jd, place, ayanamsa_mode=ayanamsa)
                    
                    planet_names_7 = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                    stb, kb, dgb, cb, nb, dkb, sb_sum, sb_rupa, sb_strength = sb
                    
                    shadbala_data = {}
                    for idx, planet in enumerate(planet_names_7):
                        shadbala_data[planet] = {
                            'sthana_bala': float(stb[idx]),
                            'kaala_bala': float(kb[idx]),
                            'dig_bala': float(dgb[idx]),
                            'cheshta_bala': float(cb[idx]),
                            'naisargika_bala': float(nb[idx]),
                            'drik_bala': float(dkb[idx]),
                            'total_score': float(sb_sum[idx]),
                            'rupas': float(sb_rupa[idx]),
                            'strength_ratio': float(sb_strength[idx])
                        }
                    
                    bb_list, bb_rupas, bb_strength = bb
                    bhavabala_data = {}
                    for house_idx in range(12):
                        house_num = house_idx + 1
                        bhavabala_data[str(house_num)] = {
                            'total_score': float(bb_list[house_idx]),
                            'rupas': float(bb_rupas[house_idx]),
                            'strength_ratio': float(bb_strength[house_idx])
                        }
                    
                    horoscope_data['strength'] = {
                        'shadbala': shadbala_data,
                        'bhavabala': bhavabala_data
                    }
                    logger.info(f"Loaded dynamically calculated correct Shadbala & Bhavabala Strength data for request {request_id}")
        except Exception as strength_error:
            logger.warning(f"Could not calculate Strength data for {request_id}: {strength_error}")
        
        # Step 0.5: Fetch birth details from user_birth_details collection
        birth_details = None
        try:
            birth_details = await mongo_db.db.user_birth_details.find_one({
                "user_email": user_email
            })
            
            if birth_details:
                logger.info(f"Fetched birth details for user {user_email}")
            else:
                logger.warning(f"No birth details found for user {user_email}")
        except Exception as birth_error:
            logger.warning(f"Could not fetch birth details for {user_email}: {birth_error}")
        
        # Step 1: Compress the horoscope data (with birth details if available)
        compressed = compress_horoscope(horoscope_data, birth_details)
        
        # Step 2: Split into chunks
        chunks = split_into_chunks(compressed)
        
        # Step 3: Delete existing chunks for this horoscope (if any)
        await mongo_db.db.horoscope_chunks.delete_many({
            "user_email": user_email,
            "request_id": request_id
        })
        
        # Step 4: Store chunks in MongoDB
        stored_chunks = []
        for idx, chunk in enumerate(chunks):
            doc = {
                "user_email": user_email,
                "request_id": request_id,
                "chunk_index": idx,
                "chunk_type": chunk.get("chunk_type"),
                "chart_name": chunk.get("chart_name"),  # For divisional charts
                "data": chunk.get("data"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Embed high-level birth details directly into EVERY chunk for easier debugging in DB
            meta_info = horoscope_data.get("meta", {})
            if meta_info and meta_info.get("name"):
                doc["name"] = meta_info.get("name")
                doc["date_of_birth"] = meta_info.get("birth_date")
                doc["time_of_birth"] = meta_info.get("birth_time")
            elif birth_details:
                doc["name"] = birth_details.get("name")
                doc["date_of_birth"] = birth_details.get("date_of_birth")
                doc["time_of_birth"] = birth_details.get("time_of_birth")
            
            result = await mongo_db.db.horoscope_chunks.insert_one(doc)
            stored_chunks.append(str(result.inserted_id))
        
        # Step 5: Create or update horoscope index entry
        index_doc = {
            "user_email": user_email,
            "request_id": request_id,
            "chunks_count": len(chunks),
            "chunk_ids": stored_chunks,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "complete"
        }
        
        # Use update_one with upsert to handle duplicates
        await mongo_db.db.horoscopes.update_one(
            {"user_email": user_email, "request_id": request_id},
            {"$set": index_doc},
            upsert=True
        )
        
        # Step 6: Clean up old horoscopes and chunks for this user (only keep the current request_id)
        await mongo_db.db.horoscope_chunks.delete_many({
            "user_email": user_email,
            "request_id": {"$ne": request_id}
        })
        await mongo_db.db.horoscopes.delete_many({
            "user_email": user_email,
            "request_id": {"$ne": request_id}
        })
        
        logger.info(f"Stored horoscope {request_id} for user {user_email} in {len(chunks)} chunks, and cleaned up legacy stale horoscopes/chunks.")
        
        return {
            "status": "success",
            "chunks_count": len(chunks),
            "chunk_ids": stored_chunks,
            "request_id": request_id
        }
    
    except Exception as e:
        logger.error(f"Failed to compress and store horoscope: {e}")
        raise

async def get_user_horoscope(
    user_email: str,
    request_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve and reconstruct horoscope from MongoDB chunks
    
    Args:
        user_email: User's email
        request_id: Horoscope request ID
    
    Returns:
        Reconstructed horoscope data or None
    """
    if mongo_db.db is None:
        raise Exception("Database not initialized")
    
    try:
        # Get index entry
        index = await mongo_db.db.horoscopes.find_one({
            "user_email": user_email,
            "request_id": request_id
        })
        
        if not index:
            return None
        
        # Get all chunks
        chunks_cursor = mongo_db.db.horoscope_chunks.find({
            "user_email": user_email,
            "request_id": request_id
        }).sort("chunk_index", 1)
        
        chunks = await chunks_cursor.to_list(length=None)
        
        logger.info(f"[HOROSCOPE] Found {len(chunks)} chunks for request_id: {request_id}")
        for i, chunk in enumerate(chunks):
            logger.info(f"[HOROSCOPE] Chunk {i}: type='{chunk.get('chunk_type')}', chart_name='{chunk.get('chart_name')}', has_data={chunk.get('data') is not None}")
        
        # Reconstruct horoscope
        horoscope = {
            "meta": {},
            "lagna": None,
            "dasha": None,
            "strength": None,
            "d_series": {}
        }
        
        for chunk in chunks:
            chunk_type = chunk.get("chunk_type")
            data = chunk.get("data")
            
            logger.debug(f"[HOROSCOPE] Processing chunk: type='{chunk_type}', data_present={data is not None}")
            
            if chunk_type == "meta":
                horoscope["meta"] = data
            elif chunk_type == "lagna":
                horoscope["lagna"] = data
                logger.info(f"[HOROSCOPE] Lagna data SET: has planets={bool(data and data.get('planets'))}")
            elif chunk_type == "dasha":
                horoscope["dasha"] = data
                logger.info(f"[HOROSCOPE] Dasha data SET: has periods={bool(data and data.get('periods'))}")
            elif chunk_type == "strength":
                horoscope["strength"] = data
                logger.info(f"[HOROSCOPE] Strength data SET: has shadbala={bool(data and data.get('shadbala'))}")
            elif chunk_type == "divisional":
                chart_name = chunk.get("chart_name")
                if chart_name:
                    horoscope["d_series"][chart_name] = data
        
        logger.info(f"[HOROSCOPE] Final horoscope: lagna={horoscope['lagna'] is not None}, dasha={horoscope['dasha'] is not None}, strength={horoscope['strength'] is not None}, d_series_count={len(horoscope['d_series'])}")
        
        # Step 6: Dynamic Auto-Upgrade and Strength Recalculation
        if horoscope:
            logger.info(f"[HOROSCOPE-UPGRADE] Upgrading and refreshing strengths dynamically on-the-fly for request_id: {request_id}...")
            try:
                from api import service as calc_service
                stored_horo = calc_service._store.get(request_id)
                birth_details = None
                
                # If the calculation cache is cleared, rebuild dynamically from original request meta or active birth details
                if not stored_horo:
                    meta = horoscope.get("meta", {})
                    birth_details = None
                    if meta and meta.get("birth_date") and meta.get("birth_time") and meta.get("latitude") is not None and meta.get("longitude") is not None:
                        birth_details = {
                            "date_of_birth": meta.get("birth_date"),
                            "time_of_birth": meta.get("birth_time"),
                            "latitude": meta.get("latitude"),
                            "longitude": meta.get("longitude"),
                            "place_of_birth": meta.get("birth_place") or "Agra, India",
                            "timezone": float(meta.get("calendar", {}).get("Timezone Offset") or 5.5),
                            "name": meta.get("name") or "User"
                        }
                        logger.info(f"[HOROSCOPE-UPGRADE] Rebuilding from original request meta details for {request_id}: {birth_details}")
                    else:
                        birth_details_doc = await mongo_db.db.user_birth_details.find_one({"user_email": user_email})
                        if birth_details_doc:
                            birth_details = {
                                "date_of_birth": birth_details_doc.get("date_of_birth"),
                                "time_of_birth": birth_details_doc.get("time_of_birth"),
                                "latitude": birth_details_doc.get("latitude"),
                                "longitude": birth_details_doc.get("longitude"),
                                "place_of_birth": birth_details_doc.get("place_of_birth", "Delhi, India"),
                                "timezone": birth_details_doc.get("timezone", 5.5),
                                "name": birth_details_doc.get("name", "User")
                            }
                            logger.info(f"[HOROSCOPE-UPGRADE] Rebuilding from active profile birth details for {request_id}: {birth_details}")
                    
                    if birth_details:
                        from api.models import HoroscopeRequest, LocationIn
                        from api.service import compute_horoscope
                        
                        lat = birth_details.get("latitude")
                        lon = birth_details.get("longitude")
                        
                        loc = LocationIn(
                            place=birth_details.get("place_of_birth", "Agra, India"),
                            latitude=float(lat),
                            longitude=float(lon),
                            tzOffset=float(birth_details.get("timezone", 5.5))
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
                        stored_horo = compute_horoscope(req_obj)
                
                if stored_horo and stored_horo.internalHoroscope:
                    h = stored_horo.internalHoroscope
                    jd = getattr(h, 'julian_day', None)
                    place = getattr(h, 'Place', None)
                    
                    if jd and place:
                        # 1. Recalculate Vimsottari Dasha with 3-levels (depth=3)
                        from jhora.horoscope.dhasa.graha import vimsottari as _vimsottari
                        res = _vimsottari.get_vimsottari_dhasa_levels(jd, place, depth=3)
                        
                        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
                        
                        mapped_periods = []
                        for md in res:
                            md_lord = planet_names[md['lord']] if isinstance(md['lord'], int) and md['lord'] < 9 else str(md['lord'])
                            md_entry = {
                                'lord': md_lord,
                                'start': md['start'],
                                'antardasha': []
                            }
                            for ad in md.get('antardasha', []):
                                ad_lord = planet_names[ad['lord']] if isinstance(ad['lord'], int) and ad['lord'] < 9 else str(ad['lord'])
                                ad_entry = {
                                    'lord': ad_lord,
                                    'start': ad['start'],
                                    'pratyantara': []
                                }
                                for pd in ad.get('pratyantara', []):
                                    pd_lord = planet_names[pd['lord']] if isinstance(pd['lord'], int) and pd['lord'] < 9 else str(pd['lord'])
                                    ad_entry['pratyantara'].append({
                                        'lord': pd_lord,
                                        'start': pd['start']
                                    })
                                md_entry['antardasha'].append(ad_entry)
                            mapped_periods.append(md_entry)
                        
                        dasha_data = {
                            'vimsottari': {
                                'periods': mapped_periods
                            }
                        }
                        horoscope["dasha"] = dasha_data
                        
                        # 2. Recalculate Planetary and House Strengths
                        from jhora.horoscope.chart import strength as _strength
                        ayanamsa = getattr(h, 'ayanamsa_mode', 'LAHIRI')
                        sb = _strength.shad_bala(jd, place, ayanamsa_mode=ayanamsa)
                        bb = _strength.bhava_bala(jd, place, ayanamsa_mode=ayanamsa)
                        
                        planet_names_7 = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                        stb, kb, dgb, cb, nb, dkb, sb_sum, sb_rupa, sb_strength = sb
                        
                        shadbala_data = {}
                        for idx, planet in enumerate(planet_names_7):
                            shadbala_data[planet] = {
                                'sthana_bala': float(stb[idx]),
                                'kaala_bala': float(kb[idx]),
                                'dig_bala': float(dgb[idx]),
                                'cheshta_bala': float(cb[idx]),
                                'naisargika_bala': float(nb[idx]),
                                'drik_bala': float(dkb[idx]),
                                'total_score': float(sb_sum[idx]),
                                'rupas': float(sb_rupa[idx]),
                                'strength_ratio': float(sb_strength[idx])
                            }
                            
                        bb_list, bb_rupas, bb_strength = bb
                        bhavabala_data = {}
                        for house_idx in range(12):
                            house_num = house_idx + 1
                            bhavabala_data[str(house_num)] = {
                                'total_score': float(bb_list[house_idx]),
                                'rupas': float(bb_rupas[house_idx]),
                                'strength_ratio': float(bb_strength[house_idx])
                            }
                            
                        strength_data = {
                            'shadbala': shadbala_data,
                            'bhavabala': bhavabala_data
                        }
                        horoscope["strength"] = strength_data
                        
                        if hasattr(stored_horo.response, 'model_dump'):
                            raw_horo = stored_horo.response.model_dump()
                        else:
                            raw_horo = stored_horo.response.dict()
                            
                        # Inject original birth details into raw_horo["meta"] to prevent active profile mismatches
                        if birth_details:
                            if "meta" not in raw_horo or not raw_horo["meta"]:
                                raw_horo["meta"] = {}
                            raw_horo["meta"]["name"] = birth_details.get("name")
                            raw_horo["meta"]["gender"] = birth_details.get("gender", "Unknown")
                            raw_horo["meta"]["birth_date"] = birth_details.get("date_of_birth")
                            raw_horo["meta"]["birth_time"] = birth_details.get("time_of_birth")
                            raw_horo["meta"]["birth_place"] = birth_details.get("place_of_birth")
                            raw_horo["meta"]["latitude"] = birth_details.get("latitude")
                            raw_horo["meta"]["longitude"] = birth_details.get("longitude")
                            
                        raw_horo["dasha"] = dasha_data
                        raw_horo["strength"] = strength_data
                        
                        await compress_and_store_horoscope(
                            user_email=user_email,
                            horoscope_data=raw_horo,
                            request_id=request_id
                        )
                        logger.info(f"[HOROSCOPE-UPGRADE] Successfully upgraded and saved horoscope {request_id} for user {user_email} permanently.")
            except Exception as upgrade_error:
                logger.error(f"[HOROSCOPE-UPGRADE] Failed to auto-upgrade horoscope: {upgrade_error}", exc_info=True)
                
        return horoscope
    
    except Exception as e:
        logger.error(f"Failed to retrieve horoscope: {e}")
        raise

async def list_user_horoscopes(
    user_email: str,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    List all horoscopes for a user
    
    Args:
        user_email: User's email
        limit: Max results to return
        skip: Number of results to skip
    
    Returns:
        List of horoscope summaries
    """
    if mongo_db.db is None:
        raise Exception("Database not initialized")
    
    try:
        cursor = mongo_db.db.horoscopes.find({
            "user_email": user_email
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        horoscopes = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for h in horoscopes:
            h["_id"] = str(h["_id"])
        
        return horoscopes
    
    except Exception as e:
        logger.error(f"Failed to list horoscopes: {e}")
        raise

async def delete_user_horoscope(
    user_email: str,
    request_id: str
) -> bool:
    """
    Delete a horoscope and its chunks
    
    Args:
        user_email: User's email
        request_id: Horoscope request ID
    
    Returns:
        True if deleted successfully
    """
    if mongo_db.db is None:
        raise Exception("Database not initialized")
    
    try:
        # Delete chunks
        await mongo_db.db.horoscope_chunks.delete_many({
            "user_email": user_email,
            "request_id": request_id
        })
        
        # Delete index
        result = await mongo_db.db.horoscopes.delete_one({
            "user_email": user_email,
            "request_id": request_id
        })
        
        return result.deleted_count > 0
    
    except Exception as e:
        logger.error(f"Failed to delete horoscope: {e}")
        raise

async def delete_all_user_horoscopes(user_email: str) -> bool:
    """
    Delete ALL horoscopes and chunks for a user
    
    Args:
        user_email: User's email
    
    Returns:
        True if successful
    """
    if mongo_db.db is None:
        raise Exception("Database not initialized")
    
    try:
        # Delete all chunks
        await mongo_db.db.horoscope_chunks.delete_many({
            "user_email": user_email
        })
        
        # Delete all index entries
        result = await mongo_db.db.horoscopes.delete_many({
            "user_email": user_email
        })
        
        logger.info(f"Deleted {result.deleted_count} horoscopes for user {user_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete all horoscopes: {e}")
        raise
