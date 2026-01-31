import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        """Connect to MongoDB."""
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME", "unified_backend")
        
        if not mongo_uri:
            logger.warning("MONGO_URI not set. MongoDB connection will be skipped.")
            return

        try:
            import certifi
            self.client = AsyncIOMotorClient(mongo_uri, tlsCAFile=certifi.where())
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB at {mongo_uri} (DB: {db_name})")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    async def initialize_collections(self):
        """Initialize all required collections with indexes."""
        if self.db is None:
            logger.warning("Database not connected. Skipping collection initialization.")
            return
        
        try:
            # Create collections if they don't exist
            collections = await self.db.list_collection_names()
            
            required_collections = [
                "users",
                "api_keys",
                "chats",
                "chat_messages",
                "payments",
                "referrals",
                "sessions",
                "horoscopes",
                "horoscope_chunks",
                "deva_conversations",
                "user_birth_details",
                "chat_question_tracking",
                "blogs",
                "refresh_tokens"
            ]
            
            for collection_name in required_collections:
                if collection_name not in collections:
                    await self.db.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
            
            # Create indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.api_keys.create_index("user_id")
            await self.db.api_keys.create_index("key", unique=True)
            await self.db.chats.create_index("user_id")
            await self.db.chat_messages.create_index("chat_id")
            await self.db.payments.create_index("user_id")
            await self.db.referrals.create_index("code", unique=True)
            await self.db.referrals.create_index("referrer_id")
            await self.db.sessions.create_index("user_id")
            await self.db.sessions.create_index("token_hash", unique=True)
            
            # Auth indexes
            await self.db.refresh_tokens.create_index("token", unique=True)
            await self.db.refresh_tokens.create_index("user_email")
            
            # Guest session persistence index
            await self.db.users.create_index([("is_guest", 1), ("device_id", 1)])
            
            # Horoscope indexes
            await self.db.horoscopes.create_index([("user_email", 1), ("request_id", 1)], unique=True)
            await self.db.horoscopes.create_index("user_email")
            await self.db.horoscopes.create_index("created_at")
            await self.db.horoscope_chunks.create_index([("user_email", 1), ("request_id", 1), ("chunk_index", 1)])
            await self.db.horoscope_chunks.create_index("request_id")
            
            # Deva Agent conversation indexes
            await self.db.deva_conversations.create_index("user_email")
            await self.db.deva_conversations.create_index("request_id")
            await self.db.deva_conversations.create_index("created_at")
            
            # Birth details indexes
            await self.db.user_birth_details.create_index("user_email", unique=True)
            
            # Chat question tracking indexes
            await self.db.chat_question_tracking.create_index("user_email", unique=True)
            
            # Blog indexes
            await self.db.blogs.create_index([("created_at", -1)])
            await self.db.blogs.create_index("category")
            
            logger.info("All collections and indexes initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

mongo_db = MongoDB()

async def connect_to_mongo():
    mongo_db.connect()
    await mongo_db.initialize_collections()

async def close_mongo_connection():
    mongo_db.close()
