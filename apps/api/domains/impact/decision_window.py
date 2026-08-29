"""
Decision Window Calculator

Calculates time-sensitive decision windows for incidents.
Simple, transparent model for MVP demo.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from domains.incidents.models import Incident
from domains.nodes.models import Node
from domains.tasks.models import Task, TaskStatus

logger = logging.getLogger(__name__)


class DecisionWindow:
    """
    Calculates time-critical decision windows.
    
    Simple model based on:
    - Task timeout thresholds
    - Available replacement capacity
    - Deadline proximity
    """
    
    BASE_WINDOW_SECONDS = 120
    TASK_TIMEOUT_SECONDS = 180
    CAPACITY_FACTOR = 30
    DEADLINE_URGENCY_FACTOR = 0.5
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_for_node_failure(
        self,
        node_id: str,
        affected_task_ids: list[str]
    ) -> Dict[str, Any]:
        """
        Calculate decision window for node failure.
        
        Args:
            node_id: Failed node
            affected_task_ids: Tasks that need recovery
            
        Returns:
            Decision window details with urgency level
        """
        window_seconds = self.BASE_WINDOW_SECONDS
        
        task_count = len(affected_task_ids)
        if task_count > 10:
            window_seconds *= 0.7
        elif task_count > 5:
            window_seconds *= 0.85
        
        available_nodes = self._count_available_nodes(exclude_node_id=node_id)
        
        if available_nodes == 0:
            window_seconds *= 0.3
            urgency_reason = "No replacement nodes available"
        elif available_nodes < task_count:
            window_seconds *= 0.6
            urgency_reason = "Limited replacement capacity"
        else:
            urgency_reason = "Adequate replacement capacity available"
        
        deadline_risk = self._check_deadline_proximity(affected_task_ids)
        if deadline_risk:
            window_seconds *= self.DEADLINE_URGENCY_FACTOR
            urgency_reason = deadline_risk
        
        time_until_timeout = self.TASK_TIMEOUT_SECONDS
        if window_seconds > time_until_timeout * 0.7:
            window_seconds = time_until_timeout * 0.7
        
        if window_seconds < 60:
            urgency_level = "CRITICAL"
        elif window_seconds < 90:
            urgency_level = "HIGH"
        elif window_seconds < 180:
            urgency_level = "MEDIUM"
        else:
            urgency_level = "LOW"
        
        after_window_impact = self._calculate_post_window_impact(
            task_count,
            available_nodes
        )
        
        return {
            "decision_window_seconds": int(window_seconds),
            "urgency_level": urgency_level,
            "urgency_reason": urgency_reason,
            "factors": {
                "affected_tasks": task_count,
                "available_replacement_nodes": available_nodes,
                "time_until_task_timeout_seconds": time_until_timeout,
                "deadline_risk": bool(deadline_risk)
            },
            "after_window_impact": after_window_impact,
            "recommendation": "Immediate recovery recommended" if urgency_level in ["CRITICAL", "HIGH"] else "Evaluate recovery options"
        }
    
    def calculate_for_incident(self, incident: Incident) -> Dict[str, Any]:
        """Calculate decision window for existing incident."""
        if not incident.node_id:
            return {
                "decision_window_seconds": self.BASE_WINDOW_SECONDS,
                "urgency_level": "MEDIUM",
                "urgency_reason": "Non-node incident"
            }
        
        affected_task_ids = incident.metadata.get("incomplete_task_ids", []) if incident.metadata else []
        
        return self.calculate_for_node_failure(
            incident.node_id,
            affected_task_ids
        )
    
    def _count_available_nodes(self, exclude_node_id: Optional[str] = None) -> int:
        """Count available healthy nodes with capacity."""
        from domains.nodes.models import NodeStatus
        
        query = self.db.query(Node).filter(
            Node.status.in_([NodeStatus.HEALTHY, NodeStatus.AVAILABLE]),
            Node.is_healthy == True,
            Node.current_task_count < Node.max_concurrent_tasks
        )
        
        if exclude_node_id:
            query = query.filter(Node.node_id != exclude_node_id)
        
        return query.count()
    
    def _check_deadline_proximity(self, task_ids: list[str]) -> Optional[str]:
        """
        Check if any jobs are close to deadline.
        
        Returns urgency reason if deadline close, None otherwise.
        """
        if not task_ids:
            return None
        
        tasks = self.db.query(Task).filter(Task.task_id.in_(task_ids)).all()
        
        from domains.jobs.models import Job
        job_ids = list(set(t.job_id for t in tasks))
        jobs = self.db.query(Job).filter(Job.job_id.in_(job_ids)).all()
        
        for job in jobs:
            if not job.parameters or not job.created_at:
                continue
            
            deadline_minutes = job.parameters.get("deadline_minutes")
            if not deadline_minutes:
                continue
            
            elapsed = (datetime.utcnow() - job.created_at).total_seconds() / 60.0
            remaining = deadline_minutes - elapsed
            
            if remaining < deadline_minutes * 0.2:
                return f"Job deadline in {int(remaining)} minutes"
        
        return None
    
    def _calculate_post_window_impact(
        self,
        task_count: int,
        available_nodes: int
    ) -> Dict[str, Any]:
        """Calculate expected impact if decision window expires."""
        if available_nodes == 0:
            return {
                "expected_impact": "SEVERE",
                "description": "Tasks will timeout. Manual intervention required.",
                "estimated_additional_delay_minutes": task_count * 10,
                "recovery_difficulty": "HIGH"
            }
        elif available_nodes < task_count:
            return {
                "expected_impact": "HIGH",
                "description": "Partial capacity available. Extended recovery time.",
                "estimated_additional_delay_minutes": task_count * 5,
                "recovery_difficulty": "MEDIUM"
            }
        else:
            return {
                "expected_impact": "MEDIUM",
                "description": "Recovery still possible but with increased cost.",
                "estimated_additional_delay_minutes": task_count * 2,
                "recovery_difficulty": "LOW"
            }
