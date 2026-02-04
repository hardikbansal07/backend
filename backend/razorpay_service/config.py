import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

if not KEY_ID or not KEY_SECRET:
    print("WARNING: Razorpay keys are missing in environment variables.")

# Initialize Client
client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
