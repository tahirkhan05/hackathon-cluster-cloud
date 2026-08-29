"""Impact analysis API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from domains.impact.cascade_analyzer import CascadeAnalyzer
from domains.simulation.scenario_simulator import ScenarioSimulator
from domains.impact.decision_window import DecisionWindow
from domains.incidents.models import Incident
from domains.ai.bedrock_client import BedrockClient
from config import settings

router = APIRouter()


@router.get("/node-failure/{node_id}/analysis")
def analyze_node_failure_impact(
    node_id: str,
    db: Session = Depends(get_db)
):
    """
    Complete impact analysis for node failure.
    
    Returns:
    - Cascade impact chain
    - DO_NOTHING vs RECOVER_NOW scenarios
    - Decision window
    - AI explanation
    """
    cascade = CascadeAnalyzer(db)
    impact = cascade.analyze_node_failure(node_id)
    
    if not impact.affected_tasks:
        return {
            "node_id": node_id,
            "impact": "none",
            "message": "No active tasks on this node"
        }
    
    affected_task_ids = [t["task_id"] for t in impact.affected_tasks]
    
    simulator = ScenarioSimulator(db)
    scenarios = simulator.compare_scenarios(node_id, affected_task_ids)
    
    decision = DecisionWindow(db)
    window = decision.calculate_for_node_failure(node_id, affected_task_ids)
    
    explanation = None
    try:
        bedrock = BedrockClient.from_settings(settings)
        if bedrock.available:
            explanation = _generate_explanation(
                impact.to_dict(),
                scenarios,
                window,
                bedrock
            )
    except Exception as e:
        pass
    
    return {
        "node_id": node_id,
        "cascade_impact": impact.to_dict(),
        "scenarios": scenarios,
        "decision_window": window,
        "ai_explanation": explanation,
        "timestamp": Incident.detected_at.default.arg().isoformat() if hasattr(Incident.detected_at.default, 'arg') else None
    }


@router.get("/incident/{incident_id}/analysis")
def analyze_incident_impact(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Complete impact analysis for existing incident.
    """
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if not incident.node_id:
        raise HTTPException(
            status_code=400,
            detail="Incident is not a node failure"
        )
    
    affected_task_ids = incident.metadata.get("incomplete_task_ids", []) if incident.metadata else []
    
    cascade = CascadeAnalyzer(db)
    impact = cascade.analyze_incident(incident)
    
    simulator = ScenarioSimulator(db)
    scenarios = simulator.compare_scenarios(incident.node_id, affected_task_ids)
    
    decision = DecisionWindow(db)
    window = decision.calculate_for_incident(incident)
    
    explanation = None
    try:
        bedrock = BedrockClient.from_settings(settings)
        if bedrock.available:
            explanation = _generate_explanation(
                impact.to_dict(),
                scenarios,
                window,
                bedrock
            )
    except Exception as e:
        pass
    
    return {
        "incident_id": incident_id,
        "node_id": incident.node_id,
        "cascade_impact": impact.to_dict(),
        "scenarios": scenarios,
        "decision_window": window,
        "ai_explanation": explanation,
        "incident_status": incident.status.value,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None
    }


@router.post("/incident/{incident_id}/execute-recovery")
def execute_recovery(
    incident_id: str,
    db: Session = Depends(get_db)
):
    """
    Execute recovery for incident.
    
    Calls existing RecoveryService - does NOT duplicate logic.
    """
    incident = db.query(Incident).filter_by(incident_id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    from domains.recovery.recovery_service import RecoveryService
    
    recovery_service = RecoveryService(db)
    result = recovery_service.recover_from_node_failure(incident)
    
    return {
        "incident_id": incident_id,
        "recovery_executed": True,
        "result": result,
        "message": "Recovery initiated using existing RecoveryService"
    }


def _generate_explanation(
    impact: dict,
    scenarios: dict,
    window: dict,
    bedrock: BedrockClient
) -> Optional[str]:
    """Generate AI explanation of impact and scenarios."""
    do_nothing = scenarios["scenarios"]["do_nothing"]
    recover_now = scenarios["scenarios"]["recover_now"]
    comparison = scenarios["comparison"]
    
    prompt = f"""Explain this incident impact and recovery recommendation in clear, customer-friendly language.

CURRENT IMPACT:
- {impact['affected_tasks'].__len__()} tasks affected
- {impact['affected_jobs'].__len__()} jobs impacted
- Estimated delay: {impact['estimated_delay_minutes']} minutes

DO NOTHING SCENARIO:
- Completion time: {do_nothing['estimated_completion_minutes']} minutes
- Deadline breaches: {do_nothing['deadline_breaches']}
- Cost: {do_nothing['estimated_cost_clstr']} CLSTR

RECOVER NOW SCENARIO:
- Completion time: {recover_now['estimated_completion_minutes']} minutes
- Deadline breaches: {recover_now['deadline_breaches']}
- Cost: {recover_now['estimated_cost_clstr']} CLSTR

DECISION WINDOW: {window['decision_window_seconds']} seconds
URGENCY: {window['urgency_level']}

Provide a concise 2-3 sentence explanation that:
1. Describes the current situation
2. Compares the outcomes
3. Recommends an action

Use plain language. No technical jargon."""
    
    try:
        response = bedrock.invoke_text(
            system_prompt="You are a system reliability advisor explaining incident impact.",
            user_message=prompt,
            max_tokens=200,
            temperature=0.3
        )
        return response
    except Exception as e:
        return None
