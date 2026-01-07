"""
Exam API Endpoints
CRUD operations for exam configurations.
"""
from fastapi import APIRouter, HTTPException, status
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.exam import Exam, FieldConfig, AgentConfig


router = APIRouter()


# ============= Request/Response Schemas =============

class ExamCreate(BaseModel):
    """Schema for creating a new exam."""
    name: str
    slug: str
    url: str
    is_active: bool = True
    field_mappings: dict[str, FieldConfig] = {}
    agent_config: Optional[AgentConfig] = None
    notify_on_complete: bool = True
    notify_on_failure: bool = True
    notification_emails: list[str] = []


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    field_mappings: Optional[dict[str, FieldConfig]] = None
    agent_config: Optional[AgentConfig] = None
    notify_on_complete: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_emails: Optional[list[str]] = None


class ExamResponse(BaseModel):
    """Schema for exam response."""
    id: str
    name: str
    slug: str
    url: str
    is_active: bool
    field_mappings: dict[str, FieldConfig]
    agent_config: AgentConfig
    notify_on_complete: bool
    notify_on_failure: bool
    notification_emails: list[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_document(cls, exam: Exam) -> "ExamResponse":
        return cls(
            id=str(exam.id),
            name=exam.name,
            slug=exam.slug,
            url=exam.url,
            is_active=exam.is_active,
            field_mappings=exam.field_mappings,
            agent_config=exam.agent_config,
            notify_on_complete=exam.notify_on_complete,
            notify_on_failure=exam.notify_on_failure,
            notification_emails=exam.notification_emails,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
        )


# ============= Endpoints =============

@router.get("/", response_model=list[ExamResponse])
async def list_exams(active_only: bool = False):
    """List all exams."""
    query = {"is_active": True} if active_only else {}
    exams = await Exam.find(query).to_list()
    return [ExamResponse.from_document(e) for e in exams]


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: PydanticObjectId):
    """Get a specific exam by ID."""
    exam = await Exam.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return ExamResponse.from_document(exam)


@router.get("/slug/{slug}", response_model=ExamResponse)
async def get_exam_by_slug(slug: str):
    """Get a specific exam by slug."""
    exam = await Exam.find_one(Exam.slug == slug)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return ExamResponse.from_document(exam)


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(data: ExamCreate):
    """Create a new exam configuration."""
    # Check if slug already exists
    existing = await Exam.find_one(Exam.slug == data.slug)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Exam with slug '{data.slug}' already exists"
        )
    
    # Create exam
    exam = Exam(
        name=data.name,
        slug=data.slug,
        url=data.url,
        is_active=data.is_active,
        field_mappings=data.field_mappings,
        agent_config=data.agent_config or AgentConfig(),
        notify_on_complete=data.notify_on_complete,
        notify_on_failure=data.notify_on_failure,
        notification_emails=data.notification_emails,
    )
    await exam.insert()
    
    return ExamResponse.from_document(exam)


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(exam_id: PydanticObjectId, data: ExamUpdate):
    """Update an existing exam."""
    exam = await Exam.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam, field, value)
    
    exam.updated_at = datetime.utcnow()
    await exam.save()
    
    return ExamResponse.from_document(exam)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(exam_id: PydanticObjectId):
    """Delete an exam."""
    exam = await Exam.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    await exam.delete()
    return None


@router.post("/{exam_id}/toggle", response_model=ExamResponse)
async def toggle_exam_status(exam_id: PydanticObjectId):
    """Toggle exam active status."""
    exam = await Exam.get(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam.is_active = not exam.is_active
    exam.updated_at = datetime.utcnow()
    await exam.save()
    
    return ExamResponse.from_document(exam)
