"""Reliability Pydantic schemas for API validation."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ReliabilityScoreResponse(BaseModel):
    """Schema for reliability score response."""
    node_id: str
    reliability_score: float
    tasks_completed: int
    tasks_failed: int
    tasks_reassigned: int
    recovery_assists: int
    total_incidents: int
    heartbeat_timeouts: int
    task_timeouts: int
    crashes: int
    average_task_duration_seconds: Optional[float]
    total_uptime_seconds: int
    total_downtime_seconds: int
    last_calculated_at: datetime
    last_incident_at: Optional[datetime]
    success_rate: float
    uptime_percentage: float
    
    class Config:
        from_attributes = True


class ReliabilityUpdate(BaseModel):
    """Schema for updating reliability metrics."""
    tasks_completed: Optional[int] = None
    tasks_failed: Optional[int] = None
    reliability_score: Optional[float] = None
