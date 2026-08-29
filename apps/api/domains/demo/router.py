"""
Demo endpoints for hackathon presentation.

⚠️ WARNING: These endpoints should be DISABLED in production.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os

from database import get_db
from domains.nodes.models import Node, NodeStatus
from domains.incidents.models import Incident, IncidentType, IncidentStatus
from domains.tasks.models import Task, TaskStatus
from domains.recovery.recovery_service import RecoveryService
from domains.websocket.events import EventFactory
from domains.websocket.router import broadcast_event_async
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def check_demo_allowed():
    """
    Check if demo endpoints are allowed.
    
    Raises HTTPException if in production environment.
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production" and not os.getenv("ENABLE_DEMO_ENDPOINTS", "false").lower() == "true":
        raise HTTPException(
            status_code=403,
            detail="Demo endpoints are disabled in production. Set ENABLE_DEMO_ENDPOINTS=true to override."
        )


@router.post("/simulate-failure/{node_id}")
async def simulate_node_failure(node_id: str, db: Session = Depends(get_db)):
    """
    Simulate a node failure for demo purposes.
    
    ⚠️ DEMO ONLY - Disable in production
    """
    check_demo_allowed()
    
    logger.warning(f"DEMO: Simulating failure for node {node_id}")
    
    node = db.query(Node).filter_by(node_id=node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Mark node as unhealthy
    node.status = NodeStatus.UNHEALTHY
    node.is_healthy = False
    node.last_heartbeat = datetime.utcnow()
    db.commit()
    
    # Broadcast node failure event
    event = EventFactory.node_failed(
        node_id=node_id,
        incident_id="pending",
        reason="Manual demo failure simulation"
    )
    await broadcast_event_async(event)
    
    # Find active tasks on this node
    active_tasks = db.query(Task).filter(
        Task.assigned_node_id == node_id,
        Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING])
    ).all()
    
    if not active_tasks:
        logger.info(f"DEMO: No active tasks on node {node_id}")
        return {
            "success": True,
            "message": "Node marked as failed",
            "affected_tasks": 0
        }
    
    job_id = active_tasks[0].job_id
    
    # Create incident
    incident = Incident(
        incident_type=IncidentType.NODE_CRASH,
        status=IncidentStatus.DETECTED,
        node_id=node_id,
        description=f"Demo: Simulated failure of node {node.provider_id}",
        detected_at=datetime.utcnow(),
        context={
            "incomplete_task_ids": [task.task_id for task in active_tasks]
        }
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    logger.info(
        f"DEMO: Created incident {incident.incident_id} "
        f"with {len(active_tasks)} affected tasks"
    )
    
    # Broadcast recovery started event
    event = EventFactory.recovery_started(
        incident_id=incident.incident_id,
        job_id=job_id,
        affected_task_count=len(active_tasks)
    )
    await broadcast_event_async(event)
    
    # Trigger automatic recovery
    try:
        recovery_service = RecoveryService(db)
        recovery_result = recovery_service.recover_from_node_failure(incident)
        
        logger.info(f"DEMO: Recovery result: {recovery_result}")
        
        return {
            "success": True,
            "message": "Node failure simulated and recovery triggered",
            "incident_id": incident.incident_id,
            "affected_tasks": len(active_tasks),
            "recovery": recovery_result
        }
    
    except Exception as e:
        logger.error(f"DEMO: Recovery failed: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Recovery failed: {str(e)}",
            "incident_id": incident.incident_id,
            "affected_tasks": len(active_tasks),
            "error": str(e)
        }


@router.post("/reset")
async def reset_demo(db: Session = Depends(get_db)):
    """
    Reset demo state.
    
    ⚠️ DEMO ONLY - Disable in production
    """
    check_demo_allowed()
    
    logger.warning("DEMO: Resetting demo state")
    
    # Reset all nodes to healthy
    nodes = db.query(Node).all()
    for node in nodes:
        node.status = NodeStatus.HEALTHY
        node.is_healthy = True
    
    db.commit()
    
    return {
        "success": True,
        "message": "Demo state reset",
        "nodes_reset": len(nodes)
    }


@router.get("/status")
async def demo_status(db: Session = Depends(get_db)):
    """Get demo status overview."""
    nodes = db.query(Node).all()
    incidents = db.query(Incident).filter(
        Incident.status != IncidentStatus.RESOLVED
    ).all()
    
    return {
        "total_nodes": len(nodes),
        "healthy_nodes": len([n for n in nodes if n.status == NodeStatus.HEALTHY]),
        "unhealthy_nodes": len([n for n in nodes if n.status != NodeStatus.HEALTHY]),
        "active_incidents": len(incidents),
        "incidents": [
            {
                "incident_id": inc.incident_id,
                "type": inc.incident_type.value,
                "status": inc.status.value,
                "affected_node": inc.related_node_id,
                "affected_tasks": len(inc.metadata.get("incomplete_task_ids", []))
            }
            for inc in incidents
        ]
    }
