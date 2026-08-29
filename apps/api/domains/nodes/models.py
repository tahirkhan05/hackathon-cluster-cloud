"""Node data models."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Enum as SQLEnum, JSON, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class NodeStatus(str, enum.Enum):
    """Node availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class Node(Base):
    """
    Provider machine registered with control plane.
    
    Represents a compute resource that can execute tasks.
    Tracked capabilities, reliability, and economic state.
    """
    __tablename__ = "nodes"
    
    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, nullable=False, index=True)
    
    hostname = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    capabilities = Column(JSON, nullable=False)
    
    status = Column(SQLEnum(NodeStatus), default=NodeStatus.AVAILABLE, index=True)
    is_healthy = Column(Boolean, default=True)
    
    reliability_score = Column(Float, default=1.0)
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_failed = Column(Integer, default=0)
    total_recovery_assists = Column(Integer, default=0)
    
    last_heartbeat = Column(DateTime, default=datetime.utcnow, index=True)
    heartbeat_interval_seconds = Column(Integer, default=5)
    
    clstr_earned = Column(Numeric(10, 2), default=0)
    clstr_staked = Column(Numeric(10, 2), default=0)
    clstr_pending = Column(Numeric(10, 2), default=0)
    
    cost_per_task_clstr = Column(Numeric(10, 2), default=10)
    
    max_concurrent_tasks = Column(Integer, default=2)
    current_task_count = Column(Integer, default=0)
    
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="node")
    incidents = relationship("Incident", back_populates="node", foreign_keys="[Incident.node_id]")
    reliability = relationship("ReliabilityScore", back_populates="node", uselist=False)
    
    @property
    def is_available(self) -> bool:
        """Check if node can accept new tasks."""
        return (
            self.status == NodeStatus.AVAILABLE and
            self.is_healthy and
            self.current_task_count < self.max_concurrent_tasks
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        total = self.total_tasks_completed + self.total_tasks_failed
        if total == 0:
            return 1.0
        return self.total_tasks_completed / total
