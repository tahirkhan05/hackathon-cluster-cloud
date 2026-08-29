"""Nodes API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from domains.nodes.models import NodeStatus
from domains.nodes.schemas import NodeRegister, NodeResponse, NodeHeartbeat, NodeListResponse
from domains.nodes.service import NodeService
from domains.nodes.failure_detector import FailureDetector

router = APIRouter()


@router.post("/register", response_model=NodeResponse, status_code=200)
def register_node(node_data: NodeRegister, db: Session = Depends(get_db)):
    """
    Register a new node or reactivate existing one.
    
    If a node with the same provider_id exists, it will be reactivated
    with updated capabilities. Otherwise, a new node is created.
    """
    try:
        node = NodeService.register_node(db, node_data)
        return node
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{node_id}/heartbeat")
def node_heartbeat(
    node_id: str,
    heartbeat: NodeHeartbeat,
    db: Session = Depends(get_db)
):
    """
    Record node heartbeat.
    
    Updates last_heartbeat timestamp and node status based on
    health and capacity.
    """
    try:
        result = NodeService.process_heartbeat(db, node_id, heartbeat)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=NodeListResponse)
def list_nodes(
    status: Optional[NodeStatus] = Query(None, description="Filter by status"),
    available_only: bool = Query(False, description="Only available nodes"),
    db: Session = Depends(get_db)
):
    """
    List all registered nodes with optional filtering.
    
    Query parameters:
    - status: Filter by node status (available, busy, offline)
    - available_only: Only return nodes that can accept tasks
    """
    nodes = NodeService.list_nodes(db, status=status, available_only=available_only)
    return {"nodes": nodes, "total": len(nodes)}


@router.get("/statistics")
def get_node_statistics(db: Session = Depends(get_db)):
    """
    Get aggregated node statistics.
    
    Returns counts by status and overall health metrics.
    """
    return NodeService.get_node_statistics(db)


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific node."""
    node = NodeService.get_node(db, node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return node


@router.post("/maintenance/detect-stale")
def detect_stale_nodes(db: Session = Depends(get_db)):
    """
    Detect and mark stale nodes as offline.
    
    A node is considered stale if its last heartbeat exceeds
    the configured timeout threshold.
    
    This endpoint is intended for periodic maintenance tasks.
    """
    count = NodeService.mark_stale_nodes_offline(db)
    return {
        "marked_offline": count,
        "message": f"Marked {count} stale nodes offline"
    }


@router.post("/maintenance/detect-failures")
def detect_failures(db: Session = Depends(get_db)):
    """
    Run failure detection cycle.
    
    Detects:
    - Nodes with missed heartbeats
    - Recovered nodes
    - Stale (zombie) tasks
    
    Creates incidents and updates node status.
    Idempotent: safe to call repeatedly.
    """
    detector = FailureDetector(db)
    summary = detector.run_detection_cycle()
    return summary


@router.get("/health/status")
def get_health_status(db: Session = Depends(get_db)):
    """
    Get overall cluster health status.
    
    Returns counts of healthy/unhealthy nodes and open incidents.
    """
    from domains.incidents.models import Incident, IncidentStatus
    from domains.nodes.models import Node
    
    nodes = db.query(Node).all()
    
    healthy_count = sum(1 for n in nodes if n.is_healthy)
    unhealthy_count = len(nodes) - healthy_count
    
    open_incidents = db.query(Incident).filter(
        Incident.status == IncidentStatus.OPEN
    ).count()
    
    return {
        "total_nodes": len(nodes),
        "healthy_nodes": healthy_count,
        "unhealthy_nodes": unhealthy_count,
        "open_incidents": open_incidents,
        "cluster_healthy": unhealthy_count == 0 and open_incidents == 0
    }
