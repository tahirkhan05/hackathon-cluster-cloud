"""Tasks API router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

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


@router.post("/poll")
def poll_for_task(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Poll for next available task for a node.
    
    Finds a PENDING task, assigns it to the node, and returns it.
    Returns 404 if no tasks available.
    """
    node_id = payload.get("node_id")
    
    if not node_id:
        raise HTTPException(status_code=400, detail="node_id required")
    
    # First check if there are already assigned tasks for this node
    task = TaskService.get_next_task_for_node(db, node_id)
    
    # If no assigned tasks, find a PENDING task and assign it
    if not task:
        pending_tasks = TaskService.get_pending_tasks(db, limit=1)
        if pending_tasks:
            task = pending_tasks[0]
            # Assign it to this node
            task = TaskService.assign_task_to_node(db, task.task_id, node_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="No tasks available")
    
    return task


@router.put("/{task_id}/status")
def update_task_status(
    task_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update task status and metadata.
    
    Used by node agents to report status changes.
    """
    new_status = payload.get("status")
    result = payload.get("result")
    error_message = payload.get("error_message")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="status required")
    
    # Extract result_url from result dict if it's a dict
    result_url = None
    if result:
        if isinstance(result, dict):
            # Try to get output_path or filename
            result_url = result.get("output_path") or result.get("filename")
        elif isinstance(result, str):
            result_url = result
    
    try:
        task = TaskService.transition_task_status(
            db,
            task_id,
            TaskStatus[new_status],
            error_message=error_message,
            result_url=result_url
        )
        
        return {"task_id": task.task_id, "status": task.status}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")


@router.post("/{task_id}/progress")
def report_progress(
    task_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Report task progress.
    
    Used by node agents to send progress updates.
    """
    progress_percent = payload.get("progress_percent", 0)
    message = payload.get("message", "")
    
    try:
        task = TaskService.update_task_progress(
            db,
            task_id,
            progress_percent,
            message
        )
        
        return {
            "task_id": task.task_id,
            "progress_percent": progress_percent,
            "message": message
        }
        
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
