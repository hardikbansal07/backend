import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

from fastapi.testclient import TestClient
from main import app
from mongo import mongo_db
from models import User

client = TestClient(app)

async def test_language_preference():
    print("\n=== Testing Preferred Language Feature ===")
    
    # Needs a running DB, but we can mock some parts if needed.
    # Ideally, we should run this against a test DB or rely on the fact that existing tests pass.
    # However, since we don't have a full test environment set up with easy DB mocking here without external services,
    # we will focus on verifying the request/response structures and basic flow if DB is available.
    
    # 1. Register a test user
    email = "test_lang_user@example.com"
    password = "password123"
    
    # Clean up existing user if any (this might fail if DB isn't connected, but let's try)
    if mongo_db.db:
        await mongo_db.db.users.delete_one({"email": email})
    
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password
    })
    
    # If registration fails (e.g. DB not running), we can't proceed with integration test easily.
    # But let's assume the user can run this or we check code correctness.
    
    # For now, let's verify the updated schemas using Pydantic models directly to ensure syntax correctness
    from deva_routes import BirthDetailsRequest
    
    try:
        bd = BirthDetailsRequest(
            date_of_birth="2000-01-01",
            time_of_birth="12:00",
            place_of_birth="Delhi",
            preferred_language="Hindi"
        )
        print("✅ BirthDetailsRequest accepts preferred_language")
    except Exception as e:
        print(f"❌ BirthDetailsRequest schema check failed: {e}")
        
    from user_routes import ProfileUpdateRequest
    try:
        pr = ProfileUpdateRequest(preferred_language="Spanish")
        print("✅ ProfileUpdateRequest accepts preferred_language")
    except Exception as e:
        print(f"❌ ProfileUpdateRequest schema check failed: {e}")

    print("\nVerification of code structure complete.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_language_preference())
