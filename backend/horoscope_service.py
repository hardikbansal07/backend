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
        # Step 0: Fetch Vimsottari Dasha data if not present
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
                        logger.info(f"Fetched and added Vimsottari Dasha data for request {request_id}")
            except Exception as dasha_error:
                # Log warning but continue without dasha data
                logger.warning(f"Could not fetch Dasha data for {request_id}: {dasha_error}")
        
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
        
        logger.info(f"Stored horoscope {request_id} for user {user_email} in {len(chunks)} chunks")
        
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
            elif chunk_type == "divisional":
                chart_name = chunk.get("chart_name")
                if chart_name:
                    horoscope["d_series"][chart_name] = data
        
        logger.info(f"[HOROSCOPE] Final horoscope: lagna={horoscope['lagna'] is not None}, dasha={horoscope['dasha'] is not None}, d_series_count={len(horoscope['d_series'])}")
        
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
