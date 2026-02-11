import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

from logger_config import setup_logger

logger = setup_logger("MongoDBManager")

class MongoDBManager:
    """Manages connections and data retrieval from MongoDB."""
    
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_URI")
        if not self.uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(self.uri)
        db_name = os.getenv("DB_NAME", "astrocare7")
        self.db = self.client[db_name]
        self.horoscopes_coll = self.db["horoscopes"]
        self.chunks_coll = self.db["horoscope_chunks"]
        
        # Test connection and document count (with more detail)
        try:
            doc_count = self.horoscopes_coll.count_documents({})
            logger.info(f"Connected to MongoDB. Database='{self.db.name}', Collection='{self.horoscopes_coll.name}'")
            logger.info(f"Total documents available: {doc_count}")
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")

    def get_horoscope_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves and reassembles a horoscope from chunked data in MongoDB.
        """
        logger.info(f"Fetching horoscope for request_id: {request_id}")
        
        # Query for all chunks belonging to this request_id, sorted by chunkIndex
        cursor = self.chunks_coll.find({"request_id": request_id}).sort("chunkIndex", 1)
        chunks = list(cursor)
        
        if not chunks:
            # Fallback to requestId (camelCase) if request_id fails
            cursor = self.chunks_coll.find({"requestId": request_id}).sort("chunkIndex", 1)
            chunks = list(cursor)
            
        if not chunks:
            logger.warning(f"No chunks found for request_id: {request_id} in {self.chunks_coll.name}")
            return None
        
        # Reassemble data (robust handling for dict vs str/bytes)
        import json
        
        # Check if chunks are already dictionaries
        if chunks and isinstance(chunks[0].get("data"), dict):
            logger.info(f"Merging {len(chunks)} dictionary chunks for {request_id}")
            full_data = {}
            for chunk in chunks:
                d = chunk.get("data")
                if isinstance(d, dict):
                    full_data.update(d)
                else:
                    logger.warning(f"Expected dict chunk but got {type(d)}")
            
            logger.info(f"Reassembled dict horoscope. Keys: {list(full_data.keys())[:10]}...")
            return full_data

        # Standard string reassembly
        reassembled_parts = []
        for chunk in chunks:
            data_part = chunk.get("data")
            if isinstance(data_part, str):
                reassembled_parts.append(data_part)
            elif isinstance(data_part, (bytes, bytearray)):
                reassembled_parts.append(data_part.decode('utf-8'))
            elif data_part is not None:
                # Fallback: stringify it
                reassembled_parts.append(json.dumps(data_part) if isinstance(data_part, dict) else str(data_part))
        
        full_data_str = "".join(reassembled_parts)
        
        # Parse JSON
        try:
            horoscope_data = json.loads(full_data_str)
            logger.info(f"Successfully reassembled JSON horoscope for {request_id}")
            return horoscope_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode reassembled JSON for {request_id}: {e}")
            # Final attempt: if it's only one chunk and it's a weird format, try returning it raw
            if len(chunks) == 1:
                return chunks[0].get("data")
            return None

    def get_horoscope_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Finds the most recent requestId for the given email and retrieves the horoscope.
        """
        logger.info(f"Searching for email: '{email}' in {self.horoscopes_coll.name}")
        
        # Use snake_case as primary, camelCase as secondary
        # First attempt: Exact match on user_email
        cursor = self.horoscopes_coll.find({"user_email": email}).sort("created_at", -1).limit(1)
        latest_doc = next(cursor, None)
        
        if not latest_doc:
            # Second attempt: Exact match on userEmail
            cursor = self.horoscopes_coll.find({"userEmail": email}).sort("createdAt", -1).limit(1)
            latest_doc = next(cursor, None)
            
        if not latest_doc:
            # Third attempt: Case-insensitive on user_email
            import re
            regex = re.compile(f"^{re.escape(email)}$", re.IGNORECASE)
            cursor = self.horoscopes_coll.find({"user_email": regex}).sort("created_at", -1).limit(1)
            latest_doc = next(cursor, None)

        if not latest_doc:
            logger.warning(f"No document found for email: '{email}' in {self.horoscopes_coll.name}")
            return None
        
        request_id = latest_doc.get("request_id") or latest_doc.get("requestId")
        if not request_id:
            logger.error(f"Found doc for {email} but no request_id field. Doc ID: {latest_doc.get('_id')}")
            return None
            
        logger.info(f"Found request_id: {request_id} for email: {email}")
        return self.get_horoscope_by_request_id(request_id)

    def close(self):
        self.client.close()
