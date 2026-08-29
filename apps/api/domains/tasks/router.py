"""Tasks API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from domains.tasks.models import TaskStatus
from domains.tasks.schemas import TaskCreate, TaskResponse, TaskListResponse, TaskUpdate
from domains.tasks.service import TaskService

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task in PENDING state.
    
    Idempotent: returns existing task if job_id + task_number exists.
    """
    try:
        task = TaskService.create_task(db, task_data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    job_id: Optional[str] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List tasks, optionally filtered by job and/or status.
    """
    if job_id:
        tasks = TaskService.list_tasks_for_job(db, job_id, status=status)
    elif status:
        # This would need a different service method for global status filtering
        raise HTTPException(status_code=400, detail="Must specify job_id when filtering by status")
    else:
        tasks = TaskService.get_pending_tasks(db, limit=100)
    
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get detailed task information."""
    task = TaskService.get_task(db, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.post("/{task_id}/transition")
def transition_task(
    task_id: str,
    new_status: TaskStatus,
    node_id: Optional[str] = None,
    error_message: Optional[str] = None,
    result_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Transition task to new status.
    
    Validates state machine transitions.
    """
    try:
        task = TaskService.transition_task_status(
            db, task_id, new_status,
            node_id=node_id,
            error_message=error_message,
            result_url=result_url
        )
        return {"task_id": task.task_id, "status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/assign")
def assign_task(
    task_id: str,
    node_id: str,
    db: Session = Depends(get_db)
):
    """Assign a PENDING task to a node."""
    try:
        task = TaskService.assign_task_to_node(db, task_id, node_id)
        return {"task_id": task.task_id, "node_id": task.node_id, "status": task.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/retry")
def retry_task(task_id: str, db: Session = Depends(get_db)):
    """Retry a FAILED task if retries remain."""
    try:
        task = TaskService.retry_task(db, task_id)
        return {"task_id": task.task_id, "status": task.status, "retry_count": task.retry_count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
