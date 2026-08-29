"""Node data models - stub for initial setup."""
from sqlalchemy import Column, String, DateTime, Float, Integer, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from database import Base


class NodeStatus(str, enum.Enum):
    """Node status enum."""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class Node(Base):
    """Node model - to be fully implemented in task #3."""
    __tablename__ = "nodes"
    
    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, nullable=False)
    status = Column(SQLEnum(NodeStatus), default=NodeStatus.AVAILABLE)
    reliability_score = Column(Float, default=1.0)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
