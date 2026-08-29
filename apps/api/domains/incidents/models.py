"""Incident data models - stub for initial setup."""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from database import Base


class IncidentType(str, enum.Enum):
    """Incident type enum."""
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    TASK_TIMEOUT = "task_timeout"
    NODE_CRASH = "node_crash"


class IncidentStatus(str, enum.Enum):
    """Incident status enum."""
    DETECTED = "detected"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class Incident(Base):
    """Incident model - to be fully implemented in task #3."""
    __tablename__ = "incidents"
    
    incident_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    task_id = Column(String, nullable=True)
    node_id = Column(String, nullable=False)
    incident_type = Column(SQLEnum(IncidentType), nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.DETECTED)
    detected_at = Column(DateTime, default=datetime.utcnow)
