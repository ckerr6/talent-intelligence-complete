# ABOUTME: Advanced search models for multi-criteria candidate search
# ABOUTME: Includes request models, response models, and match explanations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced multi-criteria search"""
    
    technologies: Optional[List[str]] = Field(
        default=None,
        description="Programming languages/technologies (e.g., ['Rust', 'Solidity', 'TypeScript'])"
    )
    companies: Optional[List[str]] = Field(
        default=None,
        description="Current or past employers (e.g., ['Uniswap', 'Paradigm'])"
    )
    titles: Optional[List[str]] = Field(
        default=None,
        description="Job title patterns (e.g., ['Engineer', 'Developer', 'Researcher'])"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Skills, domains, or expertise keywords (e.g., ['DeFi', 'trading systems'])"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location filter (e.g., 'San Francisco', 'Remote')"
    )
    min_experience_years: Optional[int] = Field(
        default=None,
        ge=0,
        le=50,
        description="Minimum years of professional experience"
    )
    has_email: Optional[bool] = Field(
        default=None,
        description="Filter by email availability"
    )
    has_github: Optional[bool] = Field(
        default=None,
        description="Filter by GitHub profile presence"
    )
    github_min_stars: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum total GitHub stars across contributions"
    )
    github_min_repos: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum number of repository contributions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "technologies": ["Rust", "Solidity"],
                "companies": ["Uniswap", "Paradigm"],
                "titles": ["Senior Engineer", "Protocol Developer"],
                "keywords": ["DeFi", "smart contracts"],
                "location": "San Francisco",
                "has_email": True,
                "has_github": True
            }
        }


class MatchExplanation(BaseModel):
    """Explanation of why a candidate matched the search criteria"""
    
    matched_technologies: List[str] = Field(
        default_factory=list,
        description="Technologies the candidate has contributed to"
    )
    matched_companies: List[str] = Field(
        default_factory=list,
        description="Companies the candidate has worked at"
    )
    matched_titles: List[str] = Field(
        default_factory=list,
        description="Job titles that matched the search"
    )
    matched_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords found in profile"
    )
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall relevance score (0-100)"
    )
    match_summary: str = Field(
        default="",
        description="Human-readable summary of why this candidate matched"
    )


class SearchResultPerson(BaseModel):
    """Person data in search results"""
    
    person_id: str
    full_name: str
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    has_email: bool = False
    has_github: bool = False
    importance_score: Optional[float] = None
    
    # Summary data for display
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[int] = None
    total_github_stars: Optional[int] = None
    github_username: Optional[str] = None


class SearchResultWithMatch(BaseModel):
    """Search result with person data and match explanation"""
    
    person: SearchResultPerson
    match_explanation: MatchExplanation


class AdvancedSearchResponse(BaseModel):
    """Response model for advanced search"""
    
    success: bool = True
    results: List[SearchResultWithMatch]
    pagination: Dict[str, int]
    filters_applied: Dict[str, Any]
    total_results: int
    search_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "results": [
                    {
                        "person": {
                            "person_id": "123e4567-e89b-12d3-a456-426614174000",
                            "full_name": "Jane Doe",
                            "headline": "Senior Engineer at Uniswap",
                            "current_company": "Uniswap",
                            "has_github": True
                        },
                        "match_explanation": {
                            "matched_technologies": ["Solidity", "TypeScript"],
                            "matched_companies": ["Uniswap"],
                            "relevance_score": 95.0,
                            "match_summary": "Contributes to Solidity, TypeScript | Worked at Uniswap"
                        }
                    }
                ],
                "pagination": {"offset": 0, "limit": 50, "total": 127},
                "filters_applied": {"technologies": ["Solidity"], "companies": ["Uniswap"]},
                "total_results": 127,
                "search_time_ms": 145.3
            }
        }


class ParsedJobDescription(BaseModel):
    """Parsed job description with extracted requirements"""
    
    technologies: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    job_level: Optional[str] = None  # Junior, Mid, Senior, Staff, Principal
    domain_expertise: List[str] = Field(default_factory=list)
    min_experience_years: Optional[int] = None
    location: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    
    # Original text
    original_jd: str = ""
    
    # Confidence in extraction
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "technologies": ["Rust", "Solidity"],
                "companies": ["Jump Trading", "Wintermute", "Paradigm"],
                "job_level": "Senior",
                "domain_expertise": ["DeFi", "trading systems"],
                "min_experience_years": 5,
                "keywords": ["protocol development", "smart contracts"],
                "extraction_confidence": 0.92
            }
        }


class JobDescriptionParseRequest(BaseModel):
    """Request to parse a job description"""
    
    jd_text: str = Field(..., min_length=50, description="Full job description text")
    auto_search: bool = Field(
        default=False,
        description="If true, automatically execute search with parsed criteria"
    )


class JobDescriptionParseResponse(BaseModel):
    """Response from job description parsing"""
    
    success: bool = True
    parsed_jd: ParsedJobDescription
    search_request: Optional[AdvancedSearchRequest] = None
    search_results: Optional[AdvancedSearchResponse] = None
    parse_time_ms: float


class TechnologyListResponse(BaseModel):
    """Response with available technologies"""
    
    success: bool = True
    technologies: List[Dict[str, Any]]  # [{"name": "Rust", "count": 1234}, ...]
    total_technologies: int


class CompanyAutocompleteResponse(BaseModel):
    """Response for company name autocomplete"""
    
    success: bool = True
    companies: List[Dict[str, Any]]  # [{"company_id": "...", "company_name": "...", "employee_count": 45}, ...]
    total_matches: int

