"""
Recovery Service

Automatically recovers failed tasks by reassigning to healthy nodes.
Deterministic validation ensures compatibility and constraints.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from domains.nodes.models import Node, NodeStatus
from domains.tasks.models import Task, TaskStatus
from domains.jobs.models import Job
from domains.incidents.models import Incident, IncidentStatus, IncidentType

logger = logging.getLogger(__name__)


class RecoveryService:
    """
    Handles automatic recovery of failed tasks.
    
    Recovery workflow:
    1. Identify affected tasks from incident
    2. Find compatible replacement nodes
    3. Validate compatibility and constraints
    4. Reassign tasks to new nodes
    5. Mark tasks for retry
    6. Resolve incident
    """
    
    MIN_RECOVERY_RELIABILITY = 0.7
    
    def __init__(self, db: Session):
        self.db = db
    
    def recover_from_node_failure(self, incident: Incident) -> Dict[str, Any]:
        """
        Recover all tasks affected by node failure.
        
        Args:
            incident: Node failure incident
            
        Returns:
            Recovery summary with task reassignments
        """
        if incident.incident_type != "node_failure":
            raise ValueError(f"Incident {incident.incident_id} is not a node failure")
        
        if incident.status != IncidentStatus.OPEN:
            logger.info(f"Incident {incident.incident_id} already resolved, skipping recovery")
            return {
                "incident_id": incident.incident_id,
                "status": "already_resolved",
                "tasks_recovered": 0
            }
        
        logger.info(f"Starting recovery for incident {incident.incident_id}")
        
        affected_tasks = self._get_affected_tasks(incident)
        
        if not affected_tasks:
            logger.info(f"No affected tasks found for incident {incident.incident_id}")
            self._resolve_incident(incident, "No tasks to recover")
            return {
                "incident_id": incident.incident_id,
                "status": "no_tasks",
                "tasks_recovered": 0
            }
        
        logger.info(f"Found {len(affected_tasks)} affected tasks")
        
        recovery_results = []
        
        for task in affected_tasks:
            result = self._recover_task(task)
            recovery_results.append(result)
        
        successful = [r for r in recovery_results if r["success"]]
        failed = [r for r in recovery_results if not r["success"]]
        
        logger.info(
            f"Recovery complete: {len(successful)} successful, {len(failed)} failed"
        )
        
        if len(successful) == len(affected_tasks):
            self._resolve_incident(
                incident,
                f"All {len(successful)} tasks successfully reassigned and restarted"
            )
            status = "success"
        elif len(successful) > 0:
            incident.metadata["partial_recovery"] = True
            incident.metadata["tasks_recovered"] = len(successful)
            incident.metadata["tasks_failed_recovery"] = len(failed)
            self.db.commit()
            status = "partial"
        else:
            incident.metadata["recovery_failed"] = True
            incident.metadata["failure_reasons"] = [r["error"] for r in failed]
            self.db.commit()
            status = "failed"
        
        return {
            "incident_id": incident.incident_id,
            "status": status,
            "tasks_recovered": len(successful),
            "tasks_failed": len(failed),
            "recovery_details": recovery_results
        }
    
    def _get_affected_tasks(self, incident: Incident) -> List[Task]:
        """Get tasks that need recovery from incident."""
        task_ids = incident.metadata.get("incomplete_task_ids", [])
        
        if not task_ids:
            return []
        
        tasks = self.db.query(Task).filter(
            Task.task_id.in_(task_ids),
            Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING, TaskStatus.FAILED])
        ).all()
        
        return tasks
    
    def _recover_task(self, task: Task) -> Dict[str, Any]:
        """
        Recover a single task by reassigning to new node.
        
        Returns:
            Recovery result dict
        """
        logger.info(f"Recovering task {task.task_id} (job: {task.job_id})")
        
        try:
            job = self.db.query(Job).filter(Job.job_id == task.job_id).first()
            
            if not job:
                return {
                    "task_id": task.task_id,
                    "success": False,
                    "error": "Job not found"
                }
            
            requirements = self._extract_requirements(job, task)
            
            candidate_nodes = self._find_compatible_nodes(task, requirements)
            
            if not candidate_nodes:
                logger.warning(f"No compatible nodes found for task {task.task_id}")
                return {
                    "task_id": task.task_id,
                    "success": False,
                    "error": "No compatible nodes available"
                }
            
            selected_node = self._select_best_node(candidate_nodes, requirements)
            
            validation_result = self._validate_assignment(
                task, selected_node, requirements
            )
            
            if not validation_result["valid"]:
                logger.warning(
                    f"Node {selected_node.node_id} failed validation: "
                    f"{validation_result['reason']}"
                )
                return {
                    "task_id": task.task_id,
                    "success": False,
                    "error": f"Validation failed: {validation_result['reason']}"
                }
            
            old_node_id = task.node_id
            self._reassign_task(task, selected_node)
            
            logger.info(
                f"Task {task.task_id} reassigned: "
                f"{old_node_id} → {selected_node.node_id}"
            )
            
            return {
                "task_id": task.task_id,
                "success": True,
                "old_node_id": old_node_id,
                "new_node_id": selected_node.node_id,
                "retry_count": task.retry_count
            }
            
        except Exception as e:
            logger.error(f"Error recovering task {task.task_id}: {e}", exc_info=True)
            return {
                "task_id": task.task_id,
                "success": False,
                "error": str(e)
            }
    
    def _extract_requirements(self, job: Job, task: Task) -> Dict[str, Any]:
        """Extract resource requirements from job and task parameters."""
        params = job.parameters or {}
        
        requirements = {
            "cpu_cores_min": params.get("cpu_cores_min", 2),
            "ram_gb_min": params.get("ram_gb_min", 4.0),
            "gpu_required": params.get("gpu_required", False),
            "gpu_vram_gb_min": params.get("gpu_vram_gb_min"),
            "reliability_min": self.MIN_RECOVERY_RELIABILITY,
            "budget_remaining": job.budget_clstr,
            "max_cost_per_task": job.budget_clstr / max(params.get("frame_count", 100), 1)
        }
        
        return requirements
    
    def _find_compatible_nodes(
        self,
        task: Task,
        requirements: Dict[str, Any]
    ) -> List[Node]:
        """
        Find nodes compatible with task requirements.
        
        Filters:
        - Status: AVAILABLE or BUSY (not OFFLINE)
        - Healthy: is_healthy = True
        - Not the failed node
        - Has capacity
        - Meets CPU/RAM/GPU requirements
        - Meets reliability threshold
        """
        query = self.db.query(Node).filter(
            Node.status.in_([NodeStatus.AVAILABLE, NodeStatus.BUSY]),
            Node.is_healthy == True,
            Node.current_task_count < Node.max_concurrent_tasks,
            Node.reliability_score >= requirements["reliability_min"]
        )
        
        if task.node_id:
            query = query.filter(Node.node_id != task.node_id)
        
        all_nodes = query.all()
        
        compatible_nodes = []
        
        for node in all_nodes:
            caps = node.capabilities
            
            cpu_cores = caps.get("cpu_cores_logical") or caps.get("cpu_cores_physical") or 0
            if cpu_cores < requirements["cpu_cores_min"]:
                continue
            
            ram_gb = caps.get("ram_total_gb", 0)
            if ram_gb < requirements["ram_gb_min"]:
                continue
            
            if requirements["gpu_required"]:
                gpu_available = caps.get("gpu_available", False) or caps.get("gpu_count", 0) > 0
                if not gpu_available:
                    continue
                
                if requirements["gpu_vram_gb_min"]:
                    gpus = caps.get("gpus", [])
                    if gpus:
                        gpu_memory = gpus[0].get("gpu_memory_total_gb", 0)
                        if gpu_memory < requirements["gpu_vram_gb_min"]:
                            continue
                    else:
                        continue
            
            if node.cost_per_task_clstr > requirements["max_cost_per_task"]:
                continue
            
            compatible_nodes.append(node)
        
        logger.info(
            f"Found {len(compatible_nodes)} compatible nodes "
            f"(filtered from {len(all_nodes)} healthy nodes)"
        )
        
        return compatible_nodes
    
    def _select_best_node(
        self,
        nodes: List[Node],
        requirements: Dict[str, Any]
    ) -> Node:
        """
        Select best node from candidates using scoring.
        
        Scoring factors:
        - Reliability: 40%
        - Cost: 30%
        - Capacity: 30%
        """
        if not nodes:
            raise ValueError("No nodes available for selection")
        
        if len(nodes) == 1:
            return nodes[0]
        
        scored_nodes = []
        
        costs = [float(node.cost_per_task_clstr) for node in nodes]
        min_cost = min(costs)
        max_cost = max(costs)
        
        capacities = [node.max_concurrent_tasks - node.current_task_count for node in nodes]
        max_capacity = max(capacities)
        
        for node in nodes:
            reliability_score = node.reliability_score
            
            if max_cost > min_cost:
                cost_score = 1.0 - (float(node.cost_per_task_clstr) - min_cost) / (max_cost - min_cost)
            else:
                cost_score = 1.0
            
            available_capacity = node.max_concurrent_tasks - node.current_task_count
            capacity_score = available_capacity / max_capacity if max_capacity > 0 else 0.0
            
            composite_score = (
                0.40 * reliability_score +
                0.30 * cost_score +
                0.30 * capacity_score
            )
            
            scored_nodes.append((node, composite_score))
        
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        selected_node = scored_nodes[0][0]
        selected_score = scored_nodes[0][1]
        
        logger.info(
            f"Selected node {selected_node.node_id} "
            f"(score: {selected_score:.3f}, reliability: {selected_node.reliability_score:.3f})"
        )
        
        return selected_node
    
    def _validate_assignment(
        self,
        task: Task,
        node: Node,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Final validation before assignment.
        
        Double-checks all constraints.
        """
        if node.status not in [NodeStatus.AVAILABLE, NodeStatus.BUSY]:
            return {"valid": False, "reason": f"Node status is {node.status}"}
        
        if not node.is_healthy:
            return {"valid": False, "reason": "Node is unhealthy"}
        
        if node.current_task_count >= node.max_concurrent_tasks:
            return {"valid": False, "reason": "Node at capacity"}
        
        if node.reliability_score < requirements["reliability_min"]:
            return {"valid": False, "reason": "Reliability below threshold"}
        
        if node.cost_per_task_clstr > requirements["max_cost_per_task"]:
            return {"valid": False, "reason": "Cost exceeds budget"}
        
        return {"valid": True}
    
    def _reassign_task(self, task: Task, new_node: Node):
        """
        Reassign task to new node and reset to ASSIGNED status.
        
        This triggers retry when node polls for work.
        """
        old_status = task.status
        
        task.node_id = new_node.node_id
        task.status = TaskStatus.ASSIGNED
        task.retry_count += 1
        task.assigned_at = datetime.utcnow()
        
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        
        
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(
            f"Task {task.task_id} reassigned to {new_node.node_id}: "
            f"{old_status} → ASSIGNED (retry #{task.retry_count})"
        )
    
    def _resolve_incident(self, incident: Incident, resolution: str):
        """Mark incident as resolved."""
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        incident.resolution = resolution
        
        self.db.commit()
        self.db.refresh(incident)
        
        logger.info(f"Incident {incident.incident_id} resolved: {resolution}")
    
    def recover_all_open_incidents(self) -> Dict[str, Any]:
        """
        Recover all open node failure incidents.
        
        Returns:
            Summary of recovery operations
        """
        incidents = self.db.query(Incident).filter(
            Incident.status == IncidentStatus.OPEN,
            Incident.incident_type == "node_failure"
        ).all()
        
        if not incidents:
            logger.info("No open incidents to recover")
            return {
                "total_incidents": 0,
                "recovered": 0,
                "failed": 0,
                "total_tasks_recovered": 0
            }
        
        logger.info(f"Recovering {len(incidents)} open incidents")
        
        results = []
        total_tasks = 0
        
        for incident in incidents:
            result = self.recover_from_node_failure(incident)
            results.append(result)
            total_tasks += result.get("tasks_recovered", 0)
        
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "failed"])
        
        return {
            "total_incidents": len(incidents),
            "recovered": successful,
            "failed": failed,
            "total_tasks_recovered": total_tasks,
            "details": results
        }
