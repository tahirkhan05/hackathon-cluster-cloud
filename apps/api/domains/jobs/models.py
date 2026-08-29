"""Job data models."""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class JobStatus(str, enum.Enum):
    """Job status lifecycle."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """
    Customer-submitted work request.
    
    Represents a complete workload to be distributed across nodes.
    Example: Render 100 frames at 1920x1080 resolution.
    """
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False, index=True)
    workload_type = Column(String, ForeignKey("workload_types.workload_type"), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    
    # Job-specific parameters (frame_count, resolution, quality, input_url, etc.)
    parameters = Column(JSON, nullable=False)
    
    # AI analysis result
    ai_analysis = Column(JSON, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Economics
    budget_clstr = Column(Numeric(10, 2), nullable=False)
    total_cost_clstr = Column(Numeric(10, 2), nullable=True)
    
    # Progress tracking
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    # Relationships
    workload = relationship("WorkloadType", back_populates="jobs")
    tasks = relationship("Task", back_populates="job", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="job")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate job progress percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
