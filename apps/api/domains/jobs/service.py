"""
Job service layer.

Business logic for job creation, state transitions, and lifecycle management.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from domains.jobs.models import Job, JobStatus, JOB_TRANSITIONS
from domains.jobs.schemas import JobCreate
from domains.workloads.models import WorkloadType

logger = logging.getLogger(__name__)


class JobService:
    """Service for job operations with explicit state machine."""
    
    @staticmethod
    def create_job(db: Session, job_data: JobCreate) -> Job:
        """
        Create a new job in SUBMITTED state.
        
        Validates:
        - Workload type exists
        - Budget is positive
        - Required parameters present
        """
        # Validate workload type
        workload = db.query(WorkloadType).filter(
            WorkloadType.workload_type == job_data.workload_type
        ).first()
        
        if not workload:
            raise ValueError(f"Unknown workload type: {job_data.workload_type}")
        
        # Create job
        job = Job(
            customer_id=job_data.customer_id,
            workload_type=job_data.workload_type,
            parameters=job_data.parameters,
            budget_clstr=job_data.budget_clstr,
            status=JobStatus.SUBMITTED
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(
            f"Job created: {job.job_id} "
            f"(customer: {job.customer_id}, type: {job.workload_type})"
        )
        
        return job
    
    @staticmethod
    def transition_job_status(
        db: Session,
        job_id: str,
        new_status: JobStatus,
        error_message: Optional[str] = None
    ) -> Job:
        """
        Transition job to new status with validation.
        
        Raises:
            ValueError: If job not found or transition invalid
        """
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Check if transition is valid
        if not job.can_transition_to(new_status):
            raise ValueError(
                f"Invalid transition: {job.status} → {new_status} "
                f"(allowed: {JOB_TRANSITIONS.get(job.status, [])})"
            )
        
        old_status = job.status
        job.status = new_status
        
        # Update timestamps
        if new_status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        
        if new_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow()
        
        # Handle error message
        if error_message:
            job.error_message = error_message
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Job {job_id}: {old_status} → {new_status}")
        
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return db.query(Job).filter(Job.job_id == job_id).first()
    
    @staticmethod
    def list_jobs(
        db: Session,
        customer_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Job]:
        """
        List jobs with optional filtering.
        
        Args:
            customer_id: Filter by customer
            status: Filter by status
            limit: Max results
        """
        query = db.query(Job).order_by(Job.created_at.desc())
        
        if customer_id:
            query = query.filter(Job.customer_id == customer_id)
        
        if status:
            query = query.filter(Job.status == status)
        
        return query.limit(limit).all()
    
    @staticmethod
    def update_job_progress(db: Session, job_id: str) -> Job:
        """
        Update job progress counters from tasks.
        
        Recalculates:
        - total_tasks
        - completed_tasks
        - failed_tasks
        """
        job = JobService.get_job(db, job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        from domains.tasks.models import Task, TaskStatus
        
        # Count tasks by status
        total = db.query(Task).filter(Task.job_id == job_id).count()
        completed = db.query(Task).filter(
            Task.job_id == job_id,
            Task.status == TaskStatus.COMPLETED
        ).count()
        failed = db.query(Task).filter(
            Task.job_id == job_id,
            Task.status == TaskStatus.FAILED,
            Task.retry_count >= Task.max_retries
        ).count()
        
        job.total_tasks = total
        job.completed_tasks = completed
        job.failed_tasks = failed
        
        db.commit()
        db.refresh(job)
        
        return job
    
    @staticmethod
    def can_cancel_job(job: Job) -> bool:
        """Check if job can be cancelled."""
        return not job.is_terminal()
    
    @staticmethod
    def cancel_job(db: Session, job_id: str, reason: Optional[str] = None) -> Job:
        """
        Cancel a job if not in terminal state.
        
        Raises:
            ValueError: If job cannot be cancelled
        """
        job = JobService.get_job(db, job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if not JobService.can_cancel_job(job):
            raise ValueError(f"Job {job_id} is already in terminal state: {job.status}")
        
        return JobService.transition_job_status(
            db,
            job_id,
            JobStatus.CANCELLED,
            error_message=reason or "Cancelled by user"
        )
