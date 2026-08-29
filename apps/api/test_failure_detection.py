"""
Tests for Failure Detection - Phase 6

Run with: pytest test_failure_detection.py -v
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from domains.nodes.models import Node, NodeStatus
from domains.tasks.models import Task, TaskStatus
from domains.jobs.models import Job, JobStatus
from domains.incidents.models import Incident, IncidentStatus
from domains.nodes.failure_detector import FailureDetector

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_failure_detection.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    from domains.workloads.seed import seed_workload_types
    db = next(get_test_db())
    seed_workload_types(db)
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_node(
    db,
    provider_id: str,
    last_heartbeat: datetime,
    status: NodeStatus = NodeStatus.AVAILABLE
):
    """Helper to create test node."""
    node = Node(
        provider_id=provider_id,
        capabilities={
            "cpu_cores_logical": 8,
            "ram_total_gb": 16.0
        },
        status=status,
        is_healthy=True,
        last_heartbeat_at=last_heartbeat,
        reliability_score=0.95,
        cost_per_task_clstr=10.0,
        max_concurrent_tasks=4,
        current_task_count=0
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def create_test_job(db):
    """Helper to create test job."""
    job = Job(
        customer_id="test-customer",
        workload_type="frame_rendering",
        parameters={"frame_count": 10},
        budget_clstr=1000.0,
        status=JobStatus.RUNNING
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_test_task(db, job_id: str, node_id: str, status: TaskStatus):
    """Helper to create test task."""
    task = Task(
        job_id=job_id,
        task_number=1,
        parameters={"frame_number": 0},
        node_id=node_id,
        status=status,
        max_retries=3
    )
    
    if status == TaskStatus.RUNNING:
        task.started_at = datetime.utcnow()
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task



def test_detect_missed_heartbeat():
    """Test detection of node with missed heartbeat."""
    db = next(get_test_db())
    
    old_heartbeat = datetime.utcnow() - timedelta(seconds=60)
    node = create_test_node(db, "node-timeout", old_heartbeat)
    
    detector = FailureDetector(db)
    failed_nodes = detector.detect_failed_nodes()
    
    assert len(failed_nodes) == 1
    assert failed_nodes[0][0].node_id == node.node_id


def test_delayed_heartbeat_within_threshold():
    """Test that delayed but within-threshold heartbeat doesn't trigger failure."""
    db = next(get_test_db())
    
    recent_heartbeat = datetime.utcnow() - timedelta(seconds=20)
    node = create_test_node(db, "node-ok", recent_heartbeat)
    
    detector = FailureDetector(db)
    failed_nodes = detector.detect_failed_nodes()
    
    assert len(failed_nodes) == 0
    
    db.refresh(node)
    assert node.status == NodeStatus.AVAILABLE
    assert node.is_healthy == True


def test_mark_node_failed_creates_incident():
    """Test marking node failed creates incident."""
    db = next(get_test_db())
    
    old_heartbeat = datetime.utcnow() - timedelta(seconds=60)
    node = create_test_node(db, "node-fail", old_heartbeat)
    
    job = create_test_job(db)
    task1 = create_test_task(db, job.job_id, node.node_id, TaskStatus.RUNNING)
    task2 = create_test_task(db, job.job_id, node.node_id, TaskStatus.ASSIGNED)
    
    detector = FailureDetector(db)
    incident = detector.mark_node_failed(node, [task1, task2])
    
    db.refresh(node)
    assert node.status == NodeStatus.OFFLINE
    assert node.is_healthy == False
    assert node.failure_count == 1
    
    assert incident is not None
    assert incident.incident_type == "node_failure"
    assert incident.node_id == node.node_id
    assert incident.status == IncidentStatus.OPEN
    assert incident.metadata["incomplete_task_count"] == 2
    assert task1.task_id in incident.metadata["incomplete_task_ids"]
    assert task2.task_id in incident.metadata["incomplete_task_ids"]


def test_mark_node_failed_idempotent():
    """Test marking node failed is idempotent (no duplicate incidents)."""
    db = next(get_test_db())
    
    old_heartbeat = datetime.utcnow() - timedelta(seconds=60)
    node = create_test_node(db, "node-fail", old_heartbeat)
    
    detector = FailureDetector(db)
    
    incident1 = detector.mark_node_failed(node, [])
    
    incident2 = detector.mark_node_failed(node, [])
    
    assert incident1.incident_id == incident2.incident_id
    
    incidents = db.query(Incident).filter(
        Incident.node_id == node.node_id,
        Incident.incident_type == "node_failure"
    ).all()
    
    assert len(incidents) == 1


