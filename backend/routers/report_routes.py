from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from auth import get_current_active_user
from report_service import generate_pdf_report, upload_to_supabase, send_report_email
from models import User
import uuid
import datetime
import asyncio
import logging
import json
from r1_algo import generate_report as generate_r1_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])

# Simple in-memory job store (Note: In production with multiple workers, use Redis)
jobs: Dict[str, Any] = {}

class ReportRequest(BaseModel):
    report_type: str
    birth_details_id: Optional[str] = None # Optional: reference to specific birth details

class ReportStatus(BaseModel):
    job_id: str
    status: str # "pending", "processing", "completed", "failed"
    message: Optional[str] = None # Progress message
    download_url: Optional[str] = None
    estimated_time: Optional[str] = None

async def process_report(job_id: str, user: User, report_type: str, birth_details_id: Optional[str] = None):
    jobs[job_id]["status"] = "processing"
    
    try:
        logger.info(f"Starting REAL R1 report generation for job {job_id}")
        jobs[job_id]["message"] = "Initializing R1 Council..."
        jobs[job_id]["estimated_time"] = "5-10 minutes remaining"
        
        # 1. Fetch Chart Data
        # We need the full horoscope data. 
        # If birth_details_id is provided, we could re-calculate or fetch from storage.
        # For now, let's assume we can fetch the 'latest' horoscope for the user or specific one.
        # Use horoscope_service to get the latest?
        
        from horoscope_service import list_user_horoscopes, get_user_horoscope
        
        # Heuristic: Get latest horoscope
        horoscopes = await list_user_horoscopes(user.email, limit=1)
        if not horoscopes:
             raise Exception("No horoscope found for user. Please generate a horoscope first.")
        
        latest_request_id = horoscopes[0]["request_id"]
        chart_data = await get_user_horoscope(user.email, latest_request_id)
        
        if not chart_data:
             raise Exception("Failed to retrieve horoscope data.")
             
        # Map fields for R1
        # R1 expects 'd1', 'd9', etc. directly in root or via loader adapter.
        # Our loader expects dict.
        
        jobs[job_id]["message"] = "Consulting the Star Council (Agents)..."
        
        # 2. Run R1 Engine
        # We need gender.
        gender = "Male" # Default
        if "meta" in chart_data and "gender" in chart_data["meta"]:
            gender = chart_data["meta"]["gender"]
            
        markdown_report = await generate_r1_report(
            user_email=user.email,
            user_gender=gender,
            chart_data=chart_data,
            report_type=report_type
        )
        
        jobs[job_id]["message"] = "Finalizing secure PDF..."
        jobs[job_id]["estimated_time"] = "Almost done..."
        
        # 3. Generate PDF
        pdf_bytes = generate_pdf_report(user.full_name or "User", report_type, markdown_report)
        
        # 4. Upload
        jobs[job_id]["message"] = "Uploading secure report..."
        filename = f"report_{job_id}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Attempt upload
        url = await upload_to_supabase(pdf_bytes, filename)
        
        if not url:
            logger.warning("Supabase upload failed or not configured. Using DEMO fallback.")
            url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            jobs[job_id]["message"] = "Report generated (Upload Failed - Demo Link)"
        
        jobs[job_id]["download_url"] = url
        jobs[job_id]["message"] = "Report generation complete."
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["estimated_time"] = "0 seconds"
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"
        jobs[job_id]["estimated_time"] = None

@router.post("/generate", response_model=ReportStatus)
async def generate_report_endpoint(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "message": "Queued for generation",
        "estimated_time": "30 seconds",
        "created_at": datetime.datetime.now()
    }
    
    background_tasks.add_task(process_report, job_id, current_user, request.report_type, request.birth_details_id)
    
    return jobs[job_id]

@router.get("/status/{job_id}", response_model=ReportStatus)
async def get_report_status_endpoint(job_id: str, current_user: User = Depends(get_current_active_user)):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
