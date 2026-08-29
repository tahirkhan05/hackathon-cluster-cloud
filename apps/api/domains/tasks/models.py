"""Task data models."""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class TaskStatus(str, enum.Enum):
    """Task status lifecycle."""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    """
    Individual unit of work assigned to a node.
    
    Example: Render frames 1-25 for job_id=xyz
    Tasks are idempotent and can be safely retried.
    """
    __tablename__ = "tasks"
    
    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=True, index=True)
    
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.QUEUED, index=True)
    
    # Task sequence number within job
    task_number = Column(Integer, nullable=False)
    
    # Task-specific parameters (frame_range, input_urls, output_format, etc.)
    parameters = Column(JSON, nullable=False)
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    result_url = Column(String, nullable=True)
    result_metadata = Column(JSON, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="tasks")
    node = relationship("Node", back_populates="tasks")
    incidents = relationship("Incident", back_populates="task")
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries
    
    @property
    def duration_seconds(self) -> float:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
