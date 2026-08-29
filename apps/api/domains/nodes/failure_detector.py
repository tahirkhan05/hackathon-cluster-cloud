"""
Failure Detection Service

Detects node failures based on heartbeat timeouts.
Creates incidents and marks nodes as unavailable.
Idempotent and deterministic.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging
from sqlalchemy.orm import Session

from domains.nodes.models import Node, NodeStatus
from domains.tasks.models import Task, TaskStatus
from domains.incidents.models import Incident, IncidentType, IncidentStatus

logger = logging.getLogger(__name__)


class FailureDetector:
    """
    Detects and handles node failures.
    
    Criteria for failure:
    - No heartbeat within timeout threshold
    - Previous status was AVAILABLE or BUSY
    
    Actions on failure:
    - Mark node as OFFLINE
    - Mark node as unhealthy
    - Identify incomplete tasks
    - Create failure incident (idempotent)
    """
    
    HEARTBEAT_TIMEOUT_SECONDS = 30
    
    RECOVERY_GRACE_PERIOD_SECONDS = 10
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_failed_nodes(self) -> List[Tuple[Node, List[Task]]]:
        """
        Detect all nodes that have failed based on heartbeat timeout.
        
        Returns:
            List of (node, incomplete_tasks) tuples
        """
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=self.HEARTBEAT_TIMEOUT_SECONDS)
        
        failed_nodes = self.db.query(Node).filter(
            Node.last_heartbeat_at < timeout_threshold,
            Node.status.in_([NodeStatus.AVAILABLE, NodeStatus.BUSY])
        ).all()
        
        results = []
        
        for node in failed_nodes:
            logger.warning(
                f"Node failure detected: {node.node_id} "
                f"(last heartbeat: {node.last_heartbeat_at}, threshold: {timeout_threshold})"
            )
            
            incomplete_tasks = self._get_incomplete_tasks(node.node_id)
            
            results.append((node, incomplete_tasks))
        
        return results
    
    def mark_node_failed(
        self,
        node: Node,
        incomplete_tasks: List[Task],
        reason: str = "Heartbeat timeout"
    ) -> Incident:
        """
        Mark a node as failed and create incident.
        
        Idempotent: If incident already exists for this node failure, returns it.
        
        Returns:
            Incident record
        """
        existing_incident = self.db.query(Incident).filter(
            Incident.node_id == node.node_id,
            Incident.status == IncidentStatus.OPEN,
            Incident.incident_type == "node_failure"
        ).first()
        
        if existing_incident:
            logger.info(f"Incident already exists for node {node.node_id}: {existing_incident.incident_id}")
            return existing_incident
        
        old_status = node.status
        node.status = NodeStatus.OFFLINE
        node.is_healthy = False
        node.failure_count += 1
        
        incident = Incident(
            incident_type=IncidentType.HEARTBEAT_TIMEOUT,
            description=f"Node {node.node_id} ({node.provider_id}) failed: {reason}",
            node_id=node.node_id,
            context={
                "previous_status": old_status.value,
                "last_heartbeat": node.last_heartbeat_at.isoformat() if node.last_heartbeat_at else None,
                "incomplete_task_count": len(incomplete_tasks),
                "incomplete_task_ids": [t.task_id for t in incomplete_tasks],
                "failure_count": node.failure_count,
                "reason": reason
            }
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        self.db.refresh(node)
        
        logger.error(
            f"Node {node.node_id} marked as FAILED: {old_status} → OFFLINE "
            f"({len(incomplete_tasks)} incomplete tasks, incident: {incident.incident_id})"
        )
        
        return incident
    
    def detect_recovered_nodes(self) -> List[Node]:
        """
        Detect nodes that have recovered (heartbeat resumed).
        
        Only considers nodes that:
        - Are currently OFFLINE
        - Have recent heartbeat (within grace period)
        
        Returns:
            List of recovered nodes
        """
        now = datetime.utcnow()
        recovery_threshold = now - timedelta(seconds=self.RECOVERY_GRACE_PERIOD_SECONDS)
        
        recovered_nodes = self.db.query(Node).filter(
            Node.status == NodeStatus.OFFLINE,
            Node.last_heartbeat_at >= recovery_threshold
        ).all()
        
        return recovered_nodes
    
    def mark_node_recovered(self, node: Node) -> Optional[Incident]:
        """
        Mark a node as recovered.
        
        Updates node status and closes incident.
        Idempotent: Safe to call multiple times.
        
        Returns:
            Closed incident, or None if no incident found
        """
        incident = self.db.query(Incident).filter(
            Incident.node_id == node.node_id,
            Incident.status == IncidentStatus.OPEN,
            Incident.incident_type == "node_failure"
        ).first()
        
        old_status = node.status
        node.status = NodeStatus.AVAILABLE
        node.is_healthy = True
        
        if incident:
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.utcnow()
            incident.resolution = f"Node recovered, heartbeat resumed"
        
        self.db.commit()
        self.db.refresh(node)
        
        logger.info(
            f"Node {node.node_id} recovered: {old_status} → AVAILABLE "
            f"(incident: {incident.incident_id if incident else 'none'})"
        )
        
        return incident
    
    def _get_incomplete_tasks(self, node_id: str) -> List[Task]:
        """
        Get all incomplete tasks assigned to a node.
        
        Incomplete = ASSIGNED or RUNNING status
        """
        return self.db.query(Task).filter(
            Task.node_id == node_id,
            Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING])
        ).all()
    
    def check_for_stale_tasks(self, task_timeout_seconds: int = 300) -> List[Task]:
        """
        Find tasks that have been running too long (zombie tasks).
        
        Args:
            task_timeout_seconds: Max time a task should run
            
        Returns:
            List of stale tasks
        """
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=task_timeout_seconds)
        
        stale_tasks = self.db.query(Task).filter(
            Task.status == TaskStatus.RUNNING,
            Task.started_at < timeout_threshold
        ).all()
        
        if stale_tasks:
            logger.warning(f"Found {len(stale_tasks)} stale tasks")
        
        return stale_tasks
    
    def create_stale_task_incident(self, task: Task) -> Incident:
        """
        Create incident for a stale task.
        
        Idempotent: Returns existing incident if found.
        """
        existing = self.db.query(Incident).filter(
            Incident.task_id == task.task_id,
            Incident.status == IncidentStatus.OPEN,
            Incident.incident_type == "task_timeout"
        ).first()
        
        if existing:
            return existing
        
        running_duration = (datetime.utcnow() - task.started_at).total_seconds() if task.started_at else 0
        
        incident = Incident(
            incident_type=IncidentType.TASK_TIMEOUT,
            description=f"Task {task.task_id} has been running for {running_duration:.0f}s (zombie task)",
            job_id=task.job_id,
            task_id=task.task_id,
            node_id=task.node_id,
            context={
                "task_number": task.task_number,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "running_duration_seconds": running_duration,
                "retry_count": task.retry_count
            }
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        
        logger.warning(f"Created stale task incident: {incident.incident_id}")
        
        return incident
    
    def run_detection_cycle(self) -> dict:
        """
        Run complete failure detection cycle.
        
        Detects failures, creates incidents, detects recoveries.
        Safe to run repeatedly (idempotent).
        
        Returns:
            Summary dict with counts
        """
        logger.info("Running failure detection cycle")
        
        failed_nodes = self.detect_failed_nodes()
        
        incidents_created = []
        for node, incomplete_tasks in failed_nodes:
            incident = self.mark_node_failed(node, incomplete_tasks)
            incidents_created.append(incident)
        
        recovered_nodes = self.detect_recovered_nodes()
        
        incidents_resolved = []
        for node in recovered_nodes:
            incident = self.mark_node_recovered(node)
            if incident:
                incidents_resolved.append(incident)
        
        stale_tasks = self.check_for_stale_tasks()
        
        stale_incidents = []
        for task in stale_tasks:
            incident = self.create_stale_task_incident(task)
            stale_incidents.append(incident)
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes_failed": len(failed_nodes),
            "nodes_recovered": len(recovered_nodes),
            "stale_tasks_detected": len(stale_tasks),
            "incidents_created": len(incidents_created),
            "incidents_resolved": len(incidents_resolved),
            "node_ids_failed": [node.node_id for node, _ in failed_nodes],
            "node_ids_recovered": [node.node_id for node in recovered_nodes],
            "incident_ids_created": [inc.incident_id for inc in incidents_created],
            "incident_ids_resolved": [inc.incident_id for inc in incidents_resolved if inc]
        }
        
        logger.info(
            f"Detection cycle complete: "
            f"{summary['nodes_failed']} failed, "
            f"{summary['nodes_recovered']} recovered, "
            f"{summary['stale_tasks_detected']} stale tasks"
        )
        
        return summary
