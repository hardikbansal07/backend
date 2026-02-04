import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing credentials")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    res = supabase.storage.list_buckets()
    print("Buckets found:", res)
    
    # Check if 'reports' exists
    buckets = res
    report_bucket = next((b for b in buckets if b.name == 'reports'), None)
    
    if report_bucket:
        print("PASS: 'reports' bucket exists.")
    else:
        print("FAIL: 'reports' bucket does not exist.")
        # Try creating it?
        try:
            print("Attempting to create 'reports' bucket...")
            supabase.storage.create_bucket("reports", options={"public": True})
            print("PASS: Created 'reports' bucket.")
        except Exception as e:
            print(f"FAIL: Could not create bucket: {e}")
            
except Exception as e:
    print("Error listing buckets:", e)
