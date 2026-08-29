"""
Workload Analysis Agent.

Analyzes workload requirements and suggests optimal resource allocation.
"""
import json
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from domains.ai.base_agent import BaseAgent


class WorkloadAnalysisAgent(BaseAgent):
    """
    AI agent for analyzing workload and determining resource needs.
    
    Examines:
    - Workload type and parameters
    - Estimated complexity
    - Resource requirements
    - Execution strategy
    """
    
    agent_name = "WorkloadAnalysis"
    agent_version = "1.0"
    
    def gather_context(
        self,
        workload_type: str,
        parameters: Dict[str, Any],
        customer_budget: float
    ) -> Dict[str, Any]:
        """Gather context about workload."""
        
        return {
            "workload_type": workload_type,
            "parameters": parameters,
            "customer_budget": customer_budget
        }
    
    def get_system_prompt(self) -> str:
        return """You are an expert workload analysis agent for distributed computing.

Your role is to analyze a workload and recommend optimal resource requirements.

For frame rendering workloads, consider:
- Frame count and complexity
- Resolution (higher = more RAM/VRAM)
- Rendering quality settings
- Estimated time per frame

Provide recommendations as JSON:
{
  "recommendation": {
    "cpu_cores_min": number,
    "ram_gb_min": number,
    "gpu_required": boolean,
    "gpu_vram_gb_min": number or null,
    "estimated_task_duration_seconds": number,
    "estimated_total_cost_clstr": number,
    "parallelization_recommended": boolean,
    "suggested_task_count": number
  },
  "reasoning": "Explanation of resource needs",
  "confidence": 0.0-1.0
}

Be practical - don't over-provision resources. Consider the customer's budget."""
    
    def format_user_message(self, context: Dict[str, Any]) -> str:
        return f"""Analyze this workload and recommend resources:

Workload type: {context['workload_type']}

Parameters:
{json.dumps(context['parameters'], indent=2)}

Customer budget: {context['customer_budget']} CLSTR

What are the optimal resource requirements?"""
    
    def get_response_schema(self) -> Dict[str, Any]:
        return {
            "recommendation": {
                "cpu_cores_min": "number",
                "ram_gb_min": "number",
                "gpu_required": "boolean",
                "gpu_vram_gb_min": "number or null",
                "estimated_task_duration_seconds": "number",
                "estimated_total_cost_clstr": "number",
                "parallelization_recommended": "boolean",
                "suggested_task_count": "number"
            },
            "reasoning": "string",
            "confidence": "number"
        }
    
    def validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[list]]:
        """Validate resource recommendations are reasonable."""
        
        errors = []
        
        required_fields = ["cpu_cores_min", "ram_gb_min", "gpu_required"]
        for field in required_fields:
            if field not in recommendation:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, {}, errors
        
        if recommendation["cpu_cores_min"] < 1 or recommendation["cpu_cores_min"] > 128:
            errors.append("cpu_cores_min must be between 1 and 128")
        
        if recommendation["ram_gb_min"] < 1 or recommendation["ram_gb_min"] > 1024:
            errors.append("ram_gb_min must be between 1 and 1024")
        
        if recommendation.get("estimated_total_cost_clstr", 0) > context["customer_budget"] * 1.5:
            errors.append("Estimated cost exceeds budget by more than 50%")
        
        if errors:
            return False, {}, errors
        
        return True, {"validated": True}, None
    
    def deterministic_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic resource estimation based on workload type."""
        
        params = context["parameters"]
        workload_type = context["workload_type"]
        
        if workload_type == "frame_rendering":
            frame_count = params.get("frame_count", 100)
            width = params.get("width", 1920)
            height = params.get("height", 1080)
            complexity = params.get("complexity", "medium")
            
            resolution_factor = (width * height) / (1920 * 1080)
            
            complexity_multipliers = {
                "low": 0.5,
                "medium": 1.0,
                "high": 2.0
            }
            complexity_mult = complexity_multipliers.get(complexity, 1.0)
            
            cpu_cores = max(2, int(4 * resolution_factor))
            ram_gb = max(4, int(8 * resolution_factor))
            
            gpu_required = resolution_factor > 1.5 or complexity == "high"
            gpu_vram_gb = int(4 * resolution_factor) if gpu_required else None
            
            base_time_per_frame = 3
            estimated_time = base_time_per_frame * complexity_mult * resolution_factor
            
            estimated_cost = frame_count * 10
            
            return {
                "cpu_cores_min": cpu_cores,
                "ram_gb_min": ram_gb,
                "gpu_required": gpu_required,
                "gpu_vram_gb_min": gpu_vram_gb,
                "estimated_task_duration_seconds": int(estimated_time),
                "estimated_total_cost_clstr": estimated_cost,
                "parallelization_recommended": frame_count > 10,
                "suggested_task_count": frame_count,
                "fallback": True
            }
        
        return {
            "cpu_cores_min": 4,
            "ram_gb_min": 8,
            "gpu_required": False,
            "gpu_vram_gb_min": None,
            "estimated_task_duration_seconds": 60,
            "estimated_total_cost_clstr": 1000,
            "parallelization_recommended": True,
            "suggested_task_count": params.get("task_count", 10),
            "fallback": True
        }
