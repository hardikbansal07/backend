"""
Horoscope Manager - Bridge for horoscope data retrieval from MongoDB
"""

import logging
from typing import Optional, Dict, Any
from logger_config import setup_logger
from db_manager import MongoDBManager


class HoroscopeManager:
    def __init__(self):
        self.logger = setup_logger("HoroscopeManager")
        
    def load_from_mongodb(self, request_id: str) -> Dict[str, Any]:
        """
        Load a horoscope from MongoDB using request_id.
        """
        try:
            self.logger.info(f"Loading horoscope from MongoDB for request_id: {request_id}")
            db_manager = MongoDBManager()
            horoscope_data = db_manager.get_horoscope_by_request_id(request_id)
            db_manager.close()
            
            if not horoscope_data:
                raise ValueError(f"Horoscope not found in MongoDB for request_id: {request_id}")
                
            return horoscope_data
        except Exception as e:
            self.logger.error(f"Failed to load from MongoDB: {e}", exc_info=True)
            raise

    def load_from_mongodb_by_email(self, email: str) -> Dict[str, Any]:
        """
        Load a horoscope from MongoDB using user_email.
        """
        try:
            self.logger.info(f"Loading horoscope from MongoDB for email: {email}")
            db_manager = MongoDBManager()
            horoscope_data = db_manager.get_horoscope_by_email(email)
            db_manager.close()
            
            if not horoscope_data:
                raise ValueError(f"Horoscope not found in MongoDB for email: {email}")
                
            return horoscope_data
        except Exception as e:
            self.logger.error(f"Failed to load from MongoDB by email: {email}: {e}", exc_info=True)
            raise
