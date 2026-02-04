from typing import Dict, Any, Optional
from .config import client
import hmac
import hashlib
from .config import KEY_SECRET

# Tier Configuration
PLANS = {
    "plan_a": {"amount": 1, "questions": 10, "currency": "INR", "name": "Standard"},
    "plan_b": {"amount": 2, "questions": 20, "currency": "INR", "name": "Premium"},
    "plan_c": {"amount": 5, "questions": 50, "currency": "INR", "name": "Ultimate"}
}

def create_order(plan_id: str, receipt: str) -> Dict[str, Any]:
    """
    Create a Razorpay order for a specific plan
    """
    if plan_id not in PLANS:
        raise ValueError("Invalid Plan ID")
    
    plan = PLANS[plan_id]
    amount_paise = plan["amount"] * 100  # Convert to paise
    
    data = {
        "amount": amount_paise,
        "currency": plan["currency"],
        "receipt": receipt,
        "notes": {
            "plan_id": plan_id,
            "questions": plan["questions"]
        }
    }
    
    order = client.order.create(data=data)
    return order

def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verify Razorpay payment signature
    """
    if not KEY_SECRET:
        raise ValueError("Razorpay Secret not configured")
        
    msg = f"{order_id}|{payment_id}"
    
    generated_signature = hmac.new(
        KEY_SECRET.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(generated_signature, signature)

def get_plan_details(plan_id: str) -> Optional[Dict[str, Any]]:
    return PLANS.get(plan_id)
