"""Incident Pydantic schemas for API validation."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from domains.incidents.models import IncidentType, IncidentStatus


class IncidentCreate(BaseModel):
    """Schema for creating an incident."""
    job_id: str
    task_id: Optional[str] = None
    node_id: str
    incident_type: IncidentType
    description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    affected_task_ids: Optional[List[str]] = None


class IncidentUpdate(BaseModel):
    """Schema for updating incident."""
    status: Optional[IncidentStatus] = None
    recovery_node_id: Optional[str] = None
    recovery_strategy: Optional[str] = None
    ai_recovery_recommendation: Optional[Dict[str, Any]] = None
    recovery_started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    reassigned_task_count: Optional[int] = None


class IncidentResponse(BaseModel):
    """Schema for incident response."""
    incident_id: str
    job_id: str
    task_id: Optional[str]
    node_id: str
    incident_type: IncidentType
    status: IncidentStatus
    description: Optional[str]
    context: Optional[Dict[str, Any]]
    recovery_node_id: Optional[str]
    recovery_strategy: Optional[str]
    ai_recovery_recommendation: Optional[Dict[str, Any]]
    affected_task_ids: Optional[List[str]]
    reassigned_task_count: int
    detected_at: datetime
    recovery_started_at: Optional[datetime]
    resolved_at: Optional[datetime]
    recovery_duration_seconds: float
    is_resolved: bool
    
    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    """Schema for list of incidents."""
    incidents: list[IncidentResponse]
    total: int
