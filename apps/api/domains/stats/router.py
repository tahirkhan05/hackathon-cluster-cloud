"""
System statistics router.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from domains.nodes.models import Node
from domains.jobs.models import Job
from domains.tasks.models import Task
from domains.ledger.models import Transaction

router = APIRouter()


@router.get("")
async def get_system_stats(db: Session = Depends(get_db)):
    """
    Get overall system statistics.
    """
    # Node stats
    total_nodes = db.query(func.count(Node.node_id)).scalar() or 0
    healthy_nodes = db.query(func.count(Node.node_id)).filter(
        Node.status == "HEALTHY"
    ).scalar() or 0
    
    # Job stats
    total_jobs = db.query(func.count(Job.job_id)).scalar() or 0
    active_jobs = db.query(func.count(Job.job_id)).filter(
        Job.status.in_(["RUNNING", "ALLOCATED", "SCHEDULING"])
    ).scalar() or 0
    
    # Task stats
    total_tasks_completed = db.query(func.count(Task.task_id)).filter(
        Task.status == "COMPLETED"
    ).scalar() or 0
    
    # Economic stats
    total_clstr_transacted = db.query(
        func.sum(Transaction.amount_clstr)
    ).scalar() or 0
    
    return {
        "total_nodes": total_nodes,
        "healthy_nodes": healthy_nodes,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_tasks_completed": total_tasks_completed,
        "total_clstr_transacted": float(total_clstr_transacted)
    }
