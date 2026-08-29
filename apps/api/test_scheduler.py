"""
Tests for Deterministic Scheduler

Run with: pytest test_scheduler.py -v
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from domains.nodes.models import Node, NodeStatus
from domains.jobs.models import Job, JobStatus
from domains.scheduling.scheduler import ResourceScheduler, SchedulingRequirements

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_scheduler.db"
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


def create_test_node(db, provider_id: str, cpu_cores: int, ram_gb: float, 
                     gpu: bool = False, cost: float = 10.0, reliability: float = 0.95):
    """Helper to create test node."""
    caps = {
        "cpu_cores_logical": cpu_cores,
        "ram_total_gb": ram_gb,
        "gpu_available": gpu
    }
    
    if gpu:
        caps["gpu_count"] = 1
        caps["gpus"] = [{"gpu_name": "RTX 3080", "gpu_memory_total_gb": 10.0}]
    
    node = Node(
        provider_id=provider_id,
        capabilities=caps,
        status=NodeStatus.AVAILABLE,
        is_healthy=True,
        reliability_score=reliability,
        cost_per_task_clstr=cost,
        max_concurrent_tasks=4,
        current_task_count=0
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def create_test_job(db, customer_id: str = "test-customer", budget: float = 1000.0):
    """Helper to create test job."""
    job = Job(
        customer_id=customer_id,
        workload_type="frame_rendering",
        parameters={"frame_count": 100},
        budget_clstr=budget,
        status=JobStatus.SUBMITTED
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    return job



def test_sufficient_resources():
    """Test scheduling with sufficient compatible nodes."""
    db = next(get_test_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16, cost=10, reliability=0.95)
    create_test_node(db, "node-2", cpu_cores=8, ram_gb=16, cost=10, reliability=0.90)
    create_test_node(db, "node-3", cpu_cores=8, ram_gb=16, cost=10, reliability=0.85)
    
    job = create_test_job(db, budget=5000)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=100,
        budget_clstr=5000,
        reliability_min=0.8
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible
    assert len(plan.allocated_nodes) > 0
    assert plan.total_tasks == 100
    assert len(plan.warnings) == 0
    
    total_distributed = sum(len(tasks) for tasks in plan.task_distribution.values())
    assert total_distributed == 100


def test_insufficient_resources():
    """Test scheduling when no nodes meet requirements."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=2, ram_gb=4)  # Too small
    create_test_node(db, "node-2", cpu_cores=2, ram_gb=4)  # Too small
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=16,
        ram_gb_min=32,
        task_count=100,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert not plan.is_feasible
    assert len(plan.allocated_nodes) == 0
    assert len(plan.warnings) > 0
    assert "insufficient_cpu" in plan.filtered_reasons or "insufficient_ram" in plan.filtered_reasons


def test_incompatible_gpu():
    """Test scheduling fails when GPU required but none available."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16, gpu=False)
    create_test_node(db, "node-2", cpu_cores=8, ram_gb=16, gpu=False)
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        gpu_required=True,
        task_count=100,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert not plan.is_feasible
    assert "no_gpu" in plan.filtered_reasons
    assert plan.filtered_reasons["no_gpu"] == 2  # Both nodes filtered


def test_unreliable_node_filtered():
    """Test nodes below reliability threshold are filtered."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16, reliability=0.95)  # Good
    create_test_node(db, "node-2", cpu_cores=8, ram_gb=16, reliability=0.50)  # Unreliable
    create_test_node(db, "node-3", cpu_cores=8, ram_gb=16, reliability=0.60)  # Unreliable
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=100,
        budget_clstr=5000,
        reliability_min=0.80
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible
    assert len(plan.allocated_nodes) == 1
    assert "low_reliability" in plan.filtered_reasons
    assert plan.filtered_reasons["low_reliability"] == 2


def test_budget_exceeded():
    """Test scheduling warns when estimated cost exceeds budget."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16, cost=100)  # Very expensive
    
    job = create_test_job(db, budget=500)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=100,
        budget_clstr=500,
        estimated_task_duration_seconds=60
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert not plan.is_feasible
    assert any("budget" in w.lower() for w in plan.warnings)
    assert plan.estimated_cost_clstr > requirements.budget_clstr


def test_deadline_infeasible():
    """Test scheduling warns when estimated duration exceeds deadline."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=100,
        estimated_task_duration_seconds=60,
        deadline_seconds=1000,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert not plan.is_feasible
    assert any("deadline" in w.lower() for w in plan.warnings)
    assert plan.estimated_duration_seconds > requirements.deadline_seconds


