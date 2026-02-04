
import asyncio
import os
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load config
load_dotenv()

# Setup hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

async def fix_admin_user():
    print("Connecting to MongoDB...")
    # Using the connection string from main.py logging seen in previous turns
    # "mongodb+srv://Astrocare7:Rekha%407337@cluster0.ydviwil.mongodb.net/?appName=Cluster0"
    uri = os.getenv("MONGO_URI", "mongodb+srv://Astrocare7:Rekha%407337@cluster0.ydviwil.mongodb.net/?appName=Cluster0")
    client = AsyncIOMotorClient(uri)
    db = client.astrocare7 # Using the DB name seen in logs
    
    email = "admin@example.com"
    password = "password" # Resetting to 'password'
    
    print(f"Checking user: {email}")
    user = await db.users.find_one({"email": email})
    
    if user:
        print("User found. Updating password hash and role...")
        hashed_password = get_password_hash(password)
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "role": "admin",
                    "full_name": "Admin User",
                    "is_banned": False
                }
            }
        )
        print("User updated successfully.")
    else:
        print("User not found. Creating new admin user...")
        hashed_password = get_password_hash(password)
        new_user = {
            "email": email,
            "username": "admin",
            "full_name": "Admin User",
            "hashed_password": hashed_password,
            "role": "admin",
            "disabled": False,
            "is_banned": False,
            "credits": 1000,
            "created_at": "2024-01-01T00:00:00.000000"
        }
        await db.users.insert_one(new_user)
        print("Admin user created successfully.")

    client.close()

if __name__ == "__main__":
    asyncio.run(fix_admin_user())
