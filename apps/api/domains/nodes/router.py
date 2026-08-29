"""Nodes API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_nodes():
    """List all nodes."""
    return {"nodes": []}


@router.post("/register")
async def register_node():
    """Register new node."""
    return {"message": "Node registration endpoint - to be implemented"}


@router.post("/{node_id}/heartbeat")
async def node_heartbeat(node_id: str):
    """Record node heartbeat."""
    return {"node_id": node_id, "status": "alive"}