def test_partial_capacity():
    """Test scheduling with nodes at partial capacity."""
    db = next(override_get_db())
    
    node1 = create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    node1.current_task_count = 2
    
    node2 = create_test_node(db, "node-2", cpu_cores=8, ram_gb=16)
    node2.current_task_count = 0
    
    db.commit()
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=20,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible


def test_deterministic_output():
    """Test scheduler produces deterministic results."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16, cost=10, reliability=0.95)
    create_test_node(db, "node-2", cpu_cores=8, ram_gb=16, cost=12, reliability=0.90)
    create_test_node(db, "node-3", cpu_cores=8, ram_gb=16, cost=15, reliability=0.85)
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=100,
        budget_clstr=5000,
        reliability_min=0.8
    )
    
    scheduler1 = ResourceScheduler(db)
    plan1 = scheduler1.schedule(job, requirements)
    
    scheduler2 = ResourceScheduler(db)
    plan2 = scheduler2.schedule(job, requirements)
    
    assert plan1.allocated_nodes == plan2.allocated_nodes
    assert plan1.task_distribution == plan2.task_distribution
    assert plan1.estimated_cost_clstr == plan2.estimated_cost_clstr
    assert plan1.estimated_duration_seconds == plan2.estimated_duration_seconds


def test_offline_node_filtered():
    """Test offline nodes are filtered out."""
    db = next(override_get_db())
    
    node1 = create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    node1.status = NodeStatus.OFFLINE
    
    node2 = create_test_node(db, "node-2", cpu_cores=8, ram_gb=16)
    node2.status = NodeStatus.AVAILABLE
    
    db.commit()
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=20,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible
    assert len(plan.allocated_nodes) == 1
    assert "offline" in plan.filtered_reasons


def test_at_capacity_node_filtered():
    """Test nodes at full capacity are filtered."""
    db = next(override_get_db())
    
    node1 = create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    node1.current_task_count = 4
    node1.max_concurrent_tasks = 4
    
    node2 = create_test_node(db, "node-2", cpu_cores=8, ram_gb=16)
    node2.current_task_count = 0
    
    db.commit()
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=20,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible
    assert len(plan.allocated_nodes) == 1
    assert "at_capacity" in plan.filtered_reasons


def test_scoring_weights_reliability():
    """Test reliability is weighted heavily in scoring."""
    db = next(override_get_db())
    
    create_test_node(db, "node-reliable", cpu_cores=8, ram_gb=16, 
                     cost=20, reliability=0.99)
    
    create_test_node(db, "node-cheap", cpu_cores=8, ram_gb=16, 
                     cost=5, reliability=0.80)
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=20,
        budget_clstr=5000,
        reliability_min=0.75
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.is_feasible
    assert len(plan.allocated_nodes) >= 1


def test_round_robin_distribution():
    """Test tasks are distributed round-robin across nodes."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    create_test_node(db, "node-2", cpu_cores=8, ram_gb=16)
    create_test_node(db, "node-3", cpu_cores=8, ram_gb=16)
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=9,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    for node_id, tasks in plan.task_distribution.items():
        assert len(tasks) == 3


def test_audit_trail():
    """Test allocation plan includes complete audit information."""
    db = next(override_get_db())
    
    create_test_node(db, "node-1", cpu_cores=8, ram_gb=16)
    create_test_node(db, "node-2", cpu_cores=2, ram_gb=2)  # Too small
    
    job = create_test_job(db)
    
    requirements = SchedulingRequirements(
        cpu_cores_min=4,
        ram_gb_min=8,
        task_count=20,
        budget_clstr=5000
    )
    
    scheduler = ResourceScheduler(db)
    plan = scheduler.schedule(job, requirements)
    
    assert plan.candidate_nodes_count == 2
    assert len(plan.filtered_reasons) > 0
    assert len(plan.node_scores) > 0
    assert plan.scheduling_timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
