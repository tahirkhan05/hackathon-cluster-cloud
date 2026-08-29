"""Reliability API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/nodes/{node_id}")
async def get_node_reliability(node_id: str):
    """Get reliability score for a node."""
    return {
        "node_id": node_id,
        "reliability_score": 0.95,
        "tasks_completed": 0,
        "tasks_failed": 0
    }
