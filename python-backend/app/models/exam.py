"""
Exam Model
Represents an exam configuration with field mappings and agent settings.
"""
from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class FieldConfig(BaseModel):
    """Configuration for a single form field."""
    type: Literal["text", "phone", "email", "select", "date", "otp", "captcha"]
    required: bool = True
    options: Optional[list[str]] = None  # For select type
    stagehand_action: Optional[str] = None  # Custom action instruction


class CaptchaConfig(BaseModel):
    """Captcha auto-solve configuration."""
    auto_solve_enabled: bool = False
    provider: Literal["2captcha", "hcaptcha", "manual"] = "manual"
    api_key: Optional[str] = None
    timeout_seconds: int = 30


class AgentConfig(BaseModel):
    """LangGraph agent configuration."""
    max_retries: int = 3
    screenshot_interval_ms: int = 1000
    human_intervention_timeout_seconds: int = 300
    success_patterns: list[str] = []
    error_patterns: list[str] = []
    captcha: CaptchaConfig = CaptchaConfig()


class Exam(Document):
    """
    Exam document model.
    Stores configuration for automating a specific exam registration.
    """
    name: str = Field(..., description="Display name of the exam")
    slug: str = Field(..., description="URL-friendly identifier")
    url: str = Field(..., description="Registration page URL")
    is_active: bool = Field(default=True, description="Whether exam is enabled")
    
    # Field mappings: maps user data fields to form fields
    field_mappings: dict[str, FieldConfig] = Field(
        default_factory=dict,
        description="Mapping of user data fields to form field configurations"
    )
    
    # Agent configuration
    agent_config: AgentConfig = Field(default_factory=AgentConfig)
    
    # Email notifications
    notify_on_complete: bool = True
    notify_on_failure: bool = True
    notification_emails: list[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "exams"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "PW NSAT",
                "slug": "pwnsat",
                "url": "https://www.pw.live/scholarship/vidyapeeth/nsat",
                "is_active": True,
                "field_mappings": {
                    "fullName": {"type": "text", "required": True},
                    "phone": {"type": "phone", "required": True},
                    "class": {"type": "select", "options": ["11th", "12th"]}
                }
            }
        }
