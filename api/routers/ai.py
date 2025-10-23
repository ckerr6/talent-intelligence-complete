"""
AI-powered insights API endpoints

Provides AI analysis and Q&A for candidate profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from psycopg2.extras import RealDictCursor
import logging

from api.dependencies import get_db
from api.services.ai_service import get_ai_service, AIService

router = APIRouter(prefix="/api/ai", tags=["ai"])
logger = logging.getLogger(__name__)


# Request/Response Models
class ProfileSummaryRequest(BaseModel):
    """Request for profile summary generation."""
    person_id: str
    job_context: Optional[str] = Field(None, description="Optional job description or role context")
    provider: str = Field("openai", description="AI provider: 'openai' or 'anthropic'")
    model: Optional[str] = Field(None, description="Specific model (optional)")


class CodeAnalysisRequest(BaseModel):
    """Request for code quality analysis."""
    person_id: str
    job_requirements: Optional[str] = Field(None, description="Optional job requirements")
    provider: str = Field("openai", description="AI provider: 'openai' or 'anthropic'")
    model: Optional[str] = Field(None, description="Specific model (optional)")


class QuestionRequest(BaseModel):
    """Request for answering a question about a candidate."""
    person_id: str
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous Q&A")
    provider: str = Field("openai", description="AI provider: 'openai' or 'anthropic'")
    model: Optional[str] = Field(None, description="Specific model (optional)")


def _fetch_candidate_data(person_id: str, db) -> Dict[str, Any]:
    """Fetch all candidate data for AI analysis."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get person
        cursor.execute(
            "SELECT * FROM person WHERE person_id = %s",
            (person_id,)
        )
        person = cursor.fetchone()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Get employment
        cursor.execute(
            """
            SELECT e.*, c.company_name
            FROM employment e
            LEFT JOIN company c ON e.company_id = c.company_id
            WHERE e.person_id = %s
            ORDER BY 
                CASE WHEN e.end_date IS NULL THEN 0 ELSE 1 END,
                COALESCE(e.end_date, CURRENT_DATE) DESC,
                e.start_date DESC
            """,
            (person_id,)
        )
        employment = cursor.fetchall()
        
        # Get emails
        cursor.execute(
            "SELECT * FROM person_email WHERE person_id = %s",
            (person_id,)
        )
        emails = cursor.fetchall()
        
        # Get GitHub profile
        cursor.execute(
            "SELECT * FROM github_profile WHERE person_id = %s",
            (person_id,)
        )
        github_profile = cursor.fetchone()
        
        # Get GitHub contributions
        contributions = []
        if github_profile:
            cursor.execute(
                """
                SELECT 
                    gc.contribution_count,
                    gc.last_contribution_date,
                    gr.repo_id,
                    gr.full_name as repo_full_name,
                    gr.repo_name,
                    gr.description,
                    gr.language,
                    gr.stars,
                    gr.forks,
                    gr.is_fork,
                    c.company_name as owner_company_name
                FROM github_contribution gc
                JOIN github_repository gr ON gc.repo_id = gr.repo_id
                LEFT JOIN company c ON gr.company_id = c.company_id
                WHERE gc.github_profile_id = %s
                ORDER BY gr.stars DESC, gc.contribution_count DESC
                LIMIT 20
                """,
                (github_profile['github_profile_id'],)
            )
            contributions = cursor.fetchall()
        
        cursor.close()
        
        return {
            "person": dict(person),
            "employment": [dict(e) for e in employment],
            "emails": [dict(e) for e in emails],
            "github_profile": dict(github_profile) if github_profile else None,
            "github_contributions": [dict(c) for c in contributions]
        }
        
    except Exception as e:
        cursor.close()
        logger.error(f"Error fetching candidate data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile-summary")
async def generate_profile_summary(
    request: ProfileSummaryRequest,
    db=Depends(get_db)
):
    """
    Generate an AI-powered profile summary for a candidate.
    
    Returns a recruiter-friendly summary including:
    - Executive summary
    - Key strengths
    - Technical domains
    - Ideal roles
    - Career trajectory
    - Standout projects
    """
    try:
        # Fetch candidate data
        candidate_data = _fetch_candidate_data(request.person_id, db)
        
        # Initialize AI service
        ai_service = get_ai_service(
            provider=request.provider,
            model=request.model
        )
        
        # Generate summary
        summary = ai_service.generate_profile_summary(
            candidate_data=candidate_data,
            job_context=request.job_context
        )
        
        return {
            "success": True,
            "person_id": request.person_id,
            "summary": summary
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating profile summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code-analysis")
async def analyze_code_quality(
    request: CodeAnalysisRequest,
    db=Depends(get_db)
):
    """
    Analyze a candidate's code quality and technical work.
    
    Returns:
    - Code quality assessment
    - Technical depth/level
    - Engineering style
    - Standout contributions
    - Languages and tools
    - Work complexity
    - Collaboration indicators
    - Relevance to role (if job requirements provided)
    """
    try:
        # Fetch candidate data
        candidate_data = _fetch_candidate_data(request.person_id, db)
        
        if not candidate_data.get("github_profile"):
            raise HTTPException(
                status_code=404,
                detail="No GitHub profile found for this candidate"
            )
        
        # Initialize AI service
        ai_service = get_ai_service(
            provider=request.provider,
            model=request.model
        )
        
        # Analyze code
        analysis = ai_service.analyze_code_quality(
            candidate_data=candidate_data,
            job_requirements=request.job_requirements
        )
        
        return {
            "success": True,
            "person_id": request.person_id,
            "analysis": analysis
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing code quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(
    request: QuestionRequest,
    db=Depends(get_db)
):
    """
    Ask a question about a candidate.
    
    Supports follow-up questions via conversation_history.
    
    Example questions:
    - "Would they be good for a senior backend role?"
    - "Do they have blockchain experience?"
    - "How do they compare to my current team at X company?"
    - "What's their management experience?"
    """
    try:
        # Fetch candidate data
        candidate_data = _fetch_candidate_data(request.person_id, db)
        
        # Initialize AI service
        ai_service = get_ai_service(
            provider=request.provider,
            model=request.model
        )
        
        # Get answer
        answer = ai_service.answer_question(
            candidate_data=candidate_data,
            question=request.question,
            conversation_history=request.conversation_history
        )
        
        return {
            "success": True,
            "person_id": request.person_id,
            "question": request.question,
            "answer": answer
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_ai_status():
    """
    Check AI service availability and configuration.
    """
    import os
    
    status = {
        "openai": {
            "available": bool(os.getenv("OPENAI_API_KEY")),
            "default_model": "gpt-4o-mini"
        },
        "anthropic": {
            "available": bool(os.getenv("ANTHROPIC_API_KEY")),
            "default_model": "claude-3-5-sonnet-20241022"
        }
    }
    
    return {
        "success": True,
        "providers": status
    }

