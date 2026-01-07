"""
User API Endpoints
CRUD operations for user profiles.
"""
from fastapi import APIRouter, HTTPException, status
from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime

from app.models.user import User, ProfileData, AcademicData, AddressData


router = APIRouter()


# ============= Request/Response Schemas =============

class ProfileDataCreate(BaseModel):
    """Schema for profile data."""
    full_name: str
    email: EmailStr
    phone: str
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None


class AcademicDataCreate(BaseModel):
    """Schema for academic data."""
    current_class: Optional[str] = None
    school_name: Optional[str] = None
    board: Optional[str] = None


class AddressDataCreate(BaseModel):
    """Schema for address data."""
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    profile: ProfileDataCreate
    academic: Optional[AcademicDataCreate] = None
    address: Optional[AddressDataCreate] = None
    custom_fields: dict[str, dict[str, Any]] = {}


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    profile: Optional[ProfileDataCreate] = None
    academic: Optional[AcademicDataCreate] = None
    address: Optional[AddressDataCreate] = None
    custom_fields: Optional[dict[str, dict[str, Any]]] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    profile: ProfileData
    academic: AcademicData
    address: AddressData
    custom_fields: dict[str, dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_document(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            profile=user.profile,
            academic=user.academic,
            address=user.address,
            custom_fields=user.custom_fields,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserFlatData(BaseModel):
    """Flattened user data for form filling."""
    id: str
    data: dict[str, Any]


# ============= Endpoints =============

@router.get("/", response_model=list[UserResponse])
async def list_users():
    """List all users."""
    users = await User.find().to_list()
    return [UserResponse.from_document(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: PydanticObjectId):
    """Get a specific user by ID."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_document(user)


@router.get("/{user_id}/flat", response_model=UserFlatData)
async def get_user_flat(user_id: PydanticObjectId):
    """Get flattened user data for form filling."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserFlatData(id=str(user.id), data=user.get_flat_data())


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate):
    """Create a new user."""
    # Check if email already exists
    existing = await User.find_one({"profile.email": data.profile.email})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User with email '{data.profile.email}' already exists"
        )
    
    # Create user
    user = User(
        profile=ProfileData(**data.profile.model_dump()),
        academic=AcademicData(**(data.academic.model_dump() if data.academic else {})),
        address=AddressData(**(data.address.model_dump() if data.address else {})),
        custom_fields=data.custom_fields,
    )
    await user.insert()
    
    return UserResponse.from_document(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: PydanticObjectId, data: UserUpdate):
    """Update an existing user."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if data.profile:
        user.profile = ProfileData(**data.profile.model_dump())
    if data.academic:
        user.academic = AcademicData(**data.academic.model_dump())
    if data.address:
        user.address = AddressData(**data.address.model_dump())
    if data.custom_fields is not None:
        user.custom_fields = data.custom_fields
    
    user.updated_at = datetime.utcnow()
    await user.save()
    
    return UserResponse.from_document(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: PydanticObjectId):
    """Delete a user."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await user.delete()
    return None


@router.post("/{user_id}/custom-fields/{exam_slug}")
async def update_custom_fields(
    user_id: PydanticObjectId,
    exam_slug: str,
    fields: dict[str, Any]
):
    """Update custom fields for a specific exam."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.custom_fields[exam_slug] = fields
    user.updated_at = datetime.utcnow()
    await user.save()
    
    return {"message": f"Custom fields updated for exam '{exam_slug}'"}
