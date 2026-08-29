"""Job data models."""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class JobStatus(str, enum.Enum):
    """
    Job status lifecycle with explicit state machine.
    
    SUBMITTED → ANALYZING → SCHEDULING → ALLOCATED → RUNNING → COMPLETED
                                                              ↓
                                                          RECOVERING → RUNNING
                                                              ↓
                                                           FAILED
    
    CANCELLED can be reached from most states.
    """
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    SCHEDULING = "scheduling"
    ALLOCATED = "allocated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"
    CANCELLED = "cancelled"


JOB_TRANSITIONS = {
    JobStatus.SUBMITTED: [JobStatus.ANALYZING, JobStatus.CANCELLED],
    JobStatus.ANALYZING: [JobStatus.SCHEDULING, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.SCHEDULING: [JobStatus.ALLOCATED, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.ALLOCATED: [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.RUNNING: [JobStatus.COMPLETED, JobStatus.RECOVERING, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.RECOVERING: [JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED],
    JobStatus.COMPLETED: [],
    JobStatus.FAILED: [],
    JobStatus.CANCELLED: [],
}


class Job(Base):
    """
    Customer-submitted work request.
    
    Represents complete workload distributed across nodes.
    Example: Render 100 frames at 1920x1080.
    """
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False, index=True)
    workload_type = Column(String, ForeignKey("workload_types.workload_type"), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.SUBMITTED, index=True)
    
    parameters = Column(JSON, nullable=False)
    
    ai_analysis = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    budget_clstr = Column(Numeric(10, 2), nullable=False)
    total_cost_clstr = Column(Numeric(10, 2), nullable=True)
    
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    
    workload = relationship("WorkloadType", back_populates="jobs")
    tasks = relationship("Task", back_populates="job", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="job")
    
    @property
    def progress_percentage(self) -> float:
        """Calculate job completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    def can_transition_to(self, new_status: JobStatus) -> bool:
        """Check if transition to new status is valid."""
        return new_status in JOB_TRANSITIONS.get(self.status, [])
    
    def is_terminal(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
