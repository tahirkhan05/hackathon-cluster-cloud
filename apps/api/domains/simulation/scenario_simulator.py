"""
Counterfactual Scenario Simulator

Simulates future outcomes WITHOUT mutating production database.
Clones relevant state and runs deterministic projections.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from copy import deepcopy
from sqlalchemy.orm import Session
import logging

from domains.nodes.models import Node, NodeStatus
from domains.tasks.models import Task, TaskStatus
from domains.jobs.models import Job, JobStatus
from domains.incidents.models import Incident

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """Result of scenario simulation."""
    scenario_name: str
    estimated_completion_minutes: float
    affected_tasks_count: int
    affected_jobs_count: int
    deadline_breaches: int
    estimated_cost_clstr: float
    customer_impact_level: str
    timeline: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario": self.scenario_name,
            "estimated_completion_minutes": round(self.estimated_completion_minutes, 1),
            "affected_tasks_count": self.affected_tasks_count,
            "affected_jobs_count": self.affected_jobs_count,
            "deadline_breaches": self.deadline_breaches,
            "estimated_cost_clstr": round(self.estimated_cost_clstr, 2),
            "customer_impact_level": self.customer_impact_level,
            "timeline": self.timeline
        }


class ScenarioSimulator:
    """
    Simulates counterfactual scenarios.
    
    Creates in-memory state snapshots and projects outcomes
    WITHOUT touching production database.
    """
    
    AVG_TASK_MINUTES = 5.0
    AVG_RECOVERY_MINUTES = 2.0
    
    def __init__(self, db: Session):
        self.db = db
    
    def simulate_do_nothing(
        self,
        node_id: str,
        affected_task_ids: List[str]
    ) -> ScenarioResult:
        """
        Simulate doing nothing after node failure.
        
        Assumes tasks remain unassigned and eventually timeout.
        """
        timeline = []
        current_time = 0
        
        tasks = self._load_tasks_snapshot(affected_task_ids)
        jobs = self._load_jobs_for_tasks(tasks)
        
        timeline.append({
            "time_minutes": current_time,
            "event": "node_failure_detected",
            "description": f"Node {node_id} failed",
            "affected_tasks": len(tasks)
        })
        
        current_time += 5
        timeline.append({
            "time_minutes": current_time,
            "event": "tasks_timeout_warning",
            "description": f"{len(tasks)} tasks approaching timeout"
        })
        
        current_time += 9
        timeline.append({
            "time_minutes": current_time,
            "event": "job_delay_impact",
            "description": f"{len(jobs)} jobs experiencing delays"
        })
        
        deadline_breaches = 0
        for job in jobs.values():
            deadline_minutes = job.get("deadline_minutes")
            if deadline_minutes:
                elapsed = job.get("elapsed_minutes", 0)
                remaining = deadline_minutes - elapsed
                
                if current_time > remaining:
                    deadline_breaches += 1
        
        current_time += 5
        if deadline_breaches > 0:
            timeline.append({
                "time_minutes": current_time,
                "event": "deadline_breach",
                "description": f"{deadline_breaches} jobs missed deadline",
                "severity": "HIGH"
            })
        
        completion_time = current_time + (len(tasks) * self.AVG_TASK_MINUTES)
        
        timeline.append({
            "time_minutes": completion_time,
            "event": "eventual_timeout_recovery",
            "description": "Tasks eventually timeout and are recovered",
            "note": "Manual intervention likely required"
        })
        
        cost_impact = len(tasks) * 10.0 * 1.5
        
        return ScenarioResult(
            scenario_name="DO_NOTHING",
            estimated_completion_minutes=completion_time,
            affected_tasks_count=len(tasks),
            affected_jobs_count=len(jobs),
            deadline_breaches=deadline_breaches,
            estimated_cost_clstr=cost_impact,
            customer_impact_level="HIGH" if deadline_breaches > 0 else "MEDIUM",
            timeline=timeline
        )
    
    def simulate_recovery(
        self,
        node_id: str,
        affected_task_ids: List[str]
    ) -> ScenarioResult:
        """
        Simulate immediate recovery action.
        
        Assumes tasks are reassigned to healthy nodes immediately.
        """
        timeline = []
        current_time = 0
        
        tasks = self._load_tasks_snapshot(affected_task_ids)
        jobs = self._load_jobs_for_tasks(tasks)
        
        timeline.append({
            "time_minutes": current_time,
            "event": "node_failure_detected",
            "description": f"Node {node_id} failed",
            "affected_tasks": len(tasks)
        })
        
        current_time += 0.5
        timeline.append({
            "time_minutes": current_time,
            "event": "recovery_decision",
            "description": "AI recommends immediate recovery"
        })
        
        available_nodes = self._count_available_nodes(exclude_node_id=node_id)
        
        current_time += self.AVG_RECOVERY_MINUTES
        timeline.append({
            "time_minutes": current_time,
            "event": "replacement_found",
            "description": f"Found {min(available_nodes, len(tasks))} replacement nodes",
            "available_capacity": available_nodes
        })
        
        current_time += 1.0
        timeline.append({
            "time_minutes": current_time,
            "event": "tasks_reassigned",
            "description": f"{len(tasks)} tasks reassigned to healthy nodes"
        })
        
        current_time += 1.0
        timeline.append({
            "time_minutes": current_time,
            "event": "execution_resumed",
            "description": "Task execution resumed"
        })
        
        current_time += 2.0
        timeline.append({
            "time_minutes": current_time,
            "event": "cluster_stable",
            "description": "Cluster operating normally",
            "status": "HEALTHY"
        })
        
        deadline_breaches = 0
        for job in jobs.values():
            deadline_minutes = job.get("deadline_minutes")
            if deadline_minutes:
                elapsed = job.get("elapsed_minutes", 0)
                remaining = deadline_minutes - elapsed
                
                if current_time > remaining:
                    deadline_breaches += 1
        
        completion_time = current_time + 0.5
        
        cost_impact = len(tasks) * 10.0 * 1.1
        
        return ScenarioResult(
            scenario_name="RECOVER_NOW",
            estimated_completion_minutes=completion_time,
            affected_tasks_count=len(tasks),
            affected_jobs_count=len(jobs),
            deadline_breaches=deadline_breaches,
            estimated_cost_clstr=cost_impact,
            customer_impact_level="LOW" if deadline_breaches == 0 else "MEDIUM",
            timeline=timeline
        )
    
    def compare_scenarios(
        self,
        node_id: str,
        affected_task_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare DO_NOTHING vs RECOVER_NOW scenarios.
        
        Returns side-by-side comparison.
        """
        do_nothing = self.simulate_do_nothing(node_id, affected_task_ids)
        recover_now = self.simulate_recovery(node_id, affected_task_ids)
        
        return {
            "scenarios": {
                "do_nothing": do_nothing.to_dict(),
                "recover_now": recover_now.to_dict()
            },
            "comparison": {
                "time_saved_minutes": round(
                    do_nothing.estimated_completion_minutes - 
                    recover_now.estimated_completion_minutes,
                    1
                ),
                "tasks_delta": do_nothing.affected_tasks_count - recover_now.affected_tasks_count,
                "deadline_delta": do_nothing.deadline_breaches - recover_now.deadline_breaches,
                "cost_delta_clstr": round(
                    do_nothing.estimated_cost_clstr - recover_now.estimated_cost_clstr,
                    2
                ),
                "recommended_action": "RECOVER_NOW" if recover_now.estimated_completion_minutes < do_nothing.estimated_completion_minutes else "EVALUATE"
            },
            "recommendation": {
                "action": "RECOVER_NOW",
                "reason": f"Recovery saves {round(do_nothing.estimated_completion_minutes - recover_now.estimated_completion_minutes, 1)} minutes and prevents {do_nothing.deadline_breaches - recover_now.deadline_breaches} deadline breaches",
                "confidence": "HIGH" if recover_now.estimated_completion_minutes < do_nothing.estimated_completion_minutes * 0.5 else "MEDIUM"
            }
        }
    
    def _load_tasks_snapshot(self, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load read-only snapshot of tasks."""
        tasks = self.db.query(Task).filter(Task.task_id.in_(task_ids)).all()
        
        snapshot = {}
        for task in tasks:
            snapshot[task.task_id] = {
                "task_id": task.task_id,
                "job_id": task.job_id,
                "status": task.status.value,
                "parameters": task.parameters or {},
                "retry_count": task.retry_count
            }
        
        return snapshot
    
    def _load_jobs_for_tasks(self, tasks_snapshot: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Load read-only snapshot of related jobs."""
        job_ids = list(set(t["job_id"] for t in tasks_snapshot.values()))
        jobs = self.db.query(Job).filter(Job.job_id.in_(job_ids)).all()
        
        snapshot = {}
        for job in jobs:
            elapsed = 0.0
            if job.created_at:
                elapsed = (datetime.utcnow() - job.created_at).total_seconds() / 60.0
            
            snapshot[job.job_id] = {
                "job_id": job.job_id,
                "customer_id": job.customer_id,
                "total_tasks": job.total_tasks,
                "completed_tasks": job.completed_tasks,
                "deadline_minutes": job.parameters.get("deadline_minutes") if job.parameters else None,
                "elapsed_minutes": elapsed,
                "budget_clstr": float(job.budget_clstr) if job.budget_clstr else 0.0
            }
        
        return snapshot
    
    def _count_available_nodes(self, exclude_node_id: Optional[str] = None) -> int:
        """Count available healthy nodes."""
        query = self.db.query(Node).filter(
            Node.status.in_([NodeStatus.HEALTHY, NodeStatus.AVAILABLE]),
            Node.is_healthy == True,
            Node.current_task_count < Node.max_concurrent_tasks
        )
        
        if exclude_node_id:
            query = query.filter(Node.node_id != exclude_node_id)
        
        return query.count()
