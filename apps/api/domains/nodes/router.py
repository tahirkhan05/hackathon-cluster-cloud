"""Nodes API router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from domains.nodes.models import Node, NodeStatus
from domains.nodes.schemas import NodeRegister, NodeResponse, NodeHeartbeat, NodeListResponse
from domains.reliability.models import ReliabilityScore

router = APIRouter()


@router.post("/register", response_model=NodeResponse)
def register_node(node_data: NodeRegister, db: Session = Depends(get_db)):
    """Register a new node with the control plane."""
    
    # Check if node already exists
    existing = db.query(Node).filter(
        Node.provider_id == node_data.provider_id
    ).first()
    
    if existing:
        # Update existing node
        existing.status = NodeStatus.AVAILABLE
        existing.last_heartbeat = datetime.utcnow()
        existing.capabilities = node_data.capabilities
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new node
    node = Node(
        provider_id=node_data.provider_id,
        hostname=node_data.hostname,
        ip_address=node_data.ip_address,
        capabilities=node_data.capabilities,
        max_concurrent_tasks=node_data.max_concurrent_tasks,
        cost_per_task_clstr=node_data.cost_per_task_clstr,
        status=NodeStatus.AVAILABLE
    )
    
    db.add(node)
    db.flush()
    
    # Create reliability score
    reliability = ReliabilityScore(node_id=node.node_id)
    db.add(reliability)
    
    db.commit()
    db.refresh(node)
    
    return node


@router.post("/{node_id}/heartbeat")
def node_heartbeat(node_id: str, heartbeat: NodeHeartbeat, db: Session = Depends(get_db)):
    """Record node heartbeat."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node.last_heartbeat = datetime.utcnow()
    node.current_task_count = heartbeat.current_task_count
    node.is_healthy = heartbeat.is_healthy
    
    # Update status based on capacity
    if node.current_task_count >= node.max_concurrent_tasks:
        node.status = NodeStatus.BUSY
    elif node.is_healthy:
        node.status = NodeStatus.AVAILABLE
    else:
        node.status = NodeStatus.OFFLINE
    
    db.commit()
    
    return {"status": "ok", "node_id": node_id}


@router.get("/", response_model=NodeListResponse)
def list_nodes(db: Session = Depends(get_db)):
    """List all registered nodes."""
    nodes = db.query(Node).all()
    return {"nodes": nodes, "total": len(nodes)}


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, db: Session = Depends(get_db)):
    """Get node details."""
    node = db.query(Node).filter(Node.node_id == node_id).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return node
