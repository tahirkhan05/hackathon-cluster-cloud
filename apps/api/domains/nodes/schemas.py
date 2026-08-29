"""Node Pydantic schemas for API validation."""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from domains.nodes.models import NodeStatus


class NodeRegister(BaseModel):
    """Schema for node registration."""
    provider_id: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    capabilities: Dict[str, Any]
    max_concurrent_tasks: int = 2
    cost_per_task_clstr: Decimal = 10


class NodeHeartbeat(BaseModel):
    """Schema for heartbeat update."""
    node_id: str
    current_task_count: int = 0
    is_healthy: bool = True


class NodeResponse(BaseModel):
    """Schema for node response."""
    node_id: str
    provider_id: str
    hostname: Optional[str]
    ip_address: Optional[str]
    capabilities: Dict[str, Any]
    status: NodeStatus
    is_healthy: bool
    reliability_score: float
    total_tasks_completed: int
    total_tasks_failed: int
    total_recovery_assists: int
    last_heartbeat: datetime
    heartbeat_interval_seconds: int
    clstr_earned: Decimal
    clstr_staked: Decimal
    max_concurrent_tasks: int
    current_task_count: int
    registered_at: datetime
    is_available: bool
    success_rate: float
    
    class Config:
        from_attributes = True


class NodeListResponse(BaseModel):
    """Schema for list of nodes."""
    nodes: list[NodeResponse]
    total: int
