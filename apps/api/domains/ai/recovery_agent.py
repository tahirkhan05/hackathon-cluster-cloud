"""
Recovery Agent.

Provides intelligent recommendations for failure recovery strategies.
"""
import json
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from domains.ai.base_agent import BaseAgent


class RecoveryAgent(BaseAgent):
    """
    AI agent for recovery strategy recommendations.
    
    Analyzes:
    - Incident severity and impact
    - Available recovery options
    - Risk vs. urgency tradeoffs
    - Historical patterns
    """
    
    agent_name = "Recovery"
    agent_version = "1.0"
    
    def gather_context(
        self,
        incident_data: Dict[str, Any],
        affected_tasks: list,
        available_nodes_count: int,
        job_deadline: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gather context about incident and recovery options."""
        
        return {
            "incident": incident_data,
            "affected_tasks_count": len(affected_tasks),
            "affected_task_ids": [t.get("task_id") for t in affected_tasks[:5]],  # Sample
            "available_nodes_count": available_nodes_count,
            "job_deadline_seconds": job_deadline,
            "has_deadline_pressure": job_deadline is not None and job_deadline < 300
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert recovery agent for distributed computing failures.

Your role is to recommend the best recovery strategy when nodes fail.

Consider:
1. Urgency - does the job have a tight deadline?
2. Task criticality - how many tasks are affected?
3. Resource availability - are there enough healthy nodes?
4. Risk tolerance - should we wait or act immediately?
5. Cost implications - what's the budget impact?

Provide recommendations as JSON:
{
  "recommendation": {
    "strategy": "immediate_reassign" | "wait_for_recovery" | "split_across_nodes",
    "priority": "high" | "medium" | "low",
    "should_notify_customer": boolean,
    "max_wait_seconds": number or null
  },
  "reasoning": "Explanation of strategy choice",
  "confidence": 0.0-1.0
}

Prefer immediate reassignment if:
- Many tasks affected
- Tight deadline
- Sufficient healthy nodes available

Prefer waiting if:
- Few tasks affected
- No deadline pressure
- Node might recover soon"""
    
    def format_user_message(self, context: Dict[str, Any]) -> str:
        return f"""A node has failed and tasks need recovery:

Incident details:
{json.dumps(context['incident'], indent=2)}

Affected tasks: {context['affected_tasks_count']}
Available healthy nodes: {context['available_nodes_count']}
Deadline pressure: {context['has_deadline_pressure']}

What recovery strategy do you recommend?"""
    
    def get_response_schema(self) -> Dict[str, Any]:
        return {
            "recommendation": {
                "strategy": "string (immediate_reassign|wait_for_recovery|split_across_nodes)",
                "priority": "string (high|medium|low)",
                "should_notify_customer": "boolean",
                "max_wait_seconds": "number or null"
            },
            "reasoning": "string",
            "confidence": "number"
        }
    
    def validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[list]]:
        """Validate recovery strategy is feasible."""
        
        errors = []
        
        strategy = recommendation.get("strategy")
        valid_strategies = ["immediate_reassign", "wait_for_recovery", "split_across_nodes"]
        
        if strategy not in valid_strategies:
            errors.append(f"Invalid strategy: {strategy}")
        
        priority = recommendation.get("priority")
        if priority not in ["high", "medium", "low"]:
            errors.append(f"Invalid priority: {priority}")
        
        # If immediate reassignment but no nodes available
        if strategy == "immediate_reassign" and context["available_nodes_count"] == 0:
            errors.append("Cannot immediate_reassign with no available nodes")
        
        if errors:
            return False, {}, errors
        
        return True, {"validated": True}, None
    
    def deterministic_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic recovery decision based on rules."""
        
        affected_count = context["affected_tasks_count"]
        available_nodes = context["available_nodes_count"]
        has_deadline = context["has_deadline_pressure"]
        
        # Rule-based decision
        if available_nodes == 0:
            # No nodes available, must wait
            strategy = "wait_for_recovery"
            priority = "high" if affected_count > 5 else "medium"
            max_wait = 300  # 5 minutes
            notify = affected_count > 10
        elif has_deadline or affected_count > 10:
            # Urgent, reassign immediately
            strategy = "immediate_reassign"
            priority = "high"
            max_wait = None
            notify = True
        elif affected_count <= 3:
            # Few tasks, can wait a bit
            strategy = "wait_for_recovery"
            priority = "low"
            max_wait = 120  # 2 minutes
            notify = False
        else:
            # Default: reassign
            strategy = "immediate_reassign"
            priority = "medium"
            max_wait = None
            notify = affected_count > 20
        
        return {
            "strategy": strategy,
            "priority": priority,
            "should_notify_customer": notify,
            "max_wait_seconds": max_wait,
            "fallback": True
        }
