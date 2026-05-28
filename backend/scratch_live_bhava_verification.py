import os
import sys
import json
import asyncio
from datetime import datetime

# Setup paths and environment
sys.path.append(r"c:\Users\acer\backend folder\backend")
sys.path.insert(0, r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src")
os.environ["MONGO_URI"] = "mongodb+srv://Astrocare7:Astrocare7337@cluster0.ydviwil.mongodb.net/"
os.environ["DB_NAME"] = "Astrocare7"
os.environ["SE_EPHE_PATH"] = r"c:\Users\acer\backend folder\backend\calculation\calculation-main\src\jhora\data\ephe"

from motor.motor_asyncio import AsyncIOMotorClient
from mongo import mongo_db
from api.models import HoroscopeRequest, LocationIn
from api.service import compute_horoscope
from horoscope_service import get_user_horoscope, compress_and_store_horoscope

async def run_verification():
    mongo_db.client = AsyncIOMotorClient(os.environ["MONGO_URI"])
    mongo_db.db = mongo_db.client[os.environ["DB_NAME"]]
    
    user_email = "chalmaibhe@gmail.com"
    
    print("\nRegenerating Hardik's Horoscope using our corrected live service...")
    loc = LocationIn(
        place="Delhi, India",
        latitude=28.6328027,
        longitude=77.2197713,
        tzOffset=5.5
    )
    birth_dt = datetime.fromisoformat("2001-03-07T16:20:00")
    req_obj = HoroscopeRequest(
        birthDateTime=birth_dt,
        location=loc,
        language="en",
        name="hardik",
        ayanamsaMode="LAHIRI"
    )
    
    # This will calculate, compress and store the horoscope permanently in DB
    stored = compute_horoscope(req_obj)
    request_id = "b322d01eb554d78126553a71bf36666dd71e9396bbd0c573dab561cf24f80d96"
    
    if hasattr(stored, 'response') and stored.response is not None:
        if hasattr(stored.response, 'model_dump'):
            raw_horo = stored.response.model_dump()
        else:
            raw_horo = stored.response.dict()
    else:
        if hasattr(stored, 'model_dump'):
            raw_horo = stored.model_dump()
        else:
            raw_horo = stored.dict()
        
    await compress_and_store_horoscope(user_email, raw_horo, request_id)
    print(f"Stored successfully! Request ID: {request_id}")
    
    # Retrieve it back to verify
    horo = await get_user_horoscope(user_email, request_id)
    if horo:
        print("\nSUCCESS! VERIFYING RETRIEVED HOUSE BHAVA BALA VALUES:")
        bhavabala = horo.get("strength", {}).get("bhavabala", {})
        
        expected_bhava_bala = {
            "1": 563.91,
            "2": 508.98,
            "3": 574.29,
            "4": 529.46,
            "5": 388.19,
            "6": 497.54,
            "7": 455.59,
            "8": 410.70,
            "9": 454.70,
            "10": 396.58,
            "11": 507.28,
            "12": 510.16
        }
        
        print("House | Live Computed Bhava Bala | JHora Expected | Diff")
        print("-" * 55)
        for h in range(1, 13):
            h_str = str(h)
            calc_val = bhavabala.get(h_str, {}).get("total_score", 0.0)
            exp_val = expected_bhava_bala.get(h_str, 0.0)
            diff = calc_val - exp_val
            print(f"House {h:2d} | {calc_val:23.2f} | {exp_val:14.2f} | {diff:+.2f}")
    else:
        print("Failed to retrieve horoscope!")

if __name__ == "__main__":
    asyncio.run(run_verification())