def test_detect_recovered_node():
    """Test detection of recovered node."""
    db = next(get_test_db())
    
    recent_heartbeat = datetime.utcnow() - timedelta(seconds=5)
    node = create_test_node(db, "node-recover", recent_heartbeat, status=NodeStatus.OFFLINE)
    node.is_healthy = False
    db.commit()
    
    detector = FailureDetector(db)
    recovered_nodes = detector.detect_recovered_nodes()
    
    assert len(recovered_nodes) == 1
    assert recovered_nodes[0].node_id == node.node_id


def test_mark_node_recovered():
    """Test marking node as recovered."""
    db = next(get_test_db())
    
    recent_heartbeat = datetime.utcnow() - timedelta(seconds=5)
    node = create_test_node(db, "node-recover", recent_heartbeat, status=NodeStatus.OFFLINE)
    node.is_healthy = False
    db.commit()
    
    incident = Incident(
        incident_type="node_failure",
        severity="MEDIUM",
        description="Node failed",
        node_id=node.node_id,
        status=IncidentStatus.OPEN
    )
    db.add(incident)
    db.commit()
    
    detector = FailureDetector(db)
    resolved_incident = detector.mark_node_recovered(node)
    
    db.refresh(node)
    assert node.status == NodeStatus.AVAILABLE
    assert node.is_healthy == True
    
    db.refresh(incident)
    assert incident.status == IncidentStatus.RESOLVED
    assert incident.resolved_at is not None


def test_recovery_grace_period():
    """Test recovery grace period prevents premature recovery."""
    db = next(get_test_db())
    
    very_recent = datetime.utcnow() - timedelta(seconds=2)
    node = create_test_node(db, "node-flapping", very_recent, status=NodeStatus.OFFLINE)
    
    detector = FailureDetector(db)
    recovered_nodes = detector.detect_recovered_nodes()
    
    assert len(recovered_nodes) == 0


def test_stale_task_detection():
    """Test detection of stale (zombie) tasks."""
    db = next(get_test_db())
    
    node = create_test_node(db, "node-1", datetime.utcnow())
    job = create_test_job(db)
    
    task = create_test_task(db, job.job_id, node.node_id, TaskStatus.RUNNING)
    task.started_at = datetime.utcnow() - timedelta(seconds=400)
    db.commit()
    
    detector = FailureDetector(db)
    stale_tasks = detector.check_for_stale_tasks(task_timeout_seconds=300)
    
    assert len(stale_tasks) == 1
    assert stale_tasks[0].task_id == task.task_id


def test_stale_task_incident_creation():
    """Test creation of incident for stale task."""
    db = next(get_test_db())
    
    node = create_test_node(db, "node-1", datetime.utcnow())
    job = create_test_job(db)
    
    task = create_test_task(db, job.job_id, node.node_id, TaskStatus.RUNNING)
    task.started_at = datetime.utcnow() - timedelta(seconds=400)
    db.commit()
    
    detector = FailureDetector(db)
    incident = detector.create_stale_task_incident(task)
    
    assert incident.incident_type == "task_timeout"
    assert incident.task_id == task.task_id
    assert incident.node_id == node.node_id
    assert incident.status == IncidentStatus.OPEN


def test_stale_task_incident_idempotent():
    """Test stale task incident creation is idempotent."""
    db = next(get_test_db())
    
    node = create_test_node(db, "node-1", datetime.utcnow())
    job = create_test_job(db)
    
    task = create_test_task(db, job.job_id, node.node_id, TaskStatus.RUNNING)
    task.started_at = datetime.utcnow() - timedelta(seconds=400)
    db.commit()
    
    detector = FailureDetector(db)
    
    incident1 = detector.create_stale_task_incident(task)
    incident2 = detector.create_stale_task_incident(task)
    
    assert incident1.incident_id == incident2.incident_id


