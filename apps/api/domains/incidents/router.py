"""Incidents API router."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_incidents():
    """List all incidents."""
    return {"incidents": []}


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get incident by ID."""
    return {"incident_id": incident_id, "status": "detected"}
