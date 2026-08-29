"""Jobs API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from domains.jobs.models import JobStatus
from domains.jobs.schemas import JobCreate, JobResponse, JobListResponse
from domains.jobs.service import JobService

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=201)
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new job in SUBMITTED state.
    
    Validates workload type and creates initial job record + tasks.
    """
    try:
        # Create job
        job = JobService.create_job(db, job_data)
        
        # Create tasks based on workload parameters
        from domains.tasks.service import TaskService
        from domains.tasks.schemas import TaskCreate
        
        # Get frame count from parameters
        total_frames = job_data.parameters.get('total_frames', 10)
        frame_start = job_data.parameters.get('frame_range_start', 1)
        frame_end = job_data.parameters.get('frame_range_end', total_frames)
        
        # Create one task per frame
        tasks_created = 0
        for frame_num in range(frame_start, frame_end + 1):
            task_data = TaskCreate(
                job_id=job.job_id,
                task_number=frame_num,
                task_type=job.workload_type,
                parameters={
                    "frame_number": frame_num,
                    **job_data.parameters
                }
            )
            TaskService.create_task(db, task_data)
            tasks_created += 1
        
        # Update job with task count
        JobService.update_job_progress(db, job.job_id)
        
        # Refresh to get updated counts
        db.refresh(job)
        
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=JobListResponse)
def list_jobs(
    customer_id: Optional[str] = Query(None),
    status: Optional[JobStatus] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """
    List jobs with optional filtering.
    
    Query parameters:
    - customer_id: Filter by customer
    - status: Filter by job status
    - limit: Max results (default: 100)
    """
    jobs = JobService.list_jobs(db, customer_id=customer_id, status=status, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get detailed job information including progress."""
    job = JobService.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.post("/{job_id}/transition")
def transition_job(
    job_id: str,
    new_status: JobStatus,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Transition job to new status.
    
    Validates state machine transitions.
    """
    try:
        job = JobService.transition_job_status(db, job_id, new_status, error_message)
        return {"job_id": job.job_id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Cancel a job if not in terminal state."""
    try:
        job = JobService.cancel_job(db, job_id, reason)
        return {"job_id": job.job_id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/update-progress")
def update_job_progress(job_id: str, db: Session = Depends(get_db)):
    """Recalculate job progress from tasks."""
    try:
        job = JobService.update_job_progress(db, job_id)
        return {
            "job_id": job.job_id,
            "total_tasks": job.total_tasks,
            "completed_tasks": job.completed_tasks,
            "failed_tasks": job.failed_tasks,
            "progress_percentage": job.progress_percentage
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
