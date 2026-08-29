"""
Task service layer.

Business logic for task creation, assignment, and state transitions.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from domains.tasks.models import Task, TaskStatus, TASK_TRANSITIONS
from domains.tasks.schemas import TaskCreate
from domains.jobs.models import Job

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task operations with explicit state machine."""
    
    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """
        Create a new task in PENDING state.
        
        Validates:
        - Job exists
        - Task number is unique within job
        """
        # Validate job exists
        job = db.query(Job).filter(Job.job_id == task_data.job_id).first()
        
        if not job:
            raise ValueError(f"Job not found: {task_data.job_id}")
        
        # Check for duplicate task number
        existing = db.query(Task).filter(
            Task.job_id == task_data.job_id,
            Task.task_number == task_data.task_number
        ).first()
        
        if existing:
            # Idempotent: return existing task
            logger.info(f"Task {existing.task_id} already exists (idempotent)")
            return existing
        
        # Create task
        task = Task(
            job_id=task_data.job_id,
            task_number=task_data.task_number,
            parameters=task_data.parameters,
            max_retries=task_data.max_retries,
            status=TaskStatus.PENDING
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task created: {task.task_id} (job: {task.job_id}, #: {task.task_number})")
        
        return task
    
    @staticmethod
    def create_tasks_for_job(
        db: Session,
        job_id: str,
        task_count: int,
        base_parameters: dict
    ) -> List[Task]:
        """
        Create multiple tasks for a job (e.g., one per frame).
        
        Idempotent: skips existing tasks.
        """
        tasks = []
        
        for i in range(task_count):
            task_params = {**base_parameters, "task_index": i}
            
            task_data = TaskCreate(
                job_id=job_id,
                task_number=i + 1,
                parameters=task_params,
                max_retries=3
            )
            
            task = TaskService.create_task(db, task_data)
            tasks.append(task)
        
        logger.info(f"Created {len(tasks)} tasks for job {job_id}")
        return tasks
    
    @staticmethod
    def transition_task_status(
        db: Session,
        task_id: str,
        new_status: TaskStatus,
        node_id: Optional[str] = None,
        error_message: Optional[str] = None,
        result_url: Optional[str] = None
    ) -> Task:
        """
        Transition task to new status with validation.
        
        Raises:
            ValueError: If task not found or transition invalid
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Check if transition is valid
        if not task.can_transition_to(new_status):
            raise ValueError(
                f"Invalid transition: {task.status} → {new_status} "
                f"(allowed: {TASK_TRANSITIONS.get(task.status, [])})"
            )
        
        old_status = task.status
        task.status = new_status
        
        # Update timestamps and fields based on status
        if new_status == TaskStatus.ASSIGNED:
            task.assigned_at = datetime.utcnow()
            if node_id:
                task.node_id = node_id
        
        elif new_status == TaskStatus.RUNNING:
            task.started_at = datetime.utcnow()
        
        elif new_status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            if result_url:
                task.result_url = result_url
        
        elif new_status == TaskStatus.FAILED:
            task.last_error_at = datetime.utcnow()
            if error_message:
                task.error_message = error_message
        
        elif new_status == TaskStatus.RETRYING:
            task.retry_count += 1
            task.node_id = None  # Clear node assignment
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"Task {task_id}: {old_status} → {new_status}")
        
        return task
    
    @staticmethod
    def assign_task_to_node(db: Session, task_id: str, node_id: str) -> Task:
        """Assign a PENDING task to a node."""
        return TaskService.transition_task_status(
            db,
            task_id,
            TaskStatus.ASSIGNED,
            node_id=node_id
        )
    
    @staticmethod
    def retry_task(db: Session, task_id: str) -> Task:
        """
        Retry a FAILED task if retries remain.
        
        Raises:
            ValueError: If task cannot be retried
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if not task.can_retry:
            raise ValueError(
                f"Task {task_id} has exhausted retries "
                f"({task.retry_count}/{task.max_retries})"
            )
        
        return TaskService.transition_task_status(
            db,
            task_id,
            TaskStatus.RETRYING
        )
    
    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return db.query(Task).filter(Task.task_id == task_id).first()
    
    @staticmethod
    def list_tasks_for_job(
        db: Session,
        job_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """List all tasks for a job, optionally filtered by status."""
        query = db.query(Task).filter(Task.job_id == job_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.order_by(Task.task_number).all()
    
    @staticmethod
    def get_pending_tasks(db: Session, limit: int = 100) -> List[Task]:
        """Get tasks ready for assignment."""
        return db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).limit(limit).all()
    
    @staticmethod
    def complete_task(
        db: Session,
        task_id: str,
        result_url: str,
        result_metadata: Optional[dict] = None
    ) -> Task:
        """Mark task as completed with results."""
        task = TaskService.transition_task_status(
            db,
            task_id,
            TaskStatus.COMPLETED,
            result_url=result_url
        )
        
        if result_metadata:
            task.result_metadata = result_metadata
            db.commit()
            db.refresh(task)
        
        return task
    
    @staticmethod
    def fail_task(db: Session, task_id: str, error_message: str) -> Task:
        """Mark task as failed."""
        return TaskService.transition_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
    
    @staticmethod
    def get_next_task_for_node(db: Session, node_id: str) -> Optional[Task]:
        """
        Get next ASSIGNED task for a node.
        
        Returns the oldest assigned task for this node that hasn't started.
        """
        task = db.query(Task).filter(
            Task.node_id == node_id,
            Task.status == TaskStatus.ASSIGNED
        ).order_by(Task.assigned_at).first()
        
        if task:
            logger.info(f"Returning task {task.task_id} to node {node_id}")
        
        return task
    
    @staticmethod
    def update_task_progress(
        db: Session,
        task_id: str,
        progress_percent: int,
        message: str
    ) -> Task:
        """
        Update task progress information.
        
        Used for real-time progress reporting.
        """
        task = db.query(Task).filter(Task.task_id == task_id).first()
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Store progress in metadata
        if not task.result_metadata:
            task.result_metadata = {}
        
        task.result_metadata["progress_percent"] = progress_percent
        task.result_metadata["progress_message"] = message
        task.result_metadata["last_progress_update"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(task)
        
        logger.debug(f"Task {task_id} progress: {progress_percent}% - {message}")
        
        return task
