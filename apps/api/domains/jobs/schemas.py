"""Job Pydantic schemas for API validation."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

from domains.jobs.models import JobStatus


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    customer_id: str
    workload_type: str
    parameters: Dict[str, Any]
    budget_clstr: Decimal = Field(gt=0)


class JobUpdate(BaseModel):
    """Schema for updating job status."""
    status: Optional[JobStatus] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_cost_clstr: Optional[Decimal] = None
    error_message: Optional[str] = None


class JobResponse(BaseModel):
    """Schema for job response."""
    job_id: str
    customer_id: str
    workload_type: str
    status: JobStatus
    parameters: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    budget_clstr: Decimal
    total_cost_clstr: Optional[Decimal] = None
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress_percentage: float
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for list of jobs."""
    jobs: list[JobResponse]
    total: int
