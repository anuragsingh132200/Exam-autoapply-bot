"""
Workflow Session Model
Tracks the state and history of a workflow execution.
"""
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime


class LogEntry(BaseModel):
    """A single log entry during workflow execution."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: Literal["info", "warning", "error", "success"] = "info"
    message: str
    node: Optional[str] = None


class ScreenshotEntry(BaseModel):
    """A screenshot captured during workflow execution."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step: str
    image_base64: str
    url: Optional[str] = None


class PendingInput(BaseModel):
    """A pending human input request."""
    input_type: Literal["otp", "captcha", "custom"]
    field_id: str
    field_label: Optional[str] = None
    description: Optional[str] = None
    image_base64: Optional[str] = None  # For captcha
    options: Optional[list[str]] = None  # For select fields
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowSession(Document):
    """
    Workflow session document.
    Tracks the execution of a single form-filling workflow.
    """
    exam_id: PydanticObjectId
    user_id: PydanticObjectId
    
    # Current status
    status: Literal["pending", "running", "waiting_input", "paused", "completed", "failed"] = "pending"
    
    # LangGraph state (stored for resume capability)
    graph_state: dict[str, Any] = Field(default_factory=dict)
    current_node: Optional[str] = None
    thread_id: Optional[str] = None  # LangGraph thread for checkpointing
    
    # Progress tracking
    progress: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    
    # Human intervention
    pending_input: Optional[PendingInput] = None
    
    # Logs and screenshots
    logs: list[LogEntry] = Field(default_factory=list)
    screenshots: list[ScreenshotEntry] = Field(default_factory=list)
    
    # Result
    success: Optional[bool] = None
    result_message: Optional[str] = None
    error: Optional[str] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "workflow_sessions"
    
    def add_log(self, message: str, level: str = "info", node: str = None):
        """Add a log entry."""
        self.logs.append(LogEntry(
            message=message,
            level=level,
            node=node
        ))
    
    def add_screenshot(self, image_base64: str, step: str, url: str = None):
        """Add a screenshot entry."""
        self.screenshots.append(ScreenshotEntry(
            image_base64=image_base64,
            step=step,
            url=url
        ))
