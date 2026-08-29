"""Task data models."""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class TaskStatus(str, enum.Enum):
    """
    Task status lifecycle with explicit state machine.
    
    PENDING → ASSIGNED → RUNNING → COMPLETED
                  ↓         ↓
                  └── FAILED → RETRYING → ASSIGNED
                       ↓
                    (max retries) → FAILED (terminal)
    """
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


TASK_TRANSITIONS = {
    TaskStatus.PENDING: [TaskStatus.ASSIGNED, TaskStatus.FAILED],
    TaskStatus.ASSIGNED: [TaskStatus.RUNNING, TaskStatus.FAILED],
    TaskStatus.RUNNING: [TaskStatus.COMPLETED, TaskStatus.FAILED],
    TaskStatus.FAILED: [TaskStatus.RETRYING],
    TaskStatus.RETRYING: [TaskStatus.ASSIGNED, TaskStatus.FAILED],
    TaskStatus.COMPLETED: [],
}


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
    
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    task_number = Column(Integer, nullable=False)
    
    parameters = Column(JSON, nullable=False)
    
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    result_url = Column(String, nullable=True)
    result_metadata = Column(JSON, nullable=True)
    
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
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
    
    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if transition to new status is valid."""
        if self.status == TaskStatus.FAILED and new_status == TaskStatus.RETRYING:
            return self.can_retry
        
        return new_status in TASK_TRANSITIONS.get(self.status, [])
    
    def is_terminal(self) -> bool:
        """Check if task is in terminal state."""
        return (self.status == TaskStatus.COMPLETED or 
                (self.status == TaskStatus.FAILED and not self.can_retry))
