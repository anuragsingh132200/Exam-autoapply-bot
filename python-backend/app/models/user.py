"""
User Model
Represents a user with profile data that can be used for form filling.
"""
from beanie import Document
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal, Any
from datetime import datetime


class ProfileData(BaseModel):
    """User's personal profile information."""
    full_name: str
    email: EmailStr
    phone: str
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[str] = None  # Format: DD/MM/YYYY
    gender: Optional[Literal["male", "female", "other"]] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None


class AcademicData(BaseModel):
    """User's academic information."""
    current_class: Optional[str] = None
    school_name: Optional[str] = None
    board: Optional[str] = None


class AddressData(BaseModel):
    """User's address information."""
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None


class User(Document):
    """
    User document model.
    Stores user profile data used for form filling.
    """
    # Core profile
    profile: ProfileData
    
    # Academic info
    academic: AcademicData = Field(default_factory=AcademicData)
    
    # Address
    address: AddressData = Field(default_factory=AddressData)
    
    # Custom fields per exam (key: exam slug)
    custom_fields: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Custom field values specific to each exam"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
    
    def get_flat_data(self) -> dict[str, Any]:
        """
        Returns a flattened dictionary of all user data for easy field mapping.
        Example: {"fullName": "John", "phone": "9999999999", ...}
        """
        flat = {}
        
        # Profile fields
        flat["fullName"] = self.profile.full_name
        flat["email"] = self.profile.email
        flat["phone"] = self.profile.phone
        flat["mobileNumber"] = self.profile.phone
        flat["alternatePhone"] = self.profile.alternate_phone
        flat["dateOfBirth"] = self.profile.date_of_birth
        flat["gender"] = self.profile.gender
        flat["guardianName"] = self.profile.guardian_name
        flat["guardianPhone"] = self.profile.guardian_phone
        flat["guardianMobileNumber"] = self.profile.guardian_phone
        
        # Academic fields
        flat["currentClass"] = self.academic.current_class
        flat["class"] = self.academic.current_class
        flat["schoolName"] = self.academic.school_name
        flat["board"] = self.academic.board
        
        # Address fields
        flat["pincode"] = self.address.pincode
        flat["city"] = self.address.city
        flat["state"] = self.address.state
        flat["address"] = self.address.address
        
        return flat
