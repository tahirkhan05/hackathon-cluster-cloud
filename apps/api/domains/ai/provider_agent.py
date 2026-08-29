"""
Provider Recommendation Agent.

Recommends best node for task recovery based on multi-dimensional analysis.
"""
import json
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session

from domains.ai.base_agent import BaseAgent
from domains.nodes.models import Node


class ProviderRecommendationAgent(BaseAgent):
    """
    AI agent for selecting optimal provider node.
    
    Uses AI to reason about:
    - Resource compatibility
    - Historical reliability
    - Cost optimization
    - Network topology (future)
    - Provider reputation (future)
    """
    
    agent_name = "ProviderRecommendation"
    agent_version = "1.0"
    
    def gather_context(
        self,
        candidate_nodes: List[Node],
        requirements: Dict[str, Any],
        task_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Gather context about available nodes and requirements."""
        
        # Format candidate nodes for AI
        nodes_data = []
        for node in candidate_nodes:
            nodes_data.append({
                "node_id": node.node_id[:16],  # Truncate for readability
                "provider_id": node.provider_id,
                "reliability_score": node.reliability_score,
                "cost_per_task_clstr": float(node.cost_per_task_clstr),
                "available_capacity": node.max_concurrent_tasks - node.current_task_count,
                "max_capacity": node.max_concurrent_tasks,
                "cpu_cores": node.capabilities.get("cpu_cores_logical"),
                "ram_gb": node.capabilities.get("ram_total_gb"),
                "gpu_available": node.capabilities.get("gpu_available", False),
                "failure_count": node.failure_count,
                "total_tasks_completed": node.total_tasks_completed
            })
        
        return {
            "candidate_nodes": nodes_data,
            "requirements": requirements,
            "task_info": task_info or {},
            "candidate_count": len(candidate_nodes)
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert provider recommendation agent for a distributed computing cluster.

Your role is to recommend the optimal node from a list of candidates for executing a task.

Consider:
1. Reliability (most important) - nodes with high reliability scores and low failure counts
2. Cost efficiency - balance quality and cost
3. Available capacity - prefer nodes with more free slots
4. Resource match - how well the node matches requirements
5. Historical performance - total tasks completed

Provide your recommendation as JSON with:
{
  "recommendation": {
    "node_id": "selected node ID",
    "provider_id": "provider identifier"
  },
  "reasoning": "Brief explanation of why this node was selected",
  "confidence": 0.0-1.0 (how confident you are in this recommendation)
}

Be conservative - only recommend a node if you are confident it's a good match.
If candidates are equally matched, prefer higher reliability."""
    
    def format_user_message(self, context: Dict[str, Any]) -> str:
        return f"""Select the best node for this task:

Requirements:
{json.dumps(context['requirements'], indent=2)}

Available candidate nodes:
{json.dumps(context['candidate_nodes'], indent=2)}

Task information:
{json.dumps(context['task_info'], indent=2)}

Recommend the best node based on reliability, cost, and capacity."""
    
    def get_response_schema(self) -> Dict[str, Any]:
        return {
            "recommendation": {
                "node_id": "string",
                "provider_id": "string"
            },
            "reasoning": "string",
            "confidence": "number (0-1)"
        }
    
    def validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[list]]:
        """Validate that recommended node exists and meets requirements."""
        
        node_id = recommendation.get("node_id")
        provider_id = recommendation.get("provider_id")
        
        if not node_id or not provider_id:
            return False, {}, ["Missing node_id or provider_id"]
        
        # Check node exists in candidates
        candidates = context["candidate_nodes"]
        matching_node = None
        
        for node in candidates:
            if node["node_id"].startswith(node_id[:8]):  # Partial match OK
                matching_node = node
                break
        
        if not matching_node:
            return False, {}, [f"Recommended node {node_id} not in candidate list"]
        
        # All candidates already passed compatibility checks
        # so if it's in the list, it's valid
        
        return True, {"validated_node": matching_node}, None
    
    def deterministic_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select node using deterministic scoring (Phase 4 algorithm)."""
        
        candidates = context["candidate_nodes"]
        
        if not candidates:
            return {"node_id": None, "provider_id": None, "fallback": True}
        
        # Score nodes using same algorithm as scheduler
        WEIGHT_RELIABILITY = 0.40
        WEIGHT_COST = 0.30
        WEIGHT_CAPACITY = 0.30
        
        costs = [node["cost_per_task_clstr"] for node in candidates]
        min_cost = min(costs)
        max_cost = max(costs)
        
        capacities = [node["available_capacity"] for node in candidates]
        max_capacity = max(capacities) if capacities else 1
        
        best_node = None
        best_score = -1
        
        for node in candidates:
            reliability_score = node["reliability_score"]
            
            if max_cost > min_cost:
                cost_score = 1.0 - (node["cost_per_task_clstr"] - min_cost) / (max_cost - min_cost)
            else:
                cost_score = 1.0
            
            capacity_score = node["available_capacity"] / max_capacity if max_capacity > 0 else 0
            
            composite_score = (
                WEIGHT_RELIABILITY * reliability_score +
                WEIGHT_COST * cost_score +
                WEIGHT_CAPACITY * capacity_score
            )
            
            if composite_score > best_score:
                best_score = composite_score
                best_node = node
        
        return {
            "node_id": best_node["node_id"],
            "provider_id": best_node["provider_id"],
            "fallback": True,
            "score": best_score
        }
