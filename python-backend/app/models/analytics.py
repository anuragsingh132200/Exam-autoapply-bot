"""
Analytics Model
Stores aggregated workflow analytics per exam.
"""
from beanie import Document, PydanticObjectId
from pydantic import Field
from typing import Optional
from datetime import datetime


class ExamAnalytics(Document):
    """
    Exam analytics document.
    Stores aggregated statistics for workflow executions.
    """
    exam_id: PydanticObjectId
    
    # Run statistics
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    
    # Timing
    total_duration_seconds: float = 0.0
    avg_duration_seconds: float = 0.0
    
    # Common failure reasons
    failure_reasons: dict[str, int] = Field(
        default_factory=dict,
        description="Count of each failure reason"
    )
    
    # Human intervention stats
    otp_requests: int = 0
    captcha_requests: int = 0
    custom_input_requests: int = 0
    
    # Last updated
    last_run_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "analytics"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs
    
    def record_run(self, success: bool, duration_seconds: float, failure_reason: str = None):
        """Record a completed workflow run."""
        self.total_runs += 1
        self.total_duration_seconds += duration_seconds
        self.avg_duration_seconds = self.total_duration_seconds / self.total_runs
        self.last_run_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
            if failure_reason:
                self.failure_reasons[failure_reason] = self.failure_reasons.get(failure_reason, 0) + 1
