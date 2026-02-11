import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

# Force reload of .env
load_dotenv(override=True)

async def test_connection():
    mongo_uri = os.getenv("MONGO_URI")
    print(f"Testing connection to: {mongo_uri}")
    
    if not mongo_uri:
        print("ERROR: MONGO_URI is not set in .env")
        return

    try:
        client = AsyncIOMotorClient(mongo_uri, tlsCAFile=certifi.where())
        # Force a command to verify connection
        await client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB!")
    except Exception as e:
        print(f"FAILURE: Could not connect to MongoDB.")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
