"""
GitHub Ingestion API Router
Endpoints for adding individual GitHub users or organizations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uuid
import logging

from api.dependencies import get_db
from api.services.github_ingestion_service import GitHubIngestionService

router = APIRouter(prefix="/api/github/ingest", tags=["github-ingestion"])
logger = logging.getLogger(__name__)

# In-memory job tracking (for MVP, move to Redis/DB later)
ingestion_jobs = {}


class GitHubUserRequest(BaseModel):
    """Request to ingest a GitHub user"""
    username: str = Field(..., description="GitHub username")


class GitHubOrgRequest(BaseModel):
    """Request to ingest a GitHub organization"""
    org_name: str = Field(..., description="GitHub organization name")


class IngestionJobResponse(BaseModel):
    """Response with job ID for tracking"""
    job_id: str
    status: str
    message: str


class IngestionStatusResponse(BaseModel):
    """Response with job status and results"""
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


def run_user_ingestion(job_id: str, username: str, db):
    """Background task to ingest GitHub user"""
    try:
        ingestion_jobs[job_id]['status'] = 'running'
        ingestion_jobs[job_id]['progress'] = f'Fetching data for {username}...'
        
        service = GitHubIngestionService(db)
        result = service.ingest_user(username)
        
        if result['success']:
            ingestion_jobs[job_id]['status'] = 'completed'
            ingestion_jobs[job_id]['result'] = result
        else:
            ingestion_jobs[job_id]['status'] = 'failed'
            ingestion_jobs[job_id]['error'] = result.get('error', 'Unknown error')
            
    except Exception as e:
        logger.error(f"Error in user ingestion job {job_id}: {str(e)}")
        ingestion_jobs[job_id]['status'] = 'failed'
        ingestion_jobs[job_id]['error'] = str(e)
    finally:
        db.close()


def run_org_ingestion(job_id: str, org_name: str, db):
    """Background task to ingest GitHub organization"""
    try:
        ingestion_jobs[job_id]['status'] = 'running'
        ingestion_jobs[job_id]['progress'] = f'Fetching members and repos for {org_name}...'
        
        service = GitHubIngestionService(db)
        result = service.ingest_organization(org_name)
        
        if result['success']:
            ingestion_jobs[job_id]['status'] = 'completed'
            ingestion_jobs[job_id]['result'] = result
        else:
            ingestion_jobs[job_id]['status'] = 'failed'
            ingestion_jobs[job_id]['error'] = result.get('error', 'Unknown error')
            
    except Exception as e:
        logger.error(f"Error in org ingestion job {job_id}: {str(e)}")
        ingestion_jobs[job_id]['status'] = 'failed'
        ingestion_jobs[job_id]['error'] = str(e)
    finally:
        db.close()


@router.post("/user/{username}", response_model=IngestionJobResponse)
async def ingest_github_user(
    username: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Ingest a single GitHub user
    
    - Fetches user data from GitHub API
    - Matches with existing profiles or creates new one
    - Imports user's repositories and contributions
    - Returns job ID for tracking progress
    """
    try:
        # Create job
        job_id = str(uuid.uuid4())
        ingestion_jobs[job_id] = {
            'status': 'pending',
            'type': 'user',
            'username': username,
            'created_at': str(uuid.uuid4())  # Placeholder for timestamp
        }
        
        # Start background task
        background_tasks.add_task(run_user_ingestion, job_id, username, db)
        
        return {
            'job_id': job_id,
            'status': 'pending',
            'message': f'Started ingestion for GitHub user: {username}'
        }
        
    except Exception as e:
        logger.error(f"Error starting user ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/org/{org_name}", response_model=IngestionJobResponse)
async def ingest_github_org(
    org_name: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Ingest an entire GitHub organization
    
    - Fetches all organization members
    - Fetches all organization repositories
    - Processes each member and repository
    - Returns job ID for tracking progress
    
    Note: Large organizations may take several minutes
    """
    try:
        # Create job
        job_id = str(uuid.uuid4())
        ingestion_jobs[job_id] = {
            'status': 'pending',
            'type': 'organization',
            'org_name': org_name,
            'created_at': str(uuid.uuid4())  # Placeholder for timestamp
        }
        
        # Start background task
        background_tasks.add_task(run_org_ingestion, job_id, org_name, db)
        
        return {
            'job_id': job_id,
            'status': 'pending',
            'message': f'Started ingestion for GitHub organization: {org_name}'
        }
        
    except Exception as e:
        logger.error(f"Error starting org ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(job_id: str):
    """
    Check status of an ingestion job
    
    Returns:
    - status: 'pending', 'running', 'completed', or 'failed'
    - progress: Current progress message (if running)
    - result: Final results (if completed)
    - error: Error message (if failed)
    """
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = ingestion_jobs[job_id]
    
    return {
        'job_id': job_id,
        'status': job['status'],
        'progress': job.get('progress'),
        'result': job.get('result'),
        'error': job.get('error')
    }


@router.get("/jobs")
async def list_ingestion_jobs():
    """List all ingestion jobs (for debugging)"""
    return {
        'total_jobs': len(ingestion_jobs),
        'jobs': [
            {
                'job_id': job_id,
                'status': job['status'],
                'type': job['type'],
                'name': job.get('username') or job.get('org_name')
            }
            for job_id, job in list(ingestion_jobs.items())[-20:]  # Last 20 jobs
        ]
    }

