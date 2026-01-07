"""
Field Mapping Model
Stores learned field mappings for the field learning system.
"""
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


class FieldMapping(Document):
    """
    Learned field mapping document.
    Maps form field labels to user data paths for auto-fill suggestions.
    """
    # The field label as seen on forms
    field_label: str = Field(..., description="Form field label text")
    
    # The user data path this maps to
    mapped_to: str = Field(..., description="User data path, e.g. 'profile.full_name'")
    
    # Exams where this mapping was used
    exams_seen: list[str] = Field(default_factory=list)
    
    # Confidence score based on usage
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Usage count
    times_used: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "field_mappings"
