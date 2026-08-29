"""
Deterministic Resource Scheduler

Selects compatible nodes and creates task allocation plan for workloads.

Algorithm (plain English):
1. Filter nodes by compatibility (CPU, RAM, GPU requirements)
2. Filter by availability (status, capacity)
3. Filter by budget constraints
4. Rank by composite score:
   - Reliability (40% weight)
   - Cost efficiency (30% weight)
   - Capacity (30% weight)
5. Allocate tasks round-robin across top N nodes
6. Validate deadline feasibility
7. Return explicit allocation plan

All operations are deterministic and repeatable.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from domains.nodes.models import Node, NodeStatus
from domains.jobs.models import Job
from domains.tasks.service import TaskService

logger = logging.getLogger(__name__)


@dataclass
class SchedulingRequirements:
    """Workload resource requirements."""
    cpu_cores_min: int
    ram_gb_min: float
    gpu_required: bool = False
    gpu_vram_gb_min: Optional[float] = None
    
    task_count: int = 0
    estimated_task_duration_seconds: int = 60
    
    deadline_seconds: Optional[int] = None
    budget_clstr: float = 0
    reliability_min: float = 0.7
    
    prefer_gpu: bool = False


@dataclass
class NodeScore:
    """Scored node for ranking."""
    node: Node
    reliability_score: float
    cost_score: float
    capacity_score: float
    composite_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node.node_id,
            "provider_id": self.node.provider_id,
            "reliability_score": self.reliability_score,
            "cost_score": self.cost_score,
            "capacity_score": self.capacity_score,
            "composite_score": self.composite_score
        }


@dataclass
class AllocationPlan:
    """Explicit task allocation plan."""
    job_id: str
    total_tasks: int
    allocated_nodes: List[str]
    task_distribution: Dict[str, List[int]]
    estimated_cost_clstr: float
    estimated_duration_seconds: int
    scheduling_timestamp: datetime
    
    candidate_nodes_count: int
    filtered_reasons: Dict[str, int]
    node_scores: List[Dict[str, Any]]
    
    is_feasible: bool = True
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "total_tasks": self.total_tasks,
            "allocated_nodes": self.allocated_nodes,
            "task_distribution": self.task_distribution,
            "estimated_cost_clstr": self.estimated_cost_clstr,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "scheduling_timestamp": self.scheduling_timestamp.isoformat(),
            "candidate_nodes_count": self.candidate_nodes_count,
            "filtered_reasons": self.filtered_reasons,
            "node_scores": self.node_scores,
            "is_feasible": self.is_feasible,
            "warnings": self.warnings
        }


class ResourceScheduler:
    """Deterministic resource scheduler."""
    
    WEIGHT_RELIABILITY = 0.40
    WEIGHT_COST = 0.30
    WEIGHT_CAPACITY = 0.30
    
    def __init__(self, db: Session):
        self.db = db
        self.filtered_reasons: Dict[str, int] = {}
    
    def schedule(
        self,
        job: Job,
        requirements: SchedulingRequirements
    ) -> AllocationPlan:
        """
        Create deterministic allocation plan for job.
        
        Returns explicit plan with audit trail.
        """
        logger.info(f"Scheduling job {job.job_id} with {requirements.task_count} tasks")
        
        all_nodes = self.db.query(Node).all()
        logger.info(f"Total nodes in system: {len(all_nodes)}")
        
        compatible_nodes = self._filter_by_compatibility(all_nodes, requirements)
        logger.info(f"Compatible nodes: {len(compatible_nodes)}")
        
        available_nodes = self._filter_by_availability(compatible_nodes, requirements)
        logger.info(f"Available nodes: {len(available_nodes)}")
        
        if not available_nodes:
            return self._create_infeasible_plan(
                job.job_id,
                requirements,
                all_nodes,
                "No nodes meet requirements"
            )
        
        scored_nodes = self._score_nodes(available_nodes, requirements)
        scored_nodes.sort(key=lambda x: x.composite_score, reverse=True)
        
        logger.info(f"Top node score: {scored_nodes[0].composite_score:.3f}")
        
        selected_nodes = self._select_nodes(scored_nodes, requirements)
        
        if not selected_nodes:
            return self._create_infeasible_plan(
                job.job_id,
                requirements,
                all_nodes,
                "No nodes passed selection criteria"
            )
        
        task_distribution = self._distribute_tasks(
            selected_nodes,
            requirements.task_count
        )
        
        estimated_cost = self._calculate_cost(task_distribution, selected_nodes)
        estimated_duration = self._estimate_duration(
            task_distribution,
            selected_nodes,
            requirements.estimated_task_duration_seconds
        )
        
        warnings = []
        is_feasible = True
        
        if requirements.budget_clstr > 0 and estimated_cost > requirements.budget_clstr:
            warnings.append(
                f"Estimated cost {estimated_cost} exceeds budget {requirements.budget_clstr}"
            )
            is_feasible = False
        
        if requirements.deadline_seconds and estimated_duration > requirements.deadline_seconds:
            warnings.append(
                f"Estimated duration {estimated_duration}s exceeds deadline "
                f"{requirements.deadline_seconds}s"
            )
            is_feasible = False
        
        plan = AllocationPlan(
            job_id=job.job_id,
            total_tasks=requirements.task_count,
            allocated_nodes=[node.node.node_id for node in selected_nodes],
            task_distribution=task_distribution,
            estimated_cost_clstr=estimated_cost,
            estimated_duration_seconds=estimated_duration,
            scheduling_timestamp=datetime.utcnow(),
            candidate_nodes_count=len(all_nodes),
            filtered_reasons=self.filtered_reasons,
            node_scores=[ns.to_dict() for ns in scored_nodes[:10]],
            is_feasible=is_feasible,
            warnings=warnings
        )
        
        logger.info(
            f"Allocation plan: {len(selected_nodes)} nodes, "
            f"cost={estimated_cost:.2f}, duration={estimated_duration}s"
        )
        
        return plan
    
    def _filter_by_compatibility(
        self,
        nodes: List[Node],
        requirements: SchedulingRequirements
    ) -> List[Node]:
        """Filter nodes by hardware compatibility."""
        compatible = []
        
        for node in nodes:
            caps = node.capabilities
            
            cpu_cores = caps.get("cpu_cores_logical") or caps.get("cpu_cores_physical") or 0
            if cpu_cores < requirements.cpu_cores_min:
                self._increment_filter_reason("insufficient_cpu")
                continue
            
            ram_gb = caps.get("ram_total_gb", 0)
            if ram_gb < requirements.ram_gb_min:
                self._increment_filter_reason("insufficient_ram")
                continue
            
            if requirements.gpu_required:
                gpu_available = caps.get("gpu_available", False) or caps.get("gpu_count", 0) > 0
                if not gpu_available:
                    self._increment_filter_reason("no_gpu")
                    continue
                
                if requirements.gpu_vram_gb_min:
                    gpus = caps.get("gpus", [])
                    if gpus:
                        gpu_memory = gpus[0].get("gpu_memory_total_gb", 0)
                        if gpu_memory < requirements.gpu_vram_gb_min:
                            self._increment_filter_reason("insufficient_vram")
                            continue
                    else:
                        self._increment_filter_reason("gpu_info_missing")
                        continue
            
            compatible.append(node)
        
        return compatible
    
    def _filter_by_availability(
        self,
        nodes: List[Node],
        requirements: SchedulingRequirements
    ) -> List[Node]:
        """Filter nodes by availability and reliability."""
        available = []
        
        for node in nodes:
            if node.status == NodeStatus.OFFLINE:
                self._increment_filter_reason("offline")
                continue
            
            if not node.is_healthy:
                self._increment_filter_reason("unhealthy")
                continue
            
            if node.current_task_count >= node.max_concurrent_tasks:
                self._increment_filter_reason("at_capacity")
                continue
            
            if node.reliability_score < requirements.reliability_min:
                self._increment_filter_reason("low_reliability")
                continue
            
            available.append(node)
        
        return available
    
    def _score_nodes(
        self,
        nodes: List[Node],
        requirements: SchedulingRequirements
    ) -> List[NodeScore]:
        """
        Score nodes by reliability, cost, and capacity.
        
        All scores normalized to [0, 1] where higher is better.
        """
        scored = []
        
        if not nodes:
            return scored
        
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
            
            if requirements.prefer_gpu:
                caps = node.capabilities
                has_gpu = caps.get("gpu_available", False) or caps.get("gpu_count", 0) > 0
                if has_gpu:
                    reliability_score = min(1.0, reliability_score * 1.1)
            
            composite_score = (
                self.WEIGHT_RELIABILITY * reliability_score +
                self.WEIGHT_COST * cost_score +
                self.WEIGHT_CAPACITY * capacity_score
            )
            
            scored.append(NodeScore(
                node=node,
                reliability_score=reliability_score,
                cost_score=cost_score,
                capacity_score=capacity_score,
                composite_score=composite_score
            ))
        
        return scored
    
    def _select_nodes(
        self,
        scored_nodes: List[NodeScore],
        requirements: SchedulingRequirements
    ) -> List[NodeScore]:
        """
        Select nodes for allocation.
        
        Uses top-ranked nodes up to a reasonable limit.
        """
        max_nodes = max(1, len(scored_nodes) // 4)
        max_nodes = min(max_nodes, 10)
        
        selected = scored_nodes[:max_nodes]
        
        logger.info(f"Selected {len(selected)} nodes from {len(scored_nodes)} candidates")
        
        return selected
    
    def _distribute_tasks(
        self,
        nodes: List[NodeScore],
        task_count: int
    ) -> Dict[str, List[int]]:
        """
        Distribute tasks across nodes using round-robin.
        
        Ensures balanced load and deterministic allocation.
        """
        distribution = {node.node.node_id: [] for node in nodes}
        
        for task_num in range(1, task_count + 1):
            node_index = (task_num - 1) % len(nodes)
            node_id = nodes[node_index].node.node_id
            distribution[node_id].append(task_num)
        
        return distribution
    
    def _calculate_cost(
        self,
        distribution: Dict[str, List[int]],
        nodes: List[NodeScore]
    ) -> float:
        """Calculate total estimated cost."""
        total_cost = 0.0
        
        node_map = {node.node.node_id: node.node for node in nodes}
        
        for node_id, task_numbers in distribution.items():
            node = node_map[node_id]
            task_count = len(task_numbers)
            total_cost += float(node.cost_per_task_clstr) * task_count
        
        return total_cost
    
    def _estimate_duration(
        self,
        distribution: Dict[str, List[int]],
        nodes: List[NodeScore],
        task_duration_seconds: int
    ) -> int:
        """
        Estimate total job duration.
        
        Assumes parallel execution: duration = max(tasks_per_node) * task_duration
        """
        max_tasks_per_node = max(len(tasks) for tasks in distribution.values())
        
        estimated_duration = max_tasks_per_node * task_duration_seconds
        
        return estimated_duration
    
    def _increment_filter_reason(self, reason: str):
        """Track why nodes were filtered."""
        self.filtered_reasons[reason] = self.filtered_reasons.get(reason, 0) + 1
    
    def _create_infeasible_plan(
        self,
        job_id: str,
        requirements: SchedulingRequirements,
        all_nodes: List[Node],
        reason: str
    ) -> AllocationPlan:
        """Create infeasible allocation plan with reason."""
        return AllocationPlan(
            job_id=job_id,
            total_tasks=requirements.task_count,
            allocated_nodes=[],
            task_distribution={},
            estimated_cost_clstr=0.0,
            estimated_duration_seconds=0,
            scheduling_timestamp=datetime.utcnow(),
            candidate_nodes_count=len(all_nodes),
            filtered_reasons=self.filtered_reasons,
            node_scores=[],
            is_feasible=False,
            warnings=[reason]
        )
    
    def execute_allocation(
        self,
        plan: AllocationPlan,
        job: Job,
        base_task_parameters: Dict[str, Any]
    ) -> List:
        """
        Execute allocation plan by creating tasks.
        
        Creates tasks with explicit node assignments based on plan.
        """
        tasks = []
        
        for node_id, task_numbers in plan.task_distribution.items():
            for task_num in task_numbers:
                task_params = {
                    **base_task_parameters,
                    "task_index": task_num - 1,
                    "assigned_node_id": node_id
                }
                
                from domains.tasks.schemas import TaskCreate
                task_data = TaskCreate(
                    job_id=job.job_id,
                    task_number=task_num,
                    parameters=task_params,
                    max_retries=3
                )
                
                task = TaskService.create_task(self.db, task_data)
                tasks.append(task)
        
        logger.info(f"Created {len(tasks)} tasks for job {job.job_id}")
        
        return tasks
