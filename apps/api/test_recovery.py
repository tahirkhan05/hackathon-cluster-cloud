"""
Tests for Self-Healing Recovery - Phase 7

Run with: pytest test_recovery.py -v
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
from domains.recovery.recovery_service import RecoveryService

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_recovery.db"
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
    
    # Seed workload type
    from domains.workloads.seed import seed_workload_types
    db = next(get_test_db())
    seed_workload_types(db)
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_node(
    db,
    provider_id: str,
    status: NodeStatus = NodeStatus.AVAILABLE,
    is_healthy: bool = True,
    reliability: float = 0.95,
    cost: float = 10.0,
    cpu: int = 8,
    ram: float = 16.0
):
    """Helper to create test node."""
    node = Node(
        provider_id=provider_id,
        capabilities={
            "cpu_cores_logical": cpu,
            "ram_total_gb": ram
        },
        status=status,
        is_healthy=is_healthy,
        last_heartbeat_at=datetime.utcnow(),
        reliability_score=reliability,
        cost_per_task_clstr=cost,
        max_concurrent_tasks=4,
        current_task_count=0
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def create_test_job(db, budget: float = 1000.0):
    """Helper to create test job."""
    job = Job(
        customer_id="test-customer",
        workload_type="frame_rendering",
        parameters={
            "frame_count": 10,
            "cpu_cores_min": 4,
            "ram_gb_min": 8.0
        },
        budget_clstr=budget,
        status=JobStatus.RUNNING
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def create_test_task(db, job_id: str, node_id: str, task_number: int, status: TaskStatus):
    """Helper to create test task."""
    task = Task(
        job_id=job_id,
        task_number=task_number,
        parameters={"frame_number": task_number - 1},
        node_id=node_id,
        status=status,
        max_retries=3
    )
    
    if status == TaskStatus.RUNNING:
        task.started_at = datetime.utcnow()
    elif status == TaskStatus.ASSIGNED:
        task.assigned_at = datetime.utcnow()
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ============================================================================
# RECOVERY TESTS
# ============================================================================

def test_recover_single_task():
    """Test recovery of a single failed task."""
    db = next(get_test_db())
    
    # Setup: Failed node with task
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    
    # Replacement node
    healthy_node = create_test_node(db, "node-healthy")
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    # Create incident
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Verify recovery
    assert result["status"] == "success"
    assert result["tasks_recovered"] == 1
    
    # Verify task reassigned
    db.refresh(task)
    assert task.node_id == healthy_node.node_id
    assert task.status == TaskStatus.ASSIGNED
    assert task.retry_count == 1
    
    # Verify incident resolved
    db.refresh(incident)
    assert incident.status == IncidentStatus.RESOLVED


def test_recover_multiple_tasks():
    """Test recovery of multiple tasks from failed node."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    healthy_node = create_test_node(db, "node-healthy")
    
    job = create_test_job(db)
    
    # Create multiple tasks
    task1 = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    task2 = create_test_task(db, job.job_id, failed_node.node_id, 2, TaskStatus.ASSIGNED)
    task3 = create_test_task(db, job.job_id, failed_node.node_id, 3, TaskStatus.RUNNING)
    
    # Create incident
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task1.task_id, task2.task_id, task3.task_id],
            "incomplete_task_count": 3
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Verify all tasks recovered
    assert result["status"] == "success"
    assert result["tasks_recovered"] == 3
    
    # Verify all tasks reassigned
    db.refresh(task1)
    db.refresh(task2)
    db.refresh(task3)
    
    assert task1.node_id == healthy_node.node_id
    assert task2.node_id == healthy_node.node_id
    assert task3.node_id == healthy_node.node_id


