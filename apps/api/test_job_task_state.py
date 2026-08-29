"""
Tests for Job and Task State Machines - Phase 3

Run with: pytest test_job_task_state.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db
from domains.jobs.models import Job, JobStatus, JOB_TRANSITIONS
from domains.tasks.models import Task, TaskStatus, TASK_TRANSITIONS
from domains.jobs.service import JobService
from domains.tasks.service import TaskService

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_state.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    # Seed workload type
    from domains.workloads.seed import seed_workload_types
    db = next(override_get_db())
    seed_workload_types(db)
    
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# JOB STATE TESTS
# ============================================================================

def test_job_creation():
    """Test job starts in SUBMITTED state."""
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    
    assert response.status_code == 201
    job = response.json()
    assert job["status"] == "submitted"


def test_job_valid_transitions():
    """Test valid job state transitions."""
    # Create job
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = response.json()["job_id"]
    
    # SUBMITTED → ANALYZING
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "analyzing"})
    assert response.status_code == 200
    assert response.json()["status"] == "analyzing"
    
    # ANALYZING → SCHEDULING
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "scheduling"})
    assert response.status_code == 200
    
    # SCHEDULING → ALLOCATED
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "allocated"})
    assert response.status_code == 200
    
    # ALLOCATED → RUNNING
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "running"})
    assert response.status_code == 200
    
    # RUNNING → COMPLETED
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "completed"})
    assert response.status_code == 200


def test_job_invalid_transition():
    """Test invalid job state transition is rejected."""
    # Create job
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = response.json()["job_id"]
    
    # Try invalid: SUBMITTED → RUNNING (must go through ANALYZING, SCHEDULING, ALLOCATED first)
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "running"})
    assert response.status_code == 400
    assert "invalid transition" in response.json()["detail"].lower()


def test_job_recovery_transition():
    """Test job can transition to RECOVERING and back to RUNNING."""
    # Create and advance to RUNNING
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = response.json()["job_id"]
    
    # SUBMITTED → ANALYZING → SCHEDULING → ALLOCATED → RUNNING
    for status in ["analyzing", "scheduling", "allocated", "running"]:
        client.post(f"/api/jobs/{job_id}/transition", params={"new_status": status})
    
    # RUNNING → RECOVERING
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "recovering"})
    assert response.status_code == 200
    
    # RECOVERING → RUNNING
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "running"})
    assert response.status_code == 200


def test_job_cannot_transition_from_terminal():
    """Test terminal states (COMPLETED, FAILED, CANCELLED) cannot transition."""
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = response.json()["job_id"]
    
    # Advance to COMPLETED
    for status in ["analyzing", "scheduling", "allocated", "running", "completed"]:
        client.post(f"/api/jobs/{job_id}/transition", params={"new_status": status})
    
    # Try to transition from COMPLETED
    response = client.post(f"/api/jobs/{job_id}/transition", params={"new_status": "analyzing"})
    assert response.status_code == 400


def test_job_can_cancel_from_most_states():
    """Test job can be cancelled from non-terminal states."""
    response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = response.json()["job_id"]
    
    # SUBMITTED → CANCELLED
    response = client.post(f"/api/jobs/{job_id}/cancel", json={"reason": "Test cancellation"})
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# ============================================================================
# TASK STATE TESTS
# ============================================================================

def test_task_creation():
    """Test task starts in PENDING state."""
    # Create job first
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    # Create task
    response = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    
    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "pending"


def test_task_valid_transitions():
    """Test valid task state transitions."""
    # Setup
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    task_response = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    task_id = task_response.json()["task_id"]
    
    # PENDING → ASSIGNED
    response = client.post(
        f"/api/tasks/{task_id}/transition",
        params={"new_status": "assigned", "node_id": "node-123"}
    )
    assert response.status_code == 200
    
    # ASSIGNED → RUNNING
    response = client.post(
        f"/api/tasks/{task_id}/transition",
        params={"new_status": "running"}
    )
    assert response.status_code == 200
    
    # RUNNING → COMPLETED
    response = client.post(
        f"/api/tasks/{task_id}/transition",
        params={"new_status": "completed", "result_url": "s3://results/1.png"}
    )
    assert response.status_code == 200


def test_task_invalid_transition():
    """Test invalid task state transition is rejected."""
    # Setup
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    task_response = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    task_id = task_response.json()["task_id"]
    
    # Try invalid: PENDING → COMPLETED (must go through ASSIGNED, RUNNING)
    response = client.post(
        f"/api/tasks/{task_id}/transition",
        params={"new_status": "completed"}
    )
    assert response.status_code == 400
    assert "invalid transition" in response.json()["detail"].lower()


def test_task_retry_mechanism():
    """Test task can be retried after failure."""
    # Setup
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    task_response = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    task_id = task_response.json()["task_id"]
    
    # PENDING → ASSIGNED → RUNNING → FAILED
    client.post(f"/api/tasks/{task_id}/transition", params={"new_status": "assigned", "node_id": "node-123"})
    client.post(f"/api/tasks/{task_id}/transition", params={"new_status": "running"})
    client.post(f"/api/tasks/{task_id}/transition", params={"new_status": "failed", "error_message": "Node crashed"})
    
    # FAILED → RETRYING
    response = client.post(f"/api/tasks/{task_id}/retry")
    assert response.status_code == 200
    assert response.json()["status"] == "retrying"
    assert response.json()["retry_count"] == 1


def test_task_max_retries_exceeded():
    """Test task cannot retry after max_retries reached."""
    db = next(override_get_db())
    
    # Create job
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    # Create task with max_retries=2
    task_response = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 2
        }
    )
    task_id = task_response.json()["task_id"]
    
    # Manually set retry_count to max
    task = db.query(Task).filter(Task.task_id == task_id).first()
    task.retry_count = 2
    task.status = TaskStatus.FAILED
    db.commit()
    
    # Try to retry
    response = client.post(f"/api/tasks/{task_id}/retry")
    assert response.status_code == 400
    assert "exhausted retries" in response.json()["detail"].lower()


def test_task_idempotent_creation():
    """Test creating task with same job_id + task_number returns existing."""
    job_response = client.post(
        "/api/jobs/",
        json={
            "customer_id": "customer-1",
            "workload_type": "frame_rendering",
            "parameters": {"frame_count": 100},
            "budget_clstr": 1000
        }
    )
    job_id = job_response.json()["job_id"]
    
    # Create task
    response1 = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    task_id_1 = response1.json()["task_id"]
    
    # Create same task again
    response2 = client.post(
        "/api/tasks/",
        json={
            "job_id": job_id,
            "task_number": 1,  # Same task number
            "parameters": {"frame_range": "1-25"},
            "max_retries": 3
        }
    )
    task_id_2 = response2.json()["task_id"]
    
    assert task_id_1 == task_id_2  # Idempotent


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
