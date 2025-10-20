# ABOUTME: Pydantic models for Company-related API endpoints
# ABOUTME: Request and response schemas for company operations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CompanyBase(BaseModel):
    """Base company schema"""
    company_name: str = Field(..., max_length=255, description="Company name")
    linkedin_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    employee_count: Optional[int] = Field(None, ge=0)


class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    
    @field_validator('company_name')
    @classmethod
    def validate_name(cls, v):
        """Ensure company name is provided"""
        if not v or not v.strip():
            raise ValueError('Company name is required')
        return v.strip()
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        """Validate website URL format"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class CompanyUpdate(BaseModel):
    """Schema for updating a company"""
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None


class CompanyResponse(CompanyBase):
    """Company response schema"""
    company_id: UUID
    normalized_linkedin_url: Optional[str] = None
    created_at: Optional[datetime] = None
    employee_count_in_db: Optional[int] = Field(None, description="Number of employees in database")
    
    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Simplified company response for lists"""
    company_id: UUID
    company_name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    employee_count_in_db: Optional[int] = None
    
    class Config:
        from_attributes = True


class CompanySearchFilters(BaseModel):
    """Filters for company search"""
    industry: Optional[str] = Field(None, description="Filter by industry")
    has_website: Optional[bool] = Field(None, description="Filter by website presence")
    min_employees: Optional[int] = Field(None, ge=0, description="Minimum employee count")

