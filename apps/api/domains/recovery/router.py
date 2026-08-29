"""Recovery API router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from domains.recovery.recovery_service import RecoveryService
from domains.incidents.models import Incident

router = APIRouter()


@router.post("/recover/{incident_id}")
def recover_incident(incident_id: str, db: Session = Depends(get_db)):
    """
    Recover tasks from a specific incident.
    
    Automatically reassigns affected tasks to healthy nodes.
    """
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.incident_type != "node_failure":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot recover incident type: {incident.incident_type}"
        )
    
    recovery_service = RecoveryService(db)
    result = recovery_service.recover_from_node_failure(incident)
    
    return result


@router.post("/recover-all")
def recover_all_incidents(db: Session = Depends(get_db)):
    """
    Recover all open node failure incidents.
    
    Processes all open incidents and attempts recovery.
    """
    recovery_service = RecoveryService(db)
    result = recovery_service.recover_all_open_incidents()
    
    return result


@router.get("/status")
def get_recovery_status(db: Session = Depends(get_db)):
    """
    Get recovery system status.
    
    Returns counts of recoverable incidents and tasks.
    """
    from domains.incidents.models import IncidentStatus
    from domains.tasks.models import TaskStatus
    
    open_incidents = db.query(Incident).filter(
        Incident.status == IncidentStatus.OPEN,
        Incident.incident_type == "node_failure"
    ).count()
    
    from domains.tasks.models import Task
    tasks_needing_recovery = db.query(Task).filter(
        Task.status.in_([TaskStatus.FAILED]),
        Task.retry_count < Task.max_retries
    ).count()
    
    return {
        "open_incidents": open_incidents,
        "tasks_needing_recovery": tasks_needing_recovery,
        "recovery_enabled": True
    }
