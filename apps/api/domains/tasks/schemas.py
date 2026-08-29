"""Task Pydantic schemas for API validation."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from domains.tasks.models import TaskStatus


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    job_id: str
    task_number: int
    parameters: Dict[str, Any]
    max_retries: int = 3


class TaskAssignment(BaseModel):
    """Schema for task assignment to node."""
    task_id: str
    node_id: str


class TaskUpdate(BaseModel):
    """Schema for task status update."""
    status: Optional[TaskStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    result_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task response."""
    task_id: str
    job_id: str
    node_id: Optional[str]
    status: TaskStatus
    task_number: int
    parameters: Dict[str, Any]
    retry_count: int
    max_retries: int
    created_at: datetime
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_url: Optional[str]
    result_metadata: Optional[Dict[str, Any]]
    error_message: Optional[str]
    can_retry: bool
    duration_seconds: float
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for list of tasks."""
    tasks: list[TaskResponse]
    total: int
