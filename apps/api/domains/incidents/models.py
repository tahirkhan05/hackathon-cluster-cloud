"""Incident data models."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class IncidentType(str, enum.Enum):
    """Types of failure incidents."""
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    TASK_TIMEOUT = "task_timeout"
    NODE_CRASH = "node_crash"
    TASK_ERROR = "task_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class IncidentStatus(str, enum.Enum):
    """Incident resolution status."""
    DETECTED = "detected"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class Incident(Base):
    """
    Failure event record.
    
    Captures node failures, task timeouts, and other incidents
    that require recovery action. Used for reliability scoring
    and audit trail.
    """
    __tablename__ = "incidents"
    
    incident_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False, index=True)
    
    incident_type = Column(SQLEnum(IncidentType), nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.DETECTED, index=True)
    
    description = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)
    
    recovery_node_id = Column(String, ForeignKey("nodes.node_id"), nullable=True)
    recovery_strategy = Column(String, nullable=True)
    ai_recovery_recommendation = Column(JSON, nullable=True)
    
    affected_task_ids = Column(JSON, nullable=True)
    reassigned_task_count = Column(Integer, default=0)
    
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    recovery_started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    job = relationship("Job", back_populates="incidents")
    task = relationship("Task", back_populates="incidents")
    node = relationship("Node", back_populates="incidents", foreign_keys=[node_id])
    
    @property
    def recovery_duration_seconds(self) -> float:
        """Calculate time to resolve incident."""
        if self.recovery_started_at and self.resolved_at:
            return (self.resolved_at - self.recovery_started_at).total_seconds()
        return 0.0
    
    @property
    def is_resolved(self) -> bool:
        """Check if incident has been resolved."""
        return self.status == IncidentStatus.RESOLVED
