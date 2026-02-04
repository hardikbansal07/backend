import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    print("Attempting to upload test file...")
    data = b"Hello World"
    res = supabase.storage.from_("reports").upload("test.txt", data, {"content-type": "text/plain", "upsert": "true"})
    print("Upload result:", res)
    
    # Get Public URL
    url = supabase.storage.from_("reports").get_public_url("test.txt")
    print(f"Public URL: {url}")
    print("SUCCESS: Upload verified.")
    
except Exception as e:
    print(f"FAIL: Upload failed: {e}")
