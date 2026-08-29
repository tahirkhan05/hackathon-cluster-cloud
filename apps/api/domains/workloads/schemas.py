"""Workload Pydantic schemas for API validation."""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class WorkloadTypeResponse(BaseModel):
    """Schema for workload type response."""
    workload_type: str
    name: str
    parallelizable: bool
    description: Optional[str]
    resource_requirements: Optional[Dict[str, Any]]
    estimated_task_duration: Optional[int]
    
    class Config:
        from_attributes = True


class WorkloadTypeListResponse(BaseModel):
    """Schema for list of workload types."""
    workload_types: list[WorkloadTypeResponse]
