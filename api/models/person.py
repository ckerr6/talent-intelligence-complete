# ABOUTME: Pydantic models for Person-related API endpoints
# ABOUTME: Request and response schemas for person operations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EmailBase(BaseModel):
    """Base email schema"""
    email: str = Field(..., description="Email address")
    email_type: Optional[str] = Field(None, description="Email type (work/personal/unknown)")
    is_primary: bool = Field(False, description="Whether this is the primary email")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v.lower()


class EmailResponse(EmailBase):
    """Email response schema"""
    email_id: int
    person_id: UUID
    verified: bool = False
    source: Optional[str] = None


class SocialProfileBase(BaseModel):
    """Base social profile schema"""
    platform: str = Field(..., description="Platform name (linkedin/github/twitter)")
    profile_url: str = Field(..., description="Profile URL")


class SocialProfileResponse(SocialProfileBase):
    """Social profile response schema"""
    profile_id: int
    person_id: UUID


class EmploymentBase(BaseModel):
    """Base employment schema"""
    company_name: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class EmploymentResponse(EmploymentBase):
    """Employment response schema"""
    employment_id: int
    person_id: UUID
    company_id: Optional[UUID] = None


class PersonBase(BaseModel):
    """Base person schema"""
    full_name: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None


class PersonCreate(PersonBase):
    """Schema for creating a person"""
    emails: Optional[List[EmailBase]] = Field(default_factory=list)
    
    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name is provided"""
        if not v or not v.strip():
            raise ValueError('Full name is required')
        return v.strip()


class PersonUpdate(BaseModel):
    """Schema for updating a person"""
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None


class PersonResponse(PersonBase):
    """Person response schema"""
    person_id: UUID
    normalized_linkedin_url: Optional[str] = None
    followers_count: Optional[int] = None
    created_at: Optional[datetime] = None
    refreshed_at: Optional[datetime] = None
    
    # Optional nested data
    emails: Optional[List[EmailResponse]] = None
    employment: Optional[List[EmploymentResponse]] = None
    
    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    """Simplified person response for lists"""
    person_id: UUID
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    
    class Config:
        from_attributes = True


class PersonSearchFilters(BaseModel):
    """Filters for person search"""
    company: Optional[str] = Field(None, description="Filter by company name")
    location: Optional[str] = Field(None, description="Filter by location")
    headline: Optional[str] = Field(None, description="Filter by headline/title")
    has_email: Optional[bool] = Field(None, description="Filter by email presence")
    has_github: Optional[bool] = Field(None, description="Filter by GitHub profile presence")

