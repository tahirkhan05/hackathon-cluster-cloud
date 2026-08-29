"""Task data models - stub for initial setup."""
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from database import Base


class TaskStatus(str, enum.Enum):
    """Task status enum."""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base):
    """Task model - to be fully implemented in task #3."""
    __tablename__ = "tasks"
    
    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    node_id = Column(String, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.utcnow)
