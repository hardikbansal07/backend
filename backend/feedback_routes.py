from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from mongo import mongo_db
from auth import get_current_user_optional
from models import Feedback, User

logger = logging.getLogger(__name__)
router = APIRouter()

class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None

@router.post("/api/v1/feedback")
async def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    try:
        feedback_dict = {
            "rating": feedback_data.rating,
            "review_text": feedback_data.review_text,
            "created_at": datetime.utcnow()
        }
        
        if current_user:
            feedback_dict["username"] = current_user.username or current_user.email.split('@')[0]
            feedback_dict["user_id"] = current_user.email
        else:
            feedback_dict["username"] = "Anonymous"
            feedback_dict["user_id"] = None
        
        result = await mongo_db.db.feedback.insert_one(feedback_dict)
        
        logger.info(f"Feedback submitted: {result.inserted_id} by {feedback_dict['username']}")
        
        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": str(result.inserted_id)
        }
    
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/api/v1/feedback/stats")
async def get_feedback_stats():
    try:
        total_feedback = await mongo_db.db.feedback.count_documents({})
        
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "average_rating": {"$avg": "$rating"},
                    "total_count": {"$sum": 1}
                }
            }
        ]
        
        result = await mongo_db.db.feedback.aggregate(pipeline).to_list(1)
        
        if result:
            return {
                "total_feedback": result[0]["total_count"],
                "average_rating": round(result[0]["average_rating"], 2)
            }
        
        return {
            "total_feedback": 0,
            "average_rating": 0
        }
    
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback stats")
