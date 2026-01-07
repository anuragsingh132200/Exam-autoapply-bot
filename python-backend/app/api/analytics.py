"""
Analytics API Endpoints
Provides workflow analytics and statistics.
"""
from fastapi import APIRouter, HTTPException
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.models.analytics import ExamAnalytics
from app.models.session import WorkflowSession


router = APIRouter()


class AnalyticsResponse(BaseModel):
    """Response schema for analytics data."""
    exam_id: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    avg_duration_seconds: float
    otp_requests: int
    captcha_requests: int
    last_run_at: Optional[datetime]


class GlobalAnalytics(BaseModel):
    """Global analytics across all exams."""
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    active_sessions: int
    success_rate: float
    avg_duration_seconds: float


@router.get("/global", response_model=GlobalAnalytics)
async def get_global_analytics():
    """Get global analytics across all exams."""
    # Count sessions
    total = await WorkflowSession.count()
    successful = await WorkflowSession.find(WorkflowSession.status == "completed").count()
    failed = await WorkflowSession.find(WorkflowSession.status == "failed").count()
    active = await WorkflowSession.find(
        {"status": {"$in": ["running", "waiting_input", "pending"]}}
    ).count()
    
    # Calculate averages from analytics collection
    analytics_list = await ExamAnalytics.find().to_list()
    
    total_duration = sum(a.total_duration_seconds for a in analytics_list)
    total_runs = sum(a.total_runs for a in analytics_list) or 1
    
    return GlobalAnalytics(
        total_workflows=total,
        successful_workflows=successful,
        failed_workflows=failed,
        active_sessions=active,
        success_rate=successful / total if total > 0 else 0.0,
        avg_duration_seconds=total_duration / total_runs
    )


@router.get("/exam/{exam_id}", response_model=AnalyticsResponse)
async def get_exam_analytics(exam_id: PydanticObjectId):
    """Get analytics for a specific exam."""
    analytics = await ExamAnalytics.find_one(ExamAnalytics.exam_id == exam_id)
    
    if not analytics:
        # Return empty analytics if none exist
        return AnalyticsResponse(
            exam_id=str(exam_id),
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            success_rate=0.0,
            avg_duration_seconds=0.0,
            otp_requests=0,
            captcha_requests=0,
            last_run_at=None
        )
    
    return AnalyticsResponse(
        exam_id=str(analytics.exam_id),
        total_runs=analytics.total_runs,
        successful_runs=analytics.successful_runs,
        failed_runs=analytics.failed_runs,
        success_rate=analytics.success_rate,
        avg_duration_seconds=analytics.avg_duration_seconds,
        otp_requests=analytics.otp_requests,
        captcha_requests=analytics.captcha_requests,
        last_run_at=analytics.last_run_at
    )


@router.get("/recent-sessions")
async def get_recent_sessions(limit: int = 10):
    """Get recent workflow sessions."""
    sessions = await WorkflowSession.find().sort("-created_at").limit(limit).to_list()
    
    return [
        {
            "id": str(s.id),
            "exam_id": str(s.exam_id),
            "user_id": str(s.user_id),
            "status": s.status,
            "progress": s.progress,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "result_message": s.result_message
        }
        for s in sessions
    ]


@router.get("/failure-reasons/{exam_id}")
async def get_failure_reasons(exam_id: PydanticObjectId):
    """Get common failure reasons for an exam."""
    analytics = await ExamAnalytics.find_one(ExamAnalytics.exam_id == exam_id)
    
    if not analytics:
        return {"failure_reasons": {}}
    
    # Sort by count
    sorted_reasons = sorted(
        analytics.failure_reasons.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {"failure_reasons": dict(sorted_reasons[:10])}
