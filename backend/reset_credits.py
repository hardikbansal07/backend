import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    uri = "mongodb+srv://Astrocare7:Astrocare7337@cluster0.ydviwil.mongodb.net/"
    client = AsyncIOMotorClient(uri)
    db = client["Astrocare7"]
    result = await db.users.update_many({}, {"$set": {"credits": 1000}})
    print(f"Updated {result.modified_count} users to 1000 credits!")

asyncio.run(run())
