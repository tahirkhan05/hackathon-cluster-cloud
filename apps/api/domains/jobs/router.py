"""Jobs API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_jobs():
    """List all jobs."""
    return {"jobs": []}


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get job by ID."""
    return {"job_id": job_id, "status": "pending"}


@router.post("/")
async def create_job():
    """Create new job."""
    return {"message": "Job creation endpoint - to be implemented"}
