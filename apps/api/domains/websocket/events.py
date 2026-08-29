"""
WebSocket event models and types.

All real-time events are typed and follow a consistent format.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class EventType(str, Enum):
    """Real-time event types."""
    NODE_JOINED = "node_joined"
    NODE_HEARTBEAT = "node_heartbeat"
    NODE_SELECTED = "node_selected"
    NODE_FAILED = "node_failed"
    
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    RECOVERY_STARTED = "recovery_started"
    REPLACEMENT_SELECTED = "replacement_selected"
    RECOVERY_COMPLETED = "recovery_completed"
    
    LEDGER_TRANSACTION = "ledger_transaction"
    
    SYSTEM_STATUS = "system_status"
    CONNECTION_ESTABLISHED = "connection_established"


class BaseEvent(BaseModel):
    """Base event structure."""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, event_type: EventType, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Factory method for creating events."""
        return cls(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            metadata=metadata or {}
        )


class EventFactory:
    """Factory for creating typed events."""
    
    @staticmethod
    def node_joined(node_id: str, name: str, cpu_cores: int, total_ram_gb: float, gpu_info: Optional[str] = None):
        """Node registered and joined the network."""
        return BaseEvent.create(
            event_type=EventType.NODE_JOINED,
            data={
                "node_id": node_id,
                "name": name,
                "cpu_cores": cpu_cores,
                "total_ram_gb": total_ram_gb,
                "gpu_info": gpu_info,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def node_heartbeat(node_id: str, status: str):
        """Node heartbeat received."""
        return BaseEvent.create(
            event_type=EventType.NODE_HEARTBEAT,
            data={
                "node_id": node_id,
                "status": status,
            },
            metadata={"severity": "debug"}
        )
    
    @staticmethod
    def node_selected(node_id: str, job_id: str, reason: str):
        """Node selected for task assignment."""
        return BaseEvent.create(
            event_type=EventType.NODE_SELECTED,
            data={
                "node_id": node_id,
                "job_id": job_id,
                "reason": reason,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def node_failed(node_id: str, incident_id: str, reason: str):
        """Node failure detected."""
        return BaseEvent.create(
            event_type=EventType.NODE_FAILED,
            data={
                "node_id": node_id,
                "incident_id": incident_id,
                "reason": reason,
            },
            metadata={"severity": "error"}
        )
    
    @staticmethod
    def job_started(job_id: str, workload_type: str, total_frames: int, budget: float):
        """Job started execution."""
        return BaseEvent.create(
            event_type=EventType.JOB_STARTED,
            data={
                "job_id": job_id,
                "workload_type": workload_type,
                "total_frames": total_frames,
                "budget_clstr": budget,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def job_completed(job_id: str, completed_frames: int, total_cost: float):
        """Job completed successfully."""
        return BaseEvent.create(
            event_type=EventType.JOB_COMPLETED,
            data={
                "job_id": job_id,
                "completed_frames": completed_frames,
                "total_cost_clstr": total_cost,
            },
            metadata={"severity": "success"}
        )
    
    @staticmethod
    def task_assigned(task_id: str, job_id: str, node_id: str, frame_number: int):
        """Task assigned to node."""
        return BaseEvent.create(
            event_type=EventType.TASK_ASSIGNED,
            data={
                "task_id": task_id,
                "job_id": job_id,
                "node_id": node_id,
                "frame_number": frame_number,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def task_started(task_id: str, job_id: str, node_id: str):
        """Task execution started."""
        return BaseEvent.create(
            event_type=EventType.TASK_STARTED,
            data={
                "task_id": task_id,
                "job_id": job_id,
                "node_id": node_id,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def task_completed(task_id: str, job_id: str, node_id: str, duration_seconds: float):
        """Task completed successfully."""
        return BaseEvent.create(
            event_type=EventType.TASK_COMPLETED,
            data={
                "task_id": task_id,
                "job_id": job_id,
                "node_id": node_id,
                "duration_seconds": duration_seconds,
            },
            metadata={"severity": "success"}
        )
    
    @staticmethod
    def task_failed(task_id: str, job_id: str, node_id: str, error: str):
        """Task failed."""
        return BaseEvent.create(
            event_type=EventType.TASK_FAILED,
            data={
                "task_id": task_id,
                "job_id": job_id,
                "node_id": node_id,
                "error": error,
            },
            metadata={"severity": "error"}
        )
    
    @staticmethod
    def recovery_started(incident_id: str, job_id: str, affected_task_count: int):
        """Recovery process started."""
        return BaseEvent.create(
            event_type=EventType.RECOVERY_STARTED,
            data={
                "incident_id": incident_id,
                "job_id": job_id,
                "affected_task_count": affected_task_count,
            },
            metadata={"severity": "warning"}
        )
    
    @staticmethod
    def replacement_selected(incident_id: str, replacement_node_id: str, reason: str):
        """Replacement node selected for recovery."""
        return BaseEvent.create(
            event_type=EventType.REPLACEMENT_SELECTED,
            data={
                "incident_id": incident_id,
                "replacement_node_id": replacement_node_id,
                "reason": reason,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def recovery_completed(incident_id: str, recovered_task_count: int):
        """Recovery completed successfully."""
        return BaseEvent.create(
            event_type=EventType.RECOVERY_COMPLETED,
            data={
                "incident_id": incident_id,
                "recovered_task_count": recovered_task_count,
            },
            metadata={"severity": "success"}
        )
    
    @staticmethod
    def ledger_transaction(
        transaction_id: str,
        transaction_type: str,
        from_account: str,
        to_account: str,
        amount: float,
        related_entity_id: Optional[str] = None
    ):
        """Economic ledger transaction."""
        return BaseEvent.create(
            event_type=EventType.LEDGER_TRANSACTION,
            data={
                "transaction_id": transaction_id,
                "transaction_type": transaction_type,
                "from_account": from_account,
                "to_account": to_account,
                "amount_clstr": amount,
                "related_entity_id": related_entity_id,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def system_status(
        total_nodes: int,
        healthy_nodes: int,
        active_jobs: int,
        tasks_in_progress: int
    ):
        """System status snapshot."""
        return BaseEvent.create(
            event_type=EventType.SYSTEM_STATUS,
            data={
                "total_nodes": total_nodes,
                "healthy_nodes": healthy_nodes,
                "active_jobs": active_jobs,
                "tasks_in_progress": tasks_in_progress,
            },
            metadata={"severity": "info"}
        )
    
    @staticmethod
    def connection_established(client_id: str):
        """WebSocket connection established."""
        return BaseEvent.create(
            event_type=EventType.CONNECTION_ESTABLISHED,
            data={
                "client_id": client_id,
                "message": "Connected to ClusterCloud real-time events",
            },
            metadata={"severity": "info"}
        )
