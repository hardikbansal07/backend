from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from auth import get_current_active_user
from report_service import generate_pdf_report, upload_to_supabase, send_report_email
from models import User
from mongo import mongo_db
import uuid
import datetime
import asyncio
import logging
import json
import os
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
        
        # Save locally first (Always safe)
        local_path = os.path.join("generated", filename)
        with open(local_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Attempt upload
        url = await upload_to_supabase(pdf_bytes, filename)
        
        if not url:
            logger.warning("Supabase upload failed. Using LOCAL fallback.")
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            url = f"{base_url}/generated/{filename}"
            jobs[job_id]["message"] = "Report generated (Local View)"
        
        # Save report record in MongoDB for user history
        try:
            if mongo_db.db is not None:
                await mongo_db.db.user_reports.insert_one({
                    "user_email": user.email,
                    "job_id": job_id,
                    "report_type": report_type,
                    "download_url": url,
                    "filename": filename,
                    "created_at": datetime.datetime.now(),
                    "status": "completed"
                })
                logger.info(f"Report record saved for {user.email}")
        except Exception as db_err:
            logger.error(f"Failed to save report record: {db_err}")
        
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
    # 1. Check in-memory store first (for active/in-progress jobs)
    if job_id in jobs:
        return jobs[job_id]
    
    # 2. Fallback: Check MongoDB (for completed jobs that survived instance restart)
    if mongo_db.db is not None:
        saved_report = await mongo_db.db.user_reports.find_one(
            {"job_id": job_id, "user_email": current_user.email},
            {"_id": 0}
        )
        if saved_report:
            return ReportStatus(
                job_id=job_id,
                status=saved_report.get("status", "completed"),
                message="Report ready for download.",
                download_url=saved_report.get("download_url"),
                estimated_time="0 seconds"
            )
    
    # 3. Not found anywhere
    raise HTTPException(status_code=404, detail="Job not found. Please generate a new report.")

@router.get("/my-reports")
async def get_my_reports(current_user: User = Depends(get_current_active_user)):
    """
    Get all reports generated by the current user.
    User can re-download any past report from here.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    reports = await mongo_db.db.user_reports.find(
        {"user_email": current_user.email},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Convert datetime to string for JSON
    for r in reports:
        if "created_at" in r:
            r["created_at"] = r["created_at"].isoformat()
    
    return {"reports": reports, "total": len(reports)}
