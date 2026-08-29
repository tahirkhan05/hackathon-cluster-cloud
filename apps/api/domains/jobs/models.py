"""Job data models - stub for initial setup."""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from database import Base


class JobStatus(str, enum.Enum):
    """Job status enum."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Job model - to be fully implemented in task #3."""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    workload_type = Column(String, nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
