"""Tasks API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tasks():
    """List all tasks."""
    return {"tasks": []}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get task by ID."""
    return {"task_id": task_id, "status": "queued"}
