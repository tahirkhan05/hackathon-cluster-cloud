"""
Cascade Impact Analyzer

Analyzes downstream effects of incidents using actual system relationships.
Does NOT simulate future states - only analyzes current impact chain.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from domains.incidents.models import Incident
from domains.nodes.models import Node
from domains.tasks.models import Task, TaskStatus
from domains.jobs.models import Job, JobStatus

logger = logging.getLogger(__name__)


class CascadeImpact:
    """Structured cascade impact result."""
    
    def __init__(self):
        self.affected_node: Optional[Dict[str, Any]] = None
        self.affected_tasks: List[Dict[str, Any]] = []
        self.affected_jobs: List[Dict[str, Any]] = []
        self.estimated_delay_minutes: float = 0.0
        self.deadline_risks: List[Dict[str, Any]] = []
        self.customer_impacts: List[Dict[str, Any]] = []
        self.cascade_chain: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "affected_node": self.affected_node,
            "affected_tasks": self.affected_tasks,
            "affected_jobs": self.affected_jobs,
            "estimated_delay_minutes": self.estimated_delay_minutes,
            "deadline_risks": self.deadline_risks,
            "customer_impacts": self.customer_impacts,
            "cascade_chain": self.cascade_chain
        }


class CascadeAnalyzer:
    """
    Analyzes cascade effects of incidents.
    
    Uses actual database relationships to identify impact chain:
    Node → Tasks → Jobs → Deadlines → Customer Impact
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_node_failure(self, node_id: str) -> CascadeImpact:
        """
        Analyze cascade impact of node failure.
        
        Args:
            node_id: Failed node ID
            
        Returns:
            CascadeImpact with full impact chain
        """
        impact = CascadeImpact()
        
        node = self.db.query(Node).filter_by(node_id=node_id).first()
        if not node:
            logger.warning(f"Node {node_id} not found")
            return impact
        
        impact.affected_node = {
            "node_id": node.node_id,
            "name": node.provider_id,
            "provider_id": node.provider_id,
            "status": node.status.value,
            "is_healthy": node.is_healthy,
            "current_task_count": node.current_task_count
        }
        
        affected_tasks = self.db.query(Task).filter(
            Task.assigned_node_id == node_id,
            Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING])
        ).all()
        
        if not affected_tasks:
            logger.info(f"No active tasks on node {node_id}")
            return impact
        
        impact.cascade_chain.append({
            "step": "node_failure",
            "description": f"Node {node.provider_id} failed",
            "timestamp": datetime.utcnow().isoformat(),
            "affected_count": len(affected_tasks)
        })
        
        total_estimated_time = 0.0
        job_ids = set()
        
        for task in affected_tasks:
            estimated_minutes = self._estimate_task_duration(task)
            total_estimated_time += estimated_minutes
            
            job_ids.add(task.job_id)
            
            impact.affected_tasks.append({
                "task_id": task.task_id,
                "job_id": task.job_id,
                "status": task.status.value,
                "frame_number": task.parameters.get("frame_number", "unknown"),
                "estimated_completion_minutes": estimated_minutes,
                "retry_count": task.retry_count
            })
        
        impact.estimated_delay_minutes = total_estimated_time
        
        impact.cascade_chain.append({
            "step": "tasks_affected",
            "description": f"{len(affected_tasks)} tasks interrupted",
            "timestamp": datetime.utcnow().isoformat(),
            "estimated_delay_minutes": total_estimated_time
        })
        
        for job_id in job_ids:
            job = self.db.query(Job).filter_by(job_id=job_id).first()
            if not job:
                continue
            
            job_impact = self._analyze_job_impact(job, affected_tasks)
            impact.affected_jobs.append(job_impact)
            
            deadline_minutes = job.parameters.get("deadline_minutes")
            if deadline_minutes:
                deadline_risk = self._assess_deadline_risk(
                    job,
                    deadline_minutes,
                    total_estimated_time
                )
                if deadline_risk:
                    impact.deadline_risks.append(deadline_risk)
            
            customer_impact = self._assess_customer_impact(job, job_impact)
            if customer_impact:
                impact.customer_impacts.append(customer_impact)
        
        impact.cascade_chain.append({
            "step": "jobs_impacted",
            "description": f"{len(job_ids)} jobs affected",
            "timestamp": datetime.utcnow().isoformat(),
            "jobs_count": len(job_ids)
        })
        
        if impact.deadline_risks:
            impact.cascade_chain.append({
                "step": "deadline_risk",
                "description": f"{len(impact.deadline_risks)} jobs at deadline risk",
                "timestamp": datetime.utcnow().isoformat(),
                "risk_level": "HIGH"
            })
        
        if impact.customer_impacts:
            impact.cascade_chain.append({
                "step": "customer_impact",
                "description": f"{len(impact.customer_impacts)} customers affected",
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "MEDIUM"
            })
        
        return impact
    
    def analyze_incident(self, incident: Incident) -> CascadeImpact:
        """
        Analyze cascade impact of existing incident.
        
        Args:
            incident: Incident record
            
        Returns:
            CascadeImpact with full impact chain
        """
        if incident.node_id:
            return self.analyze_node_failure(incident.node_id)
        
        impact = CascadeImpact()
        
        if incident.task_id:
            task = self.db.query(Task).filter_by(task_id=incident.task_id).first()
            if task:
                impact.affected_tasks.append({
                    "task_id": task.task_id,
                    "job_id": task.job_id,
                    "status": task.status.value
                })
        
        return impact
    
    def _estimate_task_duration(self, task: Task) -> float:
        """
        Estimate task completion time in minutes.
        
        Based on workload parameters and complexity.
        """
        base_minutes = 5.0
        
        resolution = task.parameters.get("resolution", "1920x1080")
        if "2560" in resolution or "4K" in resolution:
            base_minutes *= 1.5
        elif "3840" in resolution or "8K" in resolution:
            base_minutes *= 2.0
        
        complexity = task.parameters.get("complexity", "medium")
        if complexity == "high":
            base_minutes *= 1.3
        elif complexity == "low":
            base_minutes *= 0.7
        
        return base_minutes
    
    def _analyze_job_impact(
        self,
        job: Job,
        affected_tasks: List[Task]
    ) -> Dict[str, Any]:
        """Analyze impact on specific job."""
        job_tasks = [t for t in affected_tasks if t.job_id == job.job_id]
        
        affected_percentage = (len(job_tasks) / max(job.total_tasks, 1)) * 100
        
        return {
            "job_id": job.job_id,
            "customer_id": job.customer_id,
            "workload_type": job.workload_type,
            "status": job.status.value,
            "total_tasks": job.total_tasks,
            "completed_tasks": job.completed_tasks,
            "affected_tasks_count": len(job_tasks),
            "affected_percentage": round(affected_percentage, 1),
            "progress_percentage": job.progress_percentage,
            "budget_clstr": float(job.budget_clstr) if job.budget_clstr else 0.0
        }
    
    def _assess_deadline_risk(
        self,
        job: Job,
        deadline_minutes: float,
        estimated_delay_minutes: float
    ) -> Optional[Dict[str, Any]]:
        """
        Assess deadline risk for job.
        
        Returns None if no risk, otherwise risk details.
        """
        if not job.created_at:
            return None
        
        elapsed = (datetime.utcnow() - job.created_at).total_seconds() / 60.0
        
        remaining_minutes = deadline_minutes - elapsed
        
        remaining_tasks = job.total_tasks - job.completed_tasks
        avg_task_minutes = 5.0
        estimated_remaining = remaining_tasks * avg_task_minutes + estimated_delay_minutes
        
        if estimated_remaining > remaining_minutes:
            slack_minutes = remaining_minutes - estimated_remaining
            
            return {
                "job_id": job.job_id,
                "customer_id": job.customer_id,
                "deadline_minutes": deadline_minutes,
                "elapsed_minutes": round(elapsed, 1),
                "remaining_minutes": round(remaining_minutes, 1),
                "estimated_completion_minutes": round(estimated_remaining, 1),
                "slack_minutes": round(slack_minutes, 1),
                "risk_level": "HIGH" if slack_minutes < -10 else "MEDIUM"
            }
        
        return None
    
    def _assess_customer_impact(
        self,
        job: Job,
        job_impact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Assess customer-level impact."""
        if job_impact["affected_percentage"] > 20:
            return {
                "customer_id": job.customer_id,
                "job_id": job.job_id,
                "impact_level": "MEDIUM" if job_impact["affected_percentage"] < 50 else "HIGH",
                "affected_percentage": job_impact["affected_percentage"],
                "job_progress": job_impact["progress_percentage"]
            }
        
        return None