def test_full_detection_cycle():
    """Test complete detection cycle."""
    db = next(get_test_db())
    
    now = datetime.utcnow()
    
    failed_node = create_test_node(
        db, "node-failed",
        now - timedelta(seconds=60),
        NodeStatus.AVAILABLE
    )
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, TaskStatus.RUNNING)
    
    recovered_node = create_test_node(
        db, "node-recovered",
        now - timedelta(seconds=5),
        NodeStatus.OFFLINE
    )
    recovered_node.is_healthy = False
    db.commit()
    
    old_incident = Incident(
        incident_type="node_failure",
        severity="MEDIUM",
        description="Node failed",
        node_id=recovered_node.node_id,
        status=IncidentStatus.OPEN
    )
    db.add(old_incident)
    db.commit()
    
    detector = FailureDetector(db)
    summary = detector.run_detection_cycle()
    
    assert summary["nodes_failed"] == 1
    assert summary["nodes_recovered"] == 1
    assert summary["incidents_created"] == 1
    assert summary["incidents_resolved"] == 1
    
    db.refresh(failed_node)
    assert failed_node.status == NodeStatus.OFFLINE
    assert failed_node.is_healthy == False
    
    db.refresh(recovered_node)
    assert recovered_node.status == NodeStatus.AVAILABLE
    assert recovered_node.is_healthy == True


def test_no_false_positives():
    """Test that healthy nodes are not flagged as failed."""
    db = next(get_test_db())
    
    node1 = create_test_node(db, "node-1", datetime.utcnow())
    node2 = create_test_node(db, "node-2", datetime.utcnow() - timedelta(seconds=10))
    node3 = create_test_node(db, "node-3", datetime.utcnow() - timedelta(seconds=25))
    
    detector = FailureDetector(db)
    failed_nodes = detector.detect_failed_nodes()
    
    assert len(failed_nodes) == 0
    
    summary = detector.run_detection_cycle()
    
    assert summary["nodes_failed"] == 0
    assert summary["incidents_created"] == 0


def test_only_available_busy_nodes_detected():
    """Test that only AVAILABLE/BUSY nodes are detected as failed (not already OFFLINE)."""
    db = next(get_test_db())
    
    old_time = datetime.utcnow() - timedelta(seconds=60)
    
    node_available = create_test_node(db, "node-avail", old_time, NodeStatus.AVAILABLE)
    node_busy = create_test_node(db, "node-busy", old_time, NodeStatus.BUSY)
    node_offline = create_test_node(db, "node-offline", old_time, NodeStatus.OFFLINE)
    
    detector = FailureDetector(db)
    failed_nodes = detector.detect_failed_nodes()
    
    failed_node_ids = [node.node_id for node, _ in failed_nodes]
    
    assert node_available.node_id in failed_node_ids
    assert node_busy.node_id in failed_node_ids
    assert node_offline.node_id not in failed_node_ids
    assert len(failed_nodes) == 2


def test_identify_incomplete_tasks():
    """Test identification of incomplete tasks on failed node."""
    db = next(get_test_db())
    
    node = create_test_node(db, "node-fail", datetime.utcnow() - timedelta(seconds=60))
    job = create_test_job(db)
    
    task_assigned = create_test_task(db, job.job_id, node.node_id, TaskStatus.ASSIGNED)
    task_running = create_test_task(db, job.job_id, node.node_id, TaskStatus.RUNNING)
    
    task_completed = Task(
        job_id=job.job_id,
        task_number=3,
        parameters={"frame_number": 2},
        node_id=node.node_id,
        status=TaskStatus.COMPLETED
    )
    db.add(task_completed)
    db.commit()
    
    detector = FailureDetector(db)
    incomplete = detector._get_incomplete_tasks(node.node_id)
    
    incomplete_ids = [t.task_id for t in incomplete]
    
    assert task_assigned.task_id in incomplete_ids
    assert task_running.task_id in incomplete_ids
    assert task_completed.task_id not in incomplete_ids
    assert len(incomplete) == 2


def test_detection_cycle_idempotent():
    """Test detection cycle can be run multiple times safely."""
    db = next(get_test_db())
    
    old_time = datetime.utcnow() - timedelta(seconds=60)
    node = create_test_node(db, "node-fail", old_time)
    
    detector = FailureDetector(db)
    
    summary1 = detector.run_detection_cycle()
    summary2 = detector.run_detection_cycle()
    summary3 = detector.run_detection_cycle()
    
    assert summary1["nodes_failed"] == 1
    assert summary1["incidents_created"] == 1
    
    assert summary2["nodes_failed"] == 0
    assert summary2["incidents_created"] == 0
    
    assert summary3["nodes_failed"] == 0
    assert summary3["incidents_created"] == 0
    
    incidents = db.query(Incident).filter(
        Incident.node_id == node.node_id
    ).all()
    
    assert len(incidents) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
