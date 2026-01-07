"""
Batch Processing API
Handles batch workflow execution for multiple registrations.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
import asyncio

from app.models.exam import Exam
from app.models.user import User
from app.models.session import WorkflowSession
from app.api.websocket import manager, MessageTypes


router = APIRouter()


class BatchJob(BaseModel):
    """Batch job configuration."""
    id: str
    exam_id: str
    user_ids: list[str]
    status: Literal["pending", "running", "completed", "failed"]
    total: int
    completed: int
    successful: int
    failed: int
    created_at: datetime


# In-memory batch job storage (for demo - use Redis/MongoDB in production)
_batch_jobs: dict[str, dict] = {}


class BatchCreateRequest(BaseModel):
    """Request to create a batch job."""
    exam_id: str
    user_ids: list[str]
    delay_between_runs_seconds: int = 30  # Rate limiting


class BatchStatusResponse(BaseModel):
    """Response for batch status."""
    id: str
    status: str
    total: int
    completed: int
    successful: int
    failed: int
    progress: float
    sessions: list[dict]


@router.post("/")
async def create_batch(request: BatchCreateRequest, background_tasks: BackgroundTasks):
    """Create a new batch job."""
    # Validate exam exists
    exam = await Exam.get(PydanticObjectId(request.exam_id))
    if not exam:
        raise HTTPException(404, "Exam not found")
    
    # Validate users exist
    for user_id in request.user_ids:
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(404, f"User not found: {user_id}")
    
    # Create batch job
    batch_id = str(PydanticObjectId())
    batch = {
        "id": batch_id,
        "exam_id": request.exam_id,
        "user_ids": request.user_ids,
        "status": "pending",
        "total": len(request.user_ids),
        "completed": 0,
        "successful": 0,
        "failed": 0,
        "sessions": [],
        "delay_seconds": request.delay_between_runs_seconds,
        "created_at": datetime.utcnow()
    }
    _batch_jobs[batch_id] = batch
    
    # Start batch processing in background
    background_tasks.add_task(run_batch, batch_id)
    
    return {"batch_id": batch_id, "message": f"Batch created with {len(request.user_ids)} users"}


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Get batch job status."""
    batch = _batch_jobs.get(batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    
    return BatchStatusResponse(
        id=batch["id"],
        status=batch["status"],
        total=batch["total"],
        completed=batch["completed"],
        successful=batch["successful"],
        failed=batch["failed"],
        progress=(batch["completed"] / batch["total"]) * 100 if batch["total"] > 0 else 0,
        sessions=batch.get("sessions", [])
    )


@router.get("/")
async def list_batches():
    """List all batch jobs."""
    return [
        {
            "id": b["id"],
            "status": b["status"],
            "total": b["total"],
            "completed": b["completed"],
            "successful": b["successful"],
            "failed": b["failed"],
            "created_at": b["created_at"].isoformat()
        }
        for b in _batch_jobs.values()
    ]


@router.post("/{batch_id}/cancel")
async def cancel_batch(batch_id: str):
    """Cancel a running batch job."""
    batch = _batch_jobs.get(batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found")
    
    if batch["status"] in ["completed", "failed"]:
        raise HTTPException(400, "Batch already finished")
    
    batch["status"] = "cancelled"
    return {"message": "Batch cancelled"}


async def run_batch(batch_id: str):
    """
    Run batch processing.
    Creates workflow sessions for each user sequentially.
    """
    batch = _batch_jobs.get(batch_id)
    if not batch:
        return
    
    batch["status"] = "running"
    
    exam_id = batch["exam_id"]
    delay = batch.get("delay_seconds", 30)
    
    # Get exam details
    exam = await Exam.get(PydanticObjectId(exam_id))
    if not exam:
        batch["status"] = "failed"
        return
    
    for i, user_id in enumerate(batch["user_ids"]):
        # Check if cancelled
        if batch["status"] == "cancelled":
            break
        
        try:
            # Get user
            user = await User.get(PydanticObjectId(user_id))
            if not user:
                batch["failed"] += 1
                batch["completed"] += 1
                continue
            
            # Create workflow session
            session = WorkflowSession(
                exam_id=PydanticObjectId(exam_id),
                user_id=PydanticObjectId(user_id),
                status="pending",
                created_at=datetime.utcnow()
            )
            await session.insert()
            
            session_id = str(session.id)
            
            # Record session
            batch["sessions"].append({
                "session_id": session_id,
                "user_id": user_id,
                "user_name": user.profile.full_name,
                "status": "created"
            })
            
            # Broadcast progress
            await manager.broadcast({
                "type": MessageTypes.BATCH_PROGRESS,
                "payload": {
                    "batch_id": batch_id,
                    "current": i + 1,
                    "total": batch["total"],
                    "user_name": user.profile.full_name
                }
            })
            
            # TODO: Start actual workflow execution here
            # For now, we just create the sessions
            # The frontend can then monitor/start each session individually
            
            batch["completed"] += 1
            
            # Rate limiting - wait between runs
            if i < len(batch["user_ids"]) - 1:
                await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"[Batch] Error processing user {user_id}: {e}")
            batch["failed"] += 1
            batch["completed"] += 1
    
    batch["status"] = "completed" if batch["status"] != "cancelled" else "cancelled"
