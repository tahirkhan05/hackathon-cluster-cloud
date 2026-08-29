"""Scheduling API router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from domains.scheduling.scheduler import ResourceScheduler, SchedulingRequirements
from domains.jobs.service import JobService

router = APIRouter()


class ScheduleRequest(BaseModel):
    """Request to schedule a job."""
    job_id: str
    cpu_cores_min: int = 2
    ram_gb_min: float = 4.0
    gpu_required: bool = False
    gpu_vram_gb_min: Optional[float] = None
    task_count: int
    estimated_task_duration_seconds: int = 60
    deadline_seconds: Optional[int] = None
    budget_clstr: float
    reliability_min: float = 0.7
    prefer_gpu: bool = False


@router.post("/schedule")
def schedule_job(request: ScheduleRequest, db: Session = Depends(get_db)):
    """
    Create resource allocation plan for job.
    
    Returns explicit plan with node assignments and audit trail.
    """
    job = JobService.get_job(db, request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    requirements = SchedulingRequirements(
        cpu_cores_min=request.cpu_cores_min,
        ram_gb_min=request.ram_gb_min,
        gpu_required=request.gpu_required,
        gpu_vram_gb_min=request.gpu_vram_gb_min,
        task_count=request.task_count,
        estimated_task_duration_seconds=request.estimated_task_duration_seconds,
        deadline_seconds=request.deadline_seconds,
        budget_clstr=request.budget_clstr,
        reliability_min=request.reliability_min,
        prefer_gpu=request.prefer_gpu
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    return plan.to_dict()


@router.post("/schedule-and-execute")
def schedule_and_execute(request: ScheduleRequest, db: Session = Depends(get_db)):
    """
    Schedule job and create tasks if feasible.
    
    Returns allocation plan and created tasks.
    """
    job = JobService.get_job(db, request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    requirements = SchedulingRequirements(
        cpu_cores_min=request.cpu_cores_min,
        ram_gb_min=request.ram_gb_min,
        gpu_required=request.gpu_required,
        gpu_vram_gb_min=request.gpu_vram_gb_min,
        task_count=request.task_count,
        estimated_task_duration_seconds=request.estimated_task_duration_seconds,
        deadline_seconds=request.deadline_seconds,
        budget_clstr=request.budget_clstr,
        reliability_min=request.reliability_min,
        prefer_gpu=request.prefer_gpu
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    if not plan.is_feasible:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Scheduling infeasible",
                "warnings": plan.warnings,
                "plan": plan.to_dict()
            }
        )
    
    tasks = scheduler.execute_allocation(
        plan,
        job,
        base_task_parameters=job.parameters
    )
    
    return {
        "plan": plan.to_dict(),
        "tasks_created": len(tasks),
        "task_ids": [t.task_id for t in tasks[:10]]  # First 10 for brevity
    }