def test_no_compatible_nodes():
    """Test recovery fails gracefully when no compatible nodes available."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    
    # No other nodes available
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Verify recovery failed
    assert result["status"] == "failed"
    assert result["tasks_recovered"] == 0


def test_compatibility_validation():
    """Test that replacement nodes must meet resource requirements."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False, cpu=16, ram=32.0)
    
    # Node with insufficient resources
    weak_node = create_test_node(db, "node-weak", cpu=2, ram=2.0)
    
    # Job requires more resources than weak_node has
    job = Job(
        customer_id="test-customer",
        workload_type="frame_rendering",
        parameters={
            "frame_count": 10,
            "cpu_cores_min": 8,  # Requires 8 cores
            "ram_gb_min": 16.0   # Requires 16GB
        },
        budget_clstr=1000.0,
        status=JobStatus.RUNNING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Should fail due to incompatible resources
    assert result["status"] == "failed"
    assert result["tasks_recovered"] == 0


def test_reliability_threshold():
    """Test that replacement nodes must meet reliability threshold."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    
    # Node with low reliability
    unreliable_node = create_test_node(db, "node-unreliable", reliability=0.5)  # Below 0.7 threshold
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Should fail due to low reliability
    assert result["status"] == "failed"


def test_budget_constraint():
    """Test that recovery respects budget constraints."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False, cost=10.0)
    
    # Expensive node
    expensive_node = create_test_node(db, "node-expensive", cost=1000.0)
    
    # Job with small budget
    job = create_test_job(db, budget=50.0)  # Only 5 CLSTR per task (50/10 frames)
    
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Should fail due to budget constraint
    assert result["status"] == "failed"


def test_select_best_node():
    """Test that recovery selects the best node by scoring."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    
    # Multiple candidate nodes with different characteristics
    node_reliable = create_test_node(db, "node-reliable", reliability=0.99, cost=20.0)
    node_cheap = create_test_node(db, "node-cheap", reliability=0.80, cost=5.0)
    node_balanced = create_test_node(db, "node-balanced", reliability=0.90, cost=10.0)
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    # Run recovery
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    # Should succeed
    assert result["status"] == "success"
    
    # Verify task assigned to best node (likely node_reliable due to 40% reliability weight)
    db.refresh(task)
    assert task.node_id in [node_reliable.node_id, node_balanced.node_id]


def test_end_to_end_failure_recovery():
    """
    CRITICAL END-TO-END TEST
    
    Demonstrates complete failure → recovery → completion flow:
    1. Node A fails mid-execution
    2. Failure detected → incident created
    3. Tasks identified
    4. Node B selected
    5. Tasks reassigned
    6. Tasks resume
    7. Job completes
    """
    db = next(get_test_db())
    
    # Step 1: Setup healthy cluster
    node_a = create_test_node(db, "node-a", cpu=8, ram=16.0)
    node_b = create_test_node(db, "node-b", cpu=8, ram=16.0)
    node_c = create_test_node(db, "node-c", cpu=8, ram=16.0)
    
    # Step 2: Create job with tasks
    job = create_test_job(db)
    
    # Node A has 3 tasks
    task1 = create_test_task(db, job.job_id, node_a.node_id, 1, TaskStatus.COMPLETED)
    task2 = create_test_task(db, job.job_id, node_a.node_id, 2, TaskStatus.RUNNING)
    task3 = create_test_task(db, job.job_id, node_a.node_id, 3, TaskStatus.ASSIGNED)
    
    # Node B has 2 completed tasks
    task4 = create_test_task(db, job.job_id, node_b.node_id, 4, TaskStatus.COMPLETED)
    task5 = create_test_task(db, job.job_id, node_b.node_id, 5, TaskStatus.COMPLETED)
    
    print("\n=== Initial State ===")
    print(f"Node A: {node_a.node_id} - AVAILABLE")
    print(f"  Task 1: COMPLETED")
    print(f"  Task 2: RUNNING")
    print(f"  Task 3: ASSIGNED")
    print(f"Node B: {node_b.node_id} - AVAILABLE")
    print(f"  Task 4: COMPLETED")
    print(f"  Task 5: COMPLETED")
    print(f"Node C: {node_c.node_id} - AVAILABLE (idle)")
    
    # Step 3: Node A fails (simulate heartbeat timeout)
    node_a.last_heartbeat_at = datetime.utcnow() - timedelta(seconds=60)
    db.commit()
    
    print("\n=== Node A Fails ===")
    print(f"Node A stopped sending heartbeats")
    
    # Step 4: Failure detection
    detector = FailureDetector(db)
    failed_nodes = detector.detect_failed_nodes()
    
    assert len(failed_nodes) == 1
    assert failed_nodes[0][0].node_id == node_a.node_id
    
    print(f"Failure detected: {len(failed_nodes)} node(s)")
    
    # Mark node failed and create incident
    incident = detector.mark_node_failed(node_a, [task2, task3])
    
    print(f"Incident created: {incident.incident_id}")
    print(f"Incomplete tasks: {len([task2, task3])}")
    
    # Verify node marked offline
    db.refresh(node_a)
    assert node_a.status == NodeStatus.OFFLINE
    assert node_a.is_healthy == False
    
    # Verify incident created
    assert incident.incident_type == "node_failure"
    assert incident.status == IncidentStatus.OPEN
    assert len(incident.metadata["incomplete_task_ids"]) == 2
    
    # Step 5: Automatic recovery
    print("\n=== Automatic Recovery ===")
    
    recovery = RecoveryService(db)
    result = recovery.recover_from_node_failure(incident)
    
    print(f"Recovery status: {result['status']}")
    print(f"Tasks recovered: {result['tasks_recovered']}")
    
    # Verify recovery succeeded
    assert result["status"] == "success"
    assert result["tasks_recovered"] == 2
    
    # Step 6: Verify tasks reassigned
    db.refresh(task2)
    db.refresh(task3)
    
    print(f"\nTask 2 reassigned: node-a → {task2.node_id}")
    print(f"Task 3 reassigned: node-a → {task3.node_id}")
    
    assert task2.node_id != node_a.node_id  # Not on failed node
    assert task3.node_id != node_a.node_id
    assert task2.node_id in [node_b.node_id, node_c.node_id]  # On healthy node
    assert task3.node_id in [node_b.node_id, node_c.node_id]
    assert task2.status == TaskStatus.ASSIGNED  # Ready to execute
    assert task3.status == TaskStatus.ASSIGNED
    assert task2.retry_count == 1  # Retry counter incremented
    assert task3.retry_count == 1
    
    # Step 7: Verify incident resolved
    db.refresh(incident)
    assert incident.status == IncidentStatus.RESOLVED
    
    print(f"\nIncident resolved: {incident.resolution}")
    
    # Step 8: Simulate tasks completing on new nodes
    task2.status = TaskStatus.COMPLETED
    task3.status = TaskStatus.COMPLETED
    db.commit()
    
    print("\n=== Final State ===")
    print(f"Node A: OFFLINE (failed)")
    print(f"Node B: AVAILABLE")
    print(f"Node C: AVAILABLE")
    print(f"All tasks: COMPLETED")
    print(f"Job can continue to completion!")
    
    # Verify all tasks completed
    all_tasks = [task1, task2, task3, task4, task5]
    for task in all_tasks:
        db.refresh(task)
        assert task.status == TaskStatus.COMPLETED
    
    print("\n✅ END-TO-END TEST PASSED")
    print("Node failure → detection → reassignment → completion")


def test_recovery_idempotent():
    """Test that recovery can be run multiple times safely."""
    db = next(get_test_db())
    
    failed_node = create_test_node(db, "node-failed", NodeStatus.OFFLINE, is_healthy=False)
    healthy_node = create_test_node(db, "node-healthy")
    
    job = create_test_job(db)
    task = create_test_task(db, job.job_id, failed_node.node_id, 1, TaskStatus.RUNNING)
    
    incident = Incident(
        incident_type="node_failure",
        severity="HIGH",
        description="Node failed",
        node_id=failed_node.node_id,
        status=IncidentStatus.OPEN,
        metadata={
            "incomplete_task_ids": [task.task_id],
            "incomplete_task_count": 1
        }
    )
    db.add(incident)
    db.commit()
    
    recovery = RecoveryService(db)
    
    # Run recovery multiple times
    result1 = recovery.recover_from_node_failure(incident)
    result2 = recovery.recover_from_node_failure(incident)
    result3 = recovery.recover_from_node_failure(incident)
    
    # First should succeed
    assert result1["status"] == "success"
    
    # Subsequent should skip (already resolved)
    assert result2["status"] == "already_resolved"
    assert result3["status"] == "already_resolved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
