"""Workloads API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_workload_types():
    """List available workload types."""
    return {
        "workload_types": [
            {
                "type": "frame_rendering",
                "name": "3D Frame Rendering",
                "parallelizable": True,
                "description": "Distributed rendering of 3D animation frames"
            }
        ]
    }
